"""#15 Monte Carlo Challenge Simulator — equity paths against the firm's real rule set.

One path: trades drawn from the trader's win rate and reward-to-risk, each
risking `risk_pct` of the starting balance, `trades_per_day` a day. After every
trade the path is checked against the rule pack (the same packs #14 uses):
daily loss from the day-start balance, max drawdown (static or trailing from
the equity peak), the profit target, the minimum trading days, and the
consistency rule (no single day above X % of total profit). A path ends
PASS, or FAIL with the rule that killed it, or TIMEOUT when the trade budget
runs out. Across N paths that gives the pass probability, where the failures
cluster, and the expected cost-to-funded — fee divided by pass probability.
"""

import random
from collections import Counter

from .sentinel import PACKS

FREE_SIMS = 1000
MAX_TRADES = 200
PERCENTILES = (10, 25, 50, 75, 90)


def simulate_path(rng, winrate, rr, risk_pct, pack, target_pct, trades_per_day, max_trades=MAX_TRADES):
    bal = 100.0                                   # everything in % of the starting balance
    equity, peak, day_start = bal, bal, bal
    path, day_pnl, days = [bal], 0.0, []
    trades = 0
    daily_line_pct, max_pct = pack["daily_pct"], pack["max_pct"]
    for i in range(max_trades):
        trades += 1
        won = rng.random() < winrate
        equity += risk_pct * rr if won else -risk_pct
        day_pnl += risk_pct * rr if won else -risk_pct
        peak = max(peak, equity)
        path.append(round(equity, 3))
        if equity <= day_start * (1 - daily_line_pct / 100):
            return {"result": "fail", "reason": "daily", "trades": trades, "days": len(days) + 1, "path": path, "final": equity}
        base = max(peak, bal) if pack["trailing"] else bal
        line = min(base * (1 - max_pct / 100), bal) if pack["trailing"] else base * (1 - max_pct / 100)
        if equity <= line:
            return {"result": "fail", "reason": "max", "trades": trades, "days": len(days) + 1, "path": path, "final": equity}
        if trades % trades_per_day == 0:
            days.append(day_pnl)
            day_start, day_pnl = equity, 0.0
            if equity >= bal * (1 + target_pct / 100):
                if len(days) < (pack.get("min_days") or 0):
                    continue                                        # target hit early: keep trading the days out
                if pack.get("consistency_pct"):
                    profit_days = [d for d in days if d > 0]
                    total = sum(profit_days)
                    if total and max(profit_days) / total * 100 > pack["consistency_pct"]:
                        return {"result": "fail", "reason": "consistency", "trades": trades, "days": len(days), "path": path, "final": equity}
                return {"result": "pass", "reason": None, "trades": trades, "days": len(days), "path": path, "final": equity}
    return {"result": "timeout", "reason": "timeout", "trades": trades, "days": len(days), "path": path, "final": equity}


def _num(v):
    return float(str(v).replace("%", "").replace("$", "").replace(",", "").strip())


def run(winrate, rr, risk_pct, pack_key="ftmo", target_pct=10.0, fee=500.0, trades_per_day=3, sims=FREE_SIMS, seed=None, cap=FREE_SIMS):
    winrate = _num(winrate) / (100.0 if _num(winrate) > 1 else 1.0)
    rr, risk_pct, target_pct, fee = _num(rr), _num(risk_pct), _num(target_pct), _num(fee)
    trades_per_day = max(1, int(trades_per_day))
    sims = max(100, min(int(sims), cap or int(sims)))
    if not (0 < winrate < 1) or rr <= 0 or not (0 < risk_pct <= 10) or target_pct <= 0:
        raise ValueError("inputs out of range")
    pack = PACKS.get(pack_key) or PACKS["ftmo"]
    rng = random.Random(seed)
    results = [simulate_path(rng, winrate, rr, risk_pct, pack, target_pct, trades_per_day) for _ in range(sims)]
    outcomes = Counter(r["result"] for r in results)
    reasons = Counter(r["reason"] for r in results if r["result"] != "pass")
    passes = [r for r in results if r["result"] == "pass"]
    p_pass = len(passes) / sims
    fail_trades = sorted(r["trades"] for r in results if r["result"] == "fail")
    # fan chart: percentile of equity at each trade index, forward-filled once a path ended
    length = max(len(r["path"]) for r in results)
    bands = {p: [] for p in PERCENTILES}
    for i in range(length):
        col = sorted(r["path"][i] if i < len(r["path"]) else r["path"][-1] for r in results)
        for p in PERCENTILES:
            bands[p].append(col[min(len(col) - 1, int(len(col) * p / 100))])
    expectancy = winrate * rr - (1 - winrate)            # in R
    return {
        "inputs": {"winrate": winrate, "rr": rr, "risk_pct": risk_pct, "pack": pack_key, "pack_name": pack["name"],
                   "target_pct": target_pct, "fee": fee, "trades_per_day": trades_per_day, "sims": sims},
        "p_pass": round(p_pass, 4), "p_fail": round(outcomes["fail"] / sims, 4), "p_timeout": round(outcomes["timeout"] / sims, 4),
        "reasons": {k: round(v / sims, 4) for k, v in reasons.items()},
        "median_trades_to_pass": sorted(r["trades"] for r in passes)[len(passes) // 2] if passes else None,
        "median_days_to_pass": sorted(r["days"] for r in passes)[len(passes) // 2] if passes else None,
        "median_trades_to_fail": fail_trades[len(fail_trades) // 2] if fail_trades else None,
        "expected_attempts": round(1 / p_pass, 2) if p_pass else None,
        "cost_to_funded": round(fee / p_pass, 2) if p_pass else None,
        "expectancy_r": round(expectancy, 3),
        "bands": bands, "length": length,
        "samples": [r["path"] for r in results[:12]],
    }


def verdict(p_pass):
    if p_pass >= 0.5:
        return "good"
    if p_pass >= 0.2:
        return "fair"
    return "poor"


def svg_fan(res, width=720, height=260):
    """An inline SVG: p10–p90 band, p25–p75 band, the median line, and a few sample paths."""
    b, n = res["bands"], res["length"]
    lo = min(min(v) for v in b.values()) - 1
    hi = max(max(v) for v in b.values()) + 1
    for s in res["samples"]:
        lo, hi = min(lo, min(s)), max(hi, max(s))
    pad = 34

    def x(i):
        return pad + (i / max(1, n - 1)) * (width - pad - 10)

    def y(v):
        return height - 20 - (v - lo) / max(1e-9, hi - lo) * (height - 30)

    def poly(vals):
        return " ".join("%.1f,%.1f" % (x(i), y(v)) for i, v in enumerate(vals))

    def band(top, bot):
        pts = [(x(i), y(v)) for i, v in enumerate(top)] + [(x(i), y(v)) for i, v in reversed(list(enumerate(bot)))]
        return " ".join("%.1f,%.1f" % p for p in pts)

    target = 100 * (1 + res["inputs"]["target_pct"] / 100)
    dd = 100 * (1 - PACKS[res["inputs"]["pack"]]["max_pct"] / 100)
    parts = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" style="max-width:100%%;height:auto">' % (width, height),
             '<polygon points="%s" fill="#d4af37" fill-opacity=".12"/>' % band(b[90], b[10]),
             '<polygon points="%s" fill="#d4af37" fill-opacity=".22"/>' % band(b[75], b[25])]
    for s in res["samples"]:
        parts.append('<polyline points="%s" fill="none" stroke="#b7c0ce" stroke-opacity=".35" stroke-width="1"/>' % poly(s))
    parts.append('<polyline points="%s" fill="none" stroke="#f5d76e" stroke-width="2"/>' % poly(b[50]))
    parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#00c46a" stroke-dasharray="4 4"/>' % (x(0), y(target), x(n - 1), y(target)))
    parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#ff4d4f" stroke-dasharray="4 4"/>' % (x(0), y(dd), x(n - 1), y(dd)))
    for v in (dd, 100, target):
        parts.append('<text x="2" y="%.1f" font-size="10" fill="#9aa3b2" font-family="monospace">%g%%</text>' % (y(v) + 3, v))
    parts.append('</svg>')
    return "".join(parts)
