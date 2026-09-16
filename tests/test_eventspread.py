"""#5 Gold Calendar — the event spread record.

Every calendar says NFP is at 20:30. This says what it cost and when it stopped
costing. The tests are mostly about what the module refuses to claim: one
release is an anecdote, and a recovery we never observed is never promised.
"""

import datetime as dt

from app import caltool, eventspread, goldcal, store
from app.brand import STRINGS

UTC = goldcal.UTC


def release(at, shape):
    """Samples around one release: {offset in minutes: spread}."""
    return [{"event_at": at, "ts": at + off * 60, "spread": spread} for off, spread in shape.items()]


# a blow-out that comes home 30 minutes after the print
SHAPE = {-60: 0.30, -45: 0.30, -30: 0.30, -15: 0.45, 0: 2.40, 15: 0.90, 30: 0.34, 45: 0.30, 60: 0.30}


def rows(n=3, at=1_760_000_000, shape=None):
    out = []
    for i in range(n):
        out += release(at - i * 30 * 86400, shape or SHAPE)
    return out


# --- what it refuses to claim ------------------------------------------------- #

def test_one_release_is_an_anecdote_not_a_record(app):
    assert eventspread.curve("NFP", rows=rows(1)) is None
    assert eventspread.curve("NFP", rows=rows(2)) is not None


def test_nothing_measured_produces_nothing(app):
    assert eventspread.curve("NFP", rows=[]) is None


def test_a_recovery_we_never_saw_is_never_promised(app):
    """A spread still wide at the edge of the span must not be reported as
    recovered — someone would re-enter on that."""
    wide = {-60: 0.30, -30: 0.30, 0: 2.40, 30: 2.20, 60: 2.10}
    crv = eventspread.curve("FOMC", rows=rows(3, shape=wide))
    assert crv["recovery"] is None
    assert eventspread.clock(crv, dt.datetime.now(UTC), dt.datetime.now(UTC)) is None


# --- the shape ------------------------------------------------------------------ #

def test_the_curve_finds_the_calm_the_peak_and_the_way_home(app):
    crv = eventspread.curve("NFP", rows=rows(3))
    assert crv["occurrences"] == 3
    assert crv["calm"] == 0.30
    assert crv["peak"]["minute"] == 0
    assert crv["peak"]["median"] == 2.40
    assert crv["recovery"] == 30
    assert round(crv["multiple"], 1) == 8.0


def test_the_calm_baseline_ignores_the_positioning_right_before(app):
    """The fifteen minutes before a print are already not calm."""
    assert eventspread.CALM_TO <= -30


def test_samples_beyond_the_span_are_dropped(app):
    noisy = dict(SHAPE)
    noisy[600] = 9.99
    crv = eventspread.curve("NFP", rows=rows(3, shape=noisy))
    assert max(p["minute"] for p in crv["points"]) == eventspread.SPAN
    assert crv["peak"]["median"] == 2.40      # the stray sample never becomes the peak


# --- the clock --------------------------------------------------------------------- #

def test_the_clock_counts_down_the_minutes_left(app):
    crv = eventspread.curve("NFP", rows=rows(3))
    at = dt.datetime(2026, 9, 4, 12, 30, tzinfo=UTC)
    tick = eventspread.clock(crv, at, at + dt.timedelta(minutes=10))
    assert tick["left"] == 20
    assert eventspread.clock(crv, at, at + dt.timedelta(minutes=45))["left"] == 0


# --- is today safe ------------------------------------------------------------------ #

def _ev(at, title="NFP"):
    return {"title": title, "at": at, "impact": "High", "country": "USD", "forecast": "", "previous": ""}


def test_a_release_in_an_hour_says_do_not_enter(app):
    now = dt.datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
    v = eventspread.today([_ev(now + dt.timedelta(hours=1))], now)
    assert v["band"] == "avoid"


def test_a_release_later_today_says_careful(app):
    now = dt.datetime(2026, 9, 4, 2, 0, tzinfo=UTC)
    v = eventspread.today([_ev(now + dt.timedelta(hours=6))], now)
    assert v["band"] == "careful"


def test_a_release_still_settling_counts_as_avoid(app):
    """Thirty minutes after the print is the most expensive moment to re-enter."""
    now = dt.datetime(2026, 9, 4, 12, 30, tzinfo=UTC)
    v = eventspread.today([_ev(now - dt.timedelta(minutes=30))], now)
    assert v["band"] == "avoid"


def test_an_empty_calendar_is_clear(app):
    now = dt.datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
    v = eventspread.today([], now)
    assert v["band"] == "clear" and v["next"] is None
    assert "tiada berita merah" in eventspread.today_line(v, goldcal.fmt_myt)


# --- the checker keeps the half that matters ------------------------------------------ #

def test_the_log_window_reaches_past_the_release(app):
    """Recovery is the half of the story that decides re-entry, so the window
    has to cover the hour after, not just the half hour before."""
    assert caltool.LOG_MINUTES >= 60
    at = dt.datetime(2026, 9, 4, 12, 30, tzinfo=UTC)
    assert goldcal.in_window(_ev(at), at + dt.timedelta(minutes=55), caltool.LOG_MINUTES)


def test_red_events_can_look_further_back_for_the_log(app):
    now = dt.datetime(2026, 9, 4, 14, 0, tzinfo=UTC)
    past = [_ev(now - dt.timedelta(minutes=90))]
    assert goldcal.red_events(now, days=2, events=past, back_hours=1) == []
    assert goldcal.red_events(now, days=2, events=past, back_hours=2) == past


# --- the surfaces ------------------------------------------------------------------------ #

def _seed(app, title="Non-Farm Employment Change", n=3):
    at = dt.datetime.now(UTC).timestamp() - 3600
    for row in rows(n, at=at):
        store.db().execute("INSERT OR REPLACE INTO event_spreads (title, event_at, ts, spread) VALUES (?, ?, ?, ?)",
                           (title, row["event_at"], row["ts"], row["spread"]))
    store.db().commit()


def test_calendar_spread_answers_in_the_bot(app):
    with app.app_context():
        _seed(app)
        reply = caltool.bot_calendar(["spread"], chat_id=7)
        assert "Non-Farm" in reply
        assert "8.0×" in reply
        assert "30 minit" in reply


def test_the_record_is_free_at_every_rank(app):
    with app.app_context():
        _seed(app)
        reply = caltool.bot_calendar(["spread"], chat_id=7)
        assert "A-Team" not in reply and "Rambo" not in reply


def test_an_unmeasured_calendar_says_it_is_still_collecting(app):
    with app.app_context():
        assert "Belum cukup acara" in caltool.bot_calendar(["spread"], chat_id=7)


def test_the_timetable_still_answers_with_no_database(app):
    """The surface contract: the bot's base answer never needs a read."""
    from app.telegram import reply_for
    assert "Gold" in reply_for("/calendar", "https://example.test")


def test_the_page_draws_the_record(client, app):
    with app.app_context():
        _seed(app)
    page = client.get("/p/gold-calendar").get_data(as_text=True)
    assert "Rekod spread acara" in page
    assert "Non-Farm" in page


def test_the_page_says_it_is_collecting_before_there_is_a_record(client, app):
    page = client.get("/p/gold-calendar").get_data(as_text=True)
    assert "Belum cukup acara" in page


def test_both_languages_carry_every_record_string(app):
    keys = [k for k in STRINGS["ms"] if k.startswith("evs.")]
    assert keys
    for key in keys:
        assert STRINGS["en"].get(key), key
