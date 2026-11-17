"""Recherches sur l'index inverse optimise V2."""

import re

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.exc import ProgrammingError

from app.db.models import Book, BookScore
from app.db.v2_models import PostingV2, TermV2
from app.services.index_normalization import normalize_index_query


def validate_regex(pattern: str) -> str:
    """Vérifie la syntaxe d'une expression régulière (variante PostgreSQL)."""
    if not pattern or not pattern.strip():
        raise ValueError("Expression régulière vide.")
    if len(pattern) > 100:
        raise ValueError("Expression régulière trop longue.")
    try:
        re.compile(pattern)
    except re.error as error:
        raise ValueError("Expression régulière invalide.") from error
    return pattern

LANGUAGES = ("en", "fr", "de", "ang")


class PageRankUnavailable(RuntimeError):
    """Le graphe de Jaccard n'a pas encore ete calcule."""


def _response(db, query, score, limit, offset, sort="occurrences"):
    """Execute la requete paginee et met en forme la reponse.

    Le tri et la pagination sont faits par PostgreSQL : seuls les
    `limit` livres de la page demandee sont transferes.
    """
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    if sort == "pagerank":
        try:
            available = db.scalar(select(BookScore.book_id).limit(1))
        except ProgrammingError:  # table absente
            db.rollback()
            available = None
        if not available:
            raise PageRankUnavailable(
                "Scores PageRank indisponibles : le graphe n'est pas encore calcule."
            )
        pagerank = func.coalesce(func.max(BookScore.pagerank), 0.0).label("pagerank")
        query = (
            query.outerjoin(BookScore, BookScore.book_id == Book.id)
            .add_columns(pagerank)
            .order_by(pagerank.desc(), Book.id.asc())
        )
    else:
        query = query.order_by(score.desc(), Book.id.asc())

    rows = db.execute(query.offset(offset).limit(limit)).all()

    results = []
    for row in rows:
        item = {
            "id": row.id,
            "title": row.title,
            "author": row.author,
            "score": int(row.score),
        }
        if sort == "pagerank":
            item["pagerank"] = row.pagerank
        results.append(item)

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": results,
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


def search_books_v2(
    db, query, limit=20, offset=0, sort="occurrences", book_ids=None
):
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
    if book_ids is not None:
        # Utilise par le benchmark pour simuler un corpus plus petit.
        statement = statement.where(Book.id.in_(book_ids))

    return _response(db, statement, score, limit, offset, sort=sort)


def search_regex_v2(db, pattern, limit=20, offset=0, sort="occurrences"):
    pattern = validate_regex(pattern)

    # Comme la V1, proteger PostgreSQL des regex couteuses.
    db.execute(text("SET LOCAL statement_timeout = '15000ms'"))

    statement, score = _base_query()

    statement = statement.where(
        TermV2.value.op("~*")(f"^({pattern})$")
    )

    return _response(db, statement, score, limit, offset, sort=sort)
