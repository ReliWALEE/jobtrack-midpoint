# JobTrack

A runnable single-user job application tracker for a midpoint demonstration. Built from the requested checklist because the referenced chat contained no recoverable implementation or attached deck. Exact course rubric and original architecture were unavailable.

## Run in two steps

Requires Python 3.11+ (tested with 3.13), a current browser, and Node.js 22+ only for JavaScript tests. No Python package installation or frontend build is needed.

```sh
python3 server.py
```

Open **http://127.0.0.1:8000**. Windows can use `py server.py`. The database initializes automatically at `data/jobtrack.sqlite3`. Stop with Ctrl+C. Start the same command again to retain applications. To use a different database, set `JOBTRACK_DB` to a writable file path. Do not open `index.html` directly as a file.

Optional fictional demo records:

```sh
python3 seed_demo.py
```

Run the seed once while the server is running. It checks existing company/title pairs to avoid duplicate seed records. The delivered source archive excludes runtime databases.

## Features and data rules

- Create, view, edit and delete applications. Delete requires confirmation.
- Search company, title and location. Combine employment type, status and salary filters.
- Sort by annual salary, company or application date, or most recent update.
- Salary is an optional whole annual USD amount. Unknown salaries appear last and are excluded by any salary bound. No hourly/currency conversion is implied.
- Statuses: Saved, Applied, Interview, Offer, Rejected. Employment: Full-time, Part-time, Contract, Internship.
- Overview counts use all records. The table count uses filtered records.
- Responsive dashboard, empty state, form validation and visible failure messages.

This midpoint app has no user accounts or per-user isolation. Keep local or use the private AWS tunnel described in the deployment guide. It does not submit employer applications.

## Chrome extension

1. Visit `chrome://extensions`, enable Developer mode, choose **Load unpacked**, select `extension/`.
2. Start the server and visit **http://127.0.0.1:8000/demo-job.html** in Chrome.
3. Open JobTrack Capture. Keep the dashboard address `http://127.0.0.1:8000`.
4. Click **Extract current posting**, inspect the preview, then **Review in dashboard**.
5. Edit the prefilled form if needed and click **Save application**. Refresh to verify persistence.

Supported extraction is Schema.org JSON-LD JobPosting, including arrays and `@graph`. The bundled fictional Northstar Labs page is the reliable demonstration fixture. Arbitrary job boards, authenticated sites, iframes and Chrome internal pages are not guaranteed. Unsupported pages show an actionable message. Salary extraction accepts only a single annual USD value. Review employment type, especially when source data is absent or unrecognized. Capture uses `activeTab` and `scripting`, with `storage` for the dashboard address. No persistent host access, cross-origin API writes or scraping service is required. The draft travels in the URL fragment and the dashboard removes that fragment after reading it. Do not put secrets in posting fields.

Extraction tests and the dashboard import/save flow were checked separately. Loading the unpacked extension through the Chrome toolbar and granting activeTab permission still require a manual check before recording.

Implementation follows [Chrome's activeTab scripting flow](https://developer.chrome.com/docs/extensions/get-started/tutorial/scripts-activetab).

## API

All responses are JSON except static pages. Writes use `Content-Type: application/json`.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/health` | API/database connectivity |
| GET | `/api/applications` | List/filter/sort records |
| POST | `/api/applications` | Create, returns 201 |
| PUT | `/api/applications/{id}` | Full replacement of editable fields |
| DELETE | `/api/applications/{id}` | Delete |

GET parameters: `q`, `status`, `employment_type`, `salary_min`, `salary_max`, `sort`, `direction`. Sort allowlist: `company`, `title`, `salary`, `applied_date`, `updated_at`, `status`. Direction: `asc` or `desc`. Default: updated descending. Bad input returns 400, missing records return 404, unsupported media returns 415. SQLite uses parameterized query values and an allowlist for sort fields. JSON fields: company, title, location, salary, employment_type, status, applied_date, url, notes. Company/title required, date uses YYYY-MM-DD. IDs and timestamps are server-managed. PUT resets omitted optional fields to defaults and is not a partial patch.

## Tests

```sh
python3 -m unittest discover -s tests -v
node --test tests/extraction.test.cjs
```

The committed CI workflow runs these checks on pushes and pull requests. See `docs/VERIFICATION.md` for actual results and the limits of browser/extension/AWS verification.

## Files and architecture

`web/` contains the browser interface, `server.py` serves static files and the REST API, SQLite persists records under `data/`, and `extension/` captures a reviewed draft. Browser requests and API share one origin. See `docs/ARCHITECTURE.md`, `docs/DEMO_SCRIPT.md` and `docs/AWS_DEPLOYMENT.md`.

## Docker option (configuration prepared, not built here)

```sh
docker build -t jobtrack .
docker run --rm -p 127.0.0.1:8000:8000 -v jobtrack-data:/data jobtrack
```

The named volume preserves data. Never remove the volume unless you intend to erase it.

## Presentation

`presentation/JobTrack-Midpoint.pptx` contains the editable midpoint slides with actual screenshots and timed speaker notes. The recording guide is in `docs/DEMO_SCRIPT.md`.

## AWS source package

Create the source archive expected by the CloudFormation instructions:

```sh
python3 deploy/package_source.py
```

It writes `work/JobTrack-source.zip` with a top-level `JobTrack/` directory and excludes runtime data. See `docs/AWS_DEPLOYMENT.md` for account authorization, upload, validation, cost and cleanup steps. No AWS deployment has occurred.

## GitHub handoff

The private repository is [ReliWALEE/jobtrack-midpoint](https://github.com/ReliWALEE/jobtrack-midpoint). Source arrived in separate backend, dashboard, extension and handoff commits. The repository includes `.gitignore` and a GitHub Actions test workflow. See `docs/GITHUB_HANDOFF.md` for clone/update instructions and the Actions tab for hosted run results. Runtime databases and account tokens are excluded.
