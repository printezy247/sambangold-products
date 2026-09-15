"""Group auto-scan, and the admin-rank bug that hid behind it.

The scanners answer one pasted pitch well. What a group lead needs is not to
paste anything: the scam lands in their room at 2am and by morning three
members have sent USDT somewhere. So the bot watches the room instead.
"""

import time

from app import groups, store
from app.gate import owner_tier
from app.auth import rank_for
from app.telegram import handle_update

PITCH = ("Join my VIP gold signals now! 95% win rate guaranteed, no loss ever. "
         "Send USDT to my wallet and I will double your account in 7 days. Limited slots, hurry!")
CHAT = "Just woke up, what did gold do overnight? Looks like it held the level from yesterday okay."


def _group_msg(text, uid=7, gid=-100123, title="Sam Flip Seribu"):
    return {"message": {"chat": {"id": gid, "type": "supergroup", "title": title},
                        "from": {"id": uid, "username": "ada", "first_name": "Ada"}, "text": text}}


def _watch(app, uid="7", gid="-100123"):
    store.grant_entitlement(uid, "pro", source="manual")
    return groups.watch(gid, "Sam Flip Seribu", uid)


# --- the reported bug ------------------------------------------------------- #

def test_the_admin_is_rambo_in_the_bot_not_only_on_the_page(app):
    """Reported: /autopilot told the owner that daily alerts were an A-Team
    capability. The rank was decided in auth.rank_for, which the bot never
    calls, so the admin was Rambo on the page and Awam in the chat."""
    with app.app_context():
        app.config["ADMIN_TELEGRAM_ID"] = "555"
        assert rank_for({"id": 1, "telegram_id": "555"}) == "elite"
        assert owner_tier("555") == "elite"           # the bot's path agrees now

        from app.autopilot import bot_autopilot
        reply = bot_autopilot([], chat_id="555", lang="en")
        assert "A-Team capability" not in reply and "gold-watch" in reply


def test_a_non_admin_still_needs_a_grant(app):
    with app.app_context():
        app.config["ADMIN_TELEGRAM_ID"] = "555"
        assert owner_tier("777") == "public"


# --- pointing the bot at a room --------------------------------------------- #

def test_only_a_team_may_point_the_bot_at_a_group(app):
    with app.app_context():
        assert groups.watch("-100123", "A room", "7")[1] == "gr.need"
        assert store.group_watchers("-100123") == []
        rows, err = _watch(app)
        assert not err and len(rows) == 1


def test_watchgroup_only_answers_inside_a_group(app):
    with app.app_context():
        store.grant_entitlement("7", "pro", source="manual")
        assert "inside the group" in groups.bot_watchgroup([], chat_id="7", lang="en")


def test_the_command_works_from_inside_the_room(app):
    """The confirmation is posted in the group on purpose.

    People in a room deserve to know a bot is reading what they write. It
    tips off a scammer who is paying attention, and that is the right trade."""
    with app.app_context():
        store.grant_entitlement("7", "pro", source="manual")
        actions = handle_update(_group_msg("/watchgroup"))
        assert len(actions) == 1
        assert actions[0][1] == -100123 and "Mengawasi" in actions[0][2]
        assert store.group_watchers("-100123")[0]["owner"] == "7"

        actions = handle_update(_group_msg("/unwatchgroup"))
        assert "Berhenti mengawasi" in actions[0][2]
        assert store.group_watchers("-100123") == []


def test_a_member_without_the_rank_is_told_so_in_the_group(app):
    with app.app_context():
        actions = handle_update(_group_msg("/watchgroup"))
        assert "A-Team" in actions[0][2]
        assert store.group_watchers("-100123") == []


# --- what it does with the messages ----------------------------------------- #

def test_a_pitch_reaches_the_watcher_and_chat_does_not(app):
    with app.app_context():
        _watch(app)
        actions = handle_update(_group_msg(CHAT, uid=9))
        assert actions == []                            # ordinary conversation is ignored

        actions = handle_update(_group_msg(PITCH, uid=9))
        assert len(actions) == 1
        who, body = actions[0][1], actions[0][2]
        assert who == "7"                               # the watcher, privately
        assert "Sam Flip Seribu" in body and "Untung dijamin" in body   # BM first


def test_it_never_posts_into_the_group(app):
    with app.app_context():
        _watch(app)
        actions = handle_update(_group_msg(PITCH, uid=9))
        assert all(str(a[1]) != "-100123" for a in actions)


def test_short_messages_are_never_scanned(app):
    with app.app_context():
        _watch(app)
        assert groups.inspect("-100123", "g", 9, "ada", "guaranteed 100% win", lambda *a: None) is None


def test_a_yellow_alone_does_not_wake_anyone(app):
    with app.app_context():
        _watch(app)
        soft = ("Our VIP room has limited slots this month and we are closing signups soon, "
                "so message me today if you want the monthly plan before the price changes.")
        assert groups.inspect("-100123", "g", 9, "ada", soft, lambda *a: None) is None


def test_one_alert_per_author_per_day(app):
    sent = []
    with app.app_context():
        _watch(app)
        assert groups.inspect("-100123", "g", 9, "ada", PITCH, lambda w, b: sent.append(b))
        assert groups.inspect("-100123", "g", 9, "ada", PITCH, lambda w, b: sent.append(b)) is None
        assert groups.inspect("-100123", "g", 11, "bob", PITCH, lambda w, b: sent.append(b))
    assert len(sent) == 2                               # a second spammer still gets through


def test_a_group_cannot_flood_the_watcher(app):
    sent = []
    with app.app_context():
        _watch(app)
        for i in range(groups.DAILY_PER_GROUP + 5):
            groups.inspect("-100123", "g", 100 + i, "spam%d" % i, PITCH, lambda w, b: sent.append(b))
    assert len(sent) == groups.DAILY_PER_GROUP


def test_a_lapsed_rank_stops_the_watching(app):
    with app.app_context():
        store.grant_entitlement("7", "pro", source="stripe", external_id="sub_x")
        groups.watch("-100123", "g", "7")
        assert groups.watchers("-100123")
        store.revoke_entitlement(external_id="sub_x")
        assert groups.watchers("-100123") == []
        assert groups.inspect("-100123", "g", 9, "ada", PITCH, lambda *a: None) is None
        assert store.group_watchers("-100123")          # the row survives, so it resumes


def test_the_hit_is_kept_as_a_scan_the_owner_can_review(app):
    with app.app_context():
        _watch(app)
        groups.inspect("-100123", "g", 9, "ada", PITCH, lambda *a: None)
        rows = store.scans_for("7", "red-flag-scanner")
        assert len(rows) == 1 and rows[0]["subject"] == "@ada"


def test_groups_lists_the_rooms_and_tells_you_how(app):
    with app.app_context():
        assert "A-Team" in groups.bot_groups([], chat_id="7", lang="en")
        store.grant_entitlement("7", "pro", source="manual")
        assert "make it an administrator" in groups.bot_groups([], chat_id="7", lang="en")
        groups.watch("-100123", "Sam Flip Seribu", "7")
        assert "Sam Flip Seribu" in groups.bot_groups([], chat_id="7", lang="en")
