import re
from typing import Mapping

from app.schemas.cisco import (
    DeviceFactsRefresh,
    DeviceRefreshResponse,
    InterfaceRefresh,
    NeighborRefresh,
    VlanRefresh,
)


def parse_refresh(outputs: Mapping[str, str]) -> DeviceRefreshResponse:
    facts = parse_version(outputs.get("show version", ""))
    facts = facts.model_copy(update=parse_inventory(outputs.get("show inventory", "")))
    interfaces = parse_interfaces(outputs.get("show interfaces status", ""))
    parse_interface_brief(outputs.get("show ip interface brief", ""), interfaces)
    vlans = parse_vlans(outputs.get("show vlan brief", ""))
    neighbors = parse_neighbors(
        outputs.get("show cdp neighbors detail", ""),
        outputs.get("show lldp neighbors detail", ""),
    )
    neighbor_by_port = {item.local_interface: item.device_id for item in neighbors}
    interfaces = [item.model_copy(update={"neighbor": neighbor_by_port.get(item.name)}) for item in interfaces]
    return DeviceRefreshResponse(facts=facts, interfaces=interfaces, vlans=vlans, neighbors=neighbors)


def parse_version(output: str) -> DeviceFactsRefresh:
    hostname = ""
    uptime = ""
    match = re.search(r"^([^\s]+) uptime is (.+)$", output, re.MULTILINE | re.IGNORECASE)
    if match:
        hostname, uptime = match.groups()
    version_match = re.search(r"Version\s+([^,\s]+)", output, re.IGNORECASE)
    model_match = re.search(r"^cisco\s+([^\r\n(]+)", output, re.MULTILINE | re.IGNORECASE)
    return DeviceFactsRefresh(
        hostname=hostname,
        model=model_match.group(1).strip() if model_match else "",
        software_version=version_match.group(1) if version_match else "",
        uptime=uptime,
    )


def parse_inventory(output: str) -> dict[str, str]:
    match = re.search(r"PID:\s*([^,\s]+).*?SN:\s*([^,\s]+)", output, re.IGNORECASE | re.DOTALL)
    if not match:
        return {}
    return {"model": match.group(1), "serial": match.group(2)}


def parse_interfaces(output: str) -> list[InterfaceRefresh]:
    interfaces: list[InterfaceRefresh] = []
    for line in output.splitlines():
        line = line.rstrip()
        match = re.match(
            r"^(\S+)\s+(.*?)\s+(connected|notconnect|disabled|err-disabled|inactive|sfpAbsent)\s+"
            r"(\S+)\s+(\S+)\s+(\S+)\s+(.+)$",
            line,
            re.IGNORECASE,
        )
        if not match or match.group(1).lower() in {"port", "interface"}:
            continue
        name, description, status, vlan, duplex, speed, _ = match.groups()
        status = status.lower()
        interfaces.append(
            InterfaceRefresh(
                name=name,
                description=description.strip(),
                admin_state="down" if status == "disabled" else "up",
                operational_state="up" if status == "connected" else "down",
                vlan=vlan if vlan.lower() != "trunk" else "",
                mode="trunk" if vlan.lower() == "trunk" else "access",
                speed=speed,
                duplex=duplex,
            )
        )
    return interfaces


def parse_interface_brief(output: str, interfaces: list[InterfaceRefresh]) -> None:
    by_name = {item.name: index for index, item in enumerate(interfaces)}
    for line in output.splitlines():
        match = re.match(r"^(\S+)\s+\S+\s+\S+\s+\S+\s+(up|down|administratively down)\s+(up|down)$", line, re.IGNORECASE)
        if not match or match.group(1) not in by_name:
            continue
        name, status, protocol = match.groups()
        index = by_name[name]
        interfaces[index] = interfaces[index].model_copy(
            update={
                "admin_state": "down" if "administratively" in status.lower() else "up",
                "operational_state": "up" if status.lower() == "up" and protocol.lower() == "up" else "down",
            }
        )


def parse_vlans(output: str) -> list[VlanRefresh]:
    vlans: list[VlanRefresh] = []
    for line in output.splitlines():
        match = re.match(r"^\s*(\d+)\s+(.+?)\s{2,}(active|act/lshut|suspend|shutdown)\s*$", line, re.IGNORECASE)
        if match:
            vlan_id, name, status = match.groups()
            vlans.append(VlanRefresh(vlan_id=int(vlan_id), name=name.strip(), status=status.lower()))
    return vlans


def parse_neighbors(cdp_output: str, lldp_output: str) -> list[NeighborRefresh]:
    neighbors = _parse_cdp(cdp_output)
    neighbors.extend(_parse_lldp(lldp_output))
    return neighbors


def _parse_cdp(output: str) -> list[NeighborRefresh]:
    result: list[NeighborRefresh] = []
    blocks = re.split(r"(?=^Device ID:)", output, flags=re.MULTILINE)
    for block in blocks:
        device = re.search(r"^Device ID:\s*(.+)$", block, re.MULTILINE)
        port = re.search(r"Interface:\s*(\S+),.*?Port ID \(outgoing port\):\s*(\S+)", block, re.DOTALL)
        platform = re.search(r"^Platform:\s*([^,\r\n]+)", block, re.MULTILINE)
        if device and port:
            result.append(NeighborRefresh(local_interface=port.group(1), device_id=device.group(1).strip(), remote_interface=port.group(2), protocol="CDP", platform=platform.group(1).strip() if platform else ""))
    return result


def _parse_lldp(output: str) -> list[NeighborRefresh]:
    result: list[NeighborRefresh] = []
    blocks = re.split(r"(?=^Local Intf:|^Local Port id:)", output, flags=re.MULTILINE)
    for block in blocks:
        local = re.search(r"^(?:Local Intf|Local Port id):\s*(\S+)", block, re.MULTILINE | re.IGNORECASE)
        device = re.search(r"^(?:System Name|System Name):\s*(\S+)", block, re.MULTILINE | re.IGNORECASE)
        remote = re.search(r"^(?:Port id|Port ID):\s*(\S+)", block, re.MULTILINE | re.IGNORECASE)
        if local and device:
            result.append(NeighborRefresh(local_interface=local.group(1), device_id=device.group(1), remote_interface=remote.group(1) if remote else "", protocol="LLDP"))
    return result
