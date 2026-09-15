"""#11 Churn Radar: log parsing, the four signals, ranking by revenue at risk, both surfaces, intervention log."""

import datetime as dt

import pytest

from app import churn, store
from app.telegram import reply_for
from tests.conftest import login


def test_parse_log_accepts_loose_headers_and_dates():
    rows = churn.parse_log("Login;Close Time;Instrument;Volume;Profit\n7;2026.09.01 10:00:00;xauusd;1,5;-20\n7;02/09/2026;XAUUSD;2;30\n")
    assert [r["at"] for r in rows] == [dt.date(2026, 9, 1), dt.date(2026, 9, 2)] and rows[0]["symbol"] == "XAUUSD"
    with pytest.raises(churn.InputError):
        churn.parse_log("account,lots\n1,2\n")
    with pytest.raises(churn.InputError):
        churn.parse_log("account,date,lots\n1,yesterday,2\n")


def test_sample_book_scores_each_archetype():
    book = churn.scan_book(churn.parse_log(churn.sample_log()))
    by = {c["account"]: c for c in book["clients"]}
    assert by["2001"]["band"] == "healthy" and by["2001"]["flags"] == []
    assert "decay" in by["2002"]["flags"] and by["2002"]["decay"] >= 70
    assert by["2003"]["band"] == "risk" and by["2003"]["dormancy"] == 100
    assert by["2004"]["martingale"] == 100 and by["2004"]["band"] != "healthy"
    assert by["2005"]["stress"] >= 50 and by["2005"]["worst_streak"] == 9
    assert book["clients"][0]["at_risk"] >= book["clients"][-1]["at_risk"]      # ranked by revenue at risk
    s = book["summary"]
    assert s["clients"] == 5 and s["risk"] + s["watch"] + s["healthy"] == 5 and s["as_of"] == "2026-09-13"


def test_signals_without_profit_column_still_score_volume_and_dormancy():
    rows = churn.parse_log("account,date,lots\n1,2026-08-01,2\n1,2026-08-10,2\n1,2026-08-20,2\n2,2026-09-10,1\n")
    book = churn.scan_book(rows, as_of=dt.date(2026, 9, 13))
    by = {c["account"]: c for c in book["clients"]}
    assert by["1"]["martingale"] == 0 and by["1"]["stress"] == 0 and by["1"]["dormancy"] >= 60 and by["1"]["decay"] == 50
    assert by["2"]["band"] == "healthy"


def test_bot_lists_who_to_call_and_details_one_client(app):
    with app.app_context():
        assert "Belum ada larian" in reply_for("/ibchurn", chat_id=7)
        book = churn.scan_book(churn.parse_log(churn.sample_log()))
        store.save_run("churn-radar", book, owner=7, label="2026-09-13", metric=book["summary"]["at_risk"])
        top = reply_for("/ibchurn", chat_id=7, lang="en")
        assert "Call first" in top and "<code>2003</code>" in top and "dormant" in top
        detail = reply_for("/ibchurn 2004", chat_id=7, lang="ms")
        assert "Klien 2004" in detail and "Martingale 100%" in detail and "lot tetap" in detail
        assert "tiada dalam larian" in reply_for("/ibchurn 9999", chat_id=7, lang="ms")


def test_dashboard_sample_detail_notes_and_free_cap(client):
    body = client.post("/p/churn-radar", data={"action": "sample"}).get_data(as_text=True)
    assert "Buku klien" in body and "2003" in body and "?account=2003" in body
    assert "Log trade:" in client.post("/p/churn-radar", data={"action": "run", "log": "x"}).get_data(as_text=True)
    login(client, "42")
    client.post("/p/churn-radar", data={"action": "sample"})
    page = client.get("/p/churn-radar?account=2004").get_data(as_text=True)      # last run is remembered
    assert "Butiran klien" in page and "martingale" in page.lower() and "Belum ada nota" in page
    page = client.post("/p/churn-radar", data={"action": "note", "account": "2004", "note": "Telefon, cadang lot tetap"}).get_data(as_text=True)
    assert "Telefon, cadang lot tetap" in page and "Larian sebelum ini" in page
    big = "account,date,lots\n" + "\n".join("%d,2026-09-%02d,1" % (100 + i, 1 + i % 12) for i in range(14)) + "\n"
    page = client.post("/p/churn-radar", data={"action": "run", "log": big}).get_data(as_text=True)
    assert "4 lagi dalam larian ini" in page
