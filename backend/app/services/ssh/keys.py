import base64
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings

MAX_KEY_SIZE = 64 * 1024
KEY_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class SSHKeyError(ValueError):
    pass


@dataclass(frozen=True)
class SSHKeyMetadata:
    name: str
    size_bytes: int
    fingerprint: str


def _key_dir() -> Path:
    directory = Path(get_settings().ssh_uploaded_keys_dir)
    if not directory.is_absolute():
        raise SSHKeyError("Uploaded SSH key directory is not configured as an absolute path")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    return directory


def _validate_name(name: str) -> str:
    normalized = name.strip()
    if not KEY_NAME_RE.fullmatch(normalized):
        raise SSHKeyError("Key name must use 1-64 letters, numbers, dots, dashes, or underscores")
    return normalized


def _metadata(name: str, content: bytes) -> SSHKeyMetadata:
    digest = base64.b64encode(hashlib.sha256(content).digest()).decode("ascii").rstrip("=")
    return SSHKeyMetadata(name=name, size_bytes=len(content), fingerprint=f"SHA256:{digest}")


def list_keys() -> list[SSHKeyMetadata]:
    directory = _key_dir()
    return sorted(
        (_metadata(path.name, path.read_bytes()) for path in directory.iterdir() if path.is_file() and KEY_NAME_RE.fullmatch(path.name)),
        key=lambda key: key.name.lower(),
    )


def save_key(name: str, content: bytes) -> SSHKeyMetadata:
    normalized = _validate_name(name)
    if not content or len(content) > MAX_KEY_SIZE:
        raise SSHKeyError("Private key must be between 1 byte and 64 KiB")
    if b"\x00" in content or b"PRIVATE KEY" not in content[:512]:
        raise SSHKeyError("The uploaded file does not look like a private SSH key")
    directory = _key_dir()
    destination = (directory / normalized).resolve()
    if destination.parent != directory.resolve():
        raise SSHKeyError("Invalid SSH key path")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    file_descriptor = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(file_descriptor, "wb") as key_file:
            key_file.write(content)
        os.chmod(destination, 0o600)
    except Exception:
        try:
            destination.unlink(missing_ok=True)
        except OSError:
            pass
        raise SSHKeyError("The SSH key could not be stored")
    return _metadata(normalized, content)
