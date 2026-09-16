"""#5 Gold Calendar — what the spread actually did at the last few releases.

Every calendar tells you NFP is at 20:30. None of them tell you the thing that
decides whether you keep your money: **the spread blows out around the release,
and how long it takes to come back.** A stop that was fine at 20:29 is inside
the spread at 20:30, and the trader who re-enters two minutes later pays for it.

The checker has been tagging every five-minute spread sample that falls inside a
red-event window since the calendar shipped. This reads that back as a curve per
event title — calm before, the peak, and the minute the spread came home — and
turns it into the two answers a trader wants:

* **the safe re-entry clock** — how many minutes past the release the spread
  historically stopped being a tax, and how many of those are left right now;
* **is today safe to trade** — one word, from what is on the calendar today.

The honesty rules are the same ones the hours map holds to. One occurrence is an
anecdote, so `MIN_OCCURRENCES` has to be met before anything is claimed. And the
whole thing is free at every rank: a spread you did not see coming is a loss,
and warning about a loss is never what we charge for.
"""

import datetime as dt

from . import store
from .brand import DEFAULT_LANG, t
from .hours import median

BUCKET = 15                    # minutes per point on the curve
SPAN = 60                      # how far either side of the release we plot
CALM_FROM, CALM_TO = -60, -30  # "before anyone was positioning" — the baseline
MIN_OCCURRENCES = 2            # one release is an anecdote, not a record
RECOVERED = 1.2                # within 20% of calm counts as normal again

# "Is today safe to trade": how close a red event has to be before we say so.
DANGER_AHEAD = dt.timedelta(hours=2)
DANGER_BEHIND = dt.timedelta(hours=1)


def _bucket(minutes):
    """Snap an offset to its point on the curve, clipped to the span."""
    snapped = int(round(minutes / BUCKET)) * BUCKET
    return max(-SPAN, min(SPAN, snapped))


def curve(title, occurrences=6, rows=None):
    """The shape of one event's spread, across its last few releases.

    `rows` is injected by the tests. Returns `None` when fewer than
    `MIN_OCCURRENCES` releases have been measured — a curve drawn through one
    release would look exactly as confident as a real one.
    """
    if rows is None:
        rows = store.event_samples(title, occurrences) if store.ready() else []
    if not rows:
        return None
    seen = {r["event_at"] for r in rows}
    if len(seen) < MIN_OCCURRENCES:
        return None
    points, calm_samples = {}, []
    for r in rows:
        minutes = (r["ts"] - r["event_at"]) / 60.0
        if abs(minutes) > SPAN + BUCKET:
            continue
        points.setdefault(_bucket(minutes), []).append(float(r["spread"]))
        if CALM_FROM <= minutes <= CALM_TO:
            calm_samples.append(float(r["spread"]))
    if not points:
        return None
    ordered = [{"minute": m, "median": median(v), "n": len(v)} for m, v in sorted(points.items())]
    calm = median(calm_samples) if calm_samples else ordered[0]["median"]
    after = [p for p in ordered if p["minute"] >= 0]
    peak = max(after or ordered, key=lambda p: p["median"])
    recovery = None
    for point in after:
        if point["minute"] > peak["minute"] and calm and point["median"] <= calm * RECOVERED:
            recovery = point["minute"]
            break
    return {"title": title, "points": ordered, "calm": calm, "peak": peak,
            "recovery": recovery, "occurrences": len(seen),
            "multiple": (peak["median"] / calm) if calm else None}


def records(limit=8):
    """A curve for each event we have measured enough of, worst blow-out first."""
    if not store.ready():
        return []
    out = [curve(title) for title in store.event_titles(limit)]
    return sorted((c for c in out if c), key=lambda c: c["multiple"] or 0, reverse=True)


def clock(crv, event_at, now):
    """The safe re-entry clock for a release happening around now.

    `left` is minutes until the spread historically came home; 0 means it
    already has. `None` when the record never showed a recovery inside the
    span — we will not invent an all-clear we have not seen.
    """
    if not crv or crv["recovery"] is None:
        return None
    since = (now - event_at).total_seconds() / 60.0
    return {"since": since, "recovery": crv["recovery"], "left": max(0, crv["recovery"] - since)}


def today(events, now):
    """One word for "is today safe to trade", and why.

    `avoid` while a red event is close enough that the spread is the trade.
    `careful` when one lands later today. `clear` otherwise.
    """
    local_day = now.date()
    soon = [e for e in events if now - DANGER_BEHIND <= e["at"] <= now + DANGER_AHEAD]
    rest = [e for e in events if e["at"] > now + DANGER_AHEAD and e["at"].date() == local_day]
    band = "avoid" if soon else ("careful" if rest else "clear")
    return {"band": band, "soon": soon, "later": rest, "next": (soon or rest or [None])[0]}


# --- copy --------------------------------------------------------------------- #

def offset_label(minutes):
    """`+30` reads as thirty minutes after the release; `−15` as before it."""
    return ("%+d" % minutes) if minutes else "0"


def lines(recs, lang=DEFAULT_LANG):
    """The bot's answer: one line per measured event."""
    if not recs:
        return [t("evs.none", lang)]
    out = [t("evs.h", lang), ""]
    for c in recs:
        out.append(t("evs.row", lang, title=c["title"], mult="%.1f" % (c["multiple"] or 1),
                     calm="%.2f" % c["calm"], peak="%.2f" % c["peak"]["median"], n=c["occurrences"]))
        out.append("  " + (t("evs.back", lang, n=c["recovery"]) if c["recovery"] is not None
                           else t("evs.never", lang, n=SPAN)))
    out += ["", t("evs.foot", lang)]
    return out


def today_line(verdict, fmt, lang=DEFAULT_LANG):
    """One sentence for the calendar's head: today's verdict, and the event behind it."""
    if not verdict:
        return ""
    nxt = verdict["next"]
    if verdict["band"] == "clear" or not nxt:
        return t("evs.today_clear", lang)
    return t("evs.today_" + verdict["band"], lang, title=nxt["title"], when=fmt(nxt["at"]))
