"""The dashboard half of every product, plus the landing page and admin."""

import csv
import hmac
import io
import os
import time

from flask import (Blueprint, Response, abort, current_app, flash, jsonify, make_response, redirect,
                   render_template, request, send_from_directory, session, url_for)

from . import (autopilot, brokertool, caltool, doors, feeds, gate, groups, linktool, mctool, perks, rebatetool, scan, scantool,
               seats, sentineltool, store, telegram, verifytool, watch, whitelabel)
from .auth import admin_required, current_user, lang as ui_lang, login_required
from .brand import t
from .calc import ib_checklist_text
from .products import BY_SLUG, PRODUCTS
from .tiers import BY_KEY as TIER_BY_KEY, TIERS
from .tools import DASHBOARD, money, pct

bp = Blueprint("views", __name__)

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


# Landing page: who the page speaks to, and which tools answer which loss.
LANDING_PATHS = (
    ("p1", "🧑‍💻", ("signal-verifier", "bot-scam-detector", "red-flag-scanner", "influencer-audit", "gold-watch", "gold-calendar")),
    ("p2", "🏦", ("prop-calculator", "monte-carlo-sim", "drawdown-sentinel", "exposure-monitor")),
    ("p3", "🤝", ("ib-revenue-calculator", "rebate-auditor", "churn-radar", "broker-comparator", "link-attribution")),
)
LANDING_ROWS = (
    ("r1", ("signal-verifier", "bot-scam-detector", "copy-trade-audit", "red-flag-scanner", "influencer-audit")),
    ("r2", ("prop-calculator", "monte-carlo-sim", "drawdown-sentinel", "exposure-monitor")),
    ("r3", ("ib-revenue-calculator", "rebate-auditor", "churn-radar", "broker-comparator", "link-attribution")),
    ("r4", ("gold-watch", "gold-calendar", "tokenized-gold", "miner-divergence")),
)


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
    return render_template("landing.html", products=PRODUCTS, live=live, rest=rest, quote=quote, by_slug=BY_SLUG, paths=LANDING_PATHS, rows=LANDING_ROWS)


@bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user = current_user()
    ap = autopilot.dashboard_autopilot(request, user)
    st = seats.dashboard_seats(request, user)
    wl = whitelabel.dashboard_extras(request, user)
    gr = groups.dashboard_groups(request, user)
    if request.method == "POST":
        return redirect(url_for("views.dashboard") + "#autopilot")
    live, rest = _split()
    row = store.user_by_id(user["uid"])
    saved = session.get("saves", {})
    counts = {
        "alerts": len(store.alerts_for(user["owner"])),
        "triggers": len(store.triggers_for(user["owner"])),
        "saved": sum(len(v) for v in saved.values()),
    }
    since = time.strftime("%Y-%m-%d", time.gmtime(row["created_at"])) if row else "—"
    return render_template("dashboard.html", live=live, rest=rest, counts=counts, since=since, ap=ap, st=st, wl=wl, gr=gr, by_slug=BY_SLUG)


@bp.route("/pricing", methods=["GET", "POST"])
def pricing():
    """The rank ladder — prices, the two free doors, and what each rank opens."""
    user = current_user()
    if request.method == "POST" and user and request.form.get("action") == "claim":
        _, err = doors.claim(user["owner"], request.form.get("account", ""), request.form.get("deposit") or None)
        flash(t(err, ui_lang()) if err else t("price.claim_ok", ui_lang()), "err" if err else "ok")
        return redirect(url_for("views.pricing") + "#percuma")
    owner = (user or {}).get("owner")
    return render_template(
        "pricing.html", tiers=TIERS,
        grants=store.entitlements_for(owner) if owner else [],
        claims=store.broker_claims_for(owner) if owner else [],
        invite=doors.deep_link(owner, telegram.bot_username()) if owner else "",
        invited=doors.invited(owner) if owner else [],
        referral_days=doors.REFERRAL_DAYS,
        mine=(user or {}).get("rank") or "public",
        want=request.args.get("want", ""))


@bp.route("/account")
@login_required
def account():
    user = current_user()
    return render_template("account.html", grants=store.entitlements_for(user["owner"]))


@bp.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    if request.method == "POST":
        owner = (request.form.get("owner") or "").strip()
        tier = (request.form.get("tier") or "").strip()
        if request.form.get("approve"):
            tier, err = doors.approve(request.form["approve"], request.form.get("deposit") or None)
            flash(t("adm.br_ok", ui_lang()) if not err else t(err, ui_lang()), "err" if err else "ok")
        elif request.form.get("reject"):
            doors.reject(request.form["reject"])
            flash(t("adm.br_no", ui_lang()), "ok")
        elif request.form.get("revoke"):
            store.revoke_entitlement(entitlement_id=request.form["revoke"])
            flash(t("adm.revoked", ui_lang()), "ok")
        elif owner and tier in TIER_BY_KEY:
            days = (request.form.get("days") or "").strip()
            expires = time.time() + float(days) * 86400 if days.replace(".", "", 1).isdigit() else None
            store.grant_entitlement(owner, tier, source="manual", expires_at=expires,
                                    note=(request.form.get("note") or "").strip())
            flash(t("adm.granted", ui_lang()), "ok")
        else:
            flash(t("adm.grant_bad", ui_lang()), "err")
        return redirect(url_for("views.admin"))
    return render_template("admin.html", users=store.list_users(), counts=store.user_counts(),
                           grants=store.all_entitlements(), tiers=TIERS, claims=store.broker_claims())


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
    user = current_user()
    tool = build(request, user=user) if build else None
    mine = (user or {}).get("rank") or "public"
    return render_template("product.html", p=item, tool=tool, money=money, pct=pct,
                           mine=mine, perks=perks.for_product(slug, mine, ui_lang()))


@bp.route("/p/gold-watch/history.csv")
@login_required
@gate.require_feature("history")
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
    if slug == "signal-verifier":
        page = verifytool.public_page(scan_id)
        if page is None:
            abort(404)
        return render_template("verify_public.html", p=item, s=page)
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


@bp.route("/p/monte-carlo-sim/run/<int:run_id>.pdf")
def mc_pdf(run_id):
    user = current_user()
    name, body = mctool.pdf_for(run_id, owner=user["owner"] if user else None, lang=ui_lang(),
                                brand=current_app.config.get("BRAND_NAME", "SAMBANGGOLD"))
    if body is None:
        abort(404)
    return Response(body, mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=%s" % name})


@bp.route("/p/drawdown-sentinel/ping/<token>", methods=["GET", "POST"])
def sentinel_ping(token):
    """An EA or phone shortcut reports equity here. Token is the secret."""
    status, payload = sentineltool.ping(token, request.values)
    return jsonify(payload), status


@bp.route("/l/<code>")
def short_link(code):
    """Tracked short link: count the click, send them on."""
    target = linktool.redirect_target(code)
    if not target:
        abort(404)
    return redirect(target, code=302)


@bp.route("/p/broker-comparator/card/<code>")
def broker_card(code):
    """Public referral card: the ranked table with the IB's own link, no login."""
    try:
        lots = float(request.args.get("lots", 1) or 1)
        nights = int(float(request.args.get("nights", 0) or 0))
    except ValueError:
        lots, nights = 1.0, 0
    page = brokertool.card_page(code, lots, nights)
    if page is None:
        abort(404)
    return render_template("broker_card.html", p=BY_SLUG["broker-comparator"], s=page)


@bp.route("/p/rebate-auditor/dispute/<int:run_id>.pdf")
def rebate_pdf(run_id):
    user = current_user()
    name, body = rebatetool.pdf_for(run_id, owner=user["owner"] if user else None,
                                    brand=current_app.config.get("BRAND_NAME", "SAMBANGGOLD"))
    if body is None:
        abort(404)
    return Response(body, mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=%s" % name})


@bp.route("/p/ib-revenue-calculator/checklist.txt")
def ib_checklist():
    return Response(ib_checklist_text(ui_lang()), mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=ib-compliance-checklist.txt"})


@bp.route("/w/<token>")
def widget(token):
    """A Rambo holder's branded card. Public on purpose — its audience is theirs."""
    owner = whitelabel.owner_of_widget(token)
    w = whitelabel.widget_of(owner) if owner else None
    if not w or w.get("token") != token:
        abort(404)
    if not gate.allows(gate.owner_tier(str(owner)), whitelabel.WIDGET_FEATURE):
        abort(404)      # the card goes dark with the rank that paid for it
    lang = ui_lang()
    heads, rows = whitelabel.card(w, lang)
    resp = make_response(render_template("widget.html", w=w, heads=heads, rows=rows,
                                         product=BY_SLUG[w["tool"]].view(lang)))
    resp.headers["X-Frame-Options"] = "ALLOWALL"     # embedding is the whole point
    resp.headers["Content-Security-Policy"] = "frame-ancestors *"
    return resp


@bp.route("/assets/<path:filename>")
def assets(filename):
    """Serve the repository's SVG set and brand kit so every surface shares one look."""
    return send_from_directory(ASSETS, filename)


@bp.route("/healthz")
def healthz():
    return {"ok": True, "products": len(PRODUCTS), "missing_config": current_app.config["MISSING"]}
