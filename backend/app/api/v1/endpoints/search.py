from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.search import normalize_query, search_books


router = APIRouter()


@router.get("/search", summary="Rechercher des livres")
def search(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if not normalize_query(q):
        raise HTTPException(
            status_code=400,
            detail="La recherche doit contenir au moins un mot.",
        )

    return search_books(db, q, limit, offset)
