import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


def preload_vocabulary() -> None:
    """Charge le vocabulaire RegEx en memoire sans bloquer le demarrage."""
    from app.db.session import SessionLocal
    from app.services.index_version import v2_ready
    from app.services.regex_automate_search_v2 import load_vocabulary

    try:
        with SessionLocal() as db:
            if v2_ready(db):
                load_vocabulary(db)
    except Exception as error:  # base indisponible : charge a la 1re requete
        print(f"Prechargement du vocabulaire ignore : {error}", flush=True)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Active par Docker Compose ; desactive dans les tests unitaires.
    if os.environ.get("PRELOAD_VOCABULARY") == "1":
        threading.Thread(target=preload_vocabulary, daemon=True).start()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        lifespan=lifespan,
        title=settings.project_name,
        description="API de recherche et de recommandation de livres.",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    application.include_router(
        api_router,
        prefix=settings.api_prefix,
    )

   

    return application


app = create_app()