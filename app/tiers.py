"""The rank ladder — ported from Sam's site so both properties agree.

`printezy247/website_sam` (`src/config/tiers.ts`) is the origin of these keys,
labels, prices and broker doors. The keys never change; only the labels do.
One person carries one rank across the signals site and this tool site, so the
two tables must not drift.

What differs here, deliberately: on the tools side **General is free**, because
CLAUDE.md forbids paywalling a product at the door. The signals site charges
for General because it sells a different thing. Paid ranks here sell scale and
automation only — every one of the eighteen tools keeps its full free tier for
a visitor who never signs in.
"""

from dataclasses import dataclass

# --- capabilities ---------------------------------------------------------- #
# Derived from the `upsell` line every product carries in app/products.py.
# A feature is a capability, never a product: no tool is ever locked whole.

FEATURES = {
    "tools_free":  {"ms": "18 alat, tier percuma penuh",        "en": "18 tools, full free tier"},
    "history":     {"ms": "Sejarah larian dan eksport CSV",     "en": "Run history and CSV export"},
    "alerts":      {"ms": "Alert tersimpan dan tolakan bot",    "en": "Saved alerts and bot pushes"},
    "autopilot":   {"ms": "Pemantauan berterusan, alert harian", "en": "Continuous monitoring, daily alerts"},
    "batch":       {"ms": "Muat naik CSV pukal",                "en": "Bulk CSV upload"},
    "reports":     {"ms": "Laporan PDF berjadual",              "en": "Scheduled PDF reports"},
    "universe":    {"ms": "Universe sendiri, had lebih tinggi", "en": "Your own universe, higher limits"},
    "seats":       {"ms": "Kerusi berbilang untuk kumpulan",    "en": "Multiple seats for a group"},
    "clients":     {"ms": "Klien tanpa had, laporan klien",     "en": "Unlimited clients, client reports"},
    "whitelabel":  {"ms": "Widget jenama sendiri",              "en": "White-label embeddable widget"},
    "api":         {"ms": "Webhook keluar dan API",             "en": "Outbound webhooks and API"},
    "priority":    {"ms": "Sokongan keutamaan",                 "en": "Priority support"},
}

# The matrix, in display order.
FEATURE_ROWS = ("tools_free", "history", "alerts", "autopilot", "batch", "reports",
                "universe", "seats", "clients", "whitelabel", "api", "priority")

PUBLIC_F = ("tools_free",)
FREE_F = PUBLIC_F + ("history", "alerts")
PRO_F = FREE_F + ("autopilot", "batch", "reports", "universe")
ELITE_F = PRO_F + ("seats", "clients", "whitelabel", "api", "priority")


@dataclass(frozen=True)
class Tier:
    key: str
    rank: int
    price_month_cents: int
    price_year_cents: int
    ib_min_deposit_usd: int | None   # None = no broker door; 0 = an account with no deposit
    features: tuple = ()
    popular: bool = False

    @property
    def label(self):
        from .brand import RANKS
        return RANKS.get(self.key, RANKS["public"])["en"]

    def has(self, feature):
        return feature in self.features

    def price(self, interval="month"):
        return self.price_year_cents if interval == "year" else self.price_month_cents


TIERS = (
    Tier("public", 0, 0, 0, None, PUBLIC_F),
    Tier("free", 1, 0, 0, 0, FREE_F),
    Tier("pro", 2, 4900, 49000, 100, PRO_F, popular=True),
    Tier("elite", 3, 12900, 129000, 500, ELITE_F),
)

BY_KEY = {t.key: t for t in TIERS}
DEFAULT_TIER = "public"


def tier_by_key(key):
    return BY_KEY.get(key)


def rank_of(key):
    t = BY_KEY.get(key)
    return t.rank if t else 0


def tier_has(key, feature):
    t = BY_KEY.get(key)
    return bool(t and t.has(feature))


def higher_tier(a, b):
    return a if rank_of(a) >= rank_of(b) else b


def at_least(key, needed):
    """True when `key` sits at or above `needed` on the ladder."""
    return rank_of(key) >= rank_of(needed)


def tier_for_deposit(deposit_usd):
    """The highest rank a verified HFM deposit unlocks — the broker door."""
    eligible = [t for t in TIERS if t.ib_min_deposit_usd is not None and deposit_usd >= t.ib_min_deposit_usd]
    return max(eligible, key=lambda t: t.rank).key if eligible else DEFAULT_TIER


def tier_for_feature(feature):
    """The cheapest rank that includes this capability."""
    for t in TIERS:
        if t.has(feature):
            return t.key
    return TIERS[-1].key


def feature_label(feature, lang="ms"):
    row = FEATURES.get(feature)
    return (row or {}).get(lang) or (row or {}).get("ms") or feature


def fmt_usd(cents):
    return "$%s" % format(cents // 100, ",d") if cents % 100 == 0 else "$%.2f" % (cents / 100)
