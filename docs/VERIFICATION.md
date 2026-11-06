# Verification record

Original midpoint verification date: October 16, 2026, America/Chicago. Final-project checks below were updated November 6, 2026. Claims about AWS and the installed extension remain pending until they are actually observed.

## November 6 final-project preparation

- On the final working branch, **11 Python API/database tests** and **5 Node extraction tests** pass. SQLite connections now close after each request; the browser UI no longer says “midpoint.”
- CloudFormation JSON parses locally, and its UserData passes `bash -n`. The Amazon Linux 2023 service now explicitly installs and uses Python 3.11 because the system `/usr/bin/python3` is Python 3.9. The template now uses Learner Lab's pre-created `LabInstanceProfile` instead of attempting restricted IAM role creation. The profile and bootstrap are still untested in the actual AWS account.
- A local browser at `http://127.0.0.1:8765/` loaded five fictional seeded records with correct totals and final UI labels. This is **local evidence**, not deployed evidence.
- Docker image `jobtrack-final-check:latest` built locally from the final working tree. A disposable container on local port 8766 returned HTTP 200 for `/api/health`, `/api/applications`, and `/`; the container was then stopped. Docker's periodic health check had not yet run, so no `healthy` state is claimed.
- AWS CLI 2.39.5 and Session Manager plugin 1.2.896.0 are installed locally. The intended AWS Academy Learner Lab account has not been identified or authenticated. No JobTrack stack, EC2 instance, cloud health response, cloud-backed CRUD, or AWS performance result has been verified.
- The accessible Cloud Architecting **Sandbox** account was authenticated and read-only inspected. AWS CloudFormation `validate-template` passed, but `LabInstanceProfile` is absent there; it has `myS3Role` and `EMR_EC2_DefaultRole` instead. The user chose not to deploy in this Sandbox. No JobTrack resources were created. Temporary local CLI credentials were removed after inspection.
- In the built-in browser, the actual `extension/extract.js` produced a draft from `web/demo-job.html` with Northstar Labs, Software Engineer Intern, Austin TX, Internship and $65,000. The dashboard opened the review form with those values, saved a fictional record, retained it after refresh, accepted a status edit to Interview, retained the edit after refresh, and deleted that disposable record. The local database returned to five seeded records. This validates extraction-to-dashboard behavior, not an installed extension toolbar.
- The 42 × 56 inch poster and nine-slide final deck have **draft builders** and visually checked draft renders. Final output is guarded until verified AWS evidence, measurements, and actual team roles are supplied. The user directed that nothing be submitted.

## Completed

- Python 3.13: **11 API/database tests passed** using real HTTP requests and temporary SQLite databases. Covers CRUD, full update, deletion, restart persistence, combined filters, ascending/descending salary with nulls last, unknown-salary exclusion, input validation, bad routes, query allowlisting, cross-origin write rejection, content type and health/static response.
- Node.js: **5 extraction tests passed**, including the actual Northstar Labs HTML fixture, arrays/graphs, malformed JSON tolerance, unsupported pages and salary rules.
- Local browser: created a disposable record, edited Fable Studio to Offer and refreshed successfully, deleted the disposable record, checked Interview filtering and combined salary empty state, Contract filtering, Reset, descending salary order, and imported Northstar draft review/save/refresh.
- Browser QA found a form method shadowing issue: a button with ID `reset` hid the form reset method. The implementation now calls the native form reset method explicitly. Reset was rechecked successfully.
- Desktop dashboard screenshot and actual draft-review screenshot saved in `docs/`. Browser error log after the final import/save workflow was empty.
- Responsive check at 390 × 844: document width 390, matching viewport width. Table uses horizontal scrolling inside its container. Desktop layout inspected at 1440 × 1000.
- CloudFormation JSON parses. Resource references, bootstrap shell syntax and archive paths were checked locally; AWS service-side syntax validation also passed in the available course Sandbox. This does not validate its missing instance profile or bootstrap behavior.

- The PowerPoint package, layout, font and import checks passed, and all slide renders were visually inspected. The updated deck reflects GitHub publication while retaining AWS and extension verification limits.

## Verification limits and remaining checks

- Chrome toolbar Load unpacked, activeTab permission grant and cross-tab extension execution have **not** been manually verified as an installed extension. Extraction code and dashboard import/save were checked separately. The browser import test used the same structured-data field values as a URL-fragment draft. Complete README extension steps before recording. This is a remaining acceptance check.
- Docker build and endpoint smoke check are complete locally. The Docker image is not the Learner Lab deployment target.
- At the October 16 midpoint check, AWS CLI/account session was unavailable. As of November 6 the CLI and SSM plugin are installed and the course Sandbox was inspected, but the intended Learner Lab profile was absent there and the user paused deployment. No deployed JobTrack stack, public URL, cloud health check, bootstrap execution or deployment acceptance result exists.
- GitHub authorization and publication are complete at [ReliWALEE/jobtrack-midpoint](https://github.com/ReliWALEE/jobtrack-midpoint), using separate commits for each batch. The final batch adds the test workflow. Hosted run details are available in [GitHub Actions](https://github.com/ReliWALEE/jobtrack-midpoint/actions). Local test results above are distinct from hosted CI results.
- At midpoint, the original course rubric, original source repository and original presentation were unavailable. The final Canvas requirements were subsequently checked and are documented in `FINAL_TEAM_HANDOFF.md`.
- PowerPoint is supplied as an editable PPTX with local render and package checks. It has not been opened and checked in the Microsoft PowerPoint application.
- The actual video recording is excluded as requested.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
node --test tests/extraction.test.cjs
python3 server.py
```

Follow the README and demo guide for manual browser/extension acceptance. Tests create temporary databases and do not modify the demo database. Runtime data is excluded from the source ZIP. The included screenshots show fictional local records.
