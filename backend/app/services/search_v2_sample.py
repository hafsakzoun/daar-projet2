"""Recherche simple et Regex dans l'index V2 de test."""

import argparse

from sqlalchemy import and_, create_engine, func, or_, select, text
from sqlalchemy.orm import Session

from app.db.session import DATABASE_URL
from app.db.v2_models import BookV2, PostingV2, TermV2
from app.services.index_normalization import normalize_index_query
from app.services.regex_search import validate_regex


SANDBOX_DB = "daar_v2_sandbox"
LANGUAGES = ("en", "fr", "de", "ang")


def search_v2(session, query, regex=False, limit=10):
    score = func.sum(PostingV2.frequency).label("score")

    statement = (
        select(BookV2.id, BookV2.title, BookV2.language, score)
        .join(PostingV2, PostingV2.book_id == BookV2.id)
        .join(TermV2, TermV2.id == PostingV2.term_id)
        .where(TermV2.language == BookV2.language)
    )

    if regex:
        pattern = validate_regex(query)
        session.execute(text("SET LOCAL statement_timeout = '15000ms'"))
        statement = statement.where(
            TermV2.value.op("~*")(f"^({pattern})$")
        )
    else:
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
            return []

        statement = statement.where(or_(*conditions))

    return session.execute(
        statement
        .group_by(BookV2.id, BookV2.title, BookV2.language)
        .order_by(score.desc(), BookV2.id)
        .limit(limit)
    ).all()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--regex", action="store_true")
    args = parser.parse_args()

    engine = create_engine(
        DATABASE_URL.set(database=SANDBOX_DB),
        pool_pre_ping=True,
    )

    with Session(engine) as session:
        results = search_v2(
            session,
            args.query,
            regex=args.regex,
        )

    print(f"\nRecherche V2 : {args.query}")
    print(f"Resultats affiches : {len(results)}")

    for row in results:
        print(
            f"{row.id} | {row.language} | "
            f"score={row.score} | {row.title}"
        )

    engine.dispose()


if __name__ == "__main__":
    main()
