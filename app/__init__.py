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

    from . import auth, brand, store, teambot, teamviews, telegram, tiers, views, watch
    from markupsafe import Markup
    app.register_blueprint(views.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(telegram.bp)
    app.register_blueprint(teamviews.bp)
    app.register_blueprint(teambot.bp)
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
            "limit_rows": list(tiers.LIMITS), "limit_for": tiers.limit_for,
            "limit_label": lambda k: tiers.limit_label(k, lang),
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

    @app.cli.command("team-set-webhook")
    def team_set_webhook_command():
        """Point Telegram at PUBLIC_BASE_URL/webhook/teambot. Run once after
        the team bot's token is set."""
        base, token = app.config["PUBLIC_BASE_URL"], app.config["TEAM_BOT_TOKEN"]
        if not token:
            raise click.ClickException("TEAM_BOT_TOKEN is not set.")
        click.echo(teambot.set_webhook(base, token).text)
        click.echo(teambot.set_commands(token).text)

    @app.cli.command("team-seed")
    def team_seed_command():
        """Seed the combined product roadmap, the file library, and grant
        the first CEO role.

        Safe to re-run: seeding never overwrites a status or title a human
        already set, and the CEO grant only fills in the role if nobody
        holds it yet. Run once after deploy, and again any time a new
        product ships or a file is added to library/ (new rows insert;
        existing ones are untouched).
        """
        from . import library as library_mod
        from . import roadmap as roadmap_mod

        store.seed_roadmap(roadmap_mod.seed_data())
        click.echo("Roadmap seeded: %d items." % len(store.roadmap_items()))

        store.seed_file_items(library_mod.seed_data())
        paid = library_mod.scan_paid_files(app.config["PAID_LIBRARY_PATH"])
        if paid:
            store.seed_file_items(paid)
        click.echo("File library seeded: %d items (%d paid-tier)." % (len(store.file_items()), len(paid)))

        admin_id = app.config["ADMIN_TELEGRAM_ID"]
        if admin_id and not store.list_team_members():
            store.set_team_role(admin_id, "ceo", display_name="Sam", added_by="system")
            click.echo("Granted CEO to ADMIN_TELEGRAM_ID (%s)." % admin_id)
        elif not admin_id:
            click.echo("ADMIN_TELEGRAM_ID not set — grant the first CEO role manually via the DB or /team/people once one CEO exists.")
        else:
            click.echo("Team roles already exist — leaving them as-is.")

    return app
