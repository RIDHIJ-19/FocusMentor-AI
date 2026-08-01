"""FocusMentor AI -- web version entry point."""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from web.db import init_db
from web.repository import TaskRepository
from web.routers import tasks, updates

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="FocusMentor AI")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    removed = TaskRepository().delete_overdue_in_progress()
    for task in removed:
        logger.warning(
            "Auto-removed stale in-progress task id=%s (%r) -- started at %s, never finished.",
            task["id"], task["name"], task["started_at"],
        )


app.include_router(tasks.router)
app.include_router(updates.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
