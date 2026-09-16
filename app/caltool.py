"""#5 Gold Calendar — the bot commands, the dashboard context, and the checker hook."""

import datetime as dt

from flask import current_app

from . import eventspread, goldcal, store
from .brand import DEFAULT_LANG, t

PUSH_MINUTES = 30
PUSH_SLACK = 6   # the checker runs every five minutes; fire inside [24, 36] minutes before
# The push only needs the half hour before. The *record* needs the hour after
# too, because recovery is the half of the story that decides re-entry.
LOG_MINUTES = 60


def _now():
    return dt.datetime.now(goldcal.UTC)


def summary_text(lang, owner=None, now=None):
    now = now or _now()
    lines = [t("cal.title", lang), ""]
    # The verdict first. "Is it safe to trade today" is the question; the
    # timetable underneath it is the evidence.
    events = goldcal.red_events(now, days=2, back_hours=2)
    verdict = eventspread.today(events, now)
    lines.append(eventspread.today_line(verdict, goldcal.fmt_myt, lang))
    if verdict["band"] == "avoid" and verdict["next"]:
        crv = eventspread.curve(verdict["next"]["title"])
        tick = eventspread.clock(crv, verdict["next"]["at"], now)
        if tick:
            lines.append(t("evs.clock_wait", lang, n=int(tick["left"])) if tick["left"]
                         else t("evs.clock_ok", lang))
    lines.append("")
    reds = [e for e in goldcal.red_events(now) if e["at"] > now][:3]
    lines.append("<b>%s</b>" % t("cal.next", lang))
    if reds:
        for e in reds:
            extra = (" · f %s · p %s" % (e["forecast"], e["previous"])) if e["forecast"] or e["previous"] else ""
            lines.append("• %s — %s MYT%s" % (e["title"], goldcal.fmt_myt(e["at"]), extra))
    else:
        lines.append("• %s" % t("cal.none", lang))
    fomc = next((e for e in goldcal.fomc_events(now.year) + goldcal.fomc_events(now.year + 1) if e["at"] > now), None)
    if fomc:
        lines.append("%s: %s MYT" % (t("cal.fomc", lang), goldcal.fmt_myt(fomc["at"])))
    hol = goldcal.next_holiday(now)
    if hol:
        lines.append("%s: %s — %s" % (t("cal.holiday", lang), hol["at"].strftime("%d %b"), hol["title"].split("— ")[-1]))
    season = goldcal.seasonality()
    m = season[now.astimezone(goldcal.MYT).month]
    lines.append("")
    lines.append("<b>%s</b>: %s" % (t("cal.season", lang, n=m["n"]), t("cal.season_line", lang, ret=m["avg_return"], rng=m["avg_range"])))
    lines.append("")
    lines.append(t("cal.on" if (owner and store.calendar_subscribed(owner)) else "cal.off", lang))
    return "\n".join(lines)


# --- bot -------------------------------------------------------------------- #

def bot_calendar(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if args and args[0].lower() in ("spread", "record", "rekod"):
        # Free at every rank: a spread you did not see coming is a loss, and
        # warning about a loss is never the thing we charge for.
        return "\n".join(eventspread.lines(eventspread.records(), lang))
    return summary_text(lang, owner=chat_id)


def bot_calendar_alert(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """The standing reminder — a General capability.

    Reading the calendar stays free: /calendar answers in full for anyone.
    What the rank buys is the app *remembering* to warn you thirty minutes
    before each red event, which is the same thing an armed alert buys."""
    if not chat_id:
        return t("cal.need_chat", lang)
    from .gate import bot_gate
    blocked = bot_gate("alerts", chat_id=chat_id, lang=lang)
    if blocked:
        return blocked
    state = store.calendar_toggle(chat_id)
    return t("cal.on" if state else "cal.off", lang)


# --- checker hook ------------------------------------------------------------ #

def check_calendar(send, quote, now=None):
    """Called by the five-minute checker with the quote it already fetched.

    Logs the spread (tagged when inside a red window) and pushes to every
    subscriber once per event, ~30 minutes ahead.
    """
    now = now or _now()
    reds = goldcal.red_events(now, days=2, back_hours=2)
    inside = next((e for e in reds if goldcal.in_window(e, now, LOG_MINUTES)), None)
    store.log_spread(quote, inside)

    pushed = 0
    subs = store.calendar_subscribers()
    if not subs:
        return {"pushed": 0}
    for e in reds:
        minutes = (e["at"] - now).total_seconds() / 60
        if not (PUSH_MINUTES - PUSH_SLACK <= minutes <= PUSH_MINUTES + PUSH_SLACK):
            continue
        key = goldcal.event_key(e)
        for owner in subs:
            if store.calendar_mark_sent(key, owner):
                lang = store.tg_lang(owner) or DEFAULT_LANG
                send(owner, t("cal.push", lang, title=e["title"], when=goldcal.fmt_myt(e["at"])))
                pushed += 1
    return {"pushed": pushed}


# --- dashboard -------------------------------------------------------------- #

def dashboard_calendar(request, user=None):
    now = _now()
    owner = user["owner"] if user else None
    local = now.astimezone(goldcal.MYT)
    try:
        year, month = int(request.values.get("y", local.year)), int(request.values.get("m", local.month))
        dt.date(year, month, 1)
    except ValueError:
        year, month = local.year, local.month
    from .gate import allows, upgrade_line, user_tier
    from .auth import lang as ui_lang
    may_subscribe = allows(user_tier(user), "alerts")
    notice = None
    if owner and request.method == "POST" and request.form.get("action") in ("cal_on", "cal_off"):
        if may_subscribe:
            store.calendar_toggle(owner, request.form["action"] == "cal_on")
            notice = "ok"
        else:
            notice = "gated"
    events = goldcal.red_events(now, days=62, back_hours=2)
    prev = (dt.date(year, month, 1) - dt.timedelta(days=1))
    nxt = (dt.date(year, month, 28) + dt.timedelta(days=4)).replace(day=1)
    season = goldcal.seasonality()
    return {
        "year": year, "month": month, "month_name": dt.date(year, month, 1).strftime("%B"),
        "prev": (prev.year, prev.month), "next": (nxt.year, nxt.month),
        "weeks": goldcal.month_grid(year, month, now, events),
        "upcoming": [e for e in events if e["at"] > now][:10],
        "season": season, "this_month": season[local.month],
        "holiday": goldcal.next_holiday(now),
        "subscribed": bool(owner and may_subscribe and store.calendar_subscribed(owner)),
        "may_subscribe": may_subscribe,
        "upgrade": "" if may_subscribe else upgrade_line("alerts", ui_lang()),
        "owner": owner, "notice": notice,
        "baseline": store.baseline_spread(), "history": store.event_spread_history(),
        "records": eventspread.records(), "today": eventspread.today(events, now),
        "today_line": eventspread.today_line(eventspread.today(events, now), goldcal.fmt_myt, ui_lang()),
        "offset": eventspread.offset_label, "span": eventspread.SPAN,
        "fmt_myt": goldcal.fmt_myt, "fmt_utc": goldcal.fmt_utc,
        "quarter": (local.month - 1) // 3 + 1,
    }


def quarter_pdf_bytes():
    now = _now()
    local = now.astimezone(goldcal.MYT)
    quarter = (local.month - 1) // 3 + 1
    events = goldcal.red_events(now, days=120)
    return quarter_filename(local.year, quarter), goldcal.quarter_pdf(local.year, quarter, events, goldcal.seasonality(),
                                                                          brand=current_app.config.get("BRAND_NAME", "SAMBANGGOLD"))


def quarter_filename(year, quarter):
    return "sambanggold-gold-calendar-%dQ%d.pdf" % (year, quarter)
