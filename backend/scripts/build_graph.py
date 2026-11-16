import argparse
import json

from app.algorithms.jaccard import build_jaccard_graph
from app.algorithms.pagerank import compute_pagerank
from app.db.session import SessionLocal
from app.services.graph_corpus import load_book_vocabularies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=0.20)
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit doit être supérieur à zéro")
    if not 0 <= args.threshold <= 1:
        parser.error("--threshold doit être compris entre 0 et 1")

    with SessionLocal() as session:
        vocabularies = load_book_vocabularies(session, limit=args.limit)

    if not vocabularies:
        parser.error("Aucun livre indexé. Lance d’abord l’indexation.")

    graph = build_jaccard_graph(vocabularies, threshold=args.threshold)
    damping = 0.85
    scores = compute_pagerank(graph, damping=damping)

    result = {
        "book_count": len(vocabularies),
        "threshold": args.threshold,
        "damping": damping,
        "graph": graph,
        "pagerank": scores,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()