"""Pure math behind #3 Prop Firm Challenge Calculator and #8 IB Revenue Calculator.

Nothing here touches Flask or the network: the bot command, the dashboard page
and the tests all call these functions with plain numbers and get plain dicts
back. Every assumption is a named parameter with a default, so both surfaces
can print it next to the answer instead of hiding it.
"""

import re


class InputError(ValueError):
    """A user-supplied number that cannot be turned into an answer."""


def _number(value, name, lo=None, hi=None):
    try:
        number = float(str(value).replace(",", "").replace("$", "").replace("%", ""))
    except (TypeError, ValueError):
        raise InputError("%s must be a number, got %r" % (name, value))
    if lo is not None and number < lo:
        raise InputError("%s must be at least %g" % (name, lo))
    if hi is not None and number > hi:
        raise InputError("%s must be at most %g" % (name, hi))
    return number


# --------------------------------------------------------------------------- #
# #3 — Prop firm challenge
# --------------------------------------------------------------------------- #

def prop_ev(fee, size, pass_pct, profit_target_pct=8.0, split_pct=80.0, resets=0, reset_fee=None):
    """Expected value of paying a challenge fee.

    The first payout a funded trader can bank is the profit target times the
    profit split; multiplying that by the pass probability and subtracting what
    was paid to attempt gives the EV. Breakeven is the pass rate at which EV is
    zero — usually the more honest number to lead with.
    """
    fee = _number(fee, "fee", lo=0)
    size = _number(size, "account size", lo=1)
    pass_rate = _number(pass_pct, "pass rate", lo=0, hi=100) / 100.0
    target = _number(profit_target_pct, "profit target", lo=0, hi=100) / 100.0
    split = _number(split_pct, "profit split", lo=0, hi=100) / 100.0
    resets = int(_number(resets, "resets", lo=0))
    reset_fee = fee if reset_fee is None else _number(reset_fee, "reset fee", lo=0)

    total_cost = fee + resets * reset_fee
    first_payout = size * target * split
    ev = pass_rate * first_payout - total_cost
    breakeven = total_cost / first_payout if first_payout else float("inf")

    return {
        "fee": fee,
        "size": size,
        "pass_rate": pass_rate,
        "profit_target": target,
        "split": split,
        "resets": resets,
        "total_cost": total_cost,
        "first_payout": first_payout,
        "ev": ev,
        "roi": ev / total_cost if total_cost else float("inf"),
        "breakeven_pass_rate": breakeven,
        "verdict": "positive" if ev > 0 else ("breakeven" if ev == 0 else "negative"),
    }


# Rules that actually fail people, and the phrasing they hide behind.
# (flag, label, pattern, why it matters)
TC_RULES = (
    ("red", "Trailing drawdown",
     r"trailing (max(imum)?\s+)?drawdown|drawdown (that )?trails",
     "The floor rises with your equity high, so an early win shrinks your room."),
    ("red", "Consistency rule",
     r"consistency( rule)?|no single (trading )?day (may|can|shall) (exceed|account for)",
     "One good day can disqualify a pass; profits must be spread evenly."),
    ("red", "Balance-based daily loss",
     r"daily (loss|drawdown)[^.]{0,60}(balance|equity)[^.]{0,40}(highest|high|peak|start)",
     "Measured from the day's peak, not the open, so open profit counts against you."),
    ("red", "Fee is not refunded",
     r"non[- ]?refundable|fee(s)? (is|are) not refund",
     "You are paying for a lottery ticket, not a deposit."),
    ("yellow", "No news trading",
     r"(news|high[- ]impact) (event|trading|release)[^.]{0,40}(prohibit|not (be )?(allow|permit)|restrict|ban)",
     "Trades around scheduled releases can void a pass after the fact."),
    ("yellow", "No weekend holding",
     r"(weekend|friday close)[^.]{0,40}(close|flat|not (be )?(allow|permit)|prohibit)"
     r"|(close|flat)[^.]{0,40}(weekend|friday close)",
     "Swing setups must be flattened every Friday."),
    ("yellow", "Minimum trading days",
     r"minimum (of )?\d+ (trading )?days",
     "A fast pass is held back until the day count is met."),
    ("yellow", "Time limit",
     r"(within|in) \d+ (calendar |trading )?days|time limit",
     "The clock, not your edge, decides the attempt."),
    ("yellow", "Copy or hedge trading banned",
     r"(copy|mirror|hedg)[a-z]* (trading|positions?)[^.]{0,40}(prohibit|not (be )?(allow|permit)|ban)",
     "Common risk tools are grounds for termination."),
    ("yellow", "Firm may change rules",
     r"(reserve|reserves) the right to (change|modify|amend|alter)",
     "What you signed up for is not what you will be held to."),
    ("yellow", "Lot or position limits",
     r"(max(imum)?|limit)[^.]{0,20}(lot|position) size",
     "Caps your scaling once you are funded."),
)


def scan_terms(text):
    """Red/yellow flags found in pasted challenge terms, most severe first."""
    text = text or ""
    found = []
    for flag, label, pattern, why in TC_RULES:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 60)
            snippet = " ".join(text[start:match.end() + 60].split())
            found.append({"flag": flag, "label": label, "why": why, "snippet": snippet})
    reds = sum(1 for f in found if f["flag"] == "red")
    yellows = len(found) - reds
    return {
        "flags": sorted(found, key=lambda f: f["flag"] != "red"),
        "reds": reds,
        "yellows": yellows,
        "chars": len(text),
        "grade": "red" if reds else ("yellow" if yellows else "green"),
    }


# --------------------------------------------------------------------------- #
# #8 — IB revenue
# --------------------------------------------------------------------------- #

def ib_revenue(lots, rate, clients=1, compliance_cost=0.0, clawback_pct=0.0,
               payout_threshold=0.0, hold_days=30, months=12):
    """Net monthly IB revenue and the month-by-month payout timeline.

    Gross is lots per client per month times the per-lot rebate. Clawback and a
    fixed compliance cost come off the top. A payout threshold plus a hold
    period decide when the first cash actually lands, which is the number
    brokers never quote.
    """
    lots = _number(lots, "lots", lo=0)
    rate = _number(rate, "rate per lot", lo=0)
    clients = int(_number(clients, "clients", lo=1))
    compliance_cost = _number(compliance_cost, "compliance cost", lo=0)
    clawback = _number(clawback_pct, "clawback", lo=0, hi=100) / 100.0
    threshold = _number(payout_threshold, "payout threshold", lo=0)
    hold_days = int(_number(hold_days, "hold days", lo=0))
    months = int(_number(months, "months", lo=1, hi=60))

    gross = lots * clients * rate
    clawed = gross * clawback
    net = gross - clawed - compliance_cost

    timeline = []
    accrued = 0.0
    paid_total = 0.0
    first_paid_month = None
    for month in range(1, months + 1):
        accrued += net
        paid = 0.0
        if accrued >= threshold and accrued > 0:
            paid = accrued
            accrued = 0.0
            paid_total += paid
            if first_paid_month is None:
                first_paid_month = month
        timeline.append({"month": month, "earned": net, "paid": paid,
                         "cumulative": paid_total, "held": accrued})

    return {
        "lots": lots,
        "rate": rate,
        "clients": clients,
        "gross": gross,
        "clawback": clawed,
        "compliance_cost": compliance_cost,
        "net": net,
        "annual": net * 12,
        "margin": net / gross if gross else 0.0,
        "payout_threshold": threshold,
        "hold_days": hold_days,
        "first_cash_days": (first_paid_month * 30 + hold_days) if first_paid_month else None,
        "timeline": timeline,
    }


IB_CHECKLIST = (
    ("Registration", (
        "Confirm the broker is licensed in the jurisdiction of every client you refer.",
        "Check whether your own jurisdiction requires IB registration or a licence.",
        "Keep the signed IB agreement and every amendment in one place.",
    )),
    ("Marketing", (
        "No guaranteed-return or risk-free language anywhere, including chat groups.",
        "Every public post carries the risk disclaimer the broker requires.",
        "Keep copies of every promotional message with the date it was sent.",
    )),
    ("Client handling", (
        "Never take a deposit, hold funds or trade on a client's behalf.",
        "Pass KYC questions to the broker; do not collect ID documents yourself.",
        "Log every complaint and forward it to the broker within their deadline.",
    )),
    ("Payout", (
        "Reconcile the broker's lot report against your own client list monthly.",
        "Record the clawback window and the events that trigger it.",
        "Keep the payout threshold and hold period next to every revenue forecast.",
    )),
)


def ib_checklist_text():
    """The compliance checklist as plain text, for download."""
    lines = ["IB affiliate compliance checklist — Sambangold #8", ""]
    for section, items in IB_CHECKLIST:
        lines.append("## %s" % section)
        for item in items:
            lines.append("- [ ] %s" % item)
        lines.append("")
    lines.append("Educational research only. Not legal or financial advice.")
    return "\n".join(lines)
