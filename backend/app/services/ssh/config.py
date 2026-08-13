from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import re

from paramiko import SSHConfig
from paramiko.config import ConfigParseError

from app.core.config import get_settings

MAX_CONFIG_LENGTH = 32 * 1024
ALLOWED_DIRECTIVES = {
    "host",
    "hostname",
    "user",
    "port",
    "identityfile",
    "identitiesonly",
    "kexalgorithms",
    "hostkeyalgorithms",
    "pubkeyacceptedalgorithms",
}
LEGACY_ALGORITHM_MARKERS = ("diffie-hellman-group14-sha1", "ssh-rsa")
DIRECTIVE_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9]*)\s+(.*?)\s*$")


class SSHConfigError(ValueError):
    pass


@dataclass(frozen=True)
class SSHConfigPreview:
    host: str
    hostname: str
    user: str
    port: int
    identities_only: bool
    identity_file: str
    identity_file_relative: str
    identity_file_exists: bool
    algorithms: dict[str, str]
    warnings: list[str]


def _host_directives(config_text: str) -> tuple[str, list[tuple[str, str]]]:
    hosts: list[str] = []
    directives: list[tuple[str, str]] = []
    for line in config_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = DIRECTIVE_RE.match(line)
        if match is None:
            raise SSHConfigError("Malformed SSH configuration line")
        key, value = match.groups()
        key = key.lower()
        if key not in ALLOWED_DIRECTIVES:
            raise SSHConfigError(f"Unsupported SSH directive: {key}")
        if key == "host":
            hosts.extend(value.split())
        directives.append((key, value))
    if len(hosts) != 1 or any(char in hosts[0] for char in "*?!"):
        raise SSHConfigError("Exactly one non-wildcard Host entry is required")
    seen: set[str] = set()
    for key, _ in directives:
        if key != "host" and key in seen:
            raise SSHConfigError(f"Duplicate SSH directive is ambiguous: {key}")
        seen.add(key)
    return hosts[0], directives


def _map_identity_file(identity_file: str, require_exists: bool) -> tuple[str, str, bool]:
    settings = get_settings()
    if "\x00" in identity_file or "\x00" in settings.ssh_identity_host_prefix:
        raise SSHConfigError("IdentityFile contains an invalid character")
    if any(part == ".." for part in PurePosixPath(identity_file).parts):
        raise SSHConfigError("IdentityFile path traversal is not allowed")

    host_prefix = settings.ssh_identity_host_prefix.rstrip("/")
    container_prefix = Path(settings.ssh_identity_container_prefix).resolve()
    if (
        not host_prefix
        or any(part == ".." for part in PurePosixPath(host_prefix).parts)
        or not Path(settings.ssh_identity_container_prefix).is_absolute()
    ):
        raise SSHConfigError("SSH identity prefixes must be configured as valid paths")
    if not identity_file.startswith(f"{host_prefix}/"):
        raise SSHConfigError("IdentityFile is outside the configured allowed host prefix")

    relative = identity_file[len(host_prefix) + 1 :]
    if not relative or "/" in relative and any(part in {".", ""} for part in relative.split("/")):
        raise SSHConfigError("IdentityFile path is invalid")
    mapped = (container_prefix / relative).resolve(strict=False)
    try:
        mapped.relative_to(container_prefix)
    except ValueError as exc:
        raise SSHConfigError("Mapped IdentityFile is outside the container key directory") from exc
    exists = mapped.is_file() and os.access(mapped, os.R_OK)
    if require_exists and not exists:
        raise SSHConfigError("Configured IdentityFile is not a regular readable file")
    return str(mapped), relative, exists


def parse_ssh_config(config_text: str, *, require_identity_file: bool = False) -> SSHConfigPreview:
    if not config_text.strip() or len(config_text) > MAX_CONFIG_LENGTH:
        raise SSHConfigError("SSH configuration is empty or exceeds the size limit")
    host, directives = _host_directives(config_text)
    try:
        parsed = SSHConfig.from_text(config_text).lookup(host)
    except (ConfigParseError, ValueError) as exc:
        raise SSHConfigError("SSH configuration could not be parsed") from exc

    hostname = str(parsed.get("hostname", "")).strip()
    user = str(parsed.get("user", "")).strip()
    if not hostname or not user:
        raise SSHConfigError("HostName and User are required")
    try:
        port = int(parsed.get("port", 22))
    except (TypeError, ValueError) as exc:
        raise SSHConfigError("SSH Port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise SSHConfigError("SSH Port must be between 1 and 65535")

    identity_files = [value for key, value in directives if key == "identityfile"]
    if len(identity_files) != 1:
        raise SSHConfigError("Exactly one IdentityFile is required")
    mapped, relative, exists = _map_identity_file(identity_files[0], require_identity_file)
    identities_only = str(parsed.get("identitiesonly", "no")).lower() in {"yes", "true"}
    algorithms = {
        key: value
        for key, value in directives
        if key in {"kexalgorithms", "hostkeyalgorithms", "pubkeyacceptedalgorithms"}
    }
    warnings = [
        f"Legacy SSH algorithm enabled: {marker}"
        for value in algorithms.values()
        for marker in LEGACY_ALGORITHM_MARKERS
        if marker in value
    ]
    return SSHConfigPreview(
        host=host,
        hostname=hostname,
        user=user,
        port=port,
        identities_only=identities_only,
        identity_file=mapped,
        identity_file_relative=relative,
        identity_file_exists=exists,
        algorithms=algorithms,
        warnings=sorted(set(warnings)),
    )
