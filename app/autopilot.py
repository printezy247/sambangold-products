"""Autopilot — the A-Team half of the ladder.

A free user asks a tool a question and gets the answer. Autopilot asks the
question for them, once a day, and only speaks when the answer is worth
reading. That is the whole difference the paid ranks sell: not a locked
product, but the not-having-to-remember.

Each entry in `JOBS` is a product slug plus a builder. A builder returns the
text to push, or `None` when today's answer is not worth a message — silence
is a feature, and a digest nobody reads is worse than no digest.

Subscriptions live in the settings rows (`autopilot` = `on`) keyed by the same
owner key the bot and dashboard already share, so a subscription made in one
surface shows up in the other. The five-minute checker calls `run_daily`.
"""

import time

from . import store
from .brand import DEFAULT_LANG, t
from .gate import allows, owner_tier

FEATURE = "autopilot"
SETTING = "autopilot"
REPORT_FEATURE = "reports"


def _day(now):
    return time.strftime("%Y-%m-%d", time.gmtime(now))


def _week(now):
    return time.strftime("%G-W%V", time.gmtime(now))       # ISO week, so a year boundary cannot repeat


def _month(now):
    return time.strftime("%Y-%m", time.gmtime(now))


PERIOD = {"daily": _day, "weekly": _week, "monthly": _month}


# --- builders --------------------------------------------------------------- #
# Each returns a string to send, or None for "nothing worth saying today".

def _gold(owner, lang):
    from . import feeds
    from .watch import fmt
    try:
        q = feeds.gold_quote()
    except feeds.FeedError:
        return None
    armed = store.alerts_for(owner)
    return t("ap.gold", lang, bid=fmt(q["bid"]), ask=fmt(q["ask"]), spread=fmt(q["spread"]),
             src=q["source"], n=len(armed))


def _miners(owner, lang):
    from . import miners, minerstool
    try:
        s = minerstool._screen()
    except miners.FeedError:
        return None
    flagged = [r for r in s["rows"] if r["flags"]]
    if not flagged:
        return None
    return "\n".join([t("ap.miners", lang, n=len(flagged))]
                     + [minerstool.row_line(r, lang) for r in flagged[:5]])


def _tokengold(owner, lang):
    from . import tokengold, tokengoldtool
    try:
        a = tokengoldtool._analysed()
    except tokengold.FeedError:
        return None
    if not a["flags"]:
        return None            # a premium inside its band is not news
    return "\n".join([t("ap.tokengold", lang)] + tokengoldtool.readout_lines(a, lang))


def _sentinel(owner, lang):
    from . import sentinel, sentineltool
    accounts = store.sentinels_for(owner)
    if not accounts:
        return None
    hot = []
    for acc in accounts:
        ev = sentinel.evaluate(acc, acc["pack"])
        if ev["state"] != "safe":
            hot.append(sentineltool.status_text(acc, lang))
    if not hot:
        return None
    return "\n\n".join([t("ap.sentinel", lang, n=len(hot))] + hot)


def _exposure(owner, lang):
    from . import exposuretool
    run = exposuretool._last(owner)
    if not run:
        return None
    return "\n".join([t("ap.exposure", lang)] + exposuretool.summary_lines(run, lang))


# --- reports (A-Team, weekly and monthly) ----------------------------------- #
# A report reads what the owner already ran. It never invents a run, so an
# untouched tool stays silent instead of reporting on nothing.

def _risk_report(owner, lang):
    from . import exposuretool
    run = exposuretool._last(owner)
    if not run:
        return None
    return "\n".join([t("rp.risk", lang)] + exposuretool.summary_lines(run, lang))


def _book_report(owner, lang):
    from . import churntool
    row = store.last_run("churn-radar", owner)
    clients = ((row or {}).get("run") or {}).get("clients") or []
    at_risk = [c for c in clients if c.get("band") in ("risk", "watch")]
    if not at_risk:
        return None
    return "\n\n".join([t("rp.book", lang, n=len(at_risk), total=len(clients))]
                        + [churntool.detail_text(c, lang) for c in at_risk[:5]])


def _rebate_report(owner, lang):
    from . import rebatetool
    row = store.last_rebate_run(owner)
    if not row:
        return None
    return "\n".join([t("rp.rebate", lang), rebatetool.summary_text(row, lang)])


def _forecast_report(owner, lang):
    """The last book the owner modelled, restated for the month ahead.

    It does not re-model anything: the same inputs give the same number, so
    inventing a fresh figure would only look like new information."""
    row = store.last_run("ib-revenue-calculator", owner)
    run = (row or {}).get("run") or {}
    if not run.get("net"):
        return None
    return t("rp.forecast", lang, month=_month(time.time()), net=run["net"],
             year=run.get("annual") or run["net"] * 12, clients=run.get("clients", 1))


# --- the registry ----------------------------------------------------------- #
# (slug, cadence, capability, builder)

JOBS = (
    ("gold-watch", "daily", FEATURE, _gold),
    ("miner-divergence", "daily", FEATURE, _miners),
    ("tokenized-gold", "daily", FEATURE, _tokengold),
    ("drawdown-sentinel", "daily", FEATURE, _sentinel),
    ("exposure-monitor", "daily", FEATURE, _exposure),
    ("exposure-monitor:risk", "weekly", REPORT_FEATURE, _risk_report),
    ("churn-radar:book", "weekly", REPORT_FEATURE, _book_report),
    ("rebate-auditor:audit", "weekly", REPORT_FEATURE, _rebate_report),
    ("ib-revenue-calculator:forecast", "monthly", REPORT_FEATURE, _forecast_report),
)
BY_SLUG = {slug: build for slug, _, _, build in JOBS}
CADENCE = {slug: cadence for slug, cadence, _, _ in JOBS}
NEEDS = {slug: feature for slug, _, feature, _ in JOBS}
SLUGS = tuple(slug for slug, _, _, _ in JOBS)
DAILY = tuple(slug for slug, c, _, _ in JOBS if c == "daily")
REPORTS = tuple(slug for slug, c, _, _ in JOBS if c != "daily")


def product_of(slug):
    """`churn-radar:book` belongs to `churn-radar`."""
    return slug.split(":")[0]


# --- subscriptions ---------------------------------------------------------- #

def subscribed(owner, slug):
    return store.get_setting(slug, owner, SETTING) == "on"


def toggle(owner, slug, on=None):
    """Turn one switch on or off; returns the new state."""
    if slug not in BY_SLUG:
        raise KeyError(slug)
    state = ("on" if on else "off") if on is not None else ("off" if subscribed(owner, slug) else "on")
    store.set_setting(slug, owner, SETTING, state if state == "on" else "")
    return state


def subscriptions(owner, slugs=None):
    return {slug: subscribed(owner, slug) for slug in (slugs or SLUGS)}


# --- the run ---------------------------------------------------------------- #

def run_due(send, now=None, cadences=("daily", "weekly", "monthly")):
    """Push every switch whose period has turned over since it last fired.

    One message per switch per period, at most. A period that produced
    nothing still counts as done, so a quiet week cannot pile up into a
    burst on the day something finally happens.

    A lapsed rank simply stops producing pushes — the subscription row
    stays, so it resumes the period the rank comes back.
    """
    now = time.time() if now is None else now
    sent, skipped = 0, 0
    for slug, cadence, feature, build in JOBS:
        if cadence not in cadences:
            continue
        period = PERIOD[cadence](now)
        for owner in store.owners_by_setting(slug, SETTING, "on"):
            if not allows(owner_tier(owner, signed_in=True), feature):
                skipped += 1
                continue
            if store.get_setting(slug, owner, "ap_sent") == period:
                continue
            lang = store.tg_lang(owner) or DEFAULT_LANG
            text = build(owner, lang)
            store.set_setting(slug, owner, "ap_sent", period)
            if not text:
                continue
            send(owner, "%s\n\n%s" % (text, t("ap.footer", lang)))
            sent += 1
            from . import whitelabel   # a Rambo endpoint sees the same push; never blocks this one
            whitelabel.deliver(owner, slug, {"cadence": cadence, "period": period, "text": text})
    return {"sent": sent, "gated": skipped, "day": _day(now), "week": _week(now)}


def run_daily(send, now=None):
    """The five-minute checker's entry point — every cadence, each on its own clock."""
    return run_due(send, now)


# --- bot -------------------------------------------------------------------- #

def _name(slug, lang):
    from .products import BY_SLUG as PRODUCTS
    p = PRODUCTS[product_of(slug)].view(lang)
    name = "%s %s" % (p.emoji, p.name)
    cadence = CADENCE.get(slug, "daily")
    return name if cadence == "daily" else "%s · %s" % (name, t("ap.c_" + cadence, lang))


def bot_autopilot(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/autopilot` lists the switches; `/autopilot <slug>` flips one."""
    from .gate import bot_gate
    if not chat_id:
        return t("ap.usage", lang, slugs=SLUGS[0])
    blocked = bot_gate(FEATURE, chat_id=chat_id, lang=lang)
    if blocked:
        return blocked
    if args:
        slug = args[0].strip().lower()
        if slug not in BY_SLUG:
            return t("ap.unknown", lang, slugs=", ".join(SLUGS))
        state = toggle(chat_id, slug)
        return t("ap." + state, lang, name=_name(slug, lang))
    lines = [t("ap.head", lang)]
    for slug in DAILY:
        key = "ap.list_on" if subscribed(chat_id, slug) else "ap.list_off"
        lines.append("%s  <code>%s</code>" % (t(key, lang, name=_name(slug, lang)), slug))
    reports = [s for s in REPORTS if allows(owner_tier(str(chat_id), signed_in=True), REPORT_FEATURE)]
    if reports:
        lines += ["", t("rp.head", lang)]
        for slug in reports:
            key = "ap.list_on" if subscribed(chat_id, slug) else "ap.list_off"
            lines.append("%s  <code>%s</code>" % (t(key, lang, name=_name(slug, lang)), slug))
    lines += ["", t("ap.quiet", lang), t("ap.usage", lang, slugs=SLUGS[0])]
    return "\n".join(lines)


# --- dashboard -------------------------------------------------------------- #

def _lang():
    from .auth import lang
    return lang()


def dashboard_autopilot(request, user=None):
    """The same switches on the page. Read-only for a rank that cannot use them."""
    owner = (user or {}).get("owner")
    tier = (user or {}).get("rank") or "public"
    ok = allows(tier, FEATURE)
    if request.method == "POST" and ok and owner:
        slug = (request.form.get("slug") or "").strip().lower()
        if slug in BY_SLUG:
            toggle(owner, slug)
    return {"allowed": ok, "reports_ok": allows(tier, REPORT_FEATURE),
            "subs": subscriptions(owner) if owner else {},
            "slugs": DAILY, "reports": REPORTS, "name": lambda slug: _name(slug, _lang())}
