import os
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr, Field, SecretStr, StringConstraints
from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AuthSession, AuthToken, Book, Favorite, SearchHistory, User
from app.db.session import get_db
from app.services import rate_limit
from app.services.emails import password_changed_email, reset_email, verification_email
from app.services.mailer import send_mail


router = APIRouter(prefix="/auth", tags=["Compte"])
DbSession = Annotated[Session, Depends(get_db)]

COOKIE_NAME = "lisiere_session"
SESSION_DURATION = timedelta(hours=24)
COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"

VERIFY_DURATION = timedelta(hours=48)
RESET_DURATION = timedelta(hours=1)

password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))

Password = Annotated[SecretStr, Field(min_length=12, max_length=128)]


class LoginInput(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)


class SignupInput(LoginInput):
    first_name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
    ]
    password: SecretStr = Field(min_length=12, max_length=128)


class PublicUser(BaseModel):
    id: int
    first_name: str
    email: EmailStr


class SignupResult(PublicUser):
    # Vrai si un e-mail de confirmation a été envoyé : le compte devra être
    # activé avant la première connexion.
    verification_required: bool


class EmailInput(BaseModel):
    email: EmailStr


class TokenInput(BaseModel):
    token: Annotated[str, StringConstraints(strip_whitespace=True, min_length=20, max_length=200)]


class ResetInput(TokenInput):
    password: Password


class Message(BaseModel):
    detail: str


class PasswordChangeInput(BaseModel):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: Password


_auth_schema_ready = False


def ensure_auth_schema(db: Session) -> None:
    """Ajoute colonne et table des e-mails sur une base créée avant elles
    (ex. base restaurée sur AWS). Idempotent, exécuté une fois par processus."""
    global _auth_schema_ready
    if _auth_schema_ready:
        return
    db.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
        "email_verified boolean NOT NULL DEFAULT true"
    ))
    db.commit()
    AuthToken.__table__.create(db.get_bind(), checkfirst=True)
    _auth_schema_ready = True


def issue_token(db: Session, user_id: int, purpose: str, duration: timedelta) -> str:
    """Crée un jeton à usage unique et invalide les précédents du même type."""
    db.execute(delete(AuthToken).where(
        AuthToken.user_id == user_id, AuthToken.purpose == purpose
    ))
    token = secrets.token_urlsafe(32)
    db.add(AuthToken(
        token_hash=hash_token(token),
        user_id=user_id,
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + duration,
    ))
    return token


def consume_token(db: Session, token: str, purpose: str) -> User:
    """Valide un jeton (bon type, non expiré, jamais utilisé) et le marque utilisé."""
    row = db.scalar(select(AuthToken).where(
        AuthToken.token_hash == hash_token(token),
        AuthToken.purpose == purpose,
        AuthToken.used_at.is_(None),
        AuthToken.expires_at > datetime.now(timezone.utc),
    ).with_for_update())
    if row is None:
        raise HTTPException(
            status_code=400,
            detail="Ce lien est invalide ou a expiré. Demande-en un nouveau.",
        )
    row.used_at = datetime.now(timezone.utc)
    return db.get(User, row.user_id)


def send_verification(background: BackgroundTasks, db: Session, user: User) -> None:
    token = issue_token(db, user.id, "verify", VERIFY_DURATION)
    background.add_task(send_mail, user.email, *verification_email(user.first_name, token))


def check_origin(request: Request) -> None:
    """Protection CSRF : la requête doit venir du site lui-même.

    On accepte l'origine si elle correspond à l'hôte demandé (même site,
    quelle que soit l'adresse : localhost, IP du Wi-Fi, AWS…) ou si elle
    figure dans CORS_ORIGINS.
    """
    origin = request.headers.get("origin")
    if origin is None or origin in settings.cors_origins:
        return
    if urlsplit(origin).netloc == request.headers.get("host"):
        return
    raise HTTPException(status_code=403, detail="Origine non autorisée.")


def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def public_user(user: User) -> PublicUser:
    return PublicUser(
        id=user.id,
        first_name=user.first_name,
        email=user.email,
    )


def open_session(
    db: Session,
    request: Request,
    response: Response,
    user_id: int,
) -> None:
    previous_token = request.cookies.get(COOKIE_NAME)
    if previous_token:
        db.execute(
            delete(AuthSession).where(
                AuthSession.token_hash == hash_token(previous_token)
            )
        )

    token = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            token_hash=hash_token(token),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + SESSION_DURATION,
        )
    )
    db.commit()

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=int(SESSION_DURATION.total_seconds()),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/api/v1/auth",
    )
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "/signup",
    status_code=201,
    response_model=SignupResult,
    dependencies=[Depends(check_origin)],
)
def signup(
    payload: SignupInput,
    request: Request,
    background: BackgroundTasks,
    db: DbSession,
) -> SignupResult:
    rate_limit.check(f"signup:{rate_limit.client_ip(request)}", limit=10, window_seconds=3600)
    ensure_auth_schema(db)
    email = str(payload.email).casefold()
    if len(email) > 254:
        raise HTTPException(status_code=422, detail="Adresse e-mail trop longue.")

    statement = (
        insert(User)
        .values(
            first_name=payload.first_name,
            email=email,
            password_hash=password_hasher.hash(payload.password.get_secret_value()),
            # Avec un serveur SMTP, l'adresse doit être confirmée.
            email_verified=not settings.mail_enabled,
        )
        .on_conflict_do_nothing(index_elements=[User.email])
        .returning(User)
    )
    user = db.scalars(statement).one_or_none()

    if user is None:
        raise HTTPException(
            status_code=409,
            detail="Un compte existe déjà avec cette adresse e-mail.",
        )

    if settings.mail_enabled:
        send_verification(background, db, user)

    result = SignupResult(
        **public_user(user).model_dump(),
        verification_required=settings.mail_enabled,
    )
    db.commit()
    return result


@router.post(
    "/login",
    response_model=PublicUser,
    dependencies=[Depends(check_origin)],
)
def login(
    payload: LoginInput,
    request: Request,
    response: Response,
    db: DbSession,
) -> PublicUser:
    email = str(payload.email).casefold()
    # Anti force brute : par adresse e-mail et par IP.
    rate_limit.check(f"login:{email}", limit=8, window_seconds=600)
    rate_limit.check(f"login-ip:{rate_limit.client_ip(request)}", limit=30, window_seconds=600)
    ensure_auth_schema(db)

    user = db.scalar(select(User).where(User.email == email))
    stored_hash = user.password_hash if user else dummy_hash
    valid_password = password_hasher.verify(
        payload.password.get_secret_value(),
        stored_hash,
    )

    if user is None or not valid_password:
        raise HTTPException(status_code=401, detail="E-mail ou mot de passe incorrect.")

    if not user.email_verified:
        # Le mot de passe est correct : on peut dire pourquoi l'accès est refusé.
        raise HTTPException(
            status_code=403,
            detail="Confirme ton adresse e-mail avant de te connecter.",
        )

    # Ménage : sessions expirées de cet utilisateur.
    db.execute(delete(AuthSession).where(
        AuthSession.user_id == user.id,
        AuthSession.expires_at <= datetime.now(timezone.utc),
    ))
    open_session(db, request, response, user.id)
    return public_user(user)


GENERIC_SENT = (
    "Si un compte correspond à cette adresse, un e-mail vient d'être envoyé."
)


@router.post(
    "/email/verify",
    response_model=Message,
    dependencies=[Depends(check_origin)],
)
def verify_email(payload: TokenInput, db: DbSession) -> Message:
    ensure_auth_schema(db)
    user = consume_token(db, payload.token, "verify")
    user.email_verified = True
    db.commit()
    return Message(detail="Ton adresse est confirmée. Tu peux te connecter.")


@router.post(
    "/email/resend",
    status_code=202,
    response_model=Message,
    dependencies=[Depends(check_origin)],
)
def resend_verification(
    payload: EmailInput, request: Request, background: BackgroundTasks, db: DbSession
) -> Message:
    email = str(payload.email).casefold()
    rate_limit.check(f"mail:{email}", limit=3, window_seconds=900)
    rate_limit.check(f"mail-ip:{rate_limit.client_ip(request)}", limit=10, window_seconds=900)
    ensure_auth_schema(db)

    user = db.scalar(select(User).where(User.email == email))
    # Même réponse que le compte existe ou non : pas d'énumération d'adresses.
    if user is not None and not user.email_verified:
        send_verification(background, db, user)
        db.commit()
    return Message(detail=GENERIC_SENT)


@router.post(
    "/password/forgot",
    status_code=202,
    response_model=Message,
    dependencies=[Depends(check_origin)],
)
def forgot_password(
    payload: EmailInput, request: Request, background: BackgroundTasks, db: DbSession
) -> Message:
    email = str(payload.email).casefold()
    rate_limit.check(f"mail:{email}", limit=3, window_seconds=900)
    rate_limit.check(f"mail-ip:{rate_limit.client_ip(request)}", limit=10, window_seconds=900)
    ensure_auth_schema(db)

    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        token = issue_token(db, user.id, "reset", RESET_DURATION)
        db.commit()
        # Envoi après la réponse : même durée que l'adresse existe ou non.
        background.add_task(send_mail, user.email, *reset_email(user.first_name, token))
    return Message(detail=GENERIC_SENT)


@router.post(
    "/password/reset",
    response_model=Message,
    dependencies=[Depends(check_origin)],
)
def reset_password(
    payload: ResetInput, request: Request, background: BackgroundTasks, db: DbSession
) -> Message:
    rate_limit.check(f"reset-ip:{rate_limit.client_ip(request)}", limit=10, window_seconds=900)
    ensure_auth_schema(db)

    user = consume_token(db, payload.token, "reset")
    user.password_hash = password_hasher.hash(payload.password.get_secret_value())
    # Recevoir le lien prouve que l'adresse appartient bien à l'utilisateur.
    user.email_verified = True
    # Déconnecte toutes les sessions ouvertes avec l'ancien mot de passe.
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    db.commit()
    background.add_task(send_mail, user.email, *password_changed_email(user.first_name))
    return Message(detail="Ton mot de passe a été changé. Tu peux te connecter.")


def current_user(request: Request, db: DbSession) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Tu dois te connecter.")

    user = db.scalar(
        select(User)
        .join(AuthSession, AuthSession.user_id == User.id)
        .where(
            AuthSession.token_hash == hash_token(token),
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
    )

    if user is None:
        raise HTTPException(status_code=401, detail="Session expirée ou invalide.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


@router.get("/me", response_model=PublicUser)
def me(user: CurrentUser, response: Response) -> PublicUser:
    response.headers["Cache-Control"] = "no-store"
    return public_user(user)


@router.post(
    "/password/change",
    response_model=Message,
    dependencies=[Depends(check_origin)],
)
def change_password(
    payload: PasswordChangeInput,
    request: Request,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
) -> Message:
    """Changement de mot de passe une fois connecté (ancien mot de passe exigé)."""
    rate_limit.check(f"change:{user.id}", limit=5, window_seconds=600)

    if not password_hasher.verify(payload.current_password.get_secret_value(), user.password_hash):
        raise HTTPException(status_code=400, detail="Le mot de passe actuel est incorrect.")

    new_password = payload.new_password.get_secret_value()
    if password_hasher.verify(new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Choisis un mot de passe différent de l'actuel.")

    user.password_hash = password_hasher.hash(new_password)
    # Ferme les autres sessions ; celle en cours reste ouverte.
    current = hash_token(request.cookies.get(COOKIE_NAME, ""))
    db.execute(delete(AuthSession).where(
        AuthSession.user_id == user.id, AuthSession.token_hash != current
    ))
    db.commit()
    background.add_task(send_mail, user.email, *password_changed_email(user.first_name))
    return Message(detail="Ton mot de passe a été modifié. Un e-mail de confirmation t'a été envoyé.")


@router.post("/logout", status_code=204, dependencies=[Depends(check_origin)])
def logout(request: Request, db: DbSession) -> Response:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_token(token)))
        db.commit()

    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/api/v1/auth",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
    )
    return response


# ───────────── Favoris et historique (stockés en base) ─────────────
# Ces routes sont sous /auth/me car le cookie de session
# n'est envoyé que sur le chemin /api/v1/auth.

HISTORY_LIMIT = 30
_activity_tables_ready = False


def ensure_activity_tables(db: Session) -> None:
    """Crée les tables si la base a été restaurée depuis une ancienne
    sauvegarde (ex. AWS) qui ne les contenait pas encore."""
    global _activity_tables_ready
    if _activity_tables_ready:
        return
    bind = db.get_bind()
    Favorite.__table__.create(bind, checkfirst=True)
    SearchHistory.__table__.create(bind, checkfirst=True)
    _activity_tables_ready = True


class FavoriteOut(BaseModel):
    id: int
    title: str
    author: str


class HistoryInput(BaseModel):
    query: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    ]
    mode: Literal["keyword", "regex"]


class HistoryOut(BaseModel):
    id: int
    query: str
    mode: str
    date: datetime


@router.get("/me/favorites", response_model=list[FavoriteOut])
def list_favorites(user: CurrentUser, db: DbSession) -> list[FavoriteOut]:
    ensure_activity_tables(db)
    rows = db.execute(
        select(Book.id, Book.title, Book.author)
        .join(Favorite, Favorite.book_id == Book.id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    ).all()
    return [FavoriteOut(id=r.id, title=r.title, author=r.author) for r in rows]


@router.put(
    "/me/favorites/{book_id}",
    status_code=204,
    dependencies=[Depends(check_origin)],
)
def add_favorite(book_id: int, user: CurrentUser, db: DbSession) -> Response:
    ensure_activity_tables(db)
    if db.get(Book, book_id) is None:
        raise HTTPException(status_code=404, detail="Livre introuvable")

    db.execute(
        insert(Favorite)
        .values(
            user_id=user.id,
            book_id=book_id,
            created_at=datetime.now(timezone.utc),
        )
        .on_conflict_do_nothing()
    )
    db.commit()
    return Response(status_code=204)


@router.delete(
    "/me/favorites/{book_id}",
    status_code=204,
    dependencies=[Depends(check_origin)],
)
def remove_favorite(book_id: int, user: CurrentUser, db: DbSession) -> Response:
    ensure_activity_tables(db)
    db.execute(
        delete(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.book_id == book_id,
        )
    )
    db.commit()
    return Response(status_code=204)


@router.get("/me/history", response_model=list[HistoryOut])
def list_history(user: CurrentUser, db: DbSession) -> list[HistoryOut]:
    ensure_activity_tables(db)
    entries = db.scalars(
        select(SearchHistory)
        .where(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    return [
        HistoryOut(id=e.id, query=e.query, mode=e.mode, date=e.created_at)
        for e in entries
    ]


@router.post(
    "/me/history",
    status_code=201,
    response_model=HistoryOut,
    dependencies=[Depends(check_origin)],
)
def add_history(payload: HistoryInput, user: CurrentUser, db: DbSession) -> HistoryOut:
    ensure_activity_tables(db)
    entry = SearchHistory(
        user_id=user.id,
        query=payload.query,
        mode=payload.mode,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.flush()

    # On ne garde que les 30 dernières recherches.
    keep = (
        select(SearchHistory.id)
        .where(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc())
        .limit(HISTORY_LIMIT)
    )
    db.execute(
        delete(SearchHistory).where(
            SearchHistory.user_id == user.id,
            SearchHistory.id.not_in(keep),
        )
    )
    db.commit()
    return HistoryOut(id=entry.id, query=entry.query, mode=entry.mode, date=entry.created_at)


@router.delete(
    "/me/history",
    status_code=204,
    dependencies=[Depends(check_origin)],
)
def clear_history(user: CurrentUser, db: DbSession) -> Response:
    ensure_activity_tables(db)
    db.execute(delete(SearchHistory).where(SearchHistory.user_id == user.id))
    db.commit()
    return Response(status_code=204)
