"""My Setup: the answers a tool should never ask twice.

The point of the feature is not the storage — it is that a saved answer reaches
the forms. So most of these tests assert on what a page or a bot reply actually
shows, not on what is in the table.
"""

import pytest

from app import flows, store, telegram
from app import setup as mysetup
from tests.conftest import login


# --- validation --------------------------------------------------------------- #

def test_numbers_are_numbers_and_nonsense_is_refused(app):
    with app.app_context():
        assert mysetup.clean("size", "100,000")[0] == "100000"
        assert mysetup.clean("size", "$25000")[0] == "25000"
        assert mysetup.clean("rate", "7.5")[0] == "7.5"
        assert mysetup.clean("size", "besar")[1] == "set.bad_number"
        assert mysetup.clean("size", "-4")[1] == "set.out_of_range"


def test_a_prop_firm_must_match_a_rule_pack_but_a_broker_need_not(app):
    """A firm we cannot price is worthless; a broker we have never heard of is
    still the broker they use."""
    with app.app_context():
        assert mysetup.clean("firm", "FTMO")[0] == "ftmo"
        assert mysetup.clean("firm", "Uncle Bob Capital")[1] == "set.not_an_option"
        assert mysetup.clean("broker", "Uncle Bob Markets")[0] == "Uncle Bob Markets"


def test_saving_one_field_leaves_the_rest_alone(app):
    with app.app_context():
        mysetup.save("42", {"size": "100000", "firm": "ftmo"})
        mysetup.save("42", {"size": "50000"})
        assert mysetup.read("42") == {"size": "50000", "firm": "ftmo"}


def test_clear_empties_everything(app):
    with app.app_context():
        mysetup.save("42", {"size": "100000", "lots": "40"})
        mysetup.clear("42")
        assert mysetup.read("42") == {}
        assert mysetup.filled("42") == (0, len(mysetup.KEYS))


# --- prefill -------------------------------------------------------------------- #

def test_every_prefill_target_names_a_real_setup_key(app):
    """A typo here would silently fill nothing, forever."""
    for slug, mapping in mysetup.PREFILL.items():
        for field, key in mapping.items():
            assert key in mysetup.BY_KEY, (slug, field, key)


def test_a_saved_setup_fills_the_ib_calculator_before_anything_is_typed(client, app):
    login(client, "42")
    with app.app_context():
        mysetup.save("42", {"lots": "40", "rate": "7", "clients": "25"})
    page = client.get("/p/ib-revenue-calculator").get_data(as_text=True)
    assert "value=\"40\"" in page
    assert "Tetapan Saya" in page          # the page says where the numbers came from


def test_a_typed_value_always_beats_a_saved_one(client, app):
    login(client, "42")
    with app.app_context():
        mysetup.save("42", {"lots": "40"})
    page = client.get("/p/ib-revenue-calculator?lots=999").get_data(as_text=True)
    assert "value=\"999\"" in page
    assert "value=\"40\"" not in page


def test_prefill_never_touches_a_post(app):
    """Every dashboard handler that writes gates on POST. If a prefill could
    reach one, a page visit could create a link or delete an account."""
    with app.app_context():
        mysetup.save("42", {"channel": "telegram"})
        with app.test_request_context("/p/link-attribution", method="POST", data={}):
            from flask import request
            assert mysetup.merge(request, "link-attribution", "42") is request


def test_a_visitor_with_no_setup_sees_exactly_what_they_saw_before(client, app):
    login(client, "42")
    with app.app_context():
        with app.test_request_context("/p/prop-calculator"):
            from flask import request
            assert mysetup.merge(request, "prop-calculator", "42") is request
    assert client.get("/p/prop-calculator").status_code == 200


def test_the_sentinel_form_arrives_carrying_the_saved_firm_and_size(client, app):
    """Its form is POST-only, so the template reads the setup directly."""
    login(client, "42")
    with app.app_context():
        mysetup.save("42", {"firm": "the5ers", "size": "50000"})
    page = client.get("/p/drawdown-sentinel").get_data(as_text=True)
    assert 'value="the5ers" selected' in page
    assert 'value="50000"' in page


# --- the page --------------------------------------------------------------------- #

def test_the_page_needs_a_sign_in_and_then_saves(client, app):
    assert client.get("/setup").status_code == 302
    login(client, "42")
    assert client.get("/setup").status_code == 200
    client.post("/setup", data={"size": "100000", "firm": "ftmo"}, follow_redirects=True)
    with app.app_context():
        assert mysetup.read("42") == {"size": "100000", "firm": "ftmo"}


def test_a_bad_number_is_reported_and_nothing_else_is_lost(client, app):
    login(client, "42")
    client.post("/setup", data={"lots": "40"}, follow_redirects=True)
    page = client.post("/setup", data={"size": "banyak"}).get_data(as_text=True)
    assert "mesti nombor" in page
    with app.app_context():
        assert mysetup.read("42")["lots"] == "40"


def test_the_dashboard_card_says_how_much_is_filled_in(client, app):
    login(client, "42")
    with app.app_context():
        mysetup.save("42", {"size": "100000"})
    page = client.get("/dashboard").get_data(as_text=True)
    assert "Tetapan Saya" in page
    assert "1 daripada %d" % len(mysetup.KEYS) in page


# --- the bot ------------------------------------------------------------------------ #

def test_the_bot_reads_it_back_and_writes_one_key(app):
    with app.app_context():
        assert "Belum ada" in mysetup.bot_setup([], chat_id=7)
        reply = mysetup.bot_setup(["size=100000"], chat_id=7)
        assert "Disimpan" in reply and "100,000" not in reply and "100000" in reply
        assert "100000" in mysetup.bot_setup([], chat_id=7)


def test_the_bot_shows_the_label_not_the_key(app):
    with app.app_context():
        mysetup.bot_setup(["firm=ftmo"], chat_id=7)
        assert "FTMO" in mysetup.bot_setup([], chat_id=7)


def test_a_bad_value_is_explained_rather_than_swallowed(app):
    with app.app_context():
        assert "nombor" in mysetup.bot_setup(["size=besar"], chat_id=7)
        assert mysetup.read("7") == {}


def test_setup_clear_from_the_bot(app):
    with app.app_context():
        mysetup.bot_setup(["lots=40"], chat_id=7)
        assert "dikosongkan" in mysetup.bot_setup(["clear"], chat_id=7)
        assert mysetup.read("7") == {}


def test_an_empty_setup_opens_the_guided_flow_instead_of_a_lecture(app):
    with app.app_context():
        actions = telegram._handle_message(7, "/setup", {"id": 7})
        assert actions[0][0] == "send"
        assert actions[0][2].startswith(mysetup.label("broker"))   # the first question, with buttons
        assert actions[0][3] is not None


def test_a_filled_setup_reads_back_instead_of_asking_again(app):
    with app.app_context():
        mysetup.save("7", {"size": "100000"})
        actions = telegram._handle_message(7, "/setup", {"id": 7})
        assert "100000" in actions[0][2]


def test_the_flow_writes_the_answers_and_reads_them_back(app):
    with app.app_context():
        store.tg_touch(7, "tester", "Test")      # the flow's state lives on the bot user row
        actions = flows.start("setup", 7)
        for step in flows.FLOWS["setup"]:
            value = {"broker": "hfm", "firm": "ftmo", "channel": "telegram"}.get(step["key"], "40")
            actions = flows.on_text(value, 7)
        text = actions[-1][2]
        assert "HFM" in text and "FTMO" in text
        assert mysetup.read("7")["lots"] == "40"


def test_every_setup_flow_step_is_optional_so_nobody_is_trapped(app):
    for step in flows.FLOWS["setup"]:
        assert step["optional"], step["key"]


def test_the_flow_keys_are_the_setup_keys(app):
    assert [s["key"] for s in flows.FLOWS["setup"]] == list(mysetup.KEYS)


def test_setup_is_not_a_product_command(app):
    """It answers for many tools, so it must not sit in the product dispatch
    table — that table is what the surface-contract test counts."""
    from app.tools import BOT, DASHBOARD
    assert "setup" not in BOT
    assert "setup" not in DASHBOARD
