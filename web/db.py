"""SQLite connection and schema initialization.

Session-scoped by design: on Render's free tier this file lives on
ephemeral disk and resets on every redeploy/idle-restart. That's accepted
here (only current-session history is needed for the web version), not a
bug -- see PLAN.md.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "focusmentor.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    goal TEXT,
    plan_date TEXT NOT NULL,
    start_time TEXT,
    duration_min INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started',
    notes TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    paused_at TEXT,
    paused_seconds INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    elapsed_min INTEGER,
    remaining_min INTEGER,
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
