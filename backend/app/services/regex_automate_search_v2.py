"""Recherche RegEx par automate sur les racines de l'index V2."""

from sqlalchemy import select

from app.db.v2_models import TermV2
from app.services.automate_v2 import AutomateV2
from app.services.search_optimized import _base_query, _response


MAX_MATCHED_TERMS = 20000


class TooManyRegexMatches(ValueError):
    pass


def search_regex_automate_v2(
    db, pattern, limit=20, offset=0, sort="occurrences"
):
    automate = AutomateV2(pattern)
    matched_ids = []

    statement = (
        select(TermV2.id, TermV2.value)
        .order_by(TermV2.id)
        .execution_options(yield_per=5000)
    )

    result = db.execute(statement)

    try:
        for term_id, word in result:
            if automate.fullmatch(word):
                matched_ids.append(term_id)

                if len(matched_ids) > MAX_MATCHED_TERMS:
                    raise TooManyRegexMatches(
                        "Expression trop large : plus de "
                        "20000 termes correspondants."
                    )
    finally:
        result.close()

    if not matched_ids:
        return {
            "total": 0,
            "offset": offset,
            "limit": limit,
            "results": [],
        }

    query, score = _base_query()
    query = query.where(TermV2.id.in_(matched_ids))

    return _response(
        db, query, score, limit, offset, sort=sort
    )
