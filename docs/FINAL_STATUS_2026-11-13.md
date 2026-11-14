# JobTrack Group 42 final status — November 13, 2026

This is the current status for Ahmad Salem and NoorAldeen Waleed. It supersedes the November 5–6 planning language in the older handoff documents. The Canvas and Google Form submissions are pending.

## Final files ready for review

- `deliverables/JobTrack-poster-final.pdf`: one page, 42 × 56 inches. It includes the implemented workflow, architecture, design alternatives, cloud services, measured performance, tests, limitations, roles, and conclusion.
- `deliverables/Group42-JobTrack.pptx`: nine editable 16:9 slides with the current job-discovery feature, deployed architecture, measured results, and team roles. The filename follows the course's Group 42 convention.
- These files use fictional demonstration records only. Open both and check their content before course submission.

## Verified source and deployment

- Source base: upstream `ReliWALEE/jobtrack-midpoint` commit `a59f8d0`, merged from Ahmad's PR #1 and updated with NoorAldeen's November 12 job-discovery work. Local branch `final-nov13` adds the sandbox-specific deployment template, observed evidence, updated diagrams, and final artifact builders. The deployed application package includes the upstream source at `a59f8d0`.
- `23` Python tests and `5` JavaScript extractor tests passed locally on November 13.
- AWS Academy Cloud Architecting **Sandbox** in `us-east-1`: CloudFormation stack `jobtrack-final` reached `CREATE_COMPLETE`. It created a `t3.micro` Amazon Linux 2023 EC2 instance, 12 GiB encrypted gp2 root EBS, and a security group permitting TCP 22 only from the deployment client's single `/32` IPv4. The web app listens only on EC2 loopback port 8000. No public web port is open.
- The instance uses the pre-existing `myS3Role` profile to fetch the source ZIP from a private, public-access-blocked, AES256-encrypted S3 bucket. The original Learner Lab design in `deploy/cloudformation.json` remains separate; the deployed sandbox design is `deploy/cloudformation-sandbox.json`.
- The `jobtrack` systemd service was active. `/api/health` through an SSH local port forward returned `{"status":"ok","database":"sqlite"}`. A fictional application was created, updated to Interview, found after restarting the service, then deleted. The final database retained five fictional demo records. The deployed Remotive discovery endpoint returned 16 listings; JSearch is optional and was not configured on the EC2 instance.
- A consistent SQLite backup was made with `sqlite3.Connection.backup()` and copied to ignored `work/jobtrack-backup.sqlite3`. A local `PRAGMA integrity_check` returned `ok`, and the backup contained the same five fictional applications.
- `evidence/performance-aws.json` records 50 sequential GET requests per endpoint after five warmups, from the Mac through the SSH tunnel to EC2, with five fictional records. Health median/p95: 127.66/147.32 ms. List: 161.33/214.06 ms. Search: 124.25/199.81 ms. This is single-user HTTP latency, not a throughput or scalability test. The method includes network and SSH tunnel time.
- Supporting redacted records: `evidence/deployment-aws.json`, `evidence/cloud-crud-2026-11-13.json`, and `evidence/performance-aws.json`. No AWS access key or session token belongs in these files or GitHub.

## Access and limits

- The course sandbox is a **three-hour lab session**. Recheck that the stack and instance still exist and start a fresh session if necessary before the November 16/18 class presentation. A live demo needs the restricted SSH tunnel from an authorized client IP; a changed client IP requires updating the security group's SSH rule. Do not expose port 8000 directly.
- The root EBS volume is deleted on instance termination. Back up the SQLite database before stack deletion or replacement. The app has no user accounts or public HTTPS URL.
- The installed Chrome/Brave extension toolbar remains unverified. Its extractor unit tests and dashboard draft import flow passed separately. Demonstrate it only after a real installed extension check, or describe that limit honestly.
- The current poster and slides are final review files, but the Canvas and Google Form receipts are still pending. The Canvas poster upload requires the submitting student to accept Turnitin's End-User License Agreement, and the Google Form requires a signed-in Google account.

## Submission destinations after the pause

1. [Canvas Project Final Documentation](https://uta.instructure.com/courses/282238/assignments/2405835): upload the poster PDF and check the group receipt.
2. [Google Form for Project Final Presentation](https://forms.gle/j41x86jL6BVPT4edA): upload `Group42-JobTrack.pptx` and save the confirmation. The files are due November 13 at 11:59 PM Central.

The sandbox account's temporary CLI credentials are kept outside the repository and should be deleted after use. The private SSH key is under ignored `work/` for this lab session. Do not publish either credential.
