"""Tests for morningfocus.parser."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from morningfocus.exceptions import InvalidDateError, ParseError
from morningfocus.models import Priority, Status
from morningfocus.parser import (
    parse_add_string,
    parse_line,
    resolve_date,
    serialise_task,
)
from morningfocus.models import Task


TODAY = date(2026, 3, 11)


# ---------------------------------------------------------------------------
# resolve_date
# ---------------------------------------------------------------------------

class TestResolveDate:
    def test_iso_format(self):
        assert resolve_date("2026-03-15", today=TODAY) == date(2026, 3, 15)

    def test_tomorrow(self):
        assert resolve_date("tomorrow", today=TODAY) == TODAY + timedelta(days=1)

    def test_today(self):
        assert resolve_date("today", today=TODAY) == TODAY

    def test_natural_language(self):
        result = resolve_date("March 20 2026", today=TODAY)
        assert result == date(2026, 3, 20)

    def test_invalid_raises(self):
        with pytest.raises(InvalidDateError) as exc_info:
            resolve_date("not-a-date", today=TODAY)
        assert "not-a-date" in str(exc_info.value)


# ---------------------------------------------------------------------------
# parse_add_string
# ---------------------------------------------------------------------------

class TestParseAddString:
    def test_simple_description(self):
        task = parse_add_string("Buy milk", today=TODAY)
        assert task.description == "Buy milk"
        assert task.priority == Priority.MEDIUM
        assert task.due is None

    def test_priority_high(self):
        task = parse_add_string("Fix bug /p:High", today=TODAY)
        assert task.priority == Priority.HIGH
        assert task.description == "Fix bug"

    def test_priority_case_insensitive(self):
        task = parse_add_string("Fix bug /p:high", today=TODAY)
        assert task.priority == Priority.HIGH

    def test_priority_low(self):
        task = parse_add_string("/p:Low Write docs", today=TODAY)
        assert task.priority == Priority.LOW
        assert task.description == "Write docs"

    def test_date_iso(self):
        task = parse_add_string("Meeting /d:2026-03-15", today=TODAY)
        assert task.due == date(2026, 3, 15)

    def test_date_tomorrow(self):
        task = parse_add_string("Call /d:tomorrow", today=TODAY)
        assert task.due == TODAY + timedelta(days=1)

    def test_tag_in_middle(self):
        task = parse_add_string("Fix /p:High login bug", today=TODAY)
        assert task.priority == Priority.HIGH
        assert task.description == "Fix login bug"

    def test_both_tags(self):
        task = parse_add_string("Deploy /p:High /d:2026-03-15", today=TODAY)
        assert task.priority == Priority.HIGH
        assert task.due == date(2026, 3, 15)
        assert task.description == "Deploy"

    def test_duplicate_priority_last_wins(self):
        task = parse_add_string("Task /p:High /p:Low", today=TODAY)
        assert task.priority == Priority.LOW

    def test_duplicate_date_last_wins(self):
        task = parse_add_string("Task /d:2026-03-10 /d:2026-03-20", today=TODAY)
        assert task.due == date(2026, 3, 20)

    def test_strips_tags_anywhere(self):
        task = parse_add_string("/p:High Do something important /d:tomorrow", today=TODAY)
        assert "/p:" not in task.description
        assert "/d:" not in task.description

    def test_invalid_date_raises(self):
        with pytest.raises(InvalidDateError):
            parse_add_string("Task /d:notadate", today=TODAY)

    def test_empty_description_after_extraction_raises(self):
        with pytest.raises(ParseError):
            parse_add_string("/p:High /d:tomorrow", today=TODAY)


# ---------------------------------------------------------------------------
# parse_line
# ---------------------------------------------------------------------------

class TestParseLine:
    def test_open_task(self):
        task = parse_line("- [ ] Buy milk", line_number=1)
        assert task is not None
        assert task.status == Status.OPEN
        assert task.description == "Buy milk"

    def test_done_task(self):
        task = parse_line("- [x] Buy milk", line_number=1)
        assert task is not None
        assert task.status == Status.DONE

    def test_non_task_line_returns_none(self):
        assert parse_line("# Heading") is None
        assert parse_line("Some text") is None
        assert parse_line("- plain list item") is None

    def test_empty_line_returns_none(self):
        assert parse_line("") is None
        assert parse_line("\n") is None

    def test_malformed_task_raises(self):
        with pytest.raises(ParseError):
            parse_line("- [?] Bad status task")

    def test_priority_parsed(self):
        task = parse_line("- [ ] Fix bug /p:High", line_number=2)
        assert task is not None
        assert task.priority == Priority.HIGH

    def test_date_parsed(self):
        task = parse_line("- [ ] Meeting /d:2026-03-15", line_number=3)
        assert task is not None
        assert task.due == date(2026, 3, 15)

    def test_line_number_stored(self):
        task = parse_line("- [ ] Task", line_number=42)
        assert task is not None
        assert task.line_number == 42


# ---------------------------------------------------------------------------
# serialise_task
# ---------------------------------------------------------------------------

class TestSerialiseTask:
    def test_minimal(self):
        task = Task(description="Buy milk")
        line = serialise_task(task)
        assert line == "- [ ] Buy milk"

    def test_with_high_priority(self):
        task = Task(description="Fix bug", priority=Priority.HIGH)
        line = serialise_task(task)
        assert "/p:High" in line

    def test_medium_priority_not_serialised(self):
        task = Task(description="Task", priority=Priority.MEDIUM)
        line = serialise_task(task)
        assert "/p:" not in line

    def test_with_due_date(self):
        task = Task(description="Meeting", due=date(2026, 3, 15))
        line = serialise_task(task)
        assert "/d:2026-03-15" in line

    def test_done_status(self):
        task = Task(description="Done task", status=Status.DONE)
        line = serialise_task(task)
        assert "- [x]" in line

    def test_roundtrip(self):
        task = Task(
            description="Deploy app",
            priority=Priority.HIGH,
            due=date(2026, 3, 15),
        )
        line = serialise_task(task)
        parsed = parse_line(line, line_number=1)
        assert parsed is not None
        assert parsed.description == task.description
        assert parsed.priority == task.priority
        assert parsed.due == task.due
        assert parsed.status == task.status

    def test_roundtrip_low_priority(self):
        task = Task(description="Low prio task", priority=Priority.LOW)
        line = serialise_task(task)
        parsed = parse_line(line, line_number=1)
        assert parsed is not None
        assert parsed.priority == Priority.LOW
