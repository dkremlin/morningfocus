## ADDED Requirements

### Requirement: Briefing view tab
The UI SHALL provide a "Briefing" tab alongside the existing "Tasks" tab. Clicking the tab SHALL switch the main content area to display the briefing view without a page reload.

#### Scenario: Switch to briefing view
- **WHEN** the user clicks the "Briefing" tab
- **THEN** the briefing panel becomes visible and the tasks list is hidden

#### Scenario: Switch back to tasks view
- **WHEN** the user clicks the "Tasks" tab
- **THEN** the task list becomes visible and the briefing panel is hidden

### Requirement: Briefing panel displays tasks in urgency buckets
The briefing view SHALL call `GET /api/brief` and display open tasks grouped into three sections: **Overdue**, **Due Today**, and **General** (no due date). Each section SHALL show a count and list each task's description, priority badge, and due date.

#### Scenario: Tasks shown in correct buckets
- **WHEN** the briefing view is active and `/api/brief` returns data
- **THEN** overdue tasks appear under "Overdue", tasks due today under "Due Today", and tasks without a due date under "General"

#### Scenario: Empty bucket
- **WHEN** a bucket contains zero tasks
- **THEN** the section displays an empty-state message (e.g., "Nothing here") instead of an empty list

#### Scenario: Mark done from briefing view
- **WHEN** the user clicks the done toggle on a task in the briefing view
- **THEN** the task is marked done via `PATCH /api/tasks/{id}/done` and the briefing view refreshes

### Requirement: Briefing view auto-refreshes on tab switch
The briefing view SHALL reload data from `/api/brief` every time the user switches to the Briefing tab, so counts are always current.

#### Scenario: Refresh on tab activation
- **WHEN** the user switches to the Briefing tab
- **THEN** a fresh call to `/api/brief` is made and the displayed data reflects the current state of tasks
