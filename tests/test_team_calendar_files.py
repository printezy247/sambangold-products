"""Calendar (week/month toggle) and file library — access control and
behaviour."""

import datetime as dt

import pytest

from app import library, store, teamcalendar
from tests.conftest import login


def test_week_days_returns_monday_to_sunday():
    days = teamcalendar.week_days(offset=0)
    assert len(days) == 7
    assert days[0].weekday() == 0
    assert days[-1].weekday() == 6


def test_month_weeks_covers_the_whole_month():
    weeks, month_start = teamcalendar.month_weeks(offset=0)
    all_days = [d for w in weeks for d in w]
    today = dt.date.today()
    in_month = [d for d in all_days if d.month == today.month and d.year == today.year]
    days_in_month = (dt.date(today.year + (today.month == 12), today.month % 12 + 1, 1) - dt.date(today.year, today.month, 1)).days
    assert len(in_month) == days_in_month
    assert month_start.day == 1


def test_day_bounds_spans_exactly_one_day():
    start, end = teamcalendar.day_bounds(dt.date(2026, 1, 1))
    assert end - start == 86400


def test_calendar_requires_team_role(client):
    assert client.get("/team/calendar").status_code == 302
    login(client, user_id="1")
    assert client.get("/team/calendar").status_code == 403


def test_calendar_week_view_shows_a_due_task(client, app):
    with app.app_context():
        today_start, _ = teamcalendar.day_bounds(dt.date.today())
        store.add_task("Due today", created_by="1", due_at=today_start + 3600)
    login(client, user_id="1", team_role="executive")
    body = client.get("/team/calendar").get_data(as_text=True)
    assert "Due today" in body


def test_calendar_month_view_renders(client):
    login(client, user_id="1", team_role="ceo")
    assert client.get("/team/calendar?view=month").status_code == 200


def test_library_scan_finds_seeded_files(app):
    items = library.scan_repo_files()
    assert any(it["category"] == "doc" for it in items)
    assert any(it["category"] == "pic" for it in items)
    assert any(it["category"] == "vid" for it in items)
    assert all(it["source"] == "repo_asset" for it in items)


def test_seed_file_items_is_idempotent(app):
    with app.app_context():
        store.seed_file_items(library.seed_data())
        first = len(store.file_items())
        store.seed_file_items(library.seed_data())
        assert len(store.file_items()) == first


def test_seed_data_links_the_5_paid_titles_to_drive_not_git():
    """The paid-tier ebooks (sold on website_sam) must never be files
    committed to this public repo — they're Drive links only."""
    items = library.seed_data()
    paid = [it for it in items if it["tags"] in ("standard", "premium")]
    assert len(paid) == 10   # 5 titles x EN+BM
    assert all(it["source"] == "drive" for it in paid)
    assert all(it["url"].startswith("https://drive.google.com/") for it in paid)
    assert {it["tags"] for it in paid} == {"standard", "premium"}


def test_files_page_requires_team_role(client):
    assert client.get("/team/files").status_code == 302
    login(client, user_id="1")
    assert client.get("/team/files").status_code == 403


def test_executive_can_browse_but_not_add_files(client, app):
    with app.app_context():
        store.seed_file_items(library.seed_data())
    login(client, user_id="1", team_role="executive")
    page = client.get("/team/files")
    assert page.status_code == 200

    r = client.post("/team/files", data={"title": "New link", "category": "doc", "url": "https://example.test/x"})
    assert r.status_code == 403


def test_hod_can_add_an_external_link(client, app):
    login(client, user_id="1", team_role="hod_marketing")
    r = client.post("/team/files", data={"title": "Campaign brief", "category": "doc", "url": "https://example.test/brief"})
    assert r.status_code == 302
    with app.app_context():
        items = store.file_items(category="doc")
        assert any(it["title"] == "Campaign brief" for it in items)


def test_repo_asset_file_downloads(client, app):
    with app.app_context():
        store.seed_file_items(library.seed_data())
        item = [it for it in store.file_items(category="pic") if it["source"] == "repo_asset"][0]
    login(client, user_id="1", team_role="executive")
    r = client.get("/team/library/%s" % item["url"])
    assert r.status_code == 200


def test_library_file_requires_team_role(client, app):
    with app.app_context():
        store.seed_file_items(library.seed_data())
        item = [it for it in store.file_items(category="pic") if it["source"] == "repo_asset"][0]
    assert client.get("/team/library/%s" % item["url"]).status_code == 302


def test_scan_paid_files_is_empty_when_volume_absent(tmp_path):
    assert library.scan_paid_files(str(tmp_path / "does-not-exist")) == []


def test_paid_file_serves_from_the_volume_path_not_git(app, client, tmp_path, monkeypatch):
    paid_docs = tmp_path / "docs"
    paid_docs.mkdir()
    (paid_docs / "Gold Recruit Manual.pdf").write_bytes(b"%PDF-1.4 fake paid content")
    app.config["PAID_LIBRARY_PATH"] = str(tmp_path)

    with app.app_context():
        store.seed_file_items(library.scan_paid_files(str(tmp_path)))
        item = [it for it in store.file_items() if it["source"] == "volume"][0]
        assert item["title"] == "Gold Recruit Manual"

    login(client, user_id="1", team_role="executive")
    r = client.get("/team/library-paid/%s" % item["url"])
    assert r.status_code == 200
    assert b"fake paid content" in r.get_data()


def test_paid_file_route_requires_team_role(app, client, tmp_path):
    paid_docs = tmp_path / "docs"
    paid_docs.mkdir()
    (paid_docs / "Gold Recruit Manual.pdf").write_bytes(b"fake")
    app.config["PAID_LIBRARY_PATH"] = str(tmp_path)
    assert client.get("/team/library-paid/docs/Gold Recruit Manual.pdf").status_code == 302
