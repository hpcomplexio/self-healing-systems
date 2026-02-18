from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import UNHEALTHY_MARKER, app


@pytest.fixture(autouse=True)
def reset_health_marker() -> None:
    if UNHEALTHY_MARKER.exists():
        UNHEALTHY_MARKER.unlink()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
