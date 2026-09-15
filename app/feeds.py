"""Live prices from free public endpoints, with a short cache.

Binance ``PAXGUSDT`` is the primary source because it exposes a real bid and
ask, which is what a spread-aware alert needs. Yahoo ``GC=F`` is the fallback:
it has no order book, so the spread is unknown and the alert falls back to the
last price on both sides. Every caller gets the same dict shape either way.
"""

import time

import requests

BINANCE = "https://api.binance.com/api/v3/ticker/bookTicker?symbol=PAXGUSDT"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=1d&interval=1m"
TIMEOUT = 6
CACHE_SECONDS = 15

_cache = {"at": 0.0, "quote": None}


class FeedError(RuntimeError):
    """Every source failed."""


def _binance():
    body = requests.get(BINANCE, timeout=TIMEOUT).json()
    bid, ask = float(body["bidPrice"]), float(body["askPrice"])
    return {"symbol": "XAUUSD", "source": "Binance PAXGUSDT", "bid": bid, "ask": ask,
            "mid": (bid + ask) / 2, "spread": ask - bid, "at": time.time()}


def _yahoo():
    body = requests.get(YAHOO, timeout=TIMEOUT, headers={"User-Agent": "sambangold/1.0"}).json()
    meta = body["chart"]["result"][0]["meta"]
    last = float(meta["regularMarketPrice"])
    return {"symbol": "XAUUSD", "source": "Yahoo GC=F", "bid": last, "ask": last,
            "mid": last, "spread": None, "at": time.time()}


def fetch():
    """Uncached quote from the first source that answers."""
    errors = []
    for source in (_binance, _yahoo):
        try:
            return source()
        except Exception as exc:  # noqa: BLE001 — any failure means try the next source
            errors.append("%s: %s" % (source.__name__.strip("_"), exc))
    raise FeedError("; ".join(errors))


def gold_quote(max_age=CACHE_SECONDS):
    """Cached quote. Raises FeedError only when every source is down."""
    now = time.time()
    if _cache["quote"] is not None and now - _cache["at"] < max_age:
        return _cache["quote"]
    quote = fetch()
    _cache.update(at=now, quote=quote)
    return quote


def clear_cache():
    _cache.update(at=0.0, quote=None)


def spread_bps(quote):
    """Spread in basis points of mid, or None when the source has no book."""
    if quote["spread"] is None or not quote["mid"]:
        return None
    return quote["spread"] / quote["mid"] * 10000


def crossed(direction, level, quote):
    """Spread-aware: a buy-above fires on the ask, a sell-below on the bid.

    That is the price the trader would actually get, so the alert never fires
    on a mid that the market did not offer.
    """
    if direction == "above":
        return quote["ask"] >= level
    return quote["bid"] <= level
