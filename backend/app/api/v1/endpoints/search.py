from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.index_version import v2_ready
from app.services.search_optimized import PageRankUnavailable, search_books_v2
from app.services.automate_v2 import AutomateV2, RegexError
from app.services.regex_automate_search_v2 import (
    search_regex_automate_v2,
    TooManyRegexMatches,
)

router = APIRouter()


@router.get("/search", summary="Rechercher des livres")
def search(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: Literal["occurrences", "pagerank"] = Query(default="occurrences"),
    db: Session = Depends(get_db),
):
    # Une requête composée uniquement de mots vides (« the ») renvoie
    # simplement 0 résultat ; seule une requête vide est refusée.
    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="La recherche doit contenir au moins un mot.",
        )

    if not v2_ready(db):
        raise HTTPException(
            status_code=503,
            detail="Index en cours de construction.",
        )

    try:
        return search_books_v2(db, q, limit, offset, sort=sort)
    except PageRankUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get(
    "/search/regex",
    summary="Recherche RegEx par automate sur l'index V2",
)
def regex_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: Literal["occurrences", "pagerank"] = Query(
        default="occurrences"
    ),
    db: Session = Depends(get_db),
):
    try:
        AutomateV2(q)
    except RegexError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if not v2_ready(db):
        raise HTTPException(
            status_code=503,
            detail="Index en cours de construction.",
        )

    try:
        return search_regex_automate_v2(
            db, q, limit, offset, sort=sort
        )
    except TooManyRegexMatches as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    except RegexError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except PageRankUnavailable as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error
