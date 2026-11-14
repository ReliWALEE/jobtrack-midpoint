# Architecture

## Implemented local path

Chrome extension reads JSON-LD in the active tab after a user click. It opens the JobTrack dashboard with a URL-fragment draft. The dashboard removes the fragment, displays an editable form, and saves only after user review.

The dashboard uses fetch with same-origin JSON REST requests. A Python ThreadingHTTPServer handler validates input and queries SQLite. Each request opens its own database connection, and SQLite WAL mode supports concurrent reads. SQLite assigns record IDs. The API writes creation/update timestamps in UTC. The database file persists independently from the browser.

## Data model

One `applications` table: id, company, title, location, salary (nullable annual USD integer), employment_type, status, applied_date, url, notes, created_at, updated_at. There is no users table or tenancy model. All users of one server would share the same records.

## Verified AWS Sandbox deployment — November 13

`deploy/cloudformation-sandbox.json` created an Amazon Linux 2023 `t3.micro` EC2 instance with Python 3.11 and SQLite on a 12 GiB encrypted gp2 EBS root volume. CloudFormation also created a security group. It allows public TCP 80/443 and limits SSH to the deployment client's single `/32` IPv4. Nginx redirects HTTP to HTTPS, enforces a shared demo password, and proxies to the Python app on EC2 loopback port 8000. The public address is `https://100-58-234-86.sslip.io/`. The existing `myS3Role` instance profile lets EC2 fetch its source ZIP from a private S3 bucket. Cloud health, CRUD, service-restart persistence, Remotive discovery, public HTTPS access, and client-to-EC2 tunnel latency were verified. See `docs/FINAL_STATUS_2026-11-13.md` and `evidence/` for results.

The original `deploy/cloudformation.json` remains a separate **Learner Lab** design with `LabInstanceProfile` and Systems Manager access. It was not the deployed configuration. The Sandbox session is time-limited, and the root EBS volume is deleted when the instance terminates. Back up before deletion or replacement.

## Limits

The public class demo uses TLS and shared HTTP Basic authentication at Nginx. It has no individual accounts or per-user authorization, so all authorized visitors share the same fictional records. It is not suitable for real applicant data or durable production hosting. SQLite is not shared across replicas. No email automation, employer submission, job-board login integration, OAuth, telemetry, or background crawler is implemented.


## Job discovery extension (November 12, 2026)

`web/jobs.html` / `web/jobs.js` → same-origin `/api/jobs` → `jobs.py` → fixed Remotive or JSearch HTTPS endpoint. The server holds credentials; browser code receives normalized public listings only. SQLite adds `job_cache`, `discovered_jobs`, and `job_imports` alongside existing applications, without replacing application data. Saving a discovered ID uses a transaction and job-ID/exact-URL duplicate checks. Application edits survive subsequent saves.

Remotive's full public sample is cached for six hours and filtered locally. JSearch caches each source/query/location for 15 minutes, fetching one page. There is no unattended scheduler: opt-in polling is in the visible browser page. Provider failures have bounded timeouts and body size, retry delays, and stale-cache warnings. Provider payloads render as text and posting URLs allow HTTP(S) only. JSearch includes Indeed/LinkedIn publisher filtering via third-party search; live Indeed/LinkedIn searches were verified with a privately configured key. Fresh installations need their own key. The adapter accepts search-v2’s `data.jobs` wrapper and the older flat `data` array.
