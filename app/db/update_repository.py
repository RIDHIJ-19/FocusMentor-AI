"""Data access for check-in / session-complete replies (the `updates` table)."""
from datetime import datetime, timedelta
from typing import List, Optional

from app.db.database import get_connection
from app.models.update import Update


def _row_to_update(row) -> Update:
    return Update(
        id=row["id"],
        task_id=row["task_id"],
        kind=row["kind"],
        elapsed_min=row["elapsed_min"],
        remaining_min=row["remaining_min"],
        note=row["note"],
        created_at=row["created_at"],
    )


class UpdateRepository:
    def add(
        self,
        task_id: int,
        kind: str,
        note: Optional[str],
        elapsed_min: Optional[int] = None,
        remaining_min: Optional[int] = None,
    ) -> Update:
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
        finally:
            conn.close()
        return self._get_by_id(update_id)

    def _get_by_id(self, update_id: int) -> Optional[Update]:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM updates WHERE id = ?", (update_id,)).fetchone()
        finally:
            conn.close()
        return _row_to_update(row) if row else None

    def get_recent(self, days: int = 14) -> List[dict]:
        """Recent updates joined with the task name, newest first -- the
        shape the Dashboard's history view and future mentor-insight code
        want (task_name alongside the raw update columns)."""
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
