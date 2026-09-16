"""Access control for the internal team ops surfaces (`/team/*` and the
team bot). Reuses the same passwordless sign-in as the customer side
(Telegram Login Widget + email code) — a team role is a grant on top of an
existing account, not a second auth system.

Two tiers:

* **Full access** — CEO, HOD Sales, HOD Marketing: create/edit tasks,
  change roadmap status, everything except granting roles to others.
* **Executive** — browse and download only: read the roadmap, read tasks,
  browse the file library. No create/edit.

Granting roles is CEO-only.
"""

from functools import wraps

from flask import abort, redirect, request, url_for

from . import store
from .auth import current_user


def current_team_role():
    user = current_user()
    return (user or {}).get("team_role")


def is_team_member():
    return current_team_role() is not None


def is_team_admin():
    """CEO or an HOD — full access short of role management."""
    return current_team_role() in store.TEAM_FULL_ACCESS_ROLES


def is_ceo():
    return current_team_role() == "ceo"


def team_required(view):
    """Any team role at all — the floor for every /team/* page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.signin", next=request.path))
        if not is_team_member():
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def team_admin_required(view):
    """CEO or HOD only — for create/edit actions."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.signin", next=request.path))
        if not is_team_admin():
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def ceo_required(view):
    """CEO only — role management."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.signin", next=request.path))
        if not is_ceo():
            abort(403)
        return view(*args, **kwargs)
    return wrapped
