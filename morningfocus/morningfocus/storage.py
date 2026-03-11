"""File I/O, locking, and atomic writes for MorningFocus."""

from __future__ import annotations

import fcntl
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from morningfocus.exceptions import LockTimeoutError, ReadOnlyError, TaskNotFoundError
from morningfocus.models import Status, Task
from morningfocus.parser import parse_line, serialise_task


_LOCK_TIMEOUT = 5.0
_LOCK_POLL = 0.1


@contextmanager
def _locked_file(
    path: Path, exclusive: bool = True
) -> Generator[None, None, None]:
    """Context manager that holds an fcntl lock on the tasks file.

    Raises ReadOnlyError if the file (or its parent) is not writable when
    an exclusive lock is requested. Raises LockTimeoutError after 5 s.
    """
    if exclusive and path.exists() and not os.access(path, os.W_OK):
        raise ReadOnlyError()

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    mode = "a+" if exclusive else "r"
    try:
        fh = open(path, mode)
    except PermissionError:
        raise ReadOnlyError()

    lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH

    deadline = time.monotonic() + _LOCK_TIMEOUT
    while True:
        try:
            fcntl.flock(fh, lock_type | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                fh.close()
                raise LockTimeoutError()
            time.sleep(_LOCK_POLL)

    try:
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


def load_tasks(path: Path) -> list[Task]:
    """Read tasks.md and return all parsed tasks.

    Returns an empty list if the file does not exist.
    Malformed non-task lines are silently skipped.
    Lines matching '- [' that fail parsing raise ParseError.
    """
    if not path.exists():
        return []

    tasks: list[Task] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            task = parse_line(line, line_number=lineno)
            if task is not None:
                tasks.append(task)
    return tasks


def _save_tasks(path: Path, tasks: list[Task]) -> None:
    """Atomically write tasks to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            for task in tasks:
                fh.write(serialise_task(task) + "\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def append_task(task: Task, path: Path) -> None:
    """Append a single task to tasks.md (exclusive lock)."""
    with _locked_file(path, exclusive=True):
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(serialise_task(task) + "\n")
        except PermissionError:
            raise ReadOnlyError()


def mark_done(index: int, path: Path) -> Task:
    """Mark the n-th open task (1-based) as done.

    Re-reads the file inside the exclusive lock to avoid TOCTOU.
    Raises TaskNotFoundError if index is out of range.
    """
    with _locked_file(path, exclusive=True):
        all_tasks = load_tasks(path)
        open_tasks = [t for t in all_tasks if t.status == Status.OPEN]

        if index < 1 or index > len(open_tasks):
            raise TaskNotFoundError(index, len(open_tasks))

        target = open_tasks[index - 1]
        target.status = Status.DONE
        _save_tasks(path, all_tasks)
        return target
