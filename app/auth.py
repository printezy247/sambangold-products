"""The account spine: one Telegram identity across the bot and the dashboard.

The Telegram Login Widget posts the user's identity to the callback with a
``hash`` field. That hash is HMAC-SHA256 over the sorted "key=value" lines,
keyed by SHA256 of the bot token — which only the bot owner knows. Verifying it
is what lets the browser session and the bot agree on who the user is, without
a second login and without an external identity provider.

https://core.telegram.org/widgets/login
"""

import hashlib
import hmac
import time
from functools import wraps

from flask import Blueprint, current_app, redirect, request, session, url_for

bp = Blueprint("auth", __name__)


def data_check_string(payload):
    """The exact string Telegram signs: sorted key=value lines, minus the hash."""
    return "\n".join(
        "%s=%s" % (key, payload[key])
        for key in sorted(payload)
        if key != "hash"
    )


def verify(payload, bot_token, max_age_seconds=86400, now=None):
    """True when the payload really came from Telegram and is still fresh."""
    received = payload.get("hash")
    if not received or not bot_token:
        return False

    secret = hashlib.sha256(bot_token.encode()).digest()
    expected = hmac.new(
        secret, data_check_string(payload).encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, received):
        return False

    try:
        auth_date = int(payload.get("auth_date", 0))
    except (TypeError, ValueError):
        return False
    now = time.time() if now is None else now
    return 0 <= now - auth_date <= max_age_seconds


def current_user():
    return session.get("user")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("views.index"))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/auth/telegram")
def telegram_callback():
    """Where the Telegram Login Widget lands the user."""
    payload = request.args.to_dict()
    config = current_app.config
    if not verify(
        payload,
        config["TELEGRAM_BOT_TOKEN"],
        config["AUTH_MAX_AGE_SECONDS"],
    ):
        return "Login could not be verified.", 403

    session["user"] = {
        "id": payload.get("id"),
        "username": payload.get("username", ""),
        "first_name": payload.get("first_name", ""),
    }
    return redirect(url_for("views.index"))


@bp.route("/auth/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("views.index"))
