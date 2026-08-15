from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.backups import BackupRead
from app.services.backups import backup_detail
from app.services.errors import NotFoundError

from app.api.dependencies import require_authenticated

router = APIRouter(prefix="/backups", tags=["backups"], dependencies=[Depends(require_authenticated)])


@router.get("/{backup_id}", response_model=BackupRead)
def get_backup(backup_id: int, db: Session = Depends(get_db)) -> BackupRead:
    try:
        return backup_detail(db, backup_id)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
