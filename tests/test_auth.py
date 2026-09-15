"""Telegram Login Widget verification — the account spine."""

import hashlib
import hmac
import time

from app.auth import data_check_string, verify

TOKEN = "123456:test-token-not-a-real-secret"


def signed(**overrides):
    payload = {
        "id": "42",
        "first_name": "Ada",
        "username": "ada",
        "auth_date": str(int(time.time())),
    }
    payload.update(overrides)
    secret = hashlib.sha256(TOKEN.encode()).digest()
    payload["hash"] = hmac.new(
        secret, data_check_string(payload).encode(), hashlib.sha256
    ).hexdigest()
    return payload


def test_accepts_a_correctly_signed_payload():
    assert verify(signed(), TOKEN) is True


def test_rejects_a_tampered_field():
    payload = signed()
    payload["id"] = "99"
    assert verify(payload, TOKEN) is False


def test_rejects_a_wrong_bot_token():
    assert verify(signed(), "999:someone-elses-token") is False


def test_rejects_a_stale_login():
    old = str(int(time.time()) - 90000)
    assert verify(signed(auth_date=old), TOKEN, max_age_seconds=86400) is False


def test_rejects_a_missing_hash():
    payload = signed()
    del payload["hash"]
    assert verify(payload, TOKEN) is False


def test_rejects_when_no_bot_token_is_configured():
    assert verify(signed(), "") is False
