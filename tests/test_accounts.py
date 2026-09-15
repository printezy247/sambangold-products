"""Sign-in doors, account linking, admin gating, language, and the SAMBANGGOLD shell."""

import hashlib
import hmac
import re
import time

import pytest

from app import mailer, store
from app.auth import data_check_string
from app.config import Config
from tests.conftest import login

TOKEN = "123456:test-token-not-a-real-secret"


@pytest.fixture
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "configured", lambda: True)
    monkeypatch.setattr(mailer, "send", lambda to, subject, body: sent.append((to, subject, body)) or True)
    return sent


@pytest.fixture
def app(tmp_path):
    from app import create_app

    class TestConfig(Config):
        TESTING = True
        DATABASE_PATH = str(tmp_path / "test.db")
        TELEGRAM_BOT_TOKEN = TOKEN
        TELEGRAM_BOT_USERNAME = "samproducts_bot"
        ADMIN_TELEGRAM_ID = "777"
        TASK_TOKEN = "test-task-token"
    return create_app(TestConfig)


def signed(**overrides):
    payload = {"id": "42", "first_name": "Ada", "username": "ada", "auth_date": str(int(time.time()))}
    payload.update(overrides)
    secret = hashlib.sha256(TOKEN.encode()).digest()
    payload["hash"] = hmac.new(secret, data_check_string(payload).encode(), hashlib.sha256).hexdigest()
    return payload


def code_from(outbox):
    return re.search(r"\b(\d{8})\b", outbox[-1][2]).group(1)


# --- shell ------------------------------------------------------------------- #

def test_landing_wears_the_brand(client):
    page = client.get("/").get_data(as_text=True)
    assert "SAMBANG" in page and "GOLD" in page and "#d4af37" in page
    assert "Alat emas, telus." in page             # Bahasa Melayu first
    assert "Pendidikan sahaja" in page
    assert "brand/anton.woff2" in page and "brand/mascot-raise.png" in page


def test_language_toggle_switches_to_english(client):
    client.get("/lang/en")
    page = client.get("/").get_data(as_text=True)
    assert "Gold tools, transparent." in page and "Education only" in page
    assert client.get("/lang/xx").status_code == 302   # unknown codes are ignored, not errors


# --- Telegram door ----------------------------------------------------------- #

def test_telegram_login_creates_account_and_session(app, client):
    r = client.get("/auth/telegram", query_string=signed())
    assert r.status_code == 302 and r.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as s:
        assert s["user"]["telegram_id"] == "42" and s["user"]["owner"] == "42"
        assert s["user"]["is_admin"] is False and s["user"]["rank"] == "free"
    with app.app_context():
        assert store.user_by_telegram("42")["username"] == "ada"


def test_telegram_login_rejects_bad_hash(client):
    payload = signed()
    payload["id"] = "99"
    assert client.get("/auth/telegram", query_string=payload).status_code == 403


def test_admin_telegram_id_unlocks_admin(app, client):
    client.get("/auth/telegram", query_string=signed(id="777"))
    with client.session_transaction() as s:
        assert s["user"]["is_admin"] is True and s["user"]["rank"] == "elite"
    assert client.get("/admin").status_code == 200
    csv_body = client.get("/admin/users.csv")
    assert csv_body.mimetype == "text/csv" and "777" in csv_body.get_data(as_text=True)


def test_admin_is_forbidden_to_ordinary_members(client):
    login(client, "42")
    assert client.get("/admin").status_code == 403
    assert client.get("/admin/users.csv").status_code == 403


def test_dashboard_and_account_need_login(client):
    assert client.get("/dashboard").status_code == 302
    assert client.get("/account").status_code == 302
    login(client, "42")
    assert client.get("/dashboard").status_code == 200
    body = client.get("/account").get_data(as_text=True)
    assert "@tester" in body


# --- email door -------------------------------------------------------------- #

def test_email_code_round_trip_creates_a_verified_account(app, client, outbox):
    r = client.post("/auth/email/start", data={"email": "Ada@Example.com"})
    assert r.status_code == 200 and outbox[-1][0] == "ada@example.com"
    code = code_from(outbox)
    assert len(code) == 8 and code.isdigit()
    assert "SAMBANGGOLD" in outbox[-1][1]

    r = client.post("/auth/email/verify", data={"email": "ada@example.com", "code": code})
    assert r.status_code == 302 and r.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as s:
        assert s["user"]["email"] == "ada@example.com" and s["user"]["owner"].startswith("u:")
    with app.app_context():
        row = store.user_by_email("ada@example.com")
        assert row["verified_at"] and row["telegram_id"] is None


def test_wrong_code_then_lockout(app, client, outbox):
    client.post("/auth/email/start", data={"email": "b@example.com"})
    for _ in range(app.config["CODE_MAX_ATTEMPTS"]):
        r = client.post("/auth/email/verify", data={"email": "b@example.com", "code": "00000000"})
        assert r.status_code == 400
    r = client.post("/auth/email/verify", data={"email": "b@example.com", "code": code_from(outbox)})
    assert r.status_code == 400 and "Terlalu banyak" in r.get_data(as_text=True)


def test_code_is_single_use_and_resend_has_a_cooldown(app, client, outbox):
    client.post("/auth/email/start", data={"email": "c@example.com"})
    code = code_from(outbox)
    client.post("/auth/email/verify", data={"email": "c@example.com", "code": code})
    client.get("/auth/logout")
    r = client.post("/auth/email/verify", data={"email": "c@example.com", "code": code})
    assert r.status_code == 400
    assert client.post("/auth/email/start", data={"email": "c@example.com"}).status_code == 429


def test_bad_email_is_rejected(client, outbox):
    assert client.post("/auth/email/start", data={"email": "nope"}).status_code == 400
    assert outbox == []


def test_unconfigured_mail_shows_the_code_in_test_mode(client):
    r = client.post("/auth/email/start", data={"email": "d@example.com"})
    assert r.status_code == 200 and "Mod dev" in r.get_data(as_text=True)


# --- linking ------------------------------------------------------------------ #

def test_email_user_who_then_logs_in_with_telegram_is_linked_not_duplicated(app, client, outbox):
    client.post("/auth/email/start", data={"email": "e@example.com"})
    client.post("/auth/email/verify", data={"email": "e@example.com", "code": code_from(outbox)})
    with client.session_transaction() as s:
        uid, old_owner = s["user"]["uid"], s["user"]["owner"]
    with app.app_context():
        store.add_alert(old_owner, "XAUUSD", "above", 2500)

    client.get("/auth/telegram", query_string=signed(id="4242"))
    with client.session_transaction() as s:
        assert s["user"]["uid"] == uid and s["user"]["telegram_id"] == "4242" and s["user"]["owner"] == "4242"
    with app.app_context():
        assert store.user_counts()["users"] == 1
        assert [a["owner"] for a in store.alerts_for("4242")] == ["4242"]   # alerts followed the link


def test_telegram_user_can_add_an_email(app, client, outbox):
    client.get("/auth/telegram", query_string=signed(id="5"))
    client.post("/auth/email/start", data={"email": "f@example.com"})
    client.post("/auth/email/verify", data={"email": "f@example.com", "code": code_from(outbox)})
    with app.app_context():
        row = store.user_by_telegram("5")
        assert row["email"] == "f@example.com" and store.user_counts()["users"] == 1


def test_google_is_a_placeholder_page(client):
    body = client.get("/auth/google").get_data(as_text=True)
    assert "akan datang" in body
