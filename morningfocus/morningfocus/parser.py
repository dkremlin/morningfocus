"""Parsing, serialisation, and date resolution for MorningFocus tasks."""

from __future__ import annotations

import logging
import re
from datetime import date

from dateutil import parser as dateutil_parser

from morningfocus.exceptions import InvalidDateError, ParseError
from morningfocus.models import Priority, Status, Task

logger = logging.getLogger(__name__)

# Matches a full task line: - [status] description /p:... /d:...
_TASK_LINE_RE = re.compile(
    r"^- (\[[ x]\]) (.+)$"
)

# Tag patterns — require preceding whitespace or start-of-string
_PRIORITY_RE = re.compile(r"(?<!\S)/p:(High|Medium|Low)\b", re.IGNORECASE)
_DATE_RE = re.compile(r"(?<!\S)/d:(\S+)")

_NATURAL_TODAY = {"today"}
_NATURAL_TOMORROW = {"tomorrow"}


def resolve_date(date_str: str, today: date | None = None) -> date:
    """Parse a date string into a date object.

    Accepts YYYY-MM-DD, natural language like 'tomorrow', or anything
    dateutil can handle. Raises InvalidDateError on failure.
    """
    if today is None:
        today = date.today()

    normalized = date_str.strip().lower()

    if normalized in _NATURAL_TODAY:
        return today

    if normalized in _NATURAL_TOMORROW:
        from datetime import timedelta
        return today + timedelta(days=1)

    try:
        parsed = dateutil_parser.parse(date_str, default=None)
        return parsed.date()
    except (ValueError, OverflowError, TypeError):
        raise InvalidDateError(date_str)


def parse_add_string(raw: str, today: date | None = None) -> Task:
    """Parse a raw add-command string into a Task.

    Tags (/p:, /d:) are extracted from anywhere in the string.
    Duplicate tags: last match wins (with a debug warning).
    Remaining text becomes the description.
    """
    # Extract all priority matches; last wins
    priority_matches = _PRIORITY_RE.findall(raw)
    if len(priority_matches) > 1:
        logger.debug("Duplicate /p: tag; using last match: %s", priority_matches[-1])

    if priority_matches:
        priority = Priority(priority_matches[-1].capitalize())
    else:
        priority = Priority.MEDIUM

    # Extract all date matches; last wins
    date_matches = _DATE_RE.findall(raw)
    if len(date_matches) > 1:
        logger.debug("Duplicate /d: tag; using last match: %s", date_matches[-1])

    due: date | None = None
    if date_matches:
        due = resolve_date(date_matches[-1], today=today)

    # Remove all tags from the string to get the description
    cleaned = _PRIORITY_RE.sub("", raw)
    cleaned = _DATE_RE.sub("", cleaned)
    description = " ".join(cleaned.split())

    if not description:
        raise ParseError(raw, "description is empty after tag extraction")

    return Task(description=description, priority=priority, due=due)


def parse_line(line: str, line_number: int = 0) -> Task | None:
    """Parse a single line from tasks.md.

    Returns None if the line is not a task line at all.
    Raises ParseError if the line looks like a task but is malformed.
    """
    stripped = line.strip()

    # Not a list item — skip silently
    if not stripped.startswith("- "):
        return None

    # Looks like a task checkbox line — try to parse
    if "- [" in stripped:
        m = _TASK_LINE_RE.match(stripped)
        if not m:
            raise ParseError(line, "malformed task line")

        raw_status, rest = m.group(1), m.group(2)
        status = Status.OPEN if raw_status == "[ ]" else Status.DONE

        # Extract priority and date from the rest
        priority_matches = _PRIORITY_RE.findall(rest)
        if len(priority_matches) > 1:
            logger.debug("Duplicate /p: tag on line %d; using last", line_number)
        priority = Priority(priority_matches[-1].capitalize()) if priority_matches else Priority.MEDIUM

        date_matches = _DATE_RE.findall(rest)
        if len(date_matches) > 1:
            logger.debug("Duplicate /d: tag on line %d; using last", line_number)

        due: date | None = None
        if date_matches:
            due = resolve_date(date_matches[-1])

        # Strip tags to get description
        cleaned = _PRIORITY_RE.sub("", rest)
        cleaned = _DATE_RE.sub("", cleaned)
        description = " ".join(cleaned.split())

        return Task(
            description=description,
            status=status,
            priority=priority,
            due=due,
            line_number=line_number,
        )

    # Plain list item, not a task — skip silently
    return None


def serialise_task(task: Task) -> str:
    """Serialise a Task to a tasks.md line."""
    parts = [f"- {task.status.value} {task.description}"]

    if task.priority != Priority.MEDIUM:
        parts.append(f"/p:{task.priority.value}")

    if task.due is not None:
        parts.append(f"/d:{task.due.isoformat()}")

    return " ".join(parts)
