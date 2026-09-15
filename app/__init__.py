"""Application factory.

One Flask app carries all eighteen products: a page per product on the web
side, a command per product on the bot side, and one Telegram identity linking
the two.
"""

import time

import click
from flask import Flask

from .config import Config


# SBG monogram in a rotating gold ring — Sam's Glyph component, as plain SVG.
GLYPH = (
    '<svg width="%d" height="%d" viewBox="0 0 40 40" aria-hidden="true" class="glyph">'
    '<defs><linearGradient id="g-gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f5d76e"/><stop offset="1" stop-color="#a87d0f"/></linearGradient>'
    '<linearGradient id="g-chrome" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#8f99a8"/></linearGradient></defs>'
    '<circle cx="20" cy="20" r="18.5" fill="#050609"/>'
    '<g class="glyph-ring"><circle cx="20" cy="20" r="17" fill="none" stroke="url(#g-gold)" stroke-width="1.6" stroke-dasharray="30 6 8 6 40 6" opacity=".95"/></g>'
    '<text x="20" y="25" text-anchor="middle" font-size="14" font-style="italic" font-family="Anton, Impact, sans-serif" class="glyph-core">'
    '<tspan fill="url(#g-chrome)">SB</tspan><tspan fill="url(#g-gold)">G</tspan></text></svg>'
)


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config["MISSING"] = config_object.missing()

    from . import auth, brand, store, telegram, tiers, views, watch
    from markupsafe import Markup
    app.register_blueprint(views.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(telegram.bp)
    app.teardown_appcontext(store.close_db)

    @app.context_processor
    def inject_brand():
        lang = auth.lang()
        username = telegram.bot_username()
        return {
            "BRAND": brand.BRAND, "TOKENS": brand.TOKENS, "lang": lang,
            "t": lambda key, **kw: brand.t(key, lang, **kw),
            "rank_label": lambda rank: brand.rank_label(rank, lang),
            "user": auth.current_user(),
            "bot_username": username,
            "bot_link": ("https://t.me/%s" % username) if username else "",
            "glyph": lambda size=28: Markup(GLYPH % (size, size)),
            "TIERS": tiers.TIERS, "tier_by_key": tiers.tier_by_key, "fmt_usd": tiers.fmt_usd,
            "feature_rows": tiers.FEATURE_ROWS,
            "feature_label": lambda f: tiers.feature_label(f, lang),
            "tier_for_feature": tiers.tier_for_feature,
        }

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
        for r in telegram.set_commands(token):
            click.echo(r.text)

    return app
