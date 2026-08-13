import textwrap

import pytest

from app.core.config import get_settings
from app.services.ssh import SSHConfigError, parse_ssh_config


def config(identity_file: str = "~/.ssh/keys/cisco") -> str:
    return textwrap.dedent(
        f"""
        Host cisco-sw1
            HostName 192.0.2.10
            User cisco
            Port 2222
            IdentityFile {identity_file}
            IdentitiesOnly yes
            KexAlgorithms +diffie-hellman-group14-sha1
            HostKeyAlgorithms +ssh-rsa
            PubkeyAcceptedAlgorithms +ssh-rsa
        """
    ).strip()


@pytest.fixture
def key_root(tmp_path, monkeypatch):
    root = tmp_path / "ssh-keys"
    root.mkdir()
    (root / "cisco").write_text("PRIVATE KEY MUST NEVER BE RETURNED", encoding="utf-8")
    monkeypatch.setenv("SSH_IDENTITY_HOST_PREFIX", "~/.ssh/keys")
    monkeypatch.setenv("SSH_IDENTITY_CONTAINER_PREFIX", str(root))
    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_valid_config_and_legacy_warnings(key_root) -> None:
    preview = parse_ssh_config(config())

    assert preview.hostname == "192.0.2.10"
    assert preview.user == "cisco"
    assert preview.port == 2222
    assert preview.identity_file_relative == "cisco"
    assert preview.identity_file_exists is True
    assert "ssh-rsa" in " ".join(preview.warnings)


def test_identity_file_must_be_inside_allowed_prefix(key_root) -> None:
    with pytest.raises(SSHConfigError, match="outside"):
        parse_ssh_config(config("~/.ssh/id_rsa"))


def test_identity_file_traversal_is_rejected(key_root) -> None:
    with pytest.raises(SSHConfigError, match="traversal"):
        parse_ssh_config(config("~/.ssh/keys/../id_rsa"))


def test_multiple_hosts_and_unsupported_directives_are_rejected(key_root) -> None:
    with pytest.raises(SSHConfigError, match="Exactly one"):
        parse_ssh_config(config() + "\nHost another\n    HostName 192.0.2.11")
    with pytest.raises(SSHConfigError, match="Unsupported"):
        parse_ssh_config(config() + "\nInclude ~/.ssh/config")


def test_missing_key_is_only_blocking_when_connection_validation_runs(key_root) -> None:
    preview = parse_ssh_config(config("~/.ssh/keys/missing"))
    assert preview.identity_file_exists is False
    with pytest.raises(SSHConfigError, match="regular"):
        parse_ssh_config(config("~/.ssh/keys/missing"), require_identity_file=True)


def test_preview_does_not_contain_private_key_content(key_root) -> None:
    preview = parse_ssh_config(config())
    assert "PRIVATE KEY MUST NEVER BE RETURNED" not in repr(preview)


def test_identity_symlink_outside_allowlist_is_rejected(key_root, tmp_path) -> None:
    outside = tmp_path / "outside-key"
    outside.write_text("private", encoding="utf-8")
    (key_root / "linked").symlink_to(outside)

    with pytest.raises(SSHConfigError, match="outside"):
        parse_ssh_config(config("~/.ssh/keys/linked"), require_identity_file=True)


def test_hostname_and_user_control_characters_are_rejected(key_root) -> None:
    with pytest.raises(SSHConfigError, match="HostName"):
        parse_ssh_config(config().replace("192.0.2.10", "bad host"))
    with pytest.raises(SSHConfigError, match="User"):
        parse_ssh_config(config().replace("User cisco", "User bad user"))
