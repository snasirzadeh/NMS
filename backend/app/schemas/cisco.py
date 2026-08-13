from pydantic import BaseModel, Field


class ShowCommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=80)


class ShowCommandResponse(BaseModel):
    command: str
    output: str


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    hostname: str
    duration_ms: int


class InterfaceRefresh(BaseModel):
    name: str
    description: str = ""
    admin_state: str = "unknown"
    operational_state: str = "unknown"
    vlan: str = ""
    mode: str = ""
    speed: str = ""
    duplex: str = ""
    neighbor: str | None = None


class VlanRefresh(BaseModel):
    vlan_id: int
    name: str
    status: str = "unknown"


class NeighborRefresh(BaseModel):
    local_interface: str
    device_id: str
    remote_interface: str = ""
    protocol: str
    platform: str = ""


class DeviceFactsRefresh(BaseModel):
    hostname: str = ""
    model: str = ""
    serial: str = ""
    software_version: str = ""
    uptime: str = ""


class DeviceRefreshResponse(BaseModel):
    facts: DeviceFactsRefresh
    interfaces: list[InterfaceRefresh]
    vlans: list[VlanRefresh]
    neighbors: list[NeighborRefresh]


class ConfigurationPreviewRequest(BaseModel):
    commands: list[str] = Field(min_length=1, max_length=100)


class ConfigurationPreviewResponse(BaseModel):
    commands: list[str]
    confirmation_token: str
    expires_at: int


class ConfigurationApplyRequest(BaseModel):
    confirmation_token: str = Field(min_length=1)
    confirmed: bool = False


class ConfigurationAuditResponse(BaseModel):
    accepted: bool
    executed: bool
    message: str
