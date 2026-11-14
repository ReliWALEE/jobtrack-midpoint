# JobTrack

For the current Group 42 results and final files, see [`docs/FINAL_STATUS_2026-11-13.md`](docs/FINAL_STATUS_2026-11-13.md). The poster and slides were submitted November 13. Older handoff documents describe the November 5–6 plan.

A runnable single-user job application tracker. The dashboard, API, database, job discovery, and structured-posting capture flow were developed for a class demonstration. A time-limited public HTTPS AWS Academy Sandbox deployment was verified on November 13; see the final status and evidence files for its exact scope. It uses a shared demo password; individual accounts and data isolation are not implemented.

Public demo: **https://100-58-234-86.sslip.io/**. The password is stored only in ignored `work/public-demo-login.txt` on the deployment laptop. Use fictional records only. The address depends on the AWS Sandbox session and EC2 public IP.

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

This app has no user accounts or per-user isolation. Keep local or use the private AWS tunnel described in the deployment guide. It does not submit employer applications.

## Job discovery

Open **Find jobs** in the dashboard, or visit `http://127.0.0.1:8000/jobs.html`.

- **Remotive:** real remote listings work immediately without an API account. Search title/company keywords and the employer's location eligibility text. Keep the original Remotive link and attribution. This public feed is a limited selection, delayed by 24 hours; it is not the entire job market.
- **Indeed / LinkedIn / all boards:** the implemented JSearch adapter searches listings aggregated by OpenWeb Ninja through Google for Jobs. It is a third-party connection, not a direct Indeed or LinkedIn partnership. Coverage and publisher availability vary. A user-owned JSearch API key is required; these sources show a connection prompt until configured. Live Indeed and LinkedIn searches were verified on November 12, 2026, returning 10 publisher-matching listings each for software engineer in Chicago. Each installation needs its own private key.
- **Save to applications** imports a listing as Saved. Repeat saves return the existing application and preserve edits. Deleting an application lets you save it again. Saving does not submit an employer application.
- The last search is remembered in this browser. Optional refresh runs every 30 minutes while the page is open and visible. There is no unattended server scheduler or email alert service.
- SQLite retains feed caches and discovered listings across restarts. Remotive is fetched at most once per six hours per database, with local filtering; JSearch searches are cached for 15 minutes. A failed first attempt waits a minute before retry; a failed refresh retains older listings with a visible warning and timestamp. Clicking Find jobs does not bypass provider caches. Only the first 50 matching results are displayed; JSearch requests one provider page per search.
- Listed salary text is retained in notes. Only an exact annual USD value populates the tracker's numeric salary; ranges, hourly values, and unspecified currencies stay unknown. Missing employment type is **Not specified**.

### Connect JSearch locally

1. Create your own account at [OpenWeb Ninja](https://app.openwebninja.com) and activate JSearch. Review the current plan and request limits; JobTrack does not create an account, choose a paid plan, or authorize charges.
2. On the computer running JobTrack, set the `JSEARCH_API_KEY` environment variable. On macOS/Linux, this example prompts without echoing the key or putting it in command history:

   ```sh
   read -r -s -p "JSearch API key: " JSEARCH_API_KEY
   export JSEARCH_API_KEY
   python3 server.py
   ```

   In PowerShell, set the environment variable using your preferred local secret manager, then launch the server from that session. `.env.example` lists the setting; the server also reads `JSEARCH_API_KEY` from a local `.env` beside `server.py`. The environment takes precedence. Other `.env` entries are ignored; the file is never executed. Keep this file private (`chmod 600 .env` on macOS/Linux). With Docker, pass `-e JSEARCH_API_KEY` after setting it in the host environment.
3. Restart any existing server, reload Find jobs, choose a source, and search a title and location. Indeed and LinkedIn use the provider's documented `via <publisher>` query, then retain only matching publishers/apply links returned by JSearch. Jobs not returned by the provider are not invented or substituted.

Keep keys out of browser code, chat, screenshots, and GitHub. Source status exposes only whether a key is present. No API key is sent to Indeed or LinkedIn; the server sends it only to OpenWeb Ninja's fixed API endpoint.

Provider references: [Remotive API and reuse terms](https://github.com/remotive-com/remote-jobs-api), [JSearch endpoint, auth, and publisher queries](https://www.openwebninja.com/api/jsearch). The connected local instance has verified Indeed/LinkedIn access. A fresh clone still needs its own account/key configuration. AWS remains deferred.

## Chrome extension

1. Visit `chrome://extensions`, enable Developer mode, choose **Load unpacked**, select `extension/`.
2. Start the server and visit **http://127.0.0.1:8000/demo-job.html** in Chrome.
3. Open JobTrack Capture. Keep the dashboard address `http://127.0.0.1:8000`.
4. Click **Extract current posting**, inspect the preview, then **Review in dashboard**.
5. Edit the prefilled form if needed and click **Save application**. Refresh to verify persistence.

Supported extraction is Schema.org JSON-LD JobPosting, including arrays and `@graph`. The bundled fictional Northstar Labs page is the reliable demonstration fixture. Arbitrary job boards, authenticated sites, iframes and Chrome internal pages are not guaranteed. Unsupported pages show an actionable message. Salary extraction accepts only a single annual USD value. Review employment type, especially when source data is absent or unrecognized. Capture uses `activeTab` and `scripting`, with `storage` for the dashboard address. No persistent host access, cross-origin API writes or scraping service is required. The draft travels in the URL fragment and the dashboard removes that fragment after reading it. Do not put secrets in posting fields.

The extractor's output from the bundled fixture was carried through the dashboard review, save, refresh, edit, and deletion flow in the built-in browser. Loading the unpacked extension through a Chrome-family toolbar and granting activeTab permission remain a separate, unverified check; the built-in browser does not support unpacked extensions.

Implementation follows [Chrome's activeTab scripting flow](https://developer.chrome.com/docs/extensions/get-started/tutorial/scripts-activetab).

## API

All responses are JSON except static pages. Writes use `Content-Type: application/json`.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/health` | API/database connectivity |
| GET | `/api/job-sources` | Provider readiness, no credentials |
| GET | `/api/jobs` | Discover listings: `source`, `q`, `location` |
| POST | `/api/jobs/{id}/save` | Save a discovered listing; 201 new / 200 existing |
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

The committed CI workflow is configured to run these checks on pushes and pull requests. Local API, discovery, and extraction tests passed. Check the Actions tab for the current branch’s hosted run status. See `docs/VERIFICATION.md` for actual results and the limits of browser/extension/AWS verification.

## Files and architecture

`web/` contains the browser interface, `server.py` serves static files and the REST API, `jobs.py` fetches and caches provider listings, SQLite persists records under `data/`, and `extension/` captures a reviewed draft. Browser requests and API share one origin. See `docs/ARCHITECTURE.md`, `docs/DEMO_SCRIPT.md` and `docs/AWS_DEPLOYMENT.md`.

## Docker option (locally built and smoke tested)

```sh
docker build -t jobtrack .
docker run --rm -p 127.0.0.1:8000:8000 -v jobtrack-data:/data jobtrack
```

The named volume preserves data. Never remove the volume unless you intend to erase it.
The image was built locally on November 6; its health, list, and dashboard endpoints returned HTTP 200 on a temporary container. The November 13 AWS deployment uses a direct Amazon Linux 2023 systemd service instead of Docker.

## Presentation

`presentation/JobTrack-Midpoint.pptx` is the archived midpoint deck. `presentation/build_final.mjs` builds the editable final deck at `deliverables/Group42-JobTrack.pptx` from verified evidence. The final poster is at `deliverables/JobTrack-poster-final.pdf`. The midpoint recording guide is historical.

## AWS source package

Create the source archive expected by the CloudFormation instructions:

```sh
python3 deploy/package_source.py
```

It writes `work/JobTrack-source.zip` with a top-level `JobTrack/` directory and excludes runtime data. The verified Sandbox deployment uses `deploy/cloudformation-sandbox.json`; see [`docs/FINAL_STATUS_2026-11-13.md`](docs/FINAL_STATUS_2026-11-13.md) for the observed results. `docs/AWS_DEPLOYMENT.md` and `deploy/cloudformation.json` retain the original Learner Lab/SSM design as a separate option.

## GitHub handoff

The public repository is [ReliWALEE/jobtrack-midpoint](https://github.com/ReliWALEE/jobtrack-midpoint). Source arrived in separate backend, dashboard, extension and handoff commits. The repository includes `.gitignore` and a GitHub Actions test workflow. See `docs/GITHUB_HANDOFF.md` for clone/update instructions and the Actions tab for hosted run results. Runtime databases and account tokens are excluded.
