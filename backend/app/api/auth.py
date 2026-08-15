from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated
from app.core.config import get_settings
from app.database.session import get_db
from app.models import Admin, AuthSession
from app.schemas.auth import LoginRequest, PasswordChangeRequest, SessionRead, SetupRequest, SetupStatus
from app.services.auth import AuthenticationError, SetupConflictError, authenticate_admin, create_session, get_admin, setup_admin, verify_session
from app.services.vault import VaultLockedError, hash_admin_password, vault_service, verify_admin_password

router = APIRouter(prefix="/auth", tags=["auth"])
_attempts: dict[str, deque[float]] = defaultdict(deque)
_attempt_lock = Lock()


def _allow_attempt(key: str) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    with _attempt_lock:
        bucket = _attempts[key]
        while bucket and bucket[0] < now - 900:
            bucket.popleft()
        if len(bucket) >= 8:
            return False
        bucket.append(now)
        return True


def _cookie(response: Response, token: str, csrf: str) -> None:
    settings = get_settings()
    response.set_cookie(settings.session_cookie_name, token, httponly=True, secure=settings.secure_cookies, samesite="lax", max_age=settings.session_ttl_hours * 3600, path="/")
    response.set_cookie(settings.csrf_cookie_name, csrf, httponly=False, secure=settings.secure_cookies, samesite="lax", max_age=settings.session_ttl_hours * 3600, path="/")


@router.get("/setup/status", response_model=SetupStatus)
def setup_status(db: Session = Depends(get_db)) -> SetupStatus:
    return SetupStatus(configured=get_admin(db) is not None)


@router.post("/setup", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def setup(payload: SetupRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> SessionRead:
    if payload.password != payload.password_confirmation:
        raise HTTPException(status_code=422, detail="Passwords do not match")
    if not _allow_attempt(request.client.host if request.client else "unknown"):
        raise HTTPException(status_code=429, detail="Too many setup attempts")
    try:
        admin = setup_admin(db, payload.username, payload.password)
        session, token, csrf = create_session(db, admin)
        _cookie(response, token, csrf)
        return SessionRead(authenticated=True, configured=True, username=admin.username, csrf_token=csrf, expires_at=session.expires_at)
    except SetupConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/login", response_model=SessionRead)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> SessionRead:
    if not _allow_attempt(request.client.host if request.client else "unknown"):
        raise HTTPException(status_code=429, detail="Too many authentication attempts")
    try:
        admin = authenticate_admin(db, payload.username, payload.password)
        session, token, csrf = create_session(db, admin)
        _cookie(response, token, csrf)
        return SessionRead(authenticated=True, configured=True, username=admin.username, csrf_token=csrf, expires_at=session.expires_at)
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail="Invalid username or password") from error


@router.get("/session", response_model=SessionRead)
def session_status(request: Request, db: Session = Depends(get_db)) -> SessionRead:
    admin = get_admin(db)
    if admin is None:
        return SessionRead(authenticated=False, configured=False)
    try:
        current, session = verify_session(db, request.cookies.get(get_settings().session_cookie_name), request.cookies.get(get_settings().csrf_cookie_name))
        if vault_service.locked:
            raise AuthenticationError("Authentication required")
        return SessionRead(authenticated=True, configured=True, username=current.username, csrf_token=request.cookies.get(get_settings().csrf_cookie_name), expires_at=session.expires_at)
    except AuthenticationError:
        return SessionRead(authenticated=False, configured=True)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> Response:
    token = request.cookies.get(get_settings().session_cookie_name)
    try:
        _, session = verify_session(db, token, request.headers.get("X-CSRF-Token"), require_csrf=True)
        db.delete(session)
        db.commit()
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    vault_service.lock_vault()
    response.delete_cookie(get_settings().session_cookie_name, path="/")
    response.delete_cookie(get_settings().csrf_cookie_name, path="/")
    return response


@router.post("/password", response_model=SessionRead)
def change_password(payload: PasswordChangeRequest, request: Request, response: Response, admin: Admin = Depends(require_authenticated), db: Session = Depends(get_db)) -> SessionRead:
    if payload.new_password != payload.new_password_confirmation:
        raise HTTPException(status_code=422, detail="Passwords do not match")
    if not verify_admin_password(admin.password_hash, payload.current_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    try:
        vault_service.rotate_admin_password(db, admin, payload.current_password, payload.new_password)
        admin.password_hash = hash_admin_password(payload.new_password)
        db.execute(delete(AuthSession).where(AuthSession.admin_id == admin.id))
        db.commit()
    except VaultLockedError as error:
        raise HTTPException(status_code=401, detail="Current password is incorrect") from error
    session, token, csrf = create_session(db, admin)
    _cookie(response, token, csrf)
    return SessionRead(authenticated=True, configured=True, username=admin.username, csrf_token=csrf, expires_at=session.expires_at)
