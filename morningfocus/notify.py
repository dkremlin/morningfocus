#!/usr/bin/env python3
"""Standalone cron notification script for MorningFocus.

Usage:
    python notify.py
    python notify.py --dry-run

Allowed imports: morningfocus.config, morningfocus.storage, morningfocus.briefing only.
Never imports cli, typer, or rich.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from morningfocus.briefing import classify_tasks
from morningfocus.config import get_tasks_path
from morningfocus.storage import load_tasks

_LOG_PATH = Path.home() / ".local" / "share" / "morningfocus" / "notify.log"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _fallback_log(title: str, message: str) -> None:
    """Write notification to log file when desktop notification fails."""
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG_PATH, "a", encoding="utf-8") as fh:
        from datetime import datetime
        fh.write(f"[{datetime.now().isoformat()}] {title}: {message}\n")
    logger.info("Notification written to %s", _LOG_PATH)


def send_notification(title: str, message: str, dry_run: bool = False) -> None:
    """Send a desktop notification, falling back to log file on failure."""
    if dry_run:
        print(f"[DRY RUN] {title}: {message}")
        return

    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="MorningFocus",
            timeout=10,
        )
    except Exception as exc:
        logger.warning("Desktop notification failed (%s); falling back to log.", exc)
        _fallback_log(title, message)


def main() -> int:
    parser = argparse.ArgumentParser(description="MorningFocus cron notifier")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print notification instead of sending it",
    )
    args = parser.parse_args()

    path = get_tasks_path()
    try:
        tasks = load_tasks(path)
    except Exception as exc:
        logger.error("Failed to load tasks: %s", exc)
        return 1

    today = date.today()
    result = classify_tasks(tasks, today=today)

    title = "Morning Focus Briefing"
    message = (
        f"You have {len(result.today)} task(s) due today "
        f"and {len(result.overdue)} overdue task(s)."
    )

    send_notification(title, message, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
