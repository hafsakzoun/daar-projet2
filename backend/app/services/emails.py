"""Contenu des e-mails envoyés par Lisière (texte + HTML)."""

from html import escape

from app.core.config import settings

ACCENT = "#1f4d3a"


def _layout(title: str, intro: str, button: str, link: str, outro: str) -> str:
    return f"""<!doctype html>
<html lang="fr"><body style="margin:0;background:#f3f4f0;padding:32px 16px;font-family:Helvetica,Arial,sans-serif;color:#2a322d">
  <table role="presentation" width="100%" style="max-width:520px;margin:0 auto;background:#ffffff;border:1px solid #dde1da;border-radius:6px">
    <tr><td style="padding:28px 32px 8px;font-family:Georgia,serif;font-size:24px;font-style:italic;color:#131a16">Lisière</td></tr>
    <tr><td style="padding:8px 32px 0;font-family:Georgia,serif;font-size:22px;color:#131a16">{escape(title)}</td></tr>
    <tr><td style="padding:12px 32px;font-size:15px;line-height:1.6">{escape(intro)}</td></tr>
    <tr><td style="padding:8px 32px 20px">
      <a href="{escape(link)}" style="display:inline-block;background:{ACCENT};color:#ffffff;text-decoration:none;padding:12px 22px;border-radius:4px;font-size:15px">{escape(button)}</a>
    </td></tr>
    <tr><td style="padding:0 32px 28px;font-size:13px;line-height:1.6;color:#5d6860">{escape(outro)}<br><br>Si le bouton ne fonctionne pas, copie ce lien :<br><span style="word-break:break-all">{escape(link)}</span></td></tr>
  </table>
</body></html>"""


def verification_email(first_name: str, token: str) -> tuple[str, str, str]:
    link = f"{settings.app_url}/#/verifier?jeton={token}"
    subject = "Confirme ton adresse e-mail — Lisière"
    intro = f"Bonjour {first_name}, merci de t'être inscrit·e. Confirme ton adresse pour activer ton compte."
    outro = "Ce lien est valable 48 heures. Si tu n'as pas créé de compte, ignore simplement cet e-mail."
    text = f"{intro}\n\n{link}\n\n{outro}\n"
    return subject, text, _layout("Bienvenue sur Lisière", intro, "Confirmer mon adresse", link, outro)


def reset_email(first_name: str, token: str) -> tuple[str, str, str]:
    link = f"{settings.app_url}/#/reinitialiser?jeton={token}"
    subject = "Réinitialise ton mot de passe — Lisière"
    intro = f"Bonjour {first_name}, tu as demandé à changer ton mot de passe. Choisis-en un nouveau avec le lien ci-dessous."
    outro = "Ce lien est valable 1 heure et ne peut servir qu'une fois. Si tu n'es pas à l'origine de cette demande, ignore cet e-mail : ton mot de passe actuel reste valable."
    text = f"{intro}\n\n{link}\n\n{outro}\n"
    return subject, text, _layout("Nouveau mot de passe", intro, "Choisir un nouveau mot de passe", link, outro)
