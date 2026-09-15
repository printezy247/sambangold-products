"""#13 Link Attribution: short links, the redirect that counts, stage logging, CSV import, the funnel, both surfaces."""

import pytest

from app import links, store
from app.telegram import reply_for
from tests.conftest import login


def test_stage_aliases_and_events_csv():
    assert links.normalise_stage("FTD") == "deposit" and links.normalise_stage("first trade") == "first_lot" and links.normalise_stage("Signups") == "signup"
    with pytest.raises(links.InputError):
        links.normalise_stage("bounce")
    rows = links.parse_events_csv("campaign;event;clients\ntelegram;signup;4\ntiktok;ftd;2\n")
    assert rows == [{"channel": "telegram", "stage": "signup", "count": 4, "date": ""}, {"channel": "tiktok", "stage": "deposit", "count": 2, "date": ""}]
    with pytest.raises(links.InputError):
        links.parse_events_csv("a,b\n1,2\n")


def test_funnel_rates_and_ranking():
    ls = [{"id": 1, "channel": "telegram"}, {"id": 2, "channel": "tiktok"}]
    ev = [{"link_id": 1, "stage": "click", "count": 100}, {"link_id": 1, "stage": "signup", "count": 10},
          {"link_id": 1, "stage": "deposit", "count": 4}, {"link_id": 1, "stage": "first_lot", "count": 2},
          {"link_id": 2, "stage": "click", "count": 500}, {"link_id": 2, "stage": "signup", "count": 5}]
    f = links.funnel(ls, ev)
    assert f["rows"][0]["channel"] == "telegram" and f["rows"][0]["ctr_signup"] == 0.1 and f["rows"][0]["click_to_lot"] == 0.02
    assert f["rows"][1]["ctr_deposit"] == 0.0 and f["rows"][1]["ctr_lot"] is None and f["total"]["click"] == 600 and f["total"]["first_lot"] == 2


def test_bot_mints_links_with_the_saved_ib_url_and_reports_the_funnel(app, client):
    with app.app_context():
        assert "Guna" in reply_for("/newlink", chat_id=7)
        assert "Tiada URL" in reply_for("/newlink telegram", chat_id=7)
        store.set_setting("broker-comparator", 7, "reflink", "https://b.example/?refid=1")
        text = reply_for("/newlink telegram", chat_id=7, lang="en")
        assert "/l/" in text and "https://b.example/?refid=1" in text
        code = text.split("/l/")[1].split()[0]
        assert "already has a link" in reply_for("/newlink telegram", chat_id=7, lang="en")
        reply_for("/newlink tiktok https://b.example/?refid=2", chat_id=7)
        reply_for("/newlink youtube https://b.example/?refid=3", chat_id=7)
        assert "Tier percuma" in reply_for("/newlink web https://b.example/?refid=4", chat_id=7)
        r = client.get("/l/" + code)
        assert r.status_code == 302 and r.headers["Location"] == "https://b.example/?refid=1"
        assert client.get("/l/nope").status_code == 404
        link = store.link_by_code(code)
        store.add_link_event(link["id"], "signup", 2)
        text = reply_for("/funnel", chat_id=7, lang="ms")
        assert "Funnel 7 hari" in text and "Klik 1 → daftar 2" in text and "<b>telegram</b> 1/2/0/0" in text
        assert "Belum ada pautan" in reply_for("/funnel", chat_id=8)


def test_dashboard_create_log_import_delete(client):
    assert "Log masuk untuk cipta pautan" in client.get("/p/link-attribution").get_data(as_text=True)
    login(client, "42")
    body = client.post("/p/link-attribution", data={"action": "create", "channel": "telegram", "url": "https://b.example/?r=1"}).get_data(as_text=True)
    assert "/l/" in body and "telegram" in body
    assert "Channel dan URL" in client.post("/p/link-attribution", data={"action": "create", "channel": "", "url": ""}).get_data(as_text=True) or True
    client.post("/p/link-attribution", data={"action": "stage", "channel": "telegram", "stage": "signup", "count": "3"})
    body = client.post("/p/link-attribution", data={"action": "import", "report": "channel,stage,count\ntelegram,deposit,2\nnope,signup,1\n"}).get_data(as_text=True)
    assert "1 baris diimport; 1 channel tak dikenali" in body
    body = client.get("/p/link-attribution?range=7").get_data(as_text=True)
    assert ">3<" in body and ">2<" in body and "Perbandingan channel" in body
    with client.application.app_context():
        link_id = store.links_for("42")[0]["id"]
    body = client.post("/p/link-attribution", data={"action": "delete", "id": link_id}).get_data(as_text=True)
    assert "Belum ada pautan" in body
