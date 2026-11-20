"""Inscription confirmée par e-mail et mot de passe oublié (base daar_test)."""

import dataclasses
import re

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import auth
from app.main import app
from app.services import rate_limit

PASSWORD = "mot-de-passe-de-test-123"
NEW_PASSWORD = "nouveau-mot-de-passe-456"


@pytest.fixture
def mailbox(seeded_db, monkeypatch):
    """Active l'envoi d'e-mails et capture les messages au lieu de les envoyer."""
    sent = []
    monkeypatch.setattr(
        auth, "settings",
        dataclasses.replace(auth.settings, smtp_host="smtp.test", smtp_user="u", smtp_password="p"),
    )
    monkeypatch.setattr(auth, "send_mail", lambda to, subject, text, html: sent.append((to, subject, text)))
    monkeypatch.setattr(auth, "_auth_schema_ready", False)
    rate_limit.reset()
    yield sent
    rate_limit.reset()


def link_token(message_text):
    return re.search(r"jeton=([\w-]+)", message_text).group(1)


def signup(http, email="lecteur@example.org"):
    return http.post(
        "/api/v1/auth/signup",
        json={"first_name": "Lou", "email": email, "password": PASSWORD},
    )


def login(http, email="lecteur@example.org", password=PASSWORD):
    return http.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_signup_requires_email_confirmation(mailbox):
    with TestClient(app) as http:
        response = signup(http)
        assert response.status_code == 201
        assert response.json()["verification_required"] is True

        # Un e-mail de confirmation a été envoyé, avec un lien vers le site.
        to, subject, text = mailbox[-1]
        assert to == "lecteur@example.org"
        assert "Confirme" in subject
        assert "/#/verifier?jeton=" in text

        # Connexion refusée tant que l'adresse n'est pas confirmée.
        assert login(http).status_code == 403

        token = link_token(text)
        assert http.post("/api/v1/auth/email/verify", json={"token": token}).status_code == 200
        assert login(http).status_code == 200

        # Lien recliqué après confirmation : pas d'erreur, message « déjà confirmée ».
        again = http.post("/api/v1/auth/email/verify", json={"token": token})
        assert again.status_code == 200
        assert "déjà confirmée" in again.json()["detail"]


def test_resend_confirmation_replaces_old_link(mailbox):
    with TestClient(app) as http:
        signup(http)
        first = link_token(mailbox[-1][2])
        assert http.post("/api/v1/auth/email/resend", json={"email": "lecteur@example.org"}).status_code == 202
        second = link_token(mailbox[-1][2])

        assert first != second
        assert http.post("/api/v1/auth/email/verify", json={"token": first}).status_code == 400
        assert http.post("/api/v1/auth/email/verify", json={"token": second}).status_code == 200


def test_forgot_password_flow(mailbox):
    with TestClient(app) as http:
        signup(http)
        http.post("/api/v1/auth/email/verify", json={"token": link_token(mailbox[-1][2])})
        assert login(http).status_code == 200

        response = http.post("/api/v1/auth/password/forgot", json={"email": "lecteur@example.org"})
        assert response.status_code == 202
        to, subject, text = mailbox[-1]
        assert "mot de passe" in subject
        token = link_token(text)

        # Mot de passe trop court refusé.
        assert http.post("/api/v1/auth/password/reset", json={"token": token, "password": "court"}).status_code == 422

        assert http.post("/api/v1/auth/password/reset", json={"token": token, "password": NEW_PASSWORD}).status_code == 200
        # Les sessions ouvertes avec l'ancien mot de passe sont fermées.
        assert http.get("/api/v1/auth/me").status_code == 401

        assert login(http).status_code == 401
        assert login(http, password=NEW_PASSWORD).status_code == 200
        # Lien à usage unique.
        assert http.post("/api/v1/auth/password/reset", json={"token": token, "password": NEW_PASSWORD}).status_code == 400


def test_forgot_password_does_not_reveal_accounts(mailbox):
    with TestClient(app) as http:
        known = http.post("/api/v1/auth/password/forgot", json={"email": "personne@example.org"})
        assert known.status_code == 202
        assert mailbox == []  # aucun e-mail pour une adresse inconnue

        signup(http)
        existing = http.post("/api/v1/auth/password/forgot", json={"email": "lecteur@example.org"})
        assert existing.json() == known.json()


def test_invalid_or_expired_reset_token(mailbox):
    with TestClient(app) as http:
        response = http.post(
            "/api/v1/auth/password/reset",
            json={"token": "x" * 43, "password": NEW_PASSWORD},
        )
        assert response.status_code == 400


def test_login_is_rate_limited(mailbox):
    with TestClient(app) as http:
        codes = [login(http, email="cible@example.org", password="mauvais").status_code for _ in range(10)]
        assert codes[:8] == [401] * 8
        assert codes[8:] == [429, 429]


def verified_account(http, mailbox):
    signup(http)
    http.post("/api/v1/auth/email/verify", json={"token": link_token(mailbox[-1][2])})


def test_reset_sends_password_changed_alert(mailbox):
    with TestClient(app) as http:
        verified_account(http, mailbox)
        http.post("/api/v1/auth/password/forgot", json={"email": "lecteur@example.org"})
        token = link_token(mailbox[-1][2])
        http.post("/api/v1/auth/password/reset", json={"token": token, "password": NEW_PASSWORD})

        to, subject, _ = mailbox[-1]
        assert to == "lecteur@example.org"
        assert "modifié" in subject


def test_change_password_when_logged_in(mailbox):
    with TestClient(app) as http:
        verified_account(http, mailbox)

        # Il faut être connecté.
        anonymous = http.post(
            "/api/v1/auth/password/change",
            json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        )
        assert anonymous.status_code == 401

        assert login(http).status_code == 200

        wrong = http.post(
            "/api/v1/auth/password/change",
            json={"current_password": "pas-le-bon-mot-de-passe", "new_password": NEW_PASSWORD},
        )
        assert wrong.status_code == 400

        same = http.post(
            "/api/v1/auth/password/change",
            json={"current_password": PASSWORD, "new_password": PASSWORD},
        )
        assert same.status_code == 400

        ok = http.post(
            "/api/v1/auth/password/change",
            json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        )
        assert ok.status_code == 200
        # La session en cours reste ouverte.
        assert http.get("/api/v1/auth/me").status_code == 200
        # Un e-mail d'alerte est envoyé.
        assert "modifié" in mailbox[-1][1]

    with TestClient(app) as other:
        assert login(other).status_code == 401
        assert login(other, password=NEW_PASSWORD).status_code == 200


def test_delete_account(mailbox, monkeypatch):
    from sqlalchemy import func, select

    from app.db.models import AuthToken, Favorite, SearchHistory, User
    from app.db.session import SessionLocal

    with TestClient(app) as http:
        verified_account(http, mailbox)
        assert login(http).status_code == 200
        http.put("/api/v1/auth/me/favorites/11")
        http.post("/api/v1/auth/me/history", json={"query": "alice", "mode": "keyword"})

        # Mot de passe exigé.
        wrong = http.post("/api/v1/auth/me/delete", json={"password": "pas-le-bon"})
        assert wrong.status_code == 400

        ok = http.post("/api/v1/auth/me/delete", json={"password": PASSWORD})
        assert ok.status_code == 204
        assert "supprimé" in mailbox[-1][1]

        # Déconnecté, et le compte n'existe plus.
        assert http.get("/api/v1/auth/me").status_code == 401
        assert login(http).status_code == 401

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(User).where(User.email == "lecteur@example.org")) == 0
        # Données liées supprimées en cascade.
        assert db.scalar(select(func.count()).select_from(Favorite)) == 0
        assert db.scalar(select(func.count()).select_from(SearchHistory)) == 0
        assert db.scalar(select(func.count()).select_from(AuthToken)) == 0

    # L'adresse est de nouveau libre.
    with TestClient(app) as http:
        assert signup(http).status_code == 201


def test_delete_account_requires_login(mailbox):
    with TestClient(app) as http:
        assert http.post("/api/v1/auth/me/delete", json={"password": PASSWORD}).status_code == 401
