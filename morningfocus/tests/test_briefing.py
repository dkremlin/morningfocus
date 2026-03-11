"""Tests for morningfocus.briefing."""

from __future__ import annotations

from datetime import date, timedelta

from morningfocus.briefing import classify_tasks
from morningfocus.models import Priority, Status, Task


TODAY = date(2026, 3, 11)
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)


def _open(desc: str, due: date | None = None, priority: Priority = Priority.MEDIUM) -> Task:
    return Task(description=desc, due=due, priority=priority)


def _done(desc: str, due: date | None = None) -> Task:
    return Task(description=desc, status=Status.DONE, due=due)


class TestClassifyTasks:
    def test_empty_list(self):
        result = classify_tasks([], today=TODAY)
        assert result.overdue == []
        assert result.today == []
        assert result.general == []

    def test_overdue_task(self):
        result = classify_tasks([_open("Old task", due=YESTERDAY)], today=TODAY)
        assert len(result.overdue) == 1
        assert result.overdue[0].description == "Old task"

    def test_today_task(self):
        result = classify_tasks([_open("Today task", due=TODAY)], today=TODAY)
        assert len(result.today) == 1

    def test_future_task_not_included(self):
        result = classify_tasks([_open("Future task", due=TOMORROW)], today=TODAY)
        assert result.total_open == 0

    def test_general_task_no_due(self):
        result = classify_tasks([_open("No deadline")], today=TODAY)
        assert len(result.general) == 1

    def test_done_tasks_excluded(self):
        result = classify_tasks(
            [_done("Done overdue", due=YESTERDAY), _done("Done today", due=TODAY)],
            today=TODAY,
        )
        assert result.total_open == 0

    def test_mixed_tasks(self):
        tasks = [
            _open("Overdue", due=YESTERDAY),
            _open("Today", due=TODAY),
            _open("Future", due=TOMORROW),
            _open("General"),
            _done("Already done"),
        ]
        result = classify_tasks(tasks, today=TODAY)
        assert len(result.overdue) == 1
        assert len(result.today) == 1
        assert len(result.general) == 1
        assert result.total_open == 3

    def test_has_overdue_property(self):
        result = classify_tasks([_open("Old", due=YESTERDAY)], today=TODAY)
        assert result.has_overdue is True

    def test_has_overdue_false_when_none(self):
        result = classify_tasks([_open("Today", due=TODAY)], today=TODAY)
        assert result.has_overdue is False

    def test_total_open_count(self):
        tasks = [
            _open("A", due=YESTERDAY),
            _open("B", due=TODAY),
            _open("C"),
        ]
        result = classify_tasks(tasks, today=TODAY)
        assert result.total_open == 3
