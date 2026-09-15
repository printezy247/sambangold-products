"""The Rambo extras: a branded widget and a webhook out.

Both answer the same request from a group lead or an IB: *let my people see
this under my name, and let my own systems see it at all.*

**The widget.** A token addresses a small public card carrying one tool's live
answer under the holder's own name. It is embeddable in an iframe and readable
without an account, because the people looking at it are the holder's audience,
not ours. The risk line and the data sources stay on it — white-label renames
the wrapper, never the disclaimer.

**The webhook.** Every autopilot push and scheduled report the holder receives
is also POSTed to an endpoint they own, signed so the receiver can prove it
came from here. Delivery is best-effort: a dead endpoint never delays or
swallows the Telegram message, which is the one the human actually reads.
"""

import hashlib
import hmac
import json
import secrets
import time

import requests

from . import store
from .brand import DEFAULT_LANG, t
from .gate import allows, owner_tier

WIDGET_FEATURE = "whitelabel"
HOOK_FEATURE = "api"
SLUG = "whitelabel"
TIMEOUT = 4
WIDGETS = ("gold-watch", "broker-comparator", "tokenized-gold", "miner-divergence")


# --- the widget ------------------------------------------------------------- #

def widget_of(owner):
    raw = store.get_setting(SLUG, str(owner), "widget")
    return json.loads(raw) if raw else None


def owner_of_widget(token):
    return store.owner_by_setting(SLUG, "token", (token or "").strip())


def set_widget(owner, tool, name, tier=None):
    """Mint or update the holder's widget. (widget, error_key)."""
    owner = str(owner)
    tier = tier or owner_tier(owner, signed_in=True)
    if not allows(tier, WIDGET_FEATURE):
        return None, "wl.need"
    if tool not in WIDGETS:
        return None, "wl.tool"
    name = (name or "").strip()[:40]
    if not name:
        return None, "wl.name"
    current = widget_of(owner) or {}
    token = current.get("token") or secrets.token_urlsafe(9)
    widget = {"token": token, "tool": tool, "name": name, "at": time.time()}
    store.set_setting(SLUG, owner, "widget", json.dumps(widget))
    store.set_setting(SLUG, owner, "token", token)
    return widget, None


def clear_widget(owner):
    store.set_setting(SLUG, str(owner), "widget", "")
    store.set_setting(SLUG, str(owner), "token", "")


def widget_url(token, base):
    return "%s/w/%s" % (base.rstrip("/"), token) if token else ""


# --- the webhook ------------------------------------------------------------ #

def hook_of(owner):
    raw = store.get_setting(SLUG, str(owner), "hook")
    return json.loads(raw) if raw else None


def set_hook(owner, url, tier=None):
    """Register an endpoint. (hook, error_key). https only, and a fresh secret."""
    owner = str(owner)
    tier = tier or owner_tier(owner, signed_in=True)
    if not allows(tier, HOOK_FEATURE):
        return None, "wh.need"
    url = (url or "").strip()
    if not url.lower().startswith("https://") or len(url) > 400:
        return None, "wh.url"
    current = hook_of(owner) or {}
    hook = {"url": url, "secret": current.get("secret") or secrets.token_urlsafe(24), "at": time.time()}
    store.set_setting(SLUG, owner, "hook", json.dumps(hook))
    return hook, None


def clear_hook(owner):
    store.set_setting(SLUG, str(owner), "hook", "")


def sign(secret, body):
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


def deliver(owner, event, payload, post=None):
    """Best-effort POST. Returns None when there is nothing to send or the rank lapsed.

    Never raises: the Telegram message is the one the human reads, and a dead
    endpoint must not cost them that.
    """
    hook = hook_of(owner)
    if not hook or not allows(owner_tier(str(owner), signed_in=True), HOOK_FEATURE):
        return None
    body = json.dumps({"event": event, "at": time.time(), "owner": str(owner), "data": payload},
                      sort_keys=True, default=str)
    post = post or requests.post
    try:
        r = post(hook["url"], data=body, timeout=TIMEOUT,
                 headers={"Content-Type": "application/json",
                          "X-Sambanggold-Event": event,
                          "X-Sambanggold-Signature": sign(hook["secret"], body)})
        return getattr(r, "status_code", None)
    except Exception:          # any transport failure is the receiver's problem, not ours
        return None


# --- bot -------------------------------------------------------------------- #

def bot_widget(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/widget <tool> <name>` mints the card; `/widget off` takes it down."""
    from .config import Config
    from flask import current_app
    if not chat_id:
        return t("wl.usage", lang, tools=", ".join(WIDGETS))
    tier = owner_tier(str(chat_id), signed_in=True)
    if not allows(tier, WIDGET_FEATURE):
        from .gate import upgrade_line
        return "%s\n\n%s" % (upgrade_line(WIDGET_FEATURE, lang), t("gate.where", lang))
    base = current_app.config.get("PUBLIC_BASE_URL") or Config.PUBLIC_BASE_URL

    if args and args[0].lower() == "off":
        clear_widget(chat_id)
        return t("wl.off", lang)
    if len(args) >= 2:
        widget, err = set_widget(chat_id, args[0].lower(), " ".join(args[1:]), tier=tier)
        if err:
            return t(err, lang, tools=", ".join(WIDGETS))
        return t("wl.on", lang, name=widget["name"], url=widget_url(widget["token"], base))
    current = widget_of(chat_id)
    if current:
        return t("wl.mine", lang, name=current["name"], url=widget_url(current["token"], base))
    return t("wl.usage", lang, tools=", ".join(WIDGETS))


def bot_hook(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/webhook https://...` registers an endpoint; `/webhook off` removes it."""
    if not chat_id:
        return t("wh.usage", lang)
    tier = owner_tier(str(chat_id), signed_in=True)
    if not allows(tier, HOOK_FEATURE):
        from .gate import upgrade_line
        return "%s\n\n%s" % (upgrade_line(HOOK_FEATURE, lang), t("gate.where", lang))
    if args and args[0].lower() == "off":
        clear_hook(chat_id)
        return t("wh.off", lang)
    if args:
        hook, err = set_hook(chat_id, args[0], tier=tier)
        if err:
            return t(err, lang)
        return t("wh.on", lang, url=hook["url"], secret=hook["secret"])
    current = hook_of(chat_id)
    return t("wh.mine", lang, url=current["url"]) if current else t("wh.usage", lang)


# --- the public card -------------------------------------------------------- #

def card(widget, lang=DEFAULT_LANG):
    """(heads, rows) for the widget's tool, or (heads, []) when its feed is down."""
    tool = widget["tool"]
    if tool == "gold-watch":
        from . import feeds
        from .watch import fmt
        try:
            q = feeds.gold_quote()
        except feeds.FeedError:
            return [t("ui.b_broker", lang), ""], []
        return ["XAUUSD", t("ui.w_price", lang)], [
            ["Bid", fmt(q["bid"])], ["Ask", fmt(q["ask"])],
            [t("ui.w_spread", lang), fmt(q["spread"])], [t("ui.w_src", lang), q["source"]]]
    if tool == "broker-comparator":
        from . import brokers
        rows = brokers.rank(brokers.blend(brokers.SEED, []), 1.0, 0, "long")[:6]
        return [t("ui.b_broker", lang), t("ui.b_spread", lang)], [
            [r["name"], "$%.2f" % r["cost"]["total"]] for r in rows]
    if tool == "tokenized-gold":
        from . import tokengold, tokengoldtool
        try:
            a = tokengoldtool._analysed()
        except tokengold.FeedError:
            return ["", ""], []
        return ["", t("ui.w_price", lang)], [
            ["PAXG", "%.2f%%" % (a["paxg_premium"] * 100)],
            ["XAUT", "%.2f%%" % (a["xaut_premium"] * 100)],
            ["USDT", "%.4f" % a["usdt"] if a.get("usdt") is not None else "—"]]
    if tool == "miner-divergence":
        from . import miners, minerstool
        try:
            screen = minerstool._screen()
        except miners.FeedError:
            return ["", ""], []
        return [t("ui.w_ticker", lang), t("ui.m_residual", lang)], [
            [r["ticker"], "%+.1f%%" % (r["residual"] * 100)] for r in screen["rows"][:6]]
    return ["", ""], []


# --- dashboard -------------------------------------------------------------- #

def dashboard_extras(request, user=None):
    """Both Rambo extras on one panel, because they answer the same question."""
    owner = (user or {}).get("owner")
    tier = (user or {}).get("rank") or "public"
    ctx = {"allowed": allows(tier, WIDGET_FEATURE) and allows(tier, HOOK_FEATURE),
           "widget": None, "hook": None, "tools": WIDGETS, "error": None, "url": ""}
    if not owner or not ctx["allowed"]:
        return ctx
    action = request.form.get("wl_action") if request.method == "POST" else None
    if action == "widget":
        _, ctx["error"] = set_widget(owner, (request.form.get("tool") or "").strip(),
                                     request.form.get("name") or "", tier=tier)
    elif action == "widget_off":
        clear_widget(owner)
    elif action == "hook":
        _, ctx["error"] = set_hook(owner, request.form.get("url") or "", tier=tier)
    elif action == "hook_off":
        clear_hook(owner)
    ctx["widget"] = widget_of(owner)
    ctx["hook"] = hook_of(owner)
    if ctx["widget"]:
        from flask import current_app, url_for
        base = current_app.config.get("PUBLIC_BASE_URL") or ""
        ctx["url"] = widget_url(ctx["widget"]["token"], base) if base else url_for("views.widget", token=ctx["widget"]["token"])
    return ctx
