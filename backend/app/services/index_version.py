"""Détermine si l'index V2 est complet et utilisable."""

from sqlalchemy import func, select, text

from app.db.models import Book
from app.db.v2_models import BookV2

# Une fois l'index complet, il le reste : inutile de recompter
# les livres (2 COUNT + 1 requête catalogue) à chaque recherche.
_ready = False


def v2_ready(db) -> bool:
    global _ready
    if _ready:
        return True

    exists = db.scalar(text("SELECT to_regclass('public.books_v2') IS NOT NULL"))
    if not exists:
        return False

    book_count = db.scalar(select(func.count()).select_from(Book)) or 0
    v2_count = db.scalar(select(func.count()).select_from(BookV2)) or 0

    _ready = book_count > 0 and v2_count == book_count
    return _ready
