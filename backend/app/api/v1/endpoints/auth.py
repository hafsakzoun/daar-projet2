import os
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr, Field, SecretStr, StringConstraints
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AuthSession, User
from app.db.session import get_db


router = APIRouter(prefix="/auth", tags=["Compte"])
DbSession = Annotated[Session, Depends(get_db)]

COOKIE_NAME = "lisiere_session"
SESSION_DURATION = timedelta(hours=24)
COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"

password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


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


def check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
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
    response_model=PublicUser,
    dependencies=[Depends(check_origin)],
)
def signup(
    payload: SignupInput,
    db: DbSession,
) -> PublicUser:
    email = str(payload.email).casefold()
    if len(email) > 254:
        raise HTTPException(status_code=422, detail="Adresse e-mail trop longue.")

    statement = (
        insert(User)
        .values(
            first_name=payload.first_name,
            email=email,
            password_hash=password_hasher.hash(payload.password.get_secret_value()),
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

    result = public_user(user)
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
    user = db.scalar(select(User).where(User.email == str(payload.email).casefold()))
    stored_hash = user.password_hash if user else dummy_hash
    valid_password = password_hasher.verify(
        payload.password.get_secret_value(),
        stored_hash,
    )

    if user is None or not valid_password:
        raise HTTPException(status_code=401, detail="E-mail ou mot de passe incorrect.")

    open_session(db, request, response, user.id)
    return public_user(user)


@router.get("/me", response_model=PublicUser)
def me(request: Request, response: Response, db: DbSession) -> PublicUser:
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

    response.headers["Cache-Control"] = "no-store"
    return public_user(user)


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