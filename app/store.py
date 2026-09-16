"""SQLite persistence for anything a product must remember between requests.

Standard library only, one file under ``data/`` (gitignored), created on first
use. Free-tier hosts lose process memory on every restart; a file on a volume
does not. Tests point ``DATABASE_PATH`` at a temp file.
"""

import os
import sqlite3
import time

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    id         INTEGER PRIMARY KEY,
    owner      TEXT    NOT NULL,   -- Telegram user id; the same on both surfaces
    symbol     TEXT    NOT NULL,
    direction  TEXT    NOT NULL,   -- above | below
    level      REAL    NOT NULL,
    active     INTEGER NOT NULL DEFAULT 1,
    created_at REAL    NOT NULL
);
CREATE TABLE IF NOT EXISTS triggers (
    id       INTEGER PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id),
    owner    TEXT    NOT NULL,
    symbol   TEXT    NOT NULL,
    direction TEXT   NOT NULL,
    level    REAL    NOT NULL,
    price    REAL    NOT NULL,     -- the side that crossed: ask for above, bid for below
    spread   REAL,                 -- NULL when the source has no order book
    source   TEXT    NOT NULL,
    fired_at REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS alerts_owner ON alerts(owner, active);
CREATE INDEX IF NOT EXISTS triggers_owner ON triggers(owner, fired_at);
"""


def db():
    """One connection per request, schema applied on first open."""
    if "db" not in g:
        path = current_app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        _migrate(conn)
        g.db = conn
    return g.db


def _migrate(conn):
    """Columns added after a table first shipped. Each ALTER is a no-op once applied."""
    for table, column, ddl in (("tg_users", "state", "TEXT"), ("entitlements", "granted_by", "TEXT")):
        cols = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % table)]
        if column not in cols:
            conn.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, column, ddl))
    conn.commit()


def ready():
    """True where there is a database to read.

    The surface-contract test calls the bot's text functions with no app
    context: every product's base answer must come back without a read. The
    history we layer on top is the part that steps aside, not the answer.
    """
    from flask import has_app_context
    return has_app_context()


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


# --- alerts --------------------------------------------------------------- #

def add_alert(owner, symbol, direction, level):
    cur = db().execute(
        "INSERT INTO alerts (owner, symbol, direction, level, created_at) VALUES (?, ?, ?, ?, ?)",
        (str(owner), symbol, direction, float(level), time.time()),
    )
    db().commit()
    return cur.lastrowid


def alerts_for(owner, active_only=True):
    sql = "SELECT * FROM alerts WHERE owner = ?" + (" AND active = 1" if active_only else "")
    return [dict(r) for r in db().execute(sql + " ORDER BY id", (str(owner),))]


def active_alerts():
    return [dict(r) for r in db().execute("SELECT * FROM alerts WHERE active = 1 ORDER BY id")]


def update_alert(owner, alert_id, level=None, active=None):
    """Owner-scoped, so a user can only touch their own rows."""
    fields, values = [], []
    if level is not None:
        fields.append("level = ?"); values.append(float(level))
    if active is not None:
        fields.append("active = ?"); values.append(1 if active else 0)
    if not fields:
        return 0
    values += [int(alert_id), str(owner)]
    n = db().execute("UPDATE alerts SET %s WHERE id = ? AND owner = ?" % ", ".join(fields), values).rowcount
    db().commit()
    return n


def clear_alerts(owner):
    n = db().execute("UPDATE alerts SET active = 0 WHERE owner = ? AND active = 1", (str(owner),)).rowcount
    db().commit()
    return n


# --- triggers ------------------------------------------------------------- #

def record_trigger(alert, quote):
    price = quote["ask"] if alert["direction"] == "above" else quote["bid"]
    db().execute(
        "INSERT INTO triggers (alert_id, owner, symbol, direction, level, price, spread, source, fired_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (alert["id"], alert["owner"], alert["symbol"], alert["direction"], alert["level"],
         price, quote["spread"], quote["source"], time.time()),
    )
    db().execute("UPDATE alerts SET active = 0 WHERE id = ?", (alert["id"],))
    db().commit()
    return price


def triggers_for(owner, limit=200):
    return [dict(r) for r in db().execute(
        "SELECT * FROM triggers WHERE owner = ? ORDER BY fired_at DESC LIMIT ?", (str(owner), limit))]


# --------------------------------------------------------------------------- #
# Accounts: one row per person, reachable by Telegram id and/or email.
# --------------------------------------------------------------------------- #

ACCOUNT_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    email         TEXT UNIQUE,
    telegram_id   TEXT UNIQUE,
    username      TEXT,
    name          TEXT,
    locale        TEXT NOT NULL DEFAULT 'ms',
    created_at    REAL NOT NULL,
    verified_at   REAL,
    last_login_at REAL
);
CREATE TABLE IF NOT EXISTS email_codes (
    id         INTEGER PRIMARY KEY,
    email      TEXT    NOT NULL,
    code_hash  TEXT    NOT NULL,
    attempts   INTEGER NOT NULL DEFAULT 0,
    created_at REAL    NOT NULL,
    expires_at REAL    NOT NULL,
    used_at    REAL
);
CREATE INDEX IF NOT EXISTS email_codes_email ON email_codes(email, created_at);
CREATE TABLE IF NOT EXISTS tg_users (
    telegram_id TEXT PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    lang        TEXT,
    tag         TEXT,
    starts      INTEGER NOT NULL DEFAULT 0,
    first_seen  REAL NOT NULL,
    last_seen   REAL NOT NULL
);
"""
SCHEMA += ACCOUNT_SCHEMA


def _row(cur):
    r = cur.fetchone()
    return dict(r) if r else None


def user_by_id(user_id):
    return _row(db().execute("SELECT * FROM users WHERE id = ?", (int(user_id),)))


def user_by_telegram(telegram_id):
    return _row(db().execute("SELECT * FROM users WHERE telegram_id = ?", (str(telegram_id),)))


def user_by_email(email):
    return _row(db().execute("SELECT * FROM users WHERE email = ?", (email.lower(),)))


def upsert_telegram_user(telegram_id, username="", name="", locale=None, link_to=None):
    """Sign-in via Telegram. `link_to` attaches the Telegram id to an existing
    (email) account instead of creating a second one."""
    now = time.time()
    existing = user_by_telegram(telegram_id)
    if existing:
        db().execute("UPDATE users SET username = ?, name = COALESCE(NULLIF(?, ''), name), last_login_at = ? WHERE id = ?",
                     (username, name, now, existing["id"]))
        db().commit()
        return user_by_id(existing["id"])
    if link_to:
        db().execute("UPDATE users SET telegram_id = ?, username = ?, name = COALESCE(NULLIF(name, ''), ?), last_login_at = ? WHERE id = ?",
                     (str(telegram_id), username, name, now, int(link_to)))
        db().commit()
        _migrate_owner("u:%d" % int(link_to), str(telegram_id))
        return user_by_id(link_to)
    cur = db().execute(
        "INSERT INTO users (telegram_id, username, name, locale, created_at, verified_at, last_login_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(telegram_id), username, name, locale or "ms", now, now, now))
    db().commit()
    return user_by_id(cur.lastrowid)


def upsert_email_user(email, locale=None, link_to=None):
    """Sign-in via a verified email code. `link_to` attaches the email to the
    current (Telegram) account."""
    email = email.lower()
    now = time.time()
    existing = user_by_email(email)
    if existing:
        db().execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now, existing["id"]))
        db().commit()
        return user_by_id(existing["id"])
    if link_to:
        db().execute("UPDATE users SET email = ?, last_login_at = ? WHERE id = ?", (email, now, int(link_to)))
        db().commit()
        return user_by_id(link_to)
    cur = db().execute(
        "INSERT INTO users (email, locale, created_at, verified_at, last_login_at) VALUES (?, ?, ?, ?, ?)",
        (email, locale or "ms", now, now, now))
    db().commit()
    return user_by_id(cur.lastrowid)


def set_user_locale(user_id, locale):
    db().execute("UPDATE users SET locale = ? WHERE id = ?", (locale, int(user_id)))
    db().commit()


def owner_key(user):
    """Alerts and history are keyed by Telegram id when there is one, so the bot
    and the dashboard share a list; email-only accounts use their row id."""
    return user["telegram_id"] if user.get("telegram_id") else "u:%d" % user["id"]


def _migrate_owner(old, new):
    for table in ("alerts", "triggers"):
        db().execute("UPDATE %s SET owner = ? WHERE owner = ?" % table, (new, old))
    db().commit()


def list_users(limit=500):
    return [dict(r) for r in db().execute("SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,))]


def user_counts():
    q = db().execute
    return {
        "users": q("SELECT COUNT(*) FROM users").fetchone()[0],
        "emails": q("SELECT COUNT(*) FROM users WHERE email IS NOT NULL").fetchone()[0],
        "telegrams": q("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL").fetchone()[0],
        "starts": q("SELECT COALESCE(SUM(starts), 0) FROM tg_users").fetchone()[0],
    }


# --- email codes ---------------------------------------------------------- #

def _hash_code(email, code):
    import hashlib
    return hashlib.sha256(("%s:%s" % (email.lower(), code)).encode()).hexdigest()


def issue_code(email, ttl, resend_after):
    """Create a fresh 8-digit code. Returns (code, None) or (None, 'cooldown')."""
    import secrets
    email = email.lower()
    now = time.time()
    last = db().execute("SELECT created_at FROM email_codes WHERE email = ? ORDER BY created_at DESC LIMIT 1", (email,)).fetchone()
    if last and now - last[0] < resend_after:
        return None, "cooldown"
    code = "%08d" % secrets.randbelow(10 ** 8)
    db().execute("UPDATE email_codes SET used_at = ? WHERE email = ? AND used_at IS NULL", (now, email))
    db().execute("INSERT INTO email_codes (email, code_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
                 (email, _hash_code(email, code), now, now + ttl))
    db().commit()
    return code, None


def verify_code(email, code, max_attempts):
    """'ok' | 'wrong' | 'expired' | 'too_many'. A used or expired code never matches."""
    import hmac
    email = email.lower()
    now = time.time()
    row = _row(db().execute("SELECT * FROM email_codes WHERE email = ? AND used_at IS NULL ORDER BY created_at DESC LIMIT 1", (email,)))
    if row is None or row["expires_at"] < now:
        return "expired"
    if row["attempts"] >= max_attempts:
        return "too_many"
    db().execute("UPDATE email_codes SET attempts = attempts + 1 WHERE id = ?", (row["id"],))
    db().commit()
    if hmac.compare_digest(row["code_hash"], _hash_code(email, (code or "").strip())):
        db().execute("UPDATE email_codes SET used_at = ? WHERE id = ?", (now, row["id"]))
        db().commit()
        return "ok"
    return "wrong"


# --- bot users: language, attribution -------------------------------------- #

def tg_touch(telegram_id, username="", first_name="", tag=None, start=False):
    now = time.time()
    row = _row(db().execute("SELECT * FROM tg_users WHERE telegram_id = ?", (str(telegram_id),)))
    if row is None:
        db().execute("INSERT INTO tg_users (telegram_id, username, first_name, tag, starts, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (str(telegram_id), username, first_name, tag, 1 if start else 0, now, now))
    else:
        db().execute("UPDATE tg_users SET username = ?, first_name = ?, last_seen = ?, starts = starts + ?, tag = COALESCE(?, tag) WHERE telegram_id = ?",
                     (username, first_name, now, 1 if start else 0, tag, str(telegram_id)))
    db().commit()
    return _row(db().execute("SELECT * FROM tg_users WHERE telegram_id = ?", (str(telegram_id),)))


def tg_lang(telegram_id):
    row = _row(db().execute("SELECT lang FROM tg_users WHERE telegram_id = ?", (str(telegram_id),)))
    return row["lang"] if row else None


def tg_state(telegram_id):
    """The guided-flow state for this chat (a dict), or None."""
    import json
    row = _row(db().execute("SELECT state FROM tg_users WHERE telegram_id = ?", (str(telegram_id),)))
    return json.loads(row["state"]) if row and row["state"] else None


def tg_set_state(telegram_id, state):
    import json
    db().execute("UPDATE tg_users SET state = ? WHERE telegram_id = ?",
                 (json.dumps(state) if state else None, str(telegram_id)))
    db().commit()


def tg_set_lang(telegram_id, lang):
    db().execute("UPDATE tg_users SET lang = ? WHERE telegram_id = ?", (lang, str(telegram_id)))
    db().execute("UPDATE users SET locale = ? WHERE telegram_id = ?", (lang, str(telegram_id)))
    db().commit()


# --------------------------------------------------------------------------- #
# #5 Gold Calendar: alert subscriptions, dedup, and the measured spread log.
# --------------------------------------------------------------------------- #

CALENDAR_SCHEMA = """
CREATE TABLE IF NOT EXISTS calendar_subs (
    owner      TEXT PRIMARY KEY,
    active     INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS calendar_sent (
    event_key TEXT NOT NULL,
    owner     TEXT NOT NULL,
    sent_at   REAL NOT NULL,
    PRIMARY KEY (event_key, owner)
);
CREATE TABLE IF NOT EXISTS spread_log (
    ts     REAL PRIMARY KEY,
    bid    REAL NOT NULL,
    ask    REAL NOT NULL,
    spread REAL,
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_spreads (
    title    TEXT NOT NULL,
    event_at REAL NOT NULL,
    ts       REAL NOT NULL,
    spread   REAL,
    PRIMARY KEY (title, event_at, ts)
);
"""
SCHEMA += CALENDAR_SCHEMA


def calendar_toggle(owner, active=None):
    """Flip (or set) the 30-minute-before subscription. Returns the new state."""
    row = _row(db().execute("SELECT active FROM calendar_subs WHERE owner = ?", (str(owner),)))
    new = (not row["active"]) if (active is None and row) else (True if active is None else bool(active))
    db().execute("INSERT INTO calendar_subs (owner, active, created_at) VALUES (?, ?, ?)"
                 " ON CONFLICT(owner) DO UPDATE SET active = excluded.active",
                 (str(owner), 1 if new else 0, time.time()))
    db().commit()
    return new


def calendar_subscribed(owner):
    row = _row(db().execute("SELECT active FROM calendar_subs WHERE owner = ?", (str(owner),)))
    return bool(row and row["active"])


def calendar_subscribers():
    return [r["owner"] for r in db().execute("SELECT owner FROM calendar_subs WHERE active = 1")]


def calendar_mark_sent(event_key, owner):
    """True the first time; False if this owner already got this event."""
    try:
        db().execute("INSERT INTO calendar_sent (event_key, owner, sent_at) VALUES (?, ?, ?)",
                     (event_key, str(owner), time.time()))
        db().commit()
        return True
    except Exception:  # noqa: BLE001 — primary-key clash means already sent
        return False


def log_spread(quote, event=None):
    """One sample per checker run; tagged with the red event it sits inside, if any."""
    now = time.time()
    db().execute("INSERT OR REPLACE INTO spread_log (ts, bid, ask, spread, source) VALUES (?, ?, ?, ?, ?)",
                 (now, quote["bid"], quote["ask"], quote["spread"], quote["source"]))
    db().execute("DELETE FROM spread_log WHERE ts < ?", (now - 30 * 86400,))
    if event is not None:
        db().execute("INSERT OR REPLACE INTO event_spreads (title, event_at, ts, spread) VALUES (?, ?, ?, ?)",
                     (event["title"], event["at"].timestamp(), now, quote["spread"]))
    db().commit()


def spread_samples(days=30):
    """Every logged spread in the window — when it was taken, and how wide it was."""
    return [(r[0], r[1]) for r in db().execute(
        "SELECT ts, spread FROM spread_log WHERE spread IS NOT NULL AND ts > ? ORDER BY ts",
        (time.time() - days * 86400,))]


def baseline_spread():
    rows = [r[0] for r in db().execute("SELECT spread FROM spread_log WHERE spread IS NOT NULL")]
    if not rows:
        return None
    rows.sort()
    return rows[len(rows) // 2]


def event_samples(title, occurrences=6):
    """Every logged spread around the most recent occurrences of one event."""
    ats = [r[0] for r in db().execute(
        "SELECT DISTINCT event_at FROM event_spreads WHERE title = ? ORDER BY event_at DESC LIMIT ?",
        (title, occurrences))]
    if not ats:
        return []
    marks = ",".join("?" * len(ats))
    return [dict(r) for r in db().execute(
        "SELECT event_at, ts, spread FROM event_spreads WHERE title = ? AND spread IS NOT NULL"
        " AND event_at IN (%s) ORDER BY event_at, ts" % marks, [title] + ats)]


def event_titles(limit=12):
    """Event titles we have measured, most-measured first."""
    return [r[0] for r in db().execute(
        "SELECT title FROM event_spreads WHERE spread IS NOT NULL GROUP BY title"
        " ORDER BY COUNT(DISTINCT event_at) DESC, MAX(event_at) DESC LIMIT ?", (limit,))]


def event_spread_history(limit=12):
    """Per event title: how many past occurrences were measured and the worst spread seen."""
    return [dict(r) for r in db().execute(
        "SELECT title, COUNT(DISTINCT event_at) AS occurrences, MAX(spread) AS worst, AVG(spread) AS mean"
        " FROM event_spreads WHERE spread IS NOT NULL GROUP BY title ORDER BY occurrences DESC, worst DESC LIMIT ?",
        (limit,))]


# --------------------------------------------------------------------------- #
# Scanners (#4 #6 #7 #9): one archive for every report.
# --------------------------------------------------------------------------- #

SCAN_SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id         INTEGER PRIMARY KEY,
    product    TEXT NOT NULL,
    subject    TEXT NOT NULL,
    owner      TEXT,
    score      INTEGER NOT NULL,
    verdict    TEXT NOT NULL,
    report     TEXT NOT NULL,     -- JSON of the full report
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS scans_owner ON scans(owner, product, created_at);
CREATE INDEX IF NOT EXISTS scans_subject ON scans(product, subject);
"""
SCHEMA += SCAN_SCHEMA


def save_scan(report, owner=None):
    import json
    cur = db().execute(
        "INSERT INTO scans (product, subject, owner, score, verdict, report, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (report["product"], report["subject"], str(owner) if owner else None, report["score"], report["verdict"],
         json.dumps(report, default=str), time.time()))
    db().commit()
    return cur.lastrowid


def get_scan(scan_id):
    import json
    row = _row(db().execute("SELECT * FROM scans WHERE id = ?", (int(scan_id),)))
    if row:
        row["report"] = json.loads(row["report"])
    return row


def scans_for(owner, product, limit=50):
    return [dict(r) for r in db().execute(
        "SELECT id, subject, score, verdict, created_at FROM scans WHERE owner = ? AND product = ? ORDER BY created_at DESC LIMIT ?",
        (str(owner), product, limit))]


def watchlist(owner, product):
    """Distinct subjects this owner has scanned, with their latest score."""
    return [dict(r) for r in db().execute(
        "SELECT subject, MAX(created_at) AS last_at, COUNT(*) AS n,"
        " (SELECT score FROM scans s2 WHERE s2.owner = s.owner AND s2.product = s.product AND s2.subject = s.subject ORDER BY created_at DESC LIMIT 1) AS score"
        " FROM scans s WHERE owner = ? AND product = ? GROUP BY subject ORDER BY last_at DESC LIMIT 30",
        (str(owner), product))]


def register_rows(products, subject=None, limit=60):
    """Every subject these products have scanned, across all owners.

    Grouped case-insensitively, because "@Gold_Guru" and "@gold_guru" are one
    person. `days` counts distinct calendar days rather than raw scans: it is
    what stops one person hammering the same name from looking like a crowd.
    """
    marks = ",".join("?" * len(products))
    where = "product IN (%s)" % marks
    args = list(products)
    if subject:
        where += " AND LOWER(subject) = ?"
        args.append(subject.strip().lower())
    args.append(int(limit))
    return [dict(r) for r in db().execute(
        "SELECT LOWER(subject) AS key, MIN(subject) AS subject, product,"
        " COUNT(*) AS n, COUNT(DISTINCT CAST(created_at / 86400 AS INTEGER)) AS days,"
        " MAX(score) AS worst, MIN(created_at) AS first_at, MAX(created_at) AS last_at,"
        " SUM(CASE WHEN verdict != 'clear' THEN 1 ELSE 0 END) AS flagged"
        " FROM scans WHERE %s AND subject != '' GROUP BY key"
        " ORDER BY last_at DESC LIMIT ?" % where, args)]


def public_scans(product, subject, limit=10):
    return [dict(r) for r in db().execute(
        "SELECT id, score, verdict, created_at FROM scans WHERE product = ? AND subject = ? ORDER BY created_at DESC LIMIT ?",
        (product, subject, limit))]


# --------------------------------------------------------------------------- #
# #10 Rebate auditor: one row per reconciliation run.
# --------------------------------------------------------------------------- #

REBATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS rebate_runs (
    id         INTEGER PRIMARY KEY,
    owner      TEXT,
    broker     TEXT,
    period     TEXT,
    shortfall  REAL NOT NULL,
    run        TEXT NOT NULL,     -- JSON: rate card, summary, findings
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS rebate_owner ON rebate_runs(owner, created_at);
"""
SCHEMA += REBATE_SCHEMA


def save_rebate_run(run, owner=None):
    import json
    cur = db().execute(
        "INSERT INTO rebate_runs (owner, broker, period, shortfall, run, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (str(owner) if owner else None, run.get("broker") or "", run.get("period") or "",
         run["summary"]["shortfall"], json.dumps(run, default=str), time.time()))
    db().commit()
    return cur.lastrowid


def get_rebate_run(run_id):
    import json
    row = _row(db().execute("SELECT * FROM rebate_runs WHERE id = ?", (int(run_id),)))
    if row:
        row["run"] = json.loads(row["run"])
    return row


def rebate_runs_for(owner, limit=20):
    return [dict(r) for r in db().execute(
        "SELECT id, broker, period, shortfall, created_at FROM rebate_runs WHERE owner = ? ORDER BY created_at DESC LIMIT ?",
        (str(owner), limit))]


def last_rebate_run(owner):
    row = _row(db().execute("SELECT id FROM rebate_runs WHERE owner = ? ORDER BY created_at DESC LIMIT 1", (str(owner),)))
    return get_rebate_run(row["id"]) if row else None


# --------------------------------------------------------------------------- #
# Generic archive for dashboard-led tools (#11 onwards): one row per run,
# plus free-text notes keyed by product + subject (the intervention log).
# --------------------------------------------------------------------------- #

RUNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_runs (
    id         INTEGER PRIMARY KEY,
    product    TEXT NOT NULL,
    owner      TEXT,
    label      TEXT,
    metric     REAL,
    run        TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS tool_runs_owner ON tool_runs(product, owner, created_at);
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY,
    product    TEXT NOT NULL,
    owner      TEXT NOT NULL,
    subject    TEXT NOT NULL,
    note       TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_owner ON notes(product, owner, subject, created_at);
"""
SCHEMA += RUNS_SCHEMA


def save_run(product, run, owner=None, label="", metric=None):
    import json
    cur = db().execute("INSERT INTO tool_runs (product, owner, label, metric, run, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (product, str(owner) if owner else None, label, metric, json.dumps(run, default=str), time.time()))
    db().commit()
    return cur.lastrowid


def get_run(run_id):
    import json
    row = _row(db().execute("SELECT * FROM tool_runs WHERE id = ?", (int(run_id),)))
    if row:
        row["run"] = json.loads(row["run"])
    return row


def runs_for(product, owner, limit=20):
    return [dict(r) for r in db().execute(
        "SELECT id, label, metric, created_at FROM tool_runs WHERE product = ? AND owner = ? ORDER BY created_at DESC LIMIT ?",
        (product, str(owner), limit))]


def last_run(product, owner):
    row = _row(db().execute("SELECT id FROM tool_runs WHERE product = ? AND owner = ? ORDER BY created_at DESC LIMIT 1",
                            (product, str(owner))))
    return get_run(row["id"]) if row else None


def add_note(product, owner, subject, note):
    db().execute("INSERT INTO notes (product, owner, subject, note, created_at) VALUES (?, ?, ?, ?, ?)",
                 (product, str(owner), subject, note.strip(), time.time()))
    db().commit()


def notes_for(product, owner, subject=None, limit=50):
    if subject is None:
        return [dict(r) for r in db().execute(
            "SELECT subject, note, created_at FROM notes WHERE product = ? AND owner = ? ORDER BY created_at DESC LIMIT ?",
            (product, str(owner), limit))]
    return [dict(r) for r in db().execute(
        "SELECT subject, note, created_at FROM notes WHERE product = ? AND owner = ? AND subject = ? ORDER BY created_at DESC LIMIT ?",
        (product, str(owner), subject, limit))]


# --------------------------------------------------------------------------- #
# #12 Broker comparator: what users measured on their own platform.
# --------------------------------------------------------------------------- #

OBS_SCHEMA = """
CREATE TABLE IF NOT EXISTS spread_obs (
    id         INTEGER PRIMARY KEY,
    owner      TEXT NOT NULL,
    broker     TEXT NOT NULL,
    spread     REAL NOT NULL,
    slippage   REAL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS spread_obs_broker ON spread_obs(broker, created_at);
"""
SCHEMA += OBS_SCHEMA


def add_observation(owner, broker, spread, slippage=None):
    db().execute("INSERT INTO spread_obs (owner, broker, spread, slippage, created_at) VALUES (?, ?, ?, ?, ?)",
                 (str(owner), broker, float(spread), float(slippage) if slippage not in (None, "") else None, time.time()))
    db().commit()


def observations(days=30):
    return [dict(r) for r in db().execute(
        "SELECT broker, spread, slippage, owner, created_at FROM spread_obs WHERE created_at > ? ORDER BY created_at DESC",
        (time.time() - days * 86400,))]


def set_setting(product, owner, key, value):
    db().execute("DELETE FROM notes WHERE product = ? AND owner = ? AND subject = ?", (product, str(owner), "setting:" + key))
    if value:
        db().execute("INSERT INTO notes (product, owner, subject, note, created_at) VALUES (?, ?, ?, ?, ?)",
                     (product, str(owner), "setting:" + key, value.strip(), time.time()))
    db().commit()


def get_setting(product, owner, key):
    row = _row(db().execute("SELECT note FROM notes WHERE product = ? AND owner = ? AND subject = ? ORDER BY created_at DESC LIMIT 1",
                            (product, str(owner), "setting:" + key)))
    return row["note"] if row else ""


def owners_by_setting(product, key, value):
    rows = db().execute("SELECT DISTINCT owner FROM notes WHERE product = ? AND subject = ? AND note = ?", (product, "setting:" + key, value)).fetchall()
    return [r["owner"] for r in rows]


def owner_by_setting(product, key, value):
    row = _row(db().execute("SELECT owner FROM notes WHERE product = ? AND subject = ? AND note = ? ORDER BY created_at DESC LIMIT 1",
                            (product, "setting:" + key, value)))
    return row["owner"] if row else None


# --------------------------------------------------------------------------- #
# #13 Link attribution: short links and the stage events behind them.
# --------------------------------------------------------------------------- #

LINKS_SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    id         INTEGER PRIMARY KEY,
    owner      TEXT NOT NULL,
    code       TEXT NOT NULL UNIQUE,
    channel    TEXT NOT NULL,
    url        TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS link_events (
    id         INTEGER PRIMARY KEY,
    link_id    INTEGER NOT NULL,
    stage      TEXT NOT NULL,
    count      INTEGER NOT NULL DEFAULT 1,
    note       TEXT,
    at         REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS link_events_link ON link_events(link_id, at);
"""
SCHEMA += LINKS_SCHEMA


def add_link(owner, code, channel, url):
    cur = db().execute("INSERT INTO links (owner, code, channel, url, created_at) VALUES (?, ?, ?, ?, ?)",
                       (str(owner), code, channel.strip(), url.strip(), time.time()))
    db().commit()
    return cur.lastrowid


def links_for(owner):
    return [dict(r) for r in db().execute("SELECT * FROM links WHERE owner = ? ORDER BY created_at DESC", (str(owner),))]


def link_by_code(code):
    return _row(db().execute("SELECT * FROM links WHERE code = ?", (code,)))


def link_by_channel(owner, channel):
    return _row(db().execute("SELECT * FROM links WHERE owner = ? AND lower(channel) = lower(?) ORDER BY created_at DESC LIMIT 1",
                             (str(owner), channel.strip())))


def delete_link(owner, link_id):
    db().execute("DELETE FROM link_events WHERE link_id IN (SELECT id FROM links WHERE id = ? AND owner = ?)", (int(link_id), str(owner)))
    n = db().execute("DELETE FROM links WHERE id = ? AND owner = ?", (int(link_id), str(owner))).rowcount
    db().commit()
    return n


def add_link_event(link_id, stage, count=1, note=None, at=None):
    db().execute("INSERT INTO link_events (link_id, stage, count, note, at) VALUES (?, ?, ?, ?, ?)",
                 (int(link_id), stage, int(count), note, at or time.time()))
    db().commit()


def link_events_for(owner, since_ts=0.0):
    return [dict(r) for r in db().execute(
        "SELECT e.link_id, e.stage, e.count, e.at FROM link_events e JOIN links l ON l.id = e.link_id"
        " WHERE l.owner = ? AND e.at >= ?", (str(owner), since_ts))]


# --------------------------------------------------------------------------- #
# #14 Drawdown sentinel: linked accounts (self-reported equity) and their log.
# --------------------------------------------------------------------------- #

SENTINEL_SCHEMA = """
CREATE TABLE IF NOT EXISTS sentinel_accounts (
    id                INTEGER PRIMARY KEY,
    owner             TEXT NOT NULL,
    name              TEXT NOT NULL,
    firm              TEXT NOT NULL,
    pack              TEXT NOT NULL,       -- JSON rule pack
    token             TEXT NOT NULL UNIQUE,
    initial_balance   REAL NOT NULL,
    day_start_balance REAL NOT NULL,
    day               TEXT NOT NULL,
    equity            REAL NOT NULL,
    peak_equity       REAL NOT NULL,
    open_lots         REAL NOT NULL DEFAULT 0,
    started           TEXT NOT NULL,
    last_state        TEXT NOT NULL DEFAULT 'ok',
    updated_at        REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sentinel_log (
    id         INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    at         REAL NOT NULL,
    equity     REAL NOT NULL,
    state      TEXT NOT NULL,
    note       TEXT
);
CREATE INDEX IF NOT EXISTS sentinel_log_acc ON sentinel_log(account_id, at);
"""
SCHEMA += SENTINEL_SCHEMA


def add_sentinel(owner, name, firm, pack, token, balance, today):
    import json
    cur = db().execute(
        "INSERT INTO sentinel_accounts (owner, name, firm, pack, token, initial_balance, day_start_balance, day, equity, peak_equity, open_lots, started, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
        (str(owner), name, firm, json.dumps(pack), token, float(balance), float(balance), today, float(balance), float(balance), today, time.time()))
    db().commit()
    return cur.lastrowid


def _sentinel_row(row):
    import json
    if row:
        row["pack"] = json.loads(row["pack"])
    return row


def sentinels_for(owner):
    return [_sentinel_row(dict(r)) for r in db().execute("SELECT * FROM sentinel_accounts WHERE owner = ? ORDER BY id", (str(owner),))]


def sentinel_by_token(token):
    return _sentinel_row(_row(db().execute("SELECT * FROM sentinel_accounts WHERE token = ?", (token,))))


def sentinel_get(owner, account_id):
    return _sentinel_row(_row(db().execute("SELECT * FROM sentinel_accounts WHERE id = ? AND owner = ?", (int(account_id), str(owner)))))


def sentinel_update(account_id, **fields):
    import json
    if "pack" in fields:
        fields["pack"] = json.dumps(fields["pack"])
    fields["updated_at"] = time.time()
    cols = ", ".join("%s = ?" % k for k in fields)
    db().execute("UPDATE sentinel_accounts SET %s WHERE id = ?" % cols, (*fields.values(), int(account_id)))
    db().commit()


def sentinel_delete(owner, account_id):
    db().execute("DELETE FROM sentinel_log WHERE account_id IN (SELECT id FROM sentinel_accounts WHERE id = ? AND owner = ?)", (int(account_id), str(owner)))
    n = db().execute("DELETE FROM sentinel_accounts WHERE id = ? AND owner = ?", (int(account_id), str(owner))).rowcount
    db().commit()
    return n


def sentinel_log(account_id, equity, state, note=None):
    db().execute("INSERT INTO sentinel_log (account_id, at, equity, state, note) VALUES (?, ?, ?, ?, ?)",
                 (int(account_id), time.time(), float(equity), state, note))
    db().commit()


def sentinel_history(account_id, limit=30):
    return [dict(r) for r in db().execute("SELECT at, equity, state, note FROM sentinel_log WHERE account_id = ? ORDER BY at DESC LIMIT ?",
                                          (int(account_id), limit))]


# --------------------------------------------------------------------------- #
# #17 Tokenized gold: the premium sampled by the five-minute checker.
# --------------------------------------------------------------------------- #

PREMIUM_SCHEMA = """
CREATE TABLE IF NOT EXISTS premium_log (
    id   INTEGER PRIMARY KEY,
    at   REAL NOT NULL,
    paxg REAL, xaut REAL, spot REAL, usdt REAL
);
CREATE INDEX IF NOT EXISTS premium_log_at ON premium_log(at);
"""
SCHEMA += PREMIUM_SCHEMA


def log_premium(paxg, xaut, spot, usdt):
    db().execute("INSERT INTO premium_log (at, paxg, xaut, spot, usdt) VALUES (?, ?, ?, ?, ?)", (time.time(), paxg, xaut, spot, usdt))
    db().commit()


def premium_series(days=30, limit=4000):
    """The premium samples for the band — newest first under the cap, then put
    back in order. `premium_history` takes the oldest, which is right for a
    chart and wrong for a range that is meant to describe now."""
    rows = [dict(r) for r in db().execute(
        "SELECT at, paxg, xaut, spot, usdt FROM premium_log WHERE at > ? ORDER BY at DESC LIMIT ?",
        (time.time() - days * 86400, limit))]
    return list(reversed(rows))


def premium_history(days=7, limit=2500):
    return [dict(r) for r in db().execute("SELECT at, paxg, xaut, spot, usdt FROM premium_log WHERE at > ? ORDER BY at LIMIT ?",
                                          (time.time() - days * 86400, limit))]


# --------------------------------------------------------------------------- #
# Ranks: entitlements. Ported from website_sam src/lib/entitlements.ts so the
# two properties grant the same way — idempotent on external_id, effective
# rank is the highest active grant.
# --------------------------------------------------------------------------- #

ENTITLEMENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS entitlements (
    id          INTEGER PRIMARY KEY,
    owner       TEXT NOT NULL,
    tier_key    TEXT NOT NULL,
    source      TEXT NOT NULL,            -- ib | stripe | crypto | manual | seat
    external_id TEXT UNIQUE,              -- stripe sub id / invoice id / ib account id / seat key
    granted_by  TEXT,                     -- the member whose rank pays for this seat
    note        TEXT,
    starts_at   REAL NOT NULL,
    expires_at  REAL,
    status      TEXT NOT NULL DEFAULT 'active',   -- active | expired | cancelled
    created_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS entitlements_owner ON entitlements(owner, status);
"""
SCHEMA += ENTITLEMENT_SCHEMA


def grant_entitlement(owner, tier_key, source="manual", external_id=None, expires_at=None, note="", granted_by=None):
    """Grant a rank. Re-running with the same external_id updates instead of duplicating."""
    now = time.time()
    row = (str(owner), tier_key, source, external_id, note, now, expires_at, "active", now,
           str(granted_by) if granted_by else None)
    cols = ("INSERT INTO entitlements (owner, tier_key, source, external_id, note, starts_at, expires_at, status,"
            " created_at, granted_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
    if external_id:
        db().execute(cols + " ON CONFLICT(external_id) DO UPDATE SET tier_key = excluded.tier_key,"
                            " expires_at = excluded.expires_at, note = excluded.note, status = 'active'", row)
    else:
        db().execute(cols, row)
    db().commit()
    return entitlements_for(owner)


def revoke_entitlement(entitlement_id=None, external_id=None, status="cancelled"):
    if external_id:
        db().execute("UPDATE entitlements SET status = ? WHERE external_id = ?", (status, external_id))
    elif entitlement_id is not None:
        db().execute("UPDATE entitlements SET status = ? WHERE id = ?", (status, int(entitlement_id)))
    db().commit()


def entitlements_for(owner, active_only=True):
    sql = "SELECT * FROM entitlements WHERE owner = ?"
    args = [str(owner)]
    if active_only:
        sql += " AND status = 'active' AND (expires_at IS NULL OR expires_at > ?)"
        args.append(time.time())
    return [dict(r) for r in db().execute(sql + " ORDER BY created_at DESC", args)]


def effective_tier(owner, default="public"):
    """The highest rank the owner holds right now."""
    from .tiers import higher_tier
    best = default
    for row in entitlements_for(owner):
        best = higher_tier(best, row["tier_key"])
    return best


def seats_granted_by(owner, active_only=True):
    """The seats this member is paying for."""
    sql = "SELECT * FROM entitlements WHERE granted_by = ? AND source = 'seat'"
    args = [str(owner)]
    if active_only:
        sql += " AND status = 'active' AND (expires_at IS NULL OR expires_at > ?)"
        args.append(time.time())
    return [dict(r) for r in db().execute(sql + " ORDER BY created_at", args)]


def all_entitlements(limit=500):
    return [dict(r) for r in db().execute("SELECT * FROM entitlements ORDER BY created_at DESC LIMIT ?", (limit,))]


def expire_due(now=None):
    """Mark lapsed grants expired. Cheap enough to call from the five-minute checker."""
    now = time.time() if now is None else now
    cur = db().execute("UPDATE entitlements SET status = 'expired' WHERE status = 'active' AND expires_at IS NOT NULL AND expires_at <= ?", (now,))
    db().commit()
    return cur.rowcount


# --------------------------------------------------------------------------- #
# The broker door: an HFM account waiting to be verified, then a rank.
# --------------------------------------------------------------------------- #

BROKER_SCHEMA = """
CREATE TABLE IF NOT EXISTS broker_claims (
    id          INTEGER PRIMARY KEY,
    owner       TEXT NOT NULL,
    account     TEXT NOT NULL UNIQUE,
    deposit     REAL,
    status      TEXT NOT NULL DEFAULT 'pending',   -- pending | verified | rejected
    note        TEXT,
    created_at  REAL NOT NULL,
    verified_at REAL
);
CREATE INDEX IF NOT EXISTS broker_claims_owner ON broker_claims(owner, status);
"""
SCHEMA += BROKER_SCHEMA


def save_broker_claim(owner, account, deposit=None, note=""):
    db().execute(
        "INSERT INTO broker_claims (owner, account, deposit, status, note, created_at) VALUES (?, ?, ?, 'pending', ?, ?)"
        " ON CONFLICT(account) DO UPDATE SET owner = excluded.owner, deposit = COALESCE(excluded.deposit, broker_claims.deposit),"
        " note = excluded.note, status = 'pending'",
        (str(owner), str(account), float(deposit) if deposit not in (None, "") else None, note, time.time()))
    db().commit()
    return broker_claim_by_account(account)


def broker_claim(claim_id):
    return _row(db().execute("SELECT * FROM broker_claims WHERE id = ?", (int(claim_id),)))


def broker_claim_by_account(account):
    return _row(db().execute("SELECT * FROM broker_claims WHERE account = ?", (str(account),)))


def broker_claims_for(owner):
    return [dict(r) for r in db().execute("SELECT * FROM broker_claims WHERE owner = ? ORDER BY created_at DESC", (str(owner),))]


def broker_claims(status=None, limit=500):
    if status:
        return [dict(r) for r in db().execute("SELECT * FROM broker_claims WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))]
    return [dict(r) for r in db().execute("SELECT * FROM broker_claims ORDER BY created_at DESC LIMIT ?", (limit,))]


def set_broker_claim(claim_id, status=None, deposit=None, note=None, verified_at=None):
    sets, args = [], []
    for col, val in (("status", status), ("deposit", deposit), ("note", note), ("verified_at", verified_at)):
        if val is not None:
            sets.append("%s = ?" % col)
            args.append(val)
    if sets:
        args.append(int(claim_id))
        db().execute("UPDATE broker_claims SET %s WHERE id = ?" % ", ".join(sets), args)
        db().commit()
    return broker_claim(claim_id)


# --------------------------------------------------------------------------- #
# Group auto-scan: the rooms a member pointed the bot at.
# --------------------------------------------------------------------------- #

GROUP_SCHEMA = """
CREATE TABLE IF NOT EXISTS group_watch (
    id         INTEGER PRIMARY KEY,
    group_id   TEXT NOT NULL,
    title      TEXT,
    owner      TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE (group_id, owner)
);
CREATE INDEX IF NOT EXISTS group_watch_owner ON group_watch(owner);
"""
SCHEMA += GROUP_SCHEMA


def add_group_watch(group_id, title, owner):
    db().execute(
        "INSERT INTO group_watch (group_id, title, owner, created_at) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(group_id, owner) DO UPDATE SET title = excluded.title",
        (str(group_id), title, str(owner), time.time()))
    db().commit()
    return group_watchers(group_id)


def drop_group_watch(group_id, owner):
    db().execute("DELETE FROM group_watch WHERE group_id = ? AND owner = ?", (str(group_id), str(owner)))
    db().commit()


def group_watchers(group_id):
    return [dict(r) for r in db().execute(
        "SELECT * FROM group_watch WHERE group_id = ? ORDER BY created_at", (str(group_id),))]


def groups_for(owner):
    return [dict(r) for r in db().execute(
        "SELECT * FROM group_watch WHERE owner = ? ORDER BY created_at", (str(owner),))]


# --------------------------------------------------------------------------- #
# Team ops: the internal CEO/HOD/Executive bot + dashboard. A separate role
# space from customer ranks (tiers.py) — a team member can hold both.
# --------------------------------------------------------------------------- #

TEAM_SCHEMA = """
CREATE TABLE IF NOT EXISTS team_roles (
    owner        TEXT PRIMARY KEY,
    role         TEXT NOT NULL,     -- ceo | hod_sales | hod_marketing | executive
    display_name TEXT,
    added_by     TEXT,
    created_at   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'open',    -- open | in_progress | done | delayed
    priority     TEXT NOT NULL DEFAULT 'normal',  -- low | normal | high
    due_at       REAL,
    assigned_to  TEXT,
    created_by   TEXT NOT NULL,
    created_at   REAL NOT NULL,
    updated_at   REAL NOT NULL,
    completed_at REAL
);
CREATE INDEX IF NOT EXISTS tasks_assignee ON tasks(assigned_to, status);
CREATE INDEX IF NOT EXISTS tasks_due ON tasks(due_at);
CREATE TABLE IF NOT EXISTS roadmap_items (
    id              INTEGER PRIMARY KEY,
    family          TEXT NOT NULL,       -- saas-tools | digital-products
    slug            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    vertical        TEXT,
    internal_status TEXT NOT NULL,       -- launched | ready_to_launch | in_progress | developing | not_delivered
    owner_role      TEXT,
    notes           TEXT,
    updated_by      TEXT,
    updated_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS roadmap_family ON roadmap_items(family, internal_status);
CREATE TABLE IF NOT EXISTS notify_prefs (
    owner           TEXT PRIMARY KEY,
    daily_digest    INTEGER NOT NULL DEFAULT 1,
    task_reminders  INTEGER NOT NULL DEFAULT 1,
    group_broadcast INTEGER NOT NULL DEFAULT 1
);
"""
SCHEMA += TEAM_SCHEMA

TEAM_ROLES = ("ceo", "hod_sales", "hod_marketing", "executive")
TEAM_FULL_ACCESS_ROLES = ("ceo", "hod_sales", "hod_marketing")


def team_role(owner):
    row = _row(db().execute("SELECT role FROM team_roles WHERE owner = ?", (str(owner),)))
    return row["role"] if row else None


def team_member(owner):
    return _row(db().execute("SELECT * FROM team_roles WHERE owner = ?", (str(owner),)))


def set_team_role(owner, role, display_name="", added_by=None):
    if role not in TEAM_ROLES:
        raise ValueError("unknown team role: %s" % role)
    now = time.time()
    db().execute(
        "INSERT INTO team_roles (owner, role, display_name, added_by, created_at) VALUES (?, ?, ?, ?, ?)"
        " ON CONFLICT(owner) DO UPDATE SET role = excluded.role,"
        " display_name = COALESCE(NULLIF(excluded.display_name, ''), team_roles.display_name), added_by = excluded.added_by",
        (str(owner), role, display_name, str(added_by) if added_by else None, now))
    db().commit()
    return team_member(owner)


def remove_team_role(owner):
    db().execute("DELETE FROM team_roles WHERE owner = ?", (str(owner),))
    db().commit()


def list_team_members():
    return [dict(r) for r in db().execute("SELECT * FROM team_roles ORDER BY role, created_at")]


# --- tasks ------------------------------------------------------------------ #

def add_task(title, created_by, description="", priority="normal", due_at=None, assigned_to=None):
    now = time.time()
    cur = db().execute(
        "INSERT INTO tasks (title, description, status, priority, due_at, assigned_to, created_by, created_at, updated_at)"
        " VALUES (?, ?, 'open', ?, ?, ?, ?, ?, ?)",
        (title.strip(), (description or "").strip(), priority, due_at,
         str(assigned_to) if assigned_to else None, str(created_by), now, now))
    db().commit()
    return task(cur.lastrowid)


def task(task_id):
    return _row(db().execute("SELECT * FROM tasks WHERE id = ?", (int(task_id),)))


def update_task(task_id, **fields):
    if not fields:
        return task(task_id)
    if "status" in fields:
        fields["completed_at"] = time.time() if fields["status"] == "done" else None
    fields["updated_at"] = time.time()
    cols = ", ".join("%s = ?" % k for k in fields)
    db().execute("UPDATE tasks SET %s WHERE id = ?" % cols, (*fields.values(), int(task_id)))
    db().commit()
    return task(task_id)


def delete_task(task_id):
    db().execute("DELETE FROM tasks WHERE id = ?", (int(task_id),))
    db().commit()


def tasks_all(status=None, assigned_to=None, limit=500):
    sql = "SELECT * FROM tasks WHERE 1=1"
    args = []
    if status:
        sql += " AND status = ?"
        args.append(status)
    if assigned_to:
        sql += " AND assigned_to = ?"
        args.append(str(assigned_to))
    args.append(limit)
    return [dict(r) for r in db().execute(sql + " ORDER BY (due_at IS NULL), due_at, created_at DESC LIMIT ?", args)]


def tasks_due_between(start_ts, end_ts):
    return [dict(r) for r in db().execute(
        "SELECT * FROM tasks WHERE due_at IS NOT NULL AND due_at >= ? AND due_at < ? AND status != 'done'"
        " ORDER BY due_at", (start_ts, end_ts))]


def tasks_overdue(now=None):
    now = now if now is not None else time.time()
    return [dict(r) for r in db().execute(
        "SELECT * FROM tasks WHERE due_at IS NOT NULL AND due_at < ? AND status NOT IN ('done')"
        " ORDER BY due_at", (now,))]


# --- roadmap ------------------------------------------------------------------ #

ROADMAP_STATUSES = ("launched", "ready_to_launch", "in_progress", "developing", "not_delivered")


def seed_roadmap(items):
    """Insert seed rows that do not exist yet. Never overwrites a status a
    human has already set — the dashboard is the source of truth once seeded."""
    now = time.time()
    for it in items:
        db().execute(
            "INSERT INTO roadmap_items (family, slug, name, vertical, internal_status, owner_role, notes, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(slug) DO NOTHING",
            (it["family"], it["slug"], it["name"], it.get("vertical", ""), it["internal_status"],
             it.get("owner_role"), it.get("notes", ""), now))
    db().commit()


def roadmap_items(family=None):
    sql = "SELECT * FROM roadmap_items"
    args = []
    if family:
        sql += " WHERE family = ?"
        args.append(family)
    return [dict(r) for r in db().execute(sql + " ORDER BY family, name", args)]


def set_roadmap_status(slug, internal_status, updated_by, notes=None):
    if internal_status not in ROADMAP_STATUSES:
        raise ValueError("unknown roadmap status: %s" % internal_status)
    fields = ["internal_status = ?", "updated_by = ?", "updated_at = ?"]
    args = [internal_status, str(updated_by), time.time()]
    if notes is not None:
        fields.append("notes = ?")
        args.append(notes.strip())
    args.append(slug)
    db().execute("UPDATE roadmap_items SET %s WHERE slug = ?" % ", ".join(fields), args)
    db().commit()
    return _row(db().execute("SELECT * FROM roadmap_items WHERE slug = ?", (slug,)))


# --- notification preferences ------------------------------------------------ #

def notify_prefs(owner):
    row = _row(db().execute("SELECT * FROM notify_prefs WHERE owner = ?", (str(owner),)))
    return row or {"owner": str(owner), "daily_digest": 1, "task_reminders": 1, "group_broadcast": 1}


def set_notify_pref(owner, key, value):
    if key not in ("daily_digest", "task_reminders", "group_broadcast"):
        raise ValueError("unknown notify pref: %s" % key)
    current = notify_prefs(owner)
    current[key] = 1 if value else 0
    db().execute(
        "INSERT INTO notify_prefs (owner, daily_digest, task_reminders, group_broadcast) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(owner) DO UPDATE SET %s = excluded.%s" % (key, key),
        (str(owner), current["daily_digest"], current["task_reminders"], current["group_broadcast"]))
    db().commit()
    return notify_prefs(owner)


def notify_prefs_enabled(key):
    """Every team member whose preference for `key` is on (or unset — default on)."""
    members = [m["owner"] for m in list_team_members()]
    off = {r["owner"] for r in db().execute("SELECT owner FROM notify_prefs WHERE %s = 0" % key)}
    return [m for m in members if m not in off]


# --- file library (docs / pics / vids) --------------------------------------- #

LIBRARY_SCHEMA = """
CREATE TABLE IF NOT EXISTS file_items (
    id         INTEGER PRIMARY KEY,
    category   TEXT NOT NULL,       -- doc | pic | vid
    title      TEXT NOT NULL,
    source     TEXT NOT NULL,       -- repo_asset | drive
    url        TEXT NOT NULL UNIQUE,
    tags       TEXT,
    added_by   TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS file_items_category ON file_items(category);
"""
SCHEMA += LIBRARY_SCHEMA

FILE_CATEGORIES = ("doc", "pic", "vid")


def seed_file_items(items):
    """Insert seed rows that do not exist yet, matched on url. Never
    overwrites a title/tags a human has already edited."""
    now = time.time()
    for it in items:
        db().execute(
            "INSERT INTO file_items (category, title, source, url, tags, created_at) VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(url) DO NOTHING",
            (it["category"], it["title"], it["source"], it["url"], it.get("tags", ""), now))
    db().commit()


def add_file_item(category, title, source, url, tags="", added_by=None):
    if category not in FILE_CATEGORIES:
        raise ValueError("unknown file category: %s" % category)
    db().execute(
        "INSERT INTO file_items (category, title, source, url, tags, added_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(url) DO UPDATE SET title = excluded.title, tags = excluded.tags",
        (category, title.strip(), source, url.strip(), tags.strip(), str(added_by) if added_by else None, time.time()))
    db().commit()


def file_items(category=None):
    sql = "SELECT * FROM file_items"
    args = []
    if category:
        sql += " WHERE category = ?"
        args.append(category)
    return [dict(r) for r in db().execute(sql + " ORDER BY category, title", args)]


def delete_file_item(item_id):
    db().execute("DELETE FROM file_items WHERE id = ?", (int(item_id),))
    db().commit()
