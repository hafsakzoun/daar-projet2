"""Benchmark P1 des recherches sur les 1700 livres."""

import csv
import random
import statistics
import sys
from time import perf_counter

from sqlalchemy import func, select, text

from app.db.models import Book, Posting, Term
from app.db.session import SessionLocal
from app.services.search import normalize_query
from app.services.regex_search import validate_regex

REPETITIONS = 20

QUERIES = [
    ("simple", "alice"),
    ("simple", "love"),
    ("simple", "king"),
    ("regex", "alice|rabbit"),
    ("regex", "love|heart"),
    ("regex", "king|queen"),
]


def run_search(session, mode, expression):
    if mode == "simple":
        condition = Term.value.in_(
            normalize_query(expression)
        )
    else:
        validate_regex(expression)
        session.execute(
            text("SET LOCAL statement_timeout = '15000ms'")
        )
        condition = Term.value.op("~*")(
            f"^({expression})$"
        )

    score = func.sum(Posting.frequency).label("score")

    query = (
        select(Book.id, Book.title, Book.author, score)
        .join(Posting, Posting.book_id == Book.id)
        .join(Term, Term.id == Posting.term_id)
        .where(condition)
        .group_by(Book.id, Book.title, Book.author)
    )

    total = session.scalar(
        select(func.count()).select_from(query.subquery())
    ) or 0

    session.execute(
        query.order_by(score.desc(), Book.id.asc()).limit(20)
    ).all()

    return total


def main():
    with SessionLocal() as session:
        corpus_size = session.scalar(
            select(func.count()).select_from(Book)
        )

        if corpus_size != 1700:
            raise RuntimeError(
                f"1700 livres attendus : {corpus_size} trouves"
            )

        samples = {query: [] for query in QUERIES}
        totals = {}

        # Échauffement
        for query in QUERIES:
            for _ in range(2):
                totals[query] = run_search(session, *query)

        # Ordre mélangé pour limiter les biais de cache
        for repetition in range(REPETITIONS):
            order = list(QUERIES)
            random.Random(42 + repetition).shuffle(order)

            for query in order:
                start = perf_counter()
                totals[query] = run_search(session, *query)
                elapsed = (perf_counter() - start) * 1000
                samples[query].append(elapsed)

        writer = csv.writer(sys.stdout)
        writer.writerow([
            "mode", "requete", "livres",
            "repetitions", "resultats",
            "moyenne_ms", "ecart_type_ms",
            "mediane_ms", "min_ms", "max_ms"
        ])

        for query in QUERIES:
            values = samples[query]
            writer.writerow([
                query[0],
                query[1],
                corpus_size,
                REPETITIONS,
                totals[query],
                round(statistics.mean(values), 2),
                round(statistics.stdev(values), 2),
                round(statistics.median(values), 2),
                round(min(values), 2),
                round(max(values), 2),
            ])


if __name__ == "__main__":
    main()
