"""Task dataclass and related enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Status(str, Enum):
    OPEN = "[ ]"
    DONE = "[x]"


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Task:
    description: str
    status: Status = Status.OPEN
    priority: Priority = Priority.MEDIUM
    due: date | None = None
    line_number: int = field(default=0, compare=False, repr=False)
