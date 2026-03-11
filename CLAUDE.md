# Claude Code Project Notes

## Project: MorningFocus

Two versions of a local task manager:

| Folder | What it is |
|--------|-----------|
| `morningfocus/` | CLI version — Typer + Rich, stores tasks in `tasks.md` |
| `morningfocus-web/` | Web UI version — FastAPI + SQLite, runs in the browser |
| `spec` | Original specification |

## Python environment

- Python 3.9 (system: `/Library/Developer/CommandLineTools/usr/bin/python3`)
- pip3 at `/Users/davidk/Library/Python/3.9/bin/pip`

## Running the CLI

```bash
cd morningfocus
pip3 install -e ".[dev]"
mf add "Buy milk /p:Low"
mf list --open
mf done 1
mf brief --json
python notify.py --dry-run
```

## Running the Web UI

```bash
cd morningfocus-web
pip3 install -e "."
python3 -m uvicorn app.main:app --reload --port 8000
# Open http://localhost:8000
```

## Running tests (CLI)

```bash
cd morningfocus
/Users/davidk/Library/Python/3.9/bin/pytest tests/ --cov=morningfocus
# 77 tests, ~85% coverage
```

## Key conventions

- Architecture documented in `morningfocus/plan.md`
- `.env` files are gitignored — never commit secrets
- Local data (`tasks.md`, `tasks.db`) are gitignored
- `data/.gitkeep` keeps the data directory tracked
