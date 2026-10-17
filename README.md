# JobTrack

A personal job application tracker with a browser dashboard, Python REST API and persistent SQLite database.

## Run

Requires Python 3.11+. No package installation or frontend build is required.

```sh
python3 server.py
```

Open **http://127.0.0.1:8000** in your browser. Windows can use `py server.py`. Do not open the HTML directly as a file. The database initializes at `data/jobtrack.sqlite3` and survives restarting the server. Stop with Ctrl+C.

Optional fictional demo records, from a second terminal in the project folder:

```sh
python3 seed_demo.py
```

The seed checks existing company/title pairs before inserting records.

## Dashboard

- Add, edit and delete applications, with confirmation before deletion.
- Track company, role, location, employment type, status, date, annual salary, posting URL and notes.
- Search company, role and location. Combine status, employment type and minimum/maximum salary filters.
- Sort by annual salary, company, date or most recent update. Reset restores all filters.
- Overview statistics summarize every application. The table count reflects the selected filters.
- Salaries use whole annual US dollars. Unknown salaries sort last and do not meet a salary bound. No hourly or currency conversion is implied.
- Responsive layout with a horizontally scrolling table on narrow screens.

The bundled fictional posting at `/demo-job.html` is included for the upcoming extension batch. The dashboard already supports reviewing imported drafts before saving.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/health` | API/database health |
| GET | `/api/applications` | List, filter and sort |
| POST | `/api/applications` | Create |
| PUT | `/api/applications/{id}` | Replace editable fields |
| DELETE | `/api/applications/{id}` | Delete |

Writes use JSON with `Content-Type: application/json`. Company and title are required. PUT is a full replacement. Query parameters include `q`, `status`, `employment_type`, `salary_min`, `salary_max`, `sort` and `direction`. Salary bounds range from 0 to 10000000.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

Eleven API/database tests cover CRUD, restart persistence, filters, ordering, validation and dashboard serving. The local browser workflow was checked for adding, editing, deleting, filters, sorting, reset and draft review/save. No hosted CI run is claimed yet.

## Incremental upload status

1. Backend API, SQLite persistence and backend tests: uploaded.
2. Dashboard, demo seed and dashboard-serving test: included in this batch.
3. Chrome extension and extraction tests: next batch.
4. Full documentation, deployment configuration, CI workflow and presentation: later batch.

This is a single-user midpoint prototype with no login or per-user data isolation. Keep it local. No live AWS deployment is claimed.
