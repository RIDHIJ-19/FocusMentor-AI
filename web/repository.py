"""Data access for tasks and their check-in/completion reply history.

Ported from the desktop app's app/db/repository.py + app/db/update_repository.py,
same schema and query style -- see web/db.py for why this is plain sqlite3
rather than an ORM.
"""
from datetime import datetime, date, timedelta
from typing import List, Optional

from web.db import get_connection

STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"

CHECKIN = "checkin"
COMPLETE = "complete"
EXTEND = "extend"


def _task_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "goal": row["goal"],
        "plan_date": row["plan_date"],
        "start_time": row["start_time"],
        "duration_min": row["duration_min"],
        "status": row["status"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "started_at": row["started_at"],
        "paused_at": row["paused_at"],
        "paused_seconds": row["paused_seconds"],
    }


class TaskRepository:
    def create(
        self,
        name: str,
        goal: Optional[str],
        duration_min: int,
        start_time: Optional[str] = None,
        plan_date: Optional[str] = None,
    ) -> dict:
        plan_date = plan_date or date.today().isoformat()
        created_at = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        try:
            cur = conn.execute(
                """INSERT INTO tasks (name, goal, plan_date, start_time, duration_min, status, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, goal, plan_date, start_time, duration_min, STATUS_NOT_STARTED, None, created_at),
            )
            conn.commit()
            task_id = cur.lastrowid
        finally:
            conn.close()
        return self.get_by_id(task_id)

    def get_by_id(self, task_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        finally:
            conn.close()
        return _task_to_dict(row) if row else None

    def get_by_date(self, plan_date: Optional[str] = None) -> List[dict]:
        plan_date = plan_date or date.today().isoformat()
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE plan_date = ? ORDER BY id ASC", (plan_date,)
            ).fetchall()
        finally:
            conn.close()
        return [_task_to_dict(r) for r in rows]

    def update_status(
        self,
        task_id: int,
        status: str,
        notes: Optional[str] = None,
        started_at: Optional[str] = None,
    ) -> None:
        conn = get_connection()
        try:
            if started_at is not None:
                conn.execute(
                    "UPDATE tasks SET status = ?, started_at = ? WHERE id = ?",
                    (status, started_at, task_id),
                )
            elif notes is not None:
                conn.execute(
                    "UPDATE tasks SET status = ?, notes = ? WHERE id = ?", (status, notes, task_id)
                )
            else:
                conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
            conn.commit()
        finally:
            conn.close()

    def pause(self, task_id: int) -> None:
        """Records the moment paused_at; resume() later folds the elapsed
        pause duration into paused_seconds. Wall-clock-derived timers (no
        in-memory countdown like the desktop app's QTimer) need this
        bookkeeping to compute 'real' elapsed time around a pause."""
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE tasks SET paused_at = ? WHERE id = ?",
                (datetime.now().isoformat(timespec="seconds"), task_id),
            )
            conn.commit()
        finally:
            conn.close()

    def resume(self, task_id: int) -> None:
        conn = get_connection()
        try:
            row = conn.execute("SELECT paused_at, paused_seconds FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row and row["paused_at"]:
                paused_at = datetime.fromisoformat(row["paused_at"])
                additional = int((datetime.now() - paused_at).total_seconds())
                conn.execute(
                    "UPDATE tasks SET paused_at = NULL, paused_seconds = paused_seconds + ? WHERE id = ?",
                    (additional, task_id),
                )
                conn.commit()
        finally:
            conn.close()

    def extend_duration(self, task_id: int, additional_minutes: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE tasks SET duration_min = duration_min + ? WHERE id = ?",
                (additional_minutes, task_id),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, task_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
        finally:
            conn.close()

    def delete_overdue_in_progress(self) -> List[dict]:
        """Self-healing after a server restart: a task left 'in_progress'
        whose duration has clearly already elapsed can never resume (a
        fresh process has no in-memory timer for it), so remove it rather
        than leave it stuck."""
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? AND started_at IS NOT NULL",
                (STATUS_IN_PROGRESS,),
            ).fetchall()
            overdue = []
            now = datetime.now()
            for row in rows:
                task = _task_to_dict(row)
                if task["paused_at"]:
                    continue  # deliberately paused -- not abandoned, leave it
                started = datetime.fromisoformat(task["started_at"])
                deadline = started + timedelta(minutes=task["duration_min"], seconds=task["paused_seconds"])
                if now >= deadline:
                    overdue.append(task)
            for task in overdue:
                conn.execute("DELETE FROM tasks WHERE id = ?", (task["id"],))
            conn.commit()
        finally:
            conn.close()
        return overdue

    def get_recent(self, days: int = 14) -> List[dict]:
        since = (date.today() - timedelta(days=days)).isoformat()
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE plan_date >= ? ORDER BY plan_date DESC, id ASC",
                (since,),
            ).fetchall()
        finally:
            conn.close()
        return [_task_to_dict(r) for r in rows]

    def count_completed_all_time(self) -> int:
        conn = get_connection()
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM tasks WHERE status = 'completed'").fetchone()
        finally:
            conn.close()
        return row["c"] if row else 0

    def count_distinct_active_days(self) -> int:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT COUNT(DISTINCT plan_date) AS c FROM tasks WHERE status = 'completed'"
            ).fetchone()
        finally:
            conn.close()
        return row["c"] if row else 0


class UpdateRepository:
    def add(
        self,
        task_id: int,
        kind: str,
        note: Optional[str],
        elapsed_min: Optional[int] = None,
        remaining_min: Optional[int] = None,
    ) -> dict:
        created_at = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        try:
            cur = conn.execute(
                """INSERT INTO updates (task_id, kind, elapsed_min, remaining_min, note, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (task_id, kind, elapsed_min, remaining_min, note or None, created_at),
            )
            conn.commit()
            update_id = cur.lastrowid
            row = conn.execute("SELECT * FROM updates WHERE id = ?", (update_id,)).fetchone()
        finally:
            conn.close()
        return dict(row)

    def get_recent(self, days: int = 14) -> List[dict]:
        since = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT updates.*, tasks.name AS task_name
                   FROM updates
                   JOIN tasks ON tasks.id = updates.task_id
                   WHERE updates.created_at >= ?
                   ORDER BY updates.created_at DESC""",
                (since,),
            ).fetchall()
        finally:
            conn.close()
        return [dict(r) for r in rows]


class TodoRepository:
    """Casual, unscheduled sticky-note to-dos by date -- separate from the
    structured Task system (no duration/timer/AI judging, just jot it down
    and check it off)."""

    def create(self, todo_date: str, text: str) -> dict:
        created_at = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO todos (todo_date, text, done, created_at) VALUES (?, ?, 0, ?)",
                (todo_date, text, created_at),
            )
            conn.commit()
            todo_id = cur.lastrowid
            row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        finally:
            conn.close()
        return dict(row)

    def get_by_date(self, todo_date: str) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM todos WHERE todo_date = ? ORDER BY id ASC", (todo_date,)
            ).fetchall()
        finally:
            conn.close()
        return [dict(r) for r in rows]

    def toggle_done(self, todo_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute("SELECT done FROM todos WHERE id = ?", (todo_id,)).fetchone()
            if not row:
                return None
            new_done = 0 if row["done"] else 1
            conn.execute("UPDATE todos SET done = ? WHERE id = ?", (new_done, todo_id))
            conn.commit()
            updated = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        finally:
            conn.close()
        return dict(updated)

    def delete(self, todo_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
            conn.commit()
        finally:
            conn.close()


class NoteRepository:
    """One free-form scratchpad note per date -- a spot for comments that
    don't fit as a checklist item."""

    def get(self, note_date: str) -> str:
        conn = get_connection()
        try:
            row = conn.execute("SELECT text FROM notes WHERE note_date = ?", (note_date,)).fetchone()
        finally:
            conn.close()
        return row["text"] if row else ""

    def save(self, note_date: str, text: str) -> str:
        updated_at = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO notes (note_date, text, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(note_date) DO UPDATE SET text = excluded.text, updated_at = excluded.updated_at""",
                (note_date, text, updated_at),
            )
            conn.commit()
        finally:
            conn.close()
        return text
