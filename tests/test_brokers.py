"""#12 Broker Comparator: cost math, ranking, observation blending, bot card, public table, referral card."""

import pytest

from app import brokers, store
from app.telegram import handle_update, reply_for
from tests.conftest import login
from tests.test_bot import msg, tap


def test_cost_per_lot_adds_spread_commission_and_swap_nights():
    row = brokers.SEED["ic markets"]
    c = brokers.cost_per_lot(row, lots=1, nights=0)
    assert c == {"spread": 10.0, "commission": 7.0, "swap": 0.0, "total": 17.0}
    c = brokers.cost_per_lot(row, lots=0.5, nights=3, side="long")
    assert c["swap"] == pytest.approx(33.0) and c["total"] == pytest.approx(5 + 3.5 + 33)
    assert brokers.cost_per_lot(row, lots=1, nights=3, side="short")["swap"] == 0.0     # positive short swap costs nothing


def test_rank_changes_with_holding_period_and_blend_uses_observations():
    intraday = brokers.rank(brokers.blend(brokers.SEED, []), 1, 0)
    assert intraday[0]["name"] == "IC Markets" and intraday[0]["rank"] == 1
    month = brokers.rank(brokers.blend(brokers.SEED, []), 1, 20)
    assert month[0]["name"] == "OctaFX"                                       # swap-free wins over a month
    obs = [{"broker": "exness", "spread": 0.5, "slippage": 0.1}] * 3
    rows = {r["key"]: r for r in brokers.blend(brokers.SEED, obs)}
    assert rows["exness"]["source"] == "observed" and rows["exness"]["spread"] == 0.5 and rows["exness"]["slippage"] == 0.1
    assert rows["hfm"]["source"] == "published"
    assert brokers.blend(brokers.SEED, obs[:2])[0]["source"] == "published"      # two is not enough


def test_parse_holding_and_find():
    assert brokers.parse_holding("overnight") == 1 and brokers.parse_holding("week") == 5 and brokers.parse_holding("3") == 3
    assert brokers.parse_holding("") == 0
    with pytest.raises(ValueError):
        brokers.parse_holding("sometime")
    assert brokers.find("Pepperstone") == "pepperstone" and brokers.find("ic") == "ic markets" and brokers.find("nope") is None


def test_bot_card_ranks_and_carries_the_ib_link(app):
    with app.app_context():
        text = reply_for("/goldspread", chat_id=7, lang="en")
        assert "1. <b>IC Markets</b>" in text and "$17.00" in text and "Sign in on the dashboard" in text
        text = reply_for("/goldspread 1 overnight", chat_id=7, lang="ms")
        assert "1 malam" in text and "swap $" in text
        assert "Guna" in reply_for("/goldspread abc", chat_id=7)
        store.set_setting("broker-comparator", 7, "reflink", "https://b.example/?refid=9")
        assert "https://b.example/?refid=9" in reply_for("/goldspread 0.5 week", chat_id=7, lang="en")
        handle_update(tap("lang_ms"))
        handle_update(tap("run_broker-comparator"))
        handle_update(tap("fl_o:1"))
        done = [a for a in handle_update(tap("fl_o:5")) if a[0] == "send"][-1]
        assert "5 malam" in done[2]


def test_dashboard_table_observations_and_public_card(client):
    body = client.get("/p/broker-comparator?lots=2&nights=1").get_data(as_text=True)
    assert "IC Markets" in body and "Kos 2 lot · 1 malam" in body and "Log masuk untuk lapor" in body
    login(client, "42")
    for _ in range(3):
        client.post("/p/broker-comparator", data={"action": "observe", "broker": "exness", "spread": "0.5", "slippage": "0.1"})
    body = client.get("/p/broker-comparator").get_data(as_text=True)
    assert "diperhatikan (3)" in body
    assert "mesti nombor" in client.post("/p/broker-comparator", data={"action": "observe", "broker": "exness", "spread": "9"}).get_data(as_text=True)
    body = client.post("/p/broker-comparator", data={"action": "reflink", "reflink": "https://b.example/?refid=9", "refname": "Sam"}).get_data(as_text=True)
    assert "/p/broker-comparator/card/" in body
    code = body.split("/p/broker-comparator/card/")[1].split("?")[0].split('"')[0]
    client.get("/lang/en")
    card = client.get("/p/broker-comparator/card/%s?lots=1&nights=0" % code).get_data(as_text=True)
    assert "compiled by Sam" in card and 'href="https://b.example/?refid=9"' in card and "IC Markets" in card
    assert client.get("/p/broker-comparator/card/nope").status_code == 404
