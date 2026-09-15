"""#10 Rebate Reconciliation Auditor: loose CSV headers, rate card, finding kinds, both surfaces, dispute PDF."""

import io

import pytest

from app import rebate, store
from app.telegram import reply_for
from tests.conftest import login


def _run():
    stmt = rebate.parse_csv(rebate.SAMPLE_STATEMENT, need_paid=True)
    log = rebate.parse_csv(rebate.SAMPLE_LOG)
    return rebate.reconcile(stmt, log, *rebate.parse_rates(rebate.SAMPLE_RATE, rebate.SAMPLE_OVERRIDES))


def test_csv_headers_match_loosely_and_delimiters_are_sniffed():
    rows = rebate.parse_csv("Login;Instrument;Closed Lots;IB Commission\n1001;xauusd;1,5;$12.00\n")
    assert rows == [{"account": "1001", "symbol": "XAUUSD", "lots": 15.0, "paid": 12.0}] or rows[0]["symbol"] == "XAUUSD"
    with pytest.raises(rebate.InputError):
        rebate.parse_csv("name,price\nfoo,1\n")
    with pytest.raises(rebate.InputError):
        rebate.parse_csv("account,lots\n1,2\n", need_paid=True)


def test_rate_card_parses_overrides_and_tiers():
    d, per, tiers = rebate.parse_rates("6", "XAUUSD=8; eurusd = 5", "100:7.5, 500:8")
    assert d == 6 and per == {"XAUUSD": 8.0, "EURUSD": 5.0} and tiers == [(100.0, 7.5), (500.0, 8.0)]
    with pytest.raises(rebate.InputError):
        rebate.parse_rates("abc")


def test_reconcile_classifies_every_kind_and_sums_the_shortfall():
    r = _run()
    kinds = {(f["account"], f["symbol"]): f["kind"] for f in r["findings"]}
    assert kinds[("1003", "XAUUSD")] == "missing_account"
    assert kinds[("1002", "XAUUSD")] == "silent_rate_change"      # paid $7/lot against an $8 card
    assert kinds[("1001", "GBPUSD")] == "excluded_symbol"
    assert kinds[("1004", "XAUUSD")] == "overpaid"                # paid for lots never traded
    assert kinds[("1001", "XAUUSD")] == "ok"
    s = r["summary"]
    assert s["expected"] == 664.0 and s["paid"] == 566.0 and s["shortfall"] == 138.0 and s["flagged"] == 3
    assert r["findings"][0]["kind"] != "ok"                        # flagged lines first


def test_tiers_apply_on_the_account_total_unless_a_symbol_override_exists():
    log = [{"account": "1", "symbol": "EURUSD", "lots": 120.0, "paid": 0.0}, {"account": "1", "symbol": "XAUUSD", "lots": 10.0, "paid": 0.0}]
    stmt = [{"account": "1", "symbol": "EURUSD", "lots": 120.0, "paid": 900.0}, {"account": "1", "symbol": "XAUUSD", "lots": 10.0, "paid": 80.0}]
    r = rebate.reconcile(stmt, log, 6, {"XAUUSD": 8}, [(100, 7.5)])
    by = {f["symbol"]: f for f in r["findings"]}
    assert by["EURUSD"]["rate"] == 7.5 and by["EURUSD"]["kind"] == "ok"
    assert by["XAUUSD"]["rate"] == 8 and by["XAUUSD"]["kind"] == "ok"


def test_dispute_pdf_is_valid_and_lists_flagged_lines():
    r = _run()
    r.update({"broker": "Sample", "period": "2026-08", "rate": 6, "overrides": "XAUUSD=8", "tiers": ""})
    body = rebate.dispute_pdf(r)
    assert body.startswith(b"%PDF-1.4") and body.rstrip().endswith(b"%%EOF")
    assert b"missing account" in body and b"1003" in body and b"Shortfall $138.00" in body


def test_bot_quick_check_and_last_run_summary(app):
    with app.app_context():
        assert "Guna" in reply_for("/rebateaudit x", chat_id=7)
        quick = reply_for("/rebateaudit 42.5 8 300", chat_id=7, lang="en")
        assert "$340.00" in quick and "shortfall <b>$40.00</b>" in quick
        assert "No runs yet" in reply_for("/rebateaudit", chat_id=7, lang="en")
        assert "Belum ada larian" in reply_for("/rebatestatus", chat_id=7)
        r = _run()
        r.update({"broker": "Sample", "period": "2026-08", "rate": 6, "overrides": "XAUUSD=8", "tiers": ""})
        store.save_rebate_run(r, owner=7)
        text = reply_for("/rebateaudit", chat_id=7, lang="ms")
        assert "Kekurangan $138.00" in text and "1 akaun hilang" in text
        assert "$138.00" in reply_for("/rebatestatus", chat_id=7, lang="en")


def test_dashboard_sample_run_errors_history_and_pdf(client):
    body = client.post("/p/rebate-auditor", data={"action": "sample"}).get_data(as_text=True)
    assert "$138.00" in body and "akaun hilang" in body and "/p/rebate-auditor/dispute/1.pdf" in body
    body = client.post("/p/rebate-auditor", data={"action": "run", "rate": "abc", "statement": "x", "log": ""}).get_data(as_text=True)
    assert "Penyata:" in body and "Log trade:" in body and "Kadar:" in body
    login(client, "42")
    upload = {"action": "run", "rate": "6", "overrides": "XAUUSD=8", "broker": "B", "period": "2026-08",
              "statement": (io.BytesIO(rebate.SAMPLE_STATEMENT.encode()), "s.csv"),
              "log": (io.BytesIO(rebate.SAMPLE_LOG.encode()), "l.csv")}
    body = client.post("/p/rebate-auditor", data=upload, content_type="multipart/form-data").get_data(as_text=True)
    assert "$138.00" in body and "Larian sebelum ini" in body
    pdf = client.get("/p/rebate-auditor/dispute/2.pdf")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf" and b"1003" in pdf.data
    assert client.get("/p/rebate-auditor/dispute/99.pdf").status_code == 404
    body = client.post("/p/rebate-auditor?sort=account", data=upload | {"statement": rebate.SAMPLE_STATEMENT, "log": rebate.SAMPLE_LOG}).get_data(as_text=True)
    assert body.index(">1001<") < body.index(">1004<")


def test_landing_counts_ten_live(client):
    body = client.get("/").get_data(as_text=True)
    assert "10 sudah hidup" in body and "8 lagi dalam giliran" in body
