"""Access control and behaviour for /team/* — CEO/HOD full access, Executive
read-only, everyone else locked out."""

import pytest

from app import roadmap, store
from tests.conftest import login


@pytest.fixture(autouse=True)
def seeded(app):
    with app.app_context():
        store.seed_roadmap(roadmap.seed_data())
    yield


def test_anonymous_is_redirected_to_signin(client):
    assert client.get("/team/roadmap").status_code == 302


def test_signed_in_without_team_role_is_403(client):
    login(client, user_id="1")
    assert client.get("/team/roadmap").status_code == 403


@pytest.mark.parametrize("role", ["ceo", "hod_sales", "hod_marketing", "executive"])
def test_every_team_role_can_view_roadmap(client, role):
    login(client, user_id="1", team_role=role)
    page = client.get("/team/roadmap")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "Gold Watch" in body


@pytest.mark.parametrize("role", ["ceo", "hod_sales", "hod_marketing"])
def test_full_access_roles_can_edit_roadmap_status(client, app, role):
    login(client, user_id="1", team_role=role)
    r = client.post("/team/roadmap", data={"slug": "gold-watch", "internal_status": "in_progress", "notes": "rebuild"})
    assert r.status_code == 302
    with app.app_context():
        row = [i for i in store.roadmap_items() if i["slug"] == "gold-watch"][0]
        assert row["internal_status"] == "in_progress"


def test_executive_cannot_edit_roadmap_status(client, app):
    login(client, user_id="1", team_role="executive")
    r = client.post("/team/roadmap", data={"slug": "gold-watch", "internal_status": "in_progress"})
    assert r.status_code == 403
    with app.app_context():
        row = [i for i in store.roadmap_items() if i["slug"] == "gold-watch"][0]
        assert row["internal_status"] == "launched"


def test_hod_can_add_and_advance_a_task(client, app):
    login(client, user_id="111", team_role="hod_sales")
    r = client.post("/team/tasks", data={"title": "Call top lead", "priority": "high"})
    assert r.status_code == 302
    with app.app_context():
        t = store.tasks_all()[0]
    r2 = client.post("/team/tasks/%d/status" % t["id"], data={"status": "done"})
    assert r2.status_code == 302
    with app.app_context():
        assert store.task(t["id"])["status"] == "done"


def test_executive_cannot_add_a_task(client):
    login(client, user_id="1", team_role="executive")
    r = client.post("/team/tasks", data={"title": "Should not save"})
    assert r.status_code == 403


def test_executive_can_view_tasks(client):
    login(client, user_id="1", team_role="executive")
    assert client.get("/team/tasks").status_code == 200


def test_only_ceo_can_manage_people(client):
    login(client, user_id="1", team_role="hod_sales")
    assert client.get("/team/people").status_code == 403

    login(client, user_id="2", team_role="ceo")
    r = client.post("/team/people", data={"telegram_id": "555", "role": "executive", "display_name": "New Exec"})
    assert r.status_code == 302


def test_ceo_grant_is_readable_afterwards(client, app):
    login(client, user_id="2", team_role="ceo")
    client.post("/team/people", data={"telegram_id": "555", "role": "executive", "display_name": "New Exec"})
    with app.app_context():
        assert store.team_role("555") == "executive"
