from collections.abc import Callable
from typing import Any

from fastapi.routing import APIRoute

from app.api.router import router as api_router
from app.main import app


def endpoint_for(path: str) -> Callable[[], Any]:
    route = next(route for route in app.routes if isinstance(route, APIRoute) and route.path == path)
    return route.endpoint


def test_health() -> None:
    assert endpoint_for("/health")() == {"status": "ok"}


def test_versioned_api_health() -> None:
    route = next(route for route in api_router.routes if isinstance(route, APIRoute) and route.path == "/health")

    assert route.endpoint() == {"status": "ok"}
