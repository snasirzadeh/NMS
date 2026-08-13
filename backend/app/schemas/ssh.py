from pydantic import BaseModel, Field


class SSHConfigRequest(BaseModel):
    config: str = Field(min_length=1, max_length=32 * 1024)


class SSHConfigPreview(BaseModel):
    host: str
    hostname: str
    user: str
    port: int
    identities_only: bool
    identity_file_relative: str
    identity_file_exists: bool
    algorithms: dict[str, str]
    warnings: list[str]
