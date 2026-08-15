from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.devices import DeviceCreate, DeviceRead, DeviceUpdate
from app.schemas.backups import BackupCreateResponse, BackupRead, BackupSummary
from app.schemas.cisco import (
    ConfigurationApplyRequest,
    ConfigurationAuditResponse,
    ConfigurationPreviewRequest,
    ConfigurationPreviewResponse,
    ConnectionTestResponse,
    DeviceRefreshResponse,
    ShowCommandRequest,
    ShowCommandResponse,
)
from app.schemas.ssh import HostKeyTrustRequest
from app.services.devices import service
from app.services.errors import NotFoundError
from app.services.cisco import CiscoConnectionError, CiscoConnectionService
from app.services.backups import create_backup, device_backups
from app.services.cisco.configuration import ConfigurationValidationError, apply_preview, preview

from app.api.dependencies import require_authenticated

router = APIRouter(prefix="/devices", tags=["devices"], dependencies=[Depends(require_authenticated)])
cisco_service = CiscoConnectionService()


@router.get("", response_model=list[DeviceRead])
def list_devices(
    group_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db)
) -> list[DeviceRead]:
    return service.list_devices(db, group_id)


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)) -> DeviceRead:
    try:
        return service.create_device(db, payload)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device_id: int, db: Session = Depends(get_db)) -> DeviceRead:
    try:
        return service.get_device(db, device_id)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.patch("/{device_id}", response_model=DeviceRead)
def update_device(device_id: int, payload: DeviceUpdate, db: Session = Depends(get_db)) -> DeviceRead:
    try:
        return service.update_device(db, device_id, payload)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        service.delete_device(db, device_id)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{device_id}/test-connection", response_model=ConnectionTestResponse)
def test_connection(device_id: int, db: Session = Depends(get_db)) -> ConnectionTestResponse:
    try:
        device = service.get_device(db, device_id)
        result = cisco_service.test_connection(device, db)
        service.record_connection_result(
            db,
            device,
            success=result.success,
            error_code=result.error_code,
            model=result.model,
            software_version=result.software_version,
            uptime_text=result.uptime_text,
        )
        return ConnectionTestResponse(**result.__dict__)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{device_id}/show", response_model=ShowCommandResponse)
def show_command(
    device_id: int, payload: ShowCommandRequest, db: Session = Depends(get_db)
) -> ShowCommandResponse:
    try:
        device = service.get_device(db, device_id)
        output = cisco_service.show(device, payload.command, db)
        return ShowCommandResponse(command=" ".join(payload.command.strip().lower().split()), output=output)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except CiscoConnectionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.post("/{device_id}/refresh", response_model=DeviceRefreshResponse)
def refresh_device(device_id: int, db: Session = Depends(get_db)) -> DeviceRefreshResponse:
    try:
        device = service.get_device(db, device_id)
        result = cisco_service.refresh(device, db)
        service.record_device_facts(db, device, result.facts)
        return result
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except CiscoConnectionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.post("/{device_id}/config/preview", response_model=ConfigurationPreviewResponse)
def preview_configuration(device_id: int, payload: ConfigurationPreviewRequest, db: Session = Depends(get_db)) -> ConfigurationPreviewResponse:
    try:
        service.get_device(db, device_id)
        result = preview(payload.commands, device_id=device_id)
        return ConfigurationPreviewResponse(**result.__dict__)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ConfigurationValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.post("/{device_id}/config/apply", response_model=ConfigurationAuditResponse)
def apply_configuration(device_id: int, payload: ConfigurationApplyRequest, db: Session = Depends(get_db)) -> ConfigurationAuditResponse:
    try:
        service.get_device(db, device_id)
        result = apply_preview(payload.confirmation_token, payload.confirmed, device_id=device_id)
        return ConfigurationAuditResponse(**result.__dict__)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ConfigurationValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.get("/{device_id}/backups", response_model=list[BackupSummary])
def list_device_backups(device_id: int, db: Session = Depends(get_db)) -> list[BackupSummary]:
    try:
        return device_backups(db, device_id)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{device_id}/backups", response_model=BackupCreateResponse, status_code=status.HTTP_201_CREATED)
def create_device_backup(device_id: int, db: Session = Depends(get_db)) -> BackupCreateResponse:
    try:
        return create_backup(db, device_id, cisco_service)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except CiscoConnectionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.post("/{device_id}/host-key/trust", response_model=DeviceRead)
def trust_host_key(device_id: int, payload: HostKeyTrustRequest, db: Session = Depends(get_db)) -> DeviceRead:
    try:
        device = service.get_device(db, device_id)
        presented, algorithm = cisco_service.presented_host_key(device)
        if payload.fingerprint != presented:
            raise HTTPException(status_code=409, detail="Presented host key does not match the requested fingerprint")
        device.trusted_host_key_fingerprint = presented
        device.trusted_host_key_algorithm = algorithm
        db.commit()
        db.refresh(device)
        return device
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except CiscoConnectionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
