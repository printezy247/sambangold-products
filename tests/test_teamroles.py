"""Team ops data layer: roles, tasks, roadmap seeding — store.py functions."""

import pytest

from app import roadmap, store


def test_set_and_read_team_role(app):
    with app.app_context():
        store.set_team_role("111", "ceo", display_name="Sam", added_by="system")
        assert store.team_role("111") == "ceo"
        member = store.team_member("111")
        assert member["display_name"] == "Sam"


def test_set_team_role_rejects_unknown_role(app):
    with app.app_context():
        with pytest.raises(ValueError):
            store.set_team_role("111", "intern")


def test_set_team_role_upserts(app):
    with app.app_context():
        store.set_team_role("222", "executive")
        store.set_team_role("222", "hod_sales")
        assert store.team_role("222") == "hod_sales"
        assert len(store.list_team_members()) == 1


def test_remove_team_role(app):
    with app.app_context():
        store.set_team_role("333", "executive")
        store.remove_team_role("333")
        assert store.team_role("333") is None


def test_add_and_update_task(app):
    with app.app_context():
        t = store.add_task("Ship Q3 report", created_by="111", assigned_to="222", priority="high")
        assert t["status"] == "open"
        updated = store.update_task(t["id"], status="done")
        assert updated["status"] == "done"
        assert updated["completed_at"] is not None


def test_tasks_all_filters_by_status_and_assignee(app):
    with app.app_context():
        store.add_task("A", created_by="1", assigned_to="222")
        store.add_task("B", created_by="1", assigned_to="333")
        store.update_task(store.tasks_all()[0]["id"], status="done")
        assert len(store.tasks_all(status="open")) == 1
        assert len(store.tasks_all(assigned_to="222")) == 1


def test_tasks_overdue_excludes_done(app):
    with app.app_context():
        t = store.add_task("Overdue", created_by="1", due_at=1.0)
        assert any(x["id"] == t["id"] for x in store.tasks_overdue(now=100.0))
        store.update_task(t["id"], status="done")
        assert not any(x["id"] == t["id"] for x in store.tasks_overdue(now=100.0))


def test_seed_roadmap_is_idempotent_and_preserves_edits(app):
    with app.app_context():
        store.seed_roadmap(roadmap.seed_data())
        first_count = len(store.roadmap_items())
        assert first_count == 26  # 18 saas-tools + 8 digital-products

        store.set_roadmap_status("gold-watch", "in_progress", "111", notes="mid-rebuild")
        store.seed_roadmap(roadmap.seed_data())  # re-seed must not clobber the edit
        row = [i for i in store.roadmap_items() if i["slug"] == "gold-watch"][0]
        assert row["internal_status"] == "in_progress"
        assert row["notes"] == "mid-rebuild"
        assert len(store.roadmap_items()) == first_count


def test_seed_roadmap_covers_both_families(app):
    with app.app_context():
        store.seed_roadmap(roadmap.seed_data())
        families = {i["family"] for i in store.roadmap_items()}
        assert families == {"saas-tools", "digital-products"}


def test_notify_prefs_default_on(app):
    with app.app_context():
        prefs = store.notify_prefs("999")
        assert prefs["daily_digest"] == 1
        store.set_notify_pref("999", "daily_digest", False)
        assert store.notify_prefs("999")["daily_digest"] == 0
        assert "999" not in store.notify_prefs_enabled("daily_digest")
