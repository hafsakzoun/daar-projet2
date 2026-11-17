from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session
from pathlib import Path

from app.db.models import Book, BookSimilarity
from app.db.session import get_db
from app.schemas.book import (
    BookDetail,
    BookList,
    BookRecommendation,
    BookRecommendations,
    BookSummary,
    BookText,
)

router = APIRouter()

CORPUS_DIR = Path("/data/books")


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

@router.get(
    "/books/{book_id}/text",
    response_model=BookText,
    summary="Lire le texte d'un livre",
)
def read_book_text(
    book_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=40_000, ge=1, le=200_000),
    db: Session = Depends(get_db),
) -> BookText:
    """Renvoie un extrait du texte, pagine en caracteres.

    Certains livres depassent 4 Mo : on n'envoie qu'une tranche a la fois.
    """
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Livre introuvable")

    path = CORPUS_DIR / f"{book_id}.txt"
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail="Le texte de ce livre est indisponible",
        ) from exc

    chunk = content[offset : offset + limit]
    return BookText(
        id=book.id,
        title=book.title,
        author=book.author,
        offset=offset,
        length=len(chunk),
        total=len(content),
        text=chunk,
    )


@router.get(
    "/books/{book_id}/recommendations",
    response_model=BookRecommendations,
    summary="Recommander des livres similaires",
)
def recommend_books(
    book_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> BookRecommendations:
    if db.get(Book, book_id) is None:
        raise HTTPException(status_code=404, detail="Livre introuvable")

    # Voisins du livre dans le graphe de Jaccard, du plus proche au plus loin.
    try:
        rows = db.execute(
            select(Book.id, Book.title, Book.author, BookSimilarity.similarity)
            .join(BookSimilarity, BookSimilarity.neighbor_id == Book.id)
            .where(BookSimilarity.book_id == book_id)
            .order_by(BookSimilarity.similarity.desc(), Book.id)
            .limit(limit)
        ).all()
    except ProgrammingError as exc:  # table absente : graphe jamais calcule
        raise HTTPException(
            status_code=503,
            detail="Le graphe de recommandations est indisponible",
        ) from exc

    return BookRecommendations(
        book_id=book_id,
        results=[
            BookRecommendation(
                id=row.id, title=row.title, author=row.author, similarity=row.similarity
            )
            for row in rows
        ],
    )
