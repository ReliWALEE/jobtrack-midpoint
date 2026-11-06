# JobTrack final poster content draft

This is source copy for the final 42 × 56 inch PDF. Do not submit this Markdown file. Replace every evidence marker with observed data before export. The final poster must not claim AWS deployment until verified.

## Title and team

**JobTrack: A private cloud-hosted job application tracker**
CSE 4333 Cloud Computing · Group 42
Ahmad Salem · afs1009@mavs.uta.edu
NoorAldeen Waleed · nxw3312@mavs.uta.edu
Roles: NoorAldeen — project concept and [verified implementation contribution]; Ahmad — [verified implementation/deployment/testing/documentation contribution]. Confirm with both members before final export.

## Summary

JobTrack gives students and job seekers one place to record opportunities, update application stages, and find entries by company, role, status, employment type, and salary. The implemented core is a browser dashboard, Python JSON API, and SQLite database. A Chrome extension can prefill a draft from a supported Schema.org JobPosting page for user review. The planned private cloud path uses Amazon EC2, encrypted EBS, S3, IAM, Systems Manager, and CloudFormation. The built-in browser verified the extractor output through review, save, edit, refresh, and deletion; installed-extension toolbar use remains unverified. Local latency is recorded in `evidence/performance-local.json`; cloud latency is pending. **Replace the cloud-status sentence with actual deployment result and measured latency once verified.**

## Problem, users and use cases

Students and recent graduates often apply to many jobs and lose track of where they applied, when, and what happens next. JobTrack records company, title, location, annual USD salary, employment type, status, application date, URL, and notes. A user can add a lead, update it from Applied to Interview or Offer, search/filter the pipeline, and delete stale entries. The app tracks applications; it does not submit applications to employers.

## Architecture

Browser/extension → private local or SSM-forwarded dashboard → Python HTTP API on one EC2 instance → SQLite on encrypted EBS. The extension reads JSON-LD from a page only after a user clicks and opens an editable draft in the dashboard. CloudFormation provisions the EC2 instance, security group, and EBS root volume; it attaches Learner Lab's pre-created IAM instance profile. The instance fetches source from a private S3 bucket. The app listens on loopback, and the security group has no inbound ports. An authorized AWS user connects through Systems Manager port forwarding. **If the actual deployed configuration differs, redraw and rewrite this section.**

### Design choices

- One EC2 instance and SQLite are simple to build and explain for a private single-user class demo.
- SSM avoids exposing an unauthenticated web service to the public Internet.
- Encrypted EBS persists through process and instance stop/start, but the root volume is deleted on termination, so backup is needed before replacement/deletion.
- Alternatives considered: a public HTTPS app with login, EC2 with RDS, or API Gateway/Lambda with DynamoDB. Those add user isolation, managed storage or scaling options but also more configuration and cost for this small demonstration. They are **not implemented**.

## Application logic and services

The dashboard uses same-origin `fetch` requests. The API validates fields and writes timestamps in UTC. SQLite uses parameterized values and an allowlist for sort keys. One `applications` table holds IDs, job details, status, and timestamps. Endpoints: `GET /api/health`, `GET /api/applications` with search/filter/sort, `POST /api/applications`, `PUT /api/applications/{id}`, and `DELETE /api/applications/{id}`. The extension supports structured Schema.org `JobPosting` data, including arrays and `@graph`, but does not cover every job board. Salary extraction accepts a single annual USD amount; other cases require manual review.

## Verification and performance

Current local baseline: 11 Python API/database tests and 5 JavaScript extraction tests pass. Tests cover CRUD, filtering, salary order, validation, persistence, and supported/unsupported extraction cases. **Add installed-extension result and cloud-backed CRUD/restart result once observed.**

**Performance evidence pending:** Report AWS region, instance type, record count, client location, 50 sequential requests per endpoint with 5 warmups, mean/median/p95 latency for health/list/search, and date. Use `tools/benchmark.py` through the SSM tunnel; include a results chart and explain that this is a small single-user latency test, not a scalability test. Do not invent numbers or label local measurements as AWS.

## Challenges and lessons

The original browser QA caught a Reset-button naming conflict and was repaired. Final review found that SQLite context managers did not close connections; the final branch now closes each request connection. Private SSM access reduces exposure but adds setup and demo logistics. The design's root EBS volume needs a backup before stack deletion. **Add real AWS or extension deployment challenges only after they occur.**

## Machine learning

Not applicable. JobTrack does not use a machine-learning model.

## Future work

Add authentication and per-user access controls before any public deployment. Move data to a managed database with automated backups for stronger recovery and multi-instance options. Add monitoring, accessible HTTPS hosting, and broader job-posting extraction only after those security and data-management foundations are in place.

## Conclusion

JobTrack consolidates a job search into a searchable pipeline and supports reviewed capture of structured job postings. The final conclusion must state the **actual verified cloud status, measurements, and remaining limits**. Keep all claims consistent with the screenshots, logs, repository, and live demo.
