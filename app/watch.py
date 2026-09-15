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

WATCH_USAGE = (
    "Usage:\n"
    "<code>/watch XAUUSD</code> — live price, spread and entry/stop levels\n"
    "<code>/watch XAUUSD above 2450</code> — alert when the <i>ask</i> reaches 2450\n"
    "<code>/watch XAUUSD below 2380</code> — alert when the <i>bid</i> falls to 2380\n"
    "<code>/watch list</code> · <code>/watch clear</code>"
)
STOP_PCT = 0.005  # a 0.5% stop, widened by the spread, as a starting point


def fmt(value):
    return "%s" % format(value, ",.2f")


def quote_lines(quote):
    bps = feeds.spread_bps(quote)
    spread = ("%s (%.1f bps)" % (fmt(quote["spread"]), bps)) if bps is not None else "n/a (no order book)"
    spread_abs = quote["spread"] or 0.0
    long_entry, long_stop = quote["ask"], quote["ask"] * (1 - STOP_PCT) - spread_abs
    short_entry, short_stop = quote["bid"], quote["bid"] * (1 + STOP_PCT) + spread_abs
    return [
        "<b>XAUUSD %s</b>  bid %s · ask %s" % (fmt(quote["mid"]), fmt(quote["bid"]), fmt(quote["ask"])),
        "Spread %s · %s" % (spread, quote["source"]),
        "Long: enter %s, stop %s" % (fmt(long_entry), fmt(long_stop)),
        "Short: enter %s, stop %s" % (fmt(short_entry), fmt(short_stop)),
    ]


def alert_line(a):
    return "#%d  %s %s %s" % (a["id"], a["symbol"], a["direction"], fmt(a["level"]))


# --- bot -------------------------------------------------------------------- #

def bot_watch(args, chat_id=None, **_):
    sub = args[0].lower() if args else ""
    if sub in ("", "help"):
        return WATCH_USAGE

    if sub == "list":
        rows = store.alerts_for(chat_id) if chat_id else []
        if not rows:
            return "No alerts armed.\n\n" + WATCH_USAGE
        return "<b>Armed alerts</b>\n" + "\n".join(alert_line(a) for a in rows)

    if sub == "clear":
        n = store.clear_alerts(chat_id) if chat_id else 0
        return "Cleared %d alert%s." % (n, "" if n == 1 else "s")

    symbol = sub.upper()
    if symbol not in ("XAUUSD", "GOLD", "XAU"):
        return "Only gold for now (<code>XAUUSD</code>). Multi-pair is on the PRO tier.\n\n" + WATCH_USAGE
    symbol = "XAUUSD"

    try:
        quote = feeds.gold_quote()
    except feeds.FeedError as exc:
        return "Feed unavailable right now (%s). Try again in a minute." % exc

    if len(args) == 1:
        rows = store.alerts_for(chat_id) if chat_id else []
        lines = quote_lines(quote)
        if rows:
            lines += ["", "Armed: " + ", ".join(alert_line(a) for a in rows)]
        return "\n".join(lines)

    direction = args[1].lower()
    if direction not in ("above", "below") or len(args) < 3:
        return WATCH_USAGE
    try:
        level = float(args[2].replace(",", ""))
    except ValueError:
        return "Level must be a number.\n\n" + WATCH_USAGE
    if not chat_id:
        return "Alerts need a chat to fire into."

    alert_id = store.add_alert(chat_id, symbol, direction, level)
    side = "ask" if direction == "above" else "bid"
    return "✅ Alert #%d armed: %s %s %s (fires on the %s).\nNow: bid %s · ask %s" % (
        alert_id, symbol, direction, fmt(level), side, fmt(quote["bid"]), fmt(quote["ask"]))


# --- checker ---------------------------------------------------------------- #

def check_alerts(send):
    """Fire every crossed alert. `send(chat_id, text)` is injected so tests need no token."""
    alerts = store.active_alerts()
    if not alerts:
        return {"checked": 0, "fired": 0}
    quote = feeds.gold_quote(max_age=0)
    fired = 0
    for alert in alerts:
        if feeds.crossed(alert["direction"], alert["level"], quote):
            price = store.record_trigger(alert, quote)
            send(alert["owner"], "🔔 <b>XAUUSD %s %s</b> — %s now %s (%s)\n%s" % (
                alert["direction"], fmt(alert["level"]),
                "ask" if alert["direction"] == "above" else "bid", fmt(price), quote["source"],
                "Educational research only. Verify with your broker."))
            fired += 1
    return {"checked": len(alerts), "fired": fired, "source": quote["source"]}


# --- dashboard -------------------------------------------------------------- #

def dashboard_watch(request, user=None):
    owner = user["id"] if user else None
    ctx = {"form": request.values, "quote": None, "feed_error": None, "owner": owner,
           "alerts": [], "history": [], "notice": None}
    try:
        ctx["quote"] = feeds.gold_quote()
        ctx["lines"] = quote_lines(ctx["quote"])
        ctx["spread_bps"] = feeds.spread_bps(ctx["quote"])
    except feeds.FeedError as exc:
        ctx["feed_error"] = str(exc)

    if owner and request.method == "POST":
        form = request.form
        action = form.get("action")
        if action == "arm":
            try:
                aid = store.add_alert(owner, "XAUUSD", form.get("direction", "above"), form["level"])
                ctx["notice"] = "Alert #%d armed." % aid
            except (KeyError, ValueError):
                ctx["notice"] = "Level must be a number."
        elif action == "update":
            try:
                store.update_alert(owner, form["id"], level=form["level"])
                ctx["notice"] = "Threshold updated."
            except (KeyError, ValueError):
                ctx["notice"] = "Level must be a number."
        elif action == "disarm":
            store.update_alert(owner, form.get("id"), active=False)
            ctx["notice"] = "Alert disarmed."

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
