import os

import pytest

# Les tests ne doivent jamais envoyer de vrais e-mails, quelle que soit la
# configuration de la machine (.env local) : SMTP désactivé avant tout import
# de l'application. Les tests d'e-mail l'activent eux-mêmes avec un faux envoi.
for _name in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_PASSWORD_FILE"):
    os.environ.pop(_name, None)


@pytest.fixture(scope="function")
def seeded_db():
    """Prépare une base PostgreSQL réservée aux tests."""

    # Sécurité : ne jamais réinitialiser la vraie base.
    if (
        os.environ.get("DB_NAME") != "daar_test"
        or os.environ.get("DAAR_TEST_DB") != "1"
    ):
        pytest.skip(
            "Les tests d'intégration nécessitent "
            "DB_NAME=daar_test et DAAR_TEST_DB=1."
        )

    from app.db.models import Base, Book
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

        db.commit()

    yield


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Chaque test repart avec des compteurs de tentatives vides."""
    from app.services import rate_limit

    rate_limit.reset()
    yield
    rate_limit.reset()
