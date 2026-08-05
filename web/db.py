"""Postgres connection and schema initialization (Neon free tier).

Switched from the original session-scoped SQLite design after the user
decided data should survive redeploys/idle-restarts -- Render's free Web
Service tier has no persistent disk, so SQLite there was always going to
reset. Neon's free Postgres doesn't expire the way Render's own free
Postgres does (30-day auto-delete), so it's the one used here.

DATABASE_URL (a Neon connection string) is required -- see web/settings.py.
"""
import psycopg
from psycopg.rows import dict_row

from web import settings

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
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
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS updates (
        id SERIAL PRIMARY KEY,
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        kind TEXT NOT NULL,
        elapsed_min INTEGER,
        remaining_min INTEGER,
        note TEXT,
        created_at TEXT NOT NULL
    )
    """,
    # Migration for DBs created before ON DELETE CASCADE was added above --
    # SQLite (the original dev DB) never enforced this FK at all, so a task
    # delete that left orphaned "updates" rows behind was silently fine
    # there; Postgres enforces it, which crash-looped the app on startup
    # (delete_overdue_in_progress deleting a task that still had updates).
    """
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.referential_constraints
            WHERE constraint_name = 'updates_task_id_fkey' AND delete_rule = 'NO ACTION'
        ) THEN
            ALTER TABLE updates DROP CONSTRAINT updates_task_id_fkey;
            ALTER TABLE updates ADD CONSTRAINT updates_task_id_fkey
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE;
        END IF;
    END $$;
    """,
    """
    CREATE TABLE IF NOT EXISTS todos (
        id SERIAL PRIMARY KEY,
        todo_date TEXT NOT NULL,
        text TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notes (
        note_date TEXT PRIMARY KEY,
        text TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL
    )
    """,
]


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(settings.get_database_url(), row_factory=dict_row)
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for statement in SCHEMA_STATEMENTS:
                cur.execute(statement)
        conn.commit()
    finally:
        conn.close()
