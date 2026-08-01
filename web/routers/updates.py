"""Dashboard data, mentor insight, and audio transcription."""
from fastapi import APIRouter, File, UploadFile

from web.repository import TaskRepository, UpdateRepository
from web.services import motivation
from web.services.ai_service import AIService

router = APIRouter(prefix="/api", tags=["updates"])

repo = TaskRepository()
update_repo = UpdateRepository()
ai_service = AIService()


@router.get("/motivation/{category}")
def motivation_line(category: str):
    return {"line": motivation.get_line(category)}


@router.get("/dashboard")
def dashboard():
    tasks = repo.get_by_date()
    return {
        "tasks": tasks,
        "completed_all_time": repo.count_completed_all_time(),
        "active_days": repo.count_distinct_active_days(),
        "recent_updates": update_repo.get_recent(days=14),
    }


@router.post("/insight")
def insight():
    recent_tasks = repo.get_recent(days=14)
    text = ai_service.generate_insight(recent_tasks)
    return {"text": text}


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    wav_bytes = await file.read()
    text = ai_service.transcribe_audio(wav_bytes)
    return {"text": text}
