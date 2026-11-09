from sqlalchemy import select

from app.db.models import Posting, Term

def load_book_vocabularies(
    session, *, limit: int | None = None
) -> dict[int, set[str]]:
    """Charge les mots distincts des livres présents dans l’index."""
    book_ids = select(Posting.book_id).distinct().order_by(Posting.book_id)

    if limit is not None:
        book_ids = book_ids.limit(limit)

    query = (
        select(Posting.book_id, Term.value)
        .join(Term, Term.id == Posting.term_id)
        .where(Posting.book_id.in_(book_ids))
        .order_by(Posting.book_id)
    )

    vocabularies: dict[int, set[str]] = {}
    for book_id, word in session.execute(query):
        vocabularies.setdefault(book_id, set()).add(word)

    return vocabularies