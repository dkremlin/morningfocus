"""Database CRUD operations."""

from __future__ import annotations

import csv
import io
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Profile, Task
from app.schemas import TaskCreate, TaskUpdate


# ---------------------------------------------------------------------------
# Visibility rule (used in every task query):
# A task is visible to user X if:
#   - assigned_to = "all"            → visible to everyone
#   - assigned_to = X's UUID         → always visible to X
#   - assigned_to = someone else AND private = False → still visible to X
# ---------------------------------------------------------------------------

def _visible_filter(user_id: str):
    """SQLAlchemy filter that returns tasks the given user is allowed to see."""
    return or_(
        Task.assigned_to == "all",
        Task.assigned_to == user_id,
        Task.private == False,  # noqa: E712 — public tasks assigned to others
    )


def get_tasks(db: Session, user_id: str, include_done: bool = True) -> list[Task]:
    q = db.query(Task).filter(_visible_filter(user_id))
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
        assigned_to=task_in.assigned_to,
        private=task_in.private,
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
    if data.assigned_to is not None:
        task.assigned_to = data.assigned_to
    if data.private is not None:
        task.private = data.private
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


def get_briefing_tasks(db: Session, user_id: str, today: date | None = None):
    """Return (overdue, today, general) lists of open tasks visible to user."""
    if today is None:
        today = date.today()
    open_tasks = get_tasks(db, user_id=user_id, include_done=False)
    overdue, due_today, general = [], [], []
    for t in open_tasks:
        if t.due is None:
            general.append(t)
        elif t.due < today:
            overdue.append(t)
        elif t.due == today:
            due_today.append(t)
    return overdue, due_today, general


def export_csv(db: Session, user_id: str) -> str:
    """Export all visible tasks as a CSV string."""
    tasks = get_tasks(db, user_id=user_id, include_done=True)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "description", "priority", "due", "done", "assigned_to", "private", "created_at"])
    for t in tasks:
        writer.writerow([
            t.id, t.description, t.priority,
            t.due.isoformat() if t.due else "",
            "yes" if t.done else "no",
            t.assigned_to,
            "yes" if t.private else "no",
            t.created_at.isoformat(),
        ])
    return buf.getvalue()


def export_markdown(db: Session, user_id: str) -> str:
    """Export visible tasks in tasks.md format."""
    tasks = get_tasks(db, user_id=user_id, include_done=True)
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


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

def upsert_profile(db: Session, user_id: str, email: str) -> Profile:
    """Insert or update the user's profile row."""
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if profile is None:
        profile = Profile(id=user_id, email=email)
        db.add(profile)
    else:
        profile.email = email
    db.commit()
    db.refresh(profile)
    return profile


def get_profiles(db: Session) -> list[Profile]:
    return db.query(Profile).order_by(Profile.email).all()
