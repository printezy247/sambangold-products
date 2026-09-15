"""#14 Drawdown Sentinel — bot commands, the ping endpoint, the dashboard context, the warnings."""

import datetime as dt
import secrets

from flask import current_app

from . import sentinel, store
from . import gate
from .brand import DEFAULT_LANG, t

SLUG = "drawdown-sentinel"
ICON = {"ok": "🟢", "warn": "🟡", "breach": "🔴"}


def _today():
    return dt.date.today().isoformat()


def ping_url(token):
    return "%s/p/drawdown-sentinel/ping/%s" % (current_app.config["PUBLIC_BASE_URL"].rstrip("/"), token)


def _firms():
    return ", ".join(k for k in sentinel.PACKS if k != "custom")


def link_account(owner, name, firm, balance, pack=None, cap=None):
    """(account, error_key). `cap` of 0 means no limit."""
    cap = sentinel.FREE_ACCOUNTS if cap is None else cap
    if cap and len(store.sentinels_for(owner)) >= cap:
        return None, "sn.limit"
    key = sentinel.find_pack(firm) if pack is None else "custom"
    if not key:
        return None, "sn.firm_unknown"
    pack = pack or sentinel.PACKS[key]
    try:
        balance = float(str(balance).replace(",", "").replace("$", ""))
        if balance <= 0:
            raise ValueError
    except ValueError:
        return None, "sn.usage"
    token = secrets.token_urlsafe(12)
    acc_id = store.add_sentinel(owner, name.strip()[:40] or "Account", pack["name"], pack, token, balance, _today())
    return store.sentinel_get(owner, acc_id), None


def apply_report(acc, equity, balance=None, lots=None, note=None, send=None, lang=DEFAULT_LANG):
    """Record a report, re-evaluate, log transitions, push warnings. Returns the evaluation."""
    equity = float(equity)
    fields = {"equity": equity, "peak_equity": max(acc["peak_equity"], equity)}
    if balance is not None:
        fields["day_start_balance"] = float(balance)
    if lots is not None:
        fields["open_lots"] = float(lots)
    if acc["day"] != _today():
        fields["day"] = _today()
        if balance is None:
            fields["day_start_balance"] = equity            # a new day starts from where the equity is
    acc = dict(acc, **fields)
    ev = sentinel.evaluate(acc, acc["pack"])
    changed = ev["state"] != acc["last_state"]
    fields["last_state"] = ev["state"]
    store.sentinel_update(acc["id"], **fields)
    if changed or ev["state"] == "breach":
        worst = next((r for r in ev["rules"] if r["state"] == ev["state"]), None)
        store.sentinel_log(acc["id"], equity, ev["state"], note or (worst["key"] if worst else None))
        if send and changed:
            send(acc["owner"], push_text(acc, ev, worst, lang))
    return ev


def push_text(acc, ev, worst, lang):
    rule = t("sn.rule_" + (worst["key"] if worst else "daily"), lang)
    if ev["state"] == "breach":
        return t("sn.push_breach", lang, name=acc["name"], rule=rule, equity=ev["equity"], line=worst["line"] if worst else 0)
    if ev["state"] == "warn":
        return t("sn.push_warn", lang, name=acc["name"], rule=rule, room=worst["room"] if worst else 0, pct=(worst["room_pct"] or 0) * 100)
    return t("sn.push_ok", lang, name=acc["name"], equity=ev["equity"])


def status_text(acc, lang):
    ev = sentinel.evaluate(acc, acc["pack"])
    lines = [t("sn.status", lang, icon=ICON[ev["state"]], name=acc["name"], firm=acc["firm"], equity=ev["equity"])]
    for r in ev["rules"]:
        if r["key"] == "days":
            lines.append(t("sn.r_days", lang, done=ev["days_done"], line=r["line"]))
        elif r["key"] == "lot":
            lines.append(t("sn.r_lot", lang, line=r["line"], room=r["room"]))
        else:
            lines.append(t("sn.r_" + r["key"], lang, line=r["line"], room=r["room"], pct=(r["room_pct"] or 0) * 100))
    return "\n".join(lines)


# --- bot -------------------------------------------------------------------- #

def bot_sentinel(args, chat_id=None, lang=DEFAULT_LANG, **_):
    from .telegram import send_message
    usage = t("sn.usage", lang, firms=_firms())
    sub = args[0].lower() if args else ""
    accounts = store.sentinels_for(chat_id) if chat_id else []
    if sub == "link" and chat_id:
        if len(args) < 4:
            return usage
        cap = gate.limit("accounts", chat_id=chat_id)
        acc, err = link_account(chat_id, args[1], args[2], args[3], cap=cap)
        if err:
            return t(err, lang, n=cap, firms=_firms()) if err != "sn.usage" else usage
        p = acc["pack"]
        return t("sn.linked", lang, name=acc["name"], firm=acc["firm"], balance=acc["initial_balance"], ping=ping_url(acc["token"]),
                 daily=p["daily_pct"], max=p["max_pct"], trail=t("sn.trailing", lang) if p["trailing"] else "", days=p["min_days"])
    if not accounts:
        return t("sn.none", lang) + "\n\n" + usage
    acc = accounts[0]
    if sub in ("", "status"):
        return status_text(acc, lang)
    if sub == "firm" and len(args) > 1:
        key = sentinel.find_pack(args[1])
        if not key:
            return t("sn.firm_unknown", lang, firms=_firms())
        store.sentinel_update(acc["id"], firm=sentinel.PACKS[key]["name"], pack=sentinel.PACKS[key])
        return t("sn.firm_set", lang, name=acc["name"], firm=sentinel.PACKS[key]["name"])
    if sub == "equity" and len(args) > 1:
        try:
            equity = float(args[1].replace(",", ""))
            lots = float(args[2]) if len(args) > 2 else None
        except ValueError:
            return usage
        ev = apply_report(acc, equity, lots=lots, send=send_message, lang=lang)
        return t("sn.updated", lang, equity=equity) + "\n" + status_text(store.sentinel_get(chat_id, acc["id"]), lang)
    if sub == "newday":
        store.sentinel_update(acc["id"], day_start_balance=acc["equity"], day=_today())
        return t("sn.newday", lang, balance=acc["equity"])
    return usage


# --- ping ---------------------------------------------------------------------- #

def ping(token, values):
    """The EA / shortcut endpoint. Returns (status, payload)."""
    from .telegram import send_message
    acc = store.sentinel_by_token(token)
    if not acc:
        return 404, {"ok": False}
    try:
        equity = float(values.get("equity"))
    except (TypeError, ValueError):
        return 400, {"ok": False, "error": "equity required"}
    balance = values.get("balance")
    lots = values.get("lots")
    ev = apply_report(acc, equity, balance=float(balance) if balance else None, lots=float(lots) if lots else None,
                      note="ping", send=send_message, lang=store.tg_lang(acc["owner"]) or DEFAULT_LANG)
    return 200, {"ok": True, "state": ev["state"], "rules": ev["rules"]}


# --- dashboard ----------------------------------------------------------------- #

def dashboard_sentinel(request, user=None):
    from .auth import lang as ui_lang
    from .telegram import send_message
    lang = ui_lang()
    owner = user["owner"] if user else None
    form = request.form if request.method == "POST" else {}
    ctx = {"form": form, "owner": owner, "error": None, "notice": None, "packs": sentinel.PACKS, "pack_date": sentinel.PACK_DATE,
           "free": gate.limit("accounts", user=user), "accounts": [], "icon": ICON, "ping": ping_url}
    if request.method == "POST" and owner:
        action = form.get("action")
        if action == "link":
            pack = None
            if form.get("firm") == "custom":
                try:
                    pack = sentinel.custom_pack(form.get("daily_pct", 5), form.get("max_pct", 10), form.get("trailing") == "on",
                                                form.get("min_days") or 0, form.get("max_lot") or None)
                except ValueError:
                    ctx["error"] = t("sn.usage", lang, firms=_firms())
            if not ctx["error"]:
                acc, err = link_account(owner, form.get("name", ""), form.get("firm", ""), form.get("balance", ""), pack)
                if err:
                    ctx["error"] = t(err, lang, n=ctx["free"], firms=_firms())
        elif action == "update":
            acc = store.sentinel_get(owner, form.get("id", 0))
            if acc:
                try:
                    apply_report(acc, form.get("equity"), balance=form.get("balance") or None, lots=form.get("lots") or None,
                                 note="dashboard", send=send_message, lang=lang)
                    ctx["notice"] = "updated"
                except (TypeError, ValueError):
                    ctx["error"] = t("sn.usage", lang, firms=_firms())
        elif action == "newday":
            acc = store.sentinel_get(owner, form.get("id", 0))
            if acc:
                store.sentinel_update(acc["id"], day_start_balance=acc["equity"], day=_today())
        elif action == "delete":
            store.sentinel_delete(owner, form.get("id", 0))
    if owner:
        for acc in store.sentinels_for(owner):
            acc["eval"] = sentinel.evaluate(acc, acc["pack"])
            acc["history"] = store.sentinel_history(acc["id"])
            ctx["accounts"].append(acc)
    return ctx
