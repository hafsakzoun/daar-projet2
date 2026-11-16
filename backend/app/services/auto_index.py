"""Initialisation des index V1 et V2."""

import os

from sqlalchemy import select, func

from app.db.models import Book, Posting
from app.db.session import SessionLocal, engine
from app.db.v2_models import BookV2, V2Base
from app.services.build_index import build_index


def needs_index(book_count, indexed_count):
    """Indique si l'index V1 doit etre construit."""
    if book_count == 0:
        raise RuntimeError("Aucun livre disponible en base.")

    return indexed_count != book_count


def main():
    with SessionLocal() as session:
        book_count = session.scalar(
            select(func.count()).select_from(Book)
        )

        indexed_count = session.scalar(
            select(func.count(func.distinct(Posting.book_id)))
        )

    print(
        f"Index V1 : {indexed_count}/{book_count} livres",
        flush=True,
    )

    if needs_index(book_count, indexed_count):
        print("Construction de l'index V1...", flush=True)
        build_index(missing_only=True)
    else:
        print("Index V1 deja complet.", flush=True)

    # Ne pas lancer une reconstruction V2 pendant les tests.
    if os.environ.get("DAAR_TEST_DB") == "1":
        print("Index de test pret.", flush=True)
        return

    V2Base.metadata.create_all(engine)

    with SessionLocal() as session:
        v2_count = session.scalar(
            select(func.count()).select_from(BookV2)
        ) or 0

    print(
        f"Index V2 : {v2_count}/{book_count} livres",
        flush=True,
    )

    if v2_count != book_count:
        print("Construction/reprise de l'index V2...", flush=True)

        from app.services.build_index_v2_full import build

        os.environ["DAAR_V2_CONFIRM"] = "YES"
        build()
    else:
        print("Index V2 deja complet.", flush=True)

    print("Index pret.", flush=True)


if __name__ == "__main__":
    main()
