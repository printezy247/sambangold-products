"""#2 XAUUSD Signal Verifier — was the claimed fill price ever printed?

Binance ``PAXGUSDT`` one-minute candles are the record: PAXG is one ounce of
gold, trades 24/7, and the klines endpoint is free and public. Yahoo ``GC=F``
one-minute bars are the fallback for the last seven days (futures carry a
basis over spot, so the tolerance is wider and the source is always named).

A claim is a price and a time window. The verdict comes from the window's
low and high:

* REAL        — the price sits inside a candle's range
* BORDERLINE  — outside every candle but within the source tolerance
  (PAXG premium, futures basis, a broker's own spread)
* IMPOSSIBLE  — further away than that
* UNVERIFIED  — no candles for that window (too old, or every source down)
"""

import datetime as dt

import requests

from .goldcal import MYT, UTC

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
TIMEOUT = 8
TOLERANCE = {"Binance PAXGUSDT": 0.004, "Yahoo GC=F": 0.012}   # 0.4 % PAXG premium, 1.2 % futures basis
WINDOW_MINUTES = 60          # a claim with a time: ± this
MAX_CANDLES = 1000

VERDICTS = ("REAL", "BORDERLINE", "IMPOSSIBLE", "UNVERIFIED")


class NoData(RuntimeError):
    pass


# --- candles ------------------------------------------------------------------ #

def _binance(start, end):
    params = {"symbol": "PAXGUSDT", "interval": "1m", "limit": MAX_CANDLES,
              "startTime": int(start.timestamp() * 1000), "endTime": int(end.timestamp() * 1000)}
    body = requests.get(BINANCE_KLINES, params=params, timeout=TIMEOUT).json()
    if not isinstance(body, list):
        raise NoData(str(body)[:120])
    return [{"at": dt.datetime.fromtimestamp(k[0] / 1000, UTC), "open": float(k[1]), "high": float(k[2]),
             "low": float(k[3]), "close": float(k[4])} for k in body]


def _yahoo(start, end):
    params = {"period1": int(start.timestamp()), "period2": int(end.timestamp()), "interval": "1m"}
    body = requests.get(YAHOO_CHART, params=params, timeout=TIMEOUT, headers={"User-Agent": "sambangold/1.0"}).json()
    result = body["chart"]["result"][0]
    stamps = result.get("timestamp") or []
    q = result["indicators"]["quote"][0]
    out = []
    for i, ts in enumerate(stamps):
        if q["low"][i] is None or q["high"][i] is None:
            continue
        out.append({"at": dt.datetime.fromtimestamp(ts, UTC), "open": q["open"][i], "high": q["high"][i],
                    "low": q["low"][i], "close": q["close"][i]})
    return out


def fetch_candles(start, end):
    """(source, candles) from the first source that has bars for the window. Raises NoData."""
    errors = []
    for name, fn in (("Binance PAXGUSDT", _binance), ("Yahoo GC=F", _yahoo)):
        try:
            candles = fn(start, end)
            if candles:
                return name, candles
            errors.append("%s: no bars" % name)
        except Exception as exc:  # noqa: BLE001 — any failure means try the next source
            errors.append("%s: %s" % (name, exc))
    raise NoData("; ".join(errors))


# --- claims -------------------------------------------------------------------- #

def parse_when(date_text=None, time_text=None, now=None):
    """(start, end, label) in UTC from a date and optional time typed in MYT.

    No date → the last 24 hours. Date only → that whole day (MYT).
    Date and time → ± WINDOW_MINUTES around it.
    """
    now = now or dt.datetime.now(UTC)
    if not date_text:
        return now - dt.timedelta(hours=24), now, "24h"
    day = dt.datetime.strptime(date_text.strip(), "%Y-%m-%d").date()
    if not time_text:
        start = dt.datetime.combine(day, dt.time(0, 0), MYT)
        return start.astimezone(UTC), (start + dt.timedelta(days=1)).astimezone(UTC), date_text.strip()
    clock = dt.datetime.strptime(time_text.strip().replace(".", ":"), "%H:%M").time()
    centre = dt.datetime.combine(day, clock, MYT).astimezone(UTC)
    delta = dt.timedelta(minutes=WINDOW_MINUTES)
    return centre - delta, centre + delta, "%s %s MYT ±%dm" % (date_text.strip(), time_text.strip(), WINDOW_MINUTES)


def judge(price, candles, source):
    """The verdict for one price against a candle list."""
    if not candles:
        return {"verdict": "UNVERIFIED", "low": None, "high": None, "nearest": None, "gap": None, "gap_pct": None}
    low = min(c["low"] for c in candles)
    high = max(c["high"] for c in candles)
    inside = [c for c in candles if c["low"] <= price <= c["high"]]
    if inside:
        nearest = inside[0]
        return {"verdict": "REAL", "low": low, "high": high, "nearest": nearest, "gap": 0.0, "gap_pct": 0.0}
    gap = (low - price) if price < low else (price - high)
    gap_pct = gap / price
    nearest = min(candles, key=lambda c: min(abs(c["low"] - price), abs(c["high"] - price)))
    verdict = "BORDERLINE" if gap_pct <= TOLERANCE.get(source, 0.01) else "IMPOSSIBLE"
    return {"verdict": verdict, "low": low, "high": high, "nearest": nearest, "gap": gap, "gap_pct": gap_pct}


SCORE = {"REAL": 0, "BORDERLINE": 40, "IMPOSSIBLE": 100, "UNVERIFIED": 50}


def verify(price, date_text=None, time_text=None, side="", now=None):
    """Full report for one claim. Never raises on feed trouble — UNVERIFIED instead."""
    price = float(str(price).replace(",", "").replace("$", ""))
    start, end, label = parse_when(date_text, time_text, now)
    try:
        source, candles = fetch_candles(start, end)
    except NoData as exc:
        source, candles, error = "", [], str(exc)
    else:
        error = None
    j = judge(price, candles, source)
    subject = "%s @ %s" % (("%.2f" % price).rstrip("0").rstrip("."), label)
    return {"product": "signal-verifier", "subject": subject, "text": "", "findings": [],
            "price": price, "side": (side or "").lower(), "window": label,
            "start": start.isoformat(), "end": end.isoformat(),
            "source": source, "candles": len(candles), "error": error,
            "score": SCORE[j["verdict"]], "verdict": j["verdict"],
            "low": j["low"], "high": j["high"], "gap": j["gap"], "gap_pct": j["gap_pct"],
            "nearest": ({"at": j["nearest"]["at"].isoformat(), "low": j["nearest"]["low"], "high": j["nearest"]["high"]}
                        if j["nearest"] else None),
            "reds": 1 if j["verdict"] == "IMPOSSIBLE" else 0, "yellows": 1 if j["verdict"] == "BORDERLINE" else 0,
            "goods": 1 if j["verdict"] == "REAL" else 0}


def parse_claim_line(line):
    """'2431.5 2026-09-14 14:30 buy' → (price, date, time, side). Missing parts are None/''."""
    parts = line.replace(",", "").split()
    if not parts:
        return None
    price, date_text, time_text, side = parts[0], None, None, ""
    for p in parts[1:]:
        if p.count("-") == 2 and date_text is None:
            date_text = p
        elif ":" in p or (p.replace(".", "").isdigit() and time_text is None and date_text is not None and len(p) <= 5):
            time_text = p
        elif p.lower() in ("buy", "sell", "long", "short"):
            side = p.lower()
    return price, date_text, time_text, side
