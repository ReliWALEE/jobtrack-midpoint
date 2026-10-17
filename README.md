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

The bundled fictional posting at `/demo-job.html` provides the supported Chrome extension demonstration. Captured jobs open as editable drafts and require review before saving.

## Chrome extension

1. Start the server and open `http://127.0.0.1:8000/demo-job.html` in Chrome.
2. Visit `chrome://extensions`, enable Developer mode, select **Load unpacked**, and choose this repository's `extension/` folder.
3. Open **JobTrack Capture** from the Chrome toolbar. Keep its dashboard address `http://127.0.0.1:8000`.
4. Click **Extract current posting**, review the preview, and select **Review in dashboard**.
5. Confirm or correct the prefilled fields, then save. Refresh the dashboard to confirm persistence.

Supported extraction uses Schema.org JSON-LD JobPosting data, including arrays and `@graph`. The bundled Northstar Labs posting is the reliable fixture. Arbitrary job boards, login-only pages, iframes and Chrome internal pages are not guaranteed. Unsupported pages display an actionable message. Only a single annual USD salary value is extracted. Hourly, foreign-currency, missing or null salaries require manual entry. Review employment type if source values are absent or unrecognized.

The extension uses `activeTab` and `scripting` to read the current posting after a user click, and `storage` to remember the dashboard address. It opens a draft in a new dashboard tab instead of writing directly across origins. The dashboard removes the URL fragment after reading it, and saves only after user review. No employer application is submitted.

The extraction code and dashboard draft review/save flow were checked separately. Actual Chrome toolbar installation, activeTab permission and cross-tab extension execution still need a manual Chrome check before recording.

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
node --test tests/extraction.test.cjs
```

Requires Node.js 22+ for the JavaScript tests. Eleven API/database tests cover CRUD, restart persistence, filters, ordering, validation and dashboard serving. Five extraction tests cover the real demo fixture, JSON-LD arrays/graphs, malformed data, unsupported pages and salary rules. The local browser workflow was checked for adding, editing, deleting, filters, sorting, reset and draft review/save. No hosted CI run is claimed yet.

## Incremental upload status

1. Backend API, SQLite persistence and backend tests: uploaded.
2. Dashboard, demo seed and dashboard-serving test: uploaded.
3. Chrome extension and extraction tests: included in this batch.
4. Full documentation, deployment configuration, CI workflow and presentation: later batch.

This is a single-user midpoint prototype with no login or per-user data isolation. Keep it local. No live AWS deployment is claimed.
