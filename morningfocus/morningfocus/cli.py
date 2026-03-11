"""CLI entry point for MorningFocus."""

from __future__ import annotations

import json
import sys
from datetime import date
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from morningfocus import __version__
from morningfocus.briefing import classify_tasks
from morningfocus.config import get_tasks_path
from morningfocus.exceptions import (
    InvalidDateError,
    LockTimeoutError,
    ParseError,
    ReadOnlyError,
    TaskNotFoundError,
)
from morningfocus.models import Priority, Status, Task
from morningfocus.parser import parse_add_string
from morningfocus.storage import append_task, load_tasks, mark_done

app = typer.Typer(
    name="mf",
    help="MorningFocus — local CLI task manager",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)

_PRIORITY_COLORS = {
    Priority.HIGH: "red",
    Priority.MEDIUM: "yellow",
    Priority.LOW: "green",
}


def _priority_styled(priority: Priority) -> str:
    color = _PRIORITY_COLORS[priority]
    return f"[{color}]{priority.value}[/{color}]"


def _due_styled(due: date | None, today: date | None = None) -> str:
    if due is None:
        return ""
    if today is None:
        today = date.today()
    if due < today:
        return f"[red]{due.isoformat()}[/red]"
    if due == today:
        return f"[yellow]{due.isoformat()}[/yellow]"
    return due.isoformat()


@app.command()
def add(
    task_string: Annotated[str, typer.Argument(help="Task description with optional /p: and /d: tags")],
) -> None:
    """Add a new task."""
    path = get_tasks_path()
    try:
        task = parse_add_string(task_string)
    except InvalidDateError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ParseError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    try:
        append_task(task, path)
    except ReadOnlyError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(2)
    except LockTimeoutError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(2)

    console.print(f"[green]Added:[/green] {task.description}")


@app.command(name="list")
def list_tasks(
    open_only: bool = typer.Option(False, "--open/--no-open", help="Show only open tasks"),
    all_tasks: bool = typer.Option(False, "--all/--no-all", help="Show all tasks"),
    sort_by: Optional[str] = typer.Option(None, "--sort", help="Sort by: priority or due"),
) -> None:
    """List tasks."""
    path = get_tasks_path()

    try:
        tasks = load_tasks(path)
    except ReadOnlyError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(2)

    if not tasks:
        console.print("No tasks yet.")
        return

    # Default: show open tasks unless --all is specified
    if all_tasks:
        filtered = tasks
    else:
        filtered = [t for t in tasks if t.status == Status.OPEN]

    if not filtered:
        console.print("No open tasks." if not all_tasks else "No tasks yet.")
        return

    if sort_by == "priority":
        order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        filtered = sorted(filtered, key=lambda t: order[t.priority])
    elif sort_by == "due":
        filtered = sorted(filtered, key=lambda t: (t.due is None, t.due))

    today = date.today()
    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Status", width=6)
    table.add_column("Description")
    table.add_column("Priority", width=8)
    table.add_column("Due", width=12)

    # Number open tasks starting at 1 (for done command)
    open_counter = 0
    for task in filtered:
        if task.status == Status.OPEN:
            open_counter += 1
            idx = str(open_counter)
        else:
            idx = "-"

        status_icon = "[ ]" if task.status == Status.OPEN else "[x]"
        table.add_row(
            idx,
            status_icon,
            task.description,
            _priority_styled(task.priority),
            _due_styled(task.due, today),
        )

    console.print(table)


@app.command()
def done(
    index: Annotated[int, typer.Argument(help="1-based index of the open task to mark done")],
) -> None:
    """Mark an open task as done."""
    path = get_tasks_path()

    try:
        task = mark_done(index, path)
    except TaskNotFoundError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ReadOnlyError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(2)
    except LockTimeoutError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(2)

    console.print(f"[green]Done:[/green] {task.description}")


@app.command()
def brief(
    as_json: bool = typer.Option(False, "--json/--no-json", help="Output as machine-readable JSON"),
    exit_nonzero: bool = typer.Option(False, "--exit-nonzero/--no-exit-nonzero", help="Exit 1 if any overdue tasks"),
) -> None:
    """Print a morning briefing summary."""
    path = get_tasks_path()

    try:
        tasks = load_tasks(path)
    except ReadOnlyError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(2)

    today = date.today()
    result = classify_tasks(tasks, today=today)

    if as_json:
        def task_to_dict(t: Task) -> dict:
            return {
                "description": t.description,
                "priority": t.priority.value,
                "due": t.due.isoformat() if t.due else None,
                "status": "open" if t.status == Status.OPEN else "done",
            }

        output = {
            "date": today.isoformat(),
            "overdue": [task_to_dict(t) for t in result.overdue],
            "today": [task_to_dict(t) for t in result.today],
            "general": [task_to_dict(t) for t in result.general],
        }
        print(json.dumps(output, indent=2))
        raise typer.Exit(0)

    # Rich human output
    if result.total_open == 0:
        console.print("[green]All clear — no open tasks for today![/green]")
    else:
        console.print(f"[bold]Morning Briefing — {today.isoformat()}[/bold]\n")

        if result.overdue:
            table = Table(title="Overdue", box=box.SIMPLE, title_style="bold red")
            _add_task_columns(table)
            for t in result.overdue:
                _add_task_row(table, t, today)
            console.print(table)

        if result.today:
            table = Table(title="Due Today", box=box.SIMPLE, title_style="bold yellow")
            _add_task_columns(table)
            for t in result.today:
                _add_task_row(table, t, today)
            console.print(table)

        if result.general:
            table = Table(title="General (no due date)", box=box.SIMPLE, title_style="bold blue")
            _add_task_columns(table)
            for t in result.general:
                _add_task_row(table, t, today)
            console.print(table)

    if exit_nonzero and result.has_overdue:
        raise typer.Exit(1)


def _add_task_columns(table: Table) -> None:
    table.add_column("Description")
    table.add_column("Priority", width=8)
    table.add_column("Due", width=12)


def _add_task_row(table: Table, task: Task, today: date) -> None:
    table.add_row(
        task.description,
        _priority_styled(task.priority),
        _due_styled(task.due, today),
    )


def version_callback(value: bool) -> None:
    if value:
        print(f"mf version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """MorningFocus — local CLI task manager."""


if __name__ == "__main__":
    app()
