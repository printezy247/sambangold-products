"""The deploy-health panel: three silent failures made to speak up."""

import time

from app import health, store
from tests.conftest import login


def rows(app, **config):
    app.config.update(config)
    with app.test_request_context("https://sambangold.test/admin"):
        return {r["key"]: r for r in health.report()}


def test_it_reports_one_row_for_each_silent_failure(app):
    r = rows(app, PUBLIC_BASE_URL="https://sambangold.test")
    assert list(r) == ["base", "db", "checker", "hook", "token"]


def test_a_base_url_pointing_at_the_old_host_is_a_warning(app):
    """Telegram sign-in is signed against PUBLIC_BASE_URL. Point it at a host
    we have left and every sign-in fails with no error anywhere."""
    assert rows(app, PUBLIC_BASE_URL="https://sambangold.test")["base"]["state"] == "ok"
    stale = rows(app, PUBLIC_BASE_URL="https://old-host.example")["base"]
    assert stale["state"] == "warn" and "old-host.example" in stale["detail"]


def test_an_unset_base_url_is_not_merely_a_warning(app):
    assert rows(app, PUBLIC_BASE_URL="")["base"]["state"] == "bad"


def test_a_checker_that_stopped_reaching_us_goes_red(app):
    with app.test_request_context("https://sambangold.test/admin"):
        assert health._checker_row()["state"] == "bad"          # never ran
        store.note(health.CHECKER_KEY, "0/3")
        assert health._checker_row()["state"] == "ok"
        store.db().execute("UPDATE meta SET at = ? WHERE key = ?",
                           (time.time() - health.CHECKER_STALE - 60, health.CHECKER_KEY))
        store.db().commit()
        late = health._checker_row()
        assert late["state"] == "bad" and "min" in late["detail"]


def test_the_task_token_is_never_printed(app):
    r = rows(app, TASK_TOKEN="s3cret-token-value")
    assert r["token"]["state"] == "ok" and "s3cret" not in r["token"]["detail"]
    assert rows(app, TASK_TOKEN="")["token"]["state"] == "bad"


def test_the_checker_records_a_heartbeat_when_it_runs(client, app):
    r = client.post("/tasks/check-alerts", headers={"X-Task-Token": "test-task-token"})
    assert r.status_code == 200
    with app.test_request_context():
        assert store.noted(health.CHECKER_KEY) is not None


def test_a_wrong_token_writes_nothing(client, app):
    assert client.post("/tasks/check-alerts", headers={"X-Task-Token": "wrong"}).status_code == 403
    with app.test_request_context():
        assert store.noted(health.CHECKER_KEY) is None


def test_the_panel_is_on_the_admin_page_and_admin_only(client, app):
    login(client, user_id="99", admin=True)
    app.config["ADMIN_TELEGRAM_ID"] = "99"
    body = client.get("/admin").get_data(as_text=True)
    assert "Kesihatan deploy" in body and "Pemeriksa alert" in body
