"""The two Rambo extras: a card under the holder's own name, and a webhook out.

Both answer the same request from a group lead or an IB: let my people see this
under my name, and let my own systems see it at all.
"""

import json

from app import store, whitelabel
from app.autopilot import run_due, toggle

from tests.conftest import login


def _rambo(owner="77"):
    store.grant_entitlement(owner, "elite", source="manual")


# --- the widget ------------------------------------------------------------- #

def test_only_rambo_may_mint_a_card(app):
    with app.app_context():
        assert whitelabel.set_widget("77", "gold-watch", "Sam Flip")[1] == "wl.need"
        _rambo()
        w, err = whitelabel.set_widget("77", "gold-watch", "Sam Flip")
        assert not err and w["name"] == "Sam Flip" and w["token"]


def test_a_card_needs_a_real_tool_and_a_name(app):
    with app.app_context():
        _rambo()
        assert whitelabel.set_widget("77", "telepati", "Sam")[1] == "wl.tool"
        assert whitelabel.set_widget("77", "gold-watch", "   ")[1] == "wl.name"


def test_editing_a_card_keeps_its_token(app):
    with app.app_context():
        _rambo()
        first, _ = whitelabel.set_widget("77", "gold-watch", "Sam Flip")
        second, _ = whitelabel.set_widget("77", "broker-comparator", "Sam Flip Seribu")
        assert second["token"] == first["token"]     # a live embed must not break on a rename
        assert second["tool"] == "broker-comparator"


def test_the_card_is_public_and_carries_the_holders_name_not_ours(client, app):
    with app.app_context():
        _rambo()
        w, _ = whitelabel.set_widget("77", "gold-watch", "Sam Flip Seribu")
    r = client.get("/w/%s" % w["token"])
    body = r.get_data(as_text=True)
    assert r.status_code == 200                       # no sign-in needed
    assert "Sam Flip Seribu" in body
    assert "2,399" in body or "2399" in body          # the live bid from the fake feed
    assert "pendidikan sahaja" in body                # white-label renames the wrapper, never the risk line
    assert r.headers["Content-Security-Policy"] == "frame-ancestors *"


def test_the_card_goes_dark_with_the_rank_that_paid_for_it(client, app):
    with app.app_context():
        store.grant_entitlement("77", "elite", source="stripe", external_id="sub_x")
        w, _ = whitelabel.set_widget("77", "gold-watch", "Sam Flip")
    assert client.get("/w/%s" % w["token"]).status_code == 200
    with app.app_context():
        store.revoke_entitlement(external_id="sub_x")
    assert client.get("/w/%s" % w["token"]).status_code == 404
    assert client.get("/w/not-a-token").status_code == 404


def test_taking_the_card_down_frees_the_token(app):
    with app.app_context():
        _rambo()
        w, _ = whitelabel.set_widget("77", "gold-watch", "Sam Flip")
        whitelabel.clear_widget("77")
        assert whitelabel.widget_of("77") is None
        assert whitelabel.owner_of_widget(w["token"]) is None


def test_every_offered_tool_builds_a_card(app):
    with app.app_context():
        _rambo()
        for tool in whitelabel.WIDGETS:
            w, err = whitelabel.set_widget("77", tool, "Sam")
            assert not err
            heads, rows = whitelabel.card(w, "ms")
            assert len(heads) == 2                    # a card is always two columns
            for row in rows:
                assert len(row) == 2


# --- the webhook ------------------------------------------------------------ #

def test_only_rambo_and_only_https(app):
    with app.app_context():
        assert whitelabel.set_hook("77", "https://example.com/h")[1] == "wh.need"
        _rambo()
        assert whitelabel.set_hook("77", "http://example.com/h")[1] == "wh.url"
        assert whitelabel.set_hook("77", "not a url")[1] == "wh.url"
        hook, err = whitelabel.set_hook("77", "https://example.com/h")
        assert not err and hook["secret"]


def test_the_secret_survives_an_endpoint_change(app):
    with app.app_context():
        _rambo()
        first, _ = whitelabel.set_hook("77", "https://example.com/a")
        second, _ = whitelabel.set_hook("77", "https://example.com/b")
        assert second["secret"] == first["secret"]    # the receiver keeps verifying


def test_delivery_signs_the_body_it_sends(app):
    seen = {}

    def post(url, data=None, timeout=None, headers=None):
        seen.update({"url": url, "data": data, "headers": headers})
        return type("R", (), {"status_code": 200})()

    with app.app_context():
        _rambo()
        hook, _ = whitelabel.set_hook("77", "https://example.com/h")
        assert whitelabel.deliver("77", "gold-watch", {"text": "hi"}, post=post) == 200

    assert seen["url"] == "https://example.com/h"
    assert seen["headers"]["X-Sambanggold-Event"] == "gold-watch"
    assert seen["headers"]["X-Sambanggold-Signature"] == whitelabel.sign(hook["secret"], seen["data"])
    assert json.loads(seen["data"])["data"]["text"] == "hi"


def test_a_dead_endpoint_never_raises(app):
    def boom(*a, **k):
        raise OSError("connection refused")

    with app.app_context():
        _rambo()
        whitelabel.set_hook("77", "https://example.com/h")
        assert whitelabel.deliver("77", "gold-watch", {}, post=boom) is None


def test_no_hook_and_a_lapsed_rank_both_deliver_nothing(app):
    calls = []

    def post(*a, **k):
        calls.append(1)
        return type("R", (), {"status_code": 200})()

    with app.app_context():
        assert whitelabel.deliver("77", "x", {}, post=post) is None    # no hook at all
        store.grant_entitlement("77", "elite", source="stripe", external_id="sub_x")
        whitelabel.set_hook("77", "https://example.com/h")
        store.revoke_entitlement(external_id="sub_x")
        assert whitelabel.deliver("77", "x", {}, post=post) is None    # rank gone
    assert calls == []


def test_an_autopilot_push_reaches_the_webhook_too(app, monkeypatch):
    sent, posted = [], []
    monkeypatch.setattr(whitelabel.requests, "post",
                        lambda url, **kw: posted.append((url, kw)) or type("R", (), {"status_code": 200})())
    with app.app_context():
        _rambo()
        whitelabel.set_hook("77", "https://example.com/h")
        toggle("77", "gold-watch", on=True)
        run_due(lambda chat, text: sent.append(text))
    assert len(sent) == 1 and len(posted) == 1
    assert posted[0][0] == "https://example.com/h"
    assert json.loads(posted[0][1]["data"])["event"] == "gold-watch"


# --- the panel -------------------------------------------------------------- #

def test_the_panel_is_read_only_below_rambo(client, app):
    login(client, user_id="42")
    body = client.get("/dashboard").get_data(as_text=True)
    assert "Widget jenama sendiri" in body and "Rambo" in body

    with app.app_context():
        store.grant_entitlement("42", "elite", source="manual")
    login(client, user_id="42")
    with client.session_transaction() as s:
        user = dict(s["user"]); user["rank"] = "elite"; s["user"] = user
    client.post("/dashboard", data={"wl_action": "widget", "tool": "gold-watch", "name": "Sam Flip"},
                follow_redirects=True)
    with app.app_context():
        assert whitelabel.widget_of("42")["name"] == "Sam Flip"
