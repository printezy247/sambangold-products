"""#17 Tokenized Gold — is this premium normal, or is this the moment?

The tool already says what the premium *is*: PAXG is 1.4% over spot. That number
is useless on its own, because nobody knows whether 1.4% is the usual toll or a
bad day to buy. A fixed warning threshold does not fix it either — it fires on
every asset at the same number, when each one has its own habitual range.

The checker has been logging the PAXG and XAUT prices against spot every five
minutes since #17 shipped. This reads that back as each asset's **own** band:
the 10th and 90th percentile of its premium over the last thirty days. Then the
question stops being "what is the premium" and becomes the one a buyer actually
has — **is this cheap, normal, or dear, for this coin?** — plus the follow-up
nobody else answers: **which of the two is the cheaper way into gold right now.**

Free at every rank, on the same reasoning as the hours map and the event record:
overpaying because you had no reference is a loss, and warning about a loss is
not what we charge for.
"""

from . import store
from .brand import DEFAULT_LANG, t

ASSETS = ("paxg", "xaut")
DAYS = 30
MIN_SAMPLES = 100          # under this the percentiles are noise wearing a suit
LOW, HIGH = 10, 90         # the band edges, as percentiles


def percentile(values, p):
    """Linear-interpolated percentile. Values must be non-empty."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * (p / 100.0)
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def series(asset, days=DAYS, rows=None):
    """Every logged premium for one asset, oldest first, as a percentage."""
    if rows is None:
        rows = store.premium_series(days) if store.ready() else []
    out = []
    for r in rows:
        price, spot = r.get(asset), r.get("spot")
        if price and spot:
            out.append((price / spot - 1) * 100)
    return out


def band(asset, days=DAYS, rows=None, now=None):
    """One asset's habitual range, and where it sits inside it right now.

    Returns `None` under `MIN_SAMPLES` — a band drawn through a handful of
    samples would look exactly as authoritative as a real one, and someone
    would buy on it.
    """
    values = series(asset, days, rows)
    if len(values) < MIN_SAMPLES:
        return None
    low, high = percentile(values, LOW), percentile(values, HIGH)
    here = values[-1] if now is None else now
    verdict = "cheap" if here <= low else ("dear" if here >= high else "normal")
    span = high - low
    return {"asset": asset, "n": len(values), "days": days, "low": low, "high": high,
            "median": percentile(values, 50), "now": here, "verdict": verdict,
            "position": ((here - low) / span) if span else 0.5}


def bands(analysis=None, days=DAYS, rows=None):
    """A band per asset, using the live premium where the tool has one."""
    if rows is None:
        rows = store.premium_series(days) if store.ready() else []
    out = {}
    for asset in ASSETS:
        live = (analysis or {}).get("%s_premium" % asset)
        out[asset] = band(asset, days, rows, now=live)
    return out


def cheapest(analysis):
    """Which coin is the cheaper way into gold right now, and by how much.

    None when only one side priced — a winner declared against a missing
    number is not a comparison.
    """
    priced = {a: analysis.get("%s_premium" % a) for a in ASSETS}
    priced = {a: v for a, v in priced.items() if v is not None}
    if len(priced) < 2:
        return None
    best = min(priced, key=priced.get)
    worst = max(priced, key=priced.get)
    return {"asset": best, "premium": priced[best], "other": worst,
            "saving": priced[worst] - priced[best]}


def broke(before, after):
    """Assets whose premium has just left its band — what the alert fires on.

    A break is a crossing, not a state: an asset that was already outside stays
    quiet, because a daily push repeating yesterday's news trains people to
    ignore it.
    """
    out = []
    for asset in ASSETS:
        was, now = (before or {}).get(asset), (after or {}).get(asset)
        if not was or not now:
            continue
        if was["verdict"] == "normal" and now["verdict"] != "normal":
            out.append(now)
    return out


# --- copy ------------------------------------------------------------------- #

def line(b, lang=DEFAULT_LANG):
    """One sentence: where this coin sits in its own thirty-day range."""
    if not b:
        return t("band.thin", lang)
    return t("band.%s" % b["verdict"], lang, asset=b["asset"].upper(), now="%+.2f" % b["now"],
             low="%+.2f" % b["low"], high="%+.2f" % b["high"], days=b["days"])


def lines(analysis, days=DAYS, rows=None, lang=DEFAULT_LANG):
    """The band block: a line per coin, then which one to buy."""
    out = [t("band.h", lang)]
    measured = bands(analysis, days, rows)
    for asset in ASSETS:
        out.append(line(measured[asset], lang))
    best = cheapest(analysis)
    if best:
        out.append(t("band.route", lang, asset=best["asset"].upper(), premium="%+.2f" % best["premium"],
                     saving="%.2f" % best["saving"], other=best["other"].upper()))
    return out
