"""The internal team bot — a second, dedicated Telegram bot (its own token,
`TEAM_BOT_TOKEN`) for Sam's CEO/HODs/Executives only. Deliberately separate
from `telegram.py`'s customer-facing `@samproducts_bot`: different token,
different webhook, so internal traffic never mixes with customer traffic
and a customer can never stumble into team commands.

Every command checks `store.team_role()` first — same table the dashboard
reads (`teamauth.py`), so there is exactly one place access is granted:
`/team/people` on the dashboard, or `/promote` here.

Mirrors `telegram.py`'s shape: `handle_update()` turns one update into a
list of actions, `perform()` executes them, the webhook route ties the two
together. Kept pure/testable the same way.
"""

import time

import requests
from flask import Blueprint, current_app, jsonify, request

from . import library, roadmap as roadmap_mod, store, teamcalendar
from .auth import normalise_lang
from .brand import DEFAULT_LANG, t

bp = Blueprint("teambot", __name__)

API = "https://api.telegram.org/bot%s/%s"
TIMEOUT = 10


# --- Bot API ----------------------------------------------------------------- #

def _token():
    return current_app.config["TEAM_BOT_TOKEN"]


def _call(method, payload):
    token = _token()
    if not token:
        current_app.logger.warning("TEAM_BOT_TOKEN unset — %s not sent.", method)
        return None
    return requests.post(API % (token, method), json=payload, timeout=TIMEOUT)


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
               "link_preview_options": {"is_disabled": True}}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _call("sendMessage", payload)


def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML",
               "link_preview_options": {"is_disabled": True}}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _call("editMessageText", payload)


def answer_callback(callback_id, text=None):
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    return _call("answerCallbackQuery", payload)


def send_document(chat_id, file_path, caption=""):
    token = _token()
    if not token:
        current_app.logger.warning("TEAM_BOT_TOKEN unset — document not sent.")
        return None
    with open(file_path, "rb") as fh:
        return requests.post(
            API % (token, "sendDocument"),
            data={"chat_id": chat_id, "caption": caption[:1024]},
            files={"document": fh},
            timeout=30,
        )


def set_webhook(base_url, token):
    return requests.post(API % (token, "setWebhook"),
                         json={"url": "%s/webhook/teambot" % base_url.rstrip("/")}, timeout=TIMEOUT)


def set_commands(token):
    cmds = [("start", "Menu"), ("tasks", "Tasks"), ("calendar", "Calendar"), ("files", "Files"),
            ("people", "Team (CEO)"), ("promote", "Grant a role (CEO)"), ("broadcast", "Message the team group"),
            ("whoami", "My role")]
    payload = {"commands": [{"command": c, "description": d} for c, d in cmds]}
    return requests.post(API % (token, "setMyCommands"), json=payload, timeout=TIMEOUT)


# --- keyboards ----------------------------------------------------------------- #

def kb(rows):
    return {"inline_keyboard": rows}


def btn(text, data=None, url=None):
    return {"text": text, "url": url} if url else {"text": text, "callback_data": data}


def _base_url():
    return current_app.config["PUBLIC_BASE_URL"].rstrip("/")


def menu_keyboard(role, lang):
    rows = [[btn(t("team.bot_menu_tasks", lang), "menu_tasks"), btn(t("team.bot_menu_calendar", lang), "menu_calendar")],
            [btn(t("team.bot_menu_files", lang), "menu_files")]]
    if role == "ceo":
        rows[-1].append(btn(t("team.bot_menu_people", lang), "menu_people"))
    return kb(rows)


def back_keyboard(lang):
    return kb([[btn(t("team.bot_back", lang), "menu_main")]])


def files_categories_keyboard(lang):
    return kb([[btn(t("team.category_" + c, lang), "files_cat_%s" % c)] for c in store.FILE_CATEGORIES]
              + [[btn(t("team.bot_back", lang), "menu_main")]])


def tasks_keyboard(tasks, can_edit, lang):
    rows = []
    if can_edit:
        for tk in tasks:
            if tk["status"] != "done":
                rows.append([btn("%s — %s" % (t("team.bot_mark_done", lang), tk["title"][:30]), "task_done_%d" % tk["id"])])
    rows.append([btn(t("team.bot_back", lang), "menu_main")])
    return kb(rows)


def files_list_keyboard(items, lang):
    rows = []
    for it in items:
        if it["source"] == "drive":
            rows.append([btn("🔗 " + it["title"][:40], url=it["url"])])
        else:
            rows.append([btn("⬇️ " + it["title"][:40], "file_dl_%d" % it["id"])])
    rows.append([btn(t("team.bot_back", lang), "menu_files")])
    return kb(rows)


# --- screens ----------------------------------------------------------------- #

def _role_label(role, lang):
    return t("team.role_" + role, lang)


def tasks_text(role, owner, lang):
    tasks = store.tasks_all(status=None)
    open_tasks = [tk for tk in tasks if tk["status"] != "done"][:20]
    if not open_tasks:
        return t("team.bot_no_open_tasks", lang), open_tasks
    lines = []
    for tk in open_tasks:
        due = time.strftime("%d %b", time.gmtime(tk["due_at"])) if tk["due_at"] else "—"
        lines.append("%s — <i>%s</i> (%s)" % (tk["title"], t("team.task_status_" + tk["status"], lang), due))
    return "\n".join(lines), open_tasks


def calendar_text(lang):
    today = __import__("datetime").date.today()
    start, end = teamcalendar.day_bounds(today)
    today_tasks = store.tasks_due_between(start, end)
    week_days = teamcalendar.week_days(0)
    w_start, _ = teamcalendar.day_bounds(week_days[0])
    _, w_end = teamcalendar.day_bounds(week_days[-1])
    week_tasks = store.tasks_due_between(w_start, w_end)

    lines = [t("team.bot_calendar_today", lang)]
    lines += ["• " + tk["title"] for tk in today_tasks] if today_tasks else [t("team.bot_no_open_tasks", lang)]
    lines += ["", t("team.bot_calendar_week", lang)]
    lines += ["• " + tk["title"] for tk in week_tasks] if week_tasks else [t("team.bot_no_open_tasks", lang)]
    return "\n".join(lines)


# --- update handling ----------------------------------------------------------- #

def _lang_for(user):
    return normalise_lang(user.get("language_code")) or DEFAULT_LANG


def handle_update(update):
    """Same action-list shape as telegram.py's handle_update — ("send", ...),
    ("edit", ...), ("answer", ...), plus ("document", chat_id, path, caption)
    for a file download."""
    if "callback_query" in update:
        return _handle_callback(update["callback_query"])
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text", "")
    user = message.get("from") or {}
    if not chat_id or not text or chat.get("type") not in (None, "private"):
        return []
    return _handle_message(chat_id, text, user)


def _handle_message(chat_id, text, user):
    parts = text.strip().split()
    word = parts[0].lstrip("/").split("@")[0].lower() if parts else ""
    lang = _lang_for(user)
    telegram_id = str(user.get("id", chat_id))
    role = store.team_role(telegram_id)

    if role is None:
        return [("send", chat_id, t("team.bot_no_access", lang), None)]

    name = user.get("first_name") or telegram_id
    can_edit = role in store.TEAM_FULL_ACCESS_ROLES

    if word == "start":
        return [("send", chat_id, t("team.bot_welcome", lang, name=name, role=_role_label(role, lang)), None),
                ("send", chat_id, t("team.bot_menu", lang), menu_keyboard(role, lang))]
    if word == "whoami":
        return [("send", chat_id, t("team.bot_whoami", lang, name=name, role=_role_label(role, lang)), None)]
    if word == "tasks":
        body, tasks = tasks_text(role, telegram_id, lang)
        return [("send", chat_id, body, tasks_keyboard(tasks, can_edit, lang))]
    if word == "calendar":
        return [("send", chat_id, calendar_text(lang),
                 kb([[btn(t("team.bot_open_full_calendar", lang), url=_base_url() + "/team/calendar")],
                     [btn(t("team.bot_back", lang), "menu_main")]]))]
    if word == "files":
        return [("send", chat_id, t("team.bot_pick_category", lang), files_categories_keyboard(lang))]
    if word == "people":
        if role != "ceo":
            return [("send", chat_id, t("team.bot_promote_denied", lang), None)]
        lines = ["%s — %s" % (m["display_name"] or m["owner"], _role_label(m["role"], lang)) for m in store.list_team_members()]
        return [("send", chat_id, "\n".join(lines) or t("team.no_people", lang), back_keyboard(lang))]
    if word == "promote":
        if role != "ceo":
            return [("send", chat_id, t("team.bot_promote_denied", lang), None)]
        if len(parts) != 3:
            return [("send", chat_id, t("team.bot_promote_usage", lang), None)]
        if parts[2] not in store.TEAM_ROLES:
            return [("send", chat_id, t("team.bot_promote_bad_role", lang), None)]
        store.set_team_role(parts[1], parts[2], added_by=telegram_id)
        return [("send", chat_id, t("team.bot_promote_done", lang, owner=parts[1], role=_role_label(parts[2], lang)), None)]
    if word == "broadcast":
        if not can_edit:
            return [("send", chat_id, t("team.bot_promote_denied", lang), None)]
        group = current_app.config["TEAM_GROUP_CHAT_ID"]
        if not group:
            return [("send", chat_id, t("team.bot_broadcast_no_group", lang), None)]
        if len(parts) < 2:
            return [("send", chat_id, t("team.bot_broadcast_usage", lang), None)]
        body = text.split(None, 1)[1]
        return [("send", group, body, None), ("send", chat_id, t("team.bot_broadcast_sent", lang), None)]

    return [("send", chat_id, t("team.bot_menu", lang), menu_keyboard(role, lang))]


def _handle_callback(query):
    data = query.get("data", "")
    user = query.get("from") or {}
    message = query.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    message_id = message.get("message_id")
    actions = [("answer", query.get("id"))]
    if not chat_id:
        return actions

    lang = _lang_for(user)
    telegram_id = str(user.get("id", chat_id))
    role = store.team_role(telegram_id)
    if role is None:
        actions.append(("edit", chat_id, message_id, t("team.bot_no_access", lang), None))
        return actions
    can_edit = role in store.TEAM_FULL_ACCESS_ROLES

    if data == "menu_main":
        actions.append(("edit", chat_id, message_id, t("team.bot_menu", lang), menu_keyboard(role, lang)))
    elif data == "menu_tasks":
        body, tasks = tasks_text(role, telegram_id, lang)
        actions.append(("edit", chat_id, message_id, body, tasks_keyboard(tasks, can_edit, lang)))
    elif data == "menu_calendar":
        actions.append(("edit", chat_id, message_id, calendar_text(lang),
                        kb([[btn(t("team.bot_open_full_calendar", lang), url=_base_url() + "/team/calendar")],
                            [btn(t("team.bot_back", lang), "menu_main")]])))
    elif data == "menu_files":
        actions.append(("edit", chat_id, message_id, t("team.bot_pick_category", lang), files_categories_keyboard(lang)))
    elif data == "menu_people":
        if role != "ceo":
            actions.append(("edit", chat_id, message_id, t("team.bot_promote_denied", lang), back_keyboard(lang)))
        else:
            lines = ["%s — %s" % (m["display_name"] or m["owner"], _role_label(m["role"], lang)) for m in store.list_team_members()]
            actions.append(("edit", chat_id, message_id, "\n".join(lines) or t("team.no_people", lang), back_keyboard(lang)))
    elif data.startswith("task_done_") and can_edit:
        task_id = int(data[len("task_done_"):])
        store.update_task(task_id, status="done")
        body, tasks = tasks_text(role, telegram_id, lang)
        actions.append(("edit", chat_id, message_id, body, tasks_keyboard(tasks, can_edit, lang)))
    elif data.startswith("files_cat_"):
        category = data[len("files_cat_"):]
        items = store.file_items(category=category)
        text_body = "\n".join(it["title"] for it in items) or t("team.bot_no_files_category", lang)
        actions.append(("edit", chat_id, message_id, text_body, files_list_keyboard(items, lang)))
    elif data.startswith("file_dl_"):
        item_id = int(data[len("file_dl_"):])
        item = next((it for it in store.file_items() if it["id"] == item_id), None)
        if item and item["source"] in ("repo_asset", "volume"):
            root = library.ROOT if item["source"] == "repo_asset" else current_app.config["PAID_LIBRARY_PATH"]
            actions.append(("document", chat_id, "%s/%s" % (root, item["url"]), item["title"]))

    return actions


def perform(actions):
    for action in actions:
        if action[0] == "send":
            _, chat_id, text, keyboard = action
            send_message(chat_id, text, reply_markup=keyboard)
        elif action[0] == "edit":
            _, chat_id, message_id, text, keyboard = action
            edit_message(chat_id, message_id, text, reply_markup=keyboard)
        elif action[0] == "answer":
            answer_callback(action[1])
        elif action[0] == "document":
            _, chat_id, file_path, caption = action
            send_document(chat_id, file_path, caption)


@bp.route("/webhook/teambot", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    perform(handle_update(update))
    return jsonify(ok=True)
