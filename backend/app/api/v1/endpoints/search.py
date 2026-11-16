from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.search import normalize_query, search_books
from app.services.regex_search import search_regex, validate_regex
from app.services.index_version import v2_ready
from app.services.pagerank_scores import PageRankUnavailable
from app.services.search_optimized import (
    search_books_v2,
    search_regex_v2,
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
    if not normalize_query(q):
        raise HTTPException(
            status_code=400,
            detail="La recherche doit contenir au moins un mot.",
        )

    if v2_ready(db):
        try:
            return search_books_v2(db, q, limit, offset, sort=sort)
        except PageRankUnavailable as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    if sort == "pagerank":
        raise HTTPException(
            status_code=503,
            detail="Index V2 indisponible pour le tri PageRank.",
        )

    return search_books(db, q, limit, offset)


@router.get(
    "/search/regex",
    summary="Recherche Regex sur les racines en V2",
)
def regex_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: Literal["occurrences", "pagerank"] = Query(default="occurrences"),
    db: Session = Depends(get_db),
):
    try:
        validate_regex(q)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    try:
        if v2_ready(db):
            return search_regex_v2(db, q, limit, offset, sort=sort)

        if sort == "pagerank":
            raise HTTPException(
                status_code=503,
                detail="Index V2 indisponible pour le tri PageRank.",
            )

        return search_regex(db, q, limit, offset)

    except PageRankUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    except DBAPIError as error:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Recherche regex interrompue ou non prise en charge.",
        ) from error
