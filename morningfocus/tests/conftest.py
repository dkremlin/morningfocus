"""Shared pytest fixtures for MorningFocus tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tasks_path(tmp_path: Path) -> Path:
    """Return a temporary path for tasks.md."""
    return tmp_path / "tasks.md"
