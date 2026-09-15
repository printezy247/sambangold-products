"""The button-driven bot: language first, three-button menu, edit in place, retention keys."""

from app import store
from app.telegram import handle_update, help_text


def msg(text, uid=7, lang_code=None, username="ada"):
    frm = {"id": uid, "username": username, "first_name": "Ada"}
    if lang_code:
        frm["language_code"] = lang_code
    return {"message": {"chat": {"id": uid}, "from": frm, "text": text}}


def tap(data, uid=7, message_id=99):
    return {"callback_query": {"id": "cb1", "data": data, "from": {"id": uid, "username": "ada", "first_name": "Ada"},
                               "message": {"message_id": message_id, "chat": {"id": uid}}}}


def buttons(keyboard):
    return [b["text"] for row in keyboard["inline_keyboard"] for b in row]


def test_first_start_asks_language_and_logs_the_tag(app):
    with app.app_context():
        actions = handle_update(msg("/start ad_meta_01"))
        assert actions[0][0] == "send" and "Pilih bahasa" in actions[0][2]
        assert buttons(actions[0][3]) == ["🇲🇾 Bahasa Melayu", "🇬🇧 English"]
        row = store.tg_touch(7)
        assert row["tag"] == "ad_meta_01" and row["starts"] == 1


def test_language_pick_welcomes_then_shows_a_three_button_menu(app):
    with app.app_context():
        handle_update(msg("/start"))
        actions = handle_update(tap("lang_ms"))
        kinds = [a[0] for a in actions]
        assert kinds == ["answer", "edit", "send"]
        assert "SAMBANGGOLD" in actions[1][3] and "Pendidikan sahaja" in actions[1][3]
        assert actions[2][2] == "Apa yang anda mahu buat?"
        assert len(buttons(actions[2][3])) == 3   # never more than three actions on the main menu
        assert store.tg_lang(7) == "ms"


def test_telegram_client_language_skips_the_picker(app):
    with app.app_context():
        actions = handle_update(msg("/start", lang_code="en-GB"))
        assert "18 gold tools" in actions[0][2]
        assert buttons(actions[1][3]) == ["🥇 Try a free tool", "🌐 Open dashboard", "❓ FAQ"]


def test_menu_edits_in_place_and_every_screen_has_a_way_back(app):
    with app.app_context():
        handle_update(tap("lang_en"))
        for data in ("menu_tools", "menu_faq", "menu_queued", "tool_gold-watch"):
            actions = handle_update(tap(data))
            assert actions[1][0] == "edit" and actions[1][2] == 99
            labels = buttons(actions[1][4])
            assert any("Back" in l or "Main Menu" in l for l in labels), data


def test_the_tools_screen_asks_who_you_are_first(app):
    """Eighteen buttons in one list is a wall. Four rooms is a question."""
    with app.app_context():
        handle_update(tap("lang_en"))
        labels = buttons(handle_update(tap("menu_tools"))[1][4])
        assert any("I trade on my own" in l for l in labels)
        assert any("prop firm" in l for l in labels)
        assert any("IB" in l for l in labels)
        assert not any("Gold Watch" in l for l in labels)     # not until you pick a room


def test_picking_a_room_lists_only_that_audiences_live_tools(app):
    with app.app_context():
        handle_update(tap("lang_en"))
        labels = buttons(handle_update(tap("path_p1"))[1][4])
        assert any("Gold Watch" in l for l in labels)
        assert not any("Prop Firm" in l for l in labels)      # that is another room
        assert not any("Churn Radar" in l for l in labels)    # dashboard-led, never listed

        labels = buttons(handle_update(tap("path_p2"))[1][4])
        assert any("Prop Firm" in l for l in labels)
        assert any("Back" in l or "Tools" in l or "Menu" in l for l in labels)


def test_every_live_tool_lives_in_exactly_one_room(app):
    """A tool nobody can reach from the menu may as well not exist."""
    from app.telegram import PATHS, SAMPLES
    placed = [slug for _, _, slugs in PATHS for slug in slugs]
    assert len(placed) == len(set(placed)), "a tool is in two rooms"
    assert set(SAMPLES) <= set(placed), set(SAMPLES) - set(placed)


def test_try_example_runs_the_tool_and_offers_retention_keys(app):
    with app.app_context():
        handle_update(tap("lang_en"))
        actions = handle_update(tap("try_prop-calculator"))
        send = actions[1]
        assert send[0] == "send" and "$460" in send[2]
        labels = buttons(send[3])
        assert "🔁 Try again" in labels and "📤 Share" in labels and "🌐 Open on dashboard" in labels
        share = [b for row in send[3]["inline_keyboard"] for b in row if b["text"] == "📤 Share"][0]
        assert share["url"].startswith("https://t.me/share/url?")


def test_typed_command_gets_a_result_keyboard_in_the_users_language(app):
    with app.app_context():
        handle_update(tap("lang_ms"))
        actions = handle_update(msg("/ibcalc 40 7"))
        assert "$280" in actions[0][2]
        assert "⬅️ Menu Utama" in buttons(actions[0][3])


def test_language_command_reswitches_without_the_welcome(app):
    with app.app_context():
        handle_update(tap("lang_ms"))
        assert "Pilih bahasa" in handle_update(msg("/language"))[0][2]
        actions = handle_update(tap("lang_en"))
        assert [a[0] for a in actions] == ["answer", "edit"] and "Language set" in actions[1][3]


def test_unknown_command_points_back_to_the_menu(app):
    with app.app_context():
        actions = handle_update(msg("/nope", lang_code="ms"))
        assert "tak dikenali" in actions[0][2] and len(actions[0][3]["inline_keyboard"]) >= 3


def test_help_is_bilingual_and_lists_every_product(app):
    ms, en = help_text("ms"), help_text("en")
    assert "Arahan" in ms and "Commands" in en
    assert ms.count("<code>") == 18 == en.count("<code>")


def test_webhook_handles_a_callback_without_a_token(client):
    r = client.post("/webhook/telegram", json=tap("menu_main"))
    assert r.status_code == 200 and r.get_json() == {"ok": True}


def test_tools_command_opens_the_tool_picker_and_commands_are_registered(app):
    from app.telegram import COMMANDS
    with app.app_context():
        actions = handle_update(msg("/tools", lang_code="ms"))
        assert actions[0][0] == "send" and "Alat yang sudah hidup" in actions[0][2]
    assert [c for c, _ in COMMANDS["ms"]] == [c for c, _ in COMMANDS["en"]]
    assert {"start", "tools", "dashboard", "language", "help"} <= {c for c, _ in COMMANDS["ms"]}
