import json
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException


GRAPH_PATH = Path("/data/generated/graph-pilot.json")


@lru_cache(maxsize=1)
def load_pagerank_scores(file_version: tuple[int, int, int]) -> dict[int, float]:
    with GRAPH_PATH.open(encoding="utf-8") as file:
        scores = json.load(file)["pagerank"]

    if not isinstance(scores, dict) or not scores:
        raise ValueError("Scores PageRank absents")

    return {int(book_id): float(value) for book_id, value in scores.items()}


def fetch_search_page(db, query, score, book_id, limit, offset, sort):
    if sort == "occurrences":
        return db.execute(
            query.order_by(score.desc(), book_id.asc())
            .offset(offset)
            .limit(limit)
        ).all()

    try:
        info = GRAPH_PATH.stat()
        scores = load_pagerank_scores(
            (info.st_ino, info.st_mtime_ns, info.st_size)
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=503,
            detail="Les scores PageRank sont indisponibles.",
        ) from error

    rows = db.execute(query).all()
    rows.sort(key=lambda row: (-scores.get(row.id, 0.0), -row.score, row.id))
    return rows[offset:offset + limit]