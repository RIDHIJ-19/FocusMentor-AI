"""SQLite connection and schema initialization."""
import sqlite3

from app.config import DB_PATH

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
    started_at TEXT
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


def _migrate(conn: sqlite3.Connection) -> None:
    """Lightweight migration for databases created before a column existed."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
    if "started_at" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN started_at TEXT")


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()
    finally:
        conn.close()
