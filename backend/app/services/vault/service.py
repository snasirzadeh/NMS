from __future__ import annotations

import secrets
from dataclasses import dataclass
from threading import RLock

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Admin, Vault

PASSWORD_TIME_COST = 3
PASSWORD_MEMORY_COST = 64 * 1024
PASSWORD_PARALLELISM = 4
PASSWORD_HASH_LENGTH = 32
PASSWORD_SALT_LENGTH = 16
VAULT_AAD = b"cisco-nms:vault-master-key:v1"
SECRET_AAD_PREFIX = b"cisco-nms:ssh-credential:v1:"


class VaultLockedError(RuntimeError):
    pass


@dataclass(frozen=True)
class KDFParameters:
    time_cost: int = PASSWORD_TIME_COST
    memory_cost: int = PASSWORD_MEMORY_COST
    parallelism: int = PASSWORD_PARALLELISM
    hash_len: int = PASSWORD_HASH_LENGTH


def hash_admin_password(password: str) -> str:
    return Argon2id(salt=secrets.token_bytes(PASSWORD_SALT_LENGTH), length=PASSWORD_HASH_LENGTH,
                    iterations=PASSWORD_TIME_COST, lanes=PASSWORD_PARALLELISM,
                    memory_cost=PASSWORD_MEMORY_COST).derive_phc_encoded(password.encode("utf-8"))


def verify_admin_password(password_hash: str, password: str) -> bool:
    try:
        Argon2id.verify_phc_encoded(password.encode("utf-8"), password_hash)
        return True
    except Exception:
        return False


def derive_kek(password: str, salt: bytes, parameters: KDFParameters) -> bytes:
    return Argon2id(salt=salt, length=parameters.hash_len, iterations=parameters.time_cost,
                    lanes=parameters.parallelism, memory_cost=parameters.memory_cost).derive(password.encode("utf-8"))


def _wrap(master_key: bytes, kek: bytes) -> tuple[bytes, bytes]:
    nonce = secrets.token_bytes(12)
    return AESGCM(kek).encrypt(nonce, master_key, VAULT_AAD), nonce


class VaultService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._master_key: bytearray | None = None

    @property
    def locked(self) -> bool:
        with self._lock:
            return self._master_key is None

    def initialize_vault(self, db: Session, admin: Admin, password: str) -> Vault:
        parameters = KDFParameters()
        salt = secrets.token_bytes(PASSWORD_SALT_LENGTH)
        master_key = secrets.token_bytes(32)
        wrapped, nonce = _wrap(master_key, derive_kek(password, salt, parameters))
        vault = Vault(admin_id=admin.id, wrapped_vault_key=wrapped, wrapped_vault_key_nonce=nonce,
                      kdf_salt=salt, kdf_time_cost=parameters.time_cost, kdf_memory_cost=parameters.memory_cost,
                      kdf_parallelism=parameters.parallelism, kdf_hash_len=parameters.hash_len)
        db.add(vault)
        return vault

    def unlock_vault(self, db: Session, admin: Admin, password: str) -> None:
        vault = db.scalar(select(Vault).where(Vault.admin_id == admin.id))
        if vault is None:
            raise VaultLockedError("Vault is not initialized")
        parameters = KDFParameters(vault.kdf_time_cost, vault.kdf_memory_cost, vault.kdf_parallelism, vault.kdf_hash_len)
        kek = derive_kek(password, vault.kdf_salt, parameters)
        try:
            master_key = AESGCM(kek).decrypt(vault.wrapped_vault_key_nonce, vault.wrapped_vault_key, VAULT_AAD)
        except Exception as error:
            raise VaultLockedError("Vault could not be unlocked") from error
        with self._lock:
            self._clear_key_locked()
            self._master_key = bytearray(master_key)

    def lock_vault(self) -> None:
        with self._lock:
            self._clear_key_locked()

    def _clear_key_locked(self) -> None:
        if self._master_key is not None:
            for index in range(len(self._master_key)):
                self._master_key[index] = 0
        self._master_key = None

    def _key(self) -> bytes:
        with self._lock:
            if self._master_key is None:
                raise VaultLockedError("Vault is locked")
            return bytes(self._master_key)

    def encrypt_secret(self, plaintext: bytes, *, credential_id: int, field: str) -> tuple[bytes, bytes]:
        nonce = secrets.token_bytes(12)
        aad = SECRET_AAD_PREFIX + f"{credential_id}:{field}".encode("ascii")
        return AESGCM(self._key()).encrypt(nonce, plaintext, aad), nonce

    def decrypt_secret(self, ciphertext: bytes, nonce: bytes, *, credential_id: int, field: str) -> bytes:
        aad = SECRET_AAD_PREFIX + f"{credential_id}:{field}".encode("ascii")
        return AESGCM(self._key()).decrypt(nonce, ciphertext, aad)

    def rotate_admin_password(self, db: Session, admin: Admin, old_password: str, new_password: str) -> None:
        vault = db.scalar(select(Vault).where(Vault.admin_id == admin.id))
        if vault is None:
            raise VaultLockedError("Vault is not initialized")
        parameters = KDFParameters(vault.kdf_time_cost, vault.kdf_memory_cost, vault.kdf_parallelism, vault.kdf_hash_len)
        old_kek = derive_kek(old_password, vault.kdf_salt, parameters)
        try:
            master_key = AESGCM(old_kek).decrypt(vault.wrapped_vault_key_nonce, vault.wrapped_vault_key, VAULT_AAD)
        except Exception as error:
            raise VaultLockedError("Vault could not be unlocked") from error
        new_salt = secrets.token_bytes(PASSWORD_SALT_LENGTH)
        wrapped, nonce = _wrap(master_key, derive_kek(new_password, new_salt, parameters))
        vault.wrapped_vault_key = wrapped
        vault.wrapped_vault_key_nonce = nonce
        vault.kdf_salt = new_salt
        with self._lock:
            self._clear_key_locked()
            self._master_key = bytearray(master_key)


vault_service = VaultService()
