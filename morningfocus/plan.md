# MorningFocus — Architecture & Implementation Plan

## What is this project?

**MorningFocus** is a local CLI task manager. You type a command in your terminal and it saves tasks to a simple text file (`tasks.md`) you can open in any editor. Each morning you run `mf brief` to see what's overdue or due today.

---

## Project Structure

```
morningfocus/
├── pyproject.toml          ← package config + dependencies
├── .env.example            ← example environment config
├── plan.md                 ← this file
├── notify.py               ← standalone cron script (no CLI framework)
├── data/
│   └── .gitkeep            ← tasks.md is stored here (gitignored)
├── morningfocus/           ← main Python package
│   ├── __init__.py         ← version
│   ├── exceptions.py       ← typed error hierarchy
│   ├── models.py           ← Task dataclass, Status/Priority enums
│   ├── config.py           ← where to find tasks.md (env var / XDG / home)
│   ├── parser.py           ← read & write individual task lines
│   ├── storage.py          ← file I/O with locking and atomic writes
│   ├── briefing.py         ← pure classification logic (overdue/today/general)
│   └── cli.py              ← four CLI commands using Typer + Rich
└── tests/
    ├── conftest.py         ← shared fixtures
    ├── test_parser.py      ← 35 tests
    ├── test_storage.py     ← 17 tests
    ├── test_briefing.py    ← 10 tests
    └── test_cli.py         ← 15 tests
```

---

## Key Decisions (Why things work the way they do)

### 1. `tasks.md` — human-readable storage
Every task is one line:
```
- [ ] Buy milk /p:Low
- [x] Fix login bug /p:High /d:2026-03-12
```
- `[ ]` = open, `[x]` = done
- `/p:High|Medium|Low` = priority (default Medium, not stored if Medium)
- `/d:YYYY-MM-DD` = due date (optional)

### 2. Parser — regex tag extraction
Tags are pulled out from anywhere in the string. After removing tags, the leftover text is the description. Duplicate tags → last one wins.

### 3. Storage — safe concurrent writes
- Every write is wrapped in an `fcntl` exclusive lock (prevents corruption if two terminals run at once)
- Writes go to a temp file first, then `os.replace()` swaps it in atomically (no half-written files)
- File is re-read inside the lock before marking done (no stale data)

### 4. `done` command — 1-based index into open tasks only
`mf list` shows open tasks numbered 1, 2, 3... `mf done 2` marks open task #2. Done tasks are skipped in the numbering.

### 5. `brief` buckets
| Bucket | Condition |
|--------|-----------|
| Overdue | due date < today, still open |
| Today | due date == today, still open |
| General | no due date, open |
| (Future tasks are not shown in the brief) |

### 6. `notify.py` — standalone, no CLI framework
Imports only `morningfocus.config`, `.storage`, `.briefing`. Uses `plyer` for desktop notifications; falls back to a log file if that fails. Safe to call from cron.

### 7. Config — where tasks.md lives
Resolution order:
1. `MORNINGFOCUS_DATA_DIR` env var → `$DIR/tasks.md`
2. `$XDG_DATA_HOME/morningfocus/tasks.md`
3. `~/morningfocus/data/tasks.md`

---

## CLI Commands

| Command | Example | What it does |
|---------|---------|--------------|
| `mf add` | `mf add "Fix bug /p:High /d:tomorrow"` | Parse tags, append to tasks.md |
| `mf list` | `mf list --open` / `mf list --all` | Show table of tasks |
| `mf done N` | `mf done 2` | Mark open task #N as done |
| `mf brief` | `mf brief --json` / `mf brief --exit-nonzero` | Morning summary |

---

## Error Handling

| Situation | Message | Exit code |
|-----------|---------|-----------|
| `done N` out of range | `Error: no open task at index N (M open tasks).` | 1 |
| tasks.md absent | Auto-create on `add`; others print "No tasks yet." | 0 |
| File read-only | `Error: tasks.md is read-only. Check file permissions.` | 2 |
| Lock timeout (5s) | `Error: could not acquire lock after 5s.` | 2 |
| Bad date string | `Error: cannot parse date 'X'. Try YYYY-MM-DD or 'tomorrow'.` | 1 |

---

## How to Install & Run

```bash
# From inside the morningfocus/ directory:
pip3 install -e ".[dev]"

# Use the CLI
mf add "Buy milk /p:Low"
mf add "Fix login bug /p:High /d:tomorrow"
mf list --open
mf done 1
mf list --all
mf brief
mf brief --json
python notify.py --dry-run
```

## How to Run Tests

```bash
pytest tests/ --cov=morningfocus
# 77 tests, 85% coverage
```

## Cron Setup (optional — the "morning" part)

Add this to your crontab (`crontab -e`) to get a desktop notification every morning at 8am:
```
0 8 * * * cd /path/to/morningfocus && python notify.py
```

---

## Implementation Phases Completed

- [x] **Phase 1** — Data layer: exceptions, models, parser, config, storage + tests
- [x] **Phase 2** — CLI commands: briefing, cli (Typer + Rich), pyproject.toml + tests
- [x] **Phase 3** — Automation: notify.py with plyer + log fallback + `--dry-run`
- [ ] **Phase 4** — Hardening (Windows lock compat, concurrency integration test)
