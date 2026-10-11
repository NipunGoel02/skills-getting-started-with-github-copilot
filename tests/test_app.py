import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = copy.deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def signup_path(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/signup"


def participants_path(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/participants"


def test_get_activities_returns_activity_catalog(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert "participants" in response.json()["Chess Club"]


def test_signup_adds_participant(client):
    activity_name = "Art Club"
    email = "new-student@example.com"

    response = client.post(signup_path(activity_name), params={"email": email})

    assert response.status_code == 200
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_duplicate_signup_returns_conflict_without_adding_another_entry(client):
    activity_name = "Art Club"
    email = "new-student@example.com"
    signup_response = client.post(signup_path(activity_name), params={"email": email})

    assert signup_response.status_code == 200

    response = client.post(signup_path(activity_name), params={"email": email})

    assert response.status_code == 409
    assert client.get("/activities").json()[activity_name]["participants"].count(email) == 1


def test_signup_for_unknown_activity_returns_not_found(client):
    response = client.post(signup_path("Unknown Activity"), params={"email": "student@example.com"})

    assert response.status_code == 404


def test_unregister_removes_participant(client):
    activity_name = "Art Club"
    email = "student-to-remove@example.com"
    signup_response = client.post(signup_path(activity_name), params={"email": email})
    assert signup_response.status_code == 200

    response = client.delete(participants_path(activity_name), params={"email": email})

    assert response.status_code == 200
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_from_unknown_activity_returns_not_found(client):
    response = client.delete(
        participants_path("Unknown Activity"),
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404


def test_unregister_unregistered_participant_returns_not_found(client):
    response = client.delete(
        participants_path("Art Club"),
        params={"email": "not-registered@example.com"},
    )

    assert response.status_code == 404