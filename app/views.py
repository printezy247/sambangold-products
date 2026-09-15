"""The dashboard half of every product, plus the landing page and admin."""

import csv
import hmac
import io
import os
import time

from flask import (Blueprint, Response, abort, current_app, jsonify, render_template, request,
                   send_from_directory, session)

from . import caltool, feeds, scan, scantool, store, telegram, watch
from .auth import admin_required, current_user, login_required
from .calc import ib_checklist_text
from .products import BY_SLUG, PRODUCTS
from .tools import DASHBOARD, money, pct

bp = Blueprint("views", __name__)

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _split():
    """Live tools first (they have a dashboard handler), then the rest in order."""
    live = [p for p in PRODUCTS if p.slug in DASHBOARD]
    rest = [p for p in PRODUCTS if p.slug not in DASHBOARD]
    return live, rest


@bp.route("/")
def index():
    live, rest = _split()
    try:
        quote = feeds.gold_quote()
    except feeds.FeedError:
        quote = None
    return render_template("landing.html", products=PRODUCTS, live=live, rest=rest, quote=quote)


@bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    live, rest = _split()
    row = store.user_by_id(user["uid"])
    saved = session.get("saves", {})
    counts = {
        "alerts": len(store.alerts_for(user["owner"])),
        "triggers": len(store.triggers_for(user["owner"])),
        "saved": sum(len(v) for v in saved.values()),
    }
    since = time.strftime("%Y-%m-%d", time.gmtime(row["created_at"])) if row else "—"
    return render_template("dashboard.html", live=live, rest=rest, counts=counts, since=since)


@bp.route("/account")
@login_required
def account():
    return render_template("account.html")


@bp.route("/admin")
@admin_required
def admin():
    return render_template("admin.html", users=store.list_users(), counts=store.user_counts())


@bp.route("/admin/users.csv")
@admin_required
def admin_users_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "email", "telegram_id", "username", "name", "locale", "created_utc", "last_login_utc"])
    for u in store.list_users(limit=100000):
        w.writerow([u["id"], u["email"] or "", u["telegram_id"] or "", u["username"] or "", u["name"] or "", u["locale"],
                    time.strftime("%Y-%m-%d %H:%M", time.gmtime(u["created_at"])),
                    time.strftime("%Y-%m-%d %H:%M", time.gmtime(u["last_login_at"] or u["created_at"]))])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=sambangold-users.csv"})


@bp.route("/p/<slug>", methods=["GET", "POST"])
def product(slug):
    item = BY_SLUG.get(slug)
    if item is None:
        abort(404)
    build = DASHBOARD.get(slug)
    tool = build(request, user=current_user()) if build else None
    return render_template("product.html", p=item, tool=tool, money=money, pct=pct)


@bp.route("/p/gold-watch/history.csv")
@login_required
def gold_watch_csv():
    return Response(watch.history_csv(current_user()["owner"]), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=gold-watch-history.csv"})


@bp.route("/tasks/check-alerts", methods=["POST"])
def check_alerts_task():
    """Called by the scheduler. Shared-secret header, constant-time compare."""
    expected = current_app.config["TASK_TOKEN"]
    given = request.headers.get("X-Task-Token", "")
    if not expected or not hmac.compare_digest(expected, given):
        abort(403)
    return jsonify(watch.check_alerts(telegram.send_message))


@bp.route("/p/gold-calendar/quarter.pdf")
def gold_calendar_pdf():
    name, body = caltool.quarter_pdf_bytes()
    return Response(body, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=%s" % name})


@bp.route("/p/<slug>/s/<int:scan_id>")
def scan_public(slug, scan_id):
    """Public share page for one archived scan — the score, the findings, nothing about who ran it."""
    item = BY_SLUG.get(slug)
    page = scantool.public_page(scan_id)
    if item is None or page is None or page["row"]["product"] != slug:
        abort(404)
    return render_template("scan_public.html", p=item, s=page)


@bp.route("/p/influencer-audit/report.txt", methods=["POST"])
def influencer_loss_report():
    f = request.form
    body = scan.loss_report(f.get("handle", ""), f.get("platform", ""), f.get("amount", ""), f.get("currency", ""),
                            f.get("date", ""), f.get("story", ""), f.get("broker", ""))
    return Response(body, mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=scam-loss-report.txt"})


@bp.route("/p/ib-revenue-calculator/checklist.txt")
def ib_checklist():
    return Response(ib_checklist_text(), mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=ib-compliance-checklist.txt"})


@bp.route("/assets/<path:filename>")
def assets(filename):
    """Serve the repository's SVG set and brand kit so every surface shares one look."""
    return send_from_directory(ASSETS, filename)


@bp.route("/healthz")
def healthz():
    return {"ok": True, "products": len(PRODUCTS), "missing_config": current_app.config["MISSING"]}
