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
        g.db = conn
    return g.db


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


def baseline_spread():
    rows = [r[0] for r in db().execute("SELECT spread FROM spread_log WHERE spread IS NOT NULL")]
    if not rows:
        return None
    rows.sort()
    return rows[len(rows) // 2]


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


def public_scans(product, subject, limit=10):
    return [dict(r) for r in db().execute(
        "SELECT id, score, verdict, created_at FROM scans WHERE product = ? AND subject = ? ORDER BY created_at DESC LIMIT ?",
        (product, subject, limit))]
