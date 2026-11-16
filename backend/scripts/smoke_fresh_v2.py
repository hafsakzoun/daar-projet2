"""Test d'initialisation V2 dans une base temporaire."""

import os
import subprocess
import sys

from sqlalchemy import create_engine, func, select, text

from app.db.models import Base, Book, Posting
from app.db.session import DATABASE_URL, SessionLocal


TEST_DB = "daar_v2_smoke_fresh"


def test_child():
    if DATABASE_URL.database != TEST_DB:
        raise RuntimeError("Mauvaise base de test")

    from app.db.v2_models import BookV2, PostingV2, TermV2
    from app.services import build_index_v2_full as builder
    from app.services.auto_index import main as auto_main
    from app.services.index_version import v2_ready
    from app.services.search_optimized import search_books_v2

    class StopAfterFive(Exception):
        pass

    original = builder.count_index_words
    processed = 0

    def limited_count(content, language):
        nonlocal processed
        if processed == 5:
            raise StopAfterFive()
        processed += 1
        return original(content, language)

    builder.count_index_words = limited_count

    try:
        auto_main()
    except StopAfterFive:
        print("Arret volontaire apres 5 livres : OK")
    else:
        raise AssertionError("Arret du test non declenche")
    finally:
        builder.count_index_words = original

    with SessionLocal() as session:
        books = session.scalar(
            select(func.count()).select_from(Book)
        )
        old_postings = session.scalar(
            select(func.count()).select_from(Posting)
        )
        new_books = session.scalar(
            select(func.count()).select_from(BookV2)
        )
        new_terms = session.scalar(
            select(func.count()).select_from(TermV2)
        )
        new_postings = session.scalar(
            select(func.count()).select_from(PostingV2)
        )

        assert books == 1700
        assert old_postings == 0
        assert new_books == 5
        assert new_terms > 0
        assert new_postings > 0
        assert not v2_ready(session)

        result = search_books_v2(session, "king", limit=3)
        assert "total" in result
        assert "results" in result

    print("=== TEST V2 REUSSI ===")
    print(f"V1 : {old_postings} postings")
    print(f"V2 : {new_books} livres")
    print(f"Termes V2 : {new_terms}")
    print(f"Postings V2 : {new_postings}")


def test_parent():
    if DATABASE_URL.database == TEST_DB:
        raise RuntimeError("Base source incorrecte")

    if os.environ.get("DAAR_TEST_DB") == "1":
        raise RuntimeError("Ne pas utiliser DAAR_TEST_DB ici")

    admin = create_engine(
        DATABASE_URL.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )

    created = False

    try:
        with admin.connect() as connection:
            existing = connection.scalar(
                text(
                    "SELECT 1 FROM pg_database "
                    "WHERE datname = :name"
                ),
                {"name": TEST_DB},
            )

            if existing:
                raise RuntimeError(
                    "Base temporaire deja existante : "
                    "aucune suppression effectuee"
                )

            connection.execute(
                text(f"CREATE DATABASE {TEST_DB}")
            )
            created = True

        with SessionLocal() as source:
            records = [
                dict(row)
                for row in source.execute(
                    select(Book.__table__)
                ).mappings().all()
            ]

        assert len(records) == 1700

        temporary = create_engine(
            DATABASE_URL.set(database=TEST_DB)
        )

        try:
            Base.metadata.create_all(temporary)

            with temporary.begin() as connection:
                connection.execute(
                    Book.__table__.insert(),
                    records,
                )
        finally:
            temporary.dispose()

        env = os.environ.copy()
        env["DB_NAME"] = TEST_DB
        env.pop("DAAR_TEST_DB", None)
        env.pop("DAAR_BUILD_V1", None)
        env.pop("DAAR_SEARCH_INDEX", None)

        subprocess.run(
            [sys.executable, __file__, "--child"],
            env=env,
            check=True,
        )

    finally:
        if created:
            with admin.connect() as connection:
                connection.execute(
                    text(
                        f"DROP DATABASE {TEST_DB} WITH (FORCE)"
                    )
                )
            print("Base temporaire supprimee.")

        admin.dispose()


if __name__ == "__main__":
    if "--child" in sys.argv:
        test_child()
    else:
        test_parent()
