from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import STORE_MANAGER_TOKEN, auth_header


def test_create_programme_and_add_member(client: TestClient) -> None:
    create_resp = client.post(
        "/api/programmes",
        json={"name": "Spring reset"},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    assert create_resp.status_code == 201
    programme = create_resp.json()

    member_resp = client.post(
        f"/api/programmes/{programme['id']}/members",
        json={"user_id": "user-2", "role": "ASSOCIATE"},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    assert member_resp.status_code == 201
    assert member_resp.json()["user_id"] == "user-2"

    list_resp = client.get("/api/programmes", headers=auth_header(STORE_MANAGER_TOKEN))
    assert list_resp.status_code == 200
    assert any(p["id"] == programme["id"] for p in list_resp.json())


def test_add_member_to_unknown_programme_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/api/programmes/does-not-exist/members",
        json={"user_id": "user-2", "role": "ASSOCIATE"},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    assert resp.status_code == 404


def test_add_unknown_user_as_member_returns_validation_error(client: TestClient) -> None:
    programme = client.post(
        "/api/programmes", json={"name": "P"}, headers=auth_header(STORE_MANAGER_TOKEN)
    ).json()
    resp = client.post(
        f"/api/programmes/{programme['id']}/members",
        json={"user_id": "ghost", "role": "ASSOCIATE"},
        headers=auth_header(STORE_MANAGER_TOKEN),
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"
