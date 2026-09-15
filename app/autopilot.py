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


def _day(now):
    return time.strftime("%Y-%m-%d", time.gmtime(now))


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


JOBS = (
    ("gold-watch", _gold),
    ("miner-divergence", _miners),
    ("tokenized-gold", _tokengold),
    ("drawdown-sentinel", _sentinel),
    ("exposure-monitor", _exposure),
)
BY_SLUG = dict(JOBS)
SLUGS = tuple(slug for slug, _ in JOBS)


# --- subscriptions ---------------------------------------------------------- #

def subscribed(owner, slug):
    return store.get_setting(slug, owner, SETTING) == "on"


def toggle(owner, slug, on=None):
    """Turn a product's autopilot on or off; returns the new state."""
    if slug not in BY_SLUG:
        raise KeyError(slug)
    state = ("on" if on else "off") if on is not None else ("off" if subscribed(owner, slug) else "on")
    store.set_setting(slug, owner, SETTING, state if state == "on" else "")
    return state


def subscriptions(owner):
    return {slug: subscribed(owner, slug) for slug in SLUGS}


# --- the run ---------------------------------------------------------------- #

def run_daily(send, now=None):
    """Push one digest per subscribed owner per product per day.

    A rank that has lapsed simply stops producing pushes — the subscription
    row stays, so it resumes the day the rank comes back.
    """
    now = time.time() if now is None else now
    day, sent, skipped = _day(now), 0, 0
    for slug, build in JOBS:
        for owner in store.owners_by_setting(slug, SETTING, "on"):
            if not allows(owner_tier(owner, signed_in=True), FEATURE):
                skipped += 1
                continue
            if store.get_setting(slug, owner, "ap_sent") == day:
                continue
            lang = store.tg_lang(owner) or DEFAULT_LANG
            text = build(owner, lang)
            store.set_setting(slug, owner, "ap_sent", day)   # a quiet day still counts as done
            if not text:
                continue
            send(owner, "%s\n\n%s" % (text, t("ap.footer", lang)))
            sent += 1
    return {"sent": sent, "gated": skipped, "day": day}


# --- bot -------------------------------------------------------------------- #

def _name(slug, lang):
    from .products import BY_SLUG as PRODUCTS
    p = PRODUCTS[slug].view(lang)
    return "%s %s" % (p.emoji, p.name)


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
    for slug in SLUGS:
        key = "ap.list_on" if subscribed(chat_id, slug) else "ap.list_off"
        lines.append("%s  <code>%s</code>" % (t(key, lang, name=_name(slug, lang)), slug))
    lines += ["", t("ap.quiet", lang), t("ap.usage", lang, slugs=SLUGS[0])]
    return "\n".join(lines)


# --- dashboard -------------------------------------------------------------- #

def dashboard_autopilot(request, user=None):
    """The same switches on the page. Read-only for a rank that cannot use them."""
    owner = (user or {}).get("owner")
    tier = (user or {}).get("rank") or "public"
    ok = allows(tier, FEATURE)
    if request.method == "POST" and ok and owner:
        slug = (request.form.get("slug") or "").strip().lower()
        if slug in BY_SLUG:
            toggle(owner, slug)
    return {"allowed": ok, "subs": subscriptions(owner) if owner else {}, "slugs": SLUGS}
