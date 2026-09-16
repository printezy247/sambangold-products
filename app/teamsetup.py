"""Shared logic for one-time team-ops setup: seed the roadmap/file library,
bootstrap the first CEO role, and point the team bot's webhook at this
deploy.

Called from two places:
* `flask team-seed` / `flask team-set-webhook` — local CLI. Only correct
  when run *inside* the deployed container (same DATABASE_PATH,
  PAID_LIBRARY_PATH volume mount) — running it on a laptop against
  `railway run` would touch a local, empty `/data` instead of the real one.
* `POST /tasks/team-setup` (teamviews.py) — runs inside the live app
  itself, so it always has the right environment and volume. This is the
  one to use from outside the deploy (curl, browser), no local Python
  needed — same shared-secret pattern as `/tasks/check-alerts`.
"""

from flask import current_app

from . import library, roadmap, store


def seed_all():
    """Roadmap + file library, including the paid-tier volume if it's been
    uploaded. Returns counts for a status report."""
    store.seed_roadmap(roadmap.seed_data())
    store.seed_file_items(library.seed_data())
    paid = library.scan_paid_files(current_app.config["PAID_LIBRARY_PATH"])
    if paid:
        store.seed_file_items(paid)
    return {"roadmap_items": len(store.roadmap_items()),
            "file_items": len(store.file_items()),
            "paid_items": len(paid)}


def bootstrap_ceo():
    """Grant ADMIN_TELEGRAM_ID the first CEO role, only while no team roles
    exist yet. Returns the id granted, or None if nothing changed."""
    admin_id = current_app.config["ADMIN_TELEGRAM_ID"]
    if admin_id and not store.list_team_members():
        store.set_team_role(admin_id, "ceo", display_name="Sam", added_by="system")
        return admin_id
    return None


def set_team_webhook():
    """Point Telegram at this deploy's /webhook/teambot and register the
    command list. Returns None if TEAM_BOT_TOKEN isn't set yet."""
    from . import teambot
    token = current_app.config["TEAM_BOT_TOKEN"]
    if not token:
        return None
    base = current_app.config["PUBLIC_BASE_URL"]
    webhook = teambot.set_webhook(base, token)
    commands = teambot.set_commands(token)
    return {"webhook": webhook.json() if webhook is not None else None,
            "commands": commands.json() if commands is not None else None}
