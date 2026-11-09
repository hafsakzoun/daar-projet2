import os

import pytest


@pytest.fixture(scope="function")
def seeded_db():
    """Prépare une base PostgreSQL réservée aux tests."""

    # Sécurité : ne jamais réinitialiser la vraie base.
    if (
        os.environ.get("DB_NAME") != "daar_test"
        or os.environ.get("DAAR_TEST_DB") != "1"
    ):
        pytest.fail(
            "Les tests d'intégration nécessitent "
            "DB_NAME=daar_test et DAAR_TEST_DB=1."
        )

    from app.db.models import Base, Book, Term, Posting
    from app.db.session import engine, SessionLocal

    # Remise à zéro uniquement de la base de test.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        db.add_all([
            Book(
                id=11,
                title="Alice au pays des merveilles",
                author="Lewis Carroll",
                language="en",
                word_count=12000,
                source_url="https://example.org/book11",
                text_path="tests/book11.txt",
            ),
            Book(
                id=12,
                title="Les aventures du lapin",
                author="Auteur test",
                language="en",
                word_count=11000,
                source_url="https://example.org/book12",
                text_path="tests/book12.txt",
            ),
            Book(
                id=13,
                title="Une autre histoire d'Alice",
                author="Auteur test",
                language="en",
                word_count=10500,
                source_url="https://example.org/book13",
                text_path="tests/book13.txt",
            ),
        ])

        db.add_all([
            Term(id=1, value="alice"),
            Term(id=2, value="rabbit"),
        ])

        db.flush()

        db.add_all([
            Posting(book_id=11, term_id=1, frequency=9),
            Posting(book_id=12, term_id=1, frequency=5),
            Posting(book_id=13, term_id=1, frequency=2),
            Posting(book_id=11, term_id=2, frequency=1),
            Posting(book_id=12, term_id=2, frequency=2),
            Posting(book_id=13, term_id=2, frequency=4),
        ])

        db.commit()

    yield
