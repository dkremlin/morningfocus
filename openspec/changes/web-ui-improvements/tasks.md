## 1. Backend — Partial Update Endpoint

- [x] 1.1 Add `TaskUpdate` Pydantic schema to `app/schemas.py` with optional fields `due` (date | None) and `priority` (str | None)
- [x] 1.2 Add `update_task(db, task_id, data)` function to `app/crud.py` that applies only the provided fields
- [x] 1.3 Add `PATCH /api/tasks/{task_id}` route to `app/main.py` calling `crud.update_task`, returning 404 if not found
- [x] 1.4 Test the PATCH endpoint manually: update a task's due date, clear it, and verify 404 for unknown IDs

## 2. Frontend — View Tab System

- [x] 2.1 Add a tab bar with "Tasks" and "Briefing" buttons above the existing content in `static/index.html`
- [x] 2.2 Wrap the existing task list section in a `<div id="viewTasks">` and add a new empty `<div id="viewBriefing">` section
- [x] 2.3 Implement `showView(name)` JS function that toggles `display` on the two view divs and updates the active tab style
- [x] 2.4 Wire the "Briefing" tab to call `loadBriefing()` on switch so data is always fresh

## 3. Frontend — Briefing Panel

- [x] 3.1 Add CSS styles for the briefing panel: three section cards (Overdue / Due Today / General) with appropriate colour accents matching existing priority colours
- [x] 3.2 Implement `renderBriefing(data)` JS function that generates HTML for each bucket, showing task description, priority badge, due date, and a done-toggle button
- [x] 3.3 Update `loadBriefing()` to populate `#viewBriefing` by calling `renderBriefing()` instead of only updating the chips bar
- [x] 3.4 Add empty-state message per bucket ("Nothing here") when a bucket has zero tasks
- [x] 3.5 Wire the done-toggle in the briefing panel to call `toggleDone()` and refresh the briefing view

## 4. Frontend — Priority Filter

- [x] 4.1 Add a `priorityFilter` state variable (default `'all'`) alongside the existing `filter` variable
- [x] 4.2 Add priority chip buttons (All / High / Medium / Low) to the filter bar in `static/index.html`
- [x] 4.3 Add CSS for active priority chip using the existing `--high`, `--med`, `--low` colour variables
- [x] 4.4 Implement `setPriorityFilter(p)` JS function that updates `priorityFilter` and calls `renderTasks()`
- [x] 4.5 Update `renderTasks()` to apply both `filter` (status) and `priorityFilter` dimensions before rendering

## 5. Frontend — Inline Due Date Edit

- [x] 5.1 Make the due date `<td>` cell clickable by adding an `onclick` that calls `editDue(taskId, currentDue)`
- [x] 5.2 Implement `editDue(id, current)` that replaces the cell content with a `<input type="date">` pre-filled with `current`
- [x] 5.3 On input `blur` or Enter keypress: call `PATCH /api/tasks/{id}` with `{ due: value || null }` then call `refreshAll()`
- [x] 5.4 On Escape keypress: restore the original cell content without making an API call
- [x] 5.5 Update the due date cell cursor style to `pointer` to indicate it is clickable
