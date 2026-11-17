from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import books as books_api
from app.db.session import get_db
from app.main import app


class FakeDb:
    def get(self, model, book_id):
        if book_id == 11:
            return SimpleNamespace(id=11, title="Alice", author="Carroll, Lewis")
        return None


@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "11.txt").write_text("abcdefghij", encoding="utf-8")
    monkeypatch.setattr(books_api, "CORPUS_DIR", tmp_path)
    app.dependency_overrides[get_db] = lambda: FakeDb()
    try:
        with TestClient(app) as http:
            yield http
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_text_is_paginated_by_characters(client):
    response = client.get("/api/v1/books/11/text", params={"offset": 3, "limit": 4})

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "defg"
    assert body["offset"] == 3
    assert body["length"] == 4
    assert body["total"] == 10
    assert body["title"] == "Alice"


def test_text_unknown_book_returns_404(client):
    assert client.get("/api/v1/books/999/text").status_code == 404


def test_text_missing_file_returns_503(client, tmp_path):
    (tmp_path / "11.txt").unlink()
    assert client.get("/api/v1/books/11/text").status_code == 503
