import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import search as search_api
from app.db.session import get_db
from app.main import app
from app.services.search_optimized import PageRankUnavailable


@pytest.fixture
def client(monkeypatch):
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(search_api, "v2_ready", lambda db: True)
    try:
        with TestClient(app) as http:
            yield http
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_keyword_search_forwards_parameters(client, monkeypatch):
    captured = {}

    def fake(db, q, limit, offset, sort):
        captured.update(q=q, limit=limit, offset=offset, sort=sort)
        return {"total": 0, "limit": limit, "offset": offset, "results": []}

    monkeypatch.setattr(search_api, "search_books_v2", fake)
    response = client.get("/api/v1/search", params={"q": "whale", "limit": 5, "offset": 10})

    assert response.status_code == 200
    assert captured == {"q": "whale", "limit": 5, "offset": 10, "sort": "occurrences"}


def test_blank_query_is_rejected(client):
    assert client.get("/api/v1/search", params={"q": "   "}).status_code == 400


def test_pagerank_unavailable_returns_503(client, monkeypatch):
    def fake(*args, **kwargs):
        raise PageRankUnavailable("graphe absent")

    monkeypatch.setattr(search_api, "search_books_v2", fake)
    response = client.get("/api/v1/search", params={"q": "whale", "sort": "pagerank"})

    assert response.status_code == 503


def test_index_not_ready_returns_503(client, monkeypatch):
    monkeypatch.setattr(search_api, "v2_ready", lambda db: False)
    assert client.get("/api/v1/search", params={"q": "whale"}).status_code == 503
    assert client.get("/api/v1/search/regex", params={"q": "wh.*"}).status_code == 503
