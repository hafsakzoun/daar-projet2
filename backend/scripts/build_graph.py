"""Construit le graphe de Jaccard et le PageRank, puis les stocke en base.

Lance par le service graph-init de Docker Compose :
    python -m scripts.build_graph [--force]

Tables remplies : book_similarities (aretes) et book_scores (PageRank).
"""

import argparse
import os
import statistics
from time import perf_counter

from sqlalchemy import delete, func, insert, select

from app.algorithms.jaccard import build_jaccard_graph
from app.algorithms.pagerank import compute_pagerank
from app.db.models import BookScore, BookSimilarity
from app.db.session import SessionLocal, engine
from app.db.v2_models import BookV2
from app.services.graph_corpus import load_book_vocabularies

DAMPING = 0.85
BATCH = 10_000


def graph_is_current(session) -> bool:
    """Le graphe est a jour si chaque livre indexe a un score."""
    indexed = session.scalar(select(func.count()).select_from(BookV2)) or 0
    scored = session.scalar(select(func.count()).select_from(BookScore)) or 0
    return indexed > 0 and indexed == scored


def store(session, graph, scores):
    """Remplace l'ancien graphe dans une seule transaction."""
    session.execute(delete(BookSimilarity))
    session.execute(delete(BookScore))

    edges = [
        {"book_id": book_id, "neighbor_id": neighbor_id, "similarity": similarity}
        for book_id, neighbors in graph.items()
        for neighbor_id, similarity in neighbors.items()
    ]
    for start in range(0, len(edges), BATCH):
        session.execute(insert(BookSimilarity), edges[start:start + BATCH])

    session.execute(
        insert(BookScore),
        [{"book_id": book_id, "pagerank": score} for book_id, score in scores.items()],
    )
    session.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="recalculer meme si a jour")
    args = parser.parse_args()

    threshold = float(os.environ.get("GRAPH_THRESHOLD") or 0.20)
    max_df_ratio = float(os.environ.get("GRAPH_MAX_DF") or 0.5)
    min_neighbors = int(os.environ.get("GRAPH_MIN_NEIGHBORS") or 5)
    if not 0 <= threshold <= 1 or not 0 < max_df_ratio <= 1 or min_neighbors < 0:
        parser.error("Parametres du graphe invalides.")

    BookSimilarity.__table__.create(engine, checkfirst=True)
    BookScore.__table__.create(engine, checkfirst=True)

    with SessionLocal() as session:
        if not args.force and graph_is_current(session):
            print("Graphe deja disponible.", flush=True)
            return

        start = perf_counter()
        vocabularies = load_book_vocabularies(session, max_df_ratio=max_df_ratio)
        if not vocabularies:
            parser.error("Aucun livre indexe. Lance d'abord l'indexation.")
        print(
            f"Vocabulaires charges : {len(vocabularies)} livres "
            f"({perf_counter() - start:.0f} s)",
            flush=True,
        )

        start = perf_counter()
        graph = build_jaccard_graph(
            vocabularies, threshold=threshold, min_neighbors=min_neighbors
        )
        scores = compute_pagerank(graph, damping=DAMPING)
        store(session, graph, scores)

        degrees = [len(neighbors) for neighbors in graph.values()]
        size = len(graph)
        print(
            f"Graphe : {size} livres, {sum(degrees) // 2} aretes, "
            f"densite {sum(degrees) / (size * (size - 1)):.3f}, "
            f"degre median {statistics.median(degrees)}, "
            f"{degrees.count(0)} isoles ({perf_counter() - start:.0f} s)",
            flush=True,
        )


if __name__ == "__main__":
    main()
