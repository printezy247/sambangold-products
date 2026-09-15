"""The two ways up the ladder that cost no money, and the Rambo seats.

Both doors are ported from Sam's site: the HFM broker door (deposit decides the
rank, thirty days, renewable) and referral credit (bring one person in, get a
stretch of a higher rank). Neither is a discount on a paywall, because there is
no paywall — they are how a member reaches automation and scale without cash.
"""

import time

from app import doors, seats, store, tiers
from app.telegram import handle_update

from tests.conftest import login


def _msg(text, uid=7):
    return {"message": {"chat": {"id": uid}, "from": {"id": uid, "username": "ada", "first_name": "Ada"}, "text": text}}


# --- the broker door -------------------------------------------------------- #

def test_the_deposit_band_decides_the_rank(app):
    with app.app_context():
        row, err = doors.claim("77", "1234567", 600)
        assert row and not err and row["status"] == "pending"
        assert store.effective_tier("77") == "public"        # a claim alone grants nothing

        tier, err = doors.approve(row["id"])
        assert tier == "elite" and not err
        assert store.effective_tier("77") == "elite"


def test_a_smaller_deposit_earns_a_smaller_rank(app):
    with app.app_context():
        row, _ = doors.claim("77", "7654321", 120)
        assert doors.approve(row["id"])[0] == "pro"
        row2, _ = doors.claim("88", "7654322", 0)
        assert doors.approve(row2["id"])[0] == "free"


def test_the_broker_rank_expires_after_thirty_days(app):
    now = time.time()          # grants are compared against the clock, so start from it
    with app.app_context():
        row, _ = doors.claim("77", "1234567", 600)
        doors.approve(row["id"], now=now)
        grant = store.entitlements_for("77")[0]
        assert abs(grant["expires_at"] - (now + doors.IB_DAYS * 86400)) < 1
        store.expire_due(now=now + doors.IB_DAYS * 86400 + 1)
        assert store.effective_tier("77") == "public"


def test_re_verifying_the_same_account_renews_instead_of_duplicating(app):
    with app.app_context():
        row, _ = doors.claim("77", "1234567", 600)
        doors.approve(row["id"], now=time.time())
        doors.approve(row["id"], now=time.time() + 2_000_000)
        assert len(store.entitlements_for("77", active_only=False)) == 1


def test_a_bad_or_taken_account_is_refused(app):
    with app.app_context():
        assert doors.claim("77", "abc")[1] == "br.bad_account"
        assert doors.claim("77", "12")[1] == "br.bad_account"
        doors.claim("77", "1234567", 600)
        assert doors.claim("88", "1234567")[1] == "br.taken"


def test_rejecting_a_claim_takes_the_rank_back(app):
    with app.app_context():
        row, _ = doors.claim("77", "1234567", 600)
        doors.approve(row["id"])
        doors.reject(row["id"], "deposit not found")
        assert store.effective_tier("77") == "public"


def test_the_bot_lists_the_bands_and_queues_a_claim(app):
    with app.app_context():
        listing = doors.bot_broker([], chat_id="77", lang="ms")
        assert "A-Team" in listing and "Rambo" in listing and "500" in listing
        assert "1234567" in doors.bot_broker(["1234567"], chat_id="77", lang="ms")
        assert store.broker_claims_for("77")[0]["account"] == "1234567"


# --- referral --------------------------------------------------------------- #

def test_a_referral_link_attaches_once_and_never_to_yourself(app):
    with app.app_context():
        code = doors.code_for("88")
        assert doors.owner_of_code(code) == "88"
        assert doors.attach("88", "ref_" + code) is None          # never yourself
        assert doors.attach("99", "ref_" + code) == "88"
        assert doors.attach("99", "ref_" + doors.code_for("77")) is None   # the first one keeps it
        assert doors.invited_by("99") == "88"


def test_the_credit_lands_once_when_the_invited_member_reaches_a_rank(app):
    with app.app_context():
        doors.attach("99", "ref_" + doors.code_for("88"))
        row, _ = doors.claim("99", "1234567", 600)
        doors.approve(row["id"])                                   # approving credits the referrer
        grants = store.entitlements_for("88")
        assert len(grants) == 1 and grants[0]["source"] == "referral"
        assert doors.credit_referrer("99") is None                 # one credit per person
        assert len(store.entitlements_for("88")) == 1


def test_the_credit_is_one_rank_up_and_never_reaches_rambo(app):
    with app.app_context():
        assert doors._one_up("public") == "free"
        assert doors._one_up("free") == "pro"
        assert doors._one_up("pro") == doors.REFERRAL_CAP == "pro"
        assert doors._one_up("elite") == "pro"                     # a credit never hands out Rambo


def test_the_credit_runs_out(app):
    now = time.time()          # grants are compared against the clock, so start from it
    with app.app_context():
        doors.attach("99", "ref_" + doors.code_for("88"))
        doors.credit_referrer("99", now=now)
        assert store.effective_tier("88") == "free"
        store.expire_due(now=now + doors.REFERRAL_DAYS * 86400 + 1)
        assert store.effective_tier("88") == "public"


def test_start_with_a_referral_tag_attaches_through_the_bot(app):
    with app.app_context():
        code = doors.code_for("88")
        handle_update(_msg("/start ref_%s" % code, uid=7))
        assert doors.invited_by("7") == "88"


# --- seats (Rambo) ---------------------------------------------------------- #

def test_only_rambo_carries_seats():
    assert tiers.seats_for("public") == 0 and tiers.seats_for("pro") == 0
    assert tiers.seats_for("elite") == 10


def test_a_seat_hands_the_holders_rank_to_someone_else(app):
    with app.app_context():
        store.grant_entitlement("77", "elite", source="manual")
        rows, err = seats.add("77", "555")
        assert not err and len(rows) == 1
        assert store.effective_tier("555") == "elite"
        assert seats.free_seats("77") == 9


def test_a_rank_below_rambo_cannot_seat_anyone(app):
    with app.app_context():
        store.grant_entitlement("77", "pro", source="manual")
        assert seats.add("77", "555")[1] == "st.need"
        assert store.effective_tier("555") == "public"


def test_seats_refuse_duplicates_yourself_and_overflow(app):
    with app.app_context():
        store.grant_entitlement("77", "elite", source="manual")
        seats.add("77", "555")
        assert seats.add("77", "555")[1] == "st.already"
        assert seats.add("77", "77")[1] == "st.self"
        for i in range(9):
            assert seats.add("77", "90%d" % i)[1] is None
        assert seats.add("77", "999")[1] == "st.full"


def test_taking_a_seat_back_drops_that_members_rank(app):
    with app.app_context():
        store.grant_entitlement("77", "elite", source="manual")
        seats.add("77", "555")
        assert seats.remove("77", "555")[1] is None
        assert store.effective_tier("555") == "public"
        assert seats.remove("77", "555")[1] == "st.unknown"


def test_a_seat_cannot_outlive_the_rank_paying_for_it(app):
    now = time.time()          # grants are compared against the clock, so start from it
    with app.app_context():
        store.grant_entitlement("77", "elite", source="stripe", external_id="sub_x",
                                expires_at=now + 30 * 86400)
        seats.add("77", "555")
        assert store.effective_tier("555") == "elite"
        store.expire_due(now=now + 31 * 86400)
        assert store.effective_tier("555") == "public"


def test_sync_drops_the_seats_when_the_holder_falls_off_rambo(app):
    with app.app_context():
        store.grant_entitlement("77", "elite", source="stripe", external_id="sub_x")
        seats.add("77", "555")
        seats.add("77", "556")
        store.revoke_entitlement(external_id="sub_x")
        assert seats.sync("77") == {"kept": 0, "dropped": 2}
        assert store.effective_tier("555") == "public"


def test_the_seats_panel_and_the_bot_agree(client, app):
    with app.app_context():
        store.grant_entitlement("42", "elite", source="manual")
    login(client, user_id="42", admin=False)
    with client.session_transaction() as s:
        user = dict(s["user"]); user["rank"] = "elite"; s["user"] = user
    client.post("/dashboard", data={"seat_action": "add", "member": "555"}, follow_redirects=True)
    with app.app_context():
        assert store.effective_tier("555") == "elite"
        assert "555" in seats.bot_seats([], chat_id="42", lang="ms")


# --- the page --------------------------------------------------------------- #

def test_the_ranks_page_shows_both_free_doors_and_the_annual_saving(client):
    body = client.get("/pricing").get_data(as_text=True)
    assert "Dua pintu percuma" in body
    assert "dua bulan percuma" in body and "$98" in body     # A-Team saves two months
    client.get("/lang/en")
    body = client.get("/pricing").get_data(as_text=True)
    assert "Two free doors" in body and "two months free" in body


def test_a_signed_in_visitor_can_register_an_account_from_the_page(client, app):
    login(client, user_id="42")
    client.post("/pricing", data={"action": "claim", "account": "1234567", "deposit": "600"}, follow_redirects=True)
    with app.app_context():
        assert store.broker_claims_for("42")[0]["account"] == "1234567"
