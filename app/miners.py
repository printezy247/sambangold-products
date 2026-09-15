"""#18 Miner–Bullion Divergence Screener.

Six months of daily closes from Yahoo Finance for a fixed universe of gold
miners, royalty names and the two ETFs, plus GC=F as the bullion reference.
For each name: beta to gold over the window, beta and correlation over the
last 20 sessions, and the residual — how far the name moved beyond what its
beta and gold's move explain. A large residual is a question, not a signal.

AISC (all-in sustaining cost) is quarterly and hand-maintained; each row
carries the disclosure period. Earnings dates are approximate windows from
the companies' usual cadence, flagged when within 14 days.
"""

import datetime as dt
import math
import statistics
import time

import requests

TIMEOUT = 8
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/%s?range=6mo&interval=1d"
GOLD = "GC=F"
CACHE_SECONDS = 3600
_cache = {"at": 0.0, "hist": None}

AISC_AS_OF = "Q2 2026"   # approximate, from each company's last quarterly report; verify before sizing
# ticker: name, kind, AISC USD/oz (None for ETFs and royalty companies, which carry no mine cost), approx next earnings
UNIVERSE = [
    {"ticker": "GDX", "name": "VanEck Gold Miners ETF", "kind": "etf", "aisc": None, "earnings": None},
    {"ticker": "GDXJ", "name": "VanEck Junior Gold Miners ETF", "kind": "etf", "aisc": None, "earnings": None},
    {"ticker": "NEM", "name": "Newmont", "kind": "major", "aisc": 1650, "earnings": "2026-10-22"},
    {"ticker": "B", "name": "Barrick Mining", "kind": "major", "aisc": 1500, "earnings": "2026-11-05"},
    {"ticker": "AEM", "name": "Agnico Eagle", "kind": "major", "aisc": 1300, "earnings": "2026-10-28"},
    {"ticker": "KGC", "name": "Kinross Gold", "kind": "major", "aisc": 1350, "earnings": "2026-11-04"},
    {"ticker": "AU", "name": "AngloGold Ashanti", "kind": "major", "aisc": 1700, "earnings": "2026-11-06"},
    {"ticker": "GFI", "name": "Gold Fields", "kind": "major", "aisc": 1800, "earnings": "2026-11-12"},
    {"ticker": "HMY", "name": "Harmony Gold", "kind": "mid", "aisc": 1850, "earnings": "2026-11-10"},
    {"ticker": "AGI", "name": "Alamos Gold", "kind": "mid", "aisc": 1350, "earnings": "2026-10-28"},
    {"ticker": "BTG", "name": "B2Gold", "kind": "mid", "aisc": 1550, "earnings": "2026-11-05"},
    {"ticker": "FNV", "name": "Franco-Nevada", "kind": "royalty", "aisc": None, "earnings": "2026-11-05"},
    {"ticker": "WPM", "name": "Wheaton Precious Metals", "kind": "royalty", "aisc": None, "earnings": "2026-11-05"},
    {"ticker": "RGLD", "name": "Royal Gold", "kind": "royalty", "aisc": None, "earnings": "2026-11-04"},
]
BY_TICKER = {u["ticker"]: u for u in UNIVERSE}
SHORT = 20           # sessions for the recent beta / correlation / residual
RESIDUAL_WARN = 5.0  # % beyond beta-explained move
CORR_WARN = 0.3      # 20-session correlation below this: decoupled
MARGIN_WARN = 20.0   # % AISC margin below this: squeeze
EARNINGS_DAYS = 14


class FeedError(RuntimeError):
    pass


def _closes(symbol):
    body = requests.get(YAHOO_CHART % symbol, timeout=TIMEOUT, headers={"User-Agent": "sambangold/1.0"}).json()
    result = body["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    return [(int(ts), float(c)) for ts, c in zip(result["timestamp"], closes) if c is not None]


def fetch_history():
    """{symbol: [(ts, close), ...]} for the universe plus gold; a dead ticker is dropped, dead gold raises."""
    hist, errors = {}, []
    for sym in [GOLD] + [u["ticker"] for u in UNIVERSE]:
        try:
            hist[sym] = _closes(sym)
        except Exception as exc:  # noqa: BLE001 — one dead ticker must not hide the screen
            errors.append("%s: %s" % (sym, str(exc)[:50]))
    if not hist.get(GOLD):
        raise FeedError("; ".join(errors) or "gold history empty")
    hist["errors"] = errors
    return hist


def history(max_age=CACHE_SECONDS):
    now = time.time()
    if _cache["hist"] is not None and now - _cache["at"] < max_age:
        return _cache["hist"]
    hist = fetch_history()
    _cache.update(at=now, hist=hist)
    return hist


def clear_cache():
    _cache.update(at=0.0, hist=None)


# --- maths --------------------------------------------------------------- #

def _align(a, b):
    """Closes on the days both series have, keyed to the calendar day."""
    day = lambda ts: ts // 86400
    bd = {day(ts): c for ts, c in b}
    return [(ts, ca, bd[day(ts)]) for ts, ca in a if day(ts) in bd]


def _returns(closes):
    return [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0 and closes[i] > 0]


def beta(x, y):
    """Slope of y on x, and the correlation; None when there is not enough to say."""
    if len(x) < 5 or len(x) != len(y):
        return None, None
    vx = statistics.pvariance(x)
    if vx == 0:
        return None, None
    mx, my = statistics.fmean(x), statistics.fmean(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y)) / len(x)
    vy = statistics.pvariance(y)
    corr = cov / math.sqrt(vx * vy) if vy > 0 else None
    return round(cov / vx, 2), (round(corr, 2) if corr is not None else None)


def analyse_name(u, series, gold, today=None):
    rows = _align(series, gold)
    if len(rows) < SHORT + 5:
        return None
    px = [r[1] for r in rows]
    gx = [r[2] for r in rows]
    rp, rg = _returns(px), _returns(gx)
    b_long, c_long = beta(rg, rp)
    b_short, c_short = beta(rg[-SHORT:], rp[-SHORT:])
    ret_20 = (px[-1] / px[-SHORT - 1] - 1) * 100
    gold_20 = (gx[-1] / gx[-SHORT - 1] - 1) * 100
    explained = (b_long or 0) * gold_20
    residual = ret_20 - explained
    ret_all = (px[-1] / px[0] - 1) * 100
    gold_all = (gx[-1] / gx[0] - 1) * 100
    spot = gx[-1]
    out = {"ticker": u["ticker"], "name": u["name"], "kind": u["kind"], "price": round(px[-1], 2), "spot": round(spot, 2),
           "beta": b_long, "corr": c_long, "beta_20": b_short, "corr_20": c_short,
           "ret_20": round(ret_20, 1), "gold_20": round(gold_20, 1), "explained": round(explained, 1), "residual": round(residual, 1),
           "ret_all": round(ret_all, 1), "gold_all": round(gold_all, 1), "sessions": len(px),
           "aisc": u["aisc"], "aisc_as_of": AISC_AS_OF, "margin": None, "margin_pct": None,
           "earnings": u["earnings"], "earnings_in": None, "flags": []}
    if u["aisc"]:
        out["margin"] = round(spot - u["aisc"])
        out["margin_pct"] = round((spot - u["aisc"]) / spot * 100, 1)
        if out["margin_pct"] < MARGIN_WARN:
            out["flags"].append("squeeze")
    if c_short is not None and c_short < CORR_WARN:
        out["flags"].append("decoupled")
    if residual <= -RESIDUAL_WARN:
        out["flags"].append("lagging")
    elif residual >= RESIDUAL_WARN:
        out["flags"].append("leading")
    if u["earnings"]:
        today = today or dt.date.today()
        days = (dt.date.fromisoformat(u["earnings"]) - today).days
        out["earnings_in"] = days
        if 0 <= days <= EARNINGS_DAYS:
            out["flags"].append("earnings")
    out["chart"] = [(r[0], round(r[1] / px[0] * 100, 2), round(r[2] / gx[0] * 100, 2)) for r in rows]
    return out


def screen(hist=None, today=None):
    hist = hist or history()
    gold = hist[GOLD]
    rows = []
    for u in UNIVERSE:
        series = hist.get(u["ticker"])
        r = analyse_name(u, series, gold, today) if series else None
        if r:
            rows.append(r)
    rows.sort(key=lambda r: -abs(r["residual"]))
    return {"rows": rows, "spot": round(gold[-1][1], 2), "as_of": gold[-1][0], "errors": hist.get("errors", []),
            "aisc_as_of": AISC_AS_OF, "week": week_key(today)}


def week_key(today=None):
    today = today or dt.date.today()
    y, w, _ = today.isocalendar()
    return "%d-W%02d" % (y, w)


def sort_rows(rows, key):
    keys = {"residual": lambda r: -abs(r["residual"]), "beta": lambda r: -(r["beta"] or 0), "corr": lambda r: (r["corr_20"] if r["corr_20"] is not None else 9),
            "margin": lambda r: (r["margin_pct"] if r["margin_pct"] is not None else 999), "ret": lambda r: -r["ret_20"],
            "ticker": lambda r: r["ticker"], "earnings": lambda r: (r["earnings_in"] if r["earnings_in"] is not None else 9999)}
    return sorted(rows, key=keys.get(key, keys["residual"]))
