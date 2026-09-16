"""#1 Gold Watch — the hours map.

The checker has been logging the spread every five minutes since the day it
shipped. These tests are about reading it back without lying: an hour with too
few samples must say so, and the verdict must be in Kuala Lumpur time, because
that is the clock the audience reads.
"""

import time

import pytest

from app import hours, store
from app.brand import STRINGS


def samples(per_hour, days=1, start=None):
    """A synthetic log: {kl_hour: spread} repeated `per_hour` count times.

    Timestamps are built backwards from a fixed UTC midnight so the KL hour of
    each sample is exactly the one asked for, whatever day the suite runs.
    """
    base = start if start is not None else 1_760_000_000
    midnight = base - (base % 86400)
    out = []
    for day in range(days):
        for hour, (spread, count) in per_hour.items():
            utc_hour = (hour - 8) % 24          # KL hour -> the UTC hour it sits in
            for i in range(count):
                out.append((midnight - day * 86400 + utc_hour * 3600 + i * 300, spread))
    return out


def flat(spread=0.30, count=12):
    return {h: (spread, count) for h in range(24)}


# --- the maths ------------------------------------------------------------------ #

def test_an_empty_log_produces_no_map_rather_than_an_empty_one(app):
    with app.app_context():
        assert hours.profile(30, samples=[]) is None


def test_kl_time_not_utc(app):
    """09:00 in KL is 01:00 UTC. Getting this wrong points every trader at the
    wrong half of the day."""
    midnight_utc = 1_760_000_000 - (1_760_000_000 % 86400)
    assert hours.kl_hour(midnight_utc) == 8
    assert hours.kl_hour(midnight_utc + 3600) == 9


def test_the_cheap_hour_and_the_dear_hour_are_found(app):
    rows = flat(0.30)
    rows[14] = (0.12, 12)     # London/NY overlap
    rows[2] = (0.90, 12)      # the thin Asian small hours
    prof = hours.profile(30, samples=samples(rows))
    assert prof["best"]["hour"] == 14
    assert prof["worst"]["hour"] == 2
    assert prof["rows"][14]["band"] == "best"
    assert prof["rows"][2]["band"] == "worst"
    assert prof["rows"][7]["band"] == "ok"


def test_an_hour_with_too_few_samples_is_never_graded(app):
    """A confident wrong answer about when to trade is worse than no answer."""
    rows = flat(0.30)
    rows[3] = (0.05, hours.MIN_SAMPLES - 1)      # cheap, but barely measured
    prof = hours.profile(30, samples=samples(rows))
    assert prof["rows"][3]["band"] == "thin"
    assert prof["best"]["hour"] != 3              # and so it cannot win the title


def test_the_verdict_names_this_hour_and_the_wait(app):
    rows = flat(0.30)
    rows[14] = (0.10, 12)
    prof = hours.profile(30, samples=samples(rows))
    now = 1_760_000_000 - (1_760_000_000 % 86400) + 4 * 3600      # 12:00 KL
    verd = hours.verdict(prof, now)
    assert verd["hour"] == 12
    assert verd["wait"] == 2
    assert verd["next"]["hour"] == 14


def test_a_cheap_hour_has_nothing_to_wait_for(app):
    rows = flat(0.30)
    rows[14] = (0.10, 12)
    prof = hours.profile(30, samples=samples(rows))
    now = 1_760_000_000 - (1_760_000_000 % 86400) + 6 * 3600      # 14:00 KL
    verd = hours.verdict(prof, now)
    assert verd["band"] == "best" and verd["wait"] == 0
    assert hours.cost_of_waiting(prof, verd, 5) is None


def test_the_cost_of_waiting_is_per_lot_and_never_negative(app):
    rows = flat(0.30)
    rows[14] = (0.10, 12)
    prof = hours.profile(30, samples=samples(rows))
    now = 1_760_000_000 - (1_760_000_000 % 86400) + 4 * 3600      # 12:00 KL, $0.30
    verd = hours.verdict(prof, now)
    # 20 cents an ounce, 100 ounces a lot, 5 lots
    assert hours.cost_of_waiting(prof, verd, 5) == pytest.approx(100.0, rel=1e-6)
    assert hours.cost_of_waiting(prof, verd, 1) >= 0


def test_a_day_with_no_cheap_hour_promises_no_wait(app):
    """Every hour ordinary means there is nothing honest to tell someone to
    wait for, so `wait` is None and no cost is invented."""
    prof = hours.profile(30, samples=samples(flat(0.30)))
    assert all(r["band"] == "ok" for r in prof["rows"])
    verd = hours.verdict(prof, 1_760_000_000)
    assert verd["wait"] is None
    assert hours.cost_of_waiting(prof, verd, 10) is None


# --- rank ------------------------------------------------------------------------- #

def test_the_window_grows_with_the_rank_but_the_verdict_never_locks(app):
    with app.app_context():
        assert hours.days_for(owner="42") == 7
        assert hours.days_for(user={"rank": "pro"}) == 30
        assert hours.days_for(user={"rank": "elite"}) == 30


def test_the_hours_limit_is_published_on_the_ranks_page(client, app):
    """Every cap the code enforces has to be visible where ranks are sold."""
    page = client.get("/pricing").get_data(as_text=True)
    assert "peta jam" in page


# --- the bot -------------------------------------------------------------------------- #

def _seed(rows):
    """The same synthetic day, anchored to now so it falls inside the rank's window."""
    for ts, spread in samples(rows, start=time.time()):
        store.db().execute("INSERT OR REPLACE INTO spread_log (ts, bid, ask, spread, source) VALUES (?, ?, ?, ?, ?)",
                           (ts, 2400.0, 2400.0 + spread, spread, "test"))
    store.db().commit()


def test_watch_hours_answers_in_the_bot(app):
    from app.watch import bot_watch
    with app.app_context():
        rows = flat(0.30)
        rows[14] = (0.10, 12)
        _seed(rows)
        reply = bot_watch(["hours"], chat_id=7)
        assert "Jam dagangan emas" in reply
        assert "14:00" in reply
        assert "sampel" in reply


def test_watch_hours_is_free_at_every_rank(app):
    """Paying the wrong spread is a loss. Warning about a loss is never the
    thing we charge for — the rank only buys the length of the window."""
    from app.watch import bot_watch
    with app.app_context():
        _seed(flat(0.30))
        reply = bot_watch(["hours"], chat_id=7)
        assert "A-Team" not in reply and "Rambo" not in reply


def test_an_unmeasured_log_says_it_is_still_collecting(app):
    from app.watch import bot_watch
    with app.app_context():
        assert "Belum cukup data" in bot_watch(["hours"], chat_id=7)


def test_a_silly_lot_size_does_not_crash_the_bot(app):
    from app.watch import bot_watch
    with app.app_context():
        _seed(flat(0.30))
        assert "Jam dagangan" in bot_watch(["hours", "banyak"], chat_id=7)


def test_the_flow_offers_the_hours_map_as_a_button(app):
    from app import flows
    mode = flows.FLOWS["gold-watch"][0]
    assert ("flow.watch_hours", "hours") in mode["options"]
    assert flows.build("gold-watch", {"mode": "hours"}) == "/watch hours"


def test_the_hours_branch_never_asks_for_a_price_level(app):
    """The level step is for the two alert modes only."""
    from app import flows
    level = flows.FLOWS["gold-watch"][1]
    assert level["when"]({"mode": "hours"}) is False
    assert level["when"]({"mode": "price"}) is False
    assert level["when"]({"mode": "above"}) is True


# --- the page --------------------------------------------------------------------------- #

def test_the_page_draws_the_map_and_marks_this_hour(client, app):
    with app.app_context():
        rows = flat(0.30)
        rows[14] = (0.10, 12)
        _seed(rows)
    page = client.get("/p/gold-watch").get_data(as_text=True)
    assert "Jam terbaik" in page
    assert "14:00–15:00" in page
    assert "var(--gold)" in page          # this hour is outlined


def test_the_page_shows_no_table_before_there_is_data(client, app):
    page = client.get("/p/gold-watch").get_data(as_text=True)
    assert "Belum cukup data" in page


def test_the_lot_size_carries_into_the_cost(client, app):
    with app.app_context():
        rows = flat(0.60)
        rows[14] = (0.10, 12)
        _seed(rows)
    page = client.get("/p/gold-watch?lots=10").get_data(as_text=True)
    assert 'value="10"' in page


def test_both_languages_carry_every_hours_string(app):
    keys = [k for k in STRINGS["ms"] if k.startswith("hours.")]
    assert keys
    for key in keys:
        assert STRINGS["en"].get(key), key


def test_the_daily_push_carries_the_hours_verdict(app):
    """A price on its own does not say whether to act on it."""
    from app import autopilot
    with app.app_context():
        rows = flat(0.30)
        rows[14] = (0.10, 12)
        _seed(rows)
        line = autopilot._gold("42", "ms")
        assert line and ("Sekarang" in line or "Jam ini" in line)
