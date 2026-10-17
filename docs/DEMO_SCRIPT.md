# JobTrack recording guide · target 5:15

The video itself is intentionally not included. This guide combines an approximately five-minute slide presentation with a short live browser demonstration. The eight-slide deck has matching timing notes. Rehearse once and use the clock below. Spoken sections total roughly 600 words, leaving time for clicks and pauses. Adjust your pace to finish near 5:15.

## Before recording

1. Unzip the source package and open a terminal in `JobTrack/`.
2. Run `python3 server.py`, then in another terminal run `python3 seed_demo.py`. Open `http://127.0.0.1:8000` in Chrome. Use fictional records only.
3. Load `extension/` through `chrome://extensions` using Developer mode and Load unpacked. Pin JobTrack Capture. This manual toolbar-installation/permission check remains for the presenter to verify before recording. Confirm Extract current posting on `http://127.0.0.1:8000/demo-job.html` opens a prefilled dashboard draft and saves correctly. Remove that rehearsal record if desired.
4. Open the PowerPoint in presentation mode. Keep the dashboard and demo-posting tabs ready. Confirm any course-required name, course, section, team details or rubric items, since the original assignment rubric was unavailable.
5. Record a small microphone test. Close unrelated windows and notifications. Do not show AWS credentials or GitHub tokens. The private GitHub repository is published at https://github.com/ReliWALEE/jobtrack-midpoint. Do not claim live AWS deployment unless you complete and verify it first.

## 0:00–0:25 · Slide 1 · Introduction

“JobTrack is a personal job application tracker. It helps a student or job seeker keep opportunities in one place and see where each application stands. For this midpoint, I have a runnable dashboard, a backend API and a persistent SQLite database. I also have Chrome extension source with a supported extraction flow. AWS deployment configuration is ready, but I am not presenting it as a live deployment.”

## 0:25–0:55 · Slide 2 · Dashboard

“This screenshot comes from the running application and uses fictional records. The overview shows total applications, active opportunities, interviews and offers. Each row keeps the role, company, location, employment type, annual salary, status and date together. The overview counts cover every record, while the table shows the current filter results. I will switch to the live browser to demonstrate the main workflow.”

Action: switch to browser. Keep slide 3 as the next slide when returning.

## 0:55–1:55 · Slide 3 plus live browser · CRUD and queries

“I will add a fictional role at Demo QA, enter an annual salary of eighty-five thousand dollars, and save it as Applied. I can edit the same application to Interview. Refreshing the page keeps the change because the data lives in the database rather than only in the browser.

“I can filter by Interview, combine that with Full-time employment, and add a salary bound. Reset restores the complete table. Salary sorting lets me put the highest-paying roles first. Salary values use annual US dollars, and unknown salaries do not meet a salary bound. Finally, I will delete only this disposable demo record and confirm the action.”

Actions: Add company **Demo QA**, role **QA Engineer**, salary **85000**, employment **Full-time**, status **Applied**. Save. Edit status to Interview. Refresh. Filter Interview, Full-time, min 80000. Reset. Sort salary high to low. Delete **QA Engineer** and confirm. If time is tight, show deletion immediately after refresh and describe the filters while selecting them.

## 1:55–2:50 · Slide 4 plus live Chrome · Capture

“The reliable extraction demonstration uses this fictional Northstar Labs posting. It includes structured Schema.org JobPosting data. I open JobTrack Capture and choose Extract current posting. The preview identifies the role, employer, employment type and annual salary. Review in dashboard opens an editable draft. I can correct the values before saving, and no employer application is submitted.

“This extractor supports structured job postings, including the bundled fixture. It does not promise to understand every job board. Unsupported pages show a message, and hourly or foreign-currency salaries require manual entry.”

Actions: open demo posting, extension, Extract current posting, Review in dashboard. Confirm Northstar Labs, Software Engineer Intern, Austin TX, Internship, 65000. Save and refresh. If the unpacked extension fails its preflight, fix that before recording. If you cannot fix it, show the provided screenshot and explicitly describe it as the verified dashboard draft flow, with toolbar verification pending. Do not simulate an installed extension and call it verified.

## 2:50–3:35 · Slide 5 · Architecture

“The extension reads job data from the active tab after a user click. It opens a draft in the dashboard, and the user reviews that draft before saving. The dashboard sends same-origin JSON requests to the Python API. The API validates application fields and uses parameterized SQLite queries. One applications table holds the job details and timestamps. SQLite stores the records on disk, so they survive a server restart. This is a single-user midpoint prototype. It does not yet include accounts or isolation between multiple users.”

Action: return to the deck. Optional: show `docs/ARCHITECTURE.md` briefly without spending time reading code.

## 3:35–4:15 · Slide 6 · Verification

“Eleven API and database tests passed, along with five extraction tests. They cover the main CRUD operations, invalid inputs, combined filters, salary ordering and persistence after restarting the server. Browser checks also covered creation, editing, refresh, deletion, filtering, sorting, reset and imported-draft review and save. Browser testing caught a Reset button bug, which I fixed and checked again. The interface also fits a mobile viewport. The installed extension toolbar flow and the Docker build still need their own environment checks.”

Action: show the test summary in `docs/VERIFICATION.md` if useful. After you complete the manual extension check, update that sentence and the corresponding slide note truthfully.

## 4:15–5:00 · Slide 7 · AWS and GitHub

“The AWS template prepares a private EC2 demonstration using the same app and an encrypted EBS disk. Session Manager forwards a local port to the instance, so the template opens no inbound web ports. Database data survives stop and start, but I need a backup before deleting or replacing the instance.

“Deployment still requires an authorized AWS account, a region, VPC and subnet, and approval of resource costs. I then need to validate the template, create the stack, and check the service and health endpoint. The private GitHub repository now contains separate commits for the backend, dashboard, extension and handoff. GitHub Actions provides repeatable test checks, with hosted results available in the Actions tab. No live AWS deployment is claimed.”

## 5:00–5:15 · Slide 8 · Close

“The handoff includes the runnable source, tests and README, extension source, midpoint slides, and this demo guide. The remaining work is the manual extension check and the authorized AWS deployment steps. The core local application is ready to demonstrate.”

## Recording sequence checklist

- Follow the 5:15 clock rather than reading every field.
- Use the bundled posting so the extraction fixture is predictable.
- Keep the delete target fictional and disposable.
- Show one refresh so persistence is visible.
- Keep deployment claims consistent with actual account results.
- Export and check your recording's audio, duration, legibility and submission format afterward.
