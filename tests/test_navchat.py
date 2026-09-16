"""/team/chat's search layer: local keyword search always works; the
optional AI layer only activates when fully configured, and never raises."""

import pytest

from app import navchat


ITEMS = [
    {"id": 1, "category": "doc", "title": "Gold Trading Field Manual", "tags": "standard"},
    {"id": 2, "category": "doc", "title": "Checklist Sniper", "tags": "free"},
    {"id": 3, "category": "pic", "title": "SamBangGold Brand Kit", "tags": "brand"},
]


def test_search_matches_on_title_words():
    results = navchat.search_files("checklist", ITEMS)
    assert [it["id"] for it in results] == [2]


def test_search_matches_on_tags():
    results = navchat.search_files("free tier stuff", ITEMS)
    assert 2 in [it["id"] for it in results]


def test_search_ranks_more_word_overlap_higher():
    results = navchat.search_files("brand kit", ITEMS)
    assert results[0]["id"] == 3


def test_search_empty_query_returns_nothing():
    assert navchat.search_files("", ITEMS) == []
    assert navchat.search_files("   ", ITEMS) == []


def test_search_no_match_returns_empty():
    assert navchat.search_files("xyzzy nonsense", ITEMS) == []


def test_configured_requires_all_three_settings():
    assert not navchat.configured({})
    assert not navchat.configured({"NARA_API_KEY": "k", "NARA_BASE_URL": "", "NARA_MODEL": "m"})
    assert navchat.configured({"NARA_API_KEY": "k", "NARA_BASE_URL": "https://api.example.test", "NARA_MODEL": "m"})


def test_configured_requires_at_least_one_model_in_the_list():
    assert not navchat.configured({"NARA_API_KEY": "k", "NARA_BASE_URL": "https://api.example.test", "NARA_MODEL": " , ,"})
    assert navchat.configured({"NARA_API_KEY": "k", "NARA_BASE_URL": "https://api.example.test", "NARA_MODEL": "a,b,c"})


def test_ai_answer_returns_none_when_unconfigured_without_a_network_call(monkeypatch):
    def fail(*a, **kw):
        raise AssertionError("should not call the network when unconfigured")
    monkeypatch.setattr(navchat.requests, "post", fail)
    assert navchat.ai_answer("where's the manual", ITEMS, {}) is None


def test_ai_answer_swallows_request_failures(monkeypatch):
    def boom(*a, **kw):
        raise navchat.requests.RequestException("down")
    monkeypatch.setattr(navchat.requests, "post", boom)
    config = {"NARA_API_KEY": "k", "NARA_BASE_URL": "https://api.example.test", "NARA_MODEL": "m"}
    assert navchat.ai_answer("where's the manual", ITEMS, config) is None


def test_ai_answer_parses_a_successful_response(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "  Try the Field Manual.  "}}]}

    monkeypatch.setattr(navchat.requests, "post", lambda *a, **kw: FakeResp())
    config = {"NARA_API_KEY": "k", "NARA_BASE_URL": "https://api.example.test", "NARA_MODEL": "m"}
    assert navchat.ai_answer("where's the manual", ITEMS, config) == "Try the Field Manual."


def test_ai_answer_rotates_to_the_next_model_when_the_first_fails(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "from the second model"}}]}

    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(json["model"])
        if json["model"] == "model-a":
            raise navchat.requests.RequestException("rate limited")
        return FakeResp()

    monkeypatch.setattr(navchat.requests, "post", fake_post)
    config = {"NARA_API_KEY": "k", "NARA_BASE_URL": "https://api.example.test", "NARA_MODEL": "model-a, model-b"}
    assert navchat.ai_answer("where's the manual", ITEMS, config) == "from the second model"
    assert calls == ["model-a", "model-b"]


def test_ai_answer_returns_none_when_every_model_fails(monkeypatch):
    def always_fail(*a, **kw):
        raise navchat.requests.RequestException("down")
    monkeypatch.setattr(navchat.requests, "post", always_fail)
    config = {"NARA_API_KEY": "k", "NARA_BASE_URL": "https://api.example.test", "NARA_MODEL": "model-a,model-b,model-c"}
    assert navchat.ai_answer("where's the manual", ITEMS, config) is None


def test_ai_answer_stops_rotating_once_a_model_succeeds(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "answer"}}]}

    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(json["model"])
        return FakeResp()

    monkeypatch.setattr(navchat.requests, "post", fake_post)
    config = {"NARA_API_KEY": "k", "NARA_BASE_URL": "https://api.example.test", "NARA_MODEL": "model-a,model-b,model-c"}
    navchat.ai_answer("q", ITEMS, config)
    assert calls == ["model-a"]   # never tries b or c once a succeeds
