"""POST /team/tasks/setup — the HTTP-triggered alternative to the local
`flask team-seed`/`team-set-webhook` CLI commands, for when there's no
shell access inside the deployed container (e.g. `railway run` executes
locally, not inside it, so it can't reach the volume-mounted database)."""

from app import store, teamsetup


def test_requires_the_task_token(client):
    assert client.post("/team/tasks/setup").status_code == 403
    assert client.post("/team/tasks/setup", headers={"X-Task-Token": "wrong"}).status_code == 403


def test_seeds_roadmap_and_files_and_returns_counts(client, app):
    r = client.post("/team/tasks/setup", headers={"X-Task-Token": "test-task-token"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["roadmap_items"] == 26   # 18 saas-tools + 8 digital-products
    assert body["file_items"] > 0
    with app.app_context():
        assert len(store.roadmap_items()) == 26


def test_bootstraps_ceo_when_admin_id_configured(client, app):
    app.config["ADMIN_TELEGRAM_ID"] = "42"
    r = client.post("/team/tasks/setup", headers={"X-Task-Token": "test-task-token"})
    assert r.get_json()["ceo_granted"] == "42"
    with app.app_context():
        assert store.team_role("42") == "ceo"


def test_does_not_reset_ceo_once_someone_already_holds_a_role(client, app):
    with app.app_context():
        store.set_team_role("777", "hod_sales")
    app.config["ADMIN_TELEGRAM_ID"] = "42"
    r = client.post("/team/tasks/setup", headers={"X-Task-Token": "test-task-token"})
    assert r.get_json()["ceo_granted"] is None
    with app.app_context():
        assert store.team_role("42") is None


def test_team_webhook_is_none_when_team_bot_token_unset(client, app):
    r = client.post("/team/tasks/setup", headers={"X-Task-Token": "test-task-token"})
    assert r.get_json()["team_webhook"] is None


def test_re_running_is_safe_and_idempotent(client, app):
    client.post("/team/tasks/setup", headers={"X-Task-Token": "test-task-token"})
    with app.app_context():
        store.set_roadmap_status("gold-watch", "in_progress", "1", notes="mid-rebuild")
    r2 = client.post("/team/tasks/setup", headers={"X-Task-Token": "test-task-token"})
    assert r2.get_json()["roadmap_items"] == 26
    with app.app_context():
        row = [i for i in store.roadmap_items() if i["slug"] == "gold-watch"][0]
        assert row["internal_status"] == "in_progress"   # not clobbered by the re-run


def test_set_team_webhook_returns_none_without_a_token(app):
    with app.app_context():
        assert teamsetup.set_team_webhook() is None
