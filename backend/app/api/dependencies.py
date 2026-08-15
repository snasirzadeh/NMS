from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.config import get_settings
from app.models import Admin
from app.services.auth import AuthenticationError, verify_session
from app.services.vault import vault_service


def require_authenticated(request: Request, db: Session = Depends(get_db)) -> Admin:
    try:
        admin, _ = verify_session(db, request.cookies.get(get_settings().session_cookie_name), request.headers.get("X-CSRF-Token"), require_csrf=request.method not in {"GET", "HEAD", "OPTIONS"})
        if vault_service.locked:
            raise AuthenticationError("Authentication required")
        return admin
    except AuthenticationError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error), headers={"WWW-Authenticate": "Session"}) from error
