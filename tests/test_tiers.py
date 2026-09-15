"""The rank ladder: the maths, the grants, the gate, and the two surfaces.

The ladder is ported from Sam's site (printezy247/website_sam, src/config/tiers.ts
and src/lib/entitlements.ts), so these tests pin the parts that must not drift:
the keys, the broker doors, and "effective rank is the highest active grant".
"""

import time


from app import store, tiers
from app.brand import RANKS
from app.gate import allows, bot_gate, upgrade_line

from tests.conftest import login


# --- the ladder itself ------------------------------------------------------ #

def test_keys_and_labels_match_sams_site():
    assert [t.key for t in tiers.TIERS] == ["public", "free", "pro", "elite"]
    assert [RANKS[t.key]["en"] for t in tiers.TIERS] == ["Public", "General", "A-Team", "Rambo"]
    assert [t.rank for t in tiers.TIERS] == [0, 1, 2, 3]


def test_prices_and_the_free_door():
    assert tiers.tier_by_key("pro").price_month_cents == 4900
    assert tiers.tier_by_key("elite").price_month_cents == 12900
    assert tiers.tier_by_key("elite").price("year") == 129000
    # CLAUDE.md: no product is paywalled at the door.
    assert tiers.tier_by_key("public").price_month_cents == 0
    assert tiers.tier_by_key("free").price_month_cents == 0
    assert tiers.fmt_usd(12900) == "$129"


def test_features_accumulate_up_the_ladder():
    for lower, higher in zip(tiers.TIERS, tiers.TIERS[1:]):
        assert set(lower.features) <= set(higher.features)
    assert tiers.tier_has("public", "tools_free")
    assert not tiers.tier_has("free", "autopilot")
    assert tiers.tier_has("pro", "autopilot")
    assert not tiers.tier_has("pro", "seats")
    assert tiers.tier_has("elite", "seats")
    assert set(tiers.FEATURE_ROWS) == set(tiers.FEATURES)


def test_broker_door_follows_the_deposit():
    assert tiers.tier_for_deposit(0) == "free"
    assert tiers.tier_for_deposit(99) == "free"
    assert tiers.tier_for_deposit(100) == "pro"
    assert tiers.tier_for_deposit(499) == "pro"
    assert tiers.tier_for_deposit(500) == "elite"


def test_ladder_comparisons():
    assert tiers.higher_tier("free", "elite") == "elite"
    assert tiers.higher_tier("elite", "pro") == "elite"
    assert tiers.at_least("elite", "pro") and not tiers.at_least("free", "pro")
    assert tiers.tier_for_feature("autopilot") == "pro"
    assert tiers.tier_for_feature("whitelabel") == "elite"


# --- grants ----------------------------------------------------------------- #

def test_grant_lifts_the_effective_rank(app):
    with app.app_context():
        assert store.effective_tier("77") == "public"
        store.grant_entitlement("77", "pro", source="manual")
        assert store.effective_tier("77") == "pro"
        store.grant_entitlement("77", "elite", source="ib", external_id="ib:1")
        assert store.effective_tier("77") == "elite"       # highest active wins


def test_grant_is_idempotent_on_external_id(app):
    with app.app_context():
        store.grant_entitlement("77", "pro", source="stripe", external_id="sub_1")
        store.grant_entitlement("77", "elite", source="stripe", external_id="sub_1")
        rows = store.entitlements_for("77")
        assert len(rows) == 1 and rows[0]["tier_key"] == "elite"


def test_revoke_and_expiry_drop_the_rank(app):
    with app.app_context():
        store.grant_entitlement("77", "elite", source="stripe", external_id="sub_2")
        store.revoke_entitlement(external_id="sub_2")
        assert store.effective_tier("77") == "public"

        store.grant_entitlement("88", "pro", source="crypto", external_id="np:9",
                                expires_at=time.time() - 1)
        assert store.effective_tier("88") == "public"      # lapsed is not active
        assert store.expire_due() == 1
        assert store.entitlements_for("88", active_only=False)[0]["status"] == "expired"


def test_signing_in_is_general_and_admin_is_rambo(app):
    from app.auth import rank_for
    with app.app_context():
        assert rank_for({"id": 1, "telegram_id": "77"}) == "free"
        store.grant_entitlement("77", "pro", source="manual")
        assert rank_for({"id": 1, "telegram_id": "77"}) == "pro"
        app.config["ADMIN_TELEGRAM_ID"] = "99"
        assert rank_for({"id": 2, "telegram_id": "99"}) == "elite"


# --- the gate --------------------------------------------------------------- #

def test_gate_allows_by_capability_not_by_product():
    assert allows("public", "tools_free") and allows("free", "tools_free")
    assert not allows("free", "autopilot") and allows("pro", "autopilot")
    assert not allows("pro", "clients") and allows("elite", "clients")


def test_upgrade_line_names_the_rank_in_both_languages():
    assert "A-Team" in upgrade_line("autopilot", "ms")
    assert "Rambo" in upgrade_line("seats", "en")
    assert upgrade_line("batch", "ms") != upgrade_line("batch", "en")   # BM first, EN second


def test_bot_gate_answers_instead_of_erroring(app):
    with app.app_context():
        blocked = bot_gate("autopilot", chat_id="77", lang="ms")
        assert blocked and "A-Team" in blocked
        store.grant_entitlement("77", "pro", source="manual")
        assert bot_gate("autopilot", chat_id="77", lang="ms") is None
        assert bot_gate("history", chat_id="77", lang="ms") is None   # signing in is General


# --- the surfaces ----------------------------------------------------------- #

def test_pricing_page_shows_the_ladder(client):
    body = client.get("/pricing").get_data(as_text=True)
    for label in ("Awam", "General", "A-Team", "Rambo"):
        assert label in body
    assert "$129" in body and "$49" in body
    assert "Pendidikan sahaja" in body        # the risk line survives

    client.get("/lang/en")
    body = client.get("/pricing").get_data(as_text=True)
    assert "No tool is locked at the door" in body
    assert "Deposit $500 or more" in body


def test_landing_rank_cards_carry_prices_not_coming_soon(client):
    body = client.get("/").get_data(as_text=True)
    assert "$129" in body and "$49" in body
    assert "Akan datang" not in body


def test_admin_grants_and_revokes(client, app):
    login(client, user_id="99", admin=True)
    app.config["ADMIN_TELEGRAM_ID"] = "99"
    r = client.post("/admin", data={"owner": "77", "tier": "elite", "days": "30"}, follow_redirects=True)
    assert r.status_code == 200 and "Rambo" in r.get_data(as_text=True)
    with app.app_context():
        assert store.effective_tier("77") == "elite"
        row = store.all_entitlements()[0]
    client.post("/admin", data={"revoke": str(row["id"])}, follow_redirects=True)
    with app.app_context():
        assert store.effective_tier("77") == "public"


def test_admin_grant_rejects_a_bad_rank(client, app):
    login(client, user_id="99", admin=True)
    app.config["ADMIN_TELEGRAM_ID"] = "99"
    client.post("/admin", data={"owner": "77", "tier": "kapten"}, follow_redirects=True)
    with app.app_context():
        assert store.all_entitlements() == []


def test_account_page_names_the_rank_source(client, app):
    with app.app_context():
        store.grant_entitlement("42", "pro", source="ib", external_id="ib:42")
    login(client, user_id="42")
    body = client.get("/account").get_data(as_text=True)
    assert "Pintu broker" in body
