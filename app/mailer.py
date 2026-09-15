"""Transactional email over plain SMTP (standard library only).

Any free SMTP relay works — a Gmail app password, Brevo's free tier, or a local
relay. Nothing is sent when SMTP is unconfigured; the caller decides how to
surface that. Tests replace `send` with a stub.
"""

import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app


def configured():
    c = current_app.config
    return bool(c["SMTP_HOST"] and c["MAIL_FROM"])


def send(to, subject, body):
    """Deliver one plain-text email. Returns True on success, False when unconfigured."""
    if not configured():
        current_app.logger.warning("SMTP unconfigured — email to %s not sent.", to)
        return False
    c = current_app.config
    msg = EmailMessage()
    msg["From"] = c["MAIL_FROM"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    port = int(c["SMTP_PORT"] or 587)
    if port == 465:
        with smtplib.SMTP_SSL(c["SMTP_HOST"], port, timeout=15, context=ssl.create_default_context()) as s:
            if c["SMTP_USER"]:
                s.login(c["SMTP_USER"], c["SMTP_PASS"])
            s.send_message(msg)
    else:
        with smtplib.SMTP(c["SMTP_HOST"], port, timeout=15) as s:
            s.starttls(context=ssl.create_default_context())
            if c["SMTP_USER"]:
                s.login(c["SMTP_USER"], c["SMTP_PASS"])
            s.send_message(msg)
    return True
