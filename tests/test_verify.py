"""#2 Signal Verifier: windows in MYT, verdicts against candles, both surfaces, batch, share page, flow."""

import datetime as dt

import pytest

from app import verify
from app.telegram import handle_update, reply_for
from tests.conftest import login
from tests.test_bot import msg, tap

UTC = dt.timezone.utc


def candles(lo=2420.0, hi=2440.0, n=60, start=None):
    start = start or dt.datetime(2026, 9, 14, 6, 0, tzinfo=UTC)
    out = []
    for i in range(n):
        step = (hi - lo) / n
        c_lo, c_hi = lo + i * step, lo + (i + 1) * step + 0.5
        out.append({"at": start + dt.timedelta(minutes=i), "open": c_lo, "high": c_hi, "low": c_lo, "close": c_hi})
    return out


@pytest.fixture
def fake_candles(monkeypatch):
    box = {"candles": candles(), "source": "Binance PAXGUSDT", "calls": []}

    def fetch(start, end):
        box["calls"].append((start, end))
        if box["candles"] is None:
            raise verify.NoData("Binance PAXGUSDT: no bars; Yahoo GC=F: no bars")
        return box["source"], box["candles"]

    monkeypatch.setattr(verify, "fetch_candles", fetch)
    return box


def test_parse_when_is_myt_and_defaults_to_24h():
    now = dt.datetime(2026, 9, 15, 10, 0, tzinfo=UTC)
    s, e, label = verify.parse_when(None, None, now)
    assert (e - s) == dt.timedelta(hours=24) and label == "24h"
    s, e, label = verify.parse_when("2026-09-14", None, now)
    assert s == dt.datetime(2026, 9, 13, 16, 0, tzinfo=UTC) and (e - s) == dt.timedelta(days=1)   # MYT midnight = 16:00 UTC
    s, e, label = verify.parse_when("2026-09-14", "14:30", now)
    assert s == dt.datetime(2026, 9, 14, 5, 30, tzinfo=UTC) and "±60m" in label


def test_judge_real_borderline_impossible_unverified():
    cs = candles()
    assert verify.judge(2430.0, cs, "Binance PAXGUSDT")["verdict"] == "REAL"
    b = verify.judge(2445.0, cs, "Binance PAXGUSDT")           # 4.5 above 2440.5 → 0.18 % → within 0.4 %
    assert b["verdict"] == "BORDERLINE" and b["gap"] == pytest.approx(4.5)
    assert verify.judge(2500.0, cs, "Binance PAXGUSDT")["verdict"] == "IMPOSSIBLE"
    assert verify.judge(2445.0, cs, "Yahoo GC=F")["verdict"] == "BORDERLINE"
    assert verify.judge(2430.0, [], "")["verdict"] == "UNVERIFIED"


def test_parse_claim_line_shapes():
    assert verify.parse_claim_line("2431.5 2026-09-14 14:30 buy") == ("2431.5", "2026-09-14", "14:30", "buy")
    assert verify.parse_claim_line("2,418 2026-09-14") == ("2418", "2026-09-14", None, "")
    assert verify.parse_claim_line("2455.2") == ("2455.2", None, None, "")
    assert verify.parse_claim_line("   ") is None


def test_bot_verify_replies_in_both_languages_and_archives(app, fake_candles):
    with app.app_context():
        assert "Guna" in reply_for("/verify", chat_id=7)
        text = reply_for("/verify GOLD 2431.5 2026-09-14 14:30", chat_id=7, lang="en")
        assert "✅ <b>REAL</b>" in text and "Window range: 2,420.00 – 2,440.50" in text and "Saved as scan #1" in text
        text = reply_for("/verify GOLD 2500 2026-09-14 14:30", chat_id=7, lang="ms")
        assert "❌ <b>IMPOSSIBLE</b>" in text and "Di luar julat" in text
        fake_candles["candles"] = None
        assert "TAK DAPAT SAHKAN" in reply_for("/verify 2431.5", chat_id=7, lang="ms")
        assert "mesti nombor" in reply_for("/verify GOLD abc", chat_id=7, lang="ms")


def test_dashboard_single_batch_history_and_share_page(client, fake_candles):
    body = client.post("/p/signal-verifier", data={"price": "2431.5", "date": "2026-09-14", "time": "14:30"}).get_data(as_text=True)
    assert "REAL" in body and "/p/signal-verifier/s/1" in body
    assert client.get("/p/signal-verifier/s/1").status_code == 200
    assert client.get("/p/signal-verifier/s/99").status_code == 404
    assert client.get("/p/red-flag-scanner/s/1").status_code == 404        # a verdict is not a scan
    login(client, "42")
    body = client.post("/p/signal-verifier", data={"action": "batch", "claims": "2431.5 2026-09-14 14:30\n2500 2026-09-14\n\nabc"}).get_data(as_text=True)
    assert body.count("IMPOSSIBLE") >= 1 and "REAL" in body and "mesti nombor" in body
    page = client.get("/p/signal-verifier").get_data(as_text=True)
    assert "Sejarah" in page and page.count("/p/signal-verifier/s/") >= 2
    assert "sekurang-kurangnya satu" in client.post("/p/signal-verifier", data={"action": "batch", "claims": ""}).get_data(as_text=True)


def test_verify_flow_skips_time_when_date_is_skipped(app, fake_candles):
    with app.app_context():
        handle_update(tap("lang_ms"))
        handle_update(tap("run_signal-verifier"))
        prompt = [a for a in handle_update(msg("2431.5")) if a[0] == "send"][-1]
        assert "Tarikh" in prompt[2]
        done = [a for a in handle_update(tap("fl_skip")) if a[0] == "send"][-1]
        assert "REAL" in done[2] and "24h" in done[2]
