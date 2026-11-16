"""Compare l'index V1 et V2 sans modifier PostgreSQL."""

import argparse
from collections import Counter
from pathlib import Path
from time import perf_counter

from sqlalchemy import select

from app.db.models import Book
from app.db.session import SessionLocal
from app.services.index_normalization import count_index_words
from app.services.word_count import count_words


def compare(limit: int = 200):
    with SessionLocal() as session:
        books = session.scalars(
            select(Book).order_by(Book.id)
        ).all()

    limit = min(limit, len(books))
    if limit == 0:
        raise RuntimeError("Aucun livre disponible.")

    # Echantillonnage regulier sur tout le corpus.
    selected = [
        books[i * len(books) // limit]
        for i in range(limit)
    ]

    terms_v1 = set()
    terms_v2 = set()

    postings_v1 = 0
    postings_v2 = 0

    time_v1 = 0.0
    time_v2 = 0.0
    languages = Counter()

    for position, book in enumerate(selected, 1):
        text = Path(book.text_path).read_text(
            encoding="utf-8",
            errors="replace",
        )

        start = perf_counter()
        old_counts = count_words(text)
        time_v1 += perf_counter() - start

        start = perf_counter()
        new_counts = count_index_words(
            text, book.language
        )
        time_v2 += perf_counter() - start

        terms_v1.update(old_counts)

        # Prefixe de langue pour eviter les collisions.
        terms_v2.update(
            f"{book.language}:{term}"
            for term in new_counts
        )

        postings_v1 += len(old_counts)
        postings_v2 += len(new_counts)
        languages[book.language] += 1

        if position % 25 == 0 or position == limit:
            print(
                f"Livres compares : {position}/{limit}",
                flush=True,
            )

    reduction = (
        100 * (postings_v1 - postings_v2) / postings_v1
        if postings_v1 else 0
    )

    print("\n=== COMPARAISON V1 / V2 ===")
    print(f"Livres : {limit}")
    print(f"Langues : {dict(languages)}")
    print(f"Termes V1 : {len(terms_v1)}")
    print(f"Termes V2 : {len(terms_v2)}")
    print(f"Postings V1 : {postings_v1}")
    print(f"Postings V2 : {postings_v2}")
    print(f"Reduction des postings : {reduction:.2f} %")
    print(f"Temps traitement V1 : {time_v1:.2f} s")
    print(f"Temps traitement V2 : {time_v2:.2f} s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit doit etre positif")

    compare(args.limit)
