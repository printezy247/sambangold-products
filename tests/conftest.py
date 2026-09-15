"""Shared fixtures: no test touches the network or the real data directory."""

import pytest

import datetime as dt

from app import create_app, feeds, goldcal
from app.config import Config

FAKE_QUOTE = {"symbol": "XAUUSD", "source": "test feed", "bid": 2399.50, "ask": 2400.50,
              "mid": 2400.0, "spread": 1.0, "at": 0.0}


@pytest.fixture(autouse=True)
def fake_feed(monkeypatch):
    """Every quote comes from here; tests mutate the dict to move the market."""
    quote = dict(FAKE_QUOTE)
    monkeypatch.setattr(feeds, "fetch", lambda: dict(quote))
    feeds.clear_cache()
    yield quote
    feeds.clear_cache()


def fake_events(now=None):
    """Two red USD events relative to now, plus one medium and one non-USD to be filtered out."""
    now = now or dt.datetime.now(dt.timezone.utc)
    mk = lambda title, hours, impact="High", country="USD": {
        "title": title, "country": country, "impact": impact, "at": now + dt.timedelta(hours=hours),
        "forecast": "3.1%", "previous": "3.0%", "source": "Forex Factory"}
    return [mk("CPI m/m", 0.45), mk("Non-Farm Employment Change", 30), mk("Retail Sales", 5, "Medium"), mk("ECB Rate", 2, country="EUR")]


@pytest.fixture(autouse=True)
def fake_calendar(monkeypatch):
    monkeypatch.setattr(goldcal, "fetch_events", lambda: fake_events())
    monkeypatch.setattr(goldcal, "_yahoo_monthly", lambda: (_ for _ in ()).throw(ConnectionError("no network")))
    goldcal.clear_cache()
    yield
    goldcal.clear_cache()


@pytest.fixture
def app(tmp_path):
    class TestConfig(Config):
        TESTING = True
        DATABASE_PATH = str(tmp_path / "test.db")
        TASK_TOKEN = "test-task-token"
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, user_id="42", email=None, admin=False):
    """Put a signed-in user in the session the way auth.sign_in would."""
    with client.session_transaction() as s:
        s["user"] = {"uid": 1, "owner": user_id, "telegram_id": user_id, "email": email,
                     "username": "tester", "name": "Test", "locale": "ms",
                     "is_admin": admin, "rank": "elite" if admin else "free"}
