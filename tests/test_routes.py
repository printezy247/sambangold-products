"""Both surfaces answer for all eighteen products."""

import pytest
from markupsafe import escape

from app.products import PRODUCTS
from app.telegram import reply_for


def test_index_lists_every_product(client):
    page = client.get("/").get_data(as_text=True)
    assert page.count('class="card"') == 18
    for p in PRODUCTS:
        assert str(escape(p.name)) in page


@pytest.mark.parametrize("product", PRODUCTS, ids=lambda p: p.slug)
def test_every_product_has_a_dashboard_page(client, product):
    page = client.get("/p/%s" % product.slug)
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert str(escape(product.name)) in body
    assert str(escape(product.bot_commands[0][0])) in body
    assert str(escape(product.dashboard_views[0])) in body


def test_unknown_slug_is_404(client):
    assert client.get("/p/not-a-product").status_code == 404


@pytest.mark.parametrize("product", PRODUCTS, ids=lambda p: p.slug)
def test_every_product_answers_in_telegram(product):
    reply = reply_for(product.bot_commands[0][0], "https://example.test")
    assert product.name in reply
    assert product.slug in reply


def test_help_lists_every_product():
    reply = reply_for("/help")
    for p in PRODUCTS:
        assert p.name in reply


def test_unknown_command_is_handled():
    assert "Unknown command" in reply_for("/nope")


def test_webhook_accepts_an_update_without_a_token(client):
    response = client.post("/webhook/telegram", json={
        "message": {"chat": {"id": 1}, "text": "/help"},
    })
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


def test_healthz(client):
    body = client.get("/healthz").get_json()
    assert body["ok"] is True and body["products"] == 18


# --- the two live dashboards ---------------------------------------------- #

def test_prop_dashboard_computes_and_saves(client):
    page = client.get("/p/prop-calculator?fee=500&size=100000&pass_pct=15&save=1&firm=Acme")
    body = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "$460" in body and "7.8%" in body
    assert "Acme" in body  # saved comparison row
    again = client.get("/p/prop-calculator").get_data(as_text=True)
    assert "Acme" in again  # survives in the session


def test_prop_dashboard_scans_pasted_terms(client):
    page = client.post("/p/prop-calculator", data={
        "terms": "A trailing maximum drawdown applies. News trading is prohibited."})
    body = page.get_data(as_text=True)
    assert "Trailing drawdown" in body and "No news trading" in body


def test_prop_dashboard_shows_input_errors(client):
    body = client.get("/p/prop-calculator?fee=abc").get_data(as_text=True)
    assert "must be a number" in body


def test_ib_dashboard_computes_timeline_and_checklist(client):
    page = client.get("/p/ib-revenue-calculator?lots=10&rate=5&payout_threshold=120")
    body = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "$150" in body and "day 120" in body
    assert "Registration" in body and "checklist.txt" in body


def test_ib_checklist_downloads_as_text(client):
    r = client.get("/p/ib-revenue-calculator/checklist.txt")
    assert r.status_code == 200
    assert r.mimetype == "text/plain"
    assert "attachment" in r.headers["Content-Disposition"]
    assert "- [ ]" in r.get_data(as_text=True)
