from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from threading import Lock

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Admin, AuthSession
from app.services.vault import VaultLockedError, hash_admin_password, verify_admin_password, vault_service


class AuthenticationError(RuntimeError):
    pass


class SetupConflictError(RuntimeError):
    pass


_setup_lock = Lock()


def setup_admin(db: Session, username: str, password: str) -> Admin:
    with _setup_lock:
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(914731)"))
        if db.scalar(select(Admin).limit(1)) is not None:
            raise SetupConflictError("Administrator setup is already complete")
        admin = Admin(username=username, password_hash=hash_admin_password(password))
        db.add(admin)
        db.flush()
        vault_service.initialize_vault(db, admin, password)
        db.commit()
        db.refresh(admin)
        vault_service.unlock_vault(db, admin, password)
        return admin


def get_admin(db: Session) -> Admin | None:
    return db.scalar(select(Admin).order_by(Admin.id).limit(1))


def authenticate_admin(db: Session, username: str, password: str) -> Admin:
    admin = db.scalar(select(Admin).where(Admin.username == username))
    if admin is None or not verify_admin_password(admin.password_hash, password):
        raise AuthenticationError("Invalid username or password")
    try:
        vault_service.unlock_vault(db, admin, password)
    except VaultLockedError as error:
        raise AuthenticationError("Invalid username or password") from error
    return admin


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, admin: Admin) -> tuple[AuthSession, str, str]:
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    session = AuthSession(admin_id=admin.id, token_hash=_hash_token(token), csrf_token_hash=_hash_token(csrf_token),
                          expires_at=now + timedelta(hours=get_settings().session_ttl_hours), last_seen_at=now)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, token, csrf_token


def verify_session(db: Session, token: str | None, csrf_token: str | None, *, require_csrf: bool = False) -> tuple[Admin, AuthSession]:
    if not token:
        raise AuthenticationError("Authentication required")
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == _hash_token(token)))
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at if session is not None else now
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if session is None or expires_at <= now:
        raise AuthenticationError("Authentication required")
    if require_csrf and (not csrf_token or not secrets.compare_digest(session.csrf_token_hash, _hash_token(csrf_token))):
        raise AuthenticationError("CSRF validation failed")
    admin = db.get(Admin, session.admin_id)
    if admin is None:
        raise AuthenticationError("Authentication required")
    session.last_seen_at = now
    return admin, session
