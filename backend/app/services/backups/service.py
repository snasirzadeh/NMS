import hashlib

from sqlalchemy.orm import Session

from app.models import ConfigBackup
from app.services.backups.repository import add_backup, get_backup, list_backups
from app.services.cisco import CiscoConnectionError, CiscoConnectionService
from app.services.devices.service import get_device
from app.services.errors import NotFoundError


def checksum(configuration: str) -> str:
    return hashlib.sha256(configuration.encode("utf-8")).hexdigest()


def create_backup(db: Session, device_id: int, cisco_service: CiscoConnectionService) -> ConfigBackup:
    device = get_device(db, device_id)
    if device.ssh_credential_id is None:
        raise CiscoConnectionError("Device has no SSH credential")
    configuration = cisco_service.show(device, "show running-config", db)
    return add_backup(db, device.id, configuration, checksum(configuration))


def device_backups(db: Session, device_id: int) -> list[ConfigBackup]:
    get_device(db, device_id)
    return list_backups(db, device_id)


def backup_detail(db: Session, backup_id: int) -> ConfigBackup:
    backup = get_backup(db, backup_id)
    if backup is None:
        raise NotFoundError("Backup not found")
    return backup
