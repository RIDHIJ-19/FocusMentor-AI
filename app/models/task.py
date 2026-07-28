"""Task data model."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    id: Optional[int]
    name: str
    goal: Optional[str]
    plan_date: str        # ISO date, "YYYY-MM-DD"
    start_time: Optional[str]  # "HH:MM"
    duration_min: int
    status: str
    notes: Optional[str]
    created_at: str
    started_at: Optional[str] = None

    @property
    def remaining_seconds_hint(self) -> int:
        return self.duration_min * 60
