import pytest
from fastapi import HTTPException

from app.core.config import read_secret, settings
from app.services import mailer, rate_limit
from app.services.emails import reset_email, verification_email


def test_secret_is_read_from_file(tmp_path, monkeypatch):
    secret = tmp_path / "db_password"
    secret.write_text("depuis-un-fichier\n")
    monkeypatch.setenv("DB_PASSWORD_FILE", str(secret))
    monkeypatch.setenv("DB_PASSWORD", "depuis-une-variable")
    # Le fichier (secret Docker) est prioritaire sur la variable.
    assert read_secret("DB_PASSWORD") == "depuis-un-fichier"


def test_secret_falls_back_to_variable(monkeypatch):
    monkeypatch.delenv("X_PASSWORD_FILE", raising=False)
    monkeypatch.setenv("X_PASSWORD", "valeur")
    assert read_secret("X_PASSWORD") == "valeur"


def test_missing_secret_file_gives_default(monkeypatch):
    monkeypatch.setenv("X_PASSWORD_FILE", "/nexiste/pas")
    assert read_secret("X_PASSWORD", "defaut") == "defaut"


def test_mail_disabled_without_smtp(capsys):
    assert not settings.mail_enabled
    assert mailer.send_mail("a@example.org", "Sujet", "lien", "<p>lien</p>") is False
    assert "SMTP non configuré" in capsys.readouterr().out


def test_email_links_use_configured_site_and_fragment():
    _, text, html = verification_email("Lou", "jeton123")
    assert f"{settings.app_url}/#/verifier?jeton=jeton123" in text
    _, text, html = reset_email("Lou", "jeton456")
    assert "/#/reinitialiser?jeton=jeton456" in text
    # Le prénom est échappé dans le HTML.
    _, _, html = reset_email("<script>", "t")
    assert "<script>" not in html


def test_rate_limit_blocks_after_limit():
    rate_limit.reset()
    for _ in range(3):
        rate_limit.check("test:cle", limit=3, window_seconds=60)
    with pytest.raises(HTTPException) as error:
        rate_limit.check("test:cle", limit=3, window_seconds=60)
    assert error.value.status_code == 429
    rate_limit.check("test:autre", limit=3, window_seconds=60)
    rate_limit.reset()
