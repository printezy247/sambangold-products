"""The dashboard half of every product."""

import os

from flask import Blueprint, Response, abort, current_app, render_template, request, send_from_directory

from .auth import current_user
from .calc import ib_checklist_text
from .products import BY_SLUG, PRODUCTS
from .tools import DASHBOARD, money, pct

bp = Blueprint("views", __name__)

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


@bp.route("/")
def index():
    return render_template(
        "index.html",
        shipped=[p for p in PRODUCTS if p.status == "shipped"],
        proposed=[p for p in PRODUCTS if p.status == "proposed"],
        user=current_user(),
    )


@bp.route("/p/<slug>", methods=["GET", "POST"])
def product(slug):
    item = BY_SLUG.get(slug)
    if item is None:
        abort(404)
    build = DASHBOARD.get(slug)
    tool = build(request) if build else None
    return render_template("product.html", p=item, user=current_user(),
                           tool=tool, money=money, pct=pct)


@bp.route("/p/ib-revenue-calculator/checklist.txt")
def ib_checklist():
    return Response(ib_checklist_text(), mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=ib-compliance-checklist.txt"})


@bp.route("/assets/<path:filename>")
def assets(filename):
    """Serve the repository's SVG set so the dashboard and README share one look."""
    return send_from_directory(ASSETS, filename)


@bp.route("/healthz")
def healthz():
    return {"ok": True, "products": len(PRODUCTS), "missing_config": current_app.config["MISSING"]}
