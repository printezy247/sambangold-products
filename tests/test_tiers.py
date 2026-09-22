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
    assert tiers.tier_by_key("free").price_month_cents == 1900
    assert tiers.tier_by_key("pro").price_month_cents == 4900
    assert tiers.tier_by_key("elite").price_month_cents == 12900
    # CLAUDE.md: no product is paywalled at the door. Awam still answers in full.
    assert tiers.tier_by_key("public").price_month_cents == 0
    assert tiers.tier_has("public", "tools_free")
    assert tiers.fmt_usd(12900) == "$129"


def test_the_annual_price_is_derived_not_typed():
    """Twelve months for the price of ten, computed — so it cannot drift."""
    for tier in tiers.TIERS:
        assert tier.price_year_cents == tier.price_month_cents * 10
        assert tier.year_saving_cents == tier.price_month_cents * 2
        assert tier.price("year") == tier.price_year_cents
    assert tiers.tier_by_key("free").price_year_cents == 19000        # $190
    assert tiers.tier_by_key("pro").price_year_cents == 49000         # $490
    assert tiers.tier_by_key("elite").price_year_cents == 129000      # $1,290


def test_every_paid_rank_has_a_free_broker_door():
    """Nobody has to pay: the deposit band reaches the same rank."""
    for tier in tiers.TIERS[1:]:
        assert tier.ib_min_deposit_usd is not None
    assert tiers.tier_for_deposit(0) == "free"


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


def test_a_rank_is_a_grant_never_a_side_effect_of_signing_in(app):
    from app.auth import rank_for
    with app.app_context():
        assert rank_for({"id": 1, "telegram_id": "77"}) == "public"   # signing in buys nothing
        store.grant_entitlement("77", "free", source="ib", external_id="ib:1")
        assert rank_for({"id": 1, "telegram_id": "77"}) == "free"     # the broker door does
        store.grant_entitlement("77", "pro", source="stripe", external_id="sub_1")
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


# --- General is paid for, or earned at the broker door ---------------------- #

def test_general_costs_nineteen_on_your_own_broker_and_nothing_under_sams(app):
    assert tiers.tier_by_key("free").price_month_cents == 1900
    assert tiers.tier_for_deposit(0) == "free"          # any account under Sam, no deposit needed
    with app.app_context():
        assert store.effective_tier("77") == "public"
        store.grant_entitlement("77", "free", source="ib", external_id="ib:1")
        assert store.effective_tier("77") == "free"


def test_arming_an_alert_needs_general_on_both_surfaces(app, client):
    from app.telegram import reply_for
    with app.app_context():
        blocked = reply_for("/watch XAUUSD above 2450", chat_id=7, lang="en")
        assert "General" in blocked and "armed" not in blocked
        assert store.alerts_for("7") == []               # nothing was written

        store.grant_entitlement("7", "free", source="ib", external_id="ib:7")
        assert "armed" in reply_for("/watch XAUUSD above 2450", chat_id=7, lang="en")


def test_the_tools_themselves_stay_open_to_everyone(client):
    """CLAUDE.md's rule: the price gates the memory, never the answer."""
    body = client.get("/p/gold-watch").get_data(as_text=True)
    assert "2,399" in body or "2399" in body             # the live quote, with no account at all
    assert client.get("/p/broker-comparator").status_code == 200
    assert client.get("/p/prop-calculator").status_code == 200


def test_the_export_is_what_general_keeps(client, app):
    login(client, user_id="42")
    assert client.get("/p/gold-watch/history.csv").status_code == 302   # sent to the ranks page
    login(client, user_id="42", rank="free")
    assert client.get("/p/gold-watch/history.csv").status_code == 200


def test_the_ranks_page_states_both_prices_for_general(client):
    body = client.get("/pricing").get_data(as_text=True)
    assert "$19" in body and "$190" in body and "$38" in body
    assert "Broker sendiri" in body and "Broker di bawah Sam" in body
    client.get("/lang/en")
    body = client.get("/pricing").get_data(as_text=True)
    assert "free for anyone trading under Sam" in body


# --- where the line sits: convenience is charged, safety is not ------------- #

def test_the_calendar_reminder_is_general_but_reading_the_calendar_is_free(app):
    from app.telegram import reply_for
    with app.app_context():
        assert "CPI m/m" in reply_for("/calendar", chat_id=7, lang="en")   # the answer, free
        assert "General" in reply_for("/calendar_alert", chat_id=7, lang="en")
        assert not store.calendar_subscribed(7)
        store.grant_entitlement("7", "free", source="ib", external_id="ib:7")
        assert "ON" in reply_for("/calendar_alert", chat_id=7, lang="en")


def test_a_risk_warning_is_never_behind_a_rank(app):
    """A breach warning is the difference between noticing and losing a funded
    account. The scale there is sold by the account cap, not by the warning."""
    from app.sentineltool import link_account, apply_report
    sent = []
    with app.app_context():
        acc, err = link_account("77", "A", "FTMO", 100000)      # no rank at all
        assert acc and not err
        apply_report(acc, equity=94000, send=lambda chat, text: sent.append(text))
    assert sent, "a trader near a breach hears about it whatever they pay"


def test_the_exposure_warning_is_free_too(app):
    from app import exposuretool
    with app.app_context():
        assert "ex.warn" not in str(exposuretool.bot_exposure(["warn"], chat_id="77", lang="ms"))
        assert store.get_setting("exposure-monitor", "77", "warn") == "on"


def test_admin_can_register_the_bot_commands_from_the_page(client, app, monkeypatch):
    """The command list lives in the code; Telegram only learns it when told.
    One button does it, so a newly shipped command is one press from the menu."""
    from app import telegram, views

    sent = {}
    monkeypatch.setattr(views.telegram, "set_webhook", lambda base, token: sent.setdefault("hook", (base, token)))
    monkeypatch.setattr(views.telegram, "set_commands", lambda token: sent.setdefault("cmds", token))
    login(client, user_id="99", admin=True)
    app.config["ADMIN_TELEGRAM_ID"] = "99"
    app.config["TELEGRAM_BOT_TOKEN"] = "t0ken"
    app.config["PUBLIC_BASE_URL"] = "https://example.test"

    r = client.post("/admin", data={"hook": "1"}, follow_redirects=True)
    assert r.status_code == 200
    assert sent["hook"] == ("https://example.test", "t0ken") and sent["cmds"] == "t0ken"
    # The commands the bot ships today are the ones Telegram is handed.
    names = [c for c, _ in telegram.COMMANDS["ms"]]
    assert {"setup", "brief", "register"} <= set(names)


def test_registering_without_a_token_says_so_instead_of_failing(client, app):
    login(client, user_id="99", admin=True)
    app.config["ADMIN_TELEGRAM_ID"] = "99"
    app.config["TELEGRAM_BOT_TOKEN"] = ""
    r = client.post("/admin", data={"hook": "1"}, follow_redirects=True)
    assert r.status_code == 200
