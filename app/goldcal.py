"""#5 Gold Seasonality Calendar — the engine.

Three inputs, all free and keyless:

* **Forex Factory weekly JSON** (this week + next week) for the red USD
  events — the same feed Sam's website reads. Cached 30 minutes; the last
  good copy is kept when the feed is unreachable.
* **Fixed public schedules**, embedded: the FOMC statement days and the CME
  Globex holidays for the year, so the month grid reaches past the feed's
  two-week horizon.
* **Yahoo ``GC=F`` monthly history** for seasonality — average return and
  average range per calendar month over ten years — cached a day, with a
  long-run static table as the fallback (labelled as such).

"What the spread did last time" is measured, not guessed: the five-minute
checker logs the spread while it runs and tags the samples that fall inside
±30 minutes of a red event, so each event title builds its own history.
"""

import calendar as _cal
import datetime as dt
import statistics
import time
from zoneinfo import ZoneInfo

import requests

FF_URLS = (
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
)
YAHOO_MONTHLY = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=10y&interval=1mo"
TIMEOUT = 6
FEED_TTL = 1800
SEASON_TTL = 86400
UTC = dt.timezone.utc
MYT = ZoneInfo("Asia/Kuala_Lumpur")
NY = ZoneInfo("America/New_York")

# FOMC statement days (second day of each meeting), statement at 14:00 New York.
FOMC = {
    2026: [(1, 28), (3, 18), (4, 29), (6, 17), (7, 29), (9, 16), (10, 28), (12, 9)],
}
# CME Globex full-close days for metals.
CME_HOLIDAYS = {
    2026: {(1, 1): "New Year's Day", (4, 3): "Good Friday", (12, 25): "Christmas Day"},
}
# US bank holidays where metals trade a shortened session and liquidity thins.
THIN_DAYS = {
    2026: {(1, 19): "MLK Day", (2, 16): "Presidents' Day", (5, 25): "Memorial Day", (6, 19): "Juneteenth",
           (7, 3): "Independence Day (obs.)", (9, 7): "Labor Day", (11, 26): "Thanksgiving"},
}
# Long-run gold seasonality (approximate 20-year averages), used only when Yahoo is unreachable.
SEASONALITY_STATIC = {
    1: (2.5, 4.8), 2: (0.8, 4.4), 3: (-0.4, 4.6), 4: (0.9, 3.9), 5: (-0.2, 4.2), 6: (-0.6, 4.0),
    7: (1.1, 3.8), 8: (1.5, 4.5), 9: (1.3, 4.9), 10: (-0.3, 4.7), 11: (0.4, 4.6), 12: (1.0, 4.1),
}

_feed_cache = {"at": 0.0, "events": []}
_season_cache = {"at": 0.0, "table": None}


# --- events ---------------------------------------------------------------- #

def _parse_feed(raw):
    out = []
    for e in raw:
        try:
            at = dt.datetime.fromisoformat(e["date"]).astimezone(UTC)
        except (KeyError, ValueError, TypeError):
            continue
        out.append({"title": e.get("title", ""), "country": e.get("country", ""), "impact": e.get("impact", ""),
                    "at": at, "forecast": e.get("forecast") or "", "previous": e.get("previous") or "",
                    "source": "Forex Factory"})
    return out


def fetch_events():
    """Both weeks of the feed, parsed and sorted. Never raises; falls back to the last good copy."""
    now = time.time()
    if _feed_cache["events"] and now - _feed_cache["at"] < FEED_TTL:
        return _feed_cache["events"]
    events = []
    for url in FF_URLS:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0 (compatible; sambangold/1.0)"})
            r.raise_for_status()
            events += _parse_feed(r.json())
        except Exception:  # noqa: BLE001 — a dead feed must never take the page down
            continue
    if events:
        seen, unique = set(), []
        for e in sorted(events, key=lambda x: x["at"]):
            key = (e["title"], e["at"])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        _feed_cache.update(at=now, events=unique)
        return unique
    return _feed_cache["events"]


def clear_cache():
    _feed_cache.update(at=0.0, events=[])
    _season_cache.update(at=0.0, table=None)


def fomc_events(year):
    out = []
    for month, day in FOMC.get(year, []):
        at = dt.datetime(year, month, day, 14, 0, tzinfo=NY).astimezone(UTC)
        out.append({"title": "FOMC Statement", "country": "USD", "impact": "High", "at": at,
                    "forecast": "", "previous": "", "source": "Federal Reserve schedule"})
    return out


def holiday_events(year):
    out = []
    for (m, d), name in CME_HOLIDAYS.get(year, {}).items():
        out.append({"title": "CME closed — %s" % name, "country": "USD", "impact": "Holiday",
                    "at": dt.datetime(year, m, d, 0, 0, tzinfo=UTC), "forecast": "", "previous": "", "source": "CME"})
    for (m, d), name in THIN_DAYS.get(year, {}).items():
        out.append({"title": "Thin session — %s" % name, "country": "USD", "impact": "Holiday",
                    "at": dt.datetime(year, m, d, 0, 0, tzinfo=UTC), "forecast": "", "previous": "", "source": "CME"})
    return out


def red_events(now=None, days=14, events=None):
    """High-impact USD events ahead, feed first, FOMC schedule filling the gaps."""
    now = now or dt.datetime.now(UTC)
    feed = [e for e in (events if events is not None else fetch_events())
            if e["impact"] == "High" and e["country"] == "USD"]
    merged = list(feed)
    feed_days = {e["at"].date() for e in feed if "FOMC" in e["title"].upper()}
    for e in fomc_events(now.year) + fomc_events(now.year + 1):
        if e["at"].date() not in feed_days:
            merged.append(e)
    horizon = now + dt.timedelta(days=days)
    return sorted((e for e in merged if now - dt.timedelta(hours=1) <= e["at"] <= horizon), key=lambda e: e["at"])


def next_holiday(now=None):
    now = now or dt.datetime.now(UTC)
    ahead = [e for e in holiday_events(now.year) + holiday_events(now.year + 1) if e["at"].date() >= now.date()]
    return min(ahead, key=lambda e: e["at"]) if ahead else None


def in_window(event, now, minutes=30):
    return abs((event["at"] - now).total_seconds()) <= minutes * 60


def event_key(event):
    return "%s@%s" % (event["title"], event["at"].strftime("%Y%m%d%H%M"))


# --- seasonality ------------------------------------------------------------ #

def _yahoo_monthly():
    body = requests.get(YAHOO_MONTHLY, timeout=TIMEOUT, headers={"User-Agent": "sambangold/1.0"}).json()
    result = body["chart"]["result"][0]
    stamps = result["timestamp"]
    q = result["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, UTC), o, h, l, c)
            for t, o, h, l, c in zip(stamps, q["open"], q["high"], q["low"], q["close"])
            if None not in (o, h, l, c)]


def seasonality():
    """{month: {"avg_return": %, "avg_range": %, "n": years}} plus a "source" label."""
    now = time.time()
    if _season_cache["table"] and now - _season_cache["at"] < SEASON_TTL:
        return _season_cache["table"]
    try:
        rows = _yahoo_monthly()
        by_month = {m: {"ret": [], "rng": []} for m in range(1, 13)}
        for at, o, h, l, c in rows:
            if o:
                by_month[at.month]["ret"].append((c - o) / o * 100)
                by_month[at.month]["rng"].append((h - l) / o * 100)
        table = {m: {"avg_return": statistics.fmean(v["ret"]), "avg_range": statistics.fmean(v["rng"]), "n": len(v["ret"])}
                 for m, v in by_month.items() if v["ret"]}
        if len(table) < 12:
            raise ValueError("incomplete")
        table["source"] = "Yahoo GC=F, 10 years"
    except Exception:  # noqa: BLE001
        table = {m: {"avg_return": r, "avg_range": g, "n": 20} for m, (r, g) in SEASONALITY_STATIC.items()}
        table["source"] = "long-run static table"
    _season_cache.update(at=now, table=table)
    return table


# --- month grid -------------------------------------------------------------- #

def month_grid(year, month, now=None, events=None):
    """Weeks (Mon..Sun) of day cells with the markers a trader scans for."""
    now = now or dt.datetime.now(UTC)
    reds = [e for e in (events if events is not None else red_events(now, days=62))]
    hols = holiday_events(year)
    marks = {}
    for e in reds:
        d = e["at"].astimezone(MYT).date()
        marks.setdefault(d, []).append(e)
    for e in hols:
        marks.setdefault(e["at"].date(), []).append(e)
    weeks = []
    for week in _cal.Calendar(firstweekday=0).monthdatescalendar(year, month):
        row = []
        for day in week:
            row.append({
                "date": day, "in_month": day.month == month, "today": day == now.astimezone(MYT).date(),
                "weekend": day.weekday() >= 5,
                "events": [e for e in marks.get(day, []) if e["impact"] == "High"],
                "holidays": [e for e in marks.get(day, []) if e["impact"] == "Holiday"],
            })
        weeks.append(row)
    return weeks


def fmt_myt(at):
    return at.astimezone(MYT).strftime("%a %d %b %H:%M")


def fmt_utc(at):
    return at.astimezone(UTC).strftime("%H:%M")


# --- quarter PDF (standard library only) ------------------------------------- #

def _pdf_escape(s):
    s = s.encode("latin-1", "replace").decode("latin-1")   # Courier is Latin-1 only
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def quarter_pdf(year, quarter, events, season, brand="SAMBANGGOLD"):
    """A plain, printable PDF: one page per month with its events and seasonality."""
    months = range((quarter - 1) * 3 + 1, quarter * 3 + 1)
    pages = []
    for m in months:
        lines = ["%s — Gold calendar %s %d" % (brand, _cal.month_name[m], year), ""]
        s = season.get(m, {})
        if s:
            lines.append("Seasonality: avg return %+.1f%%  avg range %.1f%%  (%s)" % (s["avg_return"], s["avg_range"], season.get("source", "")))
            lines.append("")
        month_events = [e for e in events if e["at"].astimezone(MYT).year == year and e["at"].astimezone(MYT).month == m]
        for e in holiday_events(year):
            if e["at"].month == m:
                month_events.append(e)
        month_events.sort(key=lambda e: e["at"])
        lines.append("Events (MYT):")
        if not month_events:
            lines.append("  no red USD events in the feed yet for this month")
        for e in month_events:
            when = e["at"].astimezone(MYT).strftime("%d %b %H:%M") if e["impact"] != "Holiday" else e["at"].strftime("%d %b")
            lines.append("  %s  %s" % (when, e["title"]))
        lines += ["", "Educational research only. Not financial advice. Verify every price with your broker."]
        pages.append(lines)

    return simple_pdf(pages)


def simple_pdf(pages):
    """A plain Courier PDF from a list of pages, each a list of text lines. No dependencies."""
    objs = []
    font_id = 3 + 2 * len(pages)
    kids = []
    for i, lines in enumerate(pages):
        page_id, content_id = 3 + 2 * i, 4 + 2 * i
        kids.append(page_id)
        text = "BT /F1 11 Tf 40 800 Td 15 TL " + " ".join("(%s) Tj T*" % _pdf_escape(l) for l in lines) + " ET"
        objs.append((page_id, "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>" % (content_id, font_id)))
        objs.append((content_id, "<< /Length %d >>\nstream\n%s\nendstream" % (len(text), text)))
    objs.append((font_id, "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"))
    header = [(1, "<< /Type /Catalog /Pages 2 0 R >>"),
              (2, "<< /Type /Pages /Kids [%s] /Count %d >>" % (" ".join("%d 0 R" % k for k in kids), len(kids)))]
    out = "%PDF-1.4\n"
    offsets = {}
    for oid, body in header + objs:
        offsets[oid] = len(out.encode("latin-1"))
        out += "%d 0 obj\n%s\nendobj\n" % (oid, body)
    xref_at = len(out.encode("latin-1"))
    n = max(offsets) + 1
    out += "xref\n0 %d\n0000000000 65535 f \n" % n
    for oid in range(1, n):
        out += "%010d 00000 n \n" % offsets.get(oid, 0)
    out += "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (n, xref_at)
    return out.encode("latin-1", "replace")
