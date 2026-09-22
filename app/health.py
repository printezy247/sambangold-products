"""What is quietly wrong with this deployment.

Three things can fail here without anyone noticing: the base URL can point at
a host we have left (Telegram sign-in and the webhook are signed against it),
the database can sit somewhere the volume does not cover (every restart takes
the accounts with it), and the scheduled checker can stop reaching us (no
alert ever fires, and nothing complains). Each one is silent. This module
turns all three into rows an admin can read.

Nothing here prints a secret: a token is reported as set or not set.
"""

import os
import time

from flask import current_app, request

from . import store, telegram

CHECKER_KEY = "checker_last_run"
# The scheduler runs every 5 minutes; twice that is late enough to mean broken.
CHECKER_STALE = 15 * 60

OK, WARN, BAD, UNKNOWN = "ok", "warn", "bad", "unknown"


def _row(key, state, detail):
    return {"key": key, "state": state, "detail": detail}


def _base_url_row():
    """PUBLIC_BASE_URL has to match the host actually serving the request."""
    configured = (current_app.config.get("PUBLIC_BASE_URL") or "").rstrip("/")
    if not configured:
        return _row("base", BAD, "PUBLIC_BASE_URL —")
    live = request.host_url.rstrip("/") if request else ""
    if live and live.replace("http://", "https://") != configured.replace("http://", "https://"):
        return _row("base", WARN, "%s ≠ %s" % (configured, live))
    return _row("base", OK, configured)


def _database_row():
    path = current_app.config["DATABASE_PATH"]
    on_volume = os.path.isabs(path) and not os.path.abspath(path).startswith(os.getcwd())
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0
    detail = "%s · %.0f KB" % (path, size / 1024.0)
    if not on_volume:
        # A relative path lives in the container's own filesystem, which a
        # redeploy replaces wholesale.
        return _row("db", WARN, detail)
    return _row("db", OK, detail)


def _checker_row():
    last = store.noted(CHECKER_KEY)
    if not last:
        return _row("checker", BAD, "—")
    age = time.time() - last["at"]
    mins = int(age // 60)
    state = OK if age < CHECKER_STALE else BAD
    return _row("checker", state, "%d min · %s" % (mins, last["value"]))


def _webhook_row():
    token = current_app.config["TELEGRAM_BOT_TOKEN"]
    if not token:
        return _row("hook", BAD, "TELEGRAM_BOT_TOKEN —")
    info = telegram.webhook_info(token)
    if info is None:
        return _row("hook", UNKNOWN, "—")
    url = info.get("url") or ""
    if not url:
        return _row("hook", BAD, "—")
    detail = url
    if info.get("last_error_message"):
        return _row("hook", WARN, "%s · %s" % (url, info["last_error_message"]))
    if info.get("pending_update_count"):
        detail = "%s · %d" % (url, info["pending_update_count"])
    base = (current_app.config.get("PUBLIC_BASE_URL") or "").rstrip("/")
    if base and not url.startswith(base):
        return _row("hook", WARN, detail)
    return _row("hook", OK, detail)


def _task_token_row():
    return _row("token", OK if current_app.config["TASK_TOKEN"] else BAD,
                "•" * 8 if current_app.config["TASK_TOKEN"] else "—")


def report():
    """One row per silent failure, in the order they bite."""
    return [_base_url_row(), _database_row(), _checker_row(), _webhook_row(), _task_token_row()]
