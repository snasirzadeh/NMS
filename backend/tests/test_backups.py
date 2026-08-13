from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models import ConfigBackup, Device, Group
from app.services.backups.service import checksum, create_backup


class FakeCiscoService:
    def show(self, config_text: str, command: str) -> str:
        assert command == "show running-config"
        assert config_text == "opaque ssh configuration"
        return "version 17.9\ninterface Gi1/0/1\n description uplink\n"


def test_checksum_is_sha256_of_exact_configuration() -> None:
    assert checksum("running-config") == "6fec297eabf0099ec7de572ad663a361d9a8b51d6c3ee8449922c22bec61e20a"


def test_create_backup_stores_configuration_and_checksum() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        group = Group(name="Aria")
        db.add(group)
        db.commit()
        device = Device(group_id=group.id, display_name="SW-01", hostname="sw-01", management_ip="192.0.2.10", ssh_config="opaque ssh configuration")
        db.add(device)
        db.commit()

        backup = create_backup(db, device.id, FakeCiscoService())

        assert backup.configuration.startswith("version 17.9")
        assert backup.checksum == checksum(backup.configuration)
        assert db.query(ConfigBackup).count() == 1
