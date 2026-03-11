"""Database CRUD operations."""

from __future__ import annotations

import csv
import io
from datetime import date

from sqlalchemy.orm import Session

from app.models import Task
from app.schemas import TaskCreate, TaskUpdate


def get_tasks(db: Session, include_done: bool = True) -> list[Task]:
    q = db.query(Task)
    if not include_done:
        q = q.filter(Task.done == False)  # noqa: E712
    return q.order_by(Task.id).all()


def get_task(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def create_task(db: Session, task_in: TaskCreate) -> Task:
    task = Task(
        description=task_in.description,
        priority=task_in.priority,
        due=task_in.due,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: int, data: TaskUpdate) -> Task | None:
    task = get_task(db, task_id)
    if task is None:
        return None
    if data.due is not None or "due" in data.model_fields_set:
        task.due = data.due
    if data.priority is not None:
        task.priority = data.priority
    db.commit()
    db.refresh(task)
    return task


def mark_done(db: Session, task_id: int) -> Task | None:
    task = get_task(db, task_id)
    if task is None:
        return None
    task.done = True
    db.commit()
    db.refresh(task)
    return task


def mark_open(db: Session, task_id: int) -> Task | None:
    task = get_task(db, task_id)
    if task is None:
        return None
    task.done = False
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> bool:
    task = get_task(db, task_id)
    if task is None:
        return False
    db.delete(task)
    db.commit()
    return True


def get_briefing_tasks(db: Session, today: date | None = None):
    """Return (overdue, today, general) lists of open tasks."""
    if today is None:
        today = date.today()
    open_tasks = get_tasks(db, include_done=False)
    overdue, due_today, general = [], [], []
    for t in open_tasks:
        if t.due is None:
            general.append(t)
        elif t.due < today:
            overdue.append(t)
        elif t.due == today:
            due_today.append(t)
    return overdue, due_today, general


def export_csv(db: Session) -> str:
    """Export all tasks as a CSV string."""
    tasks = get_tasks(db, include_done=True)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "description", "priority", "due", "done", "created_at"])
    for t in tasks:
        writer.writerow([
            t.id, t.description, t.priority,
            t.due.isoformat() if t.due else "",
            "yes" if t.done else "no",
            t.created_at.isoformat(),
        ])
    return buf.getvalue()


def export_markdown(db: Session) -> str:
    """Export all tasks in tasks.md format (compatible with CLI app)."""
    tasks = get_tasks(db, include_done=True)
    lines = []
    for t in tasks:
        status = "[x]" if t.done else "[ ]"
        parts = [f"- {status} {t.description}"]
        if t.priority != "Medium":
            parts.append(f"/p:{t.priority}")
        if t.due:
            parts.append(f"/d:{t.due.isoformat()}")
        lines.append(" ".join(parts))
    return "\n".join(lines) + ("\n" if lines else "")
