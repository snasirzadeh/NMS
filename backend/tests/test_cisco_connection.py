from dataclasses import dataclass

import paramiko
import pytest

from app.models import Device
from app.services.cisco import CiscoConnectionError, CiscoConnectionService, sanitize_exception
from app.services.cisco.connection import FingerprintHostKeyPolicy, FingerprintVerifiedCiscoIosSSH, fingerprint


class FakeSession:
    def __init__(self, output: str = "ok") -> None:
        self.output, self.disconnected = output, False
        self.commands: list[str] = []

    def send_command(self, command: str) -> str:
        self.commands.append(command)
        return self.output

    def disconnect(self) -> None:
        self.disconnected = True


@dataclass
class Material:
    username: str
    key: paramiko.PKey
    passphrase: str | None


def device(host_fingerprint: str | None, profile: str = "modern") -> Device:
    return Device(id=7, group_id=1, display_name="SW-01", hostname="sw-01", management_ip="192.0.2.10", ssh_credential_id=1, ssh_profile=profile, trusted_host_key_fingerprint=host_fingerprint)


@pytest.fixture
def key() -> paramiko.RSAKey:
    return paramiko.RSAKey.generate(1024)


@pytest.fixture
def material(monkeypatch: pytest.MonkeyPatch, key: paramiko.RSAKey) -> None:
    monkeypatch.setattr("app.services.cisco.connection.get_material", lambda *_: Material("cisco", key, None))


def test_successful_connection_uses_in_memory_key_and_strict_host_verification(key, material) -> None:
    session, captured = FakeSession(), {}
    def factory(**kwargs): captured.update(kwargs); return session
    def unexpected_probe(_): raise AssertionError("trusted devices must not use a second SSH handshake")
    service = CiscoConnectionService(factory, unexpected_probe)
    result = service.test_connection(device(fingerprint(key)), object())
    assert result.success is True
    assert session.disconnected is True
    assert captured["pkey"] is key
    assert captured["allow_agent"] is False and captured["use_keys"] is False
    assert "look_for_keys" not in captured
    assert "alt_key_file" not in captured
    assert captured["expected_host_key_fingerprint"] == fingerprint(key)
    assert captured["ssh_strict"] is True


def test_verified_netmiko_driver_consumes_fingerprint_argument() -> None:
    driver = FingerprintVerifiedCiscoIosSSH(
        device_type="cisco_ios",
        host="192.0.2.10",
        expected_host_key_fingerprint="SHA256:test",
        auto_connect=False,
    )

    assert isinstance(driver._build_ssh_client()._policy, FingerprintHostKeyPolicy)


def test_unknown_and_changed_host_keys_are_blocked(key, material) -> None:
    service = CiscoConnectionService(lambda **_: FakeSession(), lambda _: (key, key.get_name()))
    unknown = service.test_connection(device(None), object())
    assert unknown.error_code == "host_key_error"
    assert unknown.host_key == {"fingerprint": fingerprint(key), "algorithm": "ssh-rsa"}

    with pytest.raises(CiscoConnectionError, match="SSH host key changed") as changed:
        FingerprintHostKeyPolicy("SHA256:different").missing_host_key(object(), "192.0.2.10", key)
    assert changed.value.fingerprint == fingerprint(key)


def test_legacy_profile_is_applied_per_device(key, material) -> None:
    captured = {}
    service = CiscoConnectionService(lambda **kwargs: captured.update(kwargs) or FakeSession(), lambda _: (key, key.get_name()))
    assert service.test_connection(device(fingerprint(key), "cisco_legacy"), object()).success
    assert captured["disabled_algorithms"]["pubkeys"] == ["rsa-sha2-512", "rsa-sha2-256"]


def test_show_commands_remain_allowlisted(key, material) -> None:
    session = FakeSession("version output")
    service = CiscoConnectionService(lambda **_: session, lambda _: (key, key.get_name()))
    assert service.show(device(fingerprint(key)), " show version ", object()) == "version output"
    with pytest.raises(CiscoConnectionError, match="allowlist"):
        service.show(device(fingerprint(key)), "show running-config | include password", object())


@pytest.mark.parametrize("error,expected", [(TimeoutError("timed out"), "SSH connection timed out"), (RuntimeError("Authentication failed secret"), "SSH authentication failed"), (RuntimeError("kex algorithm"), "SSH algorithm negotiation failed"), (RuntimeError("no matching key exchange method found"), "SSH algorithm negotiation failed"), (RuntimeError("Incompatible SSH peer"), "SSH algorithm negotiation failed"), (RuntimeError("connection refused"), "SSH connection refused"), (RuntimeError("no route"), "SSH host is unreachable")])
def test_failures_are_sanitized(error, expected) -> None:
    assert sanitize_exception(error) == expected


@pytest.mark.parametrize("error", [RuntimeError("no matching key exchange method found"), RuntimeError("Incompatible SSH peer")])
def test_algorithm_negotiation_failures_get_specific_error_codes(error) -> None:
    from app.services.cisco.connection import _error_code

    assert _error_code(error) == "algorithm_negotiation_failed"
