# JobTrack — complete final-project handoff

**Read this first.** This guide was prepared November 5, 2026 for CSE 4333, **Group 42: Ahmad Salem and NoorAldeen Waleed**. It describes the included source as it actually stands, the final Canvas requirements, and the work needed to finish. It is a work plan, not evidence that the cloud app or final submissions are complete. Use fictional job records for testing. Keep AWS credentials, access keys, private emails, and real applicants' data out of screenshots and GitHub.

**November 6 update:** Ahmad directed that **nothing be turned in** and **nothing be deployed in the accessible Cloud Architecting Sandbox now**. Any submission steps below describe the eventual course process only. The current CloudFormation template targets a separate Learner Lab with `LabInstanceProfile`; that profile was absent in the inspected Sandbox. Follow the updated [`AWS_DEPLOYMENT.md`](AWS_DEPLOYMENT.md) when the deployment account is settled. The original checklist below is retained as project context.

## 1. Deliverables and hard deadline

Both final assignments are due **Friday, November 13, 2026 at 11:59 PM, America/Chicago**, and Canvas says they are available only until then. Finish and submit earlier. Save receipts.

| Deliverable | Exact destination | Format / content | Points |
| --- | --- | --- | --- |
| Final documentation | [Canvas: Project Final Documentation](https://uta.instructure.com/courses/282238/assignments/2405835) | **One PDF poster, 42 × 56 inches.** See section 8 for all required content. Canvas shows PDF as the permitted upload type and says one submission counts for everyone in the `Project Groups` group. | 50 |
| Final presentation | [Google Form linked from Canvas](https://forms.gle/j41x86jL6BVPT4edA) and [Canvas instructions](https://uta.instructure.com/courses/282238/assignments/2405836) | PowerPoint named **`Group42-JobTrack.pptx`**. The assignment says `Group<your group number>-<your system name>.pptx`; Group 42 and JobTrack are shown in the [course announcement](https://uta.instructure.com/courses/282238/discussion_topics/2515254). Google sign-in is required before the form fields can be inspected. | 20 |

The syllabus schedules in-class final presentations for **November 16 and 18**; Group 42's exact presentation day has not been confirmed. The final assignment pages do **not** require a final demo-video upload. The 5–10-minute video belonged to the midpoint assignment. A live demo is still worth rehearsing for class.

**Submission ownership:** agree which teammate uploads the poster and which submits the slides, then both check the receipts. Ahmad's Canvas group list previously did not show a Cloud `Project Groups` membership, so verify that the poster submission actually credits both people. The midpoint assignment still appeared **Missing** in Ahmad's Canvas view even though a teammate reportedly submitted it; get that teammate's receipt or instructor confirmation separately. Do not let that delay final work.

## 2. Current implementation and what is missing

The original one-page proposal describes a tracker for students, recent graduates and other job seekers, including company, title, salary, and application status. The current app substantially matches that core idea. It does **not** promise accounts, applying to employers, universal job-board scraping, or machine learning.

| Area | Current state | Final acceptance result needed |
| --- | --- | --- |
| Dashboard/API/SQLite | Runs locally; create, read, update, delete, search, filter, sort, status counts, restart persistence | Re-run tests and one human walkthrough on the final code |
| Chrome extension | Source and extraction tests exist; dashboard import was checked separately | Install unpacked extension in Chrome and complete toolbar → extraction → review → save → refresh on the bundled fixture |
| AWS | CloudFormation, S3 package script, and deployment guide are prepared; **no actual stack or cloud health check has been verified** | Live EC2/SSM deployment, service and health checks, cloud-backed CRUD, persistence, and redacted evidence |
| Performance | No measurements in repository | Repeatable measurements on the deployed service, with method/sample size/dataset/instance/region and honest interpretation |
| Final poster | Missing | 42 × 56 inch PDF with all Canvas sections, actual results and legible figures |
| Final slides | Only `presentation/JobTrack-Midpoint.pptx` exists; it says AWS is pending | Final PPTX with deployed architecture, demo/results, team roles, limitations |
| GitHub | `ReliWALEE/jobtrack-midpoint` HEAD was October 16 and matched the uploaded ZIP on November 5 | Push verified final changes/docs and confirm both teammates and grader can access it |

The local app is a **private single-user demo**. There is no login or per-user isolation. Do not expose port 8000 publicly or claim it is production-ready. Its Chrome extractor intentionally handles structured Schema.org `JobPosting` data; it is not a general scraper. The database on the EC2 root EBS disk survives stop/start but is lost if the instance/stack is deleted or replaced. Keep the instance until grading/presentation and take a tested backup before cleanup.

## Access and credentials needed

There are **no fixed JobTrack application credentials**: the current dashboard has no login. The source ZIP likewise contains no AWS key, GitHub token, S3 bucket name, AWS account number, VPC ID, or subnet ID. Those values must come from the authorized team/course account at deployment time. The following is the complete access checklist; fill in the nonsecret identifiers and confirm who can perform each action before starting:

| Access | Who needs it / where to get it | Verify before work |
| --- | --- | --- |
| **Shared GitHub repository** `ReliWALEE/jobtrack-midpoint` | Both teammates need their **own GitHub accounts** with access to the private repo. The repository owner invites the other teammate and, if required, the instructor/grader. Do not send a personal access token in the ZIP. | Both can open the repo; at least one can push; instructor access is confirmed. Record final commit ID. |
| **AWS Academy/course AWS account** | The deployment owner signs into the course-approved Learner Lab and obtains its **own current temporary CLI credentials/profile** using that program's instructions. These often expire; refresh as needed. The current template requires CloudFormation, EC2, S3, SSM and a pre-created `LabInstanceProfile`. | `aws sts get-caller-identity` returns the intended account; verify the instance profile and record **account alias/ID privately**, region, bucket, VPC and subnet. Do not paste access key, secret key or session token into the guide or repo. |
| **AWS Systems Manager** | The person who demos from the laptop needs permission to start a session to the deployed instance, AWS CLI v2 and the Session Manager plugin. If only one teammate has the course AWS account, that teammate should own the deployment and live demo. | Instance shows Online; `aws ssm start-session` works; port forward reaches the real EC2 app. |
| **UTA Canvas** | The poster submitter uses **their own UTA account**. Canvas should show the correct `Project Groups` membership so the group upload credits both. | Poster assignment can be opened; submission shows both members/receipt after upload. The submitter personally reviews the Turnitin acknowledgement. |
| **Google Form** | The slide submitter signs into a **Google account accepted by the course form**. The form requires sign-in; its internal fields were not visible in the November 5 read-only check. | Open the form while signed in, confirm any additional fields/file limits, submit `Group42-JobTrack.pptx`, save confirmation. |
| **Chrome extension/app** | No account or secret. Chrome must allow loading an unpacked extension for the demo, and the dashboard is at `http://127.0.0.1:8000` locally or through the authorized SSM tunnel. | The installed extension and full save/refresh flow work. |

**Do not include a UTA password or MFA seed in the teammate package.** Each teammate can submit with their own school account, and the personal UTA sign-in stored elsewhere in Ahmad's local workspace does not grant the missing AWS/GitHub project access. If an authorized course account needs shared access, use the course's supported invitation/role process or have its owner perform the deployment; do not copy long-lived personal credentials into a document.

## 3. Assign owners before editing

Write the real names, university emails and actual roles below before finalizing the poster. The proposal credits NoorAldeen with the idea and Ahmad with proposal review/editing; the final poster should describe actual **final development, cloud, testing, measurement, documentation, and presenting** contributions.

| Work | Owner | Done when |
| --- | --- | --- |
| AWS account/region, VPC/subnet, deployment, logs and backup | __________ | Deployed checks in section 5 pass |
| Dashboard/extension fixes and final regression test | __________ | Section 6 checklist passes |
| Benchmark/evidence/architecture diagram | __________ | Section 7 files and metrics exist |
| Poster design, content and PDF export | __________ | Section 8 checklist passes |
| Slides, rehearsal and Google Form submission | __________ | Section 9 and receipt pass |
| Poster upload and group-credit verification | __________ | Canvas receipt and both names confirmed |

Use one branch/repository as the source of truth. The provided ZIP is a snapshot. Do not independently modify two copies and then overwrite the other's changes. Create a shared change log of what changed, who verified it, and where the evidence is saved.

## 4. Unpack, run, and establish a clean baseline

Unzip the handoff archive and enter the **`jobtrack-midpoint-main/`** folder. Do not upload or run the outer archive directly as the AWS source package; the bootstrap expects the specially generated `JobTrack/` archive from `deploy/package_source.py`.

Requirements: Python 3.11+, current Chrome, Node.js 22+ for JavaScript tests. There are no third-party Python runtime dependencies. From the source root:

```sh
python3 -m unittest discover -s tests -v
node --test tests/extraction.test.cjs
python3 server.py
```

In a second terminal, open `http://127.0.0.1:8000/api/health` and `http://127.0.0.1:8000`. If demo records are useful, run `python3 seed_demo.py` **once** while the server is running. This creates only fictional records. The tests create temporary databases and should not affect the demo database. On November 5 the baseline was **11 Python tests and 5 JavaScript tests passing**; rerun after every code change. If a test fails, fix that before packaging or writing results.

Use the real GitHub repository for final source. Confirm the latest commit and compare it with the ZIP before editing. The ZIP matched GitHub commit `0c73738f9735a2e813c7c8a2037fb76e97123fa8` on November 5; any later commit supersedes it. Do not push runtime data, credentials, cache folders, or screenshots containing account identifiers.

## 5. Deploy the existing private AWS design and prove it works

The design is in `deploy/cloudformation.json` and `docs/AWS_DEPLOYMENT.md`: **EC2** runs the Python app; **encrypted EBS** stores SQLite; a private **S3** object delivers source; **IAM** lets the instance read that object and use **Systems Manager**; **CloudFormation** provisions resources. The security group has no inbound rules. The app binds to `127.0.0.1:8000` on EC2; users access it through an authenticated SSM port-forward. The selected subnet must have an Internet-gateway route and public IPv4 so bootstrap, S3, and SSM can be reached. This private design has **no public website URL**.

Use the approved Learner Lab account and region only after Ahmad resumes deployment. The current template uses its pre-created `LabInstanceProfile`, so verify that profile exists and supports S3/SSM before stack creation. The inspected Cloud Architecting Sandbox lacks it and is **not** the deployment target. Confirm cost/credit availability and keep track of resources left running.

Set these values in your shell; replace the capitalized placeholders with **actual account values**, and use the same region for the S3 bucket and stack:

The example assumes a named AWS CLI profile. If AWS Academy gives you temporary environment credentials instead, follow the lab's official CLI setup, **omit the `AWS_PROFILE` line**, and refresh those credentials when they expire. Never paste them into this guide, screenshots, or GitHub. Install AWS CLI v2 and the Session Manager plugin if missing.

```sh
export AWS_PROFILE=YOUR_AUTHENTICATED_PROFILE
export AWS_REGION=us-east-1
export JOBTRACK_BUCKET=YOUR_PRIVATE_BUCKET_NAME
export JOBTRACK_VPC_ID=vpc-xxxxxxxx
export JOBTRACK_SUBNET_ID=subnet-xxxxxxxx
aws sts get-caller-identity
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,IsDefault,CidrBlock]' --output table
aws ec2 describe-subnets --filters Name=vpc-id,Values=$JOBTRACK_VPC_ID --query 'Subnets[*].[SubnetId,AvailabilityZone,MapPublicIpOnLaunch,CidrBlock]' --output table
```

Confirm the account ID is the intended course account. Confirm the subnet belongs to the VPC and has an Internet-gateway route; `MapPublicIpOnLaunch` alone does not prove its route table is public. The template itself explicitly assigns a public IPv4, yet its security group allows **zero inbound** ports. If no suitable VPC/subnet is available, resolve that before deployment. Choose an existing private S3 bucket in the same region with Block Public Access enabled, or create one through the course-approved process.

From the source root, package and inspect the required top-level `JobTrack/` directory, upload it, validate the template against AWS, and deploy:

```sh
python3 deploy/package_source.py
unzip -l work/JobTrack-source.zip | head -20
aws s3 cp work/JobTrack-source.zip s3://$JOBTRACK_BUCKET/jobtrack/JobTrack-source.zip
aws cloudformation validate-template --template-body file://deploy/cloudformation.json
aws cloudformation deploy --stack-name jobtrack-final --template-file deploy/cloudformation.json --parameter-overrides VpcId=$JOBTRACK_VPC_ID SubnetId=$JOBTRACK_SUBNET_ID SourceBucket=$JOBTRACK_BUCKET SourceKey=jobtrack/JobTrack-source.zip InstanceProfileName=LabInstanceProfile
aws cloudformation describe-stacks --stack-name jobtrack-final --query 'Stacks[0].[StackStatus,Outputs]' --output json
aws cloudformation describe-stack-resource --stack-name jobtrack-final --logical-resource-id Instance --query 'StackResourceDetail.PhysicalResourceId' --output text
```

Record the instance ID from the last command as `JOBTRACK_INSTANCE_ID`. If deployment fails, inspect **CloudFormation → Stack → Events**, then fix the specific error. The prepared template's bootstrap has **not** been tested against AWS; `CREATE_COMPLETE` alone does not prove the app started.

Confirm the instance is **Online** in Systems Manager. Start a shell session and check the app on EC2:

```sh
aws ssm describe-instance-information --filters Key=InstanceIds,Values=YOUR_INSTANCE_ID --query 'InstanceInformationList[*].[InstanceId,PingStatus]' --output table
aws ssm start-session --target YOUR_INSTANCE_ID
```

Inside the instance's SSM shell:

```sh
sudo systemctl status jobtrack --no-pager
sudo journalctl -u jobtrack --no-pager -n 80
sudo tail -n 80 /var/log/cloud-init-output.log
curl --fail http://127.0.0.1:8000/api/health
```

Expect a JSON health response with `"status": "ok"`. If not, diagnose package installation, S3 read permissions, source-ZIP layout, `WorkingDirectory`, outbound network access, or service errors. Save a redacted screenshot/log excerpt of the resolved result. Do not mark AWS complete until it works.

On the presenter laptop, make sure local port 8000 is free and the AWS Session Manager plugin is installed. Start the tunnel in a separate terminal; leave it open:

```sh
aws ssm start-session --target YOUR_INSTANCE_ID --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8000"],"localPortNumber":["8000"]}'
```

Now `http://127.0.0.1:8000` reaches the **EC2** app. Create one fictional record, edit its status, refresh, filter/search it, and delete that specific disposable record. Create another fictional record, stop/start the `jobtrack` service, and verify it persists; then delete it. If testing instance stop/start, allow time for SSM to reconnect. Record stack ID, instance ID, region, instance type, successful health, and date, but redact account IDs/tokens in public materials.

**Update behavior:** simply uploading a new ZIP to S3 does not reliably redeploy code to an already-running instance; CloudFormation `UserData` is not an application updater. Before any code change after initial deployment, make a database backup, then explicitly update the installed source/service, or safely replace the instance after planning for data loss. Re-run all cloud checks and metrics on the **final** deployed revision. The template's `midpoint` labels and old docs should be changed to final language once results are real, but labels are less important than a verified deployment.

**Backup:** before replacement/deletion, use Python `sqlite3.Connection.backup()` to create a consistent SQLite backup; copy that backup to private S3 and test a restore. Do not just copy a live `.sqlite3` file while WAL writes may be active. Keep the AWS stack running through the class presentation and grading unless the instructor says otherwise. After it is no longer needed, back up, delete the stack, remove the source object/bucket if appropriate, and check for continuing charges.

## 6. Installed extension and full functional acceptance

In Chrome, open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select `extension/`. Pin **JobTrack Capture**. Do this on a machine/browser authorized for the course demo. Start the local server or SSM tunnel, then visit `http://127.0.0.1:8000/demo-job.html`. Click the extension, **Extract current posting**, review the preview, and **Review in dashboard**. Confirm the editable draft shows fictional **Northstar Labs**, **Software Engineer Intern**, **Austin TX**, **Internship**, and **65000** annual USD; correct anything missing, save, refresh, and verify the record persists. Test an unsupported page and confirm it displays a useful message. Remove only test records afterwards.

Then run a complete dashboard walkthrough against the **cloud-backed** instance: add, edit, refresh, search, filter by status/employment/salary, sort salary, reset filters, confirm delete, and verify empty/error feedback. Test a narrow/mobile viewport if the UI changes. Record only what you actually observed. The extractor depends on Schema.org JSON-LD and does not guarantee arbitrary job boards, authenticated sites, or iframes. If Chrome installation or capture fails, fix the specific issue and rerun; do not present unit tests as installed-extension proof.

## 7. Performance and evidence: make results defensible

The poster explicitly requires performance evaluation. The included `tools/benchmark.py` makes **read-only sequential GET** requests to health, list, and search endpoints and reports count, mean, median, p95, min, and max in milliseconds. It does not create/delete records. Use a fictional dataset; record its size, instance type, region, client location, and whether the SSM tunnel is involved. For a small but valid comparison, measure with 0 records and again after seeding demo data. If the dataset is tiny, say so. Never call this a stress or scalability test; it measures client-to-service latency for a small single-user demo.

With the SSM tunnel open and confirmed to point at EC2:

```sh
mkdir -p evidence
python3 tools/benchmark.py --base-url http://127.0.0.1:8000 --requests 50 --warmup 5 --output evidence/performance-aws.json
```

The script prints and saves the same JSON. Check `database_records`, timestamp, and that all results completed without errors. If you also run it locally, label that result `performance-local.json`; do not confuse a local result with AWS. Add one small table or chart to the poster, identify the measurement method, and explain the result and limitations. Functional proof should include redacted screenshots of CloudFormation stack complete, SSM instance online/service active, health response, dashboard on AWS, installed extension flow, and the final test command result. Save the commands/outputs or a concise verification log in `evidence/`. Before sharing, remove account numbers, ARNs, tokens, private URLs, real personal data, and unrelated browser tabs.

An architecture diagram should show: **Chrome extension → dashboard browser → SSM port forward → EC2 Python API/static files → SQLite on encrypted EBS**, plus **CloudFormation provisioning**, **private S3 source package**, and **IAM role**. Do not draw an Internet-facing application load balancer, RDS, Lambda, or public HTTPS URL unless actually deployed. Discuss alternatives (e.g. API Gateway/Lambda + DynamoDB, EC2 + RDS, public HTTPS with authentication) as alternatives, not implemented components.

## 8. Poster PDF: exact Canvas outline and export QA

Make a **42 × 56 inch poster** (portrait or landscape unless the instructor clarifies orientation) and export a **PDF**. Do not submit the midpoint slide deck or a letter-size document in its place. Canvas's rough outline is:

1. **Title/team:** JobTrack, Group 42, both full names, school emails, and truthful roles.
2. **Summary:** application, problem, main cloud services actually used, and key measured/functional results.
3. **Introduction:** application-tracking pain point, solution, target users and concrete use cases.
4. **System architecture:** high-level diagram, each component, data flow and access path, and alternatives considered with why the chosen design fits the class demo.
5. **Application logic/services:** backend, validation, SQLite data model, REST endpoints (`GET /api/health`, `GET/POST /api/applications`, `PUT/DELETE /api/applications/{id}`), frontend/dashboard and extension flow.
6. **ML, if applicable:** there is no ML in this app. A short “Not applicable; no ML component” is honest. Do not invent one.
7. **Performance evaluation:** setup, sample sizes, dataset size, AWS region/instance, actual numbers, a graph/table, interpretation and limitations.
8. **Challenges and lessons:** real issues encountered, what was changed, what was learned about deployment/SSM/SQLite/extension; do not fabricate obstacles.
9. **Future work:** authentication/multi-user isolation, managed database/backups, HTTPS public hosting, broader extraction, monitoring, if relevant. Clearly label these as future work.
10. **Conclusion:** what was built and verified, value to users, and limits.

Use real application screenshots, the architecture diagram and one legible results chart. Avoid dense prose. Export and open the PDF at 100% and at full-page zoom. Check spelling, names, dates, diagram labels, image quality, no clipped text, and that all claims match current evidence. Check PDF dimensions using `pdfinfo`: **42 × 56 inches = 3024 × 4032 PDF points**, either orientation. Do not add an AWS logo or service to the “implemented” diagram if it was not used. Include a repository link/QR only if grader access is verified.

## 9. Final presentation and classroom demo

Create a new **PowerPoint** rather than submitting `JobTrack-Midpoint.pptx` unchanged. Recommended 8–10-slide flow (the final Canvas page gives no required slide count or speaking length): title/team; problem/users; solution/live workflow; actual cloud architecture; app logic/API/data; extension; deployment and verification; measured performance; challenges/limits/future work; conclusion/contributions. Use screenshots/figures instead of text walls. Every “deployed,” “tested,” or “measured” claim must have corresponding evidence. Remove old statements that say AWS is pending once it is actually verified; if deployment still fails, state the true status and do not present mock data as cloud results.

Save exactly **`Group42-JobTrack.pptx`** unless a later official group-number update changes it. Open the actual PPTX on the presenting machine, check fonts/images/animations, rehearse speaker transitions and a short live dashboard demo. Establish the SSM tunnel before class; keep a clearly labeled screenshot or recording fallback in case the classroom network interrupts the demo. Do not depend on a public URL: the current app has none. Confirm the precise presentation day with course announcements/instructor.

The Google Form requires Google sign-in; its internal fields were not visible without it on November 5. The submitting teammate should sign in, inspect all form fields, upload the PPTX, submit, and save the confirmation page/email. The Canvas page itself only gives the form link and filename rule; do not assume uploading a PPTX to Canvas substitutes for the form.

## 10. Final source, submissions, and receipt check

Before submission, push the final tested source and updated `README.md`, `docs/ARCHITECTURE.md`, `docs/AWS_DEPLOYMENT.md`, and `docs/VERIFICATION.md` to the shared GitHub repository. The docs must describe the final deployed state and actual measurements; remove false midpoint-only statements. Check GitHub Actions for the final commit. Verify the instructor/teammate can open the repository; a private URL by itself is not proof of access. If repository access cannot be granted, ask the instructor for an accepted alternative before the deadline.

Upload **only the final poster PDF** to [Canvas Final Documentation](https://uta.instructure.com/courses/282238/assignments/2405835). Canvas currently displays a Turnitin academic-integrity acknowledgement/EULA checkbox before submission; the submitting student must review and agree themselves. After pressing Submit Assignment, verify the submitted filename and timestamp in Canvas. Confirm the group-submission credit for both members.

Submit **`Group42-JobTrack.pptx` through the Google Form** and save the form receipt. Both submissions should be complete by November 13, 11:59 PM Central. After any revision, confirm the *latest* file/attempt is the one visible in the receipt. Keep final copies and evidence together in the course project folder. Do not delete the AWS resources before the presentation/grade evidence is secure; then perform the backup and cleanup in section 5.

### Stop conditions: do not say “done” until all are checked

- [ ] Final GitHub revision identified; tests pass; no secrets or runtime data committed.
- [ ] AWS stack and service verified; SSM tunnel reaches EC2; cloud-backed CRUD and persistence verified.
- [ ] Installed Chrome extension end-to-end verified, or its real limitation accurately documented.
- [ ] Benchmark JSON, setup details, screenshots/logs, and truthful architecture diagram saved.
- [ ] 42 × 56 inch poster PDF visually inspected and submitted to Canvas; receipt saved; group credit checked.
- [ ] `Group42-JobTrack.pptx` visually inspected and submitted through Google Form; receipt saved.
- [ ] Teammates agree on roles/contributions and can present the work without relying on unverified claims.
- [ ] Midpoint “Missing” discrepancy followed up with teammate/instructor separately.
