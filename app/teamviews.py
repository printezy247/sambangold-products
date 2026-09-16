"""The internal team ops dashboard: product roadmap, tasks, and role
management for Sam's CEO/HODs/Executives. Separate from the customer-facing
`views.py` — gated by `teamauth`, not by rank.
"""

import time

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from . import roadmap, store
from .auth import current_user, lang as ui_lang
from .brand import t
from .teamauth import ceo_required, is_team_admin, team_admin_required, team_required

bp = Blueprint("team", __name__, url_prefix="/team")


def _parse_due(value):
    """A date input (`YYYY-MM-DD`) to a UTC timestamp at end of day, or None."""
    if not value:
        return None
    try:
        return time.mktime(time.strptime(value, "%Y-%m-%d")) + 23 * 3600 + 59 * 60
    except ValueError:
        return None


@bp.route("/")
@team_required
def home():
    return redirect(url_for("team.roadmap_page"))


@bp.route("/roadmap", methods=["GET", "POST"])
@team_required
def roadmap_page():
    if request.method == "POST":
        if not is_team_admin():
            from flask import abort
            abort(403)
        slug = request.form.get("slug", "")
        status = request.form.get("internal_status", "")
        notes = request.form.get("notes", "")
        if status in store.ROADMAP_STATUSES:
            store.set_roadmap_status(slug, status, current_user()["owner"], notes=notes)
            flash(t("team.updated_roadmap", ui_lang()), "ok")
        return redirect(url_for("team.roadmap_page"))

    items = store.roadmap_items()
    return render_template("team/roadmap.html", groups=roadmap.grouped(items),
                           statuses=store.ROADMAP_STATUSES, can_edit=is_team_admin())


@bp.route("/tasks", methods=["GET", "POST"])
@team_required
def tasks_page():
    if request.method == "POST":
        if not is_team_admin():
            from flask import abort
            abort(403)
        title = (request.form.get("title") or "").strip()
        if title:
            store.add_task(
                title, current_user()["owner"],
                description=request.form.get("description", ""),
                priority=request.form.get("priority") or "normal",
                due_at=_parse_due(request.form.get("due")),
                assigned_to=request.form.get("assigned_to") or None,
            )
            flash(t("team.added_task", ui_lang()), "ok")
        return redirect(url_for("team.tasks_page"))

    status = request.args.get("status") or None
    tasks = store.tasks_all(status=status)
    members = store.list_team_members()
    return render_template("team/tasks.html", tasks=tasks, members=members,
                           task_statuses=("open", "in_progress", "done", "delayed"),
                           priorities=("low", "normal", "high"),
                           filter_status=status, can_edit=is_team_admin())


@bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@team_admin_required
def task_status(task_id):
    status = request.form.get("status", "")
    if status in ("open", "in_progress", "done", "delayed"):
        store.update_task(task_id, status=status)
        flash(t("team.updated_task", ui_lang()), "ok")
    return redirect(request.referrer or url_for("team.tasks_page"))


@bp.route("/people", methods=["GET", "POST"])
@ceo_required
def people_page():
    if request.method == "POST":
        owner = (request.form.get("telegram_id") or "").strip()
        role = request.form.get("role", "")
        display_name = (request.form.get("display_name") or "").strip()
        if owner and role in store.TEAM_ROLES:
            store.set_team_role(owner, role, display_name=display_name, added_by=current_user()["owner"])
            flash(t("team.role_granted", ui_lang()), "ok")
        return redirect(url_for("team.people_page"))

    return render_template("team/people.html", members=store.list_team_members(), roles=store.TEAM_ROLES)


@bp.app_context_processor
def inject_team_nav():
    user = current_user()
    return {"in_team": bool(user and user.get("team_role"))}
