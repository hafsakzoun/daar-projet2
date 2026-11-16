"""Determine si l'index optimise V2 est utilisable."""

import os

from sqlalchemy import func, select, text

from app.db.models import Book
from app.db.v2_models import BookV2


def v2_ready(db) -> bool:
    # Les tests historiques continuent a utiliser la V1.
    if os.environ.get("DAAR_TEST_DB") == "1":
        return False

    # Option de retour immediat a la V1.
    if os.environ.get("DAAR_SEARCH_INDEX") == "v1":
        return False

    exists = db.scalar(
        text("SELECT to_regclass('public.books_v2') IS NOT NULL")
    )
    if not exists:
        return False

    book_count = db.scalar(
        select(func.count()).select_from(Book)
    ) or 0

    v2_count = db.scalar(
        select(func.count()).select_from(BookV2)
    ) or 0

    return book_count > 0 and v2_count == book_count
