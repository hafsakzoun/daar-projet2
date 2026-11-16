from fastapi import APIRouter

from app.api.v1.endpoints import auth, books, health, search
api_router = APIRouter()

api_router.include_router(health.router, tags=["Santé"])
api_router.include_router(books.router, tags=["Livres"])
api_router.include_router(search.router, tags=["Recherche"])
api_router.include_router(auth.router)
