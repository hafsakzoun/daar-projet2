from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DAAR — Moteur de recherche de livres")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Données temporaires pour vérifier la connexion avec React.
BOOKS = [
    {"id": 1, "title": "Pride and Prejudice", "author": "Jane Austen"},
    {"id": 2, "title": "Moby Dick", "author": "Herman Melville"},
]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/books")
def get_books():
    return BOOKS