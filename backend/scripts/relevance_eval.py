"""Test de pertinence des classements (fréquence, PageRank, combinaisons).

Protocole
---------
Pour chaque requête, un livre est jugé *pertinent* si son titre ou son
auteur correspond à un critère objectif fixé à l'avance (ex. « whale » :
titre contenant whal ou Moby). Ce jugement automatique est reproductible ;
il sous-estime la pertinence réelle (un roman maritime sans « whale » dans
le titre peut être pertinent) mais il est identique pour tous les classements
comparés, ce qui suffit pour les départager.

Mesures sur les 10 premiers résultats :
- P@5 : part de livres pertinents dans les 5 premiers ;
- MRR : 1 / rang du premier livre pertinent ;
- nDCG@10 : gain cumulé actualisé, normalisé par le classement idéal.

Classements comparés :
- occurrences : fréquence normalisée (occurrences par million de mots) ;
- pagerank    : centralité dans le graphe de Jaccard ;
- produit     : fréquence × PageRank ;
- fusion      : fusion de rangs réciproques (RRF, k = 60) des deux premiers.

Usage : python -m scripts.relevance_eval --out /tmp/pertinence
"""

import argparse
import csv
import math
import re
import statistics
from pathlib import Path

from sqlalchemy import select

from app.db.models import Book, BookScore
from app.db.session import SessionLocal
from app.services.search_optimized import search_books_v2

# requête -> critère de pertinence sur « titre | auteur »
QUERIES = {
    "whale": r"whal|moby",
    "sherlock holmes": r"sherlock|holmes|doyle",
    "vampire": r"vamp[iy]r|dracula|carmilla",
    "pirate": r"pira|pyrat|treasure island|buccaneer",
    "alice": r"alice",
    "napoleon": r"napol|bonaparte",
    "egypt": r"egypt",
    "ghost": r"ghost",
    "garden": r"garden",
    "witch": r"witch",
    "recipe": r"cook|recipe",
}
TOP = 10
RRF_K = 60


def all_results(db, query):
    """Tous les livres contenant la requête, avec leur fréquence."""
    data = search_books_v2(db, query, limit=10_000)
    return [(book["id"], book["score"]) for book in data["results"]]


def rankings(results, pagerank):
    by_occurrence = [book_id for book_id, _ in results]  # déjà trié
    by_pagerank = sorted(by_occurrence, key=lambda b: (-pagerank.get(b, 0), b))
    score = dict(results)
    product = sorted(by_occurrence, key=lambda b: (-score[b] * pagerank.get(b, 0), b))

    rank_occ = {b: i for i, b in enumerate(by_occurrence, 1)}
    rank_pr = {b: i for i, b in enumerate(by_pagerank, 1)}
    fusion = sorted(
        by_occurrence,
        key=lambda b: (-(1 / (RRF_K + rank_occ[b]) + 1 / (RRF_K + rank_pr[b])), b),
    )
    return {
        "occurrences": by_occurrence,
        "pagerank": by_pagerank,
        "produit": product,
        "fusion": fusion,
    }


def metrics(ranked, relevant):
    top = ranked[:TOP]
    hits = [1 if book in relevant else 0 for book in top]
    p5 = sum(hits[:5]) / 5
    mrr = next((1 / rank for rank, hit in enumerate(hits, 1) if hit), 0.0)
    dcg = sum(hit / math.log2(rank + 1) for rank, hit in enumerate(hits, 1))
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant), TOP) + 1))
    return {"p5": p5, "mrr": mrr, "ndcg10": dcg / ideal if ideal else 0.0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        books = {b.id: f"{b.title} | {b.author}" for b in db.scalars(select(Book))}
        pagerank = dict(db.execute(select(BookScore.book_id, BookScore.pagerank)).all())

        rows, examples = [], []
        for query, criterion in QUERIES.items():
            pattern = re.compile(criterion, re.IGNORECASE)
            relevant = {b for b, label in books.items() if pattern.search(label)}
            results = all_results(db, query)
            found = relevant & {b for b, _ in results}

            for method, ranked in rankings(results, pagerank).items():
                rows.append({
                    "requete": query,
                    "classement": method,
                    "resultats": len(results),
                    "pertinents": len(found),
                    **{k: round(v, 3) for k, v in metrics(ranked, found).items()},
                })
                examples.append({
                    "requete": query,
                    "classement": method,
                    "top3": " ; ".join(
                        ("✓ " if b in found else "✗ ") + books[b].split(" | ")[0][:50]
                        for b in ranked[:3]
                    ),
                })

    with (args.out / "pertinence.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with (args.out / "exemples.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(examples[0]))
        writer.writeheader()
        writer.writerows(examples)

    print(f"{'classement':<12} {'P@5':>6} {'MRR':>6} {'nDCG@10':>8}")
    for method in ("occurrences", "pagerank", "produit", "fusion"):
        subset = [r for r in rows if r["classement"] == method]
        print(
            f"{method:<12} "
            f"{statistics.mean(r['p5'] for r in subset):>6.2f} "
            f"{statistics.mean(r['mrr'] for r in subset):>6.2f} "
            f"{statistics.mean(r['ndcg10'] for r in subset):>8.2f}"
        )


if __name__ == "__main__":
    main()
