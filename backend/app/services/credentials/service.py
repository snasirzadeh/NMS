from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
import base64
import hashlib

import paramiko
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import SSHCredential
from app.services.vault import VaultService


class CredentialError(ValueError):
    pass


class CredentialInUseError(CredentialError):
    pass


@dataclass(frozen=True)
class ParsedKey:
    key: paramiko.PKey
    key_type: str
    key_bits: int | None
    fingerprint: str


@dataclass(frozen=True)
class CredentialMaterial:
    username: str
    key: paramiko.PKey
    passphrase: str | None
    key_type: str
    profile: str


def _fingerprint(key: paramiko.PKey) -> str:
    encoded = base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode("ascii").rstrip("=")
    return f"SHA256:{encoded}"


def parse_private_key(private_key: str, passphrase: str | None) -> ParsedKey:
    if not private_key.strip() or len(private_key) > 128 * 1024:
        raise CredentialError("Private key is empty or too large")
    constructors = [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey]
    dss_key = getattr(paramiko, "DSSKey", None)
    if dss_key is not None:
        constructors.append(dss_key)
    for constructor in constructors:
        try:
            key = constructor.from_private_key(StringIO(private_key), password=passphrase or None)
            return ParsedKey(key, key.get_name().replace("ssh-", "").upper(), key.get_bits(), _fingerprint(key))
        except (paramiko.SSHException, ValueError, TypeError):
            continue
    raise CredentialError("Private key could not be parsed or the passphrase is incorrect")


def _text(value: str, field: str) -> str:
    if not value.strip() or "\x00" in value:
        raise CredentialError(f"{field} is invalid")
    return value.strip()


def create_credential(db: Session, vault: VaultService, *, name: str, username: str, private_key: str, passphrase: str | None) -> SSHCredential:
    name, username = _text(name, "Credential name"), _text(username, "Username")
    parsed = parse_private_key(private_key, passphrase)
    credential = SSHCredential(name=name, username=username, encrypted_private_key=b"pending", private_key_nonce=b"pending",
                               key_type=parsed.key_type, key_bits=parsed.key_bits, key_fingerprint=parsed.fingerprint,
                               public_key_fingerprint=parsed.fingerprint)
    db.add(credential)
    db.flush()
    credential.encrypted_private_key, credential.private_key_nonce = vault.encrypt_secret(private_key.encode(), credential_id=credential.id, field="private-key")
    if passphrase:
        credential.encrypted_passphrase, credential.passphrase_nonce = vault.encrypt_secret(passphrase.encode(), credential_id=credential.id, field="passphrase")
    db.commit()
    db.refresh(credential)
    return credential


def replace_credential(db: Session, vault: VaultService, credential: SSHCredential, *, private_key: str, passphrase: str | None) -> SSHCredential:
    parsed = parse_private_key(private_key, passphrase)
    credential.encrypted_private_key, credential.private_key_nonce = vault.encrypt_secret(private_key.encode(), credential_id=credential.id, field="private-key")
    credential.encrypted_passphrase = credential.passphrase_nonce = None
    if passphrase:
        credential.encrypted_passphrase, credential.passphrase_nonce = vault.encrypt_secret(passphrase.encode(), credential_id=credential.id, field="passphrase")
    credential.key_type, credential.key_bits, credential.key_fingerprint = parsed.key_type, parsed.key_bits, parsed.fingerprint
    credential.public_key_fingerprint = parsed.fingerprint
    db.commit()
    db.refresh(credential)
    return credential


def get_material(db: Session, vault: VaultService, credential_id: int, profile: str) -> CredentialMaterial:
    credential = db.get(SSHCredential, credential_id)
    if credential is None:
        raise CredentialError("SSH credential not found")
    private_key = vault.decrypt_secret(credential.encrypted_private_key, credential.private_key_nonce, credential_id=credential.id, field="private-key").decode()
    passphrase = None
    if credential.encrypted_passphrase and credential.passphrase_nonce:
        passphrase = vault.decrypt_secret(credential.encrypted_passphrase, credential.passphrase_nonce, credential_id=credential.id, field="passphrase").decode()
    parsed = parse_private_key(private_key, passphrase)
    return CredentialMaterial(credential.username, parsed.key, passphrase, parsed.key_type, profile)


def credential_with_usage(db: Session) -> list[SSHCredential]:
    return list(db.scalars(select(SSHCredential).options(selectinload(SSHCredential.devices)).order_by(SSHCredential.name, SSHCredential.id)).all())


def delete_credential(db: Session, credential: SSHCredential) -> None:
    if credential.devices:
        names = ", ".join(device.display_name for device in credential.devices[:10])
        raise CredentialInUseError(f"This credential is used by {len(credential.devices)} device(s): {names}. Replace it on those devices first")
    db.delete(credential)
    db.commit()
