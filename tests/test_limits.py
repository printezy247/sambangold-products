"""Rank-aware caps: the same tool, more of it.

Every number here was already a hard free cap before the ladder existed. What
these tests pin is that a rank *raises* a cap and never closes a door: the
public numbers are unchanged from what they were, and nothing new is gated.
"""

from app import gate, links, mc, sentinel, store, tiers
from app.linktool import create_link
from app.sentineltool import link_account

from tests.conftest import login


def test_public_caps_are_the_old_free_caps():
    """A visitor who never signs in must not lose anything to the ladder."""
    assert tiers.limit_for("links", "public") == links.FREE_LINKS
    assert tiers.limit_for("accounts", "public") == sentinel.FREE_ACCOUNTS
    assert tiers.limit_for("sims", "public") == mc.FREE_SIMS
    assert tiers.limit_for("links", "free") == links.FREE_LINKS


def test_caps_only_ever_rise_up_the_ladder():
    for key in tiers.LIMITS:
        seen = [tiers.limit_for(key, t.key) for t in tiers.TIERS]
        for lower, higher in zip(seen, seen[1:]):
            assert higher == 0 or higher >= lower, key      # 0 is unlimited


def test_limit_reads_the_rank_from_whichever_identity_it_is_given(app):
    with app.app_context():
        assert gate.limit("sims", chat_id="77") == mc.FREE_SIMS
        store.grant_entitlement("77", "pro", source="manual")
        assert gate.limit("sims", chat_id="77") == 100000
        assert gate.limit("sims", owner="77") == 100000
        assert gate.limit("sims", user={"rank": "elite"}) == 100000
        assert gate.limit("clients", user={"rank": "elite"}) == 0     # unlimited


def test_limit_is_public_outside_a_request(app):
    """A background job has no session and must not inherit anyone's rank."""
    with app.app_context():
        assert gate.limit("sims") == mc.FREE_SIMS


def test_within_treats_zero_as_unlimited(app):
    with app.app_context():
        assert gate.within("links", 2, user={"rank": "free"})
        assert not gate.within("links", 3, user={"rank": "free"})
        assert gate.within("links", 10_000, user={"rank": "elite"})


def test_a_team_may_track_more_links_than_general(app):
    with app.app_context():
        for i in range(links.FREE_LINKS):
            row, err = create_link("77", "ch%d" % i, "https://example.com", cap=links.FREE_LINKS)
            assert row and not err
        _, err = create_link("77", "one-too-many", "https://example.com", cap=links.FREE_LINKS)
        assert err == "lk.limit"
        row, err = create_link("77", "one-too-many", "https://example.com", cap=50)
        assert row and not err


def test_a_team_may_link_more_prop_accounts(app):
    with app.app_context():
        acc, err = link_account("77", "A", "FTMO", 100000, cap=1)
        assert acc and not err
        _, err = link_account("77", "B", "FTMO", 100000, cap=1)
        assert err == "sn.limit"
        acc, err = link_account("77", "B", "FTMO", 100000, cap=10)
        assert acc and not err


def test_the_simulator_runs_more_paths_for_a_paid_rank():
    free = mc.run(55, 2, 1, "ftmo", 10, 500, 3, sims=100000, cap=mc.FREE_SIMS)
    assert free["inputs"]["sims"] == mc.FREE_SIMS
    paid = mc.run(55, 2, 1, "ftmo", 10, 500, 3, sims=5000, cap=100000)
    assert paid["inputs"]["sims"] == 5000


def test_the_ranks_page_publishes_every_cap(client):
    body = client.get("/pricing").get_data(as_text=True)
    assert "Berapa banyak" in body and "100,000" in body and "∞" in body
    client.get("/lang/en")
    body = client.get("/pricing").get_data(as_text=True)
    for label in ("Linked prop accounts", "Tracked links", "Monte Carlo paths", "Rows per batch"):
        assert label in body


def test_batch_verify_rows_follow_the_rank(client, app):
    login(client, user_id="42")
    body = client.get("/p/signal-verifier").get_data(as_text=True)
    assert str(tiers.limit_for("batch_rows", "free")) in body
