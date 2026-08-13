from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.devices import DeviceCreate, DeviceRead, DeviceUpdate
from app.schemas.ssh import SSHConfigPreview, SSHConfigRequest
from app.services.devices import service
from app.services.errors import NotFoundError
from app.services.ssh import SSHConfigError, parse_ssh_config

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceRead])
def list_devices(
    group_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db)
) -> list[DeviceRead]:
    return service.list_devices(db, group_id)


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)) -> DeviceRead:
    try:
        return service.create_device(db, payload)
    except (NotFoundError, SSHConfigError) as error:
        if isinstance(error, SSHConfigError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
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
    except (NotFoundError, SSHConfigError) as error:
        if isinstance(error, SSHConfigError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        service.delete_device(db, device_id)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def build_ssh_preview(payload: SSHConfigRequest) -> SSHConfigPreview:
    try:
        preview = parse_ssh_config(payload.config)
    except SSHConfigError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return SSHConfigPreview(
        host=preview.host,
        hostname=preview.hostname,
        user=preview.user,
        port=preview.port,
        identities_only=preview.identities_only,
        identity_file_relative=preview.identity_file_relative,
        identity_file_exists=preview.identity_file_exists,
        algorithms=preview.algorithms,
        warnings=preview.warnings,
    )


@router.post("/ssh-config/preview", response_model=SSHConfigPreview)
def preview_ssh_config(payload: SSHConfigRequest) -> SSHConfigPreview:
    return build_ssh_preview(payload)


@router.post("/{device_id}/ssh-config/preview", response_model=SSHConfigPreview)
def preview_device_ssh_config(device_id: int, payload: SSHConfigRequest) -> SSHConfigPreview:
    return build_ssh_preview(payload)
