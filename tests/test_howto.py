"""Every tool explains itself, in both languages, to someone who has never used it.

The gap was never the answer. It was the blank box: a first-time visitor opens a
tool, sees a field called "Pass rate %", and closes the tab.
"""

from app import howto
from app.brand import STRINGS
from app.products import PRODUCTS


def test_every_product_has_three_steps_in_both_languages():
    for p in PRODUCTS:
        for lang in ("ms", "en"):
            steps = howto.steps(p.slug, lang)
            assert len(steps) == 3, p.slug
            for line in steps:
                assert not line.startswith("how."), (p.slug, lang, line)   # no missing string
                assert len(line) > 18, (p.slug, lang, line)


def test_the_steps_are_written_short_enough_to_read():
    """A kid or an old man, so no wall of text and no jargon-only lines."""
    for p in PRODUCTS:
        for lang in ("ms", "en"):
            for line in howto.steps(p.slug, lang):
                assert len(line) <= 140, (p.slug, lang, len(line))


def test_every_product_has_an_example():
    for p in PRODUCTS:
        assert p.slug in howto.EXAMPLES, p.slug


def test_a_fillable_form_gets_a_link_that_fills_it():
    link = howto.example_link("prop-calculator", "en")
    assert link.startswith("?") and "fee=500" in link and "size=100000" in link
    assert howto.example_link("red-flag-scanner", "en") == ""   # a POST form cannot be filled by a link


def test_placeholder_examples_resolve_to_real_text():
    eg = howto.example_query("red-flag-scanner", "en")
    assert "guaranteed" in eg["text"].lower() and not eg["text"].startswith("eg.")
    eg = howto.example_query("red-flag-scanner", "ms")
    assert "dijamin" in eg["text"].lower()


def test_the_strip_renders_on_a_tool_page_in_both_languages(client):
    body = client.get("/p/prop-calculator").get_data(as_text=True)
    assert "Cara guna" in body and "Cuba contoh" in body
    assert "yuran challenge" in body

    client.get("/lang/en")
    body = client.get("/p/prop-calculator").get_data(as_text=True)
    assert "How to use this" in body and "Try an example" in body
    assert "challenge fee" in body


def test_the_example_link_actually_fills_the_form(client):
    client.get("/lang/en")
    body = client.get("/p/prop-calculator" + howto.example_link("prop-calculator", "en")).get_data(as_text=True)
    assert 'value="500"' in body and 'value="100000"' in body


def test_a_page_with_nothing_to_fill_shows_the_copyable_example_instead(client):
    body = client.get("/p/red-flag-scanner").get_data(as_text=True)
    assert "Contoh untuk disalin" in body and "dijamin" in body


# --- the bot half: no step is ever a blank box ------------------------------ #

def test_no_flow_step_is_a_blank_box_even_when_the_feed_is_down(monkeypatch):
    """Live buttons come from the gold price. When that feed dies, every step
    must still offer something to press."""
    from app import flows
    monkeypatch.setattr(flows, "_gold_levels", lambda: ())
    monkeypatch.setattr(flows, "_gold_now", lambda: ())
    for slug, steps in flows.FLOWS.items():
        for step in steps:
            has = bool(step["options"]) or bool(step["example"]) or bool(step["live"])
            assert has, (slug, step["key"])
            if not step["options"]:
                assert step["example"], (slug, step["key"])   # the fallback when live returns nothing


def test_live_buttons_are_built_from_the_price_right_now(app, fake_feed):
    from app.flows import FLOWS, options_for
    with app.app_context():
        level = [s for s in FLOWS["gold-watch"] if s["key"] == "level"][0]
        labels = [l for l, _ in options_for(level)]
        assert any("now" in l for l in labels)
        assert any("2410" in v or "2,410" in l for l, v in options_for(level))

        price = [s for s in FLOWS["signal-verifier"] if s["key"] == "price"][0]
        assert [l for l, _ in options_for(price)][0].startswith("Bid")


def test_the_example_button_fills_a_long_answer(app):
    """A pitch never fits in Telegram's 64-byte callback data, so the button
    carries no value and the step supplies it."""
    from app import flows, store
    with app.app_context():
        flows.start("red-flag-scanner", 7, "en")
        flows.on_callback("fl_eg", 7, 99, "en")
        state = store.tg_state(7)
        assert state is None or "guaranteed" in str(state.get("answers", {}))
