from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BackupSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    checksum: str
    created_at: datetime


class BackupRead(BackupSummary):
    configuration: str


class BackupCreateResponse(BackupSummary):
    pass
