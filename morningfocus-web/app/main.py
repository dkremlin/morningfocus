"""FastAPI application — MorningFocus Web."""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()  # reads morningfocus-web/.env automatically when running locally

import csv
import io
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import crud, models
from app.auth import require_auth
from app.database import engine, get_db, init_db
from app.parser import parse_add_string
from app.schemas import BriefingOut, ParseResult, TaskCreate, TaskOut, TaskUpdate

app = FastAPI(title="MorningFocus", version="0.1.0")

# Protected router — every route added here requires a valid Supabase token.
# The two HTML pages (/ and /login) stay on `app` directly so they are public.
_api = APIRouter(dependencies=[Depends(require_auth)])

# Serve static assets (CSS, JS, images if any)
_static = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=_static), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# ---------------------------------------------------------------------------
# Frontend (public — no auth needed to load the HTML pages)
# ---------------------------------------------------------------------------

@app.get("/", response_class=FileResponse, include_in_schema=False)
def index():
    return str(_static / "index.html")


@app.get("/login", response_class=FileResponse, include_in_schema=False)
def login_page():
    return str(_static / "login.html")


@app.get("/api/config", include_in_schema=False)
def public_config():
    """Return the public Supabase keys so the frontend can initialise the JS client.
    The anon key is intentionally public — it is safe to expose in the browser."""
    import os
    return {
        "supabase_url": os.environ.get("SUPABASE_URL", ""),
        "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
    }


# ---------------------------------------------------------------------------
# Tasks API  (protected)
# ---------------------------------------------------------------------------

@_api.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(
    include_done: bool = Query(True, description="Include completed tasks"),
    db: Session = Depends(get_db),
):
    return crud.get_tasks(db, include_done=include_done)


@_api.post("/api/tasks", response_model=TaskOut, status_code=201)
def add_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task_in)


@_api.post("/api/tasks/parse", response_model=ParseResult)
def parse_task(body: dict, db: Session = Depends(get_db)):
    """Parse a free-text string into structured fields (live preview as you type)."""
    raw = body.get("text", "")
    try:
        return parse_add_string(raw)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@_api.patch("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = crud.update_task(db, task_id, data)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@_api.patch("/api/tasks/{task_id}/done", response_model=TaskOut)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.mark_done(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@_api.patch("/api/tasks/{task_id}/reopen", response_model=TaskOut)
def reopen_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.mark_open(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@_api.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    if not crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")


# ---------------------------------------------------------------------------
# Briefing API  (protected)
# ---------------------------------------------------------------------------

@_api.get("/api/brief", response_model=BriefingOut)
def briefing(db: Session = Depends(get_db)):
    today = date.today()
    overdue, due_today, general = crud.get_briefing_tasks(db, today=today)
    return BriefingOut(
        date=today,
        overdue=[TaskOut.model_validate(t) for t in overdue],
        today=[TaskOut.model_validate(t) for t in due_today],
        general=[TaskOut.model_validate(t) for t in general],
    )


# ---------------------------------------------------------------------------
# Export API  (protected)
# ---------------------------------------------------------------------------

@_api.get("/api/export/csv")
def export_csv(db: Session = Depends(get_db)):
    content = crud.export_csv(db)
    return PlainTextResponse(
        content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tasks.csv"},
    )


@_api.get("/api/export/markdown")
def export_markdown(db: Session = Depends(get_db)):
    content = crud.export_markdown(db)
    return PlainTextResponse(
        content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=tasks.md"},
    )


# Register the protected router last (after the public routes above)
app.include_router(_api)
