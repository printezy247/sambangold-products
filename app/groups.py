"""Group auto-scan — the bot watches a room and flags the pitches in it.

The scanners already answer one pasted pitch perfectly. What a group lead
actually needs is not to paste anything: the scam arrives in their group at 2am
while they are asleep, and by morning three members have sent USDT to a wallet.

So an A-Team member adds the bot to their group as an administrator and runs
`/watchgroup`. Every message long enough to be a pitch goes through the same
rule engine the red-flag scanner uses, and anything that flags is sent to the
watcher privately, with the verdict and the reasons.

Three rules keep it from becoming the noise it is meant to catch:

* **A length floor.** Chat is not a pitch. Short messages are never scanned.
* **One alert per author per day per group.** A spammer posting the same thing
  twenty times costs the watcher one message, not twenty.
* **A daily cap per group.** A group that goes bad cannot flood the watcher.

The bot only ever reads groups it was deliberately pointed at, it never posts
into the group, and the scan happens in memory — only flagged messages are
stored, so an ordinary conversation leaves no trace.
"""

import time

from . import scan, store
from .brand import DEFAULT_LANG, t
from .gate import allows, owner_tier

FEATURE = "autoscan"
SLUG = "red-flag-scanner"      # hits are kept as scans of this product
MIN_CHARS = 90                 # below this it is conversation, not a pitch
DAILY_PER_GROUP = 12           # a group that goes bad cannot flood the watcher
QUIET_HOURS = 24               # one alert per author per group per day


def watchers(group_id):
    """Everyone watching this group whose rank still allows it."""
    rows = store.group_watchers(str(group_id))
    return [r for r in rows if allows(owner_tier(r["owner"]), FEATURE)]


def watch(group_id, title, owner, tier=None):
    """(rows, error_key). The member must hold the rank to point the bot at a room."""
    tier = tier or owner_tier(str(owner))
    if not allows(tier, FEATURE):
        return None, "gr.need"
    store.add_group_watch(str(group_id), title or "", str(owner))
    return store.group_watchers(str(group_id)), None


def unwatch(group_id, owner):
    store.drop_group_watch(str(group_id), str(owner))
    return store.groups_for(str(owner))


def _seen_key(group_id, author):
    return "seen:%s:%s" % (group_id, author)


def _recently_alerted(group_id, author, now):
    last = store.get_setting("group-watch", str(group_id), _seen_key(group_id, author))
    try:
        return last and float(last) > now - QUIET_HOURS * 3600
    except ValueError:
        return False


def _today_count(group_id, now):
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    raw = store.get_setting("group-watch", str(group_id), "count:" + day)
    return int(raw) if raw.isdigit() else 0


def _bump(group_id, author, now):
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    store.set_setting("group-watch", str(group_id), "count:" + day, str(_today_count(group_id, now) + 1))
    store.set_setting("group-watch", str(group_id), _seen_key(group_id, author), str(now))


def inspect(group_id, title, author, author_name, text, send, now=None):
    """Scan one group message. Returns the report when it alerted, else None.

    Never raises and never posts into the group: a watcher's DM is the only
    output, so a false positive costs one private message and nothing else.
    """
    now = time.time() if now is None else now
    if not text or len(text.strip()) < MIN_CHARS:
        return None
    people = watchers(group_id)
    if not people:
        return None
    if _today_count(group_id, now) >= DAILY_PER_GROUP:
        return None
    if _recently_alerted(group_id, author, now):
        return None

    report = scan.scan_pitch(text)
    if not report["reds"]:                 # a yellow alone is not worth waking someone
        return None

    report["subject"] = "@%s" % author_name if author_name else str(author)
    _bump(group_id, author, now)
    for row in people:
        lang = store.tg_lang(row["owner"]) or DEFAULT_LANG
        store.save_scan(report, owner=row["owner"])
        send(row["owner"], _alert(report, title or str(group_id), lang))
    return report


def _alert(report, title, lang):
    from .scantool import verdict_text
    lines = [t("gr.hit", lang, group=title, who=report["subject"],
               verdict=verdict_text(report["verdict"], lang), score=report["score"])]
    for f in scan.localise(report["findings"], lang)[:4]:   # BM first, like every other surface
        if f["flag"] == "red":
            lines.append(t("gr.red", lang, label=f["label"], why=f["why"]))
    lines.append("")
    lines.append(t("gr.quote", lang, text=report["text"][:220]))
    lines.append(t("gr.off", lang))
    return "\n".join(lines)


# --- bot -------------------------------------------------------------------- #

def bot_watchgroup(args, chat_id=None, lang=DEFAULT_LANG, group=None, author=None, **_):
    """`/watchgroup` inside a group points the bot at that room."""
    if not group:
        return t("gr.in_group", lang)
    owner = str(author or chat_id)
    tier = owner_tier(owner)
    if not allows(tier, FEATURE):
        from .gate import upgrade_line
        return "%s\n\n%s" % (upgrade_line(FEATURE, lang), t("gate.where", lang))
    _, err = watch(group["id"], group.get("title", ""), owner, tier=tier)
    if err:
        return t(err, lang)
    return t("gr.on", lang, group=group.get("title") or group["id"], min=MIN_CHARS, cap=DAILY_PER_GROUP)


def bot_unwatchgroup(args, chat_id=None, lang=DEFAULT_LANG, group=None, author=None, **_):
    owner = str(author or chat_id)
    if group:
        unwatch(group["id"], owner)
        return t("gr.off_ok", lang, group=group.get("title") or group["id"])
    rows = store.groups_for(owner)
    if args and args[0].strip():
        unwatch(args[0].strip(), owner)
        return t("gr.off_ok", lang, group=args[0].strip())
    if not rows:
        return t("gr.none", lang)
    return "\n".join([t("gr.list", lang)]
                     + ["• <b>%s</b> <code>%s</code>" % (r["title"] or "—", r["group_id"]) for r in rows]
                     + ["", t("gr.off_usage", lang)])


def bot_groups(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/groups` lists the rooms this member is watching."""
    if not chat_id:
        return t("gr.none", lang)
    if not allows(owner_tier(str(chat_id)), FEATURE):
        from .gate import upgrade_line
        return "%s\n\n%s" % (upgrade_line(FEATURE, lang), t("gate.where", lang))
    rows = store.groups_for(str(chat_id))
    if not rows:
        return "%s\n\n%s" % (t("gr.none", lang), t("gr.how", lang))
    return "\n".join([t("gr.list", lang)]
                     + ["• <b>%s</b> <code>%s</code>" % (r["title"] or "—", r["group_id"]) for r in rows])


# --- dashboard -------------------------------------------------------------- #

def dashboard_groups(request, user=None):
    owner = (user or {}).get("owner")
    tier = (user or {}).get("rank") or "public"
    ctx = {"allowed": allows(tier, FEATURE), "rows": [], "min": MIN_CHARS, "cap": DAILY_PER_GROUP}
    if not owner or not ctx["allowed"]:
        return ctx
    if request.method == "POST" and request.form.get("group_off"):
        unwatch(request.form["group_off"], owner)
    ctx["rows"] = store.groups_for(owner)
    return ctx
