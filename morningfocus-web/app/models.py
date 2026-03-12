"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, default="Medium", nullable=False)
    due: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    # "all" means visible to everyone; a user UUID means assigned to that person
    assigned_to: Mapped[str] = mapped_column(String, default="all", nullable=False)
    # private=True hides the task from everyone except the assignee
    private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Profile(Base):
    """One row per registered user — populated on first login."""
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)   # Supabase UUID
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
