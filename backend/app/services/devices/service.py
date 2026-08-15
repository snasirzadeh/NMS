from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Device, Group, SSHCredential
from app.schemas.devices import DeviceCreate, DeviceUpdate
from app.schemas.cisco import DeviceFactsRefresh
from app.services.errors import NotFoundError


def get_device(db: Session, device_id: int) -> Device:
    device = db.get(Device, device_id)
    if device is None:
        raise NotFoundError("Device not found")
    return device


def ensure_group(db: Session, group_id: int) -> Group:
    group = db.get(Group, group_id)
    if group is None:
        raise NotFoundError("Group not found")
    return group


def list_devices(db: Session, group_id: int | None = None) -> list[Device]:
    query = select(Device).order_by(Device.display_name, Device.id)
    if group_id is not None:
        query = query.where(Device.group_id == group_id)
    return list(db.scalars(query).all())


def create_device(db: Session, payload: DeviceCreate) -> Device:
    ensure_group(db, payload.group_id)
    if payload.ssh_credential_id is not None and db.get(SSHCredential, payload.ssh_credential_id) is None:
        raise NotFoundError("SSH credential not found")
    device = Device(**payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_device(db: Session, device_id: int, payload: DeviceUpdate) -> Device:
    device = get_device(db, device_id)
    values = payload.model_dump(exclude_unset=True)
    if "group_id" in values:
        ensure_group(db, values["group_id"])
    if values.get("ssh_credential_id") is not None and db.get(SSHCredential, values["ssh_credential_id"]) is None:
        raise NotFoundError("SSH credential not found")
    for key, value in values.items():
        setattr(device, key, value)
    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device_id: int) -> None:
    device = get_device(db, device_id)
    db.delete(device)
    db.commit()


def record_connection_result(
    db: Session,
    device: Device,
    *,
    success: bool,
    error_code: str | None,
    model: str | None = None,
    software_version: str | None = None,
    uptime_text: str | None = None,
) -> Device:
    device.last_connection_status = "success" if success else "failed"
    device.last_connection_test_at = datetime.now(timezone.utc)
    device.last_connection_error_code = error_code
    if success:
        device.model = model or device.model
        device.software_version = software_version or device.software_version
        device.uptime_text = uptime_text or device.uptime_text
    db.commit()
    db.refresh(device)
    return device


def record_device_facts(db: Session, device: Device, facts: DeviceFactsRefresh) -> Device:
    device.model = facts.model or device.model
    device.serial_number = facts.serial or device.serial_number
    device.software_version = facts.software_version or device.software_version
    device.uptime_text = facts.uptime or device.uptime_text
    db.commit()
    db.refresh(device)
    return device
