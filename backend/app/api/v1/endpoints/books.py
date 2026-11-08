from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Book
from app.db.session import get_db
from app.schemas.book import BookDetail, BookList, BookSummary


router = APIRouter()


@router.get(
    "/books",
    response_model=BookList,
    summary="Lister les livres",
)
def list_books(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> BookList:
    total = db.scalar(select(func.count()).select_from(Book)) or 0

    query = (
        select(Book)
        .order_by(Book.id)
        .offset(offset)
        .limit(limit)
    )

    books = db.scalars(query).all()

    results = [
        BookSummary(
            id=book.id,
            title=book.title,
            author=book.author,
        )
        for book in books
    ]

    return BookList(
        total=total,
        offset=offset,
        limit=limit,
        results=results,
    )


@router.get(
    "/books/{book_id}",
    response_model=BookDetail,
    summary="Consulter un livre",
)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
) -> BookDetail:
    book = db.get(Book, book_id)

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Livre introuvable",
        )

    return BookDetail(
        id=book.id,
        title=book.title,
        author=book.author,
        language=book.language,
        word_count=book.word_count,
        source_url=book.source_url,
    )
