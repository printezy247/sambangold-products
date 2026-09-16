"""The combined internal product roadmap: this repo's 18 SaaS tools plus
website_sam's digital-product catalog, in one Apple-style status grid.

`internal_status` is deliberately separate from `products.Product.status`.
The latter means "the code exists on both the bot and dashboard surfaces" —
CLAUDE.md calls it the single source of truth for that narrower fact, and
tests enforce it. `internal_status` means "where this actually stands for
the business" (launched / ready to launch / in progress / developing / not
delivered), which is a judgement call for the CEO/HODs, not a code fact.
Seeding never overwrites a status a person has already set — see
`store.seed_roadmap`.
"""

from .products import PRODUCTS

FAMILIES = ("saas-tools", "digital-products")


def _saas_tools_seed():
    """All 18 tools in this repo ship both surfaces and are live — see
    products/product-01..18.md, all now SHIPPED or LIVE."""
    return [
        {"family": "saas-tools", "slug": p.slug, "name": p.name, "vertical": p.vertical,
         "internal_status": "launched", "owner_role": None, "notes": ""}
        for p in PRODUCTS
    ]


# website_sam (printezy247/website_sam) digital-product catalog, from its
# src/db/seed.ts sample data. That repo isn't imported here, so the grain is
# per product line rather than per SKU — 24 ebook titles collapse into three
# tier rows — enough to track launch status without a second registry to keep
# in sync by hand.
DIGITAL_PRODUCTS_SEED = (
    {"slug": "dp-tv-indicators", "name": "TradingView Indicators (Sam Gold Levels, SMC Suite)",
     "vertical": "Gold", "internal_status": "launched"},
    {"slug": "dp-mt5-indicators", "name": "MT5 Indicators (Sam Gold Levels)",
     "vertical": "Gold", "internal_status": "launched"},
    {"slug": "dp-copier", "name": "Telegram → MT5 Copier",
     "vertical": "Gold", "internal_status": "launched"},
    {"slug": "dp-ebooks-free", "name": "Ebook Library — Free tier (7 titles, EN+BM)",
     "vertical": "Education", "internal_status": "launched"},
    {"slug": "dp-ebooks-standard", "name": "Ebook Library — Standard tier (4 titles, EN+BM)",
     "vertical": "Education", "internal_status": "launched"},
    {"slug": "dp-ebooks-premium", "name": "Ebook Library — Premium (Gold Recruit Manual, EN+BM)",
     "vertical": "Education", "internal_status": "launched"},
    {"slug": "dp-signals", "name": "Live XAUUSD Signals + auto TP/SL tracking",
     "vertical": "Signals", "internal_status": "launched"},
    {"slug": "dp-mentorship", "name": "Mentorship tier",
     "vertical": "Education", "internal_status": "developing"},
)


def _digital_products_seed():
    return [
        {"family": "digital-products", "slug": d["slug"], "name": d["name"], "vertical": d["vertical"],
         "internal_status": d["internal_status"], "owner_role": None,
         "notes": "Planned per website_sam docs/product-spec.md — not live yet." if d["slug"] == "dp-mentorship" else ""}
        for d in DIGITAL_PRODUCTS_SEED
    ]


def seed_data():
    return _saas_tools_seed() + _digital_products_seed()


def grouped(items):
    """Roadmap rows grouped by family, in FAMILIES order."""
    by_family = {f: [] for f in FAMILIES}
    for it in items:
        by_family.setdefault(it["family"], []).append(it)
    return [(f, by_family[f]) for f in FAMILIES if by_family.get(f)]
