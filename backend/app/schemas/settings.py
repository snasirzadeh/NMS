from pydantic import BaseModel


class SSHKeyRead(BaseModel):
    name: str
    size_bytes: int
    fingerprint: str


class SSHKeyUploadResponse(SSHKeyRead):
    identity_file: str
