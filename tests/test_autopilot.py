"""Autopilot: the A-Team capability that asks the question for you.

What these pin down: a rank that cannot use it is told so rather than shown an
error, a quiet day sends nothing, a day only ever sends once, and a lapsed rank
stops the pushes without losing the subscription.
"""

import time

from app import autopilot, store
from app.telegram import handle_update

from tests.conftest import login


def _sent(app, now=None):
    out = []
    with app.app_context():
        result = autopilot.run_daily(lambda chat, text: out.append((str(chat), text)), now=now)
    return out, result


def test_only_a_team_and_above_may_switch_it_on(app):
    with app.app_context():
        reply = autopilot.bot_autopilot([], chat_id="77", lang="ms")
        assert "A-Team" in reply and "Pangkat" in reply      # told where to look, not errored
        store.grant_entitlement("77", "pro", source="manual")
        reply = autopilot.bot_autopilot([], chat_id="77", lang="ms")
        assert "gold-watch" in reply and "A-Team" not in reply


def test_toggle_round_trips_and_is_shared_between_surfaces(app):
    with app.app_context():
        store.grant_entitlement("77", "pro", source="manual")
        assert autopilot.toggle("77", "gold-watch") == "on"
        assert autopilot.subscribed("77", "gold-watch")
        assert autopilot.subscriptions("77")["gold-watch"] is True
        assert autopilot.toggle("77", "gold-watch") == "off"
        assert not autopilot.subscribed("77", "gold-watch")


def test_unknown_slug_lists_the_real_ones(app):
    with app.app_context():
        store.grant_entitlement("77", "pro", source="manual")
        reply = autopilot.bot_autopilot(["telepati"], chat_id="77", lang="en")
        assert "gold-watch" in reply and "miner-divergence" in reply


def test_a_subscribed_owner_gets_one_push_a_day(app):
    with app.app_context():
        store.grant_entitlement("77", "pro", source="manual")
        autopilot.toggle("77", "gold-watch", on=True)
    out, result = _sent(app)
    assert result["sent"] == 1 and out[0][0] == "77"
    assert "2,399" in out[0][1] or "2399" in out[0][1]      # the live bid, from the fake feed
    out2, result2 = _sent(app)
    assert result2["sent"] == 0 and out2 == []             # same day, already done

    tomorrow = time.time() + 86400
    out3, result3 = _sent(app, now=tomorrow)
    assert result3["sent"] == 1


def test_a_quiet_day_sends_nothing(app, fake_miners):
    """The miner screen only speaks when something is actually flagged."""
    with app.app_context():
        store.grant_entitlement("77", "pro", source="manual")
        autopilot.toggle("77", "miner-divergence", on=True)
        text = autopilot._sentinel("77", "ms")
    assert text is None            # no linked accounts, so nothing to say


def test_a_lapsed_rank_stops_the_pushes_but_keeps_the_switch(app):
    with app.app_context():
        store.grant_entitlement("77", "pro", source="manual", external_id="sub_x")
        autopilot.toggle("77", "gold-watch", on=True)
        store.revoke_entitlement(external_id="sub_x")
    out, result = _sent(app)
    assert out == [] and result["gated"] == 1
    with app.app_context():
        assert autopilot.subscribed("77", "gold-watch")     # the switch survives
        store.grant_entitlement("77", "pro", source="manual")
    out2, result2 = _sent(app)
    assert result2["sent"] == 1                              # and resumes


def _msg(text, uid=7):
    return {"message": {"chat": {"id": uid}, "from": {"id": uid, "username": "ada", "first_name": "Ada"}, "text": text}}


def test_the_bot_command_is_reachable_and_gated(app):
    with app.app_context():
        handle_update(_msg("/start"))
        texts = [a[2] for a in handle_update(_msg("/autopilot")) if a[0] == "send"]
        assert any("A-Team" in x for x in texts)
        store.grant_entitlement("7", "elite", source="manual")
        texts = [a[2] for a in handle_update(_msg("/autopilot")) if a[0] == "send"]
        assert any("gold-watch" in x for x in texts)


def test_dashboard_panel_is_read_only_below_a_team(client, app):
    login(client, user_id="42")
    body = client.get("/dashboard").get_data(as_text=True)
    assert "Autopilot" in body and "A-Team" in body

    with app.app_context():
        store.grant_entitlement("42", "pro", source="manual")
    login(client, user_id="42")
    with client.session_transaction() as s:
        user = dict(s["user"]); user["rank"] = "pro"; s["user"] = user
    r = client.post("/dashboard", data={"slug": "gold-watch"}, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        assert autopilot.subscribed("42", "gold-watch")


# --- reports: weekly and monthly ------------------------------------------- #

def test_report_slugs_belong_to_a_real_product():
    from app.products import BY_SLUG as PRODUCTS
    for slug in autopilot.SLUGS:
        assert autopilot.product_of(slug) in PRODUCTS
    assert set(autopilot.DAILY) | set(autopilot.REPORTS) == set(autopilot.SLUGS)


def test_reports_need_the_reports_capability_not_autopilot(app):
    with app.app_context():
        assert autopilot.NEEDS["gold-watch"] == "autopilot"
        assert autopilot.NEEDS["churn-radar:book"] == "reports"


def test_a_weekly_report_fires_once_a_week_not_once_a_day(app):
    with app.app_context():
        store.grant_entitlement("77", "pro", source="manual")
        autopilot.toggle("77", "ib-revenue-calculator:forecast", on=True)
        store.save_run("ib-revenue-calculator", {"net": 4200.0, "annual": 50400.0, "clients": 25}, owner="77")

    monday = 1_757_462_400.0            # a fixed instant, so the period keys are stable
    out, res = _sent(app, now=monday)
    assert res["sent"] == 1 and "4,200" in out[0][1]

    out2, res2 = _sent(app, now=monday + 86400)       # next day, same month
    assert res2["sent"] == 0

    out3, res3 = _sent(app, now=monday + 40 * 86400)  # next month
    assert res3["sent"] == 1


def test_a_report_with_nothing_to_read_stays_silent(app):
    with app.app_context():
        store.grant_entitlement("77", "pro", source="manual")
        autopilot.toggle("77", "rebate-auditor:audit", on=True)
        assert autopilot._rebate_report("77", "ms") is None
        assert autopilot._book_report("77", "ms") is None
    out, res = _sent(app)
    assert out == [] and res["sent"] == 0


def test_the_book_scorecard_names_only_the_clients_at_risk(app):
    """Built from a real scan, so the report and the tool cannot disagree."""
    from app import churn
    run = churn.scan_book(churn.parse_log(churn.sample_log()), 6.0)
    at_risk = [c for c in run["clients"] if c["band"] in ("risk", "watch")]
    assert at_risk, "the sample book should contain someone worth flagging"
    with app.app_context():
        store.save_run("churn-radar", run, owner="77")
        text = autopilot._book_report("77", "en")
    assert text and "of %d clients" % len(run["clients"]) in text
    assert str(at_risk[0]["account"]) in text


def test_the_dashboard_separates_reports_from_daily(client, app):
    with app.app_context():
        store.grant_entitlement("42", "pro", source="manual")
    login(client, user_id="42")
    with client.session_transaction() as s:
        user = dict(s["user"]); user["rank"] = "pro"; s["user"] = user
    body = client.get("/dashboard").get_data(as_text=True)
    assert "Laporan berjadual" in body
    assert "mingguan" in body and "bulanan" in body
