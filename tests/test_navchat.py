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
