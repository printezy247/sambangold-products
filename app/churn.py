"""#11 IB Client Churn & Blow-Up Radar — score a referred client book from its trade log.

One CSV, the client trade log the IB portal already exports: account, close
time, symbol, lots, profit (balance optional). Per client, four signals over a
rolling window, each 0–100:

* volume decay   — lots in the last 30 days against the 30 days before
* dormancy       — days since the last trade against the client's own gap
* martingale     — lot size stepping up after a losing trade
* margin stress  — losing streak and drawdown of the running P&L (against
                   balance when the log has one, else against gross profit)

Blended into a 30-day blow-up / churn probability, then ranked by revenue at
risk (probability × recent lots × rebate rate) so the client worth saving sits
at the top, not the dormant one at 90 %. Each flag names an intervention.
"""

import csv
import datetime as dt
import io
from collections import defaultdict

from .rebate import _norm, _num, _pick

ACCOUNT = ("account", "login", "client", "client_id", "account_id", "trader", "mt4", "mt5")
SYMBOL = ("symbol", "instrument", "pair", "product")
LOTS = ("lots", "volume", "lot", "closed_lots", "size")
PROFIT = ("profit", "pnl", "p&l", "net", "result", "pl")
DATE = ("close_time", "close", "date", "time", "closed", "timestamp", "open_time")
BALANCE = ("balance", "equity")

WINDOW = 30
WEIGHTS = {"decay": 0.30, "dormancy": 0.30, "martingale": 0.20, "stress": 0.20}
FREE_CLIENTS = 10


class InputError(ValueError):
    pass


def _parse_date(v):
    v = (v or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d",
                "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return dt.datetime.strptime(v[:19] if "T" in v else v, fmt).date()
        except ValueError:
            continue
    raise InputError("date not understood: %s" % v)


def parse_log(text):
    """Trades as {account, at, symbol, lots, profit, balance}, sorted by time."""
    text = (text or "").strip().lstrip("﻿")
    if not text:
        raise InputError("empty")
    try:
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = [_norm(h) for h in (reader.fieldnames or [])]
    reader.fieldnames = headers
    acc, date, lots = _pick(headers, ACCOUNT), _pick(headers, DATE), _pick(headers, LOTS)
    sym, profit, bal = _pick(headers, SYMBOL), _pick(headers, PROFIT), _pick(headers, BALANCE)
    if not (acc and date and lots):
        raise InputError("need account, date and lots columns; found: %s" % ", ".join(h for h in headers if h))
    rows = []
    for r in reader:
        if not (r.get(acc) or "").strip():
            continue
        rows.append({"account": r[acc].strip(), "at": _parse_date(r.get(date)), "symbol": (r.get(sym) or "").strip().upper(),
                     "lots": _num(r.get(lots)), "profit": _num(r.get(profit)) if profit else None,
                     "balance": _num(r.get(bal)) if bal and (r.get(bal) or "").strip() else None})
    if not rows:
        raise InputError("no data rows")
    rows.sort(key=lambda r: r["at"])
    return rows


def _clamp(x):
    return max(0, min(100, int(round(x))))


def score_client(trades, as_of):
    """Signals for one client's trades (sorted). Returns a dict with the four signals, probability, flags."""
    recent_from = as_of - dt.timedelta(days=WINDOW)
    prior_from = as_of - dt.timedelta(days=2 * WINDOW)
    recent = [t for t in trades if recent_from < t["at"] <= as_of]
    prior = [t for t in trades if prior_from < t["at"] <= recent_from]
    lots_recent, lots_prior = sum(t["lots"] for t in recent), sum(t["lots"] for t in prior)

    # volume decay: 0 when flat or growing, 100 when the client stopped
    if lots_prior > 0:
        decay = _clamp((1 - lots_recent / lots_prior) * 100)
    else:
        decay = 0 if lots_recent > 0 else 50

    # dormancy: days since last trade vs the client's typical gap
    days = sorted({t["at"] for t in trades})
    gaps = [(b - a).days for a, b in zip(days, days[1:])] or [7]
    typical = max(1, sorted(gaps)[len(gaps) // 2])
    since = (as_of - days[-1]).days
    dormancy = _clamp((since / max(typical * 3, 7)) * 100)

    # martingale: lot size stepping up right after a losing trade
    ups, losses = 0, 0
    if trades and trades[0]["profit"] is not None:
        for a, b in zip(trades, trades[1:]):
            if a["profit"] is not None and a["profit"] < 0:
                losses += 1
                if b["lots"] > a["lots"] * 1.25:
                    ups += 1
    martingale = _clamp((ups / losses) * 100) if losses >= 3 else (0 if losses < 3 else 0)

    # stress: longest losing streak and drawdown of running P&L
    streak = best = 0
    peak = run = 0.0
    dd = 0.0
    for t in trades:
        if t["profit"] is None:
            continue
        streak = streak + 1 if t["profit"] < 0 else 0
        best = max(best, streak)
        run += t["profit"]
        peak = max(peak, run)
        dd = max(dd, peak - run)
    base = next((t["balance"] for t in reversed(trades) if t["balance"]), None)
    if base is None:
        gross = sum(t["profit"] for t in trades if t["profit"] and t["profit"] > 0) or 1.0
        base = gross
    stress = _clamp(min(100, best * 12) * 0.5 + min(100, dd / base * 100) * 0.5) if trades[0]["profit"] is not None else 0

    blended = WEIGHTS["decay"] * decay + WEIGHTS["dormancy"] * dormancy + WEIGHTS["martingale"] * martingale + WEIGHTS["stress"] * stress
    prob = _clamp(0.5 * blended + 0.5 * max(decay, dormancy, martingale, stress))   # one loud signal is enough to matter
    flags = []
    if decay >= 50:
        flags.append("decay")
    if dormancy >= 50:
        flags.append("dormancy")
    if martingale >= 40:
        flags.append("martingale")
    if stress >= 50:
        flags.append("stress")
    return {"decay": decay, "dormancy": dormancy, "martingale": martingale, "stress": stress, "prob": prob,
            "lots_recent": round(lots_recent, 2), "lots_prior": round(lots_prior, 2), "days_since": since,
            "trades": len(trades), "last_at": days[-1].isoformat(), "worst_streak": best, "drawdown": round(dd, 2),
            "flags": flags, "band": "risk" if prob >= 60 else ("watch" if prob >= 30 else "healthy")}


def scan_book(rows, rate=6.0, as_of=None):
    """Every client scored and ranked by revenue at risk."""
    as_of = as_of or max(r["at"] for r in rows)
    by = defaultdict(list)
    for r in rows:
        by[r["account"]].append(r)
    clients = []
    for acc, trades in by.items():
        s = score_client(trades, as_of)
        s["account"] = acc
        s["revenue_recent"] = round(s["lots_recent"] * rate, 2)
        s["at_risk"] = round(max(s["lots_recent"], s["lots_prior"]) * rate * s["prob"] / 100, 2)
        clients.append(s)
    clients.sort(key=lambda c: (-c["at_risk"], -c["prob"]))
    summary = {"clients": len(clients), "risk": sum(1 for c in clients if c["band"] == "risk"),
               "watch": sum(1 for c in clients if c["band"] == "watch"),
               "healthy": sum(1 for c in clients if c["band"] == "healthy"),
               "at_risk": round(sum(c["at_risk"] for c in clients), 2),
               "revenue_recent": round(sum(c["revenue_recent"] for c in clients), 2),
               "as_of": as_of.isoformat(), "rate": rate}
    return {"clients": clients, "summary": summary}


INTERVENTIONS = {
    "decay": ("Volume is falling against the client's own baseline.", "Ask what changed — platform, results, time. A short call beats a promo."),
    "dormancy": ("Quiet for longer than this client's usual gap.", "One personal message, no pitch. Dormant clients answer people, not campaigns."),
    "martingale": ("Lot size steps up after losses.", "Send the risk-per-trade sheet and suggest a fixed-lot week. Blow-up is close."),
    "stress": ("Long losing streak or deep drawdown on the running P&L.", "Check margin level with the broker; suggest a pause before the account is gone."),
}
INTERVENTIONS_MS = {
    "decay": ("Volum jatuh berbanding baseline klien sendiri.", "Tanya apa yang berubah — platform, keputusan, masa. Panggilan pendek lebih baik daripada promo."),
    "dormancy": ("Senyap lebih lama daripada jurang biasa klien ini.", "Satu mesej peribadi, tanpa pitch. Klien dorman jawab manusia, bukan kempen."),
    "martingale": ("Saiz lot naik selepas rugi.", "Hantar helaian risiko setiap trade dan cadangkan seminggu lot tetap. Blow-up sudah dekat."),
    "stress": ("Streak rugi panjang atau drawdown dalam pada P&L berjalan.", "Semak tahap margin dengan broker; cadangkan rehat sebelum akaun lenyap."),
}


def interventions(lang="ms"):
    return INTERVENTIONS_MS if lang == "ms" else INTERVENTIONS


def _days_ago(n):
    return (dt.date(2026, 9, 14) - dt.timedelta(days=n)).isoformat()


def sample_log():
    """A five-client book: one healthy, one decaying, one dormant, one martingale, one bleeding."""
    rows = ["account,close_time,symbol,lots,profit,balance"]
    for d in range(58, 0, -3):                                  # healthy: steady 1 lot every 3 days
        rows.append("2001,%s,XAUUSD,1.0,%s,5000" % (_days_ago(d), 40 if d % 2 else -25))
    for d in range(58, 0, -2):                                  # decay: heavy before, thin now
        lots = 2.0 if d > 30 else 0.3
        rows.append("2002,%s,XAUUSD,%s,%s,8000" % (_days_ago(d), lots, 30 if d % 3 else -20))
    for d in range(58, 24, -2):                                 # dormant: stopped 24 days ago
        rows.append("2003,%s,EURUSD,0.5,%s,3000" % (_days_ago(d), 10 if d % 2 else -8))
    lots = 0.5
    for i, d in enumerate(range(20, 0, -1)):                     # martingale: doubles after each loss
        profit = -30 * lots if i % 3 != 2 else 20 * lots
        rows.append("2004,%s,XAUUSD,%s,%s,2000" % (_days_ago(d), round(lots, 2), round(profit, 2)))
        lots = round(lots * 2, 2) if profit < 0 else 0.5
    bal = 4000
    for d in range(30, 0, -1):                                   # stress: nine losses in a row
        profit = -120 if d > 21 else (60 if d % 2 else -50)
        bal += profit
        rows.append("2005,%s,XAUUSD,1.0,%s,%s" % (_days_ago(d), profit, bal))
    return "\n".join(rows) + "\n"
