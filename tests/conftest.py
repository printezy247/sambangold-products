"""Shared fixtures: no test touches the network or the real data directory."""

import pytest

import datetime as dt

from app import create_app, feeds, goldcal, miners, tokengold
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


REAL_TOKEN_FETCH = tokengold.fetch      # the unpatched function, for the one test that exercises it
FAKE_TOKENS = {"at": 0.0, "source_spot": "Yahoo GC=F (front futures)", "errors": [],
               "paxg": 2420.0, "xaut": 2410.0, "spot": 2400.0, "usdt": 0.9995}


@pytest.fixture(autouse=True)
def fake_tokens(monkeypatch):
    """#17: PAXG, XAUT, GC=F and USDT come from here; tests mutate the dict to move the premium."""
    snap = dict(FAKE_TOKENS)
    monkeypatch.setattr(tokengold, "fetch", lambda: dict(snap))
    tokengold.clear_cache()
    yield snap
    tokengold.clear_cache()


REAL_MINER_FETCH = miners.fetch_history


def fake_miner_history(days=130, start=1_750_000_000):
    """Deterministic six months: gold drifts up; each name = beta × gold plus its own drift, so residuals are known."""
    import math
    gold = [(start + i * 86400, 2400.0 * math.exp(0.001 * i + 0.01 * math.sin(i / 3.0))) for i in range(days)]
    hist = {miners.GOLD: gold, "errors": []}
    profile = {"GDX": (2.0, 0.0), "GDXJ": (2.5, 0.0), "NEM": (1.5, 0.0), "B": (1.5, -0.004), "AEM": (1.2, 0.0), "KGC": (1.8, 0.0),
               "AU": (1.6, 0.0), "GFI": (1.7, 0.0), "HMY": (2.0, 0.004), "AGI": (1.4, 0.0), "BTG": (1.9, 0.0),
               "FNV": (0.8, 0.0), "WPM": (0.9, 0.0), "RGLD": (0.7, 0.0)}
    for u in miners.UNIVERSE:
        b, drift = profile[u["ticker"]]
        px = [100.0]
        for i in range(1, days):
            g = math.log(gold[i][1] / gold[i - 1][1])
            px.append(px[-1] * math.exp(b * g + (drift if i >= days - 20 else 0.0)))
        hist[u["ticker"]] = [(ts, round(p, 4)) for (ts, _), p in zip(gold, px)]
    return hist


@pytest.fixture(autouse=True)
def fake_miners(monkeypatch):
    """#18: six months of miner and gold closes come from here."""
    hist = fake_miner_history()
    monkeypatch.setattr(miners, "fetch_history", lambda: {k: (list(v) if isinstance(v, list) else v) for k, v in hist.items()})
    miners.clear_cache()
    yield hist
    miners.clear_cache()


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


def login(client, user_id="42", email=None, admin=False, rank=None, team_role=None):
    """Put a signed-in user in the session the way auth.sign_in would.

    Signing in grants no rank: `public` unless the caller asks for one, which
    mirrors `auth.rank_for` now that General is paid for or earned at the
    broker door. `team_role` mirrors `auth.session_user`'s team_role — None
    for everyone outside Sam's internal team ops."""
    with client.session_transaction() as s:
        s["user"] = {"uid": 1, "owner": user_id, "telegram_id": user_id, "email": email,
                     "username": "tester", "name": "Test", "locale": "ms",
                     "is_admin": admin, "rank": rank or ("elite" if admin else "public"),
                     "team_role": team_role}
