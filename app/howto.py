"""Plain-language instructions on every tool page.

The tools answer well once you know what to type. The gap was never the
answer, it was the blank box: someone who has never used the thing opens the
page, sees a field called "Pass rate %", and closes the tab.

So every product carries three short steps and one concrete example. The steps
are written for someone who has never traded, the example is real data the tool
accepts, and where the form reads its values from the URL the example is a link
that fills the page in for you.

One map, one partial, eighteen tools. Adding a product without an entry here
fails `test_howto`, so a page can never ship as a blank box again.
"""

from urllib.parse import urlencode

# slug -> (example query, whether a link can fill the form)
EXAMPLES = {
    "prop-calculator":       ({"fee": "500", "size": "100000", "pass_pct": "15"}, True),
    "ib-revenue-calculator": ({"lots": "40", "rate": "7", "clients": "25", "clawback_pct": "5"}, True),
    "monte-carlo-sim":       ({"winrate": "55", "rr": "2", "risk": "1", "firm": "ftmo"}, True),
    "broker-comparator":     ({"lots": "1", "nights": "5"}, True),
    "gold-watch":            ({"level": "2450", "direction": "above"}, False),
    "gold-calendar":         ({}, False),
    "signal-verifier":       ({"price": "2400", "date": "today"}, False),
    "red-flag-scanner":      ({"text": "eg.pitch"}, False),
    "bot-scam-detector":     ({"subject": "@gold_ea_bot", "text": "eg.pitch"}, False),
    "influencer-audit":      ({"subject": "@gold_guru_my", "text": "eg.pitch"}, False),
    "copy-trade-audit":      ({"subject": "exness", "text": "eg.pitch"}, False),
    "exposure-monitor":      ({"text": "eg.positions"}, False),
    "drawdown-sentinel":     ({"name": "Akaun-1", "firm": "ftmo", "balance": "100000"}, False),
    "rebate-auditor":        ({}, False),
    "churn-radar":           ({}, False),
    "link-attribution":      ({"channel": "telegram"}, False),
    "tokenized-gold":        ({}, False),
    "miner-divergence":      ({}, False),
}


def steps(slug, lang="ms"):
    """Three short lines: what to do, what you get, and the shortcut."""
    from .brand import t
    return [t("how.%s_%d" % (slug.replace("-", "_"), i), lang) for i in (1, 2, 3)]


def example_query(slug, lang="ms"):
    """The example values, with any string-key placeholders resolved."""
    from .brand import t
    raw, _ = EXAMPLES.get(slug, ({}, False))
    return {k: (t("flow." + v.replace("eg.", "eg_"), lang) if v.startswith("eg.") else v)
            for k, v in raw.items()}


def example_link(slug, lang="ms"):
    """A URL that fills the form, or "" when the form cannot be filled that way."""
    query, linkable = EXAMPLES.get(slug, ({}, False))
    if not linkable or not query:
        return ""
    return "?" + urlencode(example_query(slug, lang))


def for_product(slug, lang="ms"):
    # Not "values": Jinja resolves that to the dict method, not the key.
    return {"steps": steps(slug, lang), "link": example_link(slug, lang),
            "example": example_query(slug, lang)}
