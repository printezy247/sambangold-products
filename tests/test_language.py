"""Bahasa Melayu first, English second — and never both at once.

The bug this file exists for: `dashboard_setup` handed the template a bare
`label` function whose `lang` defaulted to Malay, so the My Setup page rendered
its field labels in BM while the nav around them was English. Nothing caught it,
because every individual string was correctly translated — the mistake was in
*which* language got asked for.

So these tests do not check the table. They render every real surface in each
language and refuse to let the other one bleed in, which catches the whole class:
a missed translation, an unbound `lang`, a default argument, a hard-coded string.
"""

import re

import pytest

from app.brand import LANGS, STRINGS
from app.products import PRODUCTS
from app.telegram import reply_for
from tests.conftest import login

# Function words. A page that contains any of these in the wrong language is
# either untranslated or asked the wrong table, and both are bugs.
MARKERS = {
    "ms": r"\b(anda|yang|untuk|dengan|ialah|adalah|tidak|sudah|belum|daripada|sebulan|setiap|dalam|kepada|semua|boleh|jangan|tanpa|sahaja|lagi)\b",
    "en": r"\b(the|your|with|every|from|what|when|which|these|those|because|about|into|after|would|should|nothing|anything)\b",
}
OTHER = {"ms": "en", "en": "ms"}

PAGES = ["/", "/setup", "/dashboard", "/pricing", "/account", "/admin", "/register"] + ["/p/%s" % p.slug for p in PRODUCTS]


def _copy(html):
    """The words a reader sees: no scripts, no styles, no tag attributes."""
    html = re.sub(r"(?s)<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", html)
    return re.sub(r"<[^>]+>", " ", html)


def _foreign(text, lang):
    return sorted(set(m.group(0).lower() for m in re.finditer(MARKERS[OTHER[lang]], text, re.I)))


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.strip("/").replace("/", "-") or "landing")
def test_no_page_mixes_the_two_languages(client, app, path, lang):
    login(client, "42", admin=True)
    client.get("/lang/%s" % lang)
    response = client.get(path)
    assert response.status_code == 200, path
    leaked = _foreign(_copy(response.get_data(as_text=True)), lang)
    assert not leaked, "%s in %s leaked %s" % (path, lang, ", ".join(leaked))


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("product", PRODUCTS, ids=lambda p: p.slug)
def test_no_bot_reply_mixes_the_two_languages(app, product, lang):
    with app.app_context():
        reply = reply_for(product.bot_commands[0][0], "https://example.test", chat_id=7, lang=lang)
    leaked = _foreign(_copy(reply), lang)
    assert not leaked, "%s in %s leaked %s" % (product.slug, lang, ", ".join(leaked))


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("command", ["setup", "brief", "register", "autopilot", "broker", "invite", "seats", "widget", "webhook", "groups"])
def test_no_platform_command_mixes_the_two_languages(app, command, lang):
    """The ladder's own commands are not products, so the surface-contract test
    never sees them. They still have to speak one language."""
    from app import telegram
    with app.app_context():
        actions = telegram._handle_message(7, "/" + command, {"id": 7, "language_code": lang})
        text = " ".join(a[2] for a in actions if a[0] == "send")
    leaked = _foreign(_copy(text), lang)
    assert not leaked, "/%s in %s leaked %s" % (command, lang, ", ".join(leaked))


def test_a_dead_feed_never_shows_a_raw_error(client, app, monkeypatch):
    """A `requests` exception is English, technical, and names our own hosts.
    None of those belong on a page a trader is reading."""
    from app import feeds
    def down(*_a, **_k):
        raise feeds.FeedError("HTTPSConnectionPool(host='api.binance.com', port=443): Max retries")
    monkeypatch.setattr(feeds, "gold_quote", down)
    client.get("/lang/ms")
    page = client.get("/p/gold-watch").get_data(as_text=True)
    assert "api.binance.com" not in page
    assert "HTTPSConnectionPool" not in page
    assert "Cuba lagi seminit" in page


def test_the_token_facts_table_is_translated(app):
    """The attestation and redemption terms were English-only for both
    languages — product data is copy too."""
    from app import tokengold
    ms = tokengold.tokens("ms")
    assert "bulanan" in ms["PAXG"]["attestation"]
    assert ms["PAXG"]["issuer"] == "Paxos"          # names stay names
    assert tokengold.tokens("en") == tokengold.TOKENS


def test_both_tables_carry_exactly_the_same_keys(app):
    assert set(STRINGS["ms"]) == set(STRINGS["en"])


# Identical in both tables on purpose: pure layout, sample data a user pastes,
# or names. Listed one by one, because the whole point is that a *new* identical
# string is a missed translation until someone decides otherwise.
SAME_ON_PURPOSE = {
    "flow.chosen", "gr.quote", "gr.red", "lk.row", "mn.n_head", "rp.scan_row",   # layout, no prose
    "watch.spread",                                                              # "Spread" is the term in both
    "flow.eg_positions", "ui.k_csv_ph", "ui.r_overrides_ph", "ui.r_tiers_ph", "ui.v_batch_ph",  # samples
    "tk.chain_evm",                                                              # chain names
}


def test_no_string_is_left_untranslated_by_accident(app):
    """Identical in both tables usually means a copy-paste nobody came back to.

    That is how `ui.p_ev` sat as "Expected value" on a Malay page, and
    `tk.premium` said "Premium vs spot". The exceptions are named above rather
    than matched by a rule, so adding one is a decision, not an accident.
    """
    same = {k for k in STRINGS["ms"] if STRINGS["ms"][k] == STRINGS["en"][k]}
    allowed = SAME_ON_PURPOSE | {k for k in same if (
        len(STRINGS["ms"][k]) < 14                      # a word or two: Admin, Dashboard, PDF
        or "<code>" in STRINGS["ms"][k]                 # a command someone types
        or STRINGS["ms"][k].startswith("/")
        or k.startswith(("brand.", "rank.", "nav.lang")))}
    assert same <= allowed, "untranslated: %s" % sorted(same - allowed)
