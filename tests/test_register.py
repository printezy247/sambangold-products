"""The public register — look someone up before you pay them.

The scanners each answer well and then forget. This reads the archive back the
other way round, by subject across everybody, so a name that keeps coming back
accumulates a page. These tests are mostly about the bar for being named on a
public page, because that page is about real businesses and real handles.
"""

import time

from app import register, store
from app.brand import STRINGS


def scan(subject, product="red-flag-scanner", score=80, verdict="HIGH RISK", days_ago=0, minute=0):
    store.db().execute(
        "INSERT INTO scans (product, subject, owner, score, verdict, report, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (product, subject, None, score, verdict, "{}", time.time() - days_ago * 86400 - minute * 60))
    store.db().commit()


def seed_listed(subject="@gold_guru_my", product="red-flag-scanner"):
    """Flagged on three separate days — a real record."""
    for day in range(3):
        scan(subject, product, score=70 + day, days_ago=day)


# --- the bar for being named ------------------------------------------------------ #

def test_one_afternoon_of_scanning_a_rival_is_not_a_record(app):
    """Five scans in an hour is one person with a grudge, not a crowd."""
    with app.app_context():
        for i in range(5):
            scan("@rival_broker", minute=i)
        assert [r["subject"] for r in register.rows()] == []


def test_a_name_flagged_across_several_days_is_listed(app):
    with app.app_context():
        seed_listed()
        listed = register.rows()
        assert [r["subject"] for r in listed] == ["@gold_guru_my"]
        assert listed[0]["days"] == 3 and listed[0]["flagged"] == 3


def test_a_clean_scan_leaves_no_entry(app):
    """The register is what the scanner flagged, so a subject that came back
    clear every time must never appear on it."""
    with app.app_context():
        for day in range(4):
            scan("@honest_broker", score=5, verdict="clear", days_ago=day)
        assert register.rows() == []


def test_the_bar_is_named_on_the_page(client, app):
    """Someone reading a public accusation-shaped list deserves to know what it
    took to get on it."""
    page = client.get("/register").get_data(as_text=True)
    assert str(register.MIN_DAYS) in page and str(register.MIN_FLAGGED) in page
    assert "bukan tuduhan" in page          # the disclaimer, not an accusation


# --- looking one up ------------------------------------------------------------------ #

def test_the_same_name_in_different_case_is_one_subject(app):
    with app.app_context():
        scan("@Gold_Guru_MY", days_ago=0)
        scan("@gold_guru_my", days_ago=1)
        scan("@GOLD_GURU_MY", days_ago=2)
        found = register.rows()
        assert len(found) == 1 and found[0]["n"] == 3


def test_looking_up_an_unknown_name_says_so_without_saying_safe(app):
    """"No record" reading as a clean bill of health is the one way this page
    could get someone hurt."""
    with app.app_context():
        reply = register.bot_register(["@never_seen"], chat_id=7)
        assert "Tiada rekod" in reply
        assert "bukan bermakna selamat" in reply


def test_a_name_under_the_bar_is_returned_marked_when_searched(app):
    """Searching a name we have seen twice must not answer "nothing" — that
    would read as an all-clear. It says: seen, not enough to list."""
    with app.app_context():
        scan("@rival_broker", minute=0)
        scan("@rival_broker", minute=5)
        row = register.lookup("@rival_broker")
        assert row is not None and row["listed"] is False


def test_the_lookup_spans_every_scanner(app):
    with app.app_context():
        seed_listed("@same_handle", product="influencer-audit")
        assert register.lookup("@same_handle")["listed"] is True


# --- the bot -------------------------------------------------------------------------- #

def test_register_answers_with_the_record(app):
    with app.app_context():
        seed_listed()
        reply = register.bot_register(["@gold_guru_my"], chat_id=7)
        assert "@gold_guru_my" in reply and "3" in reply


def test_register_with_no_name_explains_itself(app):
    with app.app_context():
        assert "/register" in register.bot_register([], chat_id=7)


def test_the_command_is_dispatched_by_the_bot(app):
    from app import telegram
    with app.app_context():
        seed_listed()
        actions = telegram._handle_message(7, "/register @gold_guru_my", {"id": 7})
        assert actions[0][0] == "send" and "@gold_guru_my" in actions[0][2]


def test_register_is_not_a_product_command(app):
    from app.tools import BOT, DASHBOARD
    assert "register" not in BOT and "register" not in DASHBOARD


# --- the page ---------------------------------------------------------------------------- #

def test_the_page_needs_no_login(client, app):
    """Someone about to be defrauded is exactly the person who has not signed up."""
    assert client.get("/register").status_code == 200


def test_the_page_lists_and_searches(client, app):
    with app.app_context():
        seed_listed()
    assert "@gold_guru_my" in client.get("/register").get_data(as_text=True)
    hit = client.get("/register?q=@GOLD_GURU_MY").get_data(as_text=True)
    assert "@gold_guru_my" in hit
    miss = client.get("/register?q=@nobody_at_all").get_data(as_text=True)
    assert "Tiada rekod" in miss


def test_the_page_can_be_filtered_to_one_scanner(client, app):
    with app.app_context():
        seed_listed("@a_handle", product="influencer-audit")
        seed_listed("@a_broker", product="copy-trade-audit")
    page = client.get("/register?p=influencer-audit").get_data(as_text=True)
    assert "@a_handle" in page and "@a_broker" not in page


def test_an_empty_register_says_it_is_still_collecting(client, app):
    assert "Belum ada nama" in client.get("/register").get_data(as_text=True)


def test_a_scanner_page_shows_the_record_it_just_matched(client, app):
    """The moment that matters: you scan a pitch and learn this name has been
    flagged six times before."""
    with app.app_context():
        seed_listed("@gold_guru_my", product="influencer-audit")
    page = client.post("/p/influencer-audit",
                       data={"subject": "@gold_guru_my", "text": "guaranteed 10% monthly, join my broker"}).get_data(as_text=True)
    assert "Daftar awam" in page or "ditanda" in page


def test_the_register_is_in_the_nav(client, app):
    assert "Daftar awam" in client.get("/").get_data(as_text=True)


def test_both_languages_carry_every_register_string(app):
    keys = [k for k in STRINGS["ms"] if k.startswith("reg.")]
    assert keys
    for key in keys:
        assert STRINGS["en"].get(key), key
