"""Typed exception hierarchy for MorningFocus."""


class MorningFocusError(Exception):
    """Base exception for all MorningFocus errors."""


class ParseError(MorningFocusError):
    """Raised when a task line cannot be parsed."""

    def __init__(self, line: str, reason: str = "") -> None:
        self.line = line
        self.reason = reason
        msg = f"Cannot parse task line: {line!r}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)


class InvalidDateError(MorningFocusError):
    """Raised when a date string cannot be resolved."""

    def __init__(self, date_str: str) -> None:
        self.date_str = date_str
        super().__init__(
            f"cannot parse date '{date_str}'. Try YYYY-MM-DD or 'tomorrow'."
        )


class TaskNotFoundError(MorningFocusError):
    """Raised when a task index is out of range."""

    def __init__(self, index: int, total_open: int) -> None:
        self.index = index
        self.total_open = total_open
        super().__init__(
            f"no open task at index {index} ({total_open} open tasks)."
        )


class StorageError(MorningFocusError):
    """Raised for file I/O errors."""


class ReadOnlyError(StorageError):
    """Raised when tasks.md is read-only."""

    def __init__(self) -> None:
        super().__init__("tasks.md is read-only. Check file permissions.")


class LockTimeoutError(StorageError):
    """Raised when a file lock cannot be acquired."""

    def __init__(self) -> None:
        super().__init__("could not acquire lock after 5s.")
