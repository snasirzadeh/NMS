from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ConfigBackup


def list_backups(db: Session, device_id: int) -> list[ConfigBackup]:
    return list(db.scalars(select(ConfigBackup).where(ConfigBackup.device_id == device_id).order_by(ConfigBackup.created_at.desc(), ConfigBackup.id.desc())).all())


def get_backup(db: Session, backup_id: int) -> ConfigBackup | None:
    return db.get(ConfigBackup, backup_id)


def add_backup(db: Session, device_id: int, configuration: str, checksum: str) -> ConfigBackup:
    backup = ConfigBackup(device_id=device_id, configuration=configuration, checksum=checksum)
    db.add(backup)
    db.commit()
    db.refresh(backup)
    return backup
