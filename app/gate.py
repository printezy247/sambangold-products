"""The gate — where a rank starts to matter.

The rule from CLAUDE.md, enforced here rather than merely written down: no
product is paywalled at the door. A gate only ever guards *scale* and
*automation*, so every gated call has an ungated answer the visitor already
got. The gate's job is to say what the next rank adds, in the caller's
language, and to do it without an error page or a dead end.
"""

from functools import wraps

from flask import flash, has_request_context, redirect, request, url_for

from . import store
from .auth import current_user, lang as session_lang
from .brand import t
from .tiers import at_least, feature_label, tier_for_feature


def owner_tier(owner):
    """The rank an owner key carries — the highest grant standing behind it."""
    return store.effective_tier(owner) if owner else "public"


def user_tier(user=None):
    """The signed-in visitor's rank. Public outside a request — a background
    job has no session, and must not be handed someone else's rank."""
    if user is None:
        user = current_user() if has_request_context() else None
    return (user or {}).get("rank") or "public"


def allows(tier, feature):
    """Does this rank include the capability?"""
    return at_least(tier, tier_for_feature(feature))


def upgrade_line(feature, lang="ms", tier=None):
    """One sentence: what is locked, and which rank opens it."""
    from .brand import rank_label
    needed = tier or tier_for_feature(feature)
    return t("gate.line", lang, what=feature_label(feature, lang), rank=rank_label(needed, lang))


# --- dashboard ------------------------------------------------------------- #

def require_feature(feature):
    """Guard a dashboard view. The visitor lands on pricing with the reason shown."""
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if allows(user_tier(), feature):
                return view(*args, **kwargs)
            flash(upgrade_line(feature, session_lang()), "gate")
            return redirect(url_for("views.pricing", want=feature, next=request.path))
        return wrapped
    return decorate


# --- bot ------------------------------------------------------------------- #

def bot_gate(feature, chat_id=None, lang="ms"):
    """For a bot handler: None when allowed, otherwise the reply to send instead.

    The handler keeps answering the free part of the question; only the
    automation branch calls this.
    """
    tier = owner_tier(str(chat_id)) if chat_id else "public"
    if allows(tier, feature):
        return None
    return "%s\n\n%s" % (upgrade_line(feature, lang), t("gate.where", lang))


# --- limits ----------------------------------------------------------------- #

def limit(key, user=None, owner=None, chat_id=None):
    """The cap this caller carries for `key`. 0 means unlimited.

    Pass whichever identity the call site already has: the dashboard has a
    `user`, a bot handler has a `chat_id`, a background job has an `owner`.
    """
    from .tiers import limit_for
    if user is not None:
        tier = user.get("rank") or "public"
    elif chat_id is not None:
        tier = owner_tier(str(chat_id))
    elif owner is not None:
        tier = owner_tier(str(owner))
    else:
        tier = user_tier()
    return limit_for(key, tier)


def within(key, count, **who):
    """True while `count` is still under the caller's cap for `key`."""
    cap = limit(key, **who)
    return cap == 0 or count < cap
