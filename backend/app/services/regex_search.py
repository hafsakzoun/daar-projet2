import re

from sqlalchemy import func, select, text

from app.db.models import Book, Posting, Term


def validate_regex(pattern: str) -> str:
    """Vérifie la syntaxe de l'expression régulière."""
    if not pattern or not pattern.strip():
        raise ValueError("Expression régulière vide.")

    if len(pattern) > 100:
        raise ValueError("Expression régulière trop longue.")

    try:
        re.compile(pattern)
    except re.error as error:
        raise ValueError(
            "Expression régulière invalide."
        ) from error

    return pattern


def search_regex(db, pattern: str, limit: int = 20,
                 offset: int = 0):
    """Recherche les mots de l'index correspondant à une regex."""
    pattern = validate_regex(pattern)

    db.execute(text("SET LOCAL statement_timeout = '15000ms'"))

    expression = f"^({pattern})$"
    score = func.sum(Posting.frequency).label("score")

    query = (
        select(
            Book.id,
            Book.title,
            Book.author,
            score,
        )
        .join(Posting, Posting.book_id == Book.id)
        .join(Term, Term.id == Posting.term_id)
        .where(Term.value.op("~*")(expression))
        .group_by(Book.id, Book.title, Book.author)
    )

    total = db.scalar(
        select(func.count()).select_from(query.subquery())
    ) or 0

    rows = db.execute(
        query
        .order_by(score.desc(), Book.id.asc())
        .offset(offset)
        .limit(limit)
    ).all()

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
