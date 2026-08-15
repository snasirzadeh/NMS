from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models import Device, Group
from app.schemas.cisco import DeviceFactsRefresh
from app.services.devices.service import record_connection_result, record_device_facts


def test_explicit_connection_status_transitions() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        group = Group(name="Lab"); db.add(group); db.flush()
        device = Device(group_id=group.id, display_name="SW-01", hostname="sw-01", management_ip="192.0.2.10")
        db.add(device); db.commit(); db.refresh(device)
        assert device.last_connection_status == "unknown"
        record_connection_result(db, device, success=True, error_code=None)
        assert device.last_connection_status == "success"
        record_connection_result(db, device, success=False, error_code="connection_timeout")
        assert device.last_connection_status == "failed"
        record_connection_result(db, device, success=True, error_code=None)
        assert device.last_connection_status == "success"
        record_connection_result(db, device, success=False, error_code="authentication_failed")
        assert device.last_connection_status == "failed"


def test_explicit_ssh_operations_persist_safe_device_facts() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        group = Group(name="Lab"); db.add(group); db.flush()
        device = Device(group_id=group.id, display_name="SW-01", hostname="sw-01", management_ip="192.0.2.10")
        db.add(device); db.commit(); db.refresh(device)

        record_connection_result(db, device, success=True, error_code=None, model="C9300-24T", software_version="17.9.4", uptime_text="2 weeks")
        assert (device.model, device.software_version, device.uptime_text) == ("C9300-24T", "17.9.4", "2 weeks")

        record_device_facts(db, device, DeviceFactsRefresh(model="C9300-24T", serial="FOC123", software_version="17.9.5", uptime="3 weeks"))
        assert (device.serial_number, device.software_version, device.uptime_text) == ("FOC123", "17.9.5", "3 weeks")
