"""#12 Live Gold Broker Comparator — XAUUSD cost per broker, ranked, with the IB's link on the card.

No free feed publishes every broker's live gold spread, so the table is two
layers:

* a **seeded** row per broker — the published typical XAUUSD spread, the
  commission per round-turn lot and the overnight swap per lot, from the
  brokers' own account pages, dated and marked "verify"
* **observed** values — spread and slippage that signed-in users measured on
  their own platform, blended in as the median of the last 30 days when there
  are at least three observations

Cost for a trade = spread + commission + swap × nights, in USD per lot, so
the ranking changes with lot size and holding period. The live spot reference
and its bid/ask on our own feed sit above the table so "wide" has a baseline.
"""

import statistics

# Per lot (100 oz). spread in USD per oz (1 pip = $0.01), commission per round-turn lot,
# swap long/short per lot per night. Published typical values on the broker's
# standard gold account as of 2026-09; every row ends in "verify with the broker".
SEED = {
    "exness":      {"name": "Exness",         "account": "Standard",  "spread": 0.20, "commission": 0.0,  "swap_long": -18.0, "swap_short": 6.0,  "url": "https://www.exness.com/"},
    "hfm":         {"name": "HFM",            "account": "Premium",   "spread": 0.22, "commission": 0.0,  "swap_long": -24.0, "swap_short": 8.0,  "url": "https://www.hfm.com/"},
    "xm":          {"name": "XM",             "account": "Standard",  "spread": 0.30, "commission": 0.0,  "swap_long": -26.0, "swap_short": 9.0,  "url": "https://www.xm.com/"},
    "ic markets":  {"name": "IC Markets",     "account": "Raw",       "spread": 0.10, "commission": 7.0,  "swap_long": -22.0, "swap_short": 7.0,  "url": "https://www.icmarkets.com/"},
    "pepperstone": {"name": "Pepperstone",    "account": "Razor",     "spread": 0.11, "commission": 7.0,  "swap_long": -23.0, "swap_short": 7.5,  "url": "https://pepperstone.com/"},
    "vantage":     {"name": "Vantage",        "account": "Raw ECN",   "spread": 0.12, "commission": 6.0,  "swap_long": -21.0, "swap_short": 6.5,  "url": "https://www.vantagemarkets.com/"},
    "fbs":         {"name": "FBS",            "account": "Standard",  "spread": 0.35, "commission": 0.0,  "swap_long": -25.0, "swap_short": 8.0,  "url": "https://fbs.com/"},
    "octafx":      {"name": "OctaFX",         "account": "MT5",       "spread": 0.28, "commission": 0.0,  "swap_long": 0.0,   "swap_short": 0.0,  "url": "https://www.octafx.com/"},
    "tickmill":    {"name": "Tickmill",       "account": "Raw",       "spread": 0.13, "commission": 6.0,  "swap_long": -20.0, "swap_short": 6.0,  "url": "https://www.tickmill.com/"},
    "fp markets":  {"name": "FP Markets",     "account": "Raw",       "spread": 0.12, "commission": 6.0,  "swap_long": -22.0, "swap_short": 7.0,  "url": "https://www.fpmarkets.com/"},
}
SEED_DATE = "2026-09"
MIN_OBS = 3
CONTRACT_OZ = 100

HOLDINGS = {"intraday": 0, "overnight": 1, "week": 5, "month": 20}


def cost_per_lot(row, lots=1.0, nights=0, side="long"):
    """USD cost of one round-turn for `lots` held `nights` nights."""
    spread = row["spread"] * CONTRACT_OZ * lots
    commission = row["commission"] * lots
    swap = abs(min(0.0, row["swap_long" if side == "long" else "swap_short"])) * nights * lots
    return {"spread": round(spread, 2), "commission": round(commission, 2), "swap": round(swap, 2),
            "total": round(spread + commission + swap, 2)}


def blend(seed, observations):
    """Rows with observed medians folded in when there are enough observations."""
    rows = []
    for key, row in seed.items():
        obs = [o for o in observations if o["broker"] == key]
        r = dict(row, key=key, source="published", n_obs=len(obs), slippage=None)
        if len(obs) >= MIN_OBS:
            r["spread"] = round(statistics.median(o["spread"] for o in obs), 3)
            slips = [o["slippage"] for o in obs if o.get("slippage") is not None]
            r["slippage"] = round(statistics.median(slips), 3) if slips else None
            r["source"] = "observed"
        rows.append(r)
    return rows


def rank(rows, lots=1.0, nights=0, side="long"):
    out = []
    for r in rows:
        c = cost_per_lot(r, lots, nights, side)
        if r.get("slippage"):
            c["slippage"] = round(r["slippage"] * CONTRACT_OZ * lots, 2)
            c["total"] = round(c["total"] + c["slippage"], 2)
        out.append(dict(r, cost=c))
    out.sort(key=lambda r: r["cost"]["total"])
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


def parse_holding(text):
    text = (text or "").strip().lower()
    if not text:
        return 0
    if text in HOLDINGS:
        return HOLDINGS[text]
    try:
        return max(0, int(float(text)))
    except ValueError:
        raise ValueError(text)


def find(key_or_name):
    k = (key_or_name or "").strip().lower()
    for key, row in SEED.items():
        if k == key or k == row["name"].lower() or (k and (k in key or key in k)):
            return key
    return None
