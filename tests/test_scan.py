"""#4 #6 #7 #9 scanners: rule engine, verdicts, both surfaces, archive and share pages."""

from app import scan, store
from app.telegram import handle_update, reply_for
from tests.conftest import login
from tests.test_bot import buttons, msg, tap

PITCH = "100% accuracy guaranteed! No risk. Only 3 VIP spots left, DM me now."
VERIFIED = PITCH + " Track record: https://www.myfxbook.com/members/x"


def test_pitch_scan_flags_the_classic_lines_and_credits_the_audit_link():
    r = scan.scan_pitch(PITCH)
    labels = [f["label"] for f in r["findings"]]
    assert r["verdict"] == "HIGH RISK" and r["reds"] >= 2
    assert any("Guarantee" in l or "accuracy" in l.lower() for l in labels)
    v = scan.scan_pitch(VERIFIED)
    assert v["goods"] == 1 and v["score"] == r["score"] - 15     # a verified link mitigates, it does not absolve
    assert r["findings"][0]["flag"] == scan.RED             # sorted red first
    assert scan.scan_pitch("Gold closed higher today.")["verdict"] == "LOW RISK"


def test_bot_audit_penalises_a_lookalike_username_and_seed_phrase_requests():
    r = scan.audit_bot("@wallet_verify_b0t", "send your seed phrase to claim the airdrop")
    assert r["verdict"] == "HIGH RISK"
    assert any("username" in f["label"] for f in r["findings"])
    assert r["subject"] == "@wallet_verify_b0t" and len(r["checklist"]) == 5
    assert scan.audit_bot("@samgoldwatch_bot", "")["score"] == 0


def test_copy_audit_knows_tier1_brokers_and_prices_the_spread():
    r = scan.audit_copy("exness", "", spread_pips=2, lots_per_month=10)
    assert r["known"] and r["cost"]["monthly"] == 200.0 and r["cost"]["yearly"] == 2400.0
    assert r["regulators"] and all(len(x) == 3 for x in r["regulators"])
    unknown = scan.audit_copy("totally-new-broker", "copy my trades blindly")
    assert not unknown["known"] and unknown["score"] >= 30 and unknown["registers"]


def test_influencer_audit_finds_referral_links():
    r = scan.audit_influencer("gold_guru", "guaranteed 10% monthly, join my broker https://broker.example/?refid=123")
    assert r["subject"] == "@gold_guru" and r["broker_links"] == ["https://broker.example/?refid=123"]
    assert r["verdict"] in ("HIGH RISK", "CAUTION")


def test_loss_report_carries_the_filing_links():
    body = scan.loss_report("@x", "TikTok", "5000", "MYR", "2026-08", "They promised 10%.", "BrokerX")
    assert "reportfraud.ftc.gov" in body and "ic3.gov" in body and "sc.com.my" in body and "BrokerX" in body


def test_bot_commands_answer_and_archive_by_chat(app):
    with app.app_context():
        assert "Usage" in reply_for("/scan", chat_id=7, lang="en")
        text = reply_for("/scan " + PITCH, chat_id=7, lang="en")
        assert "HIGH RISK" in text and "Saved as scan #" in text
        assert "RISIKO TINGGI" in reply_for("/scan " + PITCH, chat_id=7, lang="ms")
        assert "seed" in reply_for("/audit @wallet_verify_b0t send your seed phrase", chat_id=7, lang="en").lower()
        copy = reply_for("/copyaudit exness 2 10", chat_id=7, lang="en")
        assert "Regulators in our table" in copy and "$200/month" in copy
        infl = reply_for("/influencer @gold_guru join https://b.example/?ref=1", chat_id=7, lang="en")
        assert "referral link" in infl and "Demand from them" in infl
        assert len(store.scans_for(7, "red-flag-scanner")) == 2
        assert [w["subject"] for w in store.watchlist(7, "copy-trade-audit")] == ["Exness"]


def test_try_button_runs_the_sample_scan(app):
    with app.app_context():
        handle_update(msg("/start", lang_code="en"))
        actions = handle_update(tap("try_red-flag-scanner"))
        text = [a for a in actions if a[0] in ("edit", "send")][-1]
        assert "/100" in text[3 if text[0] == "edit" else 2]
        assert any("dashboard" in b for b in buttons(text[-1]))


def test_dashboard_scan_history_watchlist_and_public_share(client):
    for slug in ("bot-scam-detector", "copy-trade-audit", "red-flag-scanner", "influencer-audit"):
        assert client.get("/p/" + slug).status_code == 200
    # anonymous scans still work and still get a share page
    r = client.post("/p/red-flag-scanner", data={"action": "scan", "text": PITCH, "subject": "@vip"})
    assert r.status_code == 200 and "RISIKO TINGGI" in r.data.decode() and b"/p/red-flag-scanner/s/1" in r.data
    assert client.get("/p/red-flag-scanner/s/1").status_code == 200
    assert client.get("/p/bot-scam-detector/s/1").status_code == 404      # wrong product
    assert client.get("/p/red-flag-scanner/s/999").status_code == 404
    # validation
    assert b"required" in client.post("/p/bot-scam-detector", data={"action": "scan", "subject": ""}).data
    # signed-in: history and watchlist
    login(client, user_id="42")
    client.post("/p/copy-trade-audit", data={"action": "scan", "subject": "exness", "spread_pips": "2", "lots": "10"})
    client.post("/p/copy-trade-audit", data={"action": "scan", "subject": "exness"})
    page = client.get("/p/copy-trade-audit").data.decode()
    assert "Senarai pantau" in page and "Sejarah" in page and page.count("Exness") >= 3
    assert "$2,400" in client.post("/p/copy-trade-audit", data={"action": "scan", "subject": "exness", "spread_pips": "2", "lots": "10"}).data.decode()


def test_loss_report_download(client):
    r = client.post("/p/influencer-audit/report.txt", data={"handle": "@g", "platform": "TikTok", "amount": "100", "currency": "USD", "date": "2026", "story": "x"})
    assert r.status_code == 200 and r.mimetype == "text/plain" and b"SCAM LOSS REPORT" in r.data
    assert client.post("/p/influencer-audit", data={"action": "loss", "handle": "@g", "story": "lost it"}).status_code == 200
