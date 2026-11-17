"""Favoris et historique stockés en base (necessite DB_NAME=daar_test)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

PASSWORD = "mot-de-passe-de-test-123"


@pytest.fixture
def client(seeded_db):
    with TestClient(app) as http:
        email = "lecteur@example.org"
        assert http.post(
            "/api/v1/auth/signup",
            json={"first_name": "Test", "email": email, "password": PASSWORD},
        ).status_code == 201
        assert http.post(
            "/api/v1/auth/login",
            json={"email": email, "password": PASSWORD},
        ).status_code == 200
        yield http


def test_activity_requires_login(seeded_db):
    with TestClient(app) as http:
        assert http.get("/api/v1/auth/me/favorites").status_code == 401
        assert http.get("/api/v1/auth/me/history").status_code == 401


def test_favorites_are_persisted(client):
    assert client.put("/api/v1/auth/me/favorites/11").status_code == 204
    # Ajout idempotent
    assert client.put("/api/v1/auth/me/favorites/11").status_code == 204
    assert client.put("/api/v1/auth/me/favorites/12").status_code == 204

    ids = [book["id"] for book in client.get("/api/v1/auth/me/favorites").json()]
    assert sorted(ids) == [11, 12]

    assert client.delete("/api/v1/auth/me/favorites/11").status_code == 204
    ids = [book["id"] for book in client.get("/api/v1/auth/me/favorites").json()]
    assert ids == [12]


def test_favorite_unknown_book(client):
    assert client.put("/api/v1/auth/me/favorites/999").status_code == 404


def test_history_is_capped_and_clearable(client):
    for i in range(35):
        response = client.post(
            "/api/v1/auth/me/history",
            json={"query": f"mot{i}", "mode": "keyword"},
        )
        assert response.status_code == 201

    history = client.get("/api/v1/auth/me/history").json()
    assert len(history) == 30
    assert history[0]["query"] == "mot34"

    assert client.post(
        "/api/v1/auth/me/history", json={"query": "x", "mode": "sql"}
    ).status_code == 422

    assert client.delete("/api/v1/auth/me/history").status_code == 204
    assert client.get("/api/v1/auth/me/history").json() == []
