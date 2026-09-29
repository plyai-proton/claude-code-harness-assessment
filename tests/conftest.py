from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app

STORE_MANAGER_TOKEN = "dev-token-store-manager"
ASSOCIATE_TOKEN = "dev-token-associate"
DEPARTMENT_LEAD_TOKEN = "dev-token-department-lead"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
