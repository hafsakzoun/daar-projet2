"""Construit un echantillon V2 dans une base PostgreSQL isolee."""

import argparse
from pathlib import Path

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from app.db.models import Book
from app.db.session import DATABASE_URL, SessionLocal
from app.db.v2_models import BookV2, TermV2, PostingV2, V2Base
from app.services.index_normalization import count_index_words


SANDBOX_DB = "daar_v2_sandbox"
BATCH_SIZE = 1000


def build_sample(limit: int) -> None:
    if DATABASE_URL.database == SANDBOX_DB:
        raise RuntimeError("La base source doit etre differente du sandbox.")

    with SessionLocal() as source:
        books = source.scalars(
            select(Book).order_by(Book.id)
        ).all()

    if not books:
        raise RuntimeError("Aucun livre dans la base source.")

    limit = min(limit, len(books))

    selected = [
        books[i * len(books) // limit]
        for i in range(limit)
    ]

    sandbox_engine = create_engine(
        DATABASE_URL.set(database=SANDBOX_DB),
        pool_pre_ping=True,
    )

    V2Base.metadata.create_all(sandbox_engine)
    SandboxSession = sessionmaker(bind=sandbox_engine)

    for position, book in enumerate(selected, start=1):
        text = Path(book.text_path).read_text(
            encoding="utf-8",
            errors="replace",
        )

        counts = count_index_words(text, book.language)
        words = list(counts)
        term_ids = {}

        with SandboxSession.begin() as session:
            book_insert = insert(BookV2).values(
                id=book.id,
                title=book.title,
                author=book.author,
                language=book.language,
            )

            session.execute(
                book_insert.on_conflict_do_update(
                    index_elements=[BookV2.id],
                    set_={
                        "title": book.title,
                        "author": book.author,
                        "language": book.language,
                    },
                )
            )

            for start in range(0, len(words), BATCH_SIZE):
                batch = words[start:start + BATCH_SIZE]

                term_insert = insert(TermV2).values([
                    {
                        "language": book.language,
                        "value": word,
                    }
                    for word in batch
                ])

                session.execute(
                    term_insert.on_conflict_do_nothing(
                        index_elements=[
                            TermV2.language,
                            TermV2.value,
                        ],
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

            session.execute(
                delete(PostingV2).where(
                    PostingV2.book_id == book.id
                )
            )

            postings = [
                {
                    "book_id": book.id,
                    "term_id": term_ids[word],
                    "frequency": frequency,
                }
                for word, frequency in counts.items()
            ]

            for start in range(0, len(postings), BATCH_SIZE):
                session.execute(
                    insert(PostingV2),
                    postings[start:start + BATCH_SIZE],
                )

        print(
            f"[{position}/{limit}] Livre {book.id} : "
            f"{len(counts)} racines",
            flush=True,
        )

    with SandboxSession() as session:
        book_count = session.scalar(
            select(func.count()).select_from(BookV2)
        )
        term_count = session.scalar(
            select(func.count()).select_from(TermV2)
        )
        posting_count = session.scalar(
            select(func.count()).select_from(PostingV2)
        )

    print("\n=== INDEX V2 SANDBOX ===")
    print(f"Livres : {book_count}")
    print(f"Termes : {term_count}")
    print(f"Postings : {posting_count}")

    sandbox_engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit doit etre positif")

    build_sample(args.limit)
