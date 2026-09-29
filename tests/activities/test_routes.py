from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import ASSOCIATE_TOKEN, STORE_MANAGER_TOKEN, auth_header


def test_create_and_get_activity(client: TestClient) -> None:
    create_resp = client.post(
        "/api/activities",
        json={"title": "Restock aisle 4", "category": "RESTOCKING"},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    assert create_resp.status_code == 201
    task = create_resp.json()
    assert task["status"] == "TODO"
    assert task["category"] == "RESTOCKING"

    get_resp = client.get(f"/api/activities/{task['id']}", headers=auth_header(STORE_MANAGER_TOKEN))
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Restock aisle 4"


def test_list_activities_filters_by_status(client: TestClient) -> None:
    client.post(
        "/api/activities", json={"title": "A"}, headers=auth_header(STORE_MANAGER_TOKEN)
    )
    created = client.post(
        "/api/activities", json={"title": "B"}, headers=auth_header(STORE_MANAGER_TOKEN)
    ).json()
    client.patch(
        f"/api/activities/{created['id']}",
        json={"status": "DONE"},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )

    resp = client.get(
        "/api/activities", params={"status": "DONE"}, headers=auth_header(STORE_MANAGER_TOKEN)
    )
    assert resp.status_code == 200
    results = resp.json()
    assert all(t["status"] == "DONE" for t in results)
    assert any(t["id"] == created["id"] for t in results)


def test_get_activity_not_found(client: TestClient) -> None:
    resp = client.get("/api/activities/does-not-exist", headers=auth_header(STORE_MANAGER_TOKEN))
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


def test_delete_activity_requires_owner_or_manager(client: TestClient) -> None:
    created = client.post(
        "/api/activities",
        json={"title": "Owned by manager"},
        headers=auth_header(STORE_MANAGER_TOKEN),
    ).json()

    forbidden_resp = client.delete(
        f"/api/activities/{created['id']}", headers=auth_header(ASSOCIATE_TOKEN)
    )
    assert forbidden_resp.status_code == 403
    assert forbidden_resp.json()["code"] == "FORBIDDEN"

    allowed_resp = client.delete(
        f"/api/activities/{created['id']}", headers=auth_header(STORE_MANAGER_TOKEN)
    )
    assert allowed_resp.status_code == 204


def test_missing_auth_header_rejected(client: TestClient) -> None:
    resp = client.get("/api/activities")
    assert resp.status_code == 422  # FastAPI required-header validation
