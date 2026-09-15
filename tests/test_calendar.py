"""#5 Gold Calendar: feed filtering, FOMC/holiday schedules, seasonality fallback, pushes, both surfaces."""

import datetime as dt

from app import goldcal, store, watch
from app.telegram import handle_update, reply_for
from tests.conftest import fake_events, login
from tests.test_bot import buttons, msg, tap

UTC = dt.timezone.utc


def test_red_events_keep_only_high_usd_and_merge_fomc():
    now = dt.datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    reds = goldcal.red_events(now, days=14, events=fake_events(now))
    titles = [e["title"] for e in reds]
    assert "CPI m/m" in titles and "Non-Farm Employment Change" in titles
    assert "Retail Sales" not in titles and "ECB Rate" not in titles
    assert "FOMC Statement" in titles                     # 16 Sep 2026 comes from the embedded schedule
    assert titles == [e["title"] for e in sorted(reds, key=lambda e: e["at"])]


def test_fomc_statement_is_1400_new_york():
    e = [x for x in goldcal.fomc_events(2026) if x["at"].month == 9][0]
    assert e["at"].astimezone(goldcal.NY).strftime("%d %H:%M") == "16 14:00"


def test_next_holiday_and_seasonality_fallback():
    now = dt.datetime(2026, 3, 1, tzinfo=UTC)
    assert "Good Friday" in goldcal.next_holiday(now)["title"]
    table = goldcal.seasonality()
    assert table["source"] == "long-run static table" and set(range(1, 13)) <= set(table)


def test_month_grid_marks_events_and_holidays():
    now = dt.datetime(2026, 4, 1, tzinfo=UTC)
    weeks = goldcal.month_grid(2026, 4, now, events=goldcal.red_events(now, days=62, events=[]))
    cells = [c for w in weeks for c in w if c["in_month"]]
    assert len(cells) == 30
    assert any(c["holidays"] for c in cells if c["date"] == dt.date(2026, 4, 3))
    assert any(c["events"] for c in cells if c["date"] == dt.date(2026, 4, 30))   # FOMC 29 Apr 14:00 NY = 30 Apr 02:00 MYT


def test_quarter_pdf_is_a_valid_pdf_with_three_pages():
    now = dt.datetime(2026, 9, 1, tzinfo=UTC)
    body = goldcal.quarter_pdf(2026, 3, goldcal.red_events(now, days=120, events=fake_events(now)), goldcal.seasonality())
    assert body.startswith(b"%PDF-1.4") and body.rstrip().endswith(b"%%EOF")
    assert body.count(b"/Type /Page ") == 3 and b"FOMC Statement" in body


def test_bot_calendar_summary_and_alert_toggle(app):
    with app.app_context():
        text = reply_for("/calendar", chat_id=7, lang="en")
        assert "Next red USD events" in text and "CPI m/m" in text and "Next FOMC" in text
        assert "30-minute alert: <b>OFF</b>" in text
        assert "ON" in reply_for("/calendar_alert", chat_id=7, lang="en")
        assert store.calendar_subscribed(7)
        assert "MATI" in reply_for("/calendar_alert", chat_id=7, lang="ms")


def test_calendar_callback_toggles_and_edits_in_place(app):
    with app.app_context():
        handle_update(tap("lang_en"))
        actions = handle_update(msg("/calendar"))
        assert "🔔 Turn alerts on" in buttons(actions[0][3])
        actions = handle_update(tap("cal_on"))
        assert actions[1][0] == "edit" and "alert: <b>ON</b>" in actions[1][3]
        assert "🔕 Turn alerts off" in buttons(actions[1][4])


def test_checker_pushes_once_per_event_and_logs_spread(app, fake_feed):
    sent = []
    with app.app_context():
        store.tg_touch(7); store.tg_set_lang(7, "en")
        store.calendar_toggle(7, True)
        store.calendar_toggle(9, True)
        first = watch.check_alerts(lambda cid, text: sent.append((cid, text)))
        assert first["pushed"] == 2                       # CPI is 30 minutes out, both subscribers
        assert "CPI m/m" in sent[0][1] and "in 30 minutes" in [s for s in sent if s[0] == "7"][0][1]
        second = watch.check_alerts(lambda cid, text: sent.append((cid, text)))
        assert second["pushed"] == 0                      # dedup: never twice
        assert store.baseline_spread() == 1.0
        assert store.event_spread_history()[0]["title"] == "CPI m/m"


def test_dashboard_calendar_renders_grid_pdf_and_toggle(client):
    body = client.get("/p/gold-calendar").get_data(as_text=True)
    assert "CPI m/m" in body and "Good Friday" in body or "FOMC" in body
    assert "quarter.pdf" in body and "long-run static table" in body
    pdf = client.get("/p/gold-calendar/quarter.pdf")
    assert pdf.mimetype == "application/pdf" and pdf.data.startswith(b"%PDF")

    login(client, "42")
    body = client.post("/p/gold-calendar", data={"action": "cal_on"}).get_data(as_text=True)
    assert "Matikan alert" in body
    with client.application.app_context():
        assert store.calendar_subscribed("42")
