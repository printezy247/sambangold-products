"""The dashboard half of every product."""

import os

from flask import Blueprint, abort, current_app, render_template, send_from_directory

from .auth import current_user
from .products import BY_SLUG, PRODUCTS

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


@bp.route("/p/<slug>")
def product(slug):
    item = BY_SLUG.get(slug)
    if item is None:
        abort(404)
    return render_template("product.html", p=item, user=current_user())


@bp.route("/assets/<path:filename>")
def assets(filename):
    """Serve the repository's SVG set so the dashboard and README share one look."""
    return send_from_directory(ASSETS, filename)


@bp.route("/healthz")
def healthz():
    return {"ok": True, "products": len(PRODUCTS), "missing_config": current_app.config["MISSING"]}
