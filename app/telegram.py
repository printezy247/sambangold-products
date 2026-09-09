"""The Telegram half of every product.

A webhook-only bot needs one POST route and one outbound call, so this talks to
the Bot API directly over HTTPS rather than pulling in an async framework that
Flask would have to bridge.
"""

import requests
from flask import Blueprint, current_app, jsonify, request

from .products import PRODUCTS, command_index

bp = Blueprint("telegram", __name__)

API = "https://api.telegram.org/bot%s/%s"
TIMEOUT = 10


def send_message(chat_id, text, token=None):
    token = token or current_app.config["TELEGRAM_BOT_TOKEN"]
    if not token:
        current_app.logger.warning("TELEGRAM_BOT_TOKEN unset — message not sent.")
        return None
    return requests.post(
        API % (token, "sendMessage"),
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=TIMEOUT,
    )


def set_webhook(base_url, token):
    return requests.post(
        API % (token, "setWebhook"),
        json={"url": "%s/webhook/telegram" % base_url.rstrip("/")},
        timeout=TIMEOUT,
    )


def help_text():
    lines = ["<b>Every product answers here and on the dashboard.</b>", ""]
    for product in PRODUCTS:
        command = product.bot_commands[0][0]
        lines.append("%s %s — <code>%s</code>" % (product.emoji, product.name, command))
    lines.append("")
    lines.append("Educational research only. Not financial advice.")
    return "\n".join(lines)


def reply_for(text, base_url=""):
    """Answer for one incoming message. Pure, so the tests can call it."""
    word = text.strip().split()[0].lstrip("/").split("@")[0] if text.strip() else ""
    if word in ("start", "help", ""):
        return help_text()

    product = command_index().get(word)
    if product is None:
        return "Unknown command. Send /help for the full list."

    page = "%s/p/%s" % (base_url.rstrip("/"), product.slug)
    if product.status == "shipped":
        head = "%s <b>%s</b>\n%s" % (product.emoji, product.name, product.solution)
    else:
        head = (
            "%s <b>%s</b> — queued for build.\n%s"
            % (product.emoji, product.name, product.solution)
        )
    return "%s\n\nFree tier: %s\nDashboard: %s" % (head, product.free_tier, page)


@bp.route("/webhook/telegram", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or update.get("edited_message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text = message.get("text", "")

    if chat_id and text:
        send_message(chat_id, reply_for(text, current_app.config["PUBLIC_BASE_URL"]))
    return jsonify(ok=True)
