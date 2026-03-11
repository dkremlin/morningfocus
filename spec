# Specification: MorningFocus (CLI Task & Note Manager)

## 1. Overview
MorningFocus is a local CLI application designed to help users manage personal tasks and notes. It uses a human-readable Markdown file (`tasks.md`) as its primary database. The goal is to provide a quick way to capture tasks and receive a "Daily Briefing" of what remains.

## 2. Technical Stack
- **Language:** Python 3.10+ (or Node.js)
- **Data Storage:** `data/tasks.md`
- **Core Libraries (Suggested):** - `rich` (for beautiful CLI tables)
    - `python-dateutil` (for natural language date parsing like "tomorrow")
    - `plyer` (for cross-platform desktop notifications)

---

## 3. Data Schema: `tasks.md`
The file must follow standard Markdown list syntax so it remains readable in any text editor.

**Format:** `- [status] Task Description /p:[Priority] /d:[YYYY-MM-DD]`

- **Status:** `[ ]` for Open, `[x]` for Done.
- **Priority:** `High`, `Medium`, `Low` (Default: `Medium`).
- **Due Date:** $YYYY-MM-DD$ (Default: `None`).

---

## 4. Functional Requirements

### 4.1 CLI Commands
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `add` | `"Task String"` | Extracts metadata using regex and appends to the file. |
| `list` | `--open` / `--all` | Displays a formatted table of tasks from the file. |
| `done` | `[index]` | Finds the $n^{th}$ task and changes `[ ]` to `[x]`. |
| `brief` | None | Scans the file and prints a summary for the current day. |

### 4.2 Parsing Logic
The `add` command must be able to parse tags within the string:
- **Priority Tag:** `/p:High` (case insensitive).
- **Date Tag:** `/d:2026-03-12` or `/d:tomorrow`.
- **Logic:** If tags are missing, use defaults. If "tomorrow" is used, calculate the date based on `today()`.

### 4.3 Morning Briefing Logic
When the `brief` command is triggered, the app must filter the Markdown file for:
1. **Overdue:** Tasks with a date < `today` and status `[ ]`.
2. **Today:** Tasks with a date == `today` and status `[ ]`.
3. **General:** Open tasks with no due date.

---

## 5. Automation (The "Morning" Part)
- Create a standalone script `notify.py` that can be called by a system scheduler (Cron/Task Scheduler).
- This script should trigger a desktop notification:
    - **Title:** "Morning Focus Briefing"
    - **Message:** "You have X tasks due today and Y overdue tasks."

---

## 6. Implementation Plan for Claude Code
1. **Phase 1:** Create `data/tasks.md` and implement the `add` parser.
2.