"""A single timestamped reply against a task: a mid-session check-in or the
end-of-session "how did it go" note. Multiple can exist per task, unlike
Task.notes which only holds the latest/final one."""
from dataclasses import dataclass
from typing import Optional

CHECKIN = "checkin"
COMPLETE = "complete"
EXTEND = "extend"


@dataclass
class Update:
    id: Optional[int]
    task_id: int
    kind: str  # CHECKIN | COMPLETE | EXTEND
    elapsed_min: Optional[int]
    remaining_min: Optional[int]
    note: Optional[str]
    created_at: str
