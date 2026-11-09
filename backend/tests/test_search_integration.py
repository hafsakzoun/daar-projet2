import pytest

pytestmark = pytest.mark.usefixtures("seeded_db")


from sqlalchemy import select

from app.db.models import Posting, Term
from app.db.session import SessionLocal
from app.services.search import search_books


def test_search_alice():
    with SessionLocal() as db:
        result = search_books(db, "alice", limit=3)

    assert result["total"] > 0
    assert len(result["results"]) == 3

    scores = [book["score"] for book in result["results"]]
    assert scores == sorted(scores, reverse=True)


def test_search_unknown_word():
    with SessionLocal() as db:
        result = search_books(
            db,
            "zzzznonexistentwordzzzz",
        )

    assert result["total"] == 0
    assert result["results"] == []


def test_search_frequency():
    with SessionLocal() as db:
        frequency = db.execute(
            select(Posting.frequency)
            .join(Term, Term.id == Posting.term_id)
            .where(
                Posting.book_id == 11,
                Term.value == "alice",
            )
        ).scalar_one()

        assert frequency > 0

        first_page = search_books(
            db, "alice", limit=100, offset=0
        )

        found = None

        for offset in range(0, first_page["total"], 100):
            page = search_books(
                db, "alice", limit=100, offset=offset
            )

            for book in page["results"]:
                if book["id"] == 11:
                    found = book
                    break

            if found is not None:
                break

        assert found is not None
        assert found["score"] == frequency
