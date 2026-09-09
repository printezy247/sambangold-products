"""Configuration read from the environment. No secret is ever committed."""

import os


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-only-not-for-production")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:5000")
    ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID", "")

    # Telegram login payloads older than this are refused.
    AUTH_MAX_AGE_SECONDS = 86400

    @classmethod
    def missing(cls):
        """Names of the settings that must be filled before going live."""
        return [
            name for name in ("FLASK_SECRET_KEY", "TELEGRAM_BOT_TOKEN")
            if not os.environ.get(name)
        ]
