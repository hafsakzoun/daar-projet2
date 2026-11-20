"""Envoi des e-mails transactionnels (SMTP, ex. Gmail).

Sans configuration SMTP, rien n'est envoyé : le message est écrit dans les
logs du backend (`docker compose logs backend`), ce qui permet de tester
les parcours en local sans compte e-mail.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from app.core.config import settings

logger = logging.getLogger("lisiere.mail")


def send_mail(to: str, subject: str, text: str, html: str) -> bool:
    """Envoie un e-mail ; renvoie False en cas d'échec (jamais d'exception).

    Appelée en tâche de fond : une panne SMTP ne doit pas faire échouer
    la requête de l'utilisateur.
    """
    if not settings.mail_enabled:
        print(f"[e-mail non envoyé : SMTP non configuré] À : {to} | {subject}\n{text}", flush=True)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(("Lisière", settings.mail_from))
    message["To"] = to
    message["Message-ID"] = make_msgid(domain=settings.mail_from.split("@")[-1])
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    context = ssl.create_default_context()
    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, 465, context=context, timeout=20) as smtp:
                smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                smtp.starttls(context=context)
                smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        # Le contenu (qui contient le lien) n'est pas journalisé.
        logger.error("Échec de l'envoi d'un e-mail à %s : %s", to, error)
        return False
    return True
