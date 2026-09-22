"""The Telegram half of every product — SAMBANGGOLD voice, button-driven.

A webhook-only bot needs one POST route and a couple of outbound calls, so this
talks to the Bot API directly over HTTPS rather than pulling in an async
framework that Flask would have to bridge.

UX rules, carried over from Sam's other bots:

* language picker first, remembered; ``/language`` re-opens it
* the main menu never has more than three actions
* every screen has a way back; callbacks edit the message in place so the chat
  stays clean
* every ``/start`` is logged with its deep-link tag for attribution
"""

import time
from urllib.parse import quote

import requests
from flask import Blueprint, current_app, jsonify, request

from . import flows, store
from .brand import DEFAULT_LANG, normalise_lang, t
from .products import BY_SLUG, PRODUCTS, command_index
from .tools import BOT

bp = Blueprint("telegram", __name__)

API = "https://api.telegram.org/bot%s/%s"
TIMEOUT = 10

# The one-tap example each live tool answers with. Keys are product slugs.
SAMPLES = {
    "gold-watch": "/watch XAUUSD",
    "prop-calculator": "/propcalc 500 100000 15",
    "ib-revenue-calculator": "/ibcalc 40 7 25 5",
    "gold-calendar": "/calendar",
    "signal-verifier": "/verify GOLD 2431.5",
    "rebate-auditor": "/rebateaudit 42.5 8 300",
    "churn-radar": "/ibchurn",
    "broker-comparator": "/goldspread 1 overnight",
    "link-attribution": "/funnel 30",
    "drawdown-sentinel": "/sentinel status",
    "monte-carlo-sim": "/simulate 45 2 1 ftmo",
    "exposure-monitor": "/exposure XAUUSD buy 1, EURUSD buy 1, GBPUSD buy 0.5, USDJPY sell 1",
    "tokenized-gold": "/paxg",
    "miner-divergence": "/miners",
    "bot-scam-detector": "/audit @wallet_verify_b0t send your seed phrase to claim the airdrop",
    "copy-trade-audit": "/copyaudit exness 2 10",
    "red-flag-scanner": "/scan 100% accuracy guaranteed, no risk, only 3 VIP spots left, DM me",
    "influencer-audit": "/influencer @gold_guru guaranteed 10% monthly, lambo giveaway, join my broker https://broker.example/?refid=123",
}


# --- Bot API --------------------------------------------------------------- #

def _call(method, payload, token=None):
    token = token or current_app.config["TELEGRAM_BOT_TOKEN"]
    if not token:
        current_app.logger.warning("TELEGRAM_BOT_TOKEN unset — %s not sent.", method)
        return None
    return requests.post(API % (token, method), json=payload, timeout=TIMEOUT)


def send_message(chat_id, text, token=None, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
               "link_preview_options": {"is_disabled": True}}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _call("sendMessage", payload, token)


def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML",
               "link_preview_options": {"is_disabled": True}}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _call("editMessageText", payload)


def answer_callback(callback_id):
    return _call("answerCallbackQuery", {"callback_query_id": callback_id})


def set_webhook(base_url, token):
    return requests.post(
        API % (token, "setWebhook"),
        json={"url": "%s/webhook/telegram" % base_url.rstrip("/")},
        timeout=TIMEOUT,
    )


# The "/" command list and the Menu button Telegram shows next to the input.
# Registered once, in both languages, so the bot is button-driven from the very
# first screen — before the user has tapped anything.
COMMANDS = {
    "ms": [("start", "Menu utama"), ("tools", "Cuba alat percuma"), ("watch", "Harga emas & alert"),
           ("calendar", "Kalendar emas & alert"), ("propcalc", "EV cabaran prop firm"), ("ibcalc", "Anggaran hasil IB"),
           ("verify", "Sahkan harga signal"), ("scan", "Imbas pitch signal"), ("audit", "Semak bot Telegram"), ("copyaudit", "Semak broker copy-trade"),
           ("influencer", "Audit influencer"), ("rebateaudit", "Audit rebate IB"), ("ibchurn", "Radar churn klien"), ("goldspread", "Banding kos broker emas"), ("funnel", "Funnel pautan IB"), ("sentinel", "Jaga garisan drawdown"), ("simulate", "Simulasi lulus challenge"), ("exposure", "Semak dedahan buku"), ("paxg", "Premium PAXG/XAUT"), ("walletcheck", "Semak wallet payout"), ("miners", "Saringan pelombong vs emas"), ("register", "Cari nama dalam daftar awam"), ("brief", "Ringkasan Pagi — satu mesej sehari"), ("setup", "Tetapan Saya — isi sekali"), ("autopilot", "Autopilot harian (A-Team)"), ("broker", "Naik pangkat percuma — akaun HFM"), ("invite", "Jemput kawan, dapat pangkat"), ("seats", "Kerusi pasukan (Rambo)"), ("widget", "Widget jenama sendiri (Rambo)"), ("webhook", "Webhook keluar (Rambo)"), ("groups", "Kumpulan diawasi (A-Team)"), ("dashboard", "Buka dashboard"), ("language", "Tukar bahasa"), ("help", "Semua arahan")],
    "en": [("start", "Main menu"), ("tools", "Try a free tool"), ("watch", "Gold price & alerts"),
           ("calendar", "Gold calendar & alerts"), ("propcalc", "Prop challenge EV"), ("ibcalc", "IB revenue estimate"),
           ("verify", "Verify a signal price"), ("scan", "Scan a signal pitch"), ("audit", "Check a Telegram bot"), ("copyaudit", "Check a copy-trade broker"),
           ("influencer", "Audit an influencer"), ("rebateaudit", "IB rebate audit"), ("ibchurn", "Client churn radar"), ("goldspread", "Compare gold broker cost"), ("funnel", "IB link funnel"), ("sentinel", "Guard the drawdown lines"), ("simulate", "Simulate the challenge"), ("exposure", "Check book exposure"), ("paxg", "PAXG/XAUT premium"), ("walletcheck", "Check a payout wallet"), ("miners", "Miners vs gold screen"), ("register", "Search the public register"), ("brief", "Morning Brief — one message a day"), ("setup", "My Setup — fill it once"), ("autopilot", "Daily autopilot (A-Team)"), ("broker", "Free rank — HFM account"), ("invite", "Invite a friend, earn rank"), ("seats", "Team seats (Rambo)"), ("widget", "White-label widget (Rambo)"), ("webhook", "Outbound webhook (Rambo)"), ("groups", "Watched groups (A-Team)"), ("dashboard", "Open dashboard"), ("language", "Switch language"), ("help", "All commands")],
}


def webhook_info(token):
    """What Telegram thinks our webhook is, or None when we cannot ask."""
    try:
        r = requests.get(API % (token, "getWebhookInfo"), timeout=TIMEOUT)
        body = r.json()
    except Exception:
        return None
    return body.get("result") if isinstance(body, dict) and body.get("ok") else None


def set_commands(token):
    """Register the command list (default = Bahasa Melayu, plus English) and the Menu button."""
    results = []
    for code, cmds in (("", COMMANDS["ms"]), ("ms", COMMANDS["ms"]), ("en", COMMANDS["en"])):
        payload = {"commands": [{"command": c, "description": d} for c, d in cmds]}
        if code:
            payload["language_code"] = code
        results.append(requests.post(API % (token, "setMyCommands"), json=payload, timeout=TIMEOUT))
    results.append(requests.post(API % (token, "setChatMenuButton"), json={"menu_button": {"type": "commands"}}, timeout=TIMEOUT))
    return results


# --- keyboards ------------------------------------------------------------- #

def kb(rows):
    return {"inline_keyboard": rows}


def btn(text, data=None, url=None):
    return {"text": text, "url": url} if url else {"text": text, "callback_data": data}


def _base_url():
    return current_app.config["PUBLIC_BASE_URL"].rstrip("/")


USERNAME_RETRY_SECONDS = 300


def bot_username():
    """The bot's @username: from config, else asked of the Bot API once and cached on the app."""
    username = current_app.config["TELEGRAM_BOT_USERNAME"]
    if username:
        return username
    token = current_app.config["TELEGRAM_BOT_TOKEN"]
    if not token or current_app.testing:
        return ""
    cache = current_app.extensions.setdefault("sambanggold", {})
    hit = cache.get("bot_username")
    if hit and (hit[0] or time.time() - hit[1] < USERNAME_RETRY_SECONDS):
        return hit[0]
    name = ""
    try:
        body = requests.get(API % (token, "getMe"), timeout=TIMEOUT).json()
        name = (body.get("result") or {}).get("username") or ""
    except (requests.RequestException, ValueError):
        current_app.logger.warning("getMe failed; the Telegram login button stays hidden until it succeeds.")
    cache["bot_username"] = (name, time.time())
    return name


def _bot_link():
    username = bot_username()
    return "https://t.me/%s" % username if username else _base_url()


def _share_url(lang):
    text = t("bot.share_text", lang)
    return "https://t.me/share/url?url=%s&text=%s" % (quote(_bot_link(), safe=""), quote(text, safe=""))


def lang_keyboard():
    return kb([[btn("🇲🇾 Bahasa Melayu", "lang_ms")], [btn("🇬🇧 English", "lang_en")]])


def menu_keyboard(lang):
    rows = [
        [btn(t("bot.btn_tools", lang), "menu_tools")],
        [btn(t("bot.btn_dash", lang), url=_base_url() + "/dashboard")],
        [btn(t("bot.btn_faq", lang), "menu_faq")],
    ]
    channel = current_app.config["PUBLIC_CHANNEL_URL"]
    if channel:
        rows.append([btn(t("bot.btn_channel", lang), url=channel)])
    return kb(rows)


# Eighteen buttons in one list is a wall. The same three audiences the landing
# page speaks to sort them into rooms small enough to read.
PATHS = (
    ("p1", "🧑\u200d💻", ("signal-verifier", "bot-scam-detector", "red-flag-scanner",
                          "influencer-audit", "copy-trade-audit", "gold-watch", "gold-calendar")),
    ("p2", "🏦", ("prop-calculator", "monte-carlo-sim", "drawdown-sentinel", "exposure-monitor")),
    ("p3", "🤝", ("ib-revenue-calculator", "rebate-auditor", "churn-radar",
                  "broker-comparator", "link-attribution")),
    ("p4", "🪙", ("tokenized-gold", "miner-divergence")),
)
BY_PATH = {key: slugs for key, _, slugs in PATHS}


def tools_keyboard(lang):
    """Pick who you are first. Four buttons beats eighteen."""
    rows = [[btn("%s %s" % (icon, t("bot.path_" + key, lang)), "path_%s" % key)] for key, icon, _ in PATHS]
    rows.append([btn("☀️ " + t("brief.title", lang), "brief_now"),
                 btn("🧰 " + t("set.title", lang), "run_setup")])   # fill it once, before the first form
    rows.append([btn(t("bot.btn_more", lang), "menu_queued")])
    rows.append([btn(t("bot.btn_menu", lang), "menu_main")])
    return kb(rows)


def path_keyboard(key, lang):
    """The tools for one audience, two to a row."""
    rows, row = [], []
    for slug in BY_PATH.get(key, ()):
        p = BY_SLUG.get(slug)
        if not p or slug not in SAMPLES:
            continue
        row.append(btn("%s %s" % (p.emoji, p.view(lang).name), "tool_%s" % slug))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([btn(t("bot.btn_tools", lang), "menu_tools"), btn(t("bot.btn_menu", lang), "menu_main")])
    return kb(rows)


def tool_keyboard(product, lang):
    return kb([
        [btn(t("flow.start", lang), "run_%s" % product.slug), btn(t("flow.example", lang), "try_%s" % product.slug)],
        [btn(t("bot.btn_open", lang), url="%s/p/%s" % (_base_url(), product.slug))],
        [btn(t("bot.btn_back", lang), "menu_tools"), btn(t("bot.btn_menu", lang), "menu_main")],
    ])


def result_keyboard(product, lang, chat_id=None):
    rows = []
    if product.slug == "gold-calendar":
        on = bool(chat_id and store.calendar_subscribed(chat_id))
        rows.append([btn(t("cal.btn_off" if on else "cal.btn_on", lang), "cal_off" if on else "cal_on")])
    if product.slug in flows.FLOWS:
        rows.append([btn(t("bot.btn_again", lang), "run_%s" % product.slug)])
    elif product.slug in SAMPLES:
        rows.append([btn(t("bot.btn_again", lang), "try_%s" % product.slug)])
    rows.append([btn(t("bot.btn_open", lang), url="%s/p/%s" % (_base_url(), product.slug)),
                 btn(t("bot.btn_share", lang), url=_share_url(lang))])
    rows.append([btn(t("bot.btn_menu", lang), "menu_main")])
    return kb(rows)


def setup_keyboard(lang):
    """Read it back, change it with buttons, or open the page."""
    return kb([
        [btn("✏️ " + t("set.title", lang), "run_setup")],
        [btn(t("set.open", lang), url=_base_url() + "/setup")],
        [btn(t("bot.btn_menu", lang), "menu_main")],
    ])


def back_keyboard(lang, to="menu_main"):
    return kb([[btn(t("bot.btn_menu", lang), to)]])


# --- screens ----------------------------------------------------------------- #

def help_text(lang=DEFAULT_LANG):
    lines = [t("bot.help", lang), ""]
    for product in PRODUCTS:
        command = product.view(lang).bot_commands[0][0]
        lines.append("%s %s — <code>%s</code>" % (product.emoji, product.name, command))
    lines += ["", t("bot.help_tail", lang)]
    return "\n".join(lines)


def tool_card(product, lang):
    v = product.view(lang)
    return t("bot.tool_card", lang, emoji=v.emoji, name=v.name, solution=v.solution,
             free=v.free_tier, command=v.bot_commands[0][0])


def queued_text(lang):
    lines = [t("bot.queued", lang), ""]
    for p in PRODUCTS:
        if p.slug not in SAMPLES:
            lines.append("%s %s — <code>%s</code>" % (p.emoji, p.name, p.view(lang).bot_commands[0][0]))
    return "\n".join(lines)


def reply_for(text, base_url="", chat_id=None, lang=DEFAULT_LANG):
    """Answer for one typed command. Pure text, so the tests can call it."""
    parts = text.strip().split()
    word = parts[0].lstrip("/").split("@")[0] if parts else ""
    if word in ("start", "help", ""):
        return help_text(lang)

    product = command_index().get(word)
    if product is None:
        return t("bot.unknown", lang)

    page = "%s/p/%s" % (base_url.rstrip("/"), product.slug)
    handler = BOT.get(word)
    if handler is not None:
        return "%s <b>%s</b>\n%s\n\nDashboard: %s" % (
            product.emoji, product.name, handler(parts[1:], chat_id=chat_id, lang=lang), page)
    v = product.view(lang)
    if product.status == "shipped":
        head = "%s <b>%s</b>\n%s" % (v.emoji, v.name, v.solution)
    else:
        head = t("bot.queued_reply", lang, emoji=v.emoji, name=v.name, solution=v.solution)
    return "%s\n\n%s: %s\nDashboard: %s" % (head, t("product.free", lang), v.free_tier, page)


# --- update handling --------------------------------------------------------- #

def _lang_for(user):
    """Stored choice → Telegram client language → None (ask)."""
    if not user:
        return DEFAULT_LANG
    return store.tg_lang(user["id"]) or normalise_lang(user.get("language_code"))


def handle_update(update):
    """Turn one Telegram update into a list of API actions.

    Actions are ("send", chat_id, text, keyboard), ("edit", chat_id, message_id,
    text, keyboard) or ("answer", callback_id). The webhook executes them; tests
    read them.
    """
    if "callback_query" in update:
        return _handle_callback(update["callback_query"])
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text", "")
    user = message.get("from") or {}
    if not chat_id or not text:
        return []
    if chat.get("type") in ("group", "supergroup"):
        return _handle_group(chat, text, user)
    return _handle_message(chat_id, text, user)


def _handle_group(chat, text, user):
    """A message in a room the bot was pointed at.

    Only two commands answer in a group, and both reply once. Everything else
    is read, scanned in memory, and never replied to — the bot is a watcher
    here, not a participant, so it never posts into someone's group.
    """
    from . import groups
    group = {"id": chat.get("id"), "title": chat.get("title", "")}
    author = user.get("id")
    word = text.strip().split()[0].lstrip("/").split("@")[0].lower() if text.strip() else ""
    lang = store.tg_lang(author) or _lang_for({"id": author, "language_code": user.get("language_code")}) or DEFAULT_LANG

    if word in ("watchgroup", "unwatchgroup"):
        fn = groups.bot_watchgroup if word == "watchgroup" else groups.bot_unwatchgroup
        return [("send", chat["id"], fn([], chat_id=author, lang=lang, group=group, author=author), None)]

    out = []
    groups.inspect(group["id"], group["title"], author,
                   user.get("username") or user.get("first_name", ""), text,
                   lambda who, body: out.append(("send", who, body, None)))
    return out


def _handle_message(chat_id, text, user):
    parts = text.strip().split()
    word = parts[0].lstrip("/").split("@")[0].lower() if parts else ""
    tag = parts[1] if word == "start" and len(parts) > 1 else None
    store.tg_touch(user.get("id", chat_id), user.get("username", ""), user.get("first_name", ""),
                   tag=tag, start=(word == "start"))
    if tag and str(tag).startswith("ref_"):
        from .doors import attach            # a referral link only counts on the first /start
        attach(chat_id, tag)
    lang = _lang_for({"id": user.get("id", chat_id), "language_code": user.get("language_code")})

    if word == "start":
        if lang is None:
            return [("send", chat_id, t("bot.pick_lang"), lang_keyboard())]
        return [("send", chat_id, t("bot.welcome", lang), None),
                ("send", chat_id, t("bot.menu", lang), menu_keyboard(lang))]
    if word == "language":
        return [("send", chat_id, t("bot.pick_lang"), lang_keyboard())]

    lang = lang or DEFAULT_LANG
    if not text.strip().startswith("/"):
        answered = flows.on_text(text, chat_id, lang)
        if answered is not None:
            return answered
    flows.cancel(chat_id)   # a fresh command ends any open flow
    if word == "tools":
        return [("send", chat_id, t("bot.tools", lang), tools_keyboard(lang))]
    if word == "dashboard":
        return [("send", chat_id, t("bot.dash", lang), kb([[btn(t("bot.btn_dash", lang), url=_base_url() + "/dashboard")]]))]
    if word == "help":
        return [("send", chat_id, help_text(lang), back_keyboard(lang))]
    if word == "register":
        from . import register as reg      # one lookup across four scanners, not any one product's
        return [("send", chat_id, reg.bot_register(parts[1:], chat_id=chat_id, lang=lang),
                 kb([[btn(t("reg.title", lang), url=_base_url() + "/register")],
                     [btn(t("bot.btn_menu", lang), "menu_main")]]))]
    if word == "brief":
        from . import brief                  # one message for many tools, not any one product's
        return [("send", chat_id, brief.bot_brief(parts[1:], chat_id=chat_id, lang=lang), back_keyboard(lang))]
    if word == "setup":
        from . import setup as mysetup     # not a product: one answer sheet for many tools
        if len(parts) == 1 and not mysetup.read(str(chat_id)):
            return flows.start("setup", chat_id, lang)      # nothing saved yet — ask with buttons
        return [("send", chat_id, mysetup.bot_setup(parts[1:], chat_id=chat_id, lang=lang), setup_keyboard(lang))]
    if word == "autopilot":
        from .autopilot import bot_autopilot   # a rank feature, not a product command
        return [("send", chat_id, bot_autopilot(parts[1:], chat_id=chat_id, lang=lang), back_keyboard(lang))]
    if word in ("broker", "invite", "seats", "widget", "webhook", "groups", "unwatchgroup"):
        from . import doors, groups, seats, whitelabel   # the ladder's own commands, not any one product's
        fn = {"broker": doors.bot_broker, "invite": doors.bot_invite, "seats": seats.bot_seats,
              "widget": whitelabel.bot_widget, "webhook": whitelabel.bot_hook,
              "groups": groups.bot_groups, "unwatchgroup": groups.bot_unwatchgroup}[word]
        return [("send", chat_id, fn(parts[1:], chat_id=chat_id, lang=lang), back_keyboard(lang))]

    product = command_index().get(word)
    if product is None:
        return [("send", chat_id, t("bot.unknown", lang), menu_keyboard(lang))]
    if len(parts) == 1 and product.slug in flows.FLOWS and flows.FLOWS[product.slug] and word == product.bot_commands[0][0].split()[0].lstrip("/"):
        return flows.start(product.slug, chat_id, lang)   # `/scan` alone: ask, don't lecture
    return [("send", chat_id, reply_for(text, _base_url(), chat_id=chat_id, lang=lang), result_keyboard(product, lang, chat_id))]


def _handle_callback(query):
    data = query.get("data", "")
    user = query.get("from") or {}
    message = query.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    message_id = message.get("message_id")
    actions = [("answer", query.get("id"))]
    if not chat_id:
        return actions
    store.tg_touch(user.get("id", chat_id), user.get("username", ""), user.get("first_name", ""))

    if data in ("lang_ms", "lang_en"):
        lang = data[-2:]
        first_pick = store.tg_lang(user.get("id", chat_id)) is None
        store.tg_set_lang(user.get("id", chat_id), lang)
        if first_pick:
            actions.append(("edit", chat_id, message_id, t("bot.welcome", lang), None))
            actions.append(("send", chat_id, t("bot.menu", lang), menu_keyboard(lang)))
        else:
            actions.append(("edit", chat_id, message_id, t("bot.lang_set", lang), menu_keyboard(lang)))
        return actions

    lang = _lang_for({"id": user.get("id", chat_id), "language_code": user.get("language_code")}) or DEFAULT_LANG

    if data == "menu_main":
        actions.append(("edit", chat_id, message_id, t("bot.menu", lang), menu_keyboard(lang)))
    elif data == "menu_tools":
        actions.append(("edit", chat_id, message_id, t("bot.tools", lang), tools_keyboard(lang)))
    elif data.startswith("path_"):
        key = data[5:]
        actions.append(("edit", chat_id, message_id, t("bot.path_head", lang, who=t("bot.path_" + key, lang)),
                        path_keyboard(key, lang)))
    elif data == "brief_now":
        from . import brief
        actions.append(("send", chat_id, brief.bot_brief([], chat_id=chat_id, lang=lang), back_keyboard(lang)))
    elif data == "menu_queued":
        actions.append(("edit", chat_id, message_id, queued_text(lang), back_keyboard(lang, "menu_tools")))
    elif data == "menu_faq":
        actions.append(("edit", chat_id, message_id, t("bot.faq", lang), back_keyboard(lang)))
    elif data.startswith("tool_"):
        product = _product_by_slug(data[5:])
        if product:
            actions.append(("edit", chat_id, message_id, tool_card(product, lang), tool_keyboard(product, lang)))
    elif data.startswith("run_"):
        actions += flows.start(data[4:], chat_id, lang)
    elif data.startswith("fl_"):
        actions += flows.on_callback(data, chat_id, message_id, lang)
    elif data.startswith("try_"):
        product = _product_by_slug(data[4:])
        sample = SAMPLES.get(product.slug) if product else None
        if sample:
            actions.append(("send", chat_id, reply_for(sample, _base_url(), chat_id=chat_id, lang=lang),
                            result_keyboard(product, lang, chat_id)))
    elif data in ("cal_on", "cal_off"):
        store.calendar_toggle(chat_id, data == "cal_on")
        product = _product_by_slug("gold-calendar")
        actions.append(("edit", chat_id, message_id, reply_for("/calendar", _base_url(), chat_id=chat_id, lang=lang),
                        result_keyboard(product, lang, chat_id)))
    return actions


def _product_by_slug(slug):
    for p in PRODUCTS:
        if p.slug == slug:
            return p
    return None


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


@bp.route("/webhook/telegram", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    perform(handle_update(update))
    return jsonify(ok=True)
