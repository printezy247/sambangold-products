"""#14 Drawdown Sentinel: rule packs, distance-to-breach, transitions and pushes, bot, ping, dashboard."""

from app import sentinel, sentineltool, store, telegram
from app.telegram import handle_update, reply_for
from tests.conftest import login
from tests.test_bot import tap


def test_evaluate_static_and_trailing_packs():
    acc = {"initial_balance": 100000, "day_start_balance": 100000, "equity": 96000, "peak_equity": 101000,
           "open_lots": 2, "started": "2026-09-10", "day": "2026-09-15"}
    ev = sentinel.evaluate(acc, sentinel.PACKS["ftmo"])
    by = {r["key"]: r for r in ev["rules"]}
    assert by["daily"]["line"] == 95000 and by["daily"]["room"] == 1000 and by["daily"]["state"] == "warn"
    assert by["max"]["line"] == 90000 and by["max"]["state"] == "ok" and ev["state"] == "warn" and ev["days_done"] == 5
    ev = sentinel.evaluate(acc, sentinel.PACKS["myfundedfx"])          # trailing 8 % from the 101k peak
    assert {r["key"]: r for r in ev["rules"]}["max"]["line"] == 92920.0
    ev = sentinel.evaluate(dict(acc, day_start_balance=93600, equity=93500), sentinel.PACKS["myfundedfx"])
    assert ev["state"] == "warn"                                        # trailing line 92,920: 580 of 8,080 left
    ev = sentinel.evaluate(dict(acc, equity=92000), sentinel.PACKS["myfundedfx"])
    assert ev["state"] == "breach"
    pack = sentinel.custom_pack(4, 8, max_lot=5)
    ev = sentinel.evaluate(dict(acc, equity=99000, open_lots=4.5), pack)
    assert {r["key"]: r for r in ev["rules"]}["lot"]["state"] == "warn"
    assert sentinel.find_pack("FTMO") == "ftmo" and sentinel.find_pack("funded next") == "fundednext" and sentinel.find_pack("x") is None


def test_bot_links_reports_and_pushes_on_transition(app, monkeypatch):
    sent = []
    monkeypatch.setattr(telegram, "send_message", lambda chat_id, text, **k: sent.append((chat_id, text)))
    with app.app_context():
        assert "Belum ada akaun" in reply_for("/sentinel", chat_id=7)
        assert "Firm tak dikenali" in reply_for("/sentinel link Cabaran1 nope 100000", chat_id=7)
        text = reply_for("/sentinel link Cabaran1 ftmo 100000", chat_id=7, lang="en")
        assert "linked" in text and "/p/drawdown-sentinel/ping/" in text and "daily loss 5.0%" in text
        assert "Free tier" in reply_for("/sentinel link Two ftmo 50000", chat_id=7, lang="en")
        status = reply_for("/sentinel status", chat_id=7, lang="en")
        assert "🟢" in status and "line $95,000" in status
        reply_for("/sentinel equity 95800", chat_id=7, lang="en")
        assert sent and "⚠️" in sent[-1][1] and "daily loss" in sent[-1][1]
        reply_for("/sentinel equity 94000", chat_id=7, lang="ms")
        assert "🚨" in sent[-1][1] and "DILANGGAR" in sent[-1][1]
        n = len(sent)
        reply_for("/sentinel equity 93900", chat_id=7)                    # still breached: no second push
        assert len(sent) == n
        reply_for("/sentinel equity 99000", chat_id=7, lang="en")
        assert "✅" in sent[-1][1]
        assert "switched to <b>E8 Markets</b>" in reply_for("/sentinel firm e8", chat_id=7, lang="en")
        assert "reset" in reply_for("/sentinel newday", chat_id=7, lang="en")
        acc = store.sentinels_for(7)[0]
        assert acc["day_start_balance"] == 99000 and [h["state"] for h in store.sentinel_history(acc["id"])] == ["ok", "breach", "breach", "warn"]


def test_ping_endpoint_and_dashboard(app, client, monkeypatch):
    monkeypatch.setattr(telegram, "send_message", lambda *a, **k: None)
    assert "Log masuk" in client.get("/p/drawdown-sentinel").get_data(as_text=True)
    login(client, "42")
    body = client.post("/p/drawdown-sentinel", data={"action": "link", "name": "Cabaran1", "firm": "fundednext", "balance": "50000"}).get_data(as_text=True)
    assert "Cabaran1" in body and "/p/drawdown-sentinel/ping/" in body and "selamat" in body
    with app.app_context():
        token = store.sentinels_for("42")[0]["token"]
    r = client.get("/p/drawdown-sentinel/ping/%s?equity=47600&lots=1.5" % token)
    assert r.status_code == 200 and r.get_json()["state"] == "warn"
    assert client.get("/p/drawdown-sentinel/ping/%s" % token).status_code == 400
    assert client.get("/p/drawdown-sentinel/ping/nope?equity=1").status_code == 404
    body = client.get("/p/drawdown-sentinel").get_data(as_text=True)
    assert "hampir" in body and "47,600" in body
    body = client.post("/p/drawdown-sentinel", data={"action": "update", "id": 1, "equity": "44000"}).get_data(as_text=True)
    assert "dilanggar" in body
    body = client.post("/p/drawdown-sentinel", data={"action": "delete", "id": 1}).get_data(as_text=True)
    assert "🔴 Cabaran1" not in body and "Belum ada rekod" not in body


def test_flow_links_an_account(app):
    with app.app_context():
        handle_update(tap("lang_ms"))
        handle_update(tap("run_drawdown-sentinel"))
        from tests.test_bot import msg
        handle_update(msg("Akaun Satu"))
        handle_update(tap("fl_o:ftmo"))
        done = [a for a in handle_update(tap("fl_o:100000")) if a[0] == "send"][-1]
        assert "dipautkan" in done[2] and store.sentinels_for(7)[0]["name"] == "Akaun_Satu"
