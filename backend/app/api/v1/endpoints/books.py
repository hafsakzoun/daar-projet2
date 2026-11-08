
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Book
from app.db.session import get_db
from app.schemas.book import BookSummary


router = APIRouter()


@router.get(
    "/books",
    response_model=list[BookSummary],
    summary="Lister les livres",
    description=(
        "Retourne les livres enregistrés dans PostgreSQL, "
        "avec une pagination."
    ),
)
def list_books(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[BookSummary]:

    # Récupérer les livres depuis PostgreSQL
    query = (
        select(Book)
        .order_by(Book.id)
        .offset(offset)
        .limit(limit)
    )

    books = db.scalars(query).all()

    # Convertir les résultats au format attendu par l'API
    return [
        BookSummary(
            id=book.id,
            title=book.title,
            author=book.author,
        )
        for book in books
    ]
