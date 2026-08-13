from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.settings import SSHKeyRead, SSHKeyUploadResponse
from app.services.ssh.keys import SSHKeyError, list_keys, save_key

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/ssh-keys", response_model=list[SSHKeyRead])
def get_ssh_keys() -> list[SSHKeyRead]:
    try:
        return [SSHKeyRead(**key.__dict__) for key in list_keys()]
    except SSHKeyError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.post("/ssh-keys", response_model=SSHKeyUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_ssh_key(name: str = Form(...), key_file: UploadFile = File(...)) -> SSHKeyUploadResponse:
    try:
        content = await key_file.read(64 * 1024 + 1)
        metadata = save_key(name, content)
        return SSHKeyUploadResponse(**metadata.__dict__, identity_file=f"~/.ssh/nms-keys/{metadata.name}")
    except SSHKeyError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
