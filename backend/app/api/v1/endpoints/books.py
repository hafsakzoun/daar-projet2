from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
import json
from pathlib import Path

from app.db.models import Book
from app.db.session import get_db
from app.schemas.book import (
    BookDetail,
    BookList,
    BookRecommendation,
    BookRecommendations,
    BookSummary,
)

router = APIRouter()

GRAPH_PATH = Path("/data/generated/graph-pilot.json")


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

    try:
        graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))["graph"]
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Le graphe de recommandations est indisponible",
        ) from exc

    neighbors = graph.get(str(book_id))
    if neighbors is None:
        raise HTTPException(
            status_code=503,
            detail="Ce livre ne figure pas encore dans le graphe de recommandations",
        )

    ranked_neighbors = sorted(
        ((int(neighbor_id), score) for neighbor_id, score in neighbors.items()),
        key=lambda item: (-item[1], item[0]),
    )

    if not ranked_neighbors:
        return BookRecommendations(book_id=book_id, results=[])

    neighbor_ids = [neighbor_id for neighbor_id, _ in ranked_neighbors]
    books = db.scalars(select(Book).where(Book.id.in_(neighbor_ids))).all()
    books_by_id = {book.id: book for book in books}

    results = [
        BookRecommendation(
            id=neighbor_id,
            title=books_by_id[neighbor_id].title,
            author=books_by_id[neighbor_id].author,
            similarity=score,
        )
        for neighbor_id, score in ranked_neighbors
        if neighbor_id in books_by_id
    ]

    return BookRecommendations(book_id=book_id, results=results[:limit])