from __future__ import annotations

from fastapi.testclient import TestClient

from app.shared.event_bus import event_bus
from tests.conftest import STORE_MANAGER_TOKEN, auth_header


def test_list_alerts_empty_by_default(client: TestClient) -> None:
    resp = client.get("/api/alerts", headers=auth_header(STORE_MANAGER_TOKEN))
    assert resp.status_code == 200
    assert resp.json() == []


def test_alert_created_via_event_bus_is_listed(client: TestClient) -> None:
    event_bus.emit(
        "notification.requested",
        {
            "alert_type": "SLA_BREACH",
            "recipient_id": "user-1",
            "store_id": "store-1",
            "message": "Task task-1 breached its SLA",
        },
    )
    resp = client.get("/api/alerts", headers=auth_header(STORE_MANAGER_TOKEN))
    assert resp.status_code == 200
    messages = [n["message"] for n in resp.json()]
    assert "Task task-1 breached its SLA" in messages
