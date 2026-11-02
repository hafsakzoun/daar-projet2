import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    project_name: str
    api_prefix: str
    cors_origins: tuple[str, ...]


settings = Settings(
    project_name="Moteur de recherche de livres",
    api_prefix="/api/v1",
    cors_origins=tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ),
)