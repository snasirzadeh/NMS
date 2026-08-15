from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeviceBase(BaseModel):
    group_id: int = Field(gt=0)
    display_name: str = Field(min_length=1, max_length=200)
    hostname: str = Field(min_length=1, max_length=255)
    management_ip: str
    device_type: str = Field(default="switch", min_length=1, max_length=100)
    platform: str | None = Field(default=None, max_length=100)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_credential_id: int | None = Field(default=None, gt=0)
    ssh_profile: str = Field(default="modern", pattern="^(modern|cisco_legacy)$")
    description: str | None = None
    site: str | None = Field(default=None, max_length=200)
    rack: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=200)
    model: str | None = Field(default=None, max_length=200)
    software_version: str | None = Field(default=None, max_length=200)

    @field_validator("management_ip")
    @classmethod
    def validate_management_ip(cls, value: str) -> str:
        try:
            parsed = IPv4Address(value) if "." in value else IPv6Address(value)
        except ValueError as exc:
            raise ValueError("management_ip must be a valid IPv4 or IPv6 address") from exc
        return str(parsed)


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    group_id: int | None = Field(default=None, gt=0)
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    hostname: str | None = Field(default=None, min_length=1, max_length=255)
    management_ip: str | None = None
    device_type: str | None = Field(default=None, min_length=1, max_length=100)
    platform: str | None = Field(default=None, max_length=100)
    ssh_port: int | None = Field(default=None, ge=1, le=65535)
    ssh_credential_id: int | None = Field(default=None, gt=0)
    ssh_profile: str | None = Field(default=None, pattern="^(modern|cisco_legacy)$")
    description: str | None = None
    site: str | None = Field(default=None, max_length=200)
    rack: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=200)
    model: str | None = Field(default=None, max_length=200)
    software_version: str | None = Field(default=None, max_length=200)

    @field_validator("management_ip")
    @classmethod
    def validate_management_ip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            parsed = IPv4Address(value) if "." in value else IPv6Address(value)
        except ValueError as exc:
            raise ValueError("management_ip must be a valid IPv4 or IPv6 address") from exc
        return str(parsed)


class DeviceRead(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uptime_text: str | None
    ssh_credential_id: int | None
    ssh_profile: str
    trusted_host_key_fingerprint: str | None
    trusted_host_key_algorithm: str | None
    last_connection_status: str
    last_connection_test_at: datetime | None
    last_connection_error_code: str | None
    created_at: datetime
    updated_at: datetime
