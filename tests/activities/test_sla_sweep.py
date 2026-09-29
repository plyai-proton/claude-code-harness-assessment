from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient

from app.activities.repository import activity_repository
from tests.conftest import STORE_MANAGER_TOKEN, auth_header

# Repository reset between tests is handled by tests/conftest.py's autouse
# _reset_module_state fixture.


def _create_task(
    client: TestClient, *, priority: str, status: str | None, due_at: datetime | None
) -> dict[str, Any]:
    payload: dict[str, Any] = {"title": "SLA test task", "priority": priority}
    if due_at is not None:
        payload["due_at"] = due_at.isoformat()
    created = client.post(
        "/api/activities", json=payload, headers=auth_header(STORE_MANAGER_TOKEN)
    ).json()
    if status is not None and status != "TODO":
        client.patch(
            f"/api/activities/{created['id']}",
            json={"status": status},
            headers=auth_header(STORE_MANAGER_TOKEN),
        )
        created = client.get(
            f"/api/activities/{created['id']}", headers=auth_header(STORE_MANAGER_TOKEN)
        ).json()
    return created


def test_ac1_breach_detected_and_notified(client: TestClient) -> None:
    past = datetime.now(UTC) - timedelta(hours=2)
    task = _create_task(client, priority="CRITICAL", status=None, due_at=past)

    resp = client.post("/api/activities/sla-sweep", headers=auth_header(STORE_MANAGER_TOKEN))
    assert resp.status_code == 200
    result = resp.json()
    assert task["id"] in result["breached"]
    assert task["id"] not in result["escalated"]

    updated = client.get(
        f"/api/activities/{task['id']}", headers=auth_header(STORE_MANAGER_TOKEN)
    ).json()
    assert updated["sla_notified_at"] is not None

    alerts = client.get("/api/alerts", headers=auth_header(STORE_MANAGER_TOKEN)).json()
    matching = [
        a for a in alerts if a["type"] == "SLA_BREACH" and a["related_entity_id"] == task["id"]
    ]
    assert len(matching) == 1
    assert matching[0]["recipient_id"] == "user-1"  # falls back to owner: unassigned task


def test_ac2_priority_filter_honored(client: TestClient) -> None:
    past = datetime.now(UTC) - timedelta(hours=2)
    task = _create_task(client, priority="LOW", status=None, due_at=past)

    resp = client.post("/api/activities/sla-sweep", headers=auth_header(STORE_MANAGER_TOKEN))
    result = resp.json()
    assert task["id"] not in result["breached"]
    assert task["id"] not in result["escalated"]


def test_ac3_done_tasks_never_breach(client: TestClient) -> None:
    past = datetime.now(UTC) - timedelta(hours=2)
    task = _create_task(client, priority="HIGH", status="DONE", due_at=past)

    resp = client.post("/api/activities/sla-sweep", headers=auth_header(STORE_MANAGER_TOKEN))
    result = resp.json()
    assert task["id"] not in result["breached"]
    assert task["id"] not in result["escalated"]


def test_ac4_escalation_after_grace_period(client: TestClient) -> None:
    task = _create_task(
        client, priority="HIGH", status=None, due_at=datetime.now(UTC) - timedelta(hours=3)
    )
    stored = activity_repository.get(task["id"])
    assert stored is not None
    stored.sla_notified_at = datetime.now(UTC) - timedelta(minutes=90)
    activity_repository.update(stored)

    resp = client.post(
        "/api/activities/sla-sweep",
        params={"grace_period_minutes": 60},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    result = resp.json()
    assert task["id"] in result["escalated"]
    assert task["id"] not in result["breached"]

    alerts = client.get("/api/alerts", headers=auth_header(STORE_MANAGER_TOKEN)).json()
    escalations = [
        a for a in alerts if a["type"] == "ESCALATION" and a["related_entity_id"] == task["id"]
    ]
    assert len(escalations) == 1
    assert escalations[0]["recipient_id"] == "user-1"  # seeded STORE_MANAGER


def test_ac5_grace_period_honored(client: TestClient) -> None:
    task = _create_task(
        client, priority="HIGH", status=None, due_at=datetime.now(UTC) - timedelta(hours=3)
    )
    stored = activity_repository.get(task["id"])
    assert stored is not None
    stored.sla_notified_at = datetime.now(UTC) - timedelta(minutes=10)
    activity_repository.update(stored)

    resp = client.post(
        "/api/activities/sla-sweep",
        params={"grace_period_minutes": 60},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    result = resp.json()
    assert task["id"] not in result["escalated"]
    assert task["id"] not in result["breached"]


def test_ac6_idempotent_rerun_after_escalation(client: TestClient) -> None:
    task = _create_task(
        client, priority="CRITICAL", status=None, due_at=datetime.now(UTC) - timedelta(hours=3)
    )
    stored = activity_repository.get(task["id"])
    assert stored is not None
    stored.sla_notified_at = datetime.now(UTC) - timedelta(minutes=90)
    stored.sla_escalated_at = datetime.now(UTC) - timedelta(minutes=30)
    activity_repository.update(stored)

    resp = client.post(
        "/api/activities/sla-sweep",
        params={"grace_period_minutes": 60},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    result = resp.json()
    assert task["id"] not in result["breached"]
    assert task["id"] not in result["escalated"]


def test_ac6_invalid_grace_period_raises_validation_error(client: TestClient) -> None:
    resp = client.post(
        "/api/activities/sla-sweep",
        params={"grace_period_minutes": 0},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"
