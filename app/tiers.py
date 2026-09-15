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


DEFAULT_TIER = "public"

# --- limits ----------------------------------------------------------------- #
# The other half of "paid ranks sell scale": the same tool, more of it. Every
# number below already existed as a hard free cap; a rank raises it rather than
# unlocking anything that was previously shut. 0 means no limit.

LIMITS = {
    "accounts":   {"public": 1, "free": 1, "pro": 10, "elite": 50},        # #14 linked prop accounts
    "clients":    {"public": 10, "free": 10, "pro": 200, "elite": 0},      # #11 clients scored per run
    "links":      {"public": 3, "free": 3, "pro": 50, "elite": 0},         # #13 tracked links
    "sims":       {"public": 1000, "free": 1000, "pro": 100000, "elite": 100000},   # #15 Monte Carlo paths
    "batch_rows": {"public": 20, "free": 20, "pro": 200, "elite": 1000},   # #2 claims verified at once
    "saves":      {"public": 8, "free": 8, "pro": 50, "elite": 200},       # saved comparisons
}

LIMIT_LABELS = {
    "accounts":   {"ms": "Akaun prop dipaut",       "en": "Linked prop accounts"},
    "clients":    {"ms": "Klien setiap larian",     "en": "Clients per run"},
    "links":      {"ms": "Pautan dijejak",          "en": "Tracked links"},
    "sims":       {"ms": "Laluan Monte Carlo",      "en": "Monte Carlo paths"},
    "batch_rows": {"ms": "Baris setiap kelompok",   "en": "Rows per batch"},
    "saves":      {"ms": "Perbandingan disimpan",   "en": "Saved comparisons"},
}


def limit_for(key, tier=DEFAULT_TIER):
    """The cap this rank carries for `key`. 0 means unlimited."""
    row = LIMITS.get(key) or {}
    return row.get(tier, row.get(DEFAULT_TIER, 0))


def limit_label(key, lang="ms"):
    row = LIMIT_LABELS.get(key) or {}
    return row.get(lang) or row.get("ms") or key


@dataclass(frozen=True)
class Tier:
    key: str
    rank: int
    price_month_cents: int
    price_year_cents: int
    ib_min_deposit_usd: int | None   # None = no broker door; 0 = an account with no deposit
    features: tuple = ()
    popular: bool = False
    seats: int = 0                   # extra people this rank may carry, beyond the holder

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
    Tier("elite", 3, 12900, 129000, 500, ELITE_F, seats=10),
)

BY_KEY = {t.key: t for t in TIERS}


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


def seats_for(key):
    """How many extra people this rank may seat. Kept off the LIMITS map on
    purpose: there 0 means unlimited, and here 0 must mean none."""
    t = BY_KEY.get(key)
    return t.seats if t else 0


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
