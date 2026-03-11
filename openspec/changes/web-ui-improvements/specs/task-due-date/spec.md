## ADDED Requirements

### Requirement: Inline due date editing on existing tasks
The task list SHALL allow the user to edit the due date of an existing task by clicking on the due date cell. Clicking SHALL replace the cell content with a `<input type="date">` pre-filled with the current value. Confirming the edit (pressing Enter or blurring the input) SHALL save the new date via `PATCH /api/tasks/{id}` and re-render the row.

#### Scenario: Click to edit due date
- **WHEN** the user clicks a task's due date cell
- **THEN** the cell displays a date input pre-filled with the current due date (or empty if none)

#### Scenario: Save edited due date
- **WHEN** the user changes the date and presses Enter or clicks away
- **THEN** the new date is sent to `PATCH /api/tasks/{id}` with body `{ "due": "YYYY-MM-DD" }` and the cell reverts to display mode showing the updated date

#### Scenario: Clear due date
- **WHEN** the user clears the date input and confirms
- **THEN** `PATCH /api/tasks/{id}` is called with `{ "due": null }` and the cell shows "—"

#### Scenario: Cancel edit with Escape
- **WHEN** the user presses Escape while the date input is active
- **THEN** the cell reverts to display mode with the original value unchanged and no API call is made

### Requirement: PATCH /api/tasks/{id} endpoint for partial update
The backend SHALL expose `PATCH /api/tasks/{id}` accepting a JSON body with optional fields `due` (date string or null) and `priority` (string). Only provided fields SHALL be updated; omitted fields SHALL remain unchanged.

#### Scenario: Update due date only
- **WHEN** `PATCH /api/tasks/5` is called with `{ "due": "2026-04-01" }`
- **THEN** the task's due date is updated to 2026-04-01 and all other fields are unchanged

#### Scenario: Clear due date via API
- **WHEN** `PATCH /api/tasks/5` is called with `{ "due": null }`
- **THEN** the task's due date is set to null

#### Scenario: Task not found
- **WHEN** `PATCH /api/tasks/999` is called and task 999 does not exist
- **THEN** the API returns HTTP 404
