import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.db.models import Book
from app.services.pagerank_scores import (
    PageRankUnavailable,
    load_pagerank_scores,
    sort_pagerank_rows,
)
from app.services.search_optimized import _response
from app.api.v1.endpoints import search as search_api


def write_scores(tmp_path, monkeypatch, scores, count=None):
    path = tmp_path / "graph.json"
    path.write_text(json.dumps({
        "book_count": len(scores) if count is None else count,
        "pagerank": scores,
    }))
    monkeypatch.setenv("PAGERANK_PATH", str(path))


def test_load_pagerank(tmp_path, monkeypatch):
    write_scores(tmp_path, monkeypatch, {"10": 0.3, "20": 0.7})
    assert load_pagerank_scores() == {10: 0.3, 20: 0.7}


def test_missing_pagerank_file(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "PAGERANK_PATH", str(tmp_path / "absent.json")
    )
    with pytest.raises(PageRankUnavailable):
        load_pagerank_scores()


def test_invalid_pagerank_file(tmp_path, monkeypatch):
    path = tmp_path / "graph.json"
    path.write_text("not json")
    monkeypatch.setenv("PAGERANK_PATH", str(path))
    with pytest.raises(PageRankUnavailable):
        load_pagerank_scores()


def test_incomplete_pagerank_file(tmp_path, monkeypatch):
    write_scores(tmp_path, monkeypatch, {"10": 0.3}, count=2)
    with pytest.raises(PageRankUnavailable):
        load_pagerank_scores()


def test_negative_pagerank_rejected(tmp_path, monkeypatch):
    write_scores(tmp_path, monkeypatch, {"10": -0.5})
    with pytest.raises(PageRankUnavailable):
        load_pagerank_scores()


def test_sort_and_equal_score_tiebreak():
    rows = [
        SimpleNamespace(id=30),
        SimpleNamespace(id=20),
        SimpleNamespace(id=10),
    ]
    scores = {10: 0.4, 20: 0.8, 30: 0.8}

    result = sort_pagerank_rows(rows, scores)

    assert [row.id for row in result] == [20, 30, 10]


def test_missing_book_score_rejected():
    rows = [SimpleNamespace(id=10), SimpleNamespace(id=20)]

    with pytest.raises(PageRankUnavailable):
        sort_pagerank_rows(rows, {10: 0.9})


def test_pagerank_sort_before_pagination(tmp_path, monkeypatch):
    write_scores(
        tmp_path, monkeypatch,
        {"10": 0.1, "20": 0.7, "30": 0.9},
    )

    rows = [
        SimpleNamespace(id=i, title=f"Livre {i}", author="Auteur", score=5)
        for i in (10, 20, 30)
    ]

    class FakeDB:
        def execute(self, statement):
            return SimpleNamespace(all=lambda: rows)

        def scalar(self, statement):
            raise AssertionError("Pagination avant tri interdite")

    result = _response(
        FakeDB(),
        select(Book.id),
        Book.id,
        limit=1,
        offset=1,
        sort="pagerank",
    )

    assert result["total"] == 3
    assert [book["id"] for book in result["results"]] == [20]
    assert result["results"][0]["pagerank"] == 0.7


def test_keyword_api_returns_503(monkeypatch):
    monkeypatch.setattr(search_api, "v2_ready", lambda db: True)

    def fail(*args, **kwargs):
        raise PageRankUnavailable("Graphe incomplet")

    monkeypatch.setattr(search_api, "search_books_v2", fail)

    with pytest.raises(HTTPException) as exc:
        search_api.search(
            q="alice", limit=20, offset=0,
            sort="pagerank", db=object(),
        )

    assert exc.value.status_code == 503


def test_regex_api_returns_503(monkeypatch):
    monkeypatch.setattr(search_api, "v2_ready", lambda db: True)

    def fail(*args, **kwargs):
        raise PageRankUnavailable("Graphe incomplet")

    monkeypatch.setattr(search_api, "search_regex_automate_v2", fail)

    with pytest.raises(HTTPException) as exc:
        search_api.regex_search(
            q="alice", limit=20, offset=0,
            sort="pagerank", db=object(),
        )

    assert exc.value.status_code == 503
