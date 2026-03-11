"""Tests for morningfocus.storage."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from morningfocus.exceptions import TaskNotFoundError
from morningfocus.models import Priority, Status, Task
from morningfocus.storage import append_task, load_tasks, mark_done


def _make_task(desc: str, **kwargs) -> Task:
    return Task(description=desc, **kwargs)


class TestLoadTasks:
    def test_absent_file_returns_empty(self, tasks_path: Path):
        assert load_tasks(tasks_path) == []

    def test_loads_open_task(self, tasks_path: Path):
        tasks_path.write_text("- [ ] Buy milk\n")
        tasks = load_tasks(tasks_path)
        assert len(tasks) == 1
        assert tasks[0].description == "Buy milk"
        assert tasks[0].status == Status.OPEN

    def test_loads_done_task(self, tasks_path: Path):
        tasks_path.write_text("- [x] Buy milk\n")
        tasks = load_tasks(tasks_path)
        assert tasks[0].status == Status.DONE

    def test_skips_non_task_lines(self, tasks_path: Path):
        tasks_path.write_text("# Heading\nSome text\n- [ ] Real task\n")
        tasks = load_tasks(tasks_path)
        assert len(tasks) == 1

    def test_multiple_tasks(self, tasks_path: Path):
        tasks_path.write_text(
            "- [ ] Task one\n- [x] Task two\n- [ ] Task three /p:High\n"
        )
        tasks = load_tasks(tasks_path)
        assert len(tasks) == 3
        assert tasks[2].priority == Priority.HIGH


class TestAppendTask:
    def test_creates_file_if_absent(self, tasks_path: Path):
        task = _make_task("New task")
        append_task(task, tasks_path)
        assert tasks_path.exists()

    def test_appends_to_existing(self, tasks_path: Path):
        tasks_path.write_text("- [ ] Existing task\n")
        append_task(_make_task("New task"), tasks_path)
        tasks = load_tasks(tasks_path)
        assert len(tasks) == 2

    def test_task_content_correct(self, tasks_path: Path):
        task = _make_task("Buy milk", priority=Priority.HIGH, due=date(2026, 3, 15))
        append_task(task, tasks_path)
        tasks = load_tasks(tasks_path)
        assert tasks[0].description == "Buy milk"
        assert tasks[0].priority == Priority.HIGH
        assert tasks[0].due == date(2026, 3, 15)


class TestMarkDone:
    def test_marks_first_open_task(self, tasks_path: Path):
        tasks_path.write_text("- [ ] Task one\n- [ ] Task two\n")
        mark_done(1, tasks_path)
        tasks = load_tasks(tasks_path)
        assert tasks[0].status == Status.DONE
        assert tasks[1].status == Status.OPEN

    def test_marks_second_open_task(self, tasks_path: Path):
        tasks_path.write_text("- [ ] Task one\n- [ ] Task two\n")
        mark_done(2, tasks_path)
        tasks = load_tasks(tasks_path)
        assert tasks[0].status == Status.OPEN
        assert tasks[1].status == Status.DONE

    def test_skips_done_tasks_in_index(self, tasks_path: Path):
        tasks_path.write_text("- [x] Already done\n- [ ] Open task\n")
        mark_done(1, tasks_path)
        tasks = load_tasks(tasks_path)
        assert tasks[1].status == Status.DONE

    def test_out_of_range_raises(self, tasks_path: Path):
        tasks_path.write_text("- [ ] Task one\n- [ ] Task two\n- [ ] Task three\n")
        with pytest.raises(TaskNotFoundError) as exc_info:
            mark_done(99, tasks_path)
        assert exc_info.value.index == 99
        assert exc_info.value.total_open == 3

    def test_zero_index_raises(self, tasks_path: Path):
        tasks_path.write_text("- [ ] Task one\n")
        with pytest.raises(TaskNotFoundError):
            mark_done(0, tasks_path)

    def test_negative_index_raises(self, tasks_path: Path):
        tasks_path.write_text("- [ ] Task one\n")
        with pytest.raises(TaskNotFoundError):
            mark_done(-1, tasks_path)

    def test_empty_file_raises(self, tasks_path: Path):
        tasks_path.write_text("")
        with pytest.raises(TaskNotFoundError) as exc_info:
            mark_done(1, tasks_path)
        assert exc_info.value.total_open == 0

    def test_preserves_done_tasks(self, tasks_path: Path):
        tasks_path.write_text("- [x] Done already\n- [ ] Open\n")
        mark_done(1, tasks_path)
        tasks = load_tasks(tasks_path)
        assert tasks[0].status == Status.DONE
        assert tasks[1].status == Status.DONE

    def test_returns_completed_task(self, tasks_path: Path):
        tasks_path.write_text("- [ ] Buy milk /p:High\n")
        task = mark_done(1, tasks_path)
        assert task.description == "Buy milk"
        assert task.status == Status.DONE
