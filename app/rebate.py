"""#10 Rebate Reconciliation Auditor — recompute what the broker owed, diff it against what was paid.

Inputs are two CSVs the IB already has: the broker's rebate statement (what
was paid, per account and symbol) and the client trade log (what was traded).
Headers are matched loosely — ``account``/``login``/``client``, ``symbol``/
``instrument``/``pair``, ``lots``/``volume``, ``rebate``/``paid``/``commission``
— so exports from MT4/MT5 partner portals load without editing.

The rate card is the IB agreement: a default rate per lot, per-symbol
overrides (``XAUUSD=8``) and optional volume tiers (``100:7.5,500:8``: from
100 lots the rate is 7.5, from 500 it is 8, applied on the account's month
total). Every finding names the account, the symbol, the arithmetic and the
amount, which is what a dispute email needs.
"""

import csv
import io
from collections import defaultdict

from .goldcal import simple_pdf

ACCOUNT = ("account", "login", "client", "client_id", "account_id", "trader", "mt4", "mt5")
SYMBOL = ("symbol", "instrument", "pair", "product")
LOTS = ("lots", "volume", "lot", "closed_lots", "traded_lots", "size")
PAID = ("rebate", "paid", "commission", "amount", "payout", "ib_commission", "rebate_paid")
TOLERANCE = 0.01   # dollars; below this a difference is rounding, not a finding

KINDS = ("shortfall", "missing_account", "silent_rate_change", "excluded_symbol", "overpaid", "ok")


class InputError(ValueError):
    pass


def _norm(h):
    return (h or "").strip().lower().replace(" ", "_").replace("-", "_").replace("#", "")


def _pick(headers, wanted):
    for w in wanted:
        for h in headers:
            if h == w or h.startswith(w):
                return h
    return None


def _num(v):
    v = (v or "").strip().replace(",", "").replace("$", "").replace("USD", "").strip()
    if v in ("", "-"):
        return 0.0
    return float(v)


def parse_csv(text, need_paid=False):
    """Rows of {account, symbol, lots, paid} from loosely-headed CSV text."""
    text = (text or "").strip().lstrip("﻿")
    if not text:
        raise InputError("empty")
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = [_norm(h) for h in (reader.fieldnames or [])]
    reader.fieldnames = headers
    acc, sym, lots, paid = _pick(headers, ACCOUNT), _pick(headers, SYMBOL), _pick(headers, LOTS), _pick(headers, PAID)
    if not acc or not lots:
        raise InputError("need account and lots columns; found: %s" % ", ".join(h for h in headers if h))
    if need_paid and not paid:
        raise InputError("statement needs a rebate/paid column; found: %s" % ", ".join(h for h in headers if h))
    rows = []
    for r in reader:
        if not (r.get(acc) or "").strip():
            continue
        try:
            rows.append({"account": r[acc].strip(), "symbol": (r.get(sym) or "ALL").strip().upper() if sym else "ALL",
                         "lots": _num(r.get(lots)), "paid": _num(r.get(paid)) if paid else 0.0})
        except ValueError as exc:
            raise InputError("bad number in row for account %s: %s" % (r[acc], exc))
    if not rows:
        raise InputError("no data rows")
    return rows


def parse_rates(default, overrides="", tiers=""):
    """(default_rate, {SYMBOL: rate}, [(from_lots, rate), ...] ascending)."""
    try:
        default = float(str(default).replace("$", "").strip() or 0)
    except ValueError:
        raise InputError("default rate must be a number")
    per = {}
    for chunk in (overrides or "").replace(";", ",").split(","):
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            try:
                per[k.strip().upper()] = float(v.strip().replace("$", ""))
            except ValueError:
                raise InputError("bad symbol rate: %s" % chunk.strip())
    tier_list = []
    for chunk in (tiers or "").replace(";", ",").split(","):
        if ":" in chunk:
            k, v = chunk.split(":", 1)
            try:
                tier_list.append((float(k.strip()), float(v.strip().replace("$", ""))))
            except ValueError:
                raise InputError("bad tier: %s" % chunk.strip())
    tier_list.sort()
    if default <= 0 and not per:
        raise InputError("rate card is empty")
    return default, per, tier_list


def _rate_for(symbol, account_lots, default, per, tiers):
    rate = per.get(symbol, default)
    for from_lots, tier_rate in tiers:
        if account_lots >= from_lots:
            rate = tier_rate if symbol not in per else rate
    return rate


def _group(rows):
    g = defaultdict(lambda: {"lots": 0.0, "paid": 0.0})
    for r in rows:
        key = (r["account"], r["symbol"])
        g[key]["lots"] += r["lots"]
        g[key]["paid"] += r["paid"]
    return g


def reconcile(statement_rows, log_rows, default, per=None, tiers=None):
    """Per (account, symbol) diff between expected (log × rate) and paid (statement)."""
    per, tiers = per or {}, tiers or []
    stmt, log = _group(statement_rows), _group(log_rows)
    per_account_lots = defaultdict(float)
    for (acc, _), v in log.items():
        per_account_lots[acc] += v["lots"]
    findings = []
    for (acc, sym), v in sorted(log.items()):
        rate = _rate_for(sym, per_account_lots[acc], default, per, tiers)
        expected = v["lots"] * rate
        paid_row = stmt.get((acc, sym))
        paid = paid_row["paid"] if paid_row else 0.0
        paid_lots = paid_row["lots"] if paid_row else 0.0
        diff = expected - paid
        if acc not in {a for a, _ in stmt}:
            kind = "missing_account"
        elif paid_row is None or (paid == 0 and expected > 0):
            kind = "excluded_symbol"
        elif abs(diff) <= TOLERANCE:
            kind = "ok"
        elif paid_lots and abs(paid_lots - v["lots"]) <= 0.01 and paid / paid_lots < rate - 1e-9:
            kind = "silent_rate_change"
        elif diff > 0:
            kind = "shortfall"
        else:
            kind = "overpaid"
        findings.append({"account": acc, "symbol": sym, "lots": round(v["lots"], 2), "rate": rate,
                         "expected": round(expected, 2), "paid": round(paid, 2), "paid_lots": round(paid_lots, 2),
                         "implied_rate": round(paid / paid_lots, 4) if paid_lots else None,
                         "diff": round(diff, 2), "kind": kind})
    # paid for accounts that never traded — not owed, but worth a line
    for (acc, sym), v in sorted(stmt.items()):
        if (acc, sym) not in log and v["paid"]:
            findings.append({"account": acc, "symbol": sym, "lots": 0.0, "rate": None, "expected": 0.0,
                             "paid": round(v["paid"], 2), "paid_lots": round(v["lots"], 2), "implied_rate": None,
                             "diff": round(-v["paid"], 2), "kind": "overpaid"})
    order = {k: i for i, k in enumerate(KINDS)}
    findings.sort(key=lambda f: (order[f["kind"]], -abs(f["diff"])))
    summary = {
        "accounts": len({f["account"] for f in findings}),
        "lines": len(findings),
        "expected": round(sum(f["expected"] for f in findings), 2),
        "paid": round(sum(f["paid"] for f in findings), 2),
        "shortfall": round(sum(f["diff"] for f in findings if f["diff"] > TOLERANCE), 2),
        "overpaid": round(-sum(f["diff"] for f in findings if f["diff"] < -TOLERANCE), 2),
        "by_kind": {k: sum(1 for f in findings if f["kind"] == k) for k in KINDS},
        "flagged": sum(1 for f in findings if f["kind"] not in ("ok", "overpaid")),
    }
    return {"findings": findings, "summary": summary}


def sort_findings(findings, key="diff", desc=True):
    if key not in ("account", "symbol", "lots", "expected", "paid", "diff", "kind"):
        key = "diff"
    return sorted(findings, key=lambda f: (f[key] is None, f[key]), reverse=desc)


def dispute_pdf(run, brand="SAMBANGGOLD"):
    """One page of summary, then the flagged lines with the arithmetic shown."""
    s = run["summary"]
    head = ["%s — IB rebate dispute: %s, %s" % (brand, run.get("broker") or "broker", run.get("period") or "period"), "",
            "Rate card: default $%s/lot%s%s" % (run["rate"], ("  overrides " + run["overrides"]) if run.get("overrides") else "",
                                                ("  tiers " + run["tiers"]) if run.get("tiers") else ""),
            "", "Expected  $%s" % format(s["expected"], ",.2f"), "Paid      $%s" % format(s["paid"], ",.2f"),
            "Shortfall $%s  across %d line(s) on %d account(s)" % (format(s["shortfall"], ",.2f"), s["flagged"], s["accounts"]), "",
            "Findings: %d shortfall, %d missing account, %d silent rate change, %d excluded symbol" % (
                s["by_kind"]["shortfall"], s["by_kind"]["missing_account"], s["by_kind"]["silent_rate_change"], s["by_kind"]["excluded_symbol"]),
            "", "Please review the lines on the following pages and remit the shortfall or explain the difference.",
            "", "Educational research only. Not legal or financial advice."]
    pages = [head]
    lines = []
    for f in run["findings"]:
        if f["kind"] in ("ok", "overpaid"):
            continue
        lines.append("%-14s %-9s %8.2f lots x $%-6s = $%9s  paid $%9s  diff $%9s  [%s]" % (
            f["account"][:14], f["symbol"][:9], f["lots"], f["rate"], format(f["expected"], ",.2f"),
            format(f["paid"], ",.2f"), format(f["diff"], ",.2f"), f["kind"].replace("_", " ")))
    for i in range(0, len(lines), 45):
        pages.append(["Flagged lines (%d-%d of %d)" % (i + 1, min(i + 45, len(lines)), len(lines)), ""] + lines[i:i + 45])
    if len(pages) == 1:
        pages.append(["No flagged lines. Every account was paid in full at the agreed rate."])
    return simple_pdf(pages)


SAMPLE_STATEMENT = """account,symbol,lots,rebate
1001,XAUUSD,42.5,340.00
1001,EURUSD,10.0,60.00
1002,XAUUSD,18.0,126.00
1004,XAUUSD,5.0,40.00
"""
SAMPLE_LOG = """login,instrument,volume
1001,XAUUSD,42.5
1001,EURUSD,10.0
1001,GBPUSD,4.0
1002,XAUUSD,18.0
1003,XAUUSD,12.0
"""
SAMPLE_RATE = "6"
SAMPLE_OVERRIDES = "XAUUSD=8"
