"""Recherche RegEx par automate sur les racines de l'index V2.

Le vocabulaire (toutes les racines de l'index) est charge une seule fois
en memoire, trie. Pour chaque requete :
1. on extrait les prefixes litteraux de l'expression (alic.* -> "alic") ;
2. une recherche dichotomique restreint le parcours aux racines qui
   commencent par ces prefixes ;
3. l'automate valide chaque racine candidate ;
4. PostgreSQL agrege les livres contenant les racines reconnues.
"""

from array import array
from bisect import bisect_left
from threading import Lock

from sqlalchemy import Integer, any_, literal, select
from sqlalchemy.dialects.postgresql import ARRAY

from app.db.v2_models import PostingV2, TermV2
from app.services.automate_v2 import AutomateV2, literal_prefixes
from app.services.search_optimized import _base_query, _response


MAX_MATCHED_TERMS = 20000

_vocabulary = None
_lock = Lock()


class TooManyRegexMatches(ValueError):
    pass


def load_vocabulary(db):
    """(valeurs triees, identifiants) de toutes les racines de l'index.

    Le tri est fait par PostgreSQL en ordre binaire (COLLATE "C"), qui
    coincide avec l'ordre des chaines Python : la recherche dichotomique
    reste valide. La lecture est faite par lots pour limiter la memoire.
    """
    global _vocabulary
    with _lock:
        if _vocabulary is None:
            values, ids = [], array("i")
            rows = db.execute(
                select(TermV2.value, TermV2.id)
                .order_by(TermV2.value.collate("C"), TermV2.id)
                .execution_options(yield_per=20_000)
            )
            for value, term_id in rows:
                values.append(value)
                ids.append(term_id)
            _vocabulary = (values, ids)
    return _vocabulary


def reset_vocabulary():
    """Oublie le vocabulaire en memoire (apres une reindexation, tests)."""
    global _vocabulary
    with _lock:
        _vocabulary = None


def candidate_ranges(values, prefixes):
    """Intervalles [debut, fin) des racines commencant par un prefixe."""
    if "" in prefixes:
        return [(0, len(values))]

    ranges = sorted(
        (bisect_left(values, prefix), bisect_left(values, prefix + "\U0010ffff"))
        for prefix in set(prefixes)
    )
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def matching_term_ids(db, automate):
    values, ids = load_vocabulary(db)
    prefixes, _ = literal_prefixes(automate.tree)
    matched = []

    for start, end in candidate_ranges(values, prefixes):
        for position in range(start, end):
            if automate.fullmatch_normalized(values[position]):
                matched.append(ids[position])
                if len(matched) > MAX_MATCHED_TERMS:
                    raise TooManyRegexMatches(
                        "Expression trop large : plus de "
                        "20000 termes correspondants."
                    )
    return matched


def search_regex_automate_v2(
    db, pattern, limit=20, offset=0, sort="occurrences"
):
    matched_ids = matching_term_ids(db, AutomateV2(pattern))

    if not matched_ids:
        return {
            "total": 0,
            "offset": offset,
            "limit": limit,
            "results": [],
        }

    query, score = _base_query()
    # Un seul parametre tableau (au lieu de milliers de valeurs IN) ;
    # le filtre porte sur postings_v2.term_id, qui est indexe.
    query = query.where(
        PostingV2.term_id == any_(literal(matched_ids, ARRAY(Integer)))
    )

    return _response(
        db, query, score, limit, offset, sort=sort
    )
