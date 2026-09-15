"""Where a product's math meets its two surfaces.

`BOT` maps a command word to a function taking the argument list (plus
`chat_id` as a keyword) and returning HTML for Telegram. `DASHBOARD` maps a slug to a function taking the Flask
request and returning the template context for that product's tool panel. A
product in neither table still renders its spec; a product in one table only
fails the surface-contract test.
"""

from flask import session

from . import calc
from .caltool import bot_calendar, bot_calendar_alert, dashboard_calendar
from .watch import bot_watch, dashboard_watch

SAVE_LIMIT = 8


def money(value):
    sign = "-" if value < 0 else ""
    return "%s$%s" % (sign, format(abs(value), ",.0f"))


def pct(value):
    return "%.1f%%" % (value * 100)


# --------------------------------------------------------------------------- #
# #3 — Prop firm challenge
# --------------------------------------------------------------------------- #

PROPCALC_USAGE = (
    "Usage: <code>/propcalc FEE SIZE PASS%</code>\n"
    "Example: <code>/propcalc 500 100000 15</code> — a $500 fee on a $100k "
    "account with a 15% chance of passing."
)


def bot_propcalc(args, **_):
    if len(args) < 3:
        return PROPCALC_USAGE
    try:
        r = calc.prop_ev(args[0], args[1], args[2])
    except calc.InputError as exc:
        return "%s\n\n%s" % (exc, PROPCALC_USAGE)
    tone = {"positive": "✅", "breakeven": "➖", "negative": "❌"}[r["verdict"]]
    return (
        "%s <b>EV %s</b> on a %s fee (%s ROI)\n"
        "First payout if funded: %s (%s target × %s split on %s)\n"
        "Breakeven pass rate: <b>%s</b> — you said %s\n\n"
        "Paste the firm's terms on the dashboard for the rule scan."
    ) % (
        tone, money(r["ev"]), money(r["total_cost"]), pct(r["roi"]),
        money(r["first_payout"]), pct(r["profit_target"]), pct(r["split"]), money(r["size"]),
        pct(r["breakeven_pass_rate"]), pct(r["pass_rate"]),
    )


def dashboard_prop(request, user=None):
    form = request.values
    ctx = {"form": form, "result": None, "error": None, "scan": None,
           "saved": session.get("saves", {}).get("prop-calculator", [])}
    if form.get("fee"):
        try:
            ctx["result"] = calc.prop_ev(
                form["fee"], form.get("size", 100000), form.get("pass_pct", 15),
                form.get("profit_target_pct", 8), form.get("split_pct", 80),
                form.get("resets", 0),
            )
        except calc.InputError as exc:
            ctx["error"] = str(exc)
    if form.get("terms"):
        ctx["scan"] = calc.scan_terms(form["terms"])
    if ctx["result"] and form.get("save"):
        _save("prop-calculator", {
            "firm": form.get("firm") or "Unnamed firm",
            "fee": money(ctx["result"]["total_cost"]),
            "size": money(ctx["result"]["size"]),
            "pass": pct(ctx["result"]["pass_rate"]),
            "ev": money(ctx["result"]["ev"]),
            "breakeven": pct(ctx["result"]["breakeven_pass_rate"]),
            "verdict": ctx["result"]["verdict"],
        })
        ctx["saved"] = session["saves"]["prop-calculator"]
    return ctx


# --------------------------------------------------------------------------- #
# #8 — IB revenue
# --------------------------------------------------------------------------- #

IBCALC_USAGE = (
    "Usage: <code>/ibcalc LOTS RATE [CLIENTS] [CLAWBACK%]</code>\n"
    "Example: <code>/ibcalc 40 7 25 5</code> — 25 clients trading 40 lots a "
    "month at $7 a lot with 5% clawback."
)


def bot_ibcalc(args, **_):
    if len(args) < 2:
        return IBCALC_USAGE
    try:
        r = calc.ib_revenue(args[0], args[1],
                            clients=args[2] if len(args) > 2 else 1,
                            clawback_pct=args[3] if len(args) > 3 else 0)
    except calc.InputError as exc:
        return "%s\n\n%s" % (exc, IBCALC_USAGE)
    return (
        "<b>%s net per month</b> · %s a year\n"
        "Gross %s from %d client%s × %g lots × $%g\n"
        "Clawback %s · margin %s\n\n"
        "Add compliance cost, payout threshold and hold period on the dashboard "
        "to see when the first cash lands."
    ) % (
        money(r["net"]), money(r["annual"]),
        money(r["gross"]), r["clients"], "" if r["clients"] == 1 else "s", r["lots"], r["rate"],
        money(r["clawback"]), pct(r["margin"]),
    )


def dashboard_ib(request, user=None):
    form = request.values
    ctx = {"form": form, "result": None, "error": None,
           "checklist": calc.IB_CHECKLIST,
           "saved": session.get("saves", {}).get("ib-revenue-calculator", [])}
    if form.get("lots"):
        try:
            ctx["result"] = calc.ib_revenue(
                form["lots"], form.get("rate", 7), form.get("clients", 1),
                form.get("compliance_cost", 0), form.get("clawback_pct", 0),
                form.get("payout_threshold", 0), form.get("hold_days", 30),
            )
        except calc.InputError as exc:
            ctx["error"] = str(exc)
    if ctx["result"] and form.get("save"):
        r = ctx["result"]
        _save("ib-revenue-calculator", {
            "broker": form.get("broker") or "Unnamed broker",
            "rate": "$%g" % r["rate"],
            "clients": r["clients"],
            "net": money(r["net"]),
            "annual": money(r["annual"]),
            "first_cash": ("%d days" % r["first_cash_days"]) if r["first_cash_days"] else "never",
        })
        ctx["saved"] = session["saves"]["ib-revenue-calculator"]
    return ctx


def _save(slug, row):
    saves = session.setdefault("saves", {})
    rows = [row] + [r for r in saves.get(slug, []) if r != row]
    saves[slug] = rows[:SAVE_LIMIT]
    session.modified = True


BOT = {"watch": bot_watch, "propcalc": bot_propcalc, "ibcalc": bot_ibcalc,
       "calendar": bot_calendar, "calendar_alert": bot_calendar_alert}
DASHBOARD = {"gold-watch": dashboard_watch, "gold-calendar": dashboard_calendar,
             "prop-calculator": dashboard_prop, "ib-revenue-calculator": dashboard_ib}
