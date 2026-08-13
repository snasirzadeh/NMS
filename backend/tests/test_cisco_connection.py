from pathlib import Path

import pytest

from app.core.config import get_settings
from app.services.cisco import CiscoConnectionError, CiscoConnectionService, sanitize_exception


CONFIG = """Host switch
    HostName 192.0.2.10
    User cisco
    IdentityFile ~/.ssh/keys/cisco
    IdentitiesOnly yes
"""


class FakeSession:
    def __init__(self, output: str = "ok") -> None:
        self.output = output
        self.commands: list[str] = []
        self.disconnected = False

    def send_command(self, command: str) -> str:
        self.commands.append(command)
        return self.output

    def disconnect(self) -> None:
        self.disconnected = True


@pytest.fixture
def configured_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "keys"
    root.mkdir()
    (root / "cisco").write_text("test-only-key", encoding="utf-8")
    monkeypatch.setenv("SSH_IDENTITY_HOST_PREFIX", "~/.ssh/keys")
    monkeypatch.setenv("SSH_IDENTITY_CONTAINER_PREFIX", str(root))
    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_test_connection_disconnects_fake_session(configured_key: Path) -> None:
    session = FakeSession()
    service = CiscoConnectionService(lambda **_: session)

    result = service.test_connection(CONFIG)

    assert result.success is True
    assert session.disconnected is True


def test_safe_show_allowlist_and_disconnect(configured_key: Path) -> None:
    session = FakeSession("version output")
    service = CiscoConnectionService(lambda **_: session)

    assert service.show(CONFIG, " show version ") == "version output"
    assert session.commands == ["show version"]
    assert session.disconnected is True
    with pytest.raises(CiscoConnectionError, match="allowlist"):
        service.show(CONFIG, "show running-config | include password")


def test_connection_errors_are_sanitized(configured_key: Path) -> None:
    def failing_factory(**_: object) -> FakeSession:
        raise RuntimeError("Authentication failed for cisco with private key contents")

    service = CiscoConnectionService(failing_factory)
    result = service.test_connection(CONFIG)

    assert result.success is False
    assert result.message == "SSH authentication failed"
    assert "private key" not in result.message
    assert sanitize_exception(TimeoutError("timed out")) == "SSH connection timed out"
