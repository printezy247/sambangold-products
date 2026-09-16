"""The Morning Brief — one message, at your hour, with the day's risk in it.

Eighteen tools is eighteen things to remember to check, and nobody checks
eighteen. These tests are mostly about the two ways a daily push goes wrong:
sending twice, and sending at the wrong hour for someone who lives in KL.
"""

import time

from app import brief, store
from app.brand import STRINGS
from tests.conftest import login

KL = brief.KL_OFFSET


def at_kl(hour, day_offset=0):
    """A timestamp whose Kuala Lumpur hour is exactly `hour`."""
    base = time.time() + day_offset * 86400
    midnight_kl = base - ((base + KL) % 86400)
    return midnight_kl + hour * 3600 + 60


def grant(owner, tier="free"):
    store.grant_entitlement(owner, tier, source="manual", external_id="test:%s" % owner)


# --- the hour ------------------------------------------------------------------- #

def test_the_hour_is_kuala_lumpur_not_utc(app):
    """Someone choosing when to be woken is not going to convert time zones."""
    assert brief.kl_hour(at_kl(8)) == 8
    assert brief.kl_hour(at_kl(23)) == 23


def test_setting_and_clearing_the_hour(app):
    with app.app_context():
        assert brief.set_hour("42", "8") == 8
        assert brief.hour_of("42") == 8
        assert brief.set_hour("42", "07:30") == 7        # a typed clock time still lands
        brief.off("42")
        assert brief.hour_of("42") is None


def test_a_nonsense_hour_is_refused(app):
    with app.app_context():
        for bad in ("pagi", "25", "-1", ""):
            assert brief.set_hour("42", bad) is None
        assert brief.hour_of("42") is None


# --- the run --------------------------------------------------------------------- #

def test_it_sends_at_the_chosen_hour_and_not_before(app):
    sent = []
    with app.app_context():
        grant("42")
        brief.set_hour("42", 8)
        assert brief.run_due(lambda o, t: sent.append((o, t)), at_kl(7))["brief_sent"] == 0
        assert brief.run_due(lambda o, t: sent.append((o, t)), at_kl(8))["brief_sent"] == 1


def test_it_never_sends_twice_in_one_kl_day(app):
    sent = []
    with app.app_context():
        grant("42")
        brief.set_hour("42", 8)
        brief.run_due(lambda o, t: sent.append(t), at_kl(8))
        brief.run_due(lambda o, t: sent.append(t), at_kl(8) + 300)
        assert len(sent) == 1


def test_a_quiet_morning_still_marks_the_day_done(app):
    """Otherwise a silent 8am piles up into a second message at noon."""
    with app.app_context():
        grant("42")
        brief.set_hour("42", 8)
        import app.brief as mod
        original = mod.SECTIONS
        mod.SECTIONS = ()
        try:
            assert brief.run_due(lambda o, t: None, at_kl(8))["brief_sent"] == 0
            assert store.get_setting(brief.SLUG, "42", brief.SENT_KEY) == brief._day(at_kl(8))
        finally:
            mod.SECTIONS = original


def test_a_rank_that_lapsed_stops_the_push_but_keeps_the_subscription(app):
    sent = []
    with app.app_context():
        brief.set_hour("42", 8)                      # public: no rank
        out = brief.run_due(lambda o, t: sent.append(t), at_kl(8))
        assert out["brief_sent"] == 0 and out["brief_gated"] == 1
        assert brief.hour_of("42") == 8              # the switch survives the lapse


# --- what is in it ------------------------------------------------------------------ #

def test_one_dead_section_never_eats_the_brief(app):
    """A feed goes down; the rest of the morning still arrives."""
    import app.brief as mod
    def boom(owner, lang, now):
        raise RuntimeError("feed down")
    original = mod.SECTIONS
    mod.SECTIONS = (("boom", boom), ("ok", lambda o, l, n: "still here"))
    try:
        with app.app_context():
            assert "still here" in mod.build("42")
    finally:
        mod.SECTIONS = original


def test_nothing_to_say_produces_no_message_rather_than_an_empty_one(app):
    import app.brief as mod
    original = mod.SECTIONS
    mod.SECTIONS = (("none", lambda o, l, n: None),)
    try:
        with app.app_context():
            assert mod.build("42") is None
    finally:
        mod.SECTIONS = original


def test_your_own_overnight_movement_is_in_it(app):
    with app.app_context():
        store.add_alert("42", "XAUUSD", "above", 2400)
        alert = store.alerts_for("42")[0]
        store.record_trigger(alert, {"bid": 2449.0, "ask": 2450.0, "mid": 2449.5,
                                     "spread": 1.0, "source": "test"})
        out = brief._yours("42", "ms", time.time())
        assert "1 alert" in out and "2,450" in out


def test_a_visitor_with_nothing_of_their_own_gets_no_yours_section(app):
    with app.app_context():
        assert brief._yours("42", "ms", time.time()) is None


# --- the bot -------------------------------------------------------------------------- #

def test_brief_reads_it_now_for_anyone(app):
    """Reading it stays free. Being sent it is the rank."""
    with app.app_context():
        reply = brief.bot_brief([], chat_id=7)
        assert "Ringkasan Pagi" in reply or "Tiada apa" in reply
        assert "/brief 8" in reply


def test_setting_the_hour_needs_the_rank(app):
    with app.app_context():
        assert "General" in brief.bot_brief(["8"], chat_id=7)
        grant("7")
        assert "08:00" in brief.bot_brief(["8"], chat_id=7)
        assert brief.hour_of("7") == 8


def test_brief_off_stops_it(app):
    with app.app_context():
        grant("7")
        brief.bot_brief(["8"], chat_id=7)
        assert "dimatikan" in brief.bot_brief(["off"], chat_id=7)
        assert brief.hour_of("7") is None


def test_a_bad_hour_is_explained(app):
    with app.app_context():
        grant("7")
        assert "0 hingga 23" in brief.bot_brief(["pagi"], chat_id=7)


def test_the_command_is_dispatched_by_the_bot(app):
    from app import telegram
    with app.app_context():
        actions = telegram._handle_message(7, "/brief", {"id": 7})
        assert actions[0][0] == "send"
        assert "/brief 8" in actions[0][2]


def test_brief_is_not_a_product_command(app):
    """It answers for many tools, so it must stay out of the product table."""
    from app.tools import BOT, DASHBOARD
    assert "brief" not in BOT and "brief" not in DASHBOARD


# --- the dashboard ------------------------------------------------------------------------ #

def test_the_panel_offers_the_hour_and_a_preview(client, app):
    login(client, "42", rank="free")
    page = client.get("/dashboard").get_data(as_text=True)
    assert "Ringkasan Pagi" in page
    assert 'value="8"' in page


def test_the_panel_sells_the_rank_instead_of_hiding(client, app):
    login(client, "42")                        # public
    page = client.get("/dashboard").get_data(as_text=True)
    assert "Ringkasan Pagi" in page
    assert "General" in page


def test_saving_the_hour_from_the_dashboard(client, app):
    login(client, "42", rank="free")
    client.post("/dashboard", data={"action": "brief", "hour": "6"}, follow_redirects=True)
    with app.app_context():
        assert brief.hour_of("42") == 6
    client.post("/dashboard", data={"action": "brief", "hour": "off"}, follow_redirects=True)
    with app.app_context():
        assert brief.hour_of("42") is None


# --- the checker ---------------------------------------------------------------------------- #

def test_the_checker_reports_the_brief(app, client):
    from app import watch
    with app.app_context():
        out = watch.check_alerts(lambda o, t: None)
        assert "brief_sent" in out and "brief_gated" in out


def test_both_languages_carry_every_brief_string(app):
    keys = [k for k in STRINGS["ms"] if k.startswith("brief.")]
    assert keys
    for key in keys:
        assert STRINGS["en"].get(key), key
