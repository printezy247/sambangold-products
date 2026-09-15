"""Shared fixtures: no test touches the network or the real data directory."""

import pytest

from app import create_app, feeds
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


def login(client, user_id="42"):
    with client.session_transaction() as s:
        s["user"] = {"id": user_id, "username": "tester", "first_name": "Test"}
