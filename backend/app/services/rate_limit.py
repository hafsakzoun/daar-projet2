"""Limitation du nombre de tentatives (anti force brute, anti spam d'e-mails).

Fenêtre glissante en mémoire : suffisant pour un processus uvicorn. Avec
plusieurs répliques (Kubernetes), chaque pod compte de son côté ; il
faudrait alors un stockage partagé (Redis).
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

_hits: dict[str, deque] = defaultdict(deque)
_lock = Lock()


def client_ip(request: Request) -> str:
    # nginx transmet l'adresse réelle ; le backend n'est pas exposé directement.
    return request.headers.get("x-real-ip") or (request.client.host if request.client else "?")


def check(key: str, limit: int, window_seconds: int) -> None:
    """Lève 429 si `key` a dépassé `limit` appels sur la fenêtre."""
    now = time.monotonic()
    with _lock:
        hits = _hits[key]
        while hits and now - hits[0] > window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            retry = int(window_seconds - (now - hits[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="Trop de tentatives. Réessaie dans quelques minutes.",
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)


def reset() -> None:
    """Vide les compteurs (tests)."""
    with _lock:
        _hits.clear()
