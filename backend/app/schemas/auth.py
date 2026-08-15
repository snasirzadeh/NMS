from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _secure_password(value: str) -> str:
    classes = (any(char.islower() for char in value), any(char.isupper() for char in value), any(char.isdigit() for char in value))
    if not all(classes):
        raise ValueError("Password must include upper-case, lower-case, and numeric characters")
    return value


class SetupStatus(BaseModel):
    configured: bool


class SetupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,79}$")
    password: str = Field(min_length=12, max_length=256)
    password_confirmation: str = Field(min_length=12, max_length=256)

    _validate_password = field_validator("password")(_secure_password)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class SessionRead(BaseModel):
    authenticated: bool
    configured: bool
    username: str | None = None
    csrf_token: str | None = None
    expires_at: datetime | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)
    new_password_confirmation: str = Field(min_length=12, max_length=256)

    _validate_password = field_validator("new_password")(_secure_password)
