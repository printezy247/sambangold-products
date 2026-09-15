"""What a rank gives on one product — and the test that keeps the page honest.

The bug this file exists for: every product page rendered the registry's
`upsell` sentence as if it were a live capability. Ten of eighteen products
promised something nobody had built, and the card said "UPGRADE · A-TEAM" even
to a Rambo holder. A perk is now derived from the wiring, and
`test_no_page_can_promise_something_unbuilt` makes the old bug unreintroducible.
"""

import time

from app import autopilot, perks, store
from app.products import PRODUCTS
from app.tiers import TIERS

from tests.conftest import login


# --- the guard rail --------------------------------------------------------- #

def test_no_page_can_promise_something_unbuilt():
    """Every line a product page shows must come from real wiring.

    Perks are computed from the autopilot registry, the LIMITS map and the
    feature matrix. There is no free-text path into the card, so a sentence
    someone writes in the registry can never again be shown as a feature.
    """
    for p in PRODUCTS:
        for tier in TIERS:
            r = perks.for_product(p.slug, tier.key, "en")
            for line in r["have"] + r["adds"]:
                assert line and not line.startswith("perk."), (p.slug, tier.key, line)
            if r["next_rank"]:
                assert r["adds"], (p.slug, tier.key)      # never offer an upgrade that adds nothing


def test_every_limit_and_autopilot_entry_belongs_to_a_real_product():
    slugs = {p.slug for p in PRODUCTS}
    assert set(perks.PRODUCT_LIMIT) <= slugs
    assert set(perks.KEEPS_HISTORY) <= slugs
    assert {autopilot.product_of(s) for s in autopilot.SLUGS} <= slugs


def test_perks_only_grow_up_the_ladder():
    for p in PRODUCTS:
        seen = [set(perks.perks_at(p.slug, t.key, "en")) for t in TIERS]
        for lower, higher in zip(seen, seen[1:]):
            assert len(higher) >= len(lower), p.slug


# --- the bug the user hit --------------------------------------------------- #

def test_rambo_is_not_told_to_upgrade_to_a_team(client, app):
    """The reported bug: a Rambo holder was shown "UPGRADE · A-TEAM" on a page
    whose A-Team feature did not exist."""
    login(client, user_id="42", rank="elite")
    body = client.get("/p/red-flag-scanner").get_data(as_text=True)
    assert "Rambo" in body
    assert "A-Team" not in body
    assert "Anda sudah ada semua" in body           # you already have everything here


def test_a_page_with_nothing_behind_a_rank_says_so(client):
    assert perks.products_with_nothing() == ["broker-comparator"]
    body = client.get("/p/broker-comparator").get_data(as_text=True)
    assert "Tiada pangkat mengubah apa-apa" in body


def test_a_visitor_with_no_rank_sees_the_real_next_step(client):
    body = client.get("/p/red-flag-scanner").get_data(as_text=True)
    assert "General" in body and "Sejarah larian" in body


# --- the scorecard that was only ever a promise ----------------------------- #

def test_every_scanner_now_has_the_weekly_scorecard_it_advertised(app):
    for slug in autopilot.SCANNERS:
        assert "%s:scorecard" % slug in autopilot.REPORTS
        assert autopilot.NEEDS["%s:scorecard" % slug] == "reports"
        assert autopilot.CADENCE["%s:scorecard" % slug] == "weekly"


def test_the_scorecard_counts_the_week_and_names_what_flagged(app):
    with app.app_context():
        store.save_scan({"product": "red-flag-scanner", "subject": "@vip_gold",
                         "score": 82, "verdict": "avoid", "flags": []}, owner="77")
        store.save_scan({"product": "red-flag-scanner", "subject": "@ok_channel",
                         "score": 10, "verdict": "clear", "flags": []}, owner="77")
        text = autopilot.BY_SLUG["red-flag-scanner:scorecard"]("77", "en")
    assert text and "2 scans this week" in text and "1 flagged" in text
    assert "@vip_gold" in text and "@ok_channel" not in text     # only what flagged


def test_the_scorecard_is_silent_on_an_empty_week(app):
    with app.app_context():
        assert autopilot.BY_SLUG["red-flag-scanner:scorecard"]("77", "en") is None


def test_the_scorecard_ignores_scans_older_than_a_week(app):
    with app.app_context():
        store.save_scan({"product": "red-flag-scanner", "subject": "@old", "score": 90,
                         "verdict": "avoid", "flags": []}, owner="77")
        store.db().execute("UPDATE scans SET created_at = ? WHERE owner = '77'",
                           (time.time() - 9 * 86400,))
        store.db().commit()
        assert autopilot.BY_SLUG["red-flag-scanner:scorecard"]("77", "en") is None


def test_a_rambo_holder_can_switch_the_scorecard_on(app):
    with app.app_context():
        store.grant_entitlement("77", "elite", source="manual")
        reply = autopilot.bot_autopilot([], chat_id="77", lang="en")
        assert "red-flag-scanner:scorecard" in reply
        assert autopilot.toggle("77", "red-flag-scanner:scorecard") == "on"
