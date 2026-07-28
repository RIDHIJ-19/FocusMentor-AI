"""Data access for tasks."""
from datetime import datetime, date, timedelta
from typing import List, Optional

from app.config import STATUS_IN_PROGRESS, STATUS_NOT_STARTED
from app.db.database import get_connection
from app.models.task import Task


def _row_to_task(row) -> Task:
    return Task(
        id=row["id"],
        name=row["name"],
        goal=row["goal"],
        plan_date=row["plan_date"],
        start_time=row["start_time"],
        duration_min=row["duration_min"],
        status=row["status"],
        notes=row["notes"],
        created_at=row["created_at"],
        started_at=row["started_at"],
    )


class TaskRepository:
    def create(
        self,
        name: str,
        goal: Optional[str],
        duration_min: int,
        start_time: Optional[str] = None,
        plan_date: Optional[str] = None,
    ) -> Task:
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

    def get_by_id(self, task_id: int) -> Optional[Task]:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        finally:
            conn.close()
        return _row_to_task(row) if row else None

    def get_by_date(self, plan_date: Optional[str] = None) -> List[Task]:
        plan_date = plan_date or date.today().isoformat()
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE plan_date = ? ORDER BY id ASC", (plan_date,)
            ).fetchall()
        finally:
            conn.close()
        return [_row_to_task(r) for r in rows]

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

    def delete(self, task_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
        finally:
            conn.close()

    def delete_overdue_in_progress(self) -> List[Task]:
        """Self-healing for crashes/force-quits: a task left 'in_progress'
        whose duration has clearly already elapsed can never resume (each
        launch starts with no active timer), so it would otherwise sit
        stuck forever needing manual cleanup. Deletes and returns any such
        tasks so the caller can log/notify what was removed."""
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? AND started_at IS NOT NULL",
                (STATUS_IN_PROGRESS,),
            ).fetchall()
            overdue = []
            now = datetime.now()
            for row in rows:
                task = _row_to_task(row)
                started = datetime.fromisoformat(task.started_at)
                if now >= started + timedelta(minutes=task.duration_min):
                    overdue.append(task)
            for task in overdue:
                conn.execute("DELETE FROM tasks WHERE id = ?", (task.id,))
            conn.commit()
        finally:
            conn.close()
        return overdue

    def get_recent(self, days: int = 14) -> List[Task]:
        since = (date.today() - timedelta(days=days)).isoformat()
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE plan_date >= ? ORDER BY plan_date DESC, id ASC",
                (since,),
            ).fetchall()
        finally:
            conn.close()
        return [_row_to_task(r) for r in rows]

    def count_completed_all_time(self) -> int:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM tasks WHERE status = 'completed'"
            ).fetchone()
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
