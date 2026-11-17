import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.api.v1.endpoints import search as search_api
from app.services.search_optimized import PageRankUnavailable
from app.services.regex_automate_search_v2 import TooManyRegexMatches


@pytest.fixture
def client(monkeypatch):
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(search_api, "v2_ready", lambda db: True)

    try:
        with TestClient(app) as http:
            yield http
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_regex_http_success_and_pagination(client, monkeypatch):
    captured = {}

    def fake_search(db, pattern, limit, offset, sort):
        captured.update(
            pattern=pattern,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return {
            "total": 12,
            "limit": limit,
            "offset": offset,
            "results": [],
        }

    monkeypatch.setattr(
        search_api, "search_regex_automate_v2", fake_search
    )

    response = client.get(
        "/api/v1/search/regex",
        params={
            "q": "run.*",
            "limit": 3,
            "offset": 6,
            "sort": "pagerank",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 12
    assert captured == {
        "pattern": "run.*",
        "limit": 3,
        "offset": 6,
        "sort": "pagerank",
    }


def test_regex_http_invalid_pattern(client):
    response = client.get(
        "/api/v1/search/regex",
        params={"q": "*abc"},
    )
    assert response.status_code == 400


def test_regex_http_missing_v2(client, monkeypatch):
    monkeypatch.setattr(
        search_api, "v2_ready", lambda db: False
    )

    response = client.get(
        "/api/v1/search/regex",
        params={"q": "alice"},
    )
    assert response.status_code == 503


def test_regex_http_too_many_terms(client, monkeypatch):
    def fail(*args, **kwargs):
        raise TooManyRegexMatches("Trop de termes")

    monkeypatch.setattr(
        search_api, "search_regex_automate_v2", fail
    )

    response = client.get(
        "/api/v1/search/regex",
        params={"q": "a.*"},
    )
    assert response.status_code == 422


def test_regex_http_missing_pagerank(client, monkeypatch):
    def fail(*args, **kwargs):
        raise PageRankUnavailable("Graphe indisponible")

    monkeypatch.setattr(
        search_api, "search_regex_automate_v2", fail
    )

    response = client.get(
        "/api/v1/search/regex",
        params={"q": "alice", "sort": "pagerank"},
    )
    assert response.status_code == 503
