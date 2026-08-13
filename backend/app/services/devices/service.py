from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Device, Group
from app.schemas.devices import DeviceCreate, DeviceUpdate
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
    for key, value in values.items():
        setattr(device, key, value)
    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device_id: int) -> None:
    device = get_device(db, device_id)
    db.delete(device)
    db.commit()
