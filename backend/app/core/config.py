import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def read_secret(name: str, default: str = "") -> str:
    """Lit un secret depuis le fichier indiqué par NAME_FILE (secrets Docker,
    montés dans /run/secrets), sinon depuis la variable NAME (tests, CI)."""
    path = os.getenv(f"{name}_FILE", "").strip()
    if path:
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read().strip()
        except OSError:
            return default
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    project_name: str
    api_prefix: str
    cors_origins: tuple[str, ...]
    # Adresse publique du site, utilisée pour les liens envoyés par e-mail.
    # Jamais déduite de la requête (en-tête Host falsifiable).
    app_url: str
    # Envoi d'e-mails (vide = désactivé : les liens sont écrits dans les logs).
    smtp_host: str
    smtp_port: int
    smtp_user: str
    # repr=False : le mot de passe n'apparaît jamais dans un log ou une trace d'erreur.
    smtp_password: str = field(repr=False)
    mail_from: str = ""

    @property
    def mail_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)


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
    app_url=_env("APP_URL", "http://localhost:5173").rstrip("/"),
    smtp_host=_env("SMTP_HOST"),
    smtp_port=int(_env("SMTP_PORT", "587") or 587),
    smtp_user=_env("SMTP_USER"),
    # Les mots de passe d'application Gmail sont affichés avec des espaces.
    smtp_password=read_secret("SMTP_PASSWORD").replace(" ", ""),
    mail_from=_env("MAIL_FROM") or _env("SMTP_USER"),
)
