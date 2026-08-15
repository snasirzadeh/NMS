from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SSHCredentialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    key_type: str
    key_bits: int | None
    key_fingerprint: str
    public_key_fingerprint: str | None
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0


class SSHCredentialForm(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    username: str = Field(min_length=1, max_length=120)
    passphrase: str | None = Field(default=None, max_length=4096)


class HostKeyTrustRequest(BaseModel):
    fingerprint: str = Field(min_length=10, max_length=128)


class HostKeyInfo(BaseModel):
    status: str
    fingerprint: str | None = None
    algorithm: str | None = None
