"""#17 the premium band — is this premium normal, or is this the moment?

"PAXG is 1.4% over spot" is useless on its own; nobody knows whether 1.4% is the
usual toll. These tests are about the band being each coin's *own* range, and
about the two things it refuses to say: a range drawn through a handful of
samples, and a winner declared against a missing number.
"""

import time

import pytest

from app import premium, store
from app.brand import STRINGS


def rows(paxg_pcts, xaut_pcts=None, spot=2400.0):
    """A premium log: percentages in, prices out, the way the checker writes it."""
    xaut_pcts = xaut_pcts if xaut_pcts is not None else paxg_pcts
    now = time.time()
    return [{"at": now - (len(paxg_pcts) - i) * 300,
             "paxg": spot * (1 + p / 100), "xaut": spot * (1 + x / 100),
             "spot": spot, "usdt": 1.0}
            for i, (p, x) in enumerate(zip(paxg_pcts, xaut_pcts))]


def spread(low, high, n=200):
    """`n` samples spread evenly between two premiums."""
    return [low + (high - low) * i / (n - 1) for i in range(n)]


# --- what it refuses to say ------------------------------------------------------- #

def test_a_handful_of_samples_is_not_a_band(app):
    """A range drawn through ten samples looks exactly as authoritative as a
    real one, and someone would buy on it."""
    assert premium.band("paxg", rows=rows(spread(0.5, 1.5, 10))) is None
    assert premium.band("paxg", rows=rows(spread(0.5, 1.5, premium.MIN_SAMPLES))) is not None


def test_no_history_means_no_band(app):
    assert premium.band("paxg", rows=[]) is None
    assert premium.line(None) == STRINGS["ms"]["band.thin"]


def test_a_winner_is_never_declared_against_a_missing_number(app):
    assert premium.cheapest({"paxg_premium": 0.4, "xaut_premium": None}) is None
    assert premium.cheapest({}) is None


# --- the band --------------------------------------------------------------------- #

def test_the_band_is_each_coin_own_range(app):
    """PAXG habitually trades tighter than XAUT; a fixed threshold would call
    the same number normal for one and alarming for the other."""
    log = rows(spread(0.2, 0.6), spread(1.0, 2.0))
    assert premium.band("paxg", rows=log)["high"] < premium.band("xaut", rows=log)["low"]


def test_where_now_sits_decides_the_verdict(app):
    log = rows(spread(0.0, 2.0))
    assert premium.band("paxg", rows=log, now=0.05)["verdict"] == "cheap"
    assert premium.band("paxg", rows=log, now=1.0)["verdict"] == "normal"
    assert premium.band("paxg", rows=log, now=1.95)["verdict"] == "dear"


def test_the_edges_are_the_tenth_and_ninetieth_percentile(app):
    b = premium.band("paxg", rows=rows(spread(0.0, 10.0)))
    assert b["low"] == pytest.approx(1.0, abs=0.1)
    assert b["high"] == pytest.approx(9.0, abs=0.1)
    assert b["median"] == pytest.approx(5.0, abs=0.1)


def test_percentile_handles_the_single_sample_case(app):
    assert premium.percentile([3.0], 10) == 3.0


# --- the route ---------------------------------------------------------------------- #

def test_the_cheaper_way_into_gold_is_named_with_the_saving(app):
    best = premium.cheapest({"paxg_premium": 0.4, "xaut_premium": 1.9})
    assert best["asset"] == "paxg" and best["other"] == "xaut"
    assert best["saving"] == pytest.approx(1.5)


# --- the alert ------------------------------------------------------------------------ #

def test_a_break_is_a_crossing_not_a_state(app):
    """An asset already outside its band stays quiet — a daily push repeating
    yesterday's news trains people to ignore it."""
    normal = {"paxg": {"verdict": "normal"}, "xaut": {"verdict": "normal"}}
    dear = {"paxg": {"verdict": "dear"}, "xaut": {"verdict": "normal"}}
    assert [b["verdict"] for b in premium.broke(normal, dear)] == ["dear"]
    assert premium.broke(dear, dear) == []
    assert premium.broke(None, dear) == []


# --- the surfaces ----------------------------------------------------------------------- #

def _seed(pcts, spot=2400.0):
    for r in rows(pcts, spot=spot):
        store.db().execute("INSERT INTO premium_log (at, paxg, xaut, spot, usdt) VALUES (?, ?, ?, ?, ?)",
                           (r["at"], r["paxg"], r["xaut"], r["spot"], r["usdt"]))
    store.db().commit()


def test_the_bot_readout_carries_the_band(app, fake_tokens):
    from app.telegram import reply_for
    with app.app_context():
        _seed(spread(0.0, 2.0))
        reply = reply_for("/paxg", chat_id=7)
        assert "julat biasa" in reply
        assert "Jalan termurah" in reply


def test_the_readout_still_answers_with_no_history(app, fake_tokens):
    from app.telegram import reply_for
    with app.app_context():
        assert "PAXG" in reply_for("/paxg", chat_id=7)


def test_the_page_draws_the_band(client, app, fake_tokens):
    with app.app_context():
        _seed(spread(0.0, 2.0))
    page = client.get("/p/tokenized-gold").get_data(as_text=True)
    assert "Julat premium 30 hari" in page
    assert "julat biasa" in page


def test_the_page_says_it_is_collecting_before_there_is_a_band(client, app, fake_tokens):
    page = client.get("/p/tokenized-gold").get_data(as_text=True)
    assert "Belum cukup sampel" in page


def test_the_series_takes_the_newest_samples_not_the_oldest(app):
    """`premium_history` takes the oldest, which is right for a chart and wrong
    for a range that is meant to describe now."""
    with app.app_context():
        _seed(spread(0.0, 5.0, 300))
        assert len(store.premium_series(30, limit=50)) == 50
        newest = store.premium_series(30, limit=50)
        assert newest[0]["at"] < newest[-1]["at"]           # still oldest-first
        assert newest[-1]["at"] == max(r["at"] for r in store.premium_series(30))


def test_the_autopilot_speaks_when_a_premium_leaves_its_band(app, fake_tokens):
    from app import autopilot
    with app.app_context():
        _seed(spread(0.0, 0.5))          # a tight habitual range
        fake_tokens.update(paxg=2400.0 * 1.04)
        from app import tokengold
        tokengold.clear_cache()
        line = autopilot._tokengold("42", "ms")
        assert line and "julat biasa" in line


def test_both_languages_carry_every_band_string(app):
    keys = [k for k in STRINGS["ms"] if k.startswith("band.")]
    assert keys
    for key in keys:
        assert STRINGS["en"].get(key), key
