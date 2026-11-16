"""Lecture des scores PageRank produits par le graphe P2."""

import json
import math
import os
from pathlib import Path


class PageRankUnavailable(RuntimeError):
    pass


def load_pagerank_scores():
    path = Path(os.environ.get(
        "PAGERANK_PATH", "/data/generated/graph-pilot.json"
    ))

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PageRankUnavailable(
            "Scores PageRank indisponibles : fichier absent ou JSON invalide."
        ) from exc

    raw = payload.get("pagerank") if isinstance(payload, dict) else None

    if not isinstance(raw, dict) or not raw:
        raise PageRankUnavailable("Aucun score PageRank disponible.")

    scores = {}

    for identifier, value in raw.items():
        try:
            book_id = int(identifier)
        except (TypeError, ValueError) as exc:
            raise PageRankUnavailable(
                "Identifiant PageRank invalide."
            ) from exc

        if (
            book_id <= 0
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            or book_id in scores
        ):
            raise PageRankUnavailable(
                "Fichier PageRank contenant des scores invalides."
            )

        scores[book_id] = float(value)

    book_count = payload.get("book_count")
    if book_count is not None and book_count != len(scores):
        raise PageRankUnavailable(
            "Nombre de scores PageRank incompatible avec le graphe."
        )

    return scores


def sort_pagerank_rows(rows, scores):
    missing = [row.id for row in rows if row.id not in scores]

    if missing:
        raise PageRankUnavailable(
            f"Scores PageRank manquants pour {len(missing)} "
            "livres correspondants. Le graphe P2 est incomplet."
        )

    return sorted(rows, key=lambda row: (-scores[row.id], row.id))
