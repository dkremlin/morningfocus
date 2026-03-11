"""Tests for morningfocus.cli using Typer's CliRunner."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from morningfocus.cli import app

runner = CliRunner(mix_stderr=False)


def _run(args: list[str], data_dir: Path) -> any:
    return runner.invoke(app, args, env={"MORNINGFOCUS_DATA_DIR": str(data_dir)})


class TestAddCommand:
    def test_add_simple(self, tmp_path: Path):
        result = _run(["add", "Buy milk"], tmp_path)
        assert result.exit_code == 0
        assert "Buy milk" in result.stdout

    def test_add_creates_file(self, tmp_path: Path):
        _run(["add", "Buy milk"], tmp_path)
        assert (tmp_path / "tasks.md").exists()

    def test_add_with_priority(self, tmp_path: Path):
        _run(["add", "Fix bug /p:High"], tmp_path)
        content = (tmp_path / "tasks.md").read_text()
        assert "/p:High" in content

    def test_add_with_date(self, tmp_path: Path):
        _run(["add", "Meeting /d:2026-03-15"], tmp_path)
        content = (tmp_path / "tasks.md").read_text()
        assert "/d:2026-03-15" in content

    def test_add_invalid_date_exits_1(self, tmp_path: Path):
        result = _run(["add", "Task /d:notadate"], tmp_path)
        assert result.exit_code == 1


class TestListCommand:
    def test_list_empty(self, tmp_path: Path):
        result = _run(["list"], tmp_path)
        assert result.exit_code == 0
        assert "No tasks" in result.stdout

    def test_list_shows_tasks(self, tmp_path: Path):
        _run(["add", "Task one"], tmp_path)
        _run(["add", "Task two"], tmp_path)
        result = _run(["list"], tmp_path)
        assert "Task one" in result.stdout
        assert "Task two" in result.stdout

    def test_list_open_hides_done(self, tmp_path: Path):
        _run(["add", "Task one"], tmp_path)
        _run(["add", "Task two"], tmp_path)
        _run(["done", "1"], tmp_path)
        result = _run(["list", "--open"], tmp_path)
        assert "Task two" in result.stdout
        # Task one is done — should not appear
        assert result.stdout.count("Task") == 1

    def test_list_all_shows_done(self, tmp_path: Path):
        _run(["add", "Task one"], tmp_path)
        _run(["done", "1"], tmp_path)
        result = _run(["list", "--all"], tmp_path)
        assert "Task one" in result.stdout


class TestDoneCommand:
    def test_done_marks_task(self, tmp_path: Path):
        _run(["add", "Task one"], tmp_path)
        result = _run(["done", "1"], tmp_path)
        assert result.exit_code == 0

        result2 = _run(["list", "--open"], tmp_path)
        assert "No open tasks" in result2.stdout or "Task one" not in result2.stdout

    def test_done_out_of_range_exits_1(self, tmp_path: Path):
        _run(["add", "Task one"], tmp_path)
        result = _run(["done", "99"], tmp_path)
        assert result.exit_code == 1

    def test_done_empty_file_exits_1(self, tmp_path: Path):
        result = _run(["done", "1"], tmp_path)
        assert result.exit_code == 1


class TestBriefCommand:
    def test_brief_empty(self, tmp_path: Path):
        result = _run(["brief"], tmp_path)
        assert result.exit_code == 0

    def test_brief_json_valid(self, tmp_path: Path):
        _run(["add", "Task /p:High"], tmp_path)
        result = _run(["brief", "--json"], tmp_path)
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "overdue" in data
        assert "today" in data
        assert "general" in data
        assert "date" in data

    def test_brief_json_general_task(self, tmp_path: Path):
        _run(["add", "No due date task"], tmp_path)
        result = _run(["brief", "--json"], tmp_path)
        data = json.loads(result.stdout)
        assert len(data["general"]) == 1
        assert data["general"][0]["description"] == "No due date task"

    def test_brief_exit_nonzero_when_overdue(self, tmp_path: Path):
        # Add a task with a past date
        (tmp_path / "tasks.md").write_text("- [ ] Overdue task /d:2020-01-01\n")
        result = _run(["brief", "--exit-nonzero"], tmp_path)
        assert result.exit_code == 1

    def test_brief_exit_nonzero_no_overdue(self, tmp_path: Path):
        _run(["add", "No due date task"], tmp_path)
        result = _run(["brief", "--exit-nonzero"], tmp_path)
        assert result.exit_code == 0
