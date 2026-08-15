from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated
from app.database.session import get_db
from app.models import Admin, SSHCredential
from app.schemas.ssh import SSHCredentialRead
from app.services.credentials import CredentialError, CredentialInUseError, credential_with_usage, create_credential, delete_credential as remove_credential, replace_credential
from app.services.vault import VaultLockedError, vault_service

router = APIRouter(prefix="/credentials", tags=["credentials"])


def _read(credential: SSHCredential) -> SSHCredentialRead:
    return SSHCredentialRead(id=credential.id, name=credential.name, username=credential.username, key_type=credential.key_type, key_bits=credential.key_bits, key_fingerprint=credential.key_fingerprint, public_key_fingerprint=credential.public_key_fingerprint, created_at=credential.created_at, updated_at=credential.updated_at, usage_count=len(credential.devices))


async def _key_text(private_key: str, key_file: UploadFile | None) -> str:
    if key_file is not None:
        raw = await key_file.read(128 * 1024 + 1)
        if len(raw) > 128 * 1024:
            raise CredentialError("Private key is too large")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CredentialError("Private key file must be UTF-8 text") from error
    return private_key


@router.get("", response_model=list[SSHCredentialRead])
def list_credentials(_: Admin = Depends(require_authenticated), db: Session = Depends(get_db)) -> list[SSHCredentialRead]:
    return [_read(item) for item in credential_with_usage(db)]


@router.post("", response_model=SSHCredentialRead, status_code=status.HTTP_201_CREATED)
async def add_credential(name: str = Form(...), username: str = Form(...), private_key: str = Form(""), passphrase: str | None = Form(None), key_file: UploadFile | None = File(None), _: Admin = Depends(require_authenticated), db: Session = Depends(get_db)) -> SSHCredentialRead:
    try:
        credential = create_credential(db, vault_service, name=name, username=username, private_key=await _key_text(private_key, key_file), passphrase=passphrase or None)
        return _read(credential)
    except (CredentialError, VaultLockedError) as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="A credential with that name already exists") from error


@router.post("/{credential_id}/replace", response_model=SSHCredentialRead)
async def replace(credential_id: int, private_key: str = Form(""), passphrase: str | None = Form(None), key_file: UploadFile | None = File(None), _: Admin = Depends(require_authenticated), db: Session = Depends(get_db)) -> SSHCredentialRead:
    credential = db.get(SSHCredential, credential_id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    try:
        return _read(replace_credential(db, vault_service, credential, private_key=await _key_text(private_key, key_file), passphrase=passphrase or None))
    except (CredentialError, VaultLockedError) as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credential(credential_id: int, _: Admin = Depends(require_authenticated), db: Session = Depends(get_db)) -> Response:
    credential = db.get(SSHCredential, credential_id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    try:
        remove_credential(db, credential)
    except CredentialInUseError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return Response(status_code=204)
