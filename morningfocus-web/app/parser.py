"""Parse free-text add strings (tag extraction, date resolution).

Adapted from the CLI app's parser — same rules, no dependencies on cli/storage.
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta

from dateutil import parser as dateutil_parser

from app.schemas import ParseResult, Priority

logger = logging.getLogger(__name__)

_PRIORITY_RE = re.compile(r"(?<!\S)/p:(High|Medium|Low)\b", re.IGNORECASE)
_DATE_RE = re.compile(r"(?<!\S)/d:(\S+)")


def resolve_date(date_str: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()
    normalized = date_str.strip().lower()
    if normalized == "today":
        return today
    if normalized == "tomorrow":
        return today + timedelta(days=1)
    try:
        return dateutil_parser.parse(date_str).date()
    except (ValueError, OverflowError, TypeError):
        raise ValueError(f"Cannot parse date '{date_str}'. Try YYYY-MM-DD or 'tomorrow'.")


def parse_add_string(raw: str, today: date | None = None) -> ParseResult:
    priority_matches = _PRIORITY_RE.findall(raw)
    priority: Priority = priority_matches[-1].capitalize() if priority_matches else "Medium"  # type: ignore[assignment]

    date_matches = _DATE_RE.findall(raw)
    due: date | None = None
    if date_matches:
        due = resolve_date(date_matches[-1], today=today)

    cleaned = _PRIORITY_RE.sub("", raw)
    cleaned = _DATE_RE.sub("", cleaned)
    description = " ".join(cleaned.split())

    if not description:
        raise ValueError("Description is empty after removing tags.")

    return ParseResult(description=description, priority=priority, due=due)
