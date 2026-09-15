"""#16 Correlation & Overexposure Monitor — five open trades are often one bet.

No free feed gives rolling correlations across every pair a retail book
holds, so the clustering is structural: every position is decomposed into
its currency legs (EURUSD buy = long EUR, short USD; XAUUSD buy = long XAU,
short USD; XAGUSD sits on the metals factor with gold), the legs are netted,
and the book collapses to a true-risk figure — the largest netted factor
against the gross notional. Two positions are "correlated" when they share a
leg in the same direction. That is the part that kills accounts and it needs
no history to see. Swap and session-spread cost are estimated per position
from typical published values, and both scale with the same concentration.
"""

from collections import defaultdict

CONTRACT = {"XAUUSD": 100, "XAGUSD": 5000}          # oz per lot; every FX pair is 100k units
FACTOR = {"XAU": "METALS", "XAG": "METALS", "USD": "USD", "EUR": "EUR", "GBP": "GBP", "JPY": "JPY", "AUD": "COMMOD-FX",
          "NZD": "COMMOD-FX", "CAD": "COMMOD-FX", "CHF": "CHF", "US30": "INDEX", "NAS100": "INDEX", "SPX500": "INDEX", "BTC": "CRYPTO", "ETH": "CRYPTO"}
# Typical retail spread (pips or $/oz) and overnight swap per lot (USD, long/short) as of 2026-09. Verify with your broker.
COSTS = {
    "EURUSD": (1.0, -6.0, 2.0), "GBPUSD": (1.2, -5.0, 1.0), "USDJPY": (1.0, 8.0, -14.0), "AUDUSD": (1.2, -3.0, 0.5),
    "USDCAD": (1.5, 1.0, -5.0), "USDCHF": (1.5, 9.0, -15.0), "NZDUSD": (1.5, -2.0, 0.0), "EURJPY": (1.6, 4.0, -9.0),
    "GBPJPY": (2.0, 6.0, -12.0), "EURGBP": (1.2, -3.0, 0.5), "XAUUSD": (0.20, -18.0, 6.0), "XAGUSD": (0.03, -8.0, 2.0),
}
PIP = {"JPY": 0.01}
CONCENTRATION_WARN = 0.60     # one factor carrying 60 % of gross is one bet
STACK_WARN = 3                # three positions leaning the same way on one factor


def parse_symbol(sym):
    s = (sym or "").upper().replace("/", "").replace("_", "").replace("-", "")
    if s.endswith((".M", ".C", ".R", ".I")):
        s = s[:-2]
    if s in ("GOLD", "XAU"):
        s = "XAUUSD"
    if s in ("SILVER", "XAG"):
        s = "XAGUSD"
    if len(s) == 6 and s[:3].isalpha() and s[3:].isalpha():
        return s, s[:3], s[3:]
    return s, s, "USD"                                     # an index or crypto: itself vs USD


def parse_positions(text):
    """Lines of 'EURUSD buy 1.0' (comma or newline separated) → positions."""
    out = []
    for raw in (text or "").replace(";", "\n").replace(",", "\n").splitlines():
        parts = raw.strip().split()
        if not parts:
            continue
        if len(parts) < 3:
            raise ValueError(raw.strip())
        sym, base, quote = parse_symbol(parts[0])
        side = parts[1].lower()
        if side in ("b", "long", "l"):
            side = "buy"
        if side in ("s", "short", "sh"):
            side = "sell"
        if side not in ("buy", "sell"):
            raise ValueError(raw.strip())
        try:
            lots = float(parts[2].replace(",", "."))
        except ValueError:
            raise ValueError(raw.strip())
        if lots <= 0:
            raise ValueError(raw.strip())
        out.append({"symbol": sym, "base": base, "quote": quote, "side": side, "lots": lots})
    if not out:
        raise ValueError("empty")
    return out


def notional(pos, gold_price=2400.0):
    if pos["symbol"] == "XAUUSD":
        return pos["lots"] * CONTRACT["XAUUSD"] * gold_price
    if pos["symbol"] == "XAGUSD":
        return pos["lots"] * CONTRACT["XAGUSD"] * gold_price / 80
    return pos["lots"] * 100000.0                           # base-currency units, treated as ~USD-scale


def analyse(positions, balance=None, gold_price=2400.0):
    sign = lambda p: 1 if p["side"] == "buy" else -1
    legs = defaultdict(float)             # currency → signed notional
    factors = defaultdict(float)          # factor → signed notional
    stacks = defaultdict(list)            # factor → positions leaning long on it (sign)
    gross = 0.0
    for p in positions:
        n = notional(p, gold_price)
        p["notional"] = round(n, 2)
        gross += n
        legs[p["base"]] += sign(p) * n
        legs[p["quote"]] -= sign(p) * n
        for cur, s in ((p["base"], sign(p)), (p["quote"], -sign(p))):
            f = FACTOR.get(cur, cur)
            factors[f] += s * n
            stacks[f].append((p["symbol"], s))
    net_by_factor = {f: round(v, 2) for f, v in factors.items()}
    biggest = max(net_by_factor.items(), key=lambda kv: abs(kv[1])) if net_by_factor else ("—", 0.0)
    concentration = abs(biggest[1]) / gross if gross else 0.0
    true_risk = sum(abs(v) for v in factors.values()) / 2      # one side of the netted book
    stacked = {f: [s for s, d in v if d == (1 if net_by_factor[f] > 0 else -1)] for f, v in stacks.items()}
    worst_stack = max(((f, syms) for f, syms in stacked.items()), key=lambda kv: len(kv[1]), default=("—", []))
    flags = []
    if concentration >= CONCENTRATION_WARN and len(positions) > 1:
        flags.append("concentration")
    if len(worst_stack[1]) >= STACK_WARN:
        flags.append("stack")
    if balance and gross / balance > 20:
        flags.append("leverage")
    state = "over" if flags else ("watch" if concentration > 0.5 and len(positions) > 1 else "ok")
    # pairwise structural correlation: +1 share a leg same way, -1 opposite, 0 none
    matrix = []
    for a in positions:
        row = []
        for b in positions:
            c = 0
            for ca, sa in ((a["base"], sign(a)), (a["quote"], -sign(a))):
                for cb, sb in ((b["base"], sign(b)), (b["quote"], -sign(b))):
                    if FACTOR.get(ca, ca) == FACTOR.get(cb, cb):
                        c += sa * sb
            row.append(max(-1, min(1, c)))
        matrix.append(row)
    costs = []
    for p in positions:
        spread, swap_long, swap_short = COSTS.get(p["symbol"], (1.5, -5.0, -5.0))
        pip = PIP.get(p["quote"], 0.0001) if p["symbol"] not in CONTRACT else 1.0
        if p["symbol"] in CONTRACT:
            spread_cost = spread * CONTRACT[p["symbol"]] * p["lots"]
        else:
            spread_cost = spread * pip * 100000 * p["lots"] * (1 / 150 if p["quote"] == "JPY" else 1.0)
        swap = (swap_long if p["side"] == "buy" else swap_short) * p["lots"]
        costs.append({"symbol": p["symbol"], "side": p["side"], "lots": p["lots"], "spread": round(spread_cost, 2),
                      "swap_night": round(swap, 2), "swap_week": round(swap * 5, 2)})
    return {"positions": positions, "gross": round(gross, 2), "true_risk": round(true_risk, 2),
            "factors": dict(sorted(net_by_factor.items(), key=lambda kv: -abs(kv[1]))), "legs": {k: round(v, 2) for k, v in legs.items()},
            "biggest": {"factor": biggest[0], "net": biggest[1]}, "concentration": round(concentration, 3),
            "stack": {"factor": worst_stack[0], "symbols": worst_stack[1]}, "flags": flags, "state": state,
            "matrix": matrix, "costs": costs,
            "spread_total": round(sum(c["spread"] for c in costs), 2), "swap_week_total": round(sum(c["swap_week"] for c in costs), 2),
            "leverage": round(gross / balance, 1) if balance else None}


SAMPLE = "XAUUSD buy 1\nEURUSD buy 1\nGBPUSD buy 0.5\nUSDJPY sell 1\nXAGUSD buy 2"
