"""Construit l'index V2 en parallele de la V1.

Ne modifie jamais les tables books, terms et postings.
Chaque livre est valide dans une transaction independante.
"""

import os
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Book, Posting
from app.db.session import SessionLocal, engine, DATABASE_URL
from app.db.v2_models import BookV2, TermV2, PostingV2, V2Base
from app.services.index_normalization import count_index_words


BATCH_SIZE = 1000


def build():
    if os.environ.get("DAAR_V2_CONFIRM") != "YES":
        raise RuntimeError(
            "Confirmation requise : DAAR_V2_CONFIRM=YES"
        )

    with SessionLocal() as session:
        books = session.scalars(
            select(Book).order_by(Book.id)
        ).all()

        original_postings = session.scalar(
            select(func.count()).select_from(Posting)
        )

    if len(books) != 1700 or not original_postings:
        raise RuntimeError(
            "Base source inattendue : index V1 absent ou incomplet."
        )

    print(
        f"Base : {DATABASE_URL.database} | "
        f"V1 : {len(books)} livres, {original_postings} postings",
        flush=True,
    )

    V2Base.metadata.create_all(engine)

    with SessionLocal() as session:
        completed_ids = set(
            session.scalars(select(BookV2.id)).all()
        )

    remaining = [
        book for book in books
        if book.id not in completed_ids
    ]

    print(
        f"V2 : {len(completed_ids)} livres deja termines, "
        f"{len(remaining)} livres restants",
        flush=True,
    )

    for position, book in enumerate(remaining, 1):
        text = Path(book.text_path).read_text(
            encoding="utf-8",
            errors="replace",
        )

        counts = count_index_words(text, book.language)
        words = list(counts)
        term_ids = {}

        with SessionLocal.begin() as session:
            for start in range(0, len(words), BATCH_SIZE):
                batch = words[start:start + BATCH_SIZE]

                statement = insert(TermV2).values([
                    {
                        "language": book.language,
                        "value": word,
                    }
                    for word in batch
                ])

                session.execute(
                    statement.on_conflict_do_nothing(
                        index_elements=[
                            TermV2.language,
                            TermV2.value,
                        ]
                    )
                )

                rows = session.execute(
                    select(TermV2.value, TermV2.id).where(
                        TermV2.language == book.language,
                        TermV2.value.in_(batch),
                    )
                ).all()

                term_ids.update({
                    value: term_id
                    for value, term_id in rows
                })

            postings = [
                {
                    "book_id": book.id,
                    "term_id": term_ids[word],
                    "frequency": frequency,
                }
                for word, frequency in counts.items()
            ]

            # La ligne BookV2 est inseree dans la meme
            # transaction que tous ses postings.
            session.execute(
                insert(BookV2).values(
                    id=book.id,
                    title=book.title,
                    author=book.author,
                    language=book.language,
                )
            )

            for start in range(0, len(postings), BATCH_SIZE):
                session.execute(
                    insert(PostingV2),
                    postings[start:start + BATCH_SIZE],
                )

        if position % 25 == 0 or position == len(remaining):
            print(
                f"V2 : {position}/{len(remaining)} "
                f"livres restants traites",
                flush=True,
            )

    with SessionLocal() as session:
        book_count = session.scalar(
            select(func.count()).select_from(BookV2)
        )
        term_count = session.scalar(
            select(func.count()).select_from(TermV2)
        )
        posting_count = session.scalar(
            select(func.count()).select_from(PostingV2)
        )

    print("\n=== INDEX V2 COMPLET ===")
    print(f"Livres : {book_count}")
    print(f"Termes : {term_count}")
    print(f"Postings : {posting_count}")
    print("Indexation V2 terminee.", flush=True)


if __name__ == "__main__":
    build()
