"""The internal team bot: role-gated at every command, separate token from
the customer bot, same store.py the dashboard reads."""

from app import store
from app.teambot import handle_update


def msg(text, uid=7, lang_code=None):
    frm = {"id": uid, "username": "sam", "first_name": "Sam"}
    if lang_code:
        frm["language_code"] = lang_code
    return {"message": {"chat": {"id": uid}, "from": frm, "text": text}}


def tap(data, uid=7, message_id=99):
    return {"callback_query": {"id": "cb1", "data": data, "from": {"id": uid, "username": "sam", "first_name": "Sam"},
                               "message": {"message_id": message_id, "chat": {"id": uid}}}}


def buttons(keyboard):
    return [b["text"] for row in keyboard["inline_keyboard"] for b in row]


def test_stranger_gets_no_access_and_nothing_else(app):
    with app.app_context():
        actions = handle_update(msg("/start", uid=1))
        assert len(actions) == 1
        assert actions[0][0] == "send"
        assert "internal team" in actions[0][2] or "pasukan dalaman" in actions[0][2]


def test_stranger_callback_is_also_refused(app):
    with app.app_context():
        actions = handle_update(tap("menu_tasks", uid=1))
        kinds = [a[0] for a in actions]
        assert kinds == ["answer", "edit"]


def test_ceo_start_shows_welcome_and_four_button_menu(app):
    with app.app_context():
        store.set_team_role("7", "ceo", display_name="Sam")
        actions = handle_update(msg("/start"))
        assert "CEO" in actions[0][2]
        labels = buttons(actions[1][3])
        assert "👥 Team" in labels or "👥 Pasukan" in labels   # CEO-only People button


def test_executive_menu_has_no_people_button(app):
    with app.app_context():
        store.set_team_role("7", "executive")
        actions = handle_update(msg("/start"))
        labels = buttons(actions[1][3])
        assert "👥 Team" not in labels and "👥 Pasukan" not in labels


def test_whoami_reports_role(app):
    with app.app_context():
        store.set_team_role("7", "hod_sales")
        actions = handle_update(msg("/whoami", lang_code="en"))
        assert "HOD Sales" in actions[0][2]


def test_tasks_list_shows_open_tasks_and_mark_done_for_admins(app):
    with app.app_context():
        store.set_team_role("7", "hod_sales")
        store.add_task("Call top lead", created_by="7")
        actions = handle_update(msg("/tasks", lang_code="en"))
        assert "Call top lead" in actions[0][2]
        labels = buttons(actions[0][3])
        assert any("Mark done" in l for l in labels)


def test_executive_sees_tasks_but_no_mark_done_button(app):
    with app.app_context():
        store.set_team_role("999", "executive")
        store.add_task("Call top lead", created_by="1")
        actions = handle_update(msg("/tasks", uid=999))
        labels = buttons(actions[0][3])
        assert not any("Mark done" in l for l in labels)


def test_tap_task_done_marks_it_and_re_renders(app):
    with app.app_context():
        store.set_team_role("7", "ceo")
        t = store.add_task("Ship report", created_by="7")
        actions = handle_update(tap("task_done_%d" % t["id"]))
        assert store.task(t["id"])["status"] == "done"
        assert actions[1][0] == "edit"


def test_executive_cannot_mark_a_task_done_via_callback(app):
    with app.app_context():
        store.set_team_role("7", "executive")
        t = store.add_task("Ship report", created_by="1")
        handle_update(tap("task_done_%d" % t["id"]))
        assert store.task(t["id"])["status"] == "open"   # callback silently ignored, no crash


def test_only_ceo_can_promote(app):
    with app.app_context():
        store.set_team_role("7", "hod_marketing")
        actions = handle_update(msg("/promote 555 executive"))
        assert "Only the CEO" in actions[0][2] or "Hanya CEO" in actions[0][2]
        assert store.team_role("555") is None


def test_ceo_can_promote(app):
    with app.app_context():
        store.set_team_role("7", "ceo")
        handle_update(msg("/promote 555 hod_sales"))
        assert store.team_role("555") == "hod_sales"


def test_promote_rejects_unknown_role(app):
    with app.app_context():
        store.set_team_role("7", "ceo")
        actions = handle_update(msg("/promote 555 intern", lang_code="en"))
        assert "Unknown role" in actions[0][2]
        assert store.team_role("555") is None


def test_broadcast_requires_group_configured(app):
    with app.app_context():
        store.set_team_role("7", "ceo")
        actions = handle_update(msg("/broadcast hello team"))
        assert "TEAM_GROUP_CHAT_ID" in actions[0][2]


def test_broadcast_sends_to_group_when_configured(app):
    app.config["TEAM_GROUP_CHAT_ID"] = "-100555"
    with app.app_context():
        store.set_team_role("7", "ceo")
        actions = handle_update(msg("/broadcast hello team"))
        assert actions[0] == ("send", "-100555", "hello team", None)


def test_executive_cannot_broadcast(app):
    app.config["TEAM_GROUP_CHAT_ID"] = "-100555"
    with app.app_context():
        store.set_team_role("7", "executive")
        actions = handle_update(msg("/broadcast hello"))
        assert "Only the CEO" in actions[0][2] or "Hanya CEO" in actions[0][2]


def test_files_category_picker_then_list(app):
    with app.app_context():
        store.set_team_role("7", "executive")
        store.add_file_item("doc", "Test Doc", "drive", "https://example.test/doc")
        actions = handle_update(msg("/files"))
        assert actions[0][0] == "send"
        cat_actions = handle_update(tap("files_cat_doc"))
        assert "Test Doc" in cat_actions[1][3]
