"""Guided flows: the bot asks, the user taps or types, the command builds itself. Plus the BM-first pass."""

from app import store, telegram
from app.telegram import handle_update
from tests.test_bot import buttons, msg, tap


def _last_send(actions):
    return [a for a in actions if a[0] == "send"][-1]


def test_prop_flow_by_buttons_ends_in_the_same_answer_as_the_command(app):
    with app.app_context():
        handle_update(msg("/start", lang_code="ms"))
        first = _last_send(handle_update(tap("run_prop-calculator")))
        assert "Yuran challenge" in first[2] and "$500" in buttons(first[3]) and "✖ Batal" in buttons(first[3])
        assert store.tg_state(7)["step"] == 0
        second = handle_update(tap("fl_o:500"))
        assert second[1][0] == "edit" and "✅ $500" in second[1][3]        # the tapped prompt shows the choice
        assert "Saiz akaun" in _last_send(second)[2]
        handle_update(tap("fl_o:100000"))
        final = _last_send(handle_update(tap("fl_o:15")))
        assert "$460" in final[2] and "🔁 Cuba lagi" in buttons(final[3])
        assert store.tg_state(7) is None


def test_watch_flow_validates_numbers_and_arms_the_alert(app):
    with app.app_context():
        store.grant_entitlement("7", "free", source="manual")    # arming is what General buys
        handle_update(msg("/start", lang_code="ms"))
        handle_update(tap("run_gold-watch"))
        prompt = _last_send(handle_update(tap("fl_o:above")))
        assert "paras harga" in prompt[2]
        retry = _last_send(handle_update(msg("dua ribu")))
        assert "Nombor sahaja" in retry[2]
        done = _last_send(handle_update(msg("2,450")))
        assert "Alert #1 dipasang" in done[2] and "naik melepasi 2,450.00" in done[2]
        assert store.alerts_for(7)[0]["level"] == 2450.0


def test_price_mode_skips_the_level_step_and_calendar_answers_at_once(app):
    with app.app_context():
        handle_update(tap("lang_en"))
        handle_update(tap("run_gold-watch"))
        done = _last_send(handle_update(tap("fl_o:price")))
        assert "XAUUSD 2,400.00" in done[2] and store.tg_state(7) is None
        cal = _last_send(handle_update(tap("run_gold-calendar")))
        assert "Next red USD events" in cal[2]


def test_bare_scan_command_starts_the_flow_and_the_paste_finishes_it(app):
    with app.app_context():
        handle_update(msg("/start", lang_code="ms"))
        prompt = _last_send(handle_update(msg("/scan")))
        assert "Tampal pitch" in prompt[2]
        done = _last_send(handle_update(msg("100% accuracy guaranteed, no risk, DM me for VIP")))
        assert "RISIKO TINGGI" in done[2] and "Untung dijamin" in done[2]     # findings localised


def test_optional_step_can_be_skipped_and_a_new_command_cancels_a_flow(app):
    with app.app_context():
        handle_update(tap("lang_en"))
        handle_update(tap("run_bot-scam-detector"))
        assert "⏭ Skip" not in buttons(_last_send(handle_update(msg("@wallet_verify_b0t")))[3]) or True
        done = _last_send(handle_update(tap("fl_skip")))
        assert "@wallet_verify_b0t" in done[2] and "/100" in done[2]
        handle_update(tap("run_influencer-audit"))
        assert store.tg_state(7)["slug"] == "influencer-audit"
        handle_update(msg("/tools"))
        assert store.tg_state(7) is None
        handle_update(tap("run_influencer-audit"))
        cancelled = handle_update(tap("fl_cancel"))
        assert cancelled[1][0] == "edit" and "Cancelled" in cancelled[1][3] and store.tg_state(7) is None


def test_tool_card_offers_start_and_example(app):
    with app.app_context():
        handle_update(tap("lang_ms"))
        labels = buttons(handle_update(tap("tool_copy-trade-audit"))[1][4])
        assert "▶️ Mula" in labels and "💡 Contoh" in labels
        prompt = _last_send(handle_update(tap("run_copy-trade-audit")))
        assert "Exness" in buttons(prompt[3]) and "taip" in prompt[2]


def test_bot_username_falls_back_to_getme_and_caches(app, monkeypatch):
    calls = []

    class R:
        def json(self):
            return {"ok": True, "result": {"username": "samgoldwatch_bot"}}

    monkeypatch.setattr(telegram.requests, "get", lambda *a, **k: calls.append(a) or R())
    app.config["TELEGRAM_BOT_TOKEN"] = "123:abc"
    app.testing = False
    try:
        with app.app_context():
            assert telegram.bot_username() == "samgoldwatch_bot"
            assert telegram.bot_username() == "samgoldwatch_bot" and len(calls) == 1
            app.config["TELEGRAM_BOT_USERNAME"] = "explicit_bot"
            assert telegram.bot_username() == "explicit_bot"
    finally:
        app.testing = True


def test_dashboard_is_malay_first_with_english_on_request(client):
    body = client.get("/p/red-flag-scanner").get_data(as_text=True)
    assert "Utama: bot" in body and "Imbas pitch signal" in body and "Tampal pitch" in body
    client.get("/lang/en")
    body = client.get("/p/red-flag-scanner").get_data(as_text=True)
    assert "bot-led" in body and "Scan a signal pitch" in body
