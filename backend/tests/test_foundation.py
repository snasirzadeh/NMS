from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.base import Base
from app.models import Device, Group
from app.schemas.devices import DeviceCreate
from app.schemas.groups import GroupCreate, GroupUpdate
from app.services.devices.service import create_device
from app.services.errors import ConflictError
from app.services.groups.service import create_group, update_group


def test_settings_have_safe_local_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.ssh_identity_container_prefix == "/run/ssh-keys"


def test_foundation_models_are_registered() -> None:
    assert Group.__table__.name == "groups"
    assert Device.__table__.name == "devices"
    assert {"groups", "devices"}.issubset(Base.metadata.tables)


def test_nested_groups_and_device_ownership() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        root = create_group(db, GroupCreate(name="Aria"))
        office = create_group(db, GroupCreate(name="Main Office", parent_id=root.id))
        device = create_device(
            db,
            DeviceCreate(
                group_id=office.id,
                display_name="SW-CORE-01",
                hostname="sw-core-01",
                management_ip="192.0.2.10",
            ),
        )

        assert office.parent_id == root.id
        assert device.group_id == office.id


def test_group_cycle_is_rejected() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        root = create_group(db, GroupCreate(name="Aria"))
        child = create_group(db, GroupCreate(name="Factory", parent_id=root.id))

        try:
            update_group(db, root.id, GroupUpdate(name="Aria", parent_id=child.id))
        except ConflictError:
            pass
        else:
            raise AssertionError("group cycle should be rejected")
