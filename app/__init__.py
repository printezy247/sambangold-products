"""Application factory.

One Flask app carries all eighteen products: a page per product on the web
side, a command per product on the bot side, and one Telegram identity linking
the two.
"""

import time

import click
from flask import Flask

from .config import Config


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config["MISSING"] = config_object.missing()

    from . import auth, store, telegram, views, watch
    app.register_blueprint(views.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(telegram.bp)
    app.teardown_appcontext(store.close_db)

    @app.template_filter("utc")
    def utc(ts):
        return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts))

    @app.cli.command("check-alerts")
    def check_alerts_command():
        """Fire every armed alert that has crossed. Run from cron."""
        import json
        click.echo(json.dumps(watch.check_alerts(telegram.send_message)))

    @app.cli.command("set-webhook")
    def set_webhook_command():
        """Point Telegram at PUBLIC_BASE_URL/webhook/telegram. Run once after deploy."""
        base, token = app.config["PUBLIC_BASE_URL"], app.config["TELEGRAM_BOT_TOKEN"]
        if not token:
            raise click.ClickException("TELEGRAM_BOT_TOKEN is not set.")
        click.echo(telegram.set_webhook(base, token).text)

    return app
