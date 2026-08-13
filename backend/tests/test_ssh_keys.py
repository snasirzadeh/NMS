from pathlib import Path

import pytest

from app.services.ssh import keys


def test_save_key_uses_restrictive_permissions_and_redacted_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(keys, "get_settings", lambda: type("Settings", (), {"ssh_uploaded_keys_dir": str(tmp_path)})())

    metadata = keys.save_key("cisco-prod", b"-----BEGIN OPENSSH PRIVATE KEY-----\nsecret\n")

    stored = tmp_path / "cisco-prod"
    assert metadata.name == "cisco-prod"
    assert metadata.fingerprint.startswith("SHA256:")
    assert stored.stat().st_mode & 0o777 == 0o600
    assert keys.list_keys()[0].name == "cisco-prod"


def test_save_key_rejects_path_like_names_and_non_private_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(keys, "get_settings", lambda: type("Settings", (), {"ssh_uploaded_keys_dir": str(tmp_path)})())

    with pytest.raises(keys.SSHKeyError):
        keys.save_key("../escape", b"-----BEGIN PRIVATE KEY-----")
    with pytest.raises(keys.SSHKeyError):
        keys.save_key("not-a-key", b"plain text")
