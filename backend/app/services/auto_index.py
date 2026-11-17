"""Construction automatique de l'index V2 (service index-init de Compose)."""

import os

from sqlalchemy import func, select

from app.db.models import Book
from app.db.session import SessionLocal, engine
from app.db.v2_models import BookV2, V2Base


def needs_index(book_count, indexed_count):
    if book_count == 0:
        raise RuntimeError("Aucun livre disponible en base.")
    return indexed_count != book_count


def main():
    V2Base.metadata.create_all(engine)

    with SessionLocal() as session:
        book_count = session.scalar(select(func.count()).select_from(Book)) or 0
        indexed = session.scalar(select(func.count()).select_from(BookV2)) or 0

    print(f"Index V2 : {indexed}/{book_count} livres", flush=True)

    if needs_index(book_count, indexed):
        from app.services.build_index_v2_full import build

        os.environ["DAAR_V2_CONFIRM"] = "YES"
        build()
    else:
        print("Index V2 deja complet.", flush=True)

    print("Index pret.", flush=True)


if __name__ == "__main__":
    main()
