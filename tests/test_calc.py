"""The math behind #3 and #8, and the handler tables that expose it."""

import pytest

from app import calc, tools
from app.products import BY_SLUG, command_index
from app.telegram import reply_for


# --- #3 prop EV ----------------------------------------------------------- #

def test_prop_ev_matches_hand_calculation():
    r = calc.prop_ev(500, 100000, 15)
    assert r["first_payout"] == 100000 * 0.08 * 0.80 == 6400
    assert r["ev"] == pytest.approx(0.15 * 6400 - 500)
    assert r["breakeven_pass_rate"] == pytest.approx(500 / 6400)
    assert r["verdict"] == "positive"


def test_prop_ev_counts_resets_in_the_cost():
    r = calc.prop_ev(500, 100000, 5, resets=2)
    assert r["total_cost"] == 1500
    assert r["verdict"] == "negative"


def test_prop_ev_accepts_human_formatting():
    assert calc.prop_ev("$1,000", "200,000", "15%")["fee"] == 1000


@pytest.mark.parametrize("bad", [("x", 1, 1), (500, 0, 10), (500, 1000, 150), (-1, 1000, 10)])
def test_prop_ev_rejects_bad_input(bad):
    with pytest.raises(calc.InputError):
        calc.prop_ev(*bad)


def test_scan_terms_orders_red_before_yellow():
    text = ("Positions must be closed before the weekend. "
            "A trailing maximum drawdown of 10% applies. Fees are non-refundable.")
    s = calc.scan_terms(text)
    assert s["reds"] == 2 and s["yellows"] == 1 and s["grade"] == "red"
    assert [f["flag"] for f in s["flags"]] == ["red", "red", "yellow"]
    assert all(f["snippet"] for f in s["flags"])


def test_scan_terms_is_green_on_nothing():
    assert calc.scan_terms("")["grade"] == "green"
    assert calc.scan_terms("Enjoy your challenge.")["flags"] == []


# --- #8 IB revenue -------------------------------------------------------- #

def test_ib_revenue_matches_hand_calculation():
    r = calc.ib_revenue(40, 7, clients=25, clawback_pct=5, compliance_cost=150)
    assert r["gross"] == 7000
    assert r["clawback"] == 350
    assert r["net"] == 6500
    assert r["annual"] == 78000
    assert len(r["timeline"]) == 12


def test_ib_timeline_holds_until_threshold_then_pays():
    r = calc.ib_revenue(10, 5, payout_threshold=120, hold_days=30)  # $50 a month
    paid = [m["paid"] for m in r["timeline"]]
    assert paid[:3] == [0, 0, 150]
    assert r["first_cash_days"] == 3 * 30 + 30
    assert r["timeline"][-1]["cumulative"] == sum(paid)


def test_ib_never_pays_when_net_is_negative():
    r = calc.ib_revenue(1, 1, compliance_cost=500)
    assert r["net"] < 0 and r["first_cash_days"] is None


def test_ib_checklist_is_complete_plain_text():
    text = calc.ib_checklist_text()
    for section, items in calc.IB_CHECKLIST:
        assert "## %s" % section in text
        for item in items:
            assert "- [ ] %s" % item in text


# --- the handler tables are part of the surface contract ------------------ #

def test_every_live_product_is_live_on_both_surfaces():
    """A word in BOT must map to a product whose slug is in DASHBOARD, and back."""
    index = command_index()
    bot_slugs = {index[word].slug for word in tools.BOT}
    assert set(tools.BOT) <= set(index), "bot handler for an unregistered command"
    assert bot_slugs == set(tools.DASHBOARD)
    for slug in tools.DASHBOARD:
        assert BY_SLUG[slug].status == "shipped"


def test_bot_propcalc_answers_with_numbers_and_usage():
    assert "$460" in reply_for("/propcalc 500 100000 15")
    assert "7.8%" in reply_for("/propcalc 500 100000 15")
    assert "Guna" in reply_for("/propcalc") and "Usage" in reply_for("/propcalc", lang="en")
    assert "Guna" in reply_for("/propcalc a b c")


def test_bot_ibcalc_answers_with_numbers_and_usage():
    reply = reply_for("/ibcalc 40 7 25 5")
    assert "$6,650" in reply and "$79,800" in reply
    assert "Guna" in reply_for("/ibcalc 40")
