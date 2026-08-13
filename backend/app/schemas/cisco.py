from pydantic import BaseModel, Field


class ShowCommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=80)


class ShowCommandResponse(BaseModel):
    command: str
    output: str


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    hostname: str
    duration_ms: int
