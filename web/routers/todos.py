"""Casual sticky-note to-dos and scratchpad notes by date -- separate from
the structured Task/timer system."""
from datetime import date as date_cls
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from web.repository import NoteRepository, TodoRepository

router = APIRouter(prefix="/api/todos", tags=["todos"])
notes_router = APIRouter(prefix="/api/notes", tags=["notes"])

repo = TodoRepository()
note_repo = NoteRepository()


class CreateTodoBody(BaseModel):
    date: str
    text: str


class SaveNoteBody(BaseModel):
    date: str
    text: str


@router.get("")
def list_todos(date: Optional[str] = None):
    return repo.get_by_date(date or date_cls.today().isoformat())


@router.post("")
def create_todo(body: CreateTodoBody):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Todo text can't be empty.")
    return repo.create(body.date, text)


@router.post("/{todo_id}/toggle")
def toggle_todo(todo_id: int):
    todo = repo.toggle_done(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.delete("/{todo_id}")
def delete_todo(todo_id: int):
    repo.delete(todo_id)
    return {"ok": True}


@notes_router.get("")
def get_note(date: Optional[str] = None):
    note_date = date or date_cls.today().isoformat()
    return {"date": note_date, "text": note_repo.get(note_date)}


@notes_router.post("")
def save_note(body: SaveNoteBody):
    text = note_repo.save(body.date, body.text)
    return {"date": body.date, "text": text}
