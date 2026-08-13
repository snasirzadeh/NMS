import pytest

from app.services.cisco.configuration import ConfigurationValidationError, apply_preview, preview


def test_preview_requires_explicit_confirmation_for_apply() -> None:
    result = preview(["interface Gi1/0/1", "description uplink"])

    with pytest.raises(ConfigurationValidationError, match="confirmation"):
        apply_preview(result.confirmation_token, False)


def test_confirmed_apply_is_audit_only_until_execution_phase() -> None:
    result = preview(["interface Gi1/0/1"])

    audit = apply_preview(result.confirmation_token, True)

    assert audit.accepted is True
    assert audit.executed is False


def test_configuration_rejects_dangerous_tokens() -> None:
    with pytest.raises(ConfigurationValidationError, match="disallowed"):
        preview(["reload"])
