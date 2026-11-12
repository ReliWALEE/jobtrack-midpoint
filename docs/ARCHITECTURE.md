# Architecture

## Implemented local path

Chrome extension reads JSON-LD in the active tab after a user click. It opens the JobTrack dashboard with a URL-fragment draft. The dashboard removes the fragment, displays an editable form, and saves only after user review.

The dashboard uses fetch with same-origin JSON REST requests. A Python ThreadingHTTPServer handler validates input and queries SQLite. Each request opens its own database connection, and SQLite WAL mode supports concurrent reads. SQLite assigns record IDs. The API writes creation/update timestamps in UTC. The database file persists independently from the browser.

## Data model

One `applications` table: id, company, title, location, salary (nullable annual USD integer), employment_type, status, applied_date, url, notes, created_at, updated_at. There is no users table or tenancy model. All users of one server would share the same records.

## AWS target

An Amazon Linux 2023 EC2 instance hosts the same server with Python 3.11 and an SQLite file. The AWS Academy Learner Lab template attaches its existing `LabInstanceProfile`, which must permit source ZIP reads and SSM management; this lab profile has broader permissions than a production-specific role. The security group admits no inbound traffic. A user with authorized AWS access forwards local port 8000 to the instance. The encrypted EBS root disk persists through stop/start, but terminates with the instance. CloudFormation configuration is prepared and has not yet been verified in AWS.

## Limits

The built-in Python server is suitable for a local/private class demonstration. A public deployment requires authentication, per-user authorization, TLS and a hardened server. SQLite is not shared across replicas. No email automation, employer submission, job-board login integration, OAuth, telemetry, or background crawler is implemented.


## Job discovery extension (November 12, 2026)

`web/jobs.html` / `web/jobs.js` → same-origin `/api/jobs` → `jobs.py` → fixed Remotive or JSearch HTTPS endpoint. The server holds credentials; browser code receives normalized public listings only. SQLite adds `job_cache`, `discovered_jobs`, and `job_imports` alongside existing applications, without replacing application data. Saving a discovered ID uses a transaction and job-ID/exact-URL duplicate checks. Application edits survive subsequent saves.

Remotive's full public sample is cached for six hours and filtered locally. JSearch caches each source/query/location for 15 minutes, fetching one page. There is no unattended scheduler: opt-in polling is in the visible browser page. Provider failures have bounded timeouts and body size, retry delays, and stale-cache warnings. Provider payloads render as text and posting URLs allow HTTP(S) only. JSearch includes Indeed/LinkedIn publisher filtering via third-party search; live Indeed/LinkedIn searches were verified with a privately configured key. Fresh installations need their own key. The adapter accepts search-v2’s `data.jobs` wrapper and the older flat `data` array.
