from datetime import datetime

from pydantic import BaseModel


class TopologyNode(BaseModel):
    id: str
    label: str
    hostname: str
    managed: bool
    device_id: int | None = None


class TopologyEdge(BaseModel):
    id: str
    source: str
    target: str
    source_interface: str
    destination_interface: str
    protocol: str
    discovered_at: datetime


class TopologyResponse(BaseModel):
    group_id: int
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]


class TopologyDiscoveryResponse(TopologyResponse):
    refreshed_devices: int
    skipped_devices: list[str]
