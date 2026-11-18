"""Attend que l'index et le graphe soient prêts (initContainer Kubernetes).

Le backend ne devient « Ready » qu'une fois le Job d'initialisation
terminé : aucun trafic n'est envoyé vers un pod qui renverrait 503.
"""

import sys
import time

from sqlalchemy import func, select

from app.db.models import BookScore
from app.db.session import SessionLocal
from app.services.index_version import v2_ready

TIMEOUT = 3 * 60 * 60  # l'indexation complète prend ~30 min


def ready() -> bool:
    try:
        with SessionLocal() as db:
            return v2_ready(db) and bool(db.scalar(select(func.count()).select_from(BookScore)))
    except Exception:  # base pas encore joignable ou tables absentes
        return False


start = time.monotonic()
while not ready():
    if time.monotonic() - start > TIMEOUT:
        sys.exit("Index ou graphe toujours absent : le Job d'initialisation a-t-il échoué ?")
    print("En attente de l'index et du graphe...", flush=True)
    time.sleep(15)

print("Index et graphe prêts.", flush=True)
