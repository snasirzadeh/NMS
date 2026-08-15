from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging
import secrets
import socket
import time
from typing import Any, Protocol

import paramiko
from netmiko.cisco.cisco_ios import CiscoIosSSH
from sqlalchemy.orm import Session

from app.models import Device
from app.schemas.cisco import DeviceRefreshResponse
from app.services.credentials import CredentialError, get_material
from app.services.cisco.parsers import parse_refresh
from app.services.vault import VaultLockedError, vault_service

logger = logging.getLogger(__name__)


class CiscoConnectionError(RuntimeError):
    def __init__(self, message: str, code: str = "unknown_error", *, fingerprint: str | None = None, algorithm: str | None = None) -> None:
        super().__init__(message)
        self.code, self.fingerprint, self.algorithm = code, fingerprint, algorithm


@dataclass(frozen=True)
class ConnectionResult:
    success: bool
    message: str
    hostname: str
    duration_ms: int
    error_code: str | None = None
    host_key: dict[str, str | None] | None = None
    model: str | None = None
    software_version: str | None = None
    uptime_text: str | None = None


class CiscoSession(Protocol):
    def send_command(self, command: str) -> str: ...
    def disconnect(self) -> None: ...


class SessionFactory(Protocol):
    def __call__(self, **kwargs: Any) -> CiscoSession: ...


class HostKeyProbe(Protocol):
    def __call__(self, device: Device) -> tuple[paramiko.PKey, str]: ...


ALLOWED_SHOW_COMMANDS = {"show version", "show inventory", "show interfaces status", "show ip interface brief", "show vlan brief", "show cdp neighbors detail", "show lldp neighbors detail", "show running-config"}
REFRESH_COMMANDS = tuple(command for command in ALLOWED_SHOW_COMMANDS if command != "show running-config")


def fingerprint(key: paramiko.PKey) -> str:
    import base64
    return "SHA256:" + base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode("ascii").rstrip("=")


class FingerprintHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    def __init__(self, expected_fingerprint: str) -> None:
        self._expected_fingerprint = expected_fingerprint

    def missing_host_key(self, client: paramiko.SSHClient, hostname: str, key: paramiko.PKey) -> None:
        presented = fingerprint(key)
        if not secrets.compare_digest(self._expected_fingerprint, presented):
            raise CiscoConnectionError("SSH host key changed", "host_key_error", fingerprint=presented, algorithm=key.get_name())


class FingerprintVerifiedCiscoIosSSH(CiscoIosSSH):
    def __init__(self, *args: Any, expected_host_key_fingerprint: str, **kwargs: Any) -> None:
        self._expected_host_key_fingerprint = expected_host_key_fingerprint
        super().__init__(*args, **kwargs)

    def _build_ssh_client(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(FingerprintHostKeyPolicy(self._expected_host_key_fingerprint))
        return client

def _probe_host_key(device: Device) -> tuple[paramiko.PKey, str]:
    sock: socket.socket | None = None
    transport: paramiko.Transport | None = None
    try:
        sock = socket.create_connection((device.management_ip, device.ssh_port), timeout=10)
        transport = paramiko.Transport(sock)
        if device.ssh_profile == "cisco_legacy":
            options = transport.get_security_options()
            options.kex = ["diffie-hellman-group14-sha1", *[item for item in options.kex if item != "diffie-hellman-group14-sha1"]]
            options.key_types = ["ssh-rsa", *[item for item in options.key_types if item != "ssh-rsa"]]
        transport.start_client(timeout=10)
        key = transport.get_remote_server_key()
        algorithm = key.get_name()
        return key, algorithm
    except Exception as error:
        code = _error_code(error)
        logger.warning("SSH host-key probe failed code=%s error_type=%s", code, type(error).__name__)
        raise CiscoConnectionError(sanitize_exception(error), code) from error
    finally:
        if transport is not None:
            transport.close()
        if sock is not None:
            sock.close()


def sanitize_exception(error: BaseException) -> str:
    message = str(error).lower()
    if "host key" in message or "not a trusted" in message:
        return "SSH host key verification failed"
    if "authentication" in message or "auth" in message or "permission denied" in message:
        return "SSH authentication failed"
    if _is_algorithm_error(message):
        return "SSH algorithm negotiation failed"
    if "timeout" in message or "timed out" in message:
        return "SSH connection timed out"
    if "refused" in message:
        return "SSH connection refused"
    if "unreachable" in message or "no route" in message:
        return "SSH host is unreachable"
    return "SSH connection failed"


def _error_code(error: BaseException) -> str:
    message = str(error).lower()
    if "authentication" in message or "permission denied" in message or "auth" in message:
        return "authentication_failed"
    if _is_algorithm_error(message):
        return "algorithm_negotiation_failed"
    if "timeout" in message or "timed out" in message:
        return "connection_timeout"
    if "refused" in message:
        return "connection_refused"
    if "unreachable" in message or "no route" in message:
        return "host_unreachable"
    if "host key" in message or "trusted" in message:
        return "host_key_error"
    return "unknown_error"


def _is_algorithm_error(message: str) -> bool:
    return any(marker in message for marker in (
        "algorithm",
        "negotiation",
        "kex",
        "key exchange",
        "no matching",
        "incompatible ssh peer",
    ))


def _safe_type_error_detail(error: BaseException) -> str | None:
    """Expose only signature/type diagnostics; never log SSH payloads."""
    if not isinstance(error, TypeError):
        return None
    return " ".join(str(error).split())[:240] or None


def _netmiko_kwargs(device: Device, material: Any) -> dict[str, Any]:
    # Netmiko/Paramiko receives a key object, never a private-key path. Legacy
    # RSA authentication is enabled only for devices explicitly using the
    # cisco_legacy profile.
    disabled_algorithms = {"pubkeys": ["rsa-sha2-512", "rsa-sha2-256"]} if device.ssh_profile == "cisco_legacy" else {}
    return {"device_type": "cisco_ios", "host": device.management_ip, "username": material.username,
            "port": device.ssh_port, "pkey": material.key, "passphrase": material.passphrase,
            "use_keys": False, "allow_agent": False, "ssh_strict": True,
            "expected_host_key_fingerprint": device.trusted_host_key_fingerprint,
            "disabled_algorithms": disabled_algorithms,
            "conn_timeout": 10, "auth_timeout": 10, "banner_timeout": 10}


class CiscoConnectionService:
    def __init__(self, factory: SessionFactory = FingerprintVerifiedCiscoIosSSH, probe: HostKeyProbe = _probe_host_key) -> None:
        self._factory, self._probe = factory, probe

    def connect(self, device: Device, db: Session) -> CiscoSession:
        if device.ssh_credential_id is None:
            raise CiscoConnectionError("Device has no SSH credential", "authentication_failed")
        try:
            if device.trusted_host_key_fingerprint is None:
                host_key, algorithm = self._probe(device)
                current_fingerprint = fingerprint(host_key)
                raise CiscoConnectionError("SSH host key requires explicit trust", "host_key_error", fingerprint=current_fingerprint, algorithm=algorithm)
            material = get_material(db, vault_service, device.ssh_credential_id, device.ssh_profile)
            return self._factory(**_netmiko_kwargs(device, material))
        except CiscoConnectionError:
            raise
        except (CredentialError, VaultLockedError) as error:
            raise CiscoConnectionError("SSH credential is unavailable", "authentication_failed") from error
        except Exception as error:
            code = _error_code(error)
            detail = _safe_type_error_detail(error)
            logger.warning("Cisco connection failed device=%s code=%s error_type=%s%s", device.id, code, type(error).__name__, f" detail={detail}" if detail else "")
            raise CiscoConnectionError(sanitize_exception(error), code) from error

    def presented_host_key(self, device: Device) -> tuple[str, str]:
        key, algorithm = self._probe(device)
        return fingerprint(key), algorithm

    def test_connection(self, device: Device, db: Session) -> ConnectionResult:
        started = time.monotonic()
        session: CiscoSession | None = None
        try:
            session = self.connect(device, db)
            facts = parse_refresh({"show version": session.send_command("show version")}).facts
            return ConnectionResult(True, "SSH connection successful", facts.hostname or device.hostname, _duration_ms(started), model=facts.model or None, software_version=facts.software_version or None, uptime_text=facts.uptime or None)
        except CiscoConnectionError as error:
            host_key = {"fingerprint": error.fingerprint, "algorithm": error.algorithm} if error.fingerprint else None
            return ConnectionResult(False, str(error), device.hostname, _duration_ms(started), error.code, host_key)
        except Exception as error:
            return ConnectionResult(False, sanitize_exception(error), device.hostname, _duration_ms(started), _error_code(error))
        finally:
            if session is not None:
                try:
                    session.disconnect()
                except Exception:
                    logger.warning("Cisco disconnect failed device=%s", device.id)

    def show(self, device: Device, command: str, db: Session) -> str:
        normalized = " ".join(command.strip().lower().split())
        if normalized not in ALLOWED_SHOW_COMMANDS:
            raise CiscoConnectionError("Command is not in the safe show-command allowlist")
        session: CiscoSession | None = None
        try:
            session = self.connect(device, db)
            return session.send_command(normalized)
        except CiscoConnectionError:
            raise
        except Exception as error:
            raise CiscoConnectionError(sanitize_exception(error), _error_code(error)) from error
        finally:
            if session is not None:
                session.disconnect()

    def refresh(self, device: Device, db: Session) -> DeviceRefreshResponse:
        session: CiscoSession | None = None
        outputs: dict[str, str] = {}
        try:
            session = self.connect(device, db)
            for command in REFRESH_COMMANDS:
                outputs[command] = session.send_command(command)
            return parse_refresh(outputs)
        except CiscoConnectionError:
            raise
        except Exception as error:
            raise CiscoConnectionError(sanitize_exception(error), _error_code(error)) from error
        finally:
            if session is not None:
                session.disconnect()


def _duration_ms(started: float) -> int:
    return round((time.monotonic() - started) * 1000)
