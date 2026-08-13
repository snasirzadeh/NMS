import pytest
from pydantic import ValidationError

from app.schemas.devices import DeviceCreate


def base_device() -> dict[str, object]:
    return {
        "group_id": 1,
        "display_name": "SW-CORE-01",
        "hostname": "sw-core-01",
        "management_ip": "192.0.2.10",
    }


def test_invalid_management_ip_is_rejected() -> None:
    with pytest.raises(ValidationError):
        DeviceCreate(**{**base_device(), "management_ip": "not-an-ip"})


def test_invalid_ssh_port_is_rejected() -> None:
    with pytest.raises(ValidationError):
        DeviceCreate(**{**base_device(), "ssh_port": 70000})
