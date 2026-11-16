"""Recherches sur l'index inverse optimise V2."""

from sqlalchemy import and_, func, or_, select, text

from app.db.models import Book
from app.db.v2_models import PostingV2, TermV2
from app.services.index_normalization import normalize_index_query
from app.services.regex_search import validate_regex


LANGUAGES = ("en", "fr", "de", "ang")


def _response(db, query, score, limit, offset):
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


def _base_query():
    # Frequence relative : occurrences par million de mots.
    score = (
        1_000_000.0 * func.sum(PostingV2.frequency)
        / func.max(Book.word_count)
    ).label("score")

    query = (
        select(
            Book.id,
            Book.title,
            Book.author,
            score,
        )
        .join(PostingV2, PostingV2.book_id == Book.id)
        .join(TermV2, TermV2.id == PostingV2.term_id)
        .where(TermV2.language == Book.language)
        .group_by(Book.id, Book.title, Book.author)
    )

    return query, score


def search_books_v2(db, query, limit=20, offset=0):
    conditions = []

    for language in LANGUAGES:
        stems = normalize_index_query(query, language)

        if stems:
            conditions.append(
                and_(
                    TermV2.language == language,
                    TermV2.value.in_(stems),
                )
            )

    if not conditions:
        return {
            "total": 0,
            "offset": offset,
            "limit": limit,
            "results": [],
        }

    statement, score = _base_query()
    statement = statement.where(or_(*conditions))

    return _response(db, statement, score, limit, offset)


def search_regex_v2(db, pattern, limit=20, offset=0):
    pattern = validate_regex(pattern)

    # Comme la V1, proteger PostgreSQL des regex couteuses.
    db.execute(text("SET LOCAL statement_timeout = '15000ms'"))

    statement, score = _base_query()

    statement = statement.where(
        TermV2.value.op("~*")(f"^({pattern})$")
    )

    return _response(db, statement, score, limit, offset)
