"""#14 Drawdown Sentinel — distance to every prop-firm rule line, and a warning before it is crossed.

There is no free way for a web app to read an MT4/MT5 account, so the
account reports to us: a signed-in trader posts equity from the dashboard or
the bot, or points an EA / phone shortcut at a per-account ping URL. Every
report is scored against the firm's rule pack — daily loss, max drawdown
(static or trailing from the equity peak), max lot, minimum days — and the
state moves between ok / warn / breach. A warn is the save; a breach is the
post-mortem.
"""

import datetime as dt

# Published challenge rules as of 2026-09. Firms change these; the pack is a
# starting point the trader confirms against the firm's own page.
PACKS = {
    "ftmo":        {"name": "FTMO",           "daily_pct": 5.0,  "max_pct": 10.0, "trailing": False, "min_days": 4,  "max_lot": None, "consistency_pct": None, "news": False},
    "fundednext":  {"name": "FundedNext",     "daily_pct": 5.0,  "max_pct": 10.0, "trailing": False, "min_days": 5,  "max_lot": None, "consistency_pct": None, "news": False},
    "the5ers":     {"name": "The5ers",        "daily_pct": 5.0,  "max_pct": 10.0, "trailing": False, "min_days": 3,  "max_lot": None, "consistency_pct": None, "news": False},
    "fundingpips": {"name": "FundingPips",    "daily_pct": 5.0,  "max_pct": 10.0, "trailing": False, "min_days": 3,  "max_lot": None, "consistency_pct": None, "news": True},
    "myfundedfx":  {"name": "MyFundedFX",     "daily_pct": 5.0,  "max_pct": 8.0,  "trailing": True,  "min_days": 5,  "max_lot": None, "consistency_pct": 40.0, "news": True},
    "e8":          {"name": "E8 Markets",     "daily_pct": 5.0,  "max_pct": 8.0,  "trailing": True,  "min_days": 0,  "max_lot": None, "consistency_pct": None, "news": False},
    "custom":      {"name": "Custom",         "daily_pct": 5.0,  "max_pct": 10.0, "trailing": False, "min_days": 0,  "max_lot": None, "consistency_pct": None, "news": False},
}
PACK_DATE = "2026-09"
WARN_ROOM = 0.30      # warn when less than 30 % of the room to a line is left
FREE_ACCOUNTS = 1


def find_pack(name):
    k = (name or "").strip().lower().replace(" ", "")
    for key, p in PACKS.items():
        if k == key or k == p["name"].lower().replace(" ", "") or (len(k) >= 3 and key.startswith(k)):
            return key
    return None


def custom_pack(daily_pct, max_pct, trailing=False, min_days=0, max_lot=None):
    p = dict(PACKS["custom"])
    p.update({"daily_pct": float(daily_pct), "max_pct": float(max_pct), "trailing": bool(trailing),
              "min_days": int(min_days or 0), "max_lot": float(max_lot) if max_lot else None})
    return p


def evaluate(acc, pack):
    """Rule lines for one account snapshot.

    acc: initial_balance, day_start_balance, equity, peak_equity, open_lots, started (ISO date), day (ISO date)
    Returns rules (each with line, room, room_pct, state) and the overall state.
    """
    eq = acc["equity"]
    rules = []

    daily_line = acc["day_start_balance"] * (1 - pack["daily_pct"] / 100)
    daily_room = eq - daily_line
    rules.append(_rule("daily", daily_line, daily_room, acc["day_start_balance"] * pack["daily_pct"] / 100))

    base = max(acc["peak_equity"], acc["initial_balance"]) if pack["trailing"] else acc["initial_balance"]
    max_line = base * (1 - pack["max_pct"] / 100)
    if pack["trailing"]:
        max_line = min(max_line, acc["initial_balance"])          # trailing stops once it reaches the start balance
    rules.append(_rule("max", max_line, eq - max_line, base * pack["max_pct"] / 100))

    if pack.get("max_lot"):
        lots = acc.get("open_lots") or 0.0
        rules.append(_rule("lot", pack["max_lot"], pack["max_lot"] - lots, pack["max_lot"]))

    days_done = None
    if pack.get("min_days") and acc.get("started"):
        started = dt.date.fromisoformat(acc["started"])
        today = dt.date.fromisoformat(acc["day"]) if acc.get("day") else dt.date.today()
        days_done = max(0, (today - started).days)
        rules.append({"key": "days", "line": pack["min_days"], "room": pack["min_days"] - days_done, "room_pct": None,
                      "state": "ok" if days_done >= pack["min_days"] else "info"})

    states = [r["state"] for r in rules]
    overall = "breach" if "breach" in states else ("warn" if "warn" in states else "ok")
    return {"rules": rules, "state": overall, "equity": eq, "days_done": days_done}


def _rule(key, line, room, full):
    pct = (room / full) if full else 1.0
    state = "breach" if room < 0 else ("warn" if pct < WARN_ROOM else "ok")
    return {"key": key, "line": round(line, 2), "room": round(room, 2), "room_pct": round(max(0.0, min(1.0, pct)), 3), "state": state}
