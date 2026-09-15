"""#13 IB Link Attribution & Funnel Tracker — per-channel short links and the funnel behind them.

A tracked link is a short code that redirects to the IB's referral URL and
counts the click. Broker portals do not call back, so the later stages —
signup, first deposit, first lot — are logged by the IB: a form on the
dashboard, or a pasted CSV of the portal's report with a channel column.
The funnel per channel is then clicks → signups → deposits → first lots with
the conversion between each, over a date range, so the IB learns which
channel pays rather than which felt busiest.
"""

import csv
import io
import secrets
import time

from .rebate import _norm, _num, _pick

STAGES = ("click", "signup", "deposit", "first_lot")
FREE_LINKS = 3
RANGES = {"7": 7, "30": 30, "90": 90}

CHANNEL_COLS = ("channel", "campaign", "tag", "source", "link", "code", "ref", "utm_campaign")
STAGE_COLS = ("stage", "event", "type", "status")
COUNT_COLS = ("count", "n", "clients", "signups", "qty", "number")
DATE_COLS = ("date", "day", "at", "time", "created")


class InputError(ValueError):
    pass


def new_code():
    return secrets.token_urlsafe(4).replace("-", "x").replace("_", "y")[:6].lower()


def normalise_stage(text):
    s = (text or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"clicks": "click", "signups": "signup", "registration": "signup", "registered": "signup", "register": "signup",
               "deposits": "deposit", "ftd": "deposit", "first_deposit": "deposit", "funded": "deposit",
               "lot": "first_lot", "lots": "first_lot", "trade": "first_lot", "traded": "first_lot", "first_trade": "first_lot", "firstlot": "first_lot"}
    s = aliases.get(s, s)
    if s not in STAGES:
        raise InputError("stage not understood: %s" % text)
    return s


def parse_events_csv(text):
    """Rows of {channel, stage, count, date} from a pasted portal report."""
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
    ch, st, ct, dt_ = _pick(headers, CHANNEL_COLS), _pick(headers, STAGE_COLS), _pick(headers, COUNT_COLS), _pick(headers, DATE_COLS)
    if not (ch and st):
        raise InputError("need channel and stage columns; found: %s" % ", ".join(h for h in headers if h))
    rows = []
    for r in reader:
        if not (r.get(ch) or "").strip():
            continue
        rows.append({"channel": r[ch].strip(), "stage": normalise_stage(r.get(st)),
                     "count": int(_num(r.get(ct))) if ct and (r.get(ct) or "").strip() else 1,
                     "date": (r.get(dt_) or "").strip() if dt_ else ""})
    if not rows:
        raise InputError("no data rows")
    return rows


def funnel(links, events):
    """Per-link funnel plus totals. `events` are {link_id, stage, count}."""
    by = {l["id"]: dict(l, click=0, signup=0, deposit=0, first_lot=0) for l in links}
    for e in events:
        if e["link_id"] in by and e["stage"] in STAGES:
            by[e["link_id"]][e["stage"]] += e["count"]
    rows = list(by.values())
    for r in rows:
        r["ctr_signup"] = (r["signup"] / r["click"]) if r["click"] else None
        r["ctr_deposit"] = (r["deposit"] / r["signup"]) if r["signup"] else None
        r["ctr_lot"] = (r["first_lot"] / r["deposit"]) if r["deposit"] else None
        r["click_to_lot"] = (r["first_lot"] / r["click"]) if r["click"] else None
    rows.sort(key=lambda r: (-r["first_lot"], -r["deposit"], -r["signup"], -r["click"]))
    total = {s: sum(r[s] for r in rows) for s in STAGES}
    total["click_to_lot"] = (total["first_lot"] / total["click"]) if total["click"] else None
    return {"rows": rows, "total": total}


def since(days):
    return time.time() - days * 86400
