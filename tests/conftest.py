from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.activities.repository import activity_repository
from app.alerts.repository import alert_repository
from app.main import app
from app.programmes.repository import programme_repository

STORE_MANAGER_TOKEN = "dev-token-store-manager"
ASSOCIATE_TOKEN = "dev-token-associate"
DEPARTMENT_LEAD_TOKEN = "dev-token-department-lead"


@pytest.fixture(autouse=True)
def _reset_module_state() -> None:
    """Each module's repository is a process-wide singleton (see app-context/SKILL.md),
    so tests across different files share state unless it's reset here. staff is not
    reset — its seed users/tokens are read-only fixtures every test relies on.
    """
    activity_repository._tasks.clear()
    activity_repository._next_id = 1
    alert_repository._notifications.clear()
    alert_repository._next_id = 1
    programme_repository._projects.clear()
    programme_repository._members.clear()
    programme_repository._next_id = 1


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
