from datetime import datetime, timedelta, timezone
import logging

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_sessions():
    app_module.active_sessions.clear()
    yield
    app_module.active_sessions.clear()


@pytest.fixture
def client():
    return TestClient(app_module.app)


def login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_practice_lead_can_register_and_unregister_consultant(client: TestClient):
    token = login(client, "mona.lead", "lead123!")
    headers = {"Authorization": f"Bearer {token}"}
    email = "authorization.test@slalom.com"

    register_response = client.post(
        "/capabilities/Cloud Architecture/register",
        params={"email": email},
        headers=headers,
    )
    unregister_response = client.delete(
        "/capabilities/Cloud Architecture/unregister",
        params={"email": email},
        headers=headers,
    )

    assert register_response.status_code == 200
    assert unregister_response.status_code == 200


def test_mutation_requires_authentication(client: TestClient):
    response = client.post(
        "/capabilities/Cloud Architecture/register",
        params={"email": "unauthorized@slalom.com"},
    )

    assert response.status_code == 401


def test_invalid_credentials_are_rejected(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"username": "mona.lead", "password": "incorrect"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_practice_lead_is_limited_to_assigned_practice_areas(client: TestClient):
    token = login(client, "marcus.lead", "strategy456!")

    response = client.post(
        "/capabilities/Cloud Architecture/register",
        params={"email": "wrong.area@slalom.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Practice lead access to Technology is required"


def test_expired_session_is_rejected_and_removed(client: TestClient):
    token = login(client, "mona.lead", "lead123!")
    app_module.active_sessions[token]["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert token not in app_module.active_sessions


def test_logout_invalidates_session(client: TestClient):
    token = login(client, "mona.lead", "lead123!")
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/auth/logout", headers=headers)
    session_response = client.get("/auth/me", headers=headers)

    assert logout_response.status_code == 200
    assert session_response.status_code == 401


def test_authentication_and_mutations_are_audited(client: TestClient, caplog):
    caplog.set_level(logging.INFO, logger=app_module.audit_logger.name)
    email = "audit.test@slalom.com"
    token = login(client, "mona.lead", "lead123!")
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/capabilities/Cloud Architecture/register",
        params={"email": email},
        headers=headers,
    )
    client.delete(
        "/capabilities/Cloud Architecture/unregister",
        params={"email": email},
        headers=headers,
    )
    client.post("/auth/logout", headers=headers)

    messages = [record.getMessage() for record in caplog.records]
    assert any("event=login_succeeded" in message for message in messages)
    assert any("event=consultant_registered" in message for message in messages)
    assert any("event=consultant_unregistered" in message for message in messages)
    assert any("event=logout" in message for message in messages)