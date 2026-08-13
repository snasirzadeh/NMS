import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from app.core.config import get_settings


class ConfigurationValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ConfigurationPreview:
    commands: list[str]
    confirmation_token: str
    expires_at: int


@dataclass(frozen=True)
class ConfigurationAudit:
    accepted: bool
    executed: bool
    message: str


def validate_commands(commands: list[str]) -> list[str]:
    if not commands or len(commands) > 100:
        raise ConfigurationValidationError("Provide between 1 and 100 configuration commands")
    normalized: list[str] = []
    for command in commands:
        value = command.strip()
        if not value or len(value) > 256:
            raise ConfigurationValidationError("Configuration commands must be non-empty and at most 256 characters")
        if any(token in value for token in ("\n", "\r", ";", "|", "`", "$", "write erase", "erase startup", "reload")):
            raise ConfigurationValidationError("Configuration command contains a disallowed token")
        normalized.append(value)
    return normalized


def preview(commands: list[str], *, device_id: int) -> ConfigurationPreview:
    normalized = validate_commands(commands)
    _secret()
    expires_at = int(time.time()) + 600
    payload = json.dumps({"commands": normalized, "device_id": device_id, "expires_at": expires_at}, separators=(",", ":")).encode()
    encoded = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(_secret(), encoded.encode(), hashlib.sha256).hexdigest()
    return ConfigurationPreview(normalized, f"{encoded}.{signature}", expires_at)


def apply_preview(token: str, confirmed: bool, *, device_id: int) -> ConfigurationAudit:
    if not confirmed:
        raise ConfigurationValidationError("Explicit confirmation is required before apply")
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(_secret(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        commands = validate_commands(payload["commands"])
        if int(payload["device_id"]) != device_id or int(payload["expires_at"]) <= int(time.time()):
            raise ValueError
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise ConfigurationValidationError("Configuration preview token is invalid or expired") from None
    # Execution is deliberately deferred until the dedicated safe-config phase.
    return ConfigurationAudit(True, False, f"Preview confirmed for {len(commands)} command(s); execution is not enabled")


def _secret() -> bytes:
    settings = get_settings()
    if settings.environment.lower() in {"production", "prod"} and settings.config_confirmation_secret == "local-development-confirmation-secret":
        raise ConfigurationValidationError("Configuration confirmation secret must be changed in production")
    return settings.config_confirmation_secret.encode()
