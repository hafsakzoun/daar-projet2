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


def test_v2_ready_detects_complete_index(indexed_v2, monkeypatch):
    from app.services import index_version

    monkeypatch.setattr(index_version, "_ready", False)
    with SessionLocal() as db:
        assert v2_ready(db)


# Tri PageRank en SQL

def test_pagerank_unavailable_without_scores(indexed_v2):
    from app.services.search_optimized import PageRankUnavailable

    with SessionLocal() as db, pytest.raises(PageRankUnavailable):
        search_books_v2(db, "alice", sort="pagerank")


def test_pagerank_sort_and_pagination(indexed_v2):
    from app.db.models import BookScore

    with SessionLocal.begin() as db:
        db.add_all([
            BookScore(book_id=11, pagerank=0.1),
            BookScore(book_id=12, pagerank=0.5),
            BookScore(book_id=13, pagerank=0.3),
        ])

    with SessionLocal() as db:
        first = search_books_v2(db, "alice", limit=2, sort="pagerank")
        second = search_books_v2(db, "alice", limit=2, offset=2, sort="pagerank")

    assert first["total"] == 3
    # Tri par centralite decroissante, pagine par PostgreSQL.
    assert [b["id"] for b in first["results"]] == [12, 13]
    assert first["results"][0]["pagerank"] == 0.5
    assert [b["id"] for b in second["results"]] == [11]


# RegEx par automate (vocabulaire en memoire)

def test_regex_automate_uses_prefix_and_vocabulary(indexed_v2):
    from app.services import regex_automate_search_v2 as regex

    regex.reset_vocabulary()
    try:
        with SessionLocal() as db:
            prefixed = regex.search_regex_automate_v2(db, "ali.*")
            alternative = regex.search_regex_automate_v2(db, "(alic|rabbit)")
            unconstrained = regex.search_regex_automate_v2(db, ".*son")
            nothing = regex.search_regex_automate_v2(db, "zzz+")
    finally:
        regex.reset_vocabulary()

    assert [b["id"] for b in prefixed["results"]] == [11, 12, 13]
    assert alternative["total"] == 3
    assert [b["id"] for b in unconstrained["results"]] == [14]
    assert nothing["total"] == 0


# Suggestions : voisins dans le graphe de Jaccard

def test_recommendations_come_from_graph_table(indexed_v2):
    from fastapi.testclient import TestClient

    from app.db.models import BookSimilarity
    from app.main import app

    with SessionLocal.begin() as db:
        db.add_all([
            BookSimilarity(book_id=11, neighbor_id=12, similarity=0.4),
            BookSimilarity(book_id=11, neighbor_id=13, similarity=0.7),
            BookSimilarity(book_id=11, neighbor_id=14, similarity=0.2),
        ])

    with TestClient(app) as http:
        body = http.get("/api/v1/books/11/recommendations?limit=2").json()
        empty = http.get("/api/v1/books/12/recommendations").json()
        missing = http.get("/api/v1/books/999/recommendations")

    assert [(b["id"], b["similarity"]) for b in body["results"]] == [(13, 0.7), (12, 0.4)]
    assert empty["results"] == []
    assert missing.status_code == 404
