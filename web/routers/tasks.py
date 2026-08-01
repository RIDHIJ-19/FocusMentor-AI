"""Task CRUD + session lifecycle (start/pause/resume/checkin/finish)."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from web.config import MIN_CHECKIN_DURATION_MIN
from web.repository import (
    CHECKIN,
    COMPLETE,
    EXTEND,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    TaskRepository,
    UpdateRepository,
)
from web.services import rule_based_parser
from web.services.ai_service import AIService, SHORTFALL, SUCCESS

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

repo = TaskRepository()
update_repo = UpdateRepository()
ai_service = AIService()


class CreateTaskBody(BaseModel):
    name: str
    goal: Optional[str] = None
    duration_min: int
    start_time: Optional[str] = None


class ParseBody(BaseModel):
    text: str


class CheckinBody(BaseModel):
    note: str = ""
    elapsed_min: int
    remaining_min: int


class FinishBody(BaseModel):
    note: str = ""
    extend_requested: bool = False


def _checkin_interval(duration_min: int) -> int:
    if duration_min < MIN_CHECKIN_DURATION_MIN:
        return 0
    return duration_min // 4


@router.get("")
def list_tasks():
    return repo.get_by_date()


@router.post("")
def create_task(body: CreateTaskBody):
    return repo.create(
        name=body.name, goal=body.goal, duration_min=body.duration_min, start_time=body.start_time
    )


@router.post("/parse")
def parse_plan(body: ParseBody):
    result = ai_service.parse_plan_text(body.text)
    return {"used_ai": result.used_ai, "fallback_reason": result.fallback_reason, "tasks": result.tasks}


@router.delete("/{task_id}")
def delete_task(task_id: int):
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] == STATUS_IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Stop the active session before deleting this task.")
    repo.delete(task_id)
    return {"ok": True}


@router.post("/{task_id}/start")
def start_task(task_id: int):
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] == STATUS_COMPLETED:
        raise HTTPException(status_code=400, detail="This task is already completed.")

    started_at = datetime.now().isoformat(timespec="seconds")
    repo.update_status(task_id, STATUS_IN_PROGRESS, started_at=started_at)
    interval = _checkin_interval(task["duration_min"])
    return {
        "task_id": task_id,
        "started_at": started_at,
        "duration_min": task["duration_min"],
        "checkin_interval_min": interval,
    }


@router.post("/{task_id}/pause")
def pause_task(task_id: int):
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    repo.pause(task_id)
    return {"ok": True}


@router.post("/{task_id}/resume")
def resume_task(task_id: int):
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    repo.resume(task_id)
    return repo.get_by_id(task_id)


@router.post("/{task_id}/checkin")
def checkin(task_id: int, body: CheckinBody):
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    update = update_repo.add(
        task_id, CHECKIN, body.note, elapsed_min=body.elapsed_min, remaining_min=body.remaining_min
    )
    return update


@router.post("/{task_id}/finish")
def finish_task(task_id: int, body: FinishBody):
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.extend_requested:
        minutes = rule_based_parser.extract_duration_minutes(body.note)
        if minutes is None:
            raise HTTPException(
                status_code=422,
                detail="Couldn't tell how long -- try e.g. \"10 more minutes\" or \"half an hour\".",
            )
        extend_minutes = max(1, min(minutes, 240))
        repo.extend_duration(task_id, extend_minutes)
        update_repo.add(task_id, EXTEND, body.note)
        interval = _checkin_interval(extend_minutes)
        return {
            "extended": True,
            "extend_minutes": extend_minutes,
            "checkin_interval_min": interval,
            "task": repo.get_by_id(task_id),
        }

    repo.update_status(task_id, STATUS_COMPLETED, notes=body.note or None)
    update_repo.add(task_id, COMPLETE, body.note)

    verdict = ai_service.assess_completion(task["name"], task["goal"], body.note)
    return {
        "extended": False,
        "verdict": verdict,
        "is_success": verdict == SUCCESS,
        "is_shortfall": verdict == SHORTFALL,
        "task": repo.get_by_id(task_id),
    }
