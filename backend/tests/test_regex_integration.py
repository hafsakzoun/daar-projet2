import pytest

pytestmark = pytest.mark.usefixtures("seeded_db")

from app.db.session import SessionLocal
from app.services.regex_search import search_regex
from app.services.search import search_books


def test_regex_alice():
    with SessionLocal() as db:
        regex_result = search_regex(db, "alice", limit=3)
        keyword_result = search_books(db, "alice", limit=3)

    assert regex_result == keyword_result


def test_regex_unknown_word():
    with SessionLocal() as db:
        result = search_regex(
            db, "zzzznonexistentwordzzzz"
        )

    assert result["total"] == 0
    assert result["results"] == []


def test_regex_alternative():
    with SessionLocal() as db:
        result = search_regex(
            db, "alice|rabbit", limit=3
        )

    assert result["total"] > 0
    assert len(result["results"]) == 3
    assert all(book["score"] > 0 for book in result["results"])
