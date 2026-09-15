"""The account spine: one person, reachable by Telegram and/or email.

Three doors, no passwords:

* **Telegram Login Widget** — the browser gets Telegram identity, the server
  verifies ``hash`` (HMAC-SHA256 over the sorted data-check string, keyed by
  SHA256 of the bot token). This is what lets the bot and the dashboard agree
  on who the user is. https://core.telegram.org/widgets/login
* **Email code** — an 8-digit code mailed over plain SMTP, ten minutes, five
  tries. Verifying it creates the account and records the email.
* **Google** — a placeholder page until OAuth credentials exist.

Signing in through a second door while already signed in *links* the two,
so an email account gains a Telegram id (and its alerts move to the shared
key) instead of becoming a second person.
"""

import hashlib
import hmac
import re
import time
from functools import wraps

from flask import (Blueprint, abort, current_app, redirect, render_template, request,
                   session, url_for)

from . import mailer, store
from .brand import DEFAULT_LANG, LANGS, normalise_lang, t

bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --- Telegram signature ---------------------------------------------------- #

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


# --- session helpers ------------------------------------------------------- #

def _is_admin(user):
    admin = current_app.config["ADMIN_TELEGRAM_ID"]
    return bool(admin and user.get("telegram_id") and str(user["telegram_id"]) == str(admin))


def session_user(user):
    """The slice of a users row the templates and tools need."""
    return {
        "uid": user["id"],
        "owner": store.owner_key(user),
        "telegram_id": user.get("telegram_id"),
        "email": user.get("email"),
        "username": user.get("username") or "",
        "name": user.get("name") or "",
        "locale": user.get("locale") or DEFAULT_LANG,
        "is_admin": _is_admin(user),
        "rank": rank_for(user),
    }


def rank_for(user):
    """A rank is a grant, never a side effect of signing in. The admin is always Rambo.

    Signing in used to floor at General. It no longer does: General is paid for,
    or earned through the broker door, and a rank nobody paid for is not a rank.
    """
    if _is_admin(user):
        return "elite"
    from .gate import owner_tier      # one resolver, so the bot and the page agree
    return owner_tier(store.owner_key(user))


def sign_in(user):
    session["user"] = session_user(user)
    session["lang"] = session.get("lang") or user.get("locale") or DEFAULT_LANG
    session.permanent = True


def current_user():
    return session.get("user")


def lang():
    """Bahasa Melayu first; the visitor's choice or account locale wins."""
    code = session.get("lang")
    if code in LANGS:
        return code
    user = current_user()
    if user and user.get("locale") in LANGS:
        return user["locale"]
    return normalise_lang(request.accept_languages.best_match(LANGS)) or DEFAULT_LANG


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.signin", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            return redirect(url_for("auth.signin", next=request.path))
        if not user.get("is_admin"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def _safe_next(default="views.dashboard"):
    target = request.values.get("next") or ""
    if target.startswith("/") and not target.startswith("//"):
        return target
    return url_for(default)


# --- routes ---------------------------------------------------------------- #

@bp.route("/lang/<code>")
def set_lang(code):
    if code in LANGS:
        session["lang"] = code
        user = current_user()
        if user:
            store.set_user_locale(user["uid"], code)
            user["locale"] = code
            session["user"] = user
    return redirect(request.referrer or url_for("views.index"))


@bp.route("/signin")
def signin():
    if current_user():
        return redirect(_safe_next())
    return render_template("signin.html", next=request.args.get("next", ""))


@bp.route("/auth/telegram")
def telegram_callback():
    """Where the Telegram Login Widget lands the user."""
    payload = {k: v for k, v in request.args.items() if k != "next"}
    config = current_app.config
    if not verify(payload, config["TELEGRAM_BOT_TOKEN"], config["AUTH_MAX_AGE_SECONDS"]):
        return "Login could not be verified.", 403

    current = current_user()
    user = store.upsert_telegram_user(
        payload.get("id"),
        username=payload.get("username", ""),
        name=" ".join(filter(None, (payload.get("first_name"), payload.get("last_name")))),
        locale=lang(),
        link_to=current["uid"] if current and not current.get("telegram_id") else None,
    )
    sign_in(user)
    return redirect(_safe_next())


@bp.route("/auth/email/start", methods=["POST"])
def email_start():
    email = (request.form.get("email") or "").strip().lower()
    nxt = request.form.get("next", "")
    if not EMAIL_RE.match(email):
        return render_template("signin.html", error=t("verify.bad_email", lang()), next=nxt), 400

    c = current_app.config
    code, problem = store.issue_code(email, c["CODE_TTL_SECONDS"], c["CODE_RESEND_SECONDS"])
    if problem == "cooldown":
        return render_template("verify.html", email=email, error=t("verify.cooldown", lang()), next=nxt), 429

    sent = mailer.send(email, t("mail.subject", lang(), code=code), t("mail.body", lang(), code=code))
    dev_code = None
    if not sent:
        if c.get("DEBUG") or c.get("TESTING"):
            dev_code = code  # local runs without SMTP still get through
        else:
            return render_template("signin.html", error=t("verify.mail_down", lang()), next=nxt), 503
    return render_template("verify.html", email=email, notice=t("verify.sent", lang()),
                           dev_code=dev_code, next=nxt)


@bp.route("/auth/email/verify", methods=["POST"])
def email_verify():
    email = (request.form.get("email") or "").strip().lower()
    code = (request.form.get("code") or "").strip().replace(" ", "")
    nxt = request.form.get("next", "")
    outcome = store.verify_code(email, code, current_app.config["CODE_MAX_ATTEMPTS"])
    if outcome != "ok":
        key = "verify.too_many" if outcome == "too_many" else "verify.wrong"
        return render_template("verify.html", email=email, error=t(key, lang()), next=nxt), 400

    current = current_user()
    user = store.upsert_email_user(
        email, locale=lang(),
        link_to=current["uid"] if current and not current.get("email") else None,
    )
    sign_in(user)
    return redirect(_safe_next())


@bp.route("/auth/google")
def google_placeholder():
    """Reserved. Renders the coming-soon page until OAuth credentials exist."""
    return render_template("google.html")


@bp.route("/auth/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("views.index"))
