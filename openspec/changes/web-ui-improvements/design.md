## Context

The morningfocus-web backend is feature-complete: `/api/brief`, `/api/tasks`, PATCH done/reopen, DELETE, and CSV/Markdown export are all working. The Task model already stores `priority`, `due`, and `done`. The frontend (`static/index.html`) is a single-page vanilla JS app with a dark theme, but it is missing three things:

1. **Briefing panel** — the briefing bar shows aggregate counts (chips) but never surfaces which tasks are overdue or due today. There is no way to see the task list segmented by urgency bucket.
2. **Priority filter** — the filter bar only toggles All / Open / Done. There is no way to filter by High / Medium / Low.
3. **Due date editing** — tasks can be created with a due date but it cannot be changed after creation (no edit support).

All changes are isolated to `static/index.html`. No backend changes are needed.

## Goals / Non-Goals

**Goals:**
- Add a "Briefing" view tab that groups open tasks into Overdue / Today / General sections, calling the existing `/api/brief` endpoint
- Add priority filter chips (High / Medium / Low / All) to the task list filter bar
- Add inline due-date editing on existing tasks via the existing PATCH endpoint or a new PATCH `/api/tasks/{id}` endpoint

**Non-Goals:**
- Redesigning the visual theme or overall layout
- Adding backend features (no new routes, models, or dependencies)
- Mobile-native app or PWA support
- Multi-user or sync features

## Decisions

### 1. Single-page view switching (Tasks tab ↔ Briefing tab)

Add a top-level tab bar with two views: **Tasks** (existing list) and **Briefing** (new grouped view). A JS `currentView` variable controls which section is visible (`display: none` toggling). This avoids any routing complexity while keeping all state in memory.

*Alternative considered: show briefing as a collapsible panel above the task list.* Rejected — it adds vertical bulk and the current briefing chips already summarize the data in the header position.

### 2. Priority filter as additional chips in the existing filter bar

Extend the existing `filter-bar` with a second row (or inline group) of priority chips: All / High / Medium / Low. The `renderTasks()` function gains a second filter dimension (`priorityFilter`). No API changes needed — filtering is client-side on the already-loaded `allTasks` array.

*Alternative: server-side filtering via `?priority=High` query param.* Rejected — all tasks are already loaded, client-side filtering is instant and avoids extra round-trips.

### 3. Inline due-date edit via a small popup or click-to-edit on the due cell

Clicking the due date cell opens a `<input type="date">` in place. On blur/Enter, the value is saved via `PATCH /api/tasks/{id}` with a `{ due: "YYYY-MM-DD" }` body. This requires one new backend endpoint: `PATCH /api/tasks/{id}` accepting a partial update payload.

*Alternative: edit modal dialog.* Rejected — over-engineered for a single field. Inline edit matches the existing "click to toggle done" interaction pattern.

## Risks / Trade-offs

- [Single HTML file size] As features grow, `index.html` becomes harder to maintain → Mitigation: keep JS well-commented and grouped by section; future work can split into modules.
- [New PATCH endpoint] Adding `PATCH /api/tasks/{id}` for partial updates expands the API surface → Mitigation: keep it minimal (only `due` and optionally `priority` fields accepted).
- [Client-side filter state] Two independent filter dimensions (status + priority) must be combined correctly in `renderTasks()` → Mitigation: use a single filter function that applies both dimensions in sequence.

## Migration Plan

1. Add `PATCH /api/tasks/{id}` to `app/main.py` and `crud.py`
2. Update `static/index.html` with the new view tab, priority filter, briefing panel, and inline edit
3. No database migration needed (columns already exist)
4. No breaking changes to existing API endpoints

## Open Questions

- Should the Briefing view also show a "Mark done" button per task, or is it read-only? (Recommendation: include it — matches the task list UX)
- Should priority filter default to "All" and persist in localStorage between page loads?
