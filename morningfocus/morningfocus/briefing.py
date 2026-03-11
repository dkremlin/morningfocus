"""Pure classification logic for the morning briefing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from morningfocus.models import Status, Task


@dataclass
class BriefingResult:
    overdue: list[Task] = field(default_factory=list)
    today: list[Task] = field(default_factory=list)
    general: list[Task] = field(default_factory=list)

    @property
    def has_overdue(self) -> bool:
        return bool(self.overdue)

    @property
    def total_open(self) -> int:
        return len(self.overdue) + len(self.today) + len(self.general)


def classify_tasks(tasks: list[Task], today: date | None = None) -> BriefingResult:
    """Classify open tasks into overdue, today, and general buckets.

    This is a pure function — no I/O.
    """
    if today is None:
        today = date.today()

    result = BriefingResult()

    for task in tasks:
        if task.status != Status.OPEN:
            continue

        if task.due is None:
            result.general.append(task)
        elif task.due < today:
            result.overdue.append(task)
        elif task.due == today:
            result.today.append(task)
        # Future tasks are not included in the briefing

    return result
