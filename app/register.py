"""The public register — look someone up before you pay them.

Four of the scanners answer the same shape of question about a different kind of
subject: a Telegram bot, a signal seller, an influencer, a copy-trade broker.
Each answer is good, and each one evaporates. The person who gets pitched by the
same handle next week starts from nothing, and so does everyone else.

This reads the `scans` archive back the other way round — **by subject, across
everybody** — so a name that keeps coming back accumulates a page anyone can
search before they send money. That is the one thing a scammer cannot outrun:
not a verdict, but a record that outlives the account they will burn next month.

## What it deliberately is not

It is a record of **what our scanner found**, not a claim about a person. The
difference matters, because these are real businesses and real handles:

* only subjects the rule engine actually flagged appear — a clear scan leaves
  no entry;
* nothing is published under `MIN_DAYS` distinct days, so one person scanning a
  rival five times in an afternoon never becomes a listing;
* every row shows its evidence — the count, the dates, the score — and links to
  the scans behind it, so a reader judges rather than takes our word;
* the wording stays the scanner's own vocabulary. The register never calls
  anyone a scammer, and the risk strip rides every surface it appears on.

Free at every rank, and public without a login, because someone about to be
defrauded is exactly the person who has not signed up yet.
"""

import time

from . import store
from .brand import DEFAULT_LANG, t

# The scanners that describe a *subject* someone could look up. The signal
# verifier is here too: a seller's scorecard is this same page, filtered.
PRODUCTS = ("red-flag-scanner", "bot-scam-detector", "influencer-audit",
            "copy-trade-audit", "signal-verifier")
SELLER = "signal-verifier"

MIN_DAYS = 2        # one afternoon of scanning a rival is not a record
MIN_FLAGGED = 2     # and neither is a single bad reading
FRESH = 90 * 86400  # rows older than this are history, shown but marked


def listed(row):
    """Does this subject clear the bar to be named on a public page?"""
    return row["days"] >= MIN_DAYS and row["flagged"] >= MIN_FLAGGED


def rows(products=PRODUCTS, subject=None, limit=60, include_unlisted=False):
    """Register rows, worst first. Subjects under the bar are dropped unless
    the caller is looking one up by name — then they are returned marked, so a
    search says "we have seen this, but not enough to list it" rather than
    "nothing", which would read as a clean bill of health."""
    if not store.ready():
        return []
    out = []
    for row in store.register_rows(products, subject, limit * 3):
        row["listed"] = listed(row)
        row["stale"] = (time.time() - row["last_at"]) > FRESH
        if row["listed"] or include_unlisted or subject:
            out.append(row)
    out.sort(key=lambda r: (r["listed"], r["flagged"], r["worst"]), reverse=True)
    return out[:limit]


def lookup(subject, products=PRODUCTS):
    """One subject, everything we have on it. None when we have never seen it."""
    found = rows(products, subject=subject, limit=10)
    return found[0] if found else None


def scorecard(handle):
    """#2's seller scorecard: how the claims from one handle actually checked out."""
    return lookup(handle, products=(SELLER,))


def seen_days(row):
    return max(1, int((row["last_at"] - row["first_at"]) / 86400) + 1)


# --- copy --------------------------------------------------------------------- #

def _when(ts, lang):
    days = int((time.time() - ts) / 86400)
    if days <= 0:
        return t("reg.today", lang)
    return t("reg.days_ago", lang, n=days)


def line(row, lang=DEFAULT_LANG):
    """One subject as one sentence."""
    if not row["listed"]:
        return t("reg.thin", lang, subject=row["subject"], n=row["n"])
    return t("reg.row", lang, subject=row["subject"], flagged=row["flagged"], n=row["n"],
             worst=row["worst"], when=_when(row["last_at"], lang))


def lines(subject, lang=DEFAULT_LANG):
    """The bot's answer to "is this name known?"."""
    if not (subject or "").strip():
        return [t("reg.usage", lang)]
    row = lookup(subject)
    if not row:
        # "No record" is not "safe", and saying so is the whole point.
        return [t("reg.none", lang, subject=subject.strip()), "", t("reg.none_note", lang)]
    return [t("reg.h", lang), line(row, lang), "", t("reg.evidence", lang, n=row["n"], days=seen_days(row)),
            t("reg.disclaimer", lang)]


# --- surfaces ------------------------------------------------------------------- #

def bot_register(args, chat_id=None, lang=DEFAULT_LANG, **_):
    return "\n".join(lines(" ".join(args), lang))


def page(request):
    """The public register page: a search box and the listed subjects."""
    query = (request.values.get("q") or "").strip()
    product = request.values.get("p") or ""
    products = (product,) if product in PRODUCTS else PRODUCTS
    found = rows(products, subject=query or None) if query else rows(products)
    from .products import BY_SLUG
    return {"q": query, "product": product, "products": PRODUCTS, "rows": found, "by_slug": BY_SLUG,
            "line": lambda r: line(r, _lang()), "when": lambda ts: _when(ts, _lang()),
            "seen_days": seen_days, "min_days": MIN_DAYS, "min_flagged": MIN_FLAGGED}


def _lang():
    from .auth import lang as ui_lang
    return ui_lang()
