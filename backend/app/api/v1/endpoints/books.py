from fastapi import APIRouter

from app.schemas.book import BookSummary

router = APIRouter()

DEMO_BOOKS = [
    BookSummary(
        id=1,
        title="Pride and Prejudice",
        author="Jane Austen",
    ),
    BookSummary(
        id=2,
        title="Moby Dick",
        author="Herman Melville",
    ),
]


@router.get(
    "/books",
    response_model=list[BookSummary],
    summary="Lister les livres",
    description=(
        "Retourne actuellement les livres de démonstration. "
        "Le catalogue SQLite sera intégré à l’étape suivante."
    ),
)
def list_books() -> list[BookSummary]:
    return DEMO_BOOKS