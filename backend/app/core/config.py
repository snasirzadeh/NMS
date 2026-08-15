from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cisco NMS API"
    app_version: str = "0.3.0"
    environment: str = Field(default="development", validation_alias="NMS_ENVIRONMENT")
    config_confirmation_secret: str = Field(
        default="local-development-confirmation-secret", validation_alias="NMS_CONFIG_CONFIRMATION_SECRET"
    )
    database_url: str = Field(
        default="postgresql+psycopg://nms:nms@postgres:5432/nms",
        validation_alias="DATABASE_URL",
    )
    log_level: str = "INFO"
    session_cookie_name: str = "nms_session"
    csrf_cookie_name: str = "nms_csrf"
    session_ttl_hours: int = Field(default=12, ge=1, le=168)
    secure_cookies: bool = Field(default=False, validation_alias="NMS_SECURE_COOKIES")


@lru_cache
def get_settings() -> Settings:
    return Settings()
