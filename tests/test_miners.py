"""#18 Miner–Bullion Divergence Screener: beta maths, residual flags, margin, earnings, both surfaces, Monday digest."""

import datetime as dt

import pytest

from app import miners, minerstool, store, watch
from app.telegram import reply_for
from tests.conftest import login

TODAY = dt.date(2026, 9, 15)


def test_beta_and_residuals_recover_the_synthetic_profile():
    s = miners.screen(miners.history(), TODAY)
    by = {r["ticker"]: r for r in s["rows"]}
    assert len(s["rows"]) == len(miners.UNIVERSE) and s["week"] == "2026-W38" and s["spot"] > 2400
    assert by["GDX"]["beta"] == 2.0 and by["GDX"]["corr"] == 1.0 and abs(by["GDX"]["residual"]) < 0.5 and by["GDX"]["flags"] == []
    assert by["FNV"]["beta"] == 0.8 and by["FNV"]["margin"] is None
    assert by["HMY"]["residual"] >= 5 and "leading" in by["HMY"]["flags"]
    assert by["B"]["residual"] <= -5 and "lagging" in by["B"]["flags"]
    assert s["rows"][0]["ticker"] in ("HMY", "B")                     # sorted by |residual|
    nem = by["NEM"]
    assert nem["margin"] == round(nem["spot"] - 1650) and nem["margin_pct"] > 20 and "squeeze" not in nem["flags"]
    assert nem["earnings"] == "2026-10-22" and nem["earnings_in"] == 37 and "earnings" not in nem["flags"]
    near = miners.screen(miners.history(), dt.date(2026, 10, 15))
    assert "earnings" in {r["ticker"]: r for r in near["rows"]}["NEM"]["flags"]
    assert len(nem["chart"]) == 130 and nem["chart"][0][1] == 100.0


def test_beta_edge_cases_and_sorting():
    assert miners.beta([1, 2, 3], [1, 2, 3]) == (None, None)
    assert miners.beta([0.01] * 6, [0.02] * 6) == (None, None)
    b, c = miners.beta([0.01, -0.01, 0.02, -0.02, 0.005, -0.005], [0.02, -0.02, 0.04, -0.04, 0.01, -0.01])
    assert b == 2.0 and c == 1.0
    rows = miners.screen(miners.history(), TODAY)["rows"]
    assert [r["ticker"] for r in miners.sort_rows(rows, "ticker")][:3] == ["AEM", "AGI", "AU"]
    assert miners.sort_rows(rows, "beta")[0]["ticker"] == "GDXJ"
    assert miners.sort_rows(rows, "margin")[0]["ticker"] == "HMY"          # highest AISC → thinnest margin first
    assert miners.sort_rows(rows, "earnings")[0]["ticker"] == "NEM"
    assert miners.analyse_name(miners.UNIVERSE[0], [(0, 1.0)] * 10, [(0, 1.0)] * 10) is None


def test_squeeze_flag_when_gold_falls_toward_aisc(fake_miners):
    hist = {k: (list(v) if isinstance(v, list) else v) for k, v in fake_miners.items()}
    hist[miners.GOLD] = [(ts, c * 0.8) for ts, c in hist[miners.GOLD]]           # spot ≈ 2,100 → HMY at 1,850 is thin
    s = miners.screen(hist, TODAY)
    hmy = {r["ticker"]: r for r in s["rows"]}["HMY"]
    assert hmy["margin_pct"] < 20 and "squeeze" in hmy["flags"]


def test_fetch_history_drops_dead_tickers_and_raises_without_gold(monkeypatch):
    from tests.conftest import REAL_MINER_FETCH

    def closes(sym):
        if sym == "KGC":
            raise ConnectionError("down")
        return [(i * 86400, 100.0 + i) for i in range(30)]
    monkeypatch.setattr(miners, "_closes", closes)
    hist = REAL_MINER_FETCH()
    assert "KGC" not in hist and hist["errors"] == ["KGC: down"] and len(hist["NEM"]) == 30
    monkeypatch.setattr(miners, "_closes", lambda sym: (_ for _ in ()).throw(ConnectionError("down")))
    with pytest.raises(miners.FeedError):
        REAL_MINER_FETCH()


def test_bot_digest_single_name_and_weekly_toggle(app):
    with app.app_context():
        text = reply_for("/miners", chat_id=7, lang="en")
        assert "Miners vs gold" in text and "residual" in text and text.count("<code>") == minerstool.DIGEST_N and "🚀" in text and "🐢" in text
        ms = reply_for("/miners", chat_id=7)
        assert "Pelombong vs emas" in ms and "soalan, bukan isyarat" in ms
        one = reply_for("/miners nem", chat_id=7, lang="en")
        assert "Newmont" in one and "β to gold (6 months) <b>1.50</b>" in one and "AISC $1,650/oz (Q2 2026)" in one and "2026-10-22" in one
        assert "ETF: no AISC" in reply_for("/miners $GDX", chat_id=7, lang="en")
        assert "Royalty/streaming" in reply_for("/miners FNV", chat_id=7, lang="en")
        assert "tiada dalam universe" in reply_for("/miners XYZ", chat_id=7)
        assert "HIDUP" in reply_for("/miners weekly", chat_id=7)
        assert store.get_setting("miner-divergence", 7, "weekly") == "on"
        assert "MATI" in reply_for("/miners weekly", chat_id=7)
        assert "Guna:" in reply_for("/miners weekly")                    # no chat → usage


def test_bot_reports_a_dead_feed(app, monkeypatch):
    monkeypatch.setattr(miners, "fetch_history", lambda: (_ for _ in ()).throw(miners.FeedError("gold history empty")))
    miners.clear_cache()
    with app.app_context():
        assert "tak tersedia" in reply_for("/miners", chat_id=7)
        assert "tak tersedia" in reply_for("/miners NEM", chat_id=7)


def test_monday_digest_pushes_once_per_week(app):
    sent = []
    send = lambda cid, text: sent.append((cid, text))
    with app.app_context():
        reply_for("/miners weekly", chat_id=7)
        reply_for("/miners weekly", chat_id=9, lang="en")
        assert minerstool.check_weekly(send, today=dt.date(2026, 9, 15)) == 0          # Tuesday
        assert minerstool.check_weekly(send, today=dt.date(2026, 9, 14)) == 2          # Monday
        assert {c for c, _ in sent} == {"7", "9"} and "Pelombong" in sent[0][1]
        assert minerstool.check_weekly(send, today=dt.date(2026, 9, 14)) == 0          # same week: no repeat
        assert minerstool.check_weekly(send, today=dt.date(2026, 9, 21)) == 2          # next Monday
        result = watch.check_alerts(send)                                              # the checker hook never raises
        assert "pushed" in result


def test_dashboard_table_sort_detail_and_toggle(client):
    body = client.get("/p/miner-divergence").get_data(as_text=True)
    assert "Saringan pelombong" in body and body.count("<tr>") >= len(miners.UNIVERSE) and "Log masuk" in body and "Q2 2026" in body
    assert "<polyline" not in body
    body = client.get("/p/miner-divergence?sort=ticker").get_data(as_text=True)
    assert body.index("<b>AEM</b>") < body.index("<b>NEM</b>")
    body = client.get("/p/miner-divergence?ticker=NEM").get_data(as_text=True)
    assert "<polyline" in body and "Newmont" in body and "AISC $1,650" in body and "2026-10-22" in body
    login(client, "42")
    body = client.post("/p/miner-divergence", data={"action": "weekly"}).get_data(as_text=True)
    assert "Matikan digest" in body
    client.get("/lang/en")
    assert "Miners vs gold screen" in client.get("/p/miner-divergence").get_data(as_text=True)
