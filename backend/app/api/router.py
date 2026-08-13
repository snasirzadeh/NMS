from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["system"])
def api_health() -> dict[str, str]:
    return {"status": "ok"}
