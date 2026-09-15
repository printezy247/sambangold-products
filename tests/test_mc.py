"""#15 Monte Carlo: deterministic paths, rule kills, pass/cost maths, both surfaces, fan chart, PDF."""

import random

import pytest

from app import mc, store
from app.telegram import handle_update, reply_for
from tests.conftest import login
from tests.test_bot import tap


def test_path_ends_by_the_rule_that_kills_it():
    pack = mc.PACKS["ftmo"]
    r = mc.simulate_path(random.Random(1), 0.0, 2, 1.0, pack, 10, 5)        # never wins, 5 a day: daily loss at -5 %
    assert r["result"] == "fail" and r["reason"] == "daily" and r["trades"] == 5
    r = mc.simulate_path(random.Random(1), 0.0, 2, 1.0, pack, 10, 3)        # 3 a day resets the day line: max DD at -10 %
    assert r["reason"] == "max" and r["trades"] == 10
    r = mc.simulate_path(random.Random(1), 1.0, 2, 1.0, pack, 10, 3)        # always wins: passes after the min days
    assert r["result"] == "pass" and r["days"] >= pack["min_days"] and r["final"] >= 110
    cons = dict(pack, consistency_pct=30.0, min_days=0)
    r = mc.simulate_path(random.Random(1), 1.0, 2, 4.0, cons, 10, 3)        # one huge day breaks consistency
    assert r["result"] == "fail" and r["reason"] == "consistency"
    r = mc.simulate_path(random.Random(1), 0.5, 1, 0.01, pack, 10, 3)       # tiny risk: runs out of trades
    assert r["result"] == "timeout"


def test_run_is_deterministic_and_reports_cost_to_funded():
    a = mc.run(45, 2, 1.0, "ftmo", 10, 500, 3, 500, seed=7)
    b = mc.run("45%", "2", "1", "ftmo", "10", "500", "3", "500", seed=7)
    assert a["p_pass"] == b["p_pass"] and 0.8 < a["p_pass"] <= 1.0
    assert a["cost_to_funded"] == pytest.approx(500 / a["p_pass"], rel=1e-3) and a["expectancy_r"] == 0.35
    assert len(a["bands"][50]) == a["length"] and len(a["samples"]) == 12
    bad = mc.run(40, 1, 2.0, "myfundedfx", 8, 300, 4, 300, seed=2)
    assert bad["p_pass"] < 0.2 and set(bad["reasons"]) >= {"daily", "max"}
    with pytest.raises(ValueError):
        mc.run(150, 2, 1)
    assert mc.run(45, 2, 1, sims=99999, seed=1)["inputs"]["sims"] == mc.FREE_SIMS
    svg = mc.svg_fan(a)
    assert svg.startswith("<svg") and svg.count("<polyline") == 13 and "110%" in svg


def test_bot_card_and_flow(app):
    with app.app_context():
        assert "Guna" in reply_for("/simulate", chat_id=7)
        assert "tak masuk akal" in reply_for("/simulate 150 2 1", chat_id=7)
        text = reply_for("/simulate 45 2 1 ftmo", chat_id=7, lang="en")
        assert "<b>Pass " in text and "cost to funded" in text and "Saved as scan #1" in text
        assert store.runs_for("monte-carlo-sim", 7)[0]["metric"] > 0.5
        handle_update(tap("lang_ms"))
        handle_update(tap("run_monte-carlo-sim"))
        for data in ("fl_o:45", "fl_o:2", "fl_o:1"):
            handle_update(tap(data))
        done = [a for a in handle_update(tap("fl_o:e8")) if a[0] == "send"][-1]
        assert "Lulus" in done[2] and "E8 Markets" in done[2]


def test_dashboard_run_fan_chart_history_and_pdf(client):
    body = client.get("/p/monte-carlo-sim?winrate=45&rr=2&risk=1&firm=ftmo&seed=3").get_data(as_text=True)
    assert "Kebarangkalian lulus" in body and "<svg" in body and "seed 3" in body and "Log masuk" in body
    assert "tak masuk akal" in client.get("/p/monte-carlo-sim?winrate=abc").get_data(as_text=True)
    login(client, "42")
    body = client.get("/p/monte-carlo-sim?winrate=40&rr=1&risk=2&firm=myfundedfx&target=8&seed=2").get_data(as_text=True)
    assert "/p/monte-carlo-sim/run/1.pdf" in body and "Di mana laluan gagal" in body
    pdf = client.get("/p/monte-carlo-sim/run/1.pdf")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf" and b"MyFundedFX" in pdf.data
    assert client.get("/p/monte-carlo-sim/run/99.pdf").status_code == 404
