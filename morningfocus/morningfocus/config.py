"""XDG-aware path resolution for MorningFocus data files."""

from __future__ import annotations

import os
from pathlib import Path


def get_tasks_path() -> Path:
    """Return the path to tasks.md.

    Resolution order:
    1. MORNINGFOCUS_DATA_DIR env var
    2. $XDG_DATA_HOME/morningfocus/tasks.md
    3. ~/morningfocus/data/tasks.md
    """
    env_dir = os.environ.get("MORNINGFOCUS_DATA_DIR")
    if env_dir:
        return Path(env_dir) / "tasks.md"

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "morningfocus" / "tasks.md"

    return Path.home() / "morningfocus" / "data" / "tasks.md"
