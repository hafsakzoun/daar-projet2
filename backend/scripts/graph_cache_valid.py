"""Verifie qu'un graphe existant correspond aux livres indexes."""

import json
import math
import os
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.v2_models import PostingV2


def cache_is_valid():
    path = Path("/data/generated/graph-pilot.json")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False

    if not isinstance(data, dict):
        return False

    limit_text = os.environ.get("GRAPH_LIMIT", "").strip()
    limit = int(limit_text) if limit_text else None
    threshold = float(os.environ.get("GRAPH_THRESHOLD", "0.20"))

    if limit is not None and limit <= 0:
        return False

    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        return False

    query = (
        select(PostingV2.book_id)
        .distinct()
        .order_by(PostingV2.book_id)
    )

    if limit is not None:
        query = query.limit(limit)

    with SessionLocal() as session:
        expected_ids = {str(book_id) for book_id in session.scalars(query)}

    graph = data.get("graph")
    pagerank = data.get("pagerank")

    return (
        bool(expected_ids)
        and data.get("book_count") == len(expected_ids)
        and data.get("threshold") == threshold
        and data.get("damping") == 0.85
        and isinstance(graph, dict)
        and isinstance(pagerank, dict)
        and set(graph) == expected_ids
        and set(pagerank) == expected_ids
        and all(
            type(score) in (int, float)
            and math.isfinite(score)
            and score >= 0
            for score in pagerank.values()
        )
    )


if __name__ == "__main__":
    try:
        valid = cache_is_valid()
    except (ValueError, TypeError):
        valid = False

    print("CACHE GRAPHE : VALIDE" if valid else "CACHE GRAPHE : INVALIDE")
    sys.exit(0 if valid else 1)
