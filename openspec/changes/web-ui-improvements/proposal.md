## Why

The morningfocus-web version provides a browser UI but currently offers only basic task CRUD. Users who prefer a visual interface miss key features already available in the CLI — priority filtering, briefing view, and due-date awareness — making the web app feel incomplete compared to the terminal version.

## What Changes

- Add a **Dashboard / Briefing view** to the web UI showing Overdue, Today, and General task buckets (mirrors `mf brief`)
- Add **priority badge** display and **priority filter** to the task list
- Add **due date input** and display in the task form and list
- Add **"Mark done" toggle** directly in the task list (currently requires a separate action)
- Improve the overall **visual design**: status colours, responsive layout, empty-state messages

## Capabilities

### New Capabilities

- `briefing-view`: Dashboard page that classifies open tasks into Overdue / Today / General buckets, matching the CLI `mf brief` logic
- `task-priority-filter`: Filter the task list by priority (High / Medium / Low) via UI controls
- `task-due-date`: Due date field on task create/edit form; date displayed in list with overdue highlighting

### Modified Capabilities

- none

## Impact

- `morningfocus-web/app/` — routes, models, and templates updated
- `morningfocus-web/app/models.py` — ensure `priority` and `due_date` columns exist on the Task model
- `morningfocus-web/app/templates/` — HTML templates for list, form, and new dashboard page
- No changes to the CLI package or shared data format
- No new external dependencies expected (logic reuses existing SQLite + FastAPI)
