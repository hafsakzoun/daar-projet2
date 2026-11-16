"""Initialisation automatique des index."""

import os

from sqlalchemy import func, select

from app.db.models import Book, Posting
from app.db.session import SessionLocal, engine
from app.db.v2_models import BookV2, V2Base
from app.services.build_index import build_index


def needs_index(book_count, indexed_count):
    if book_count == 0:
        raise RuntimeError("Aucun livre disponible en base.")
    return indexed_count != book_count


def main():
    with SessionLocal() as session:
        book_count = session.scalar(
            select(func.count()).select_from(Book)
        ) or 0

        indexed_v1 = session.scalar(
            select(func.count(func.distinct(Posting.book_id)))
        ) or 0

    if book_count == 0:
        raise RuntimeError("Corpus absent.")

    # V1 uniquement pour les tests et les comparaisons.
    build_v1 = (
        os.environ.get("DAAR_TEST_DB") == "1"
        or os.environ.get("DAAR_BUILD_V1") == "1"
    )

    if build_v1:
        if needs_index(book_count, indexed_v1):
            print("Construction de V1...", flush=True)
            build_index(missing_only=True)
        else:
            print("V1 deja complete.", flush=True)
    else:
        print("V1 facultative : construction ignoree.", flush=True)

    if os.environ.get("DAAR_TEST_DB") == "1":
        return

    V2Base.metadata.create_all(engine)

    with SessionLocal() as session:
        indexed_v2 = session.scalar(
            select(func.count()).select_from(BookV2)
        ) or 0

    print(
        f"Index V2 : {indexed_v2}/{book_count} livres",
        flush=True,
    )

    if indexed_v2 != book_count:
        from app.services.build_index_v2_full import build

        os.environ["DAAR_V2_CONFIRM"] = "YES"
        build()
    else:
        print("V2 deja complete.", flush=True)

    print("Index pret.", flush=True)


if __name__ == "__main__":
    main()
