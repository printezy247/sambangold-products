"""#16 Overexposure Monitor: leg decomposition, clustering, flags, heat-map, costs, both surfaces, warn toggle."""

import pytest

from app import exposure, store, telegram
from app.telegram import reply_for
from tests.conftest import login


def test_parse_positions_accepts_loose_input():
    ps = exposure.parse_positions("gold buy 1; eur/usd b 0.5\nUSDJPY.m short 1")
    assert [(p["symbol"], p["side"], p["lots"]) for p in ps] == [("XAUUSD", "buy", 1.0), ("EURUSD", "buy", 0.5), ("USDJPY", "sell", 1.0)]
    assert ps[0]["base"] == "XAU" and ps[1]["quote"] == "USD"
    for bad in ("EURUSD buy", "EURUSD hold 1", "EURUSD buy x", ""):
        with pytest.raises(ValueError):
            exposure.parse_positions(bad)


def test_sample_book_is_one_usd_bet_and_a_hedge_is_not():
    r = exposure.analyse(exposure.parse_positions(exposure.SAMPLE), balance=10000)
    assert r["state"] == "over" and set(r["flags"]) == {"concentration", "stack", "leverage"}
    assert r["biggest"]["factor"] == "USD" and r["concentration"] == 1.0 and len(r["stack"]["symbols"]) == 5
    assert all(v == 1 for row in r["matrix"] for v in row)
    assert r["true_risk"] == r["gross"] and r["leverage"] == 79.0
    hedge = exposure.analyse(exposure.parse_positions("EURUSD buy 1\nEURUSD sell 1"))
    assert hedge["true_risk"] == 0 and hedge["matrix"][0][1] == -1 and hedge["state"] == "ok"
    spread = exposure.analyse(exposure.parse_positions("EURUSD buy 1\nUSDJPY buy 1"))     # long EUR, long JPY-short... USD nets out
    assert spread["factors"]["USD"] == 0 and spread["state"] == "ok"
    assert r["costs"][0]["spread"] == 20.0 and r["costs"][0]["swap_week"] == -90.0 and r["spread_total"] > 0


def test_bot_snapshot_last_and_warn_toggle_pushes(app, monkeypatch):
    sent = []
    monkeypatch.setattr(telegram, "send_message", lambda chat_id, text, **k: sent.append(text))
    with app.app_context():
        assert "Belum ada snapshot" in reply_for("/exposure", chat_id=7)
        assert "tak difahami" in reply_for("/exposure EURUSD hold 1", chat_id=7)
        text = reply_for("/exposure XAUUSD buy 1, EURUSD buy 1, GBPUSD buy 0.5, USDJPY sell 1", chat_id=7, lang="en")
        assert "Overexposed" in text and "4 positions ride the same factor (USD)" in text and not sent
        assert "ON" in reply_for("/exposure warn", chat_id=7, lang="en")
        reply_for("/exposure XAUUSD buy 1, EURUSD buy 1, GBPUSD buy 0.5", chat_id=7, lang="ms")
        assert sent and "Terlebih dedah" in sent[-1]
        assert "Terlebih dedah" in reply_for("/exposure", chat_id=7)              # last snapshot remembered
        assert "MATI" in reply_for("/exposure warn", chat_id=7)


def test_dashboard_sample_heatmap_and_memory(client, monkeypatch):
    monkeypatch.setattr(telegram, "send_message", lambda *a, **k: None)
    body = client.post("/p/exposure-monitor", data={"action": "sample"}).get_data(as_text=True)
    assert "Terlebih dedah" in body and "Peta haba" in body and body.count("+1") >= 20 and "Log masuk" in body
    assert "tak difahami" in client.post("/p/exposure-monitor", data={"action": "run", "positions": "EURUSD 1"}).get_data(as_text=True)
    login(client, "42")
    client.post("/p/exposure-monitor", data={"action": "run", "positions": "EURUSD buy 1\nEURUSD sell 1", "balance": "50000"})
    body = client.get("/p/exposure-monitor").get_data(as_text=True)
    assert "Tersebar" in body and "EURUSD sell 1" in body
    assert "Matikan amaran" in client.post("/p/exposure-monitor", data={"action": "warn"}).get_data(as_text=True)
