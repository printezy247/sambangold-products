"""#1 Gold Watch — the bot commands, the checker, and the dashboard context.

One armed alert is a row in ``alerts``; the checker (``flask check-alerts`` or
``POST /tasks/check-alerts``) fetches one quote, fires whatever crossed, records
each trigger and messages the owner. Owner is the Telegram user id, which the
bot gets from the chat and the dashboard gets from the Telegram login, so the
two surfaces see one list.
"""

import csv
import io
import time

from flask import current_app

from . import feeds, store
from .brand import DEFAULT_LANG, t

STOP_PCT = 0.005  # a 0.5% stop, widened by the spread, as a starting point


def fmt(value):
    return "%s" % format(value, ",.2f")


def quote_lines(quote, lang=DEFAULT_LANG):
    bps = feeds.spread_bps(quote)
    spread = ("%s (%.1f bps)" % (fmt(quote["spread"]), bps)) if bps is not None else t("watch.nobook", lang)
    spread_abs = quote["spread"] or 0.0
    long_entry, long_stop = quote["ask"], quote["ask"] * (1 - STOP_PCT) - spread_abs
    short_entry, short_stop = quote["bid"], quote["bid"] * (1 + STOP_PCT) + spread_abs
    return [
        "<b>XAUUSD %s</b>  bid %s · ask %s" % (fmt(quote["mid"]), fmt(quote["bid"]), fmt(quote["ask"])),
        t("watch.spread", lang, spread=spread, src=quote["source"]),
        t("watch.long", lang, e=fmt(long_entry), s=fmt(long_stop)),
        t("watch.short", lang, e=fmt(short_entry), s=fmt(short_stop)),
    ]


def alert_line(a, lang=DEFAULT_LANG):
    return "#%d  %s %s %s" % (a["id"], a["symbol"], t("watch." + a["direction"], lang), fmt(a["level"]))


# --- bot -------------------------------------------------------------------- #

def bot_watch(args, chat_id=None, lang=DEFAULT_LANG, **_):
    usage = t("watch.usage", lang)
    sub = args[0].lower() if args else ""
    if sub in ("", "help"):
        return usage

    if sub == "list":
        rows = store.alerts_for(chat_id) if chat_id else []
        if not rows:
            return t("watch.none", lang) + "\n\n" + usage
        return t("watch.list", lang) + "\n" + "\n".join(alert_line(a, lang) for a in rows)

    if sub == "clear":
        n = store.clear_alerts(chat_id) if chat_id else 0
        return t("watch.cleared", lang, n=n)

    symbol = sub.upper()
    if symbol not in ("XAUUSD", "GOLD", "XAU"):
        return t("watch.only_gold", lang) + "\n\n" + usage
    symbol = "XAUUSD"

    try:
        quote = feeds.gold_quote()
    except feeds.FeedError as exc:
        return t("watch.feed_down", lang, err=exc)

    if len(args) == 1:
        rows = store.alerts_for(chat_id) if chat_id else []
        lines = quote_lines(quote, lang)
        if rows:
            lines += ["", t("watch.armed", lang) + ", ".join(alert_line(a, lang) for a in rows)]
        return "\n".join(lines)

    direction = args[1].lower()
    if direction not in ("above", "below") or len(args) < 3:
        return usage
    try:
        level = float(args[2].replace(",", ""))
    except ValueError:
        return t("watch.level_num", lang) + "\n\n" + usage
    if not chat_id:
        return t("watch.need_chat", lang)

    alert_id = store.add_alert(chat_id, symbol, direction, level)
    side = "ask" if direction == "above" else "bid"
    return t("watch.ok", lang, id=alert_id, sym=symbol, dir=t("watch." + direction, lang), level=fmt(level),
             side=side, bid=fmt(quote["bid"]), ask=fmt(quote["ask"]))


# --- checker ---------------------------------------------------------------- #

def check_alerts(send):
    """Fire every crossed alert, log the spread, push calendar reminders.

    `send(chat_id, text)` is injected so tests need no token.
    """
    from . import caltool  # late import: caltool imports store, not watch
    alerts = store.active_alerts()
    try:
        quote = feeds.gold_quote(max_age=0)
    except feeds.FeedError:
        return {"checked": 0, "fired": 0, "pushed": 0, "error": "feed unavailable"}
    calendar = caltool.check_calendar(send, quote)
    from . import tokengoldtool
    tokengoldtool.log_premium()
    if not alerts:
        return {"checked": 0, "fired": 0, "pushed": calendar["pushed"]}
    fired = 0
    for alert in alerts:
        if feeds.crossed(alert["direction"], alert["level"], quote):
            price = store.record_trigger(alert, quote)
            lang = store.tg_lang(alert["owner"]) or DEFAULT_LANG
            send(alert["owner"], t("watch.fire", lang, dir=t("watch." + alert["direction"], lang), level=fmt(alert["level"]),
                                   side="ask" if alert["direction"] == "above" else "bid", price=fmt(price), src=quote["source"]))
            fired += 1
    return {"checked": len(alerts), "fired": fired, "source": quote["source"], "pushed": calendar["pushed"]}


# --- dashboard -------------------------------------------------------------- #

def dashboard_watch(request, user=None):
    owner = user["owner"] if user else None
    ctx = {"form": request.values, "quote": None, "feed_error": None, "owner": owner,
           "alerts": [], "history": [], "notice": None}
    from .auth import lang as ui_lang
    try:
        ctx["quote"] = feeds.gold_quote()
        ctx["lines"] = quote_lines(ctx["quote"], ui_lang())
        ctx["spread_bps"] = feeds.spread_bps(ctx["quote"])
    except feeds.FeedError as exc:
        ctx["feed_error"] = str(exc)

    if owner and request.method == "POST":
        form = request.form
        action = form.get("action")
        if action == "arm":
            try:
                aid = store.add_alert(owner, "XAUUSD", form.get("direction", "above"), form["level"])
                ctx["notice"] = t("watch.d_armed", ui_lang(), id=aid)
            except (KeyError, ValueError):
                ctx["notice"] = t("watch.level_num", ui_lang())
        elif action == "update":
            try:
                store.update_alert(owner, form["id"], level=form["level"])
                ctx["notice"] = t("watch.d_updated", ui_lang())
            except (KeyError, ValueError):
                ctx["notice"] = t("watch.level_num", ui_lang())
        elif action == "disarm":
            store.update_alert(owner, form.get("id"), active=False)
            ctx["notice"] = t("watch.d_disarmed", ui_lang())

    if owner:
        ctx["alerts"] = store.alerts_for(owner)
        ctx["history"] = store.triggers_for(owner)
    return ctx


def history_csv(owner):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["fired_at_utc", "symbol", "direction", "level", "price", "spread", "source"])
    for t in store.triggers_for(owner, limit=5000):
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t["fired_at"])),
                    t["symbol"], t["direction"], t["level"], t["price"],
                    "" if t["spread"] is None else t["spread"], t["source"]])
    return out.getvalue()
