from __future__ import annotations

from dataclasses import dataclass
import re
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Device, Group, TopologyLink
from app.services.cisco import CiscoConnectionError, CiscoConnectionService
from app.services.cisco.parsers import parse_neighbors
from app.services.errors import NotFoundError


@dataclass(frozen=True)
class NormalizedNeighbor:
    device_id: str
    local_interface: str
    remote_interface: str
    protocol: str
    platform: str = ""


def normalize_interface(value: str) -> str:
    normalized = re.sub(r"\s+", "", value).replace("TenGigabitEthernet", "Te").replace("GigabitEthernet", "Gi")
    normalized = normalized.replace("FastEthernet", "Fa").replace("TwentyFiveGigE", "Twe")
    return normalized


def normalize_hostname(value: str) -> str:
    return value.strip().rstrip(".").lower().split(".", 1)[0]


def normalize_neighbors(neighbors: list[NormalizedNeighbor]) -> list[NormalizedNeighbor]:
    unique: dict[tuple[str, str, str], NormalizedNeighbor] = {}
    protocol_rank = {"CDP": 0, "LLDP": 1}
    for item in neighbors:
        normalized = NormalizedNeighbor(
            device_id=normalize_hostname(item.device_id),
            local_interface=normalize_interface(item.local_interface),
            remote_interface=normalize_interface(item.remote_interface),
            protocol=item.protocol.upper(),
            platform=item.platform.strip(),
        )
        key = (normalized.device_id, normalized.local_interface, normalized.remote_interface)
        previous = unique.get(key)
        if previous is None or protocol_rank.get(normalized.protocol, 9) < protocol_rank.get(previous.protocol, 9):
            unique[key] = normalized
    return sorted(unique.values(), key=lambda item: (item.device_id, item.local_interface, item.remote_interface))


def topology_for_group(db: Session, group_id: int) -> tuple[list[TopologyNodeData], list[TopologyLink]]:
    group = db.get(Group, group_id)
    if group is None:
        raise NotFoundError("Group not found")
    group_ids = descendant_group_ids(db, group_id)
    devices = list(db.scalars(select(Device).where(Device.group_id.in_(group_ids)).order_by(Device.id)).all())
    links = list(db.scalars(select(TopologyLink).where(TopologyLink.group_id == group_id).order_by(TopologyLink.id)).all())
    known = {normalize_hostname(device.hostname): device for device in devices}
    nodes: dict[str, TopologyNodeData] = {f"device:{device.id}": TopologyNodeData(f"device:{device.id}", device.display_name, device.hostname, True, device.id) for device in devices}
    for link in links:
        if link.destination_device_id is None:
            node_id = f"unmanaged:{normalize_hostname(link.destination_hostname)}"
            nodes.setdefault(node_id, TopologyNodeData(node_id, link.destination_hostname, link.destination_hostname, False, None))
        else:
            destination = known.get(normalize_hostname(link.destination_hostname))
            if destination:
                nodes.setdefault(f"device:{destination.id}", TopologyNodeData(f"device:{destination.id}", destination.display_name, destination.hostname, True, destination.id))
    return list(nodes.values()), links


@dataclass(frozen=True)
class TopologyNodeData:
    id: str
    label: str
    hostname: str
    managed: bool
    device_id: int | None


def descendant_group_ids(db: Session, root_id: int) -> set[int]:
    groups = list(db.scalars(select(Group)).all())
    children: dict[int | None, list[int]] = {}
    for group in groups:
        children.setdefault(group.parent_id, []).append(group.id)
    result: set[int] = set()
    pending = [root_id]
    while pending:
        current = pending.pop()
        if current in result:
            continue
        result.add(current)
        pending.extend(children.get(current, []))
    return result


def discover_group(db: Session, group_id: int, cisco_service: CiscoConnectionService) -> tuple[int, list[str]]:
    group = db.get(Group, group_id)
    if group is None:
        raise NotFoundError("Group not found")
    group_ids = descendant_group_ids(db, group_id)
    devices = list(db.scalars(select(Device).where(Device.group_id.in_(group_ids)).order_by(Device.id)).all())
    known = {normalize_hostname(device.hostname): device for device in devices}
    records: list[tuple[Device, NormalizedNeighbor]] = []
    skipped: list[str] = []
    for device in devices:
        if not device.ssh_config:
            skipped.append(f"{device.display_name}: no SSH configuration")
            continue
        try:
            raw = parse_neighbors(
                cisco_service.show(device.ssh_config, "show cdp neighbors detail"),
                cisco_service.show(device.ssh_config, "show lldp neighbors detail"),
            )
        except CiscoConnectionError as error:
            skipped.append(f"{device.display_name}: {error}")
            continue
        normalized = normalize_neighbors([NormalizedNeighbor(item.device_id, item.local_interface, item.remote_interface, item.protocol, item.platform) for item in raw])
        records.extend((device, item) for item in normalized)

    deduplicated: dict[tuple[object, ...], tuple[Device, NormalizedNeighbor, Device | None]] = {}
    protocol_rank = {"CDP": 0, "LLDP": 1}
    for source, neighbor in records:
        destination = known.get(neighbor.device_id)
        if destination is not None:
            endpoints = sorted(((source.id, neighbor.local_interface), (destination.id, neighbor.remote_interface)))
            key = ("managed", tuple(endpoints))
        else:
            key = ("unmanaged", source.id, neighbor.local_interface, neighbor.device_id, neighbor.remote_interface)
        previous = deduplicated.get(key)
        if previous is None or protocol_rank.get(neighbor.protocol, 9) < protocol_rank.get(previous[1].protocol, 9):
            deduplicated[key] = (source, neighbor, destination)

    db.execute(delete(TopologyLink).where(TopologyLink.group_id == group_id))
    now = datetime.now(timezone.utc)
    for source, neighbor, destination in deduplicated.values():
        db.add(TopologyLink(group_id=group_id, source_device_id=source.id, source_interface=neighbor.local_interface, destination_device_id=destination.id if destination else None, destination_hostname=destination.hostname if destination else neighbor.device_id, destination_interface=neighbor.remote_interface, discovery_protocol=neighbor.protocol, last_discovered_at=now))
    db.commit()
    return len(devices) - len(skipped), skipped
