from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.credentials import router as credentials_router
from app.api.router import router as api_router
from app.api.devices import router as devices_router
from app.api.backups import router as backups_router
from app.api.groups import router as groups_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    from app.services.vault import vault_service
    vault_service.lock_vault()


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(credentials_router, prefix="/api/v1")
app.include_router(groups_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(backups_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
