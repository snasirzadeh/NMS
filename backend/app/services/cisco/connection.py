from collections.abc import Mapping
from dataclasses import dataclass
import logging
from typing import Any, Protocol

from netmiko import ConnectHandler

from app.services.ssh import SSHConfigError, SSHConfigPreview, parse_ssh_config

logger = logging.getLogger(__name__)


class CiscoConnectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConnectionResult:
    success: bool
    message: str
    hostname: str
    duration_ms: int


class CiscoSession(Protocol):
    def send_command(self, command: str) -> str: ...
    def disconnect(self) -> None: ...


class SessionFactory(Protocol):
    def __call__(self, **kwargs: Any) -> CiscoSession: ...


ALLOWED_SHOW_COMMANDS = {
    "show version",
    "show inventory",
    "show interfaces status",
    "show ip interface brief",
    "show vlan brief",
    "show cdp neighbors detail",
    "show lldp neighbors detail",
    "show running-config",
}


def sanitize_exception(error: BaseException) -> str:
    message = str(error).lower()
    if "authentication" in message or "auth" in message or "permission denied" in message:
        return "SSH authentication failed"
    if "negotiation" in message or "algorithm" in message or "kex" in message:
        return "SSH negotiation failed"
    if "timeout" in message or "timed out" in message:
        return "SSH connection timed out"
    if "refused" in message or "unreachable" in message or "no route" in message:
        return "SSH device is unreachable"
    return "SSH connection failed"


def _netmiko_kwargs(preview: SSHConfigPreview) -> dict[str, Any]:
    # Netmiko passes these values to Paramiko. The algorithm strings are kept
    # in the connection specification for the adapter and future compatibility.
    return {
        "device_type": "cisco_ios",
        "host": preview.hostname,
        "username": preview.user,
        "port": preview.port,
        "use_keys": True,
        "key_file": preview.identity_file,
        "allow_agent": False,
        "look_for_keys": False,
        "conn_timeout": 10,
        "auth_timeout": 10,
        "banner_timeout": 10,
    }


class CiscoConnectionService:
    def __init__(self, factory: SessionFactory = ConnectHandler) -> None:
        self._factory = factory

    def parse_effective_config(self, config_text: str, *, require_key: bool = True) -> SSHConfigPreview:
        try:
            return parse_ssh_config(config_text, require_identity_file=require_key)
        except SSHConfigError as error:
            raise CiscoConnectionError(str(error)) from error

    def connect(self, config_text: str) -> CiscoSession:
        preview = self.parse_effective_config(config_text)
        try:
            return self._factory(**_netmiko_kwargs(preview))
        except Exception as error:
            logger.warning("Cisco connection failed host=%s reason=%s", preview.hostname, sanitize_exception(error))
            raise CiscoConnectionError(sanitize_exception(error)) from error

    def test_connection(self, config_text: str) -> ConnectionResult:
        import time

        started = time.monotonic()
        try:
            preview = self.parse_effective_config(config_text)
        except CiscoConnectionError as error:
            return ConnectionResult(False, str(error), "unknown", _duration_ms(started))
        session: CiscoSession | None = None
        try:
            session = self.connect(config_text)
            return ConnectionResult(True, "SSH connection successful", preview.hostname, _duration_ms(started))
        except CiscoConnectionError as error:
            return ConnectionResult(False, str(error), preview.hostname, _duration_ms(started))
        finally:
            if session is not None:
                try:
                    session.disconnect()
                except Exception:
                    logger.warning("Cisco disconnect failed host=%s", preview.hostname)

    def show(self, config_text: str, command: str) -> str:
        normalized = " ".join(command.strip().lower().split())
        if normalized not in ALLOWED_SHOW_COMMANDS:
            raise CiscoConnectionError("Command is not in the safe show-command allowlist")
        session: CiscoSession | None = None
        try:
            session = self.connect(config_text)
            return session.send_command(normalized)
        except CiscoConnectionError:
            raise
        except Exception as error:
            raise CiscoConnectionError(sanitize_exception(error)) from error
        finally:
            if session is not None:
                try:
                    session.disconnect()
                except Exception:
                    logger.warning("Cisco disconnect failed after show command")


def _duration_ms(started: float) -> int:
    import time

    return round((time.monotonic() - started) * 1000)
