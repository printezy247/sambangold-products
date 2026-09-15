"""What a rank actually gives you on one product.

This module exists because of a bug worth naming. Every product page used to
render the `upsell` line from the registry as if it were a live capability:
marketing copy, shown to everyone, promising things that in ten of eighteen
cases were never built. A Rambo holder opening the red-flag scanner was told to
upgrade to A-Team for a group auto-scan that does not exist.

So a perk is no longer a sentence someone wrote. It is derived from the three
places a rank is actually wired:

* the autopilot registry — does this product have a daily digest or a report?
* the LIMITS map — does this product have a cap a rank raises?
* the feature matrix — history, alerts and the rest.

`for_product` returns what you already have and what the next rank would add.
If a product has nothing behind a rank, it says so instead of inventing an
upgrade, and `test_perks` asserts that no page can ever claim otherwise.
"""

from . import autopilot
from .brand import t
from .tiers import BY_KEY, LIMITS, TIERS, at_least, limit_for, limit_label, tier_for_feature

# Which cap belongs to which product. Only real entries: a product missing here
# simply has no cap a rank raises.
PRODUCT_LIMIT = {
    "drawdown-sentinel": "accounts",
    "churn-radar": "clients",
    "link-attribution": "links",
    "monte-carlo-sim": "sims",
    "signal-verifier": "batch_rows",
    "prop-calculator": "saves",
    "ib-revenue-calculator": "saves",
}

# Products whose saved history is the thing General keeps.
# The scanners the group watcher covers — the other half of what those pages
# advertised, now built.
AUTOSCAN = ("bot-scam-detector", "copy-trade-audit", "red-flag-scanner", "influencer-audit")

KEEPS_HISTORY = ("gold-watch", "signal-verifier", "bot-scam-detector", "copy-trade-audit",
                 "red-flag-scanner", "influencer-audit", "rebate-auditor", "churn-radar",
                 "monte-carlo-sim", "exposure-monitor", "ib-revenue-calculator")


def _entries(slug):
    """(feature, cadence) for every autopilot or report switch this product has."""
    return [(autopilot.NEEDS[s], autopilot.CADENCE[s]) for s in autopilot.SLUGS
            if autopilot.product_of(s) == slug]


def perks_at(slug, tier, lang="ms"):
    """Everything this rank gives on this product, as display lines."""
    out = []
    for feature, cadence in _entries(slug):
        if at_least(tier, tier_for_feature(feature)):
            out.append(t("perk.ap_" + cadence, lang))
    if slug in KEEPS_HISTORY and at_least(tier, tier_for_feature("history")):
        out.append(t("perk.history", lang))
    if slug in AUTOSCAN and at_least(tier, tier_for_feature("autoscan")):
        out.append(t("perk.autoscan", lang))
    if slug == "gold-watch" and at_least(tier, tier_for_feature("alerts")):
        out.append(t("perk.alerts", lang))
    if slug == "gold-calendar" and at_least(tier, tier_for_feature("alerts")):
        out.append(t("perk.calendar", lang))
    key = PRODUCT_LIMIT.get(slug)
    if key:
        n = limit_for(key, tier)
        out.append(t("perk.cap", lang, what=limit_label(key, lang),
                     n="∞" if n == 0 else format(n, ",d")))
    return out


def next_rank(slug, tier):
    """The cheapest rank above `tier` that adds something here, or None."""
    mine = perks_at(slug, tier, "en")
    for candidate in TIERS:
        if BY_KEY[candidate.key].rank <= BY_KEY[tier].rank:
            continue
        if perks_at(slug, candidate.key, "en") != mine:
            return candidate.key
    return None


def for_product(slug, tier, lang="ms"):
    """{have, next_rank, adds} — what you hold here, and what moving up would add."""
    have = perks_at(slug, tier, lang)
    nxt = next_rank(slug, tier)
    adds = []
    if nxt:
        mine = set(perks_at(slug, tier, "en"))
        for line, en in zip(perks_at(slug, nxt, lang), perks_at(slug, nxt, "en")):
            if en not in mine:
                adds.append(line)
    return {"have": have, "next_rank": nxt, "adds": adds}


def products_with_nothing():
    """Products where no rank changes anything. Kept honest, not hidden."""
    from .products import PRODUCTS
    return [p.slug for p in PRODUCTS if not any(for_product(p.slug, x.key, "en")["have"] for x in TIERS)]
