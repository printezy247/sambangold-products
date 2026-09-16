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


# A bare element or a shell class as the *first* compound of a selector. `main`
# slipped past a startswith() check once, as `main {`, and trapped the gate
# beneath the header inside a stacking context it had no business creating.
# `body.gated` is fine — that class is the landing's own; bare `body` is not.
SHELL_RE = re.compile(r"^(?:(?:header|nav|main|footer|body|html|a|h1|h2|h3|p|section)(?![\w.#-])"
                      r"|\.(?:wrap|bar|glass|btn|chip|lux|card|stat|grid|panel|actions|chips|mono)(?![\w-]))")


def test_landing_styles_never_touch_the_shell(client):
    """The first version called the gold bar `.bar`. So is the header's row, and
    the header inherited a 3D rotation and a 180px width. Every rule in the
    landing block must hang off a landing-only hook."""
    html = page(client)
    block = html[html.index("#field { position: fixed"):html.index("</style>")]
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith(("/*", "*", "@keyframes", "}", "to ", "from ")) or "{" not in line:
            continue
        selector = line.split("{", 1)[0].strip()
        if selector.startswith("@media"):
            selector = line.split("{", 1)[1].split("{", 1)[0].strip()
        for sel in selector.split(","):
            sel = sel.strip()
            if not sel or sel[0].isdigit() or sel.endswith("%"):
                continue
            assert not SHELL_RE.match(sel), "landing rule targets the shell: %r" % sel
    # the header's own row is an ordinary flex row again, and the landing never wraps main
    assert ".ingot {" in html and "\n  .bar {" not in block and "\n  main {" not in block


def test_the_gate_carries_the_monogram_and_the_field_shows_through(client):
    html = page(client)
    gate = html[html.index('id="gate"'):html.index('id="lift"')]
    assert 'class="glyph"' in gate                  # the SBG monogram, not just the wordmark
    assert 'class="door dl"' in gate and 'class="door dr"' in gate
    assert "#field { position: fixed" in html      # one canvas behind the whole descent
    assert 'id="field"' in html.split('id="gate"')[0]


def test_the_field_uses_the_whole_palette(client):
    """"Colourful within the palette": candles green and red, ticks gold, lines
    chrome, glyphs tinted by the floor. Never a colour from outside brand.py."""
    from app.brand import TOKENS
    html = page(client)
    script = html[html.index("PAL = {"):]
    for key in ("gold", "gold2", "chrome", "win", "loss"):
        assert TOKENS[key] in script, key


def test_reduced_motion_flattens_the_descent(client):
    """Someone who asked for no motion gets the same content, standing still —
    not a 240vh scroll of nothing happening."""
    html = page(client)
    block = html[html.index("prefers-reduced-motion"):]
    assert ".floor { height: auto; }" in block
    assert "position: static" in block
    assert ".rise, .split .c { opacity: 1; transform: none;" in block


def test_nothing_is_loaded_from_a_third_party(client):
    """CLAUDE.md rule 1: self-hosted. No CDN crept in with the 3D."""
    html = page(client)
    for src in re.findall(r'(?:src|href)="(https?://[^"]+)"', html):
        assert "t.me" in src or "telegram" in src, src


def test_the_page_stays_light(client):
    """The whole experience is CSS, one canvas and no library. If this ever
    doubles, something heavy arrived."""
    assert len(page(client)) < 140_000


# --- both languages ------------------------------------------------------------------ #

def test_the_floors_speak_english_too(client):
    html = page(client, "en")
    assert "THE GOLD DESK" in html and "THE CRYPTO VAULT" in html
    assert "MEJA EMAS" not in html


# --- a phone ---------------------------------------------------------------------- #

def test_the_shell_can_never_widen_the_page(client):
    """A header that overflowed sideways once made Chrome zoom the phone view out
    to fit it, so the body sat at two thirds of the screen with black beside it."""
    html = page(client)
    assert "html, body { overflow-x: clip; }" in html


def test_on_a_phone_every_floor_is_one_screen_that_snaps(client):
    html = page(client)
    start = html.index("@media (max-width: 940px)")
    block = html[start:html.index("@media (prefers-reduced-motion", start)]   # base.html has its own, earlier
    assert "min-height: 100svh; scroll-snap-align: start" in block
    assert ".floor .slab { display: none; }" in block           # its list is on the chips
    assert "--in: 1; --out: 0" in block                          # nothing arrives blurred and hidden
    assert "html.vault { scroll-snap-type: y proximity; }" in html


def test_register_and_ranks_are_navigation(client):
    """They belong in the nav row, so the header has one thing to wrap on a phone."""
    html = page(client)
    nav = html[html.index("<nav>"):html.index("</nav>")]
    assert "/register" in nav and "/pricing" in nav


# --- numbers and boxes ------------------------------------------------------------ #

def test_every_step_card_carries_its_own_numeral(client):
    """The numeral used to be a CSS counter on ::before — the same pseudo-element
    .lux and .lux-gold already own, so 02 vanished and 01 and 03 sat outside the card."""
    html = page(client)
    for n in ("01", "02", "03"):
        assert '<i class="n" aria-hidden="true">%s</i>' % n in html
    assert "counter-increment: step" not in html
    assert ".step::before" not in html


def test_a_wide_table_scrolls_inside_its_own_box_on_a_phone(client):
    """The page clips sideways, so a table wider than the screen lost its last
    columns with no way to reach them."""
    html = page(client)
    assert "@media (max-width: 760px) { table.flags { display: block;" in html
    assert "overflow-x: auto; } }" in html
