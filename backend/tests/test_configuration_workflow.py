import pytest

from app.core.config import get_settings
from app.services.cisco.configuration import ConfigurationValidationError, apply_preview, preview


def test_preview_requires_explicit_confirmation_for_apply() -> None:
    result = preview(["interface Gi1/0/1", "description uplink"], device_id=7)

    with pytest.raises(ConfigurationValidationError, match="confirmation"):
        apply_preview(result.confirmation_token, False, device_id=7)


def test_confirmed_apply_is_audit_only_until_execution_phase() -> None:
    result = preview(["interface Gi1/0/1"], device_id=7)

    audit = apply_preview(result.confirmation_token, True, device_id=7)

    assert audit.accepted is True
    assert audit.executed is False


def test_configuration_rejects_dangerous_tokens() -> None:
    with pytest.raises(ConfigurationValidationError, match="disallowed"):
        preview(["reload"], device_id=7)


def test_confirmation_token_cannot_be_replayed_for_another_device() -> None:
    result = preview(["interface Gi1/0/1"], device_id=7)

    with pytest.raises(ConfigurationValidationError, match="invalid or expired"):
        apply_preview(result.confirmation_token, True, device_id=8)


def test_production_rejects_the_development_confirmation_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NMS_ENVIRONMENT", "production")
    monkeypatch.setenv("NMS_CONFIG_CONFIRMATION_SECRET", "local-development-confirmation-secret")
    get_settings.cache_clear()
    try:
        with pytest.raises(ConfigurationValidationError, match="changed in production"):
            preview(["interface Gi1/0/1"], device_id=7)
    finally:
        get_settings.cache_clear()
