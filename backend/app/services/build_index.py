import argparse
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Book, Term, Posting
from app.db.session import SessionLocal
from app.services.word_count import count_words


BATCH_SIZE = 1000


def make_posting_rows(book_id, counts, term_ids):
    """Prépare les associations entre un livre et ses mots."""
    return [
        {
            "book_id": book_id,
            "term_id": term_ids[word],
            "frequency": frequency,
        }
        for word, frequency in counts.items()
    ]


def index_book(session, book):
    """Indexe un livre dans les tables terms et postings."""
    path = Path(book.text_path)

    if not path.is_file():
        raise FileNotFoundError(f"Livre introuvable : {path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    counts = count_words(text)
    words = list(counts.keys())
    term_ids = {}

    for start in range(0, len(words), BATCH_SIZE):
        batch = words[start:start + BATCH_SIZE]

        statement = insert(Term).values(
            [{"value": word} for word in batch]
        )
        statement = statement.on_conflict_do_nothing(
            index_elements=[Term.value]
        )
        session.execute(statement)

        rows = session.execute(
            select(Term.value, Term.id)
            .where(Term.value.in_(batch))
        ).all()

        term_ids.update({
            value: term_id for value, term_id in rows
        })

    postings = make_posting_rows(book.id, counts, term_ids)

    session.execute(
        delete(Posting).where(Posting.book_id == book.id)
    )

    for start in range(0, len(postings), BATCH_SIZE):
        batch = postings[start:start + BATCH_SIZE]
        session.execute(insert(Posting), batch)

    return len(postings)


def build_index(limit=None):
    """Construit l'index pour les livres sélectionnés."""
    with SessionLocal() as session:
        query = select(Book).order_by(Book.id)

        if limit is not None:
            query = query.limit(limit)

        books = session.scalars(query).all()

    print(f"Livres à indexer : {len(books)}", flush=True)

    for position, book in enumerate(books, start=1):
        with SessionLocal.begin() as session:
            count = index_book(session, book)

        print(
            f"[{position}/{len(books)}] "
            f"Livre {book.id} : {count} termes",
            flush=True,
        )

    print("Indexation terminée.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit doit être supérieur à zéro")

    build_index(args.limit)
