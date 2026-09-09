"""Both surfaces answer for all eighteen products."""

import pytest
from markupsafe import escape

from app import create_app
from app.products import PRODUCTS
from app.telegram import reply_for


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


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
