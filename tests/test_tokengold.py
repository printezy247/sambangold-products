"""#17 Tokenized gold: premium maths, peg, wallet checks (EIP-55, poisoning), both surfaces, the checker log."""

from app import store, tokengold, tokengoldtool, watch
from app.telegram import reply_for
from tests.conftest import REAL_TOKEN_FETCH, login

GOOD = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"        # EIP-55 reference vector


def test_premium_peg_and_flags(fake_tokens):
    a = tokengold.analyse(tokengold.snapshot())
    assert a["paxg_premium"] == 0.833 and a["xaut_premium"] == 0.417 and a["paxg_xaut"] == 0.415
    assert a["peg"] == "ok" and a["usdt_off"] == -0.05 and a["flags"] == []
    fake_tokens.update(paxg=2430.0, usdt=0.99)
    tokengold.clear_cache()
    a = tokengold.analyse(tokengold.snapshot())
    assert a["paxg_premium"] == 1.25 and a["flags"] == ["paxg_premium", "peg"] and a["peg"] == "off"
    fake_tokens.update(spot=None, usdt=None)
    tokengold.clear_cache()
    a = tokengold.analyse(tokengold.snapshot())
    assert a["paxg_premium"] is None and a["peg"] is None and a["paxg_xaut"] is not None and a["flags"] == []


def test_fetch_raises_only_when_both_tokens_are_missing(monkeypatch):
    import pytest
    boom = lambda: (_ for _ in ()).throw(ConnectionError("down"))
    monkeypatch.setattr(tokengold, "_paxg", boom)
    monkeypatch.setattr(tokengold, "_xaut", lambda: 2410.0)
    monkeypatch.setattr(tokengold, "_gc", boom)
    monkeypatch.setattr(tokengold, "_usdt", boom)
    snap = REAL_TOKEN_FETCH()
    assert snap["xaut"] == 2410.0 and snap["paxg"] is None and snap["spot"] is None and len(snap["errors"]) == 3
    monkeypatch.setattr(tokengold, "_xaut", boom)
    with pytest.raises(tokengold.FeedError):
        REAL_TOKEN_FETCH()


def test_keccak_eip55_chain_and_wallet_checks():
    assert tokengold.keccak256(b"") == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    assert tokengold.eip55(GOOD.lower()) == GOOD
    assert tokengold.chain_of(GOOD) == "evm"
    assert tokengold.chain_of("TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9") == "tron"
    assert tokengold.chain_of("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq") == "bitcoin"
    assert tokengold.chain_of("7EYnhQoR9YM3N7UoaKRoA44Uy8JeaZV3qyouov87awMs") == "solana"
    assert tokengold.chain_of("hello") is None and tokengold.chain_of("") is None

    ok = tokengold.check_wallet(GOOD)
    assert ok["checksum"] is True and ok["flags"] == [] and ok["fees"] == tokengold.FEES
    bad = tokengold.check_wallet(GOOD[:-1] + "D")          # one character wrong, mixed case → checksum fails
    assert bad["checksum"] is False and bad["flags"] == ["bad_checksum"]
    none = tokengold.check_wallet(GOOD.lower())
    assert none["checksum"] is None and none["flags"] == ["no_checksum"]
    assert tokengold.check_wallet("nope")["flags"] == ["unknown_format"]

    same = tokengold.check_wallet(GOOD, GOOD.lower())
    assert same["poisoning"] == "same" and "poisoning" not in same["flags"]
    look = tokengold.check_wallet("0x5aAe00000000000000000000000000000000eAed".lower(), GOOD)
    assert look["poisoning"] == "lookalike" and "poisoning" in look["flags"]
    diff = tokengold.check_wallet("0x" + "1" * 40, GOOD)
    assert diff["poisoning"] == "different" and "poisoning" not in diff["flags"]


def test_bot_paxg_and_walletcheck(app, fake_tokens):
    with app.app_context():
        text = reply_for("/paxg", chat_id=7, lang="en")
        assert "PAXG 2,420.00" in text and "+0.83%" in text and "peg OK" in text and "front futures" in text
        ms = reply_for("/paxg", chat_id=7)
        assert "Emas bertoken" in ms and "peg stabil" in ms   # the Malay reply says it in Malay
        fake_tokens.update(usdt=0.99)
        tokengold.clear_cache()
        assert "tergelincir" in reply_for("/paxg", chat_id=7)

        assert "Guna:" in reply_for("/walletcheck", chat_id=7)
        text = reply_for("/walletcheck %s" % GOOD, chat_id=7, lang="en")
        assert "EIP-55 checksum valid" in text and "TRC20 (Tron) $1" in text and "Payout rules" in text
        text = reply_for("/walletcheck 0x5aae00000000000000000000000000000000eaed %s" % GOOD, chat_id=7)
        assert "ADDRESS POISONING" in text and "Tiada checksum" in text
        assert "GAGAL" in reply_for("/walletcheck %sD" % GOOD[:-1], chat_id=7)
        assert "tak dikenali" in reply_for("/walletcheck nope", chat_id=7)


def test_bot_reports_a_dead_feed(app, monkeypatch):
    monkeypatch.setattr(tokengold, "fetch", lambda: (_ for _ in ()).throw(tokengold.FeedError("paxg: down; xaut: down")))
    tokengold.clear_cache()
    with app.app_context():
        assert "tak tersedia" in reply_for("/paxg", chat_id=7)
        assert "Checksum EIP-55 sah" in reply_for("/walletcheck %s" % GOOD, chat_id=7)   # wallet check is offline


def test_checker_logs_the_premium_and_the_dashboard_charts_it(app, client, fake_tokens):
    with app.app_context():
        assert store.premium_history() == []
        watch.check_alerts(lambda *a: None)
        assert len(store.premium_history()) == 1 and store.premium_history()[0]["paxg"] == 2420.0
        fake_tokens.update(paxg=2400.0)
        watch.check_alerts(lambda *a: None)
        rows = store.premium_history()
        assert len(rows) == 2 and rows[-1]["paxg"] == 2400.0
        svg = tokengoldtool.svg_history(rows)
        assert svg.startswith("<svg") and svg.count("<polyline") == 2
        assert tokengoldtool.svg_history(rows[:1]) == ""

    body = client.get("/p/tokenized-gold").get_data(as_text=True)
    assert "2,400.00" in body and "<polyline" in body and "Paxos" in body and "Tether" in body and "TRC20" in body
    body = client.get("/p/tokenized-gold?address=%s&expected=%s" % ("0x5aAe00000000000000000000000000000000eAed", GOOD)).get_data(as_text=True)
    assert "ADDRESS POISONING" in body
    login(client, "42")
    body = client.get("/p/tokenized-gold?address=%s" % GOOD).get_data(as_text=True)
    assert "Checksum EIP-55 sah" in body
    client.get("/lang/en")
    assert "EIP-55 checksum valid" in client.get("/p/tokenized-gold?address=%s" % GOOD).get_data(as_text=True)
