"""The Morning Brief — one message, at your hour, with the whole day's risk in it.

Eighteen tools is eighteen things to remember to check, and nobody checks
eighteen things. The autopilot solved half of that for A-Team by making each
tool speak for itself, but five separate pushes is still five. This is the other
half: **one message, once a day, at an hour you pick, that covers everything
that decides whether today is a day to trade.**

It is deliberately built out of the answers that are already free:

* is today safe to trade at all, from the calendar;
* is this a cheap hour or a dear one, from the hours map;
* has the tokenised-gold premium left its band;
* and anything of *yours* that moved overnight — an alert that fired, an
  account that is no longer safe against its rule pack.

What a rank buys is the same thing it always buys here: not the answer, which
anyone can ask for any time, but the app remembering to send it. That puts the
brief on `alerts`, beside the calendar reminder, which is the free door General
already opens.

The hour is stored in **KL time**, because someone choosing when to be woken is
not going to convert it.
"""

import time

from . import store
from .brand import DEFAULT_LANG, t
from .hours import KL_OFFSET

SLUG = "brief"
FEATURE = "alerts"
HOUR_KEY = "hour"
SENT_KEY = "sent"
DEFAULT_HOUR = 8          # before the London open, after the Malaysian breakfast
OVERNIGHT = 86400


def _day(now):
    """The KL day, so a brief sent at 08:00 MYT is one per calendar day there."""
    return time.strftime("%Y-%m-%d", time.gmtime(now + KL_OFFSET))


def kl_hour(now):
    return time.gmtime(now + KL_OFFSET).tm_hour


# --- the subscription --------------------------------------------------------- #

def hour_of(owner):
    """The KL hour this owner asked for, or None when the brief is off."""
    raw = store.get_setting(SLUG, owner, HOUR_KEY)
    return int(raw) if raw.isdigit() else None


def set_hour(owner, hour):
    """Turn it on at `hour` (KL). Returns the hour, or None when it is nonsense."""
    try:
        hour = int(str(hour).split(":")[0])
    except (TypeError, ValueError):
        return None
    if not 0 <= hour <= 23:
        return None
    store.set_setting(SLUG, owner, HOUR_KEY, str(hour))
    return hour


def off(owner):
    store.set_setting(SLUG, owner, HOUR_KEY, "")


def subscribers(hour):
    return store.owners_by_setting(SLUG, HOUR_KEY, str(hour))


# --- the sections --------------------------------------------------------------- #
# Each returns a line (or lines), or None for "nothing to say". A section that
# has nothing to say is left out rather than padded, because a brief that always
# looks the same is a brief nobody reads.

def _calendar(owner, lang, now):
    from . import eventspread, goldcal
    try:
        events = goldcal.red_events(days=2, back_hours=2)
    except Exception:                       # noqa: BLE001 — a dead feed must not kill the brief
        return None
    import datetime as dt
    verdict = eventspread.today(events, dt.datetime.fromtimestamp(now, goldcal.UTC))
    return eventspread.today_line(verdict, goldcal.fmt_myt, lang)


def _hours(owner, lang, now):
    from . import hours as hours_map
    prof = hours_map.profile(hours_map.days_for(owner=owner))
    verd = hours_map.verdict(prof, now)
    if not verd or verd["band"] == "thin":
        return None
    return "\n".join(hours_map.lines(prof, verd, 1, lang)[1:3])


def _premium(owner, lang, now):
    from . import tokengoldtool
    try:
        a = tokengoldtool._analysed()
    except Exception:                       # noqa: BLE001 — same reason
        return None
    from . import premium
    measured = premium.bands(a)
    out = [premium.line(measured[asset], lang) for asset in premium.ASSETS if measured[asset]]
    best = premium.cheapest(a)
    if best and out:
        out.append(t("band.route", lang, asset=best["asset"].upper(), premium="%+.2f" % best["premium"],
                     saving="%.2f" % best["saving"], other=best["other"].upper()))
    if out:
        return "\n".join(out)
    return t("brief.premium_off", lang) if a["flags"] else t("brief.premium_ok", lang)


def _yours(owner, lang, now):
    """Only the owner's own overnight movement — never a generic line."""
    from . import sentinel
    from .watch import fmt
    out = []
    fired = [r for r in store.triggers_for(owner, limit=50) if r["fired_at"] > now - OVERNIGHT]
    if fired:
        out.append(t("brief.fired", lang, n=len(fired)))
        for r in fired[:3]:
            out.append("• %s %s %s @ %s" % (r["symbol"], t("watch." + r["direction"], lang),
                                            fmt(r["level"]), fmt(r["price"])))
    hot = [a for a in store.sentinels_for(owner) if sentinel.evaluate(a, a["pack"])["state"] != "safe"]
    if hot:
        out.append(t("brief.sentinel", lang, n=len(hot), names=", ".join(a["name"] for a in hot[:3])))
    return "\n".join(out) if out else None


SECTIONS = (("calendar", _calendar), ("hours", _hours), ("premium", _premium), ("yours", _yours))


def build(owner, lang=DEFAULT_LANG, now=None):
    """The whole brief as one message, or None when nothing could be gathered."""
    now = time.time() if now is None else now
    blocks = []
    for _, section in SECTIONS:
        try:
            text = section(owner, lang, now)
        except Exception:                   # noqa: BLE001 — one dead section never eats the brief
            text = None
        if text:
            blocks.append(text)
    if not blocks:
        return None
    head = t("brief.h", lang, date=time.strftime("%d %b", time.gmtime(now + KL_OFFSET)))
    return "\n\n".join([head] + blocks + [t("brief.foot", lang)])


# --- the run ------------------------------------------------------------------- #

def run_due(send, now=None):
    """Called by the five-minute checker. One brief per owner per KL day.

    The day is marked sent whether or not there was anything to say, so a quiet
    morning cannot pile up into two messages at noon.
    """
    from .gate import allows, owner_tier
    now = time.time() if now is None else now
    day, hour = _day(now), kl_hour(now)
    sent = gated = 0
    for owner in subscribers(hour):
        if store.get_setting(SLUG, owner, SENT_KEY) == day:
            continue
        if not allows(owner_tier(owner), FEATURE):
            gated += 1
            continue
        lang = store.tg_lang(owner) or DEFAULT_LANG
        text = build(owner, lang, now)
        store.set_setting(SLUG, owner, SENT_KEY, day)
        if not text:
            continue
        send(owner, text)
        sent += 1
    return {"brief_sent": sent, "brief_gated": gated}


# --- surfaces -------------------------------------------------------------------- #

def bot_brief(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/brief` reads it now, `/brief 8` sets the hour, `/brief off` stops it."""
    owner = str(chat_id) if chat_id else ""
    if not owner:
        return t("brief.need_chat", lang)
    word = args[0].lower() if args else ""
    if word in ("off", "stop", "mati"):
        off(owner)
        return t("brief.off", lang)
    if word:
        from .gate import bot_gate
        blocked = bot_gate(FEATURE, chat_id=chat_id, lang=lang)
        if blocked:
            return blocked      # reading it stays free; being sent it is the rank
        hour = set_hour(owner, word)
        if hour is None:
            return t("brief.bad_hour", lang)
        return t("brief.on", lang, hour="%02d:00" % hour)
    text = build(owner, lang)
    tail = t("brief.at", lang, hour="%02d:00" % hour_of(owner)) if hour_of(owner) is not None else t("brief.set", lang)
    return "\n\n".join([text or t("brief.empty", lang), tail])


def dashboard_brief(request, user=None):
    """The dashboard panel: the hour picker and a preview of today's brief."""
    from .auth import lang as ui_lang
    from .gate import allows, upgrade_line, user_tier
    lang = ui_lang()
    owner = user["owner"] if user else None
    allowed = allows(user_tier(user), FEATURE)
    ctx = {"owner": owner, "allowed": allowed, "hour": hour_of(owner) if owner else None,
           "default": DEFAULT_HOUR, "hours": range(24), "preview": None,
           "upgrade": "" if allowed else upgrade_line(FEATURE, lang)}
    if owner and request.method == "POST" and request.form.get("action") == "brief":
        if not allowed:
            ctx["notice"] = "gated"
        elif request.form.get("hour") == "off":
            off(owner)
            ctx["hour"] = None
        else:
            ctx["hour"] = set_hour(owner, request.form.get("hour"))
    if owner:
        ctx["preview"] = build(owner, lang)
    return ctx
