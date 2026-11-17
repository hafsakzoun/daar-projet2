"""Vocabulaire discriminant de chaque livre, lu dans l'index V2."""

from sqlalchemy import func, select

from app.db.v2_models import BookV2, PostingV2


def load_book_vocabularies(session, *, max_df_ratio: float = 0.5) -> dict[int, set[int]]:
    """Renvoie {livre: ensemble d'identifiants de termes}.

    On ne garde que les termes presents dans au moins 2 livres et dans
    au plus `max_df_ratio` du corpus :
    - un terme propre a un seul livre ne peut pas etre partage ;
    - un terme present presque partout (« said », « time »…) rend tous
      les livres similaires et produit un graphe quasi complet.
    """
    book_ids = list(session.scalars(select(BookV2.id).order_by(BookV2.id)))
    max_df = max(2, int(len(book_ids) * max_df_ratio))

    kept_terms = (
        select(PostingV2.term_id)
        .group_by(PostingV2.term_id)
        .having(func.count().between(2, max_df))
        .subquery()
    )
    query = select(PostingV2.book_id, PostingV2.term_id).join(
        kept_terms, kept_terms.c.term_id == PostingV2.term_id
    )

    vocabularies: dict[int, set[int]] = {book_id: set() for book_id in book_ids}
    for book_id, term_id in session.execute(query.execution_options(yield_per=20_000)):
        vocabularies[book_id].add(term_id)

    return vocabularies
