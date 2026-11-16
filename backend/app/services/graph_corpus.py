"""Chargement des vocabulaires pour le graphe Jaccard, via V2."""

from sys import intern

from sqlalchemy import select

from app.db.v2_models import PostingV2, TermV2


def load_book_vocabularies(
    session, *, limit: int | None = None
) -> dict[int, set[str]]:
    """Charge les racines distinctes des livres indexes en V2."""

    book_ids = (
        select(PostingV2.book_id)
        .distinct()
        .order_by(PostingV2.book_id)
    )

    if limit is not None:
        book_ids = book_ids.limit(limit)

    query = (
        select(
            PostingV2.book_id,
            TermV2.language,
            TermV2.value,
        )
        .join(TermV2, TermV2.id == PostingV2.term_id)
        .where(PostingV2.book_id.in_(book_ids))
        .order_by(PostingV2.book_id)
    )

    vocabularies: dict[int, set[str]] = {}

    for book_id, language, word in session.execute(
        query.execution_options(yield_per=5000)
    ):
        token = intern(f"{language}:{word}")
        vocabularies.setdefault(book_id, set()).add(token)

    return vocabularies
