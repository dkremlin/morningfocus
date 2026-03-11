"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


Priority = Literal["High", "Medium", "Low"]


class TaskCreate(BaseModel):
    description: str
    priority: Priority = "Medium"
    due: Optional[date] = None

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Description cannot be empty")
        return v


class TaskOut(BaseModel):
    id: int
    description: str
    priority: Priority
    due: Optional[date]
    done: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BriefingOut(BaseModel):
    date: date
    overdue: list[TaskOut]
    today: list[TaskOut]
    general: list[TaskOut]


class TaskUpdate(BaseModel):
    due: Optional[date] = None
    priority: Optional[Priority] = None


class ParseResult(BaseModel):
    """Result of parsing a free-text add string."""
    description: str
    priority: Priority
    due: Optional[date]
