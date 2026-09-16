"""#1 Gold Watch: feed, spread-aware crossing, bot commands, checker, dashboard."""

import pytest

from app import feeds, store, watch
from app.telegram import reply_for
from tests.conftest import login


def test_spread_aware_crossing():
    q = {"bid": 2399.5, "ask": 2400.5}
    assert feeds.crossed("above", 2400.5, q)
    assert not feeds.crossed("above", 2400.6, q)      # mid would say yes; the ask says no
    assert feeds.crossed("below", 2399.5, q)
    assert not feeds.crossed("below", 2399.4, q)


def test_spread_bps_handles_no_book():
    assert feeds.spread_bps({"spread": None, "mid": 2400}) is None
    assert round(feeds.spread_bps({"spread": 1.0, "mid": 2400}), 3) == round(1 / 2400 * 1e4, 3)


REAL_FETCH = feeds.fetch  # captured at import, before the autouse fixture patches it


def test_feed_falls_back_and_then_raises(monkeypatch):
    def boom():
        raise ConnectionError("down")
    monkeypatch.setattr(feeds, "_binance", boom)
    monkeypatch.setattr(feeds, "_yahoo", lambda: {"source": "Yahoo GC=F"})
    assert REAL_FETCH()["source"] == "Yahoo GC=F"
    monkeypatch.setattr(feeds, "_yahoo", boom)
    with pytest.raises(feeds.FeedError):
        REAL_FETCH()


def test_watch_price_reply(app):
    with app.app_context():
        reply = reply_for("/watch XAUUSD", chat_id=7, lang="en")
    assert "2,400.00" in reply and "bid 2,399.50" in reply and "ask 2,400.50" in reply
    assert "Long: enter 2,400.50" in reply


def test_watch_usage_and_unknown_pair(app):
    with app.app_context():
        assert "Usage" in reply_for("/watch", chat_id=7, lang="en")
        assert "Only gold" in reply_for("/watch EURUSD", chat_id=7, lang="en")
        assert "Usage" in reply_for("/watch XAUUSD sideways 5", chat_id=7, lang="en")
        assert "must be a number" in reply_for("/watch XAUUSD above x", chat_id=7, lang="en")


def test_watch_arm_list_clear_round_trip(app):
    with app.app_context():
        store.grant_entitlement("7", "free", source="manual")    # arming is what General buys
        assert "Alert #1 armed" in reply_for("/watch XAUUSD above 2450", chat_id=7, lang="en")
        assert "#2 armed" in reply_for("/watch gold below 2380", chat_id=7, lang="en")
        listing = reply_for("/watch list", chat_id=7, lang="en")
        assert "above 2,450.00" in listing and "below 2,380.00" in listing
        assert "No alerts" in reply_for("/watch list", chat_id=8, lang="en")  # other chat sees nothing
        assert "Cleared 2" in reply_for("/watch clear", chat_id=7, lang="en")
        assert "No alerts" in reply_for("/watch list", chat_id=7, lang="en")


def test_checker_fires_on_the_traded_side_and_records(app, fake_feed):
    sent = []
    with app.app_context():
        store.add_alert(7, "XAUUSD", "above", 2400.5)   # ask is exactly 2400.5 → fires
        store.add_alert(7, "XAUUSD", "above", 2400.6)   # not yet
        store.add_alert(9, "XAUUSD", "below", 2399.4)   # bid 2399.5 → not yet
        result = watch.check_alerts(lambda cid, text: sent.append((cid, text)))
        assert result == {"checked": 3, "fired": 1, "source": "test feed", "pushed": 0,
                          "brief_sent": 0, "brief_gated": 0}
        assert sent[0][0] == "7" and "2,400.50" in sent[0][1]
        assert [a["level"] for a in store.active_alerts()] == [2400.6, 2399.4]
        hist = store.triggers_for(7)
        assert len(hist) == 1 and hist[0]["price"] == 2400.5 and hist[0]["spread"] == 1.0

        fake_feed["bid"] = 2390.0
        fake_feed["ask"] = 2391.0
        result = watch.check_alerts(lambda cid, text: sent.append((cid, text)))
        assert result["fired"] == 1 and sent[-1][0] == "9"


def test_task_endpoint_requires_token(client):
    assert client.post("/tasks/check-alerts").status_code == 403
    assert client.post("/tasks/check-alerts", headers={"X-Task-Token": "wrong"}).status_code == 403
    ok = client.post("/tasks/check-alerts", headers={"X-Task-Token": "test-task-token"})
    assert ok.status_code == 200 and ok.get_json() == {"checked": 0, "fired": 0, "pushed": 0,
                                                      "brief_sent": 0, "brief_gated": 0}


def test_cli_check_alerts(app):
    result = app.test_cli_runner().invoke(args=["check-alerts"])
    assert result.exit_code == 0 and "checked" in result.output


def test_dashboard_shows_price_without_login(client):
    body = client.get("/p/gold-watch").get_data(as_text=True)
    assert "2,400.00" in body and "Log masuk dengan Telegram" in body


def test_dashboard_arm_edit_disarm_export_share_the_bot_list(app, client):
    login(client, "42", rank="free")   # arming and history are what General buys
    body = client.post("/p/gold-watch", data={"action": "arm", "direction": "above", "level": "2450"}).get_data(as_text=True)
    assert "Alert #1 dipasang" in body and "2450" in body

    with app.app_context():                       # the bot sees the same alert
        assert "above 2,450.00" in reply_for("/watch list", chat_id="42", lang="en")

    body = client.post("/p/gold-watch", data={"action": "update", "id": "1", "level": "2460"}).get_data(as_text=True)
    assert "Paras dikemas kini" in body and 'value="2460"' in body

    with app.app_context():
        assert store.update_alert("999", 1, level=1) == 0   # another owner cannot touch it
        fake = {"bid": 2465, "ask": 2466, "mid": 2465.5, "spread": 1.0, "source": "test feed", "symbol": "XAUUSD", "at": 0}
        store.record_trigger(store.alerts_for("42")[0], fake)

    body = client.get("/p/gold-watch").get_data(as_text=True)
    assert "2,466.00" in body and "Eksport sejarah" in body

    csv_body = client.get("/p/gold-watch/history.csv")
    assert csv_body.status_code == 200 and csv_body.mimetype == "text/csv"
    assert "above,2460.0,2466" in csv_body.get_data(as_text=True)

    client.post("/p/gold-watch", data={"action": "arm", "direction": "below", "level": "2300"})
    body = client.post("/p/gold-watch", data={"action": "disarm", "id": "2"}).get_data(as_text=True)
    assert "Alert dibuang" in body


def test_csv_export_needs_login(client):
    assert client.get("/p/gold-watch/history.csv").status_code == 302
