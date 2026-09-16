"""Configuration read from the environment. No secret is ever committed."""

import os


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-only-not-for-production")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:5000")
    ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID", "")
    # The internal team bot — a separate token from TELEGRAM_BOT_TOKEN on
    # purpose, so customer traffic and Sam's CEO/HOD/Executive traffic never
    # share a bot. Unset means the team bot simply doesn't run yet.
    TEAM_BOT_TOKEN = os.environ.get("TEAM_BOT_TOKEN", "")
    TEAM_BOT_USERNAME = os.environ.get("TEAM_BOT_USERNAME", "")
    # Sam's internal Telegram group, for /broadcast and the Phase 4 daily digest.
    TEAM_GROUP_CHAT_ID = os.environ.get("TEAM_GROUP_CHAT_ID", "")
    # Optional AI layer on top of /team/chat's local file search — an
    # OpenAI-compatible chat-completions API. All three must be set or the
    # chat falls back to local search only (which always works, key or not).
    # NARA_MODEL is a comma-separated priority list; a failing/rate-limited
    # model just rotates to the next one rather than failing the request.
    NARA_API_KEY = os.environ.get("NARA_API_KEY", "")
    NARA_BASE_URL = os.environ.get("NARA_BASE_URL", "")
    NARA_MODEL = os.environ.get("NARA_MODEL", "")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/sambangold.db")
    # Paid-tier docs (sold as ebooks on website_sam) never go in git — this repo
    # is public. Uploaded once to the Railway volume, outside the deploy;
    # served the same way as library/ but from here instead. Absent locally
    # and in tests, which is fine — the library just has fewer items.
    PAID_LIBRARY_PATH = os.environ.get("PAID_LIBRARY_PATH", "/data/library")
    # The bot's @username (no @). The Telegram Login Widget needs it.
    TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "")
    PUBLIC_CHANNEL_URL = os.environ.get("PUBLIC_CHANNEL_URL", "")
    # Any free SMTP relay: a Gmail app password, Brevo, a local relay.
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = os.environ.get("SMTP_PORT", "587")
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")
    MAIL_FROM = os.environ.get("MAIL_FROM", "")
    # Email sign-in codes: 8 digits, ten minutes, five tries, one per minute.
    CODE_TTL_SECONDS = 600
    CODE_MAX_ATTEMPTS = 5
    CODE_RESEND_SECONDS = 60
    # Shared secret the scheduler sends to POST /tasks/check-alerts.
    TASK_TOKEN = os.environ.get("TASK_TOKEN", "")

    # Telegram login payloads older than this are refused.
    AUTH_MAX_AGE_SECONDS = 86400

    @classmethod
    def missing(cls):
        """Names of the settings that must be filled before going live."""
        return [
            name for name in ("FLASK_SECRET_KEY", "TELEGRAM_BOT_TOKEN")
            if not os.environ.get(name)
        ]
