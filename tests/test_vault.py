"""The landing page as a vault descent.

The risk in an immersive landing page is that the immersion becomes the page:
the content moves into JavaScript, the crawler sees a black screen, and someone
with a slow phone or reduced motion gets nothing. These tests hold the line that
the page is a page first and an experience second.
"""

import re

from markupsafe import escape

from app.products import PRODUCTS
from app.views import FLOORS


def page(client, lang="ms"):
    client.get("/lang/%s" % lang)
    return client.get("/").get_data(as_text=True)


# --- the floors ------------------------------------------------------------------ #

def test_every_tool_lives_on_exactly_one_floor():
    """A tool with no floor is a tool nobody scrolls past."""
    placed = [slug for _, _, slugs in FLOORS for slug in slugs]
    assert len(placed) == len(set(placed)), "a tool is on two floors"
    assert set(placed) == {p.slug for p in PRODUCTS}


def test_the_descent_renders_every_floor(client):
    html = page(client)
    assert html.count('class="floor"') == len(FLOORS)
    for key, _, _ in FLOORS:
        assert 'id="%s"' % key in html


def test_each_floor_names_itself_and_its_tools(client, app):
    from app.brand import t
    from app.products import BY_SLUG
    html = page(client)
    for key, _, slugs in FLOORS:
        assert t("vault.%s_h" % key) in html
        assert t("vault.%s_fix" % key) in html
        for slug in slugs:
            assert str(escape(BY_SLUG[slug].view("ms").name)) in html


def test_the_lift_has_a_stop_for_the_door_and_every_floor(client):
    html = page(client)
    assert html.count('data-floor=') == len(FLOORS) + 1


# --- the page is still a page ------------------------------------------------------ #

def test_the_gate_never_hides_the_content_from_a_crawler(client):
    """The gate is inert markup until JS turns it on. Everything behind it is in
    the HTML, so a crawler with no JavaScript reads the whole vault."""
    html = page(client)
    assert 'id="gate"' in html
    assert 'aria-hidden="true"' in html.split('id="gate"')[1][:80]
    assert "#gate { position: fixed" in html and "display: none" in html
    # and the content is present in the same document, not fetched later
    assert "MEJA EMAS" in html and "PETI KRIPTO" in html


def test_the_copy_below_the_vault_survived_the_redesign(client, app):
    from app.brand import t
    html = page(client)
    for key in ("land.how_h", "land.rank_h", "grid.title", "land.trust_h", "faq.title", "land.final_sub"):
        assert t(key) in html, key


def test_the_risk_strip_and_the_brand_still_ride_the_page(client):
    html = page(client)
    assert "Pendidikan sahaja" in html
    assert "brand/anton.woff2" in html and "brand/mascot-raise.png" in html
    assert "#d4af37" in html


def test_reduced_motion_flattens_the_descent(client):
    """Someone who asked for no motion gets the same content, standing still —
    not a 240vh scroll of nothing happening."""
    html = page(client)
    block = html[html.index("prefers-reduced-motion"):]
    assert ".floor { height: auto; }" in block
    assert "position: static" in block
    assert ".rise { opacity: 1; transform: none;" in block


def test_nothing_is_loaded_from_a_third_party(client):
    """CLAUDE.md rule 1: self-hosted. No CDN crept in with the 3D."""
    html = page(client)
    for src in re.findall(r'(?:src|href)="(https?://[^"]+)"', html):
        assert "t.me" in src or "telegram" in src, src


def test_the_page_stays_light(client):
    """The whole experience is CSS, one canvas and no library. If this ever
    doubles, something heavy arrived."""
    assert len(page(client)) < 120_000


# --- both languages ------------------------------------------------------------------ #

def test_the_floors_speak_english_too(client):
    html = page(client, "en")
    assert "THE GOLD DESK" in html and "THE CRYPTO VAULT" in html
    assert "MEJA EMAS" not in html
