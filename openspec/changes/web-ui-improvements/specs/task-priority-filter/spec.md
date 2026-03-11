## ADDED Requirements

### Requirement: Priority filter chips in the task list
The task list filter bar SHALL include a set of priority filter chips: **All**, **High**, **Medium**, **Low**. Selecting a chip SHALL immediately filter the visible task rows to only those matching the selected priority. Priority filtering SHALL combine with the existing status filter (All / Open / Done).

#### Scenario: Filter by High priority
- **WHEN** the user clicks the "High" priority chip
- **THEN** only tasks with priority "High" are shown in the task list

#### Scenario: Combined priority and status filter
- **WHEN** the user has "Open only" status filter active and clicks "High" priority chip
- **THEN** only open tasks with priority "High" are shown

#### Scenario: Reset priority filter
- **WHEN** the user clicks the "All" priority chip
- **THEN** tasks of all priorities are shown (subject to the active status filter)

#### Scenario: Active chip is visually indicated
- **WHEN** a priority chip is selected
- **THEN** it has a distinct visual style (e.g., filled background matching the priority colour) to indicate it is active

### Requirement: Priority filter is client-side
Priority filtering SHALL be applied client-side on the already-loaded task array without making additional API calls.

#### Scenario: No extra network request on filter change
- **WHEN** the user switches priority filter
- **THEN** no new HTTP request is made to the server
