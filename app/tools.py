"""Where a product's math meets its two surfaces.

`BOT` maps a command word to a function taking the argument list (plus
`chat_id` as a keyword) and returning HTML for Telegram. `DASHBOARD` maps a slug to a function taking the Flask
request and returning the template context for that product's tool panel. A
product in neither table still renders its spec; a product in one table only
fails the surface-contract test.
"""

from flask import session

from . import calc
from .brand import DEFAULT_LANG, t
from .caltool import bot_calendar, bot_calendar_alert, dashboard_calendar
from .scantool import (bot_audit, bot_copyaudit, bot_influencer, bot_scan, dashboard_botscam,
                       dashboard_copyaudit, dashboard_influencer, dashboard_redflag)
from .rebatetool import bot_rebateaudit, bot_rebatestatus, dashboard_rebate
from .verifytool import bot_verify, dashboard_verify
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

def _ui_lang():
    from .auth import lang
    return lang()


def bot_propcalc(args, lang=DEFAULT_LANG, **_):
    usage = t("prop.usage", lang)
    if len(args) < 3:
        return usage
    try:
        r = calc.prop_ev(args[0], args[1], args[2])
    except calc.InputError as exc:
        return "%s\n\n%s" % (exc, usage)
    tone = {"positive": "✅", "breakeven": "➖", "negative": "❌"}[r["verdict"]]
    return t("prop.reply", lang, tone=tone, ev=money(r["ev"]), cost=money(r["total_cost"]), roi=pct(r["roi"]),
             payout=money(r["first_payout"]), target=pct(r["profit_target"]), split=pct(r["split"]), size=money(r["size"]),
             be=pct(r["breakeven_pass_rate"]), **{"pass": pct(r["pass_rate"])})


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
        ctx["scan"] = calc.scan_terms(form["terms"], _ui_lang())
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

def bot_ibcalc(args, lang=DEFAULT_LANG, **_):
    usage = t("ib.usage", lang)
    if len(args) < 2:
        return usage
    try:
        r = calc.ib_revenue(args[0], args[1],
                            clients=args[2] if len(args) > 2 else 1,
                            clawback_pct=args[3] if len(args) > 3 else 0)
    except calc.InputError as exc:
        return "%s\n\n%s" % (exc, usage)
    return t("ib.reply", lang, net=money(r["net"]), annual=money(r["annual"]), gross=money(r["gross"]),
             clients=r["clients"], lots=r["lots"], rate=r["rate"], claw=money(r["clawback"]), margin=pct(r["margin"]))


def dashboard_ib(request, user=None):
    form = request.values
    ctx = {"form": form, "result": None, "error": None,
           "checklist": calc.ib_checklist(_ui_lang()),
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
       "calendar": bot_calendar, "calendar_alert": bot_calendar_alert,
       "audit": bot_audit, "copyaudit": bot_copyaudit, "scan": bot_scan, "influencer": bot_influencer,
       "verify": bot_verify, "rebateaudit": bot_rebateaudit, "rebatestatus": bot_rebatestatus}
DASHBOARD = {"gold-watch": dashboard_watch, "gold-calendar": dashboard_calendar,
             "prop-calculator": dashboard_prop, "ib-revenue-calculator": dashboard_ib,
             "bot-scam-detector": dashboard_botscam, "copy-trade-audit": dashboard_copyaudit,
             "red-flag-scanner": dashboard_redflag, "influencer-audit": dashboard_influencer,
             "signal-verifier": dashboard_verify, "rebate-auditor": dashboard_rebate}
