# Verification record

Verification date: October 16, 2026, America/Chicago.

## Completed

- Python 3.13: **11 API/database tests passed** using real HTTP requests and temporary SQLite databases. Covers CRUD, full update, deletion, restart persistence, combined filters, ascending/descending salary with nulls last, unknown-salary exclusion, input validation, bad routes, query allowlisting, cross-origin write rejection, content type and health/static response.
- Node.js: **5 extraction tests passed**, including the actual Northstar Labs HTML fixture, arrays/graphs, malformed JSON tolerance, unsupported pages and salary rules.
- Local browser: created a disposable record, edited Fable Studio to Offer and refreshed successfully, deleted the disposable record, checked Interview filtering and combined salary empty state, Contract filtering, Reset, descending salary order, and imported Northstar draft review/save/refresh.
- Browser QA found a form method shadowing issue: a button with ID `reset` hid the form reset method. The implementation now calls the native form reset method explicitly. Reset was rechecked successfully.
- Desktop dashboard screenshot and actual draft-review screenshot saved in `docs/`. Browser error log after the final import/save workflow was empty.
- Responsive check at 390 × 844: document width 390, matching viewport width. Table uses horizontal scrolling inside its container. Desktop layout inspected at 1440 × 1000.
- CloudFormation JSON parses. Resource references, bootstrap shell syntax and archive paths checked locally. No AWS service-side validation was possible.

- The PowerPoint package, layout, font and import checks passed, and all slide renders were visually inspected. The updated deck reflects GitHub publication while retaining AWS and extension verification limits.

## Verification limits and remaining checks

- Chrome toolbar Load unpacked, activeTab permission grant and cross-tab extension execution have **not** been manually verified as an installed extension. Extraction code and dashboard import/save were checked separately. The browser import test used the same structured-data field values as a URL-fragment draft. Complete README extension steps before recording. This is a remaining acceptance check.
- Docker is unavailable here. Dockerfile is prepared but no image build/run is claimed.
- AWS CLI/account session is unavailable. No deployed stack, public URL, cloud health check, bootstrap execution or deployment acceptance result exists.
- GitHub authorization and publication are complete at [ReliWALEE/jobtrack-midpoint](https://github.com/ReliWALEE/jobtrack-midpoint), using separate commits for each batch. The final batch adds the test workflow. Hosted run details are available in [GitHub Actions](https://github.com/ReliWALEE/jobtrack-midpoint/actions). Local test results above are distinct from hosted CI results.
- Original course rubric, original source repository and original presentation were unavailable. This package follows the user's requested deliverable list, not a verified original rubric. The earlier conversation exposed only text-reference placeholders and no downloadable implementation.
- PowerPoint is supplied as an editable PPTX with local render and package checks. It has not been opened and checked in the Microsoft PowerPoint application.
- The actual video recording is excluded as requested.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
node --test tests/extraction.test.cjs
python3 server.py
```

Follow the README and demo guide for manual browser/extension acceptance. Tests create temporary databases and do not modify the demo database. Runtime data is excluded from the source ZIP. The included screenshots show fictional local records.
