from io import StringIO

import paramiko
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.credentials import _read
from app.database.base import Base
from app.models import Admin, Device, Group, SSHCredential, Vault
from app.services.auth import AuthenticationError, SetupConflictError, authenticate_admin, create_session, setup_admin, verify_session
from app.services.credentials import CredentialInUseError, create_credential, delete_credential, replace_credential
from app.services.vault import VaultLockedError, VaultService, hash_admin_password, vault_service, verify_admin_password


PASSWORD = "Correct-Horse-42"
NEW_PASSWORD = "New-Correct-Horse-43"


def private_key(password: str | None = None) -> str:
    key = paramiko.RSAKey.generate(1024)
    output = StringIO()
    key.write_private_key(output, password=password)
    return output.getvalue()


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def initialized_vault(db: Session) -> tuple[Admin, VaultService]:
    admin = Admin(username="admin", password_hash=hash_admin_password(PASSWORD))
    db.add(admin)
    db.flush()
    vault = VaultService()
    vault.initialize_vault(db, admin, PASSWORD)
    db.commit()
    vault.unlock_vault(db, admin, PASSWORD)
    return admin, vault


def test_first_setup_is_atomic_one_time_and_password_is_argon2id(db: Session) -> None:
    vault_service.lock_vault()
    admin = setup_admin(db, "admin", PASSWORD)
    assert admin.password_hash.startswith("$argon2id$")
    assert PASSWORD not in admin.password_hash
    assert verify_admin_password(admin.password_hash, PASSWORD)
    assert db.query(Vault).count() == 1
    assert vault_service.locked is False
    with pytest.raises(SetupConflictError):
        setup_admin(db, "second", PASSWORD)
    vault_service.lock_vault()


def test_login_uses_server_side_hashed_session_and_csrf(db: Session) -> None:
    vault_service.lock_vault()
    admin = setup_admin(db, "admin", PASSWORD)
    vault_service.lock_vault()
    with pytest.raises(AuthenticationError):
        authenticate_admin(db, "admin", "Wrong-Password-99")
    authenticated = authenticate_admin(db, "admin", PASSWORD)
    session, token, csrf = create_session(db, authenticated)
    assert session.token_hash != token and session.csrf_token_hash != csrf
    assert verify_session(db, token, csrf, require_csrf=True)[0].id == admin.id
    with pytest.raises(AuthenticationError, match="CSRF"):
        verify_session(db, token, "wrong", require_csrf=True)
    vault_service.lock_vault()


def test_vault_unlock_encryption_random_nonces_and_wrong_password(db: Session) -> None:
    admin, vault = initialized_vault(db)
    vault.lock_vault()
    with pytest.raises(VaultLockedError):
        vault.unlock_vault(db, admin, "Wrong-Password-99")
    vault.unlock_vault(db, admin, PASSWORD)
    first, nonce_one = vault.encrypt_secret(b"secret", credential_id=1, field="private-key")
    second, nonce_two = vault.encrypt_secret(b"secret", credential_id=1, field="private-key")
    assert nonce_one != nonce_two and first != second
    assert vault.decrypt_secret(first, nonce_one, credential_id=1, field="private-key") == b"secret"


def test_password_rotation_rewraps_vault_and_preserves_credentials(db: Session) -> None:
    admin, vault = initialized_vault(db)
    credential = create_credential(db, vault, name="Core RSA", username="cisco", private_key=private_key(), passphrase=None)
    ciphertext = credential.encrypted_private_key
    old_wrapped = admin.vault.wrapped_vault_key
    vault.rotate_admin_password(db, admin, PASSWORD, NEW_PASSWORD)
    admin.password_hash = hash_admin_password(NEW_PASSWORD)
    db.commit()
    assert admin.vault.wrapped_vault_key != old_wrapped
    assert credential.encrypted_private_key == ciphertext
    vault.lock_vault()
    with pytest.raises(VaultLockedError):
        vault.unlock_vault(db, admin, PASSWORD)
    vault.unlock_vault(db, admin, NEW_PASSWORD)
    assert vault.decrypt_secret(credential.encrypted_private_key, credential.private_key_nonce, credential_id=credential.id, field="private-key").startswith(b"-----BEGIN")


def test_credential_create_replace_and_response_redaction(db: Session) -> None:
    _, vault = initialized_vault(db)
    original = private_key()
    credential = create_credential(db, vault, name="Cisco Legacy RSA", username="cisco", private_key=original, passphrase=None)
    assert original.encode() not in credential.encrypted_private_key
    response = _read(credential).model_dump()
    forbidden = {"encrypted_private_key", "private_key_nonce", "encrypted_passphrase", "passphrase_nonce", "passphrase"}
    assert forbidden.isdisjoint(response)
    old_nonce, old_fingerprint = credential.private_key_nonce, credential.key_fingerprint
    replace_credential(db, vault, credential, private_key=private_key(), passphrase=None)
    assert credential.private_key_nonce != old_nonce
    assert credential.key_fingerprint != old_fingerprint


def test_credential_passphrase_is_encrypted_and_never_serialized(db: Session) -> None:
    _, vault = initialized_vault(db)
    secret = "Key-Passphrase-77"
    credential = create_credential(db, vault, name="Encrypted Key", username="cisco", private_key=private_key(secret), passphrase=secret)
    assert credential.encrypted_passphrase is not None
    assert secret.encode() not in credential.encrypted_passphrase
    assert "passphrase" not in _read(credential).model_dump()


def test_delete_unused_and_reject_referenced_credential(db: Session) -> None:
    _, vault = initialized_vault(db)
    unused = create_credential(db, vault, name="Unused", username="cisco", private_key=private_key(), passphrase=None)
    delete_credential(db, unused)
    assert db.get(SSHCredential, unused.id) is None
    used = create_credential(db, vault, name="Used", username="cisco", private_key=private_key(), passphrase=None)
    group = Group(name="Lab")
    db.add(group); db.flush()
    db.add(Device(group_id=group.id, display_name="SW-CORE-01", hostname="sw-core-01", management_ip="192.0.2.10", ssh_credential_id=used.id))
    db.commit(); db.refresh(used)
    with pytest.raises(CredentialInUseError, match="SW-CORE-01"):
        delete_credential(db, used)
