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
