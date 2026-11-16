from sqlalchemy import func, select

from app.db.models import Book, Posting, Term
from app.services.normalization import tokenize
from app.services.search_order import fetch_search_page


def normalize_query(query: str) -> list[str]:
    """Normalise la recherche sans répéter les mots."""
    return list(dict.fromkeys(tokenize(query)))


def search_books(
    db,
    query: str,
    limit: int = 20,
    offset: int = 0,
    *,
    sort: str = "occurrences",
):
    """Recherche les livres et les trie par occurrences ou PageRank."""
    words = normalize_query(query)

    if not words:
        return {
            "total": 0,
            "offset": offset,
            "limit": limit,
            "results": [],
        }

    score = func.sum(Posting.frequency).label("score")

    base_query = (
        select(Book.id, Book.title, Book.author, score)
        .join(Posting, Posting.book_id == Book.id)
        .join(Term, Term.id == Posting.term_id)
        .where(Term.value.in_(words))
        .group_by(Book.id, Book.title, Book.author)
    )

    total = db.scalar(
        select(func.count()).select_from(base_query.subquery())
    ) or 0

    rows = fetch_search_page(db, base_query, score, Book.id, limit, offset, sort)

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [
            {
                "id": row.id,
                "title": row.title,
                "author": row.author,
                "score": int(row.score),
            }
            for row in rows
        ],
    }