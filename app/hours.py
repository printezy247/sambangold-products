"""#1 Gold Watch — the best and worst hours to trade, from our own spread log.

The checker has been sampling the gold bid, ask and spread every five minutes
since the day it shipped, and until now nothing read it back. That log is the
one thing here a competitor cannot copy: a month of observed cost, on the same
feed the alerts fire from.

What it answers is not "what is the spread" — the price panel already says that.
It is the question a trader actually has at 9am: **is now a sensible time to
enter, or should I wait?** The spread is the entry fee, it moves by several
times across the trading day, and paying it at the wrong hour costs more than
most people's stop.

Three rules keep this honest:

* **KL time, not UTC.** The audience is in Malaysia. An hour label they have to
  convert is an hour label they will misread.
* **An hour with too few samples says so.** `MIN_SAMPLES` is the floor; under it
  an hour is "not measured yet", never a verdict. A confident wrong answer about
  when to trade is worse than no answer.
* **The verdict is free.** Knowing you are about to overpay is safety, not
  convenience, so the current hour always answers. What a rank buys is the
  length of the window behind it.
"""

import time

from . import store
from .brand import DEFAULT_LANG, t

KL_OFFSET = 8 * 3600          # Malaysia has no daylight saving, so this is a constant
HOURS = 24
MIN_SAMPLES = 6               # half an hour of checker runs; under it we do not judge
OUNCES_PER_LOT = 100          # XAUUSD: spread is per ounce, cost is per lot

# An hour is cheap or dear relative to the day's own median, not to an absolute
# number — the absolute widens for everyone when the market is thin.
CHEAP = 0.90
DEAR = 1.15


def kl_hour(ts):
    """The hour in Kuala Lumpur that this timestamp falls in."""
    return time.gmtime(ts + KL_OFFSET).tm_hour


def now_hour(now=None):
    return kl_hour(now if now is not None else time.time())


def median(values):
    """Shared with the calendar's event record — both read the same spread log,
    and two copies of this would eventually disagree."""
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return None
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def profile(days=30, samples=None):
    """Twenty-four rows, one per KL hour.

    `samples` is injected by the tests; in production it comes from the log the
    checker writes. Returns `None` when there is nothing measured at all, so the
    caller shows "collecting" rather than an empty table pretending to be data.
    """
    rows_in = store.spread_samples(days) if samples is None else samples
    buckets = [[] for _ in range(HOURS)]
    for ts, spread in rows_in:
        if spread is not None:
            buckets[kl_hour(ts)].append(float(spread))
    measured = [s for bucket in buckets for s in bucket]
    if not measured:
        return None
    overall = median(measured)
    rows = []
    for hour in range(HOURS):
        bucket = buckets[hour]
        mid = median(bucket)
        thin = len(bucket) < MIN_SAMPLES
        if thin or not overall:
            band, ratio = "thin", None
        else:
            ratio = mid / overall
            band = "best" if ratio <= CHEAP else ("worst" if ratio >= DEAR else "ok")
        rows.append({"hour": hour, "n": len(bucket), "median": mid, "ratio": ratio, "band": band})
    graded = [r for r in rows if r["band"] != "thin"]
    return {
        "rows": rows, "overall": overall, "days": days,
        "samples": len(measured), "measured_hours": len(graded),
        "best": min(graded, key=lambda r: r["median"], default=None),
        "worst": max(graded, key=lambda r: r["median"], default=None),
    }


def verdict(prof, now=None):
    """What this hour is, and when the next cheap one starts.

    `wait` is whole hours until the next hour graded `best`; 0 means this hour
    already is one, and `None` means none of the measured hours qualify, so
    there is nothing honest to tell someone to wait for.
    """
    if not prof:
        return None
    hour = now_hour(now)
    row = prof["rows"][hour]
    wait = None
    if row["band"] == "best":
        wait = 0
    else:
        for ahead in range(1, HOURS):
            if prof["rows"][(hour + ahead) % HOURS]["band"] == "best":
                wait = ahead
                break
    nxt = prof["rows"][(hour + wait) % HOURS] if wait else row
    return {"hour": hour, "row": row, "band": row["band"], "wait": wait, "next": nxt}


def cost_of_waiting(prof, verd, lots=1.0):
    """What entering now costs over entering in the next cheap hour, in dollars.

    None when this hour is not measured, or when there is no cheaper hour to
    compare it against — an invented saving would be worse than a blank.
    """
    if not prof or not verd or verd["row"]["median"] is None or not verd.get("wait"):
        return None
    gap = verd["row"]["median"] - verd["next"]["median"]
    return max(0.0, gap) * OUNCES_PER_LOT * float(lots)


# --- copy ------------------------------------------------------------------- #

def label(hour):
    """`14:00` — the hour as someone in KL reads a clock."""
    return "%02d:00" % hour


def window(row):
    return "%s–%s" % (label(row["hour"]), label((row["hour"] + 1) % HOURS))


def lines(prof, verd, lots=1.0, lang=DEFAULT_LANG):
    """The bot's answer: the verdict first, the evidence after."""
    if not prof or not verd:
        return [t("hours.none", lang)]
    out = [t("hours.h", lang)]
    if verd["band"] == "thin":
        out.append(t("hours.now_thin", lang, window=window(verd["row"])))
    else:
        out.append(t("hours.now_" + verd["band"], lang, window=window(verd["row"]),
                     spread="%.2f" % verd["row"]["median"]))
    if verd["wait"]:
        out.append(t("hours.wait", lang, n=verd["wait"], window=window(verd["next"])))
        cost = cost_of_waiting(prof, verd, lots)
        if cost and cost >= 1:
            out.append(t("hours.cost", lang, usd="%.0f" % cost, lots=("%g" % float(lots))))
    elif verd["band"] == "best":
        out.append(t("hours.now_is_best", lang))
    if prof["best"] and prof["worst"] and prof["best"]["hour"] != prof["worst"]["hour"]:
        out += ["",
                t("hours.best", lang, window=window(prof["best"]), spread="%.2f" % prof["best"]["median"]),
                t("hours.worst", lang, window=window(prof["worst"]), spread="%.2f" % prof["worst"]["median"])]
    out += ["", t("hours.from", lang, n=prof["samples"], days=prof["days"])]
    return out


def days_for(user=None, chat_id=None, owner=None):
    """How far back this caller's rank lets the map look."""
    from .gate import limit
    return limit("hours_days", user=user, chat_id=chat_id, owner=owner) or 30
