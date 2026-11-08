from sqlalchemy import select, func

from app.db.models import Book, Posting
from app.db.session import SessionLocal
from app.services.build_index import build_index


def needs_index(book_count, indexed_count):
    """Indique si l'index doit être construit."""
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
        f"Index : {indexed_count}/{book_count} livres",
        flush=True,
    )

    if needs_index(book_count, indexed_count):
        print("Construction de l'index...", flush=True)
        build_index(missing_only=True)
    else:
        print("Index déjà complet. Aucune action.", flush=True)

    print("Index prêt.", flush=True)


if __name__ == "__main__":
    main()
