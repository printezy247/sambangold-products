"""/team/chat — access control and that local search works without any
AI configuration (the common case until NARA_API_KEY is set)."""

from app import store
from tests.conftest import login


def test_chat_requires_team_role(client):
    assert client.get("/team/chat").status_code == 302
    login(client, user_id="1")
    assert client.get("/team/chat").status_code == 403


def test_executive_can_search_without_any_ai_configured(client, app):
    with app.app_context():
        store.add_file_item("doc", "Gold Trading Field Manual", "drive", "https://example.test/manual")
    login(client, user_id="1", team_role="executive")
    page = client.post("/team/chat", data={"query": "field manual"})
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "Gold Trading Field Manual" in body
    assert "example.test/manual" in body


def test_no_matches_shows_a_friendly_message(client):
    login(client, user_id="1", team_role="ceo")
    body = client.post("/team/chat", data={"query": "xyzzy nonsense"}).get_data(as_text=True)
    assert "No matching files" in body or "Tiada fail sepadan" in body


def test_blank_query_shows_no_results_section(client):
    login(client, user_id="1", team_role="ceo")
    page = client.post("/team/chat", data={"query": "  "})
    assert page.status_code == 200
