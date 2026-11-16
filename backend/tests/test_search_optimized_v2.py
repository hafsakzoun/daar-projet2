"""Tests d'integration V2 sur la base protegee daar_test."""

import pytest
from sqlalchemy import update

from app.db.models import Book
from app.db.session import SessionLocal, engine
from app.db.v2_models import V2Base, BookV2, TermV2, PostingV2
from app.services.index_version import v2_ready
from app.services.search_optimized import search_books_v2, search_regex_v2


@pytest.fixture
def indexed_v2(seeded_db):
    # seeded_db garantit DB_NAME=daar_test et DAAR_TEST_DB=1.
    # Les tables suivantes sont creees uniquement dans cette base.
    V2Base.metadata.drop_all(bind=engine)
    V2Base.metadata.create_all(bind=engine)

    with SessionLocal.begin() as db:
        db.add(Book(
            id=14, title="Livre francais", author="Auteur test",
            language="fr", word_count=12000,
            source_url="https://example.org/book14",
            text_path="tests/book14.txt",
        ))

        db.add_all([
            BookV2(id=11, title="Alice", author="Auteur", language="en"),
            BookV2(id=12, title="Rabbit", author="Auteur", language="en"),
            BookV2(id=13, title="Other", author="Auteur", language="en"),
            BookV2(id=14, title="Maison", author="Auteur", language="fr"),
        ])

        db.add_all([
            TermV2(id=101, language="en", value="alic"),
            TermV2(id=102, language="en", value="rabbit"),
            TermV2(id=103, language="fr", value="maison"),
        ])

        db.flush()

        db.add_all([
            PostingV2(book_id=11, term_id=101, frequency=9),
            PostingV2(book_id=12, term_id=101, frequency=5),
            PostingV2(book_id=13, term_id=101, frequency=2),
            PostingV2(book_id=12, term_id=102, frequency=3),
            PostingV2(book_id=14, term_id=103, frequency=6),
        ])


def test_v2_stemming_and_response(indexed_v2):
    with SessionLocal() as db:
        data = search_books_v2(db, "ALICE", limit=2)

    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert [b["id"] for b in data["results"]] == [11, 12]
    assert data["results"][0]["score"] == 750


def test_v2_normalized_ranking(indexed_v2):
    with SessionLocal.begin() as db:
        db.execute(
            update(Book)
            .where(Book.id == 11)
            .values(word_count=120000)
        )

    with SessionLocal() as db:
        data = search_books_v2(db, "alice")

    assert [b["id"] for b in data["results"]] == [12, 13, 11]


def test_v2_french_and_stopwords(indexed_v2):
    with SessionLocal() as db:
        french = search_books_v2(db, "maisons")
        empty = search_books_v2(db, "the and")

    assert [b["id"] for b in french["results"]] == [14]
    assert empty["total"] == 0


def test_v2_regex_on_stems(indexed_v2):
    with SessionLocal() as db:
        matched = search_regex_v2(db, "alic|rabbit")
        original = search_regex_v2(db, "^alice$")

    assert matched["total"] == 3
    assert original["total"] == 0


def test_v2_ready_and_fallback(indexed_v2, monkeypatch):
    with SessionLocal() as db:
        # Les tests utilisent V1 par defaut.
        assert not v2_ready(db)

        # On verifie la detection V2 sans changer de base.
        monkeypatch.delenv("DAAR_TEST_DB", raising=False)
        monkeypatch.delenv("DAAR_SEARCH_INDEX", raising=False)
        assert v2_ready(db)

        # Repli explicite sur V1.
        monkeypatch.setenv("DAAR_SEARCH_INDEX", "v1")
        assert not v2_ready(db)
