# AWS deployment preparation

Status: configuration prepared and JSON checked locally. No AWS deployment, AWS template validation, bootstrap execution, Docker build, or public URL has been verified. This machine has no AWS CLI/account session available. This is a private single-user midpoint demo, not a production service.

## Design

One Amazon Linux 2023 EC2 instance runs the same Python API and static dashboard. SQLite lives at `/var/lib/jobtrack/jobtrack.sqlite3` on the encrypted root EBS volume. A systemd service restarts the process. The security group has no inbound rules, and the application listens on loopback. Access uses an authenticated AWS Systems Manager port-forwarding session. The instance needs outbound HTTPS access to package repositories, S3 and SSM. Select a public subnet with an Internet gateway route and public IPv4 assignment. Public IPv4, EC2, EBS and S3 may incur charges.

This design keeps the demo private without adding a login system. Database contents survive process restarts and instance stop/start. Stack deletion or instance replacement destroys the root volume and data. Back up before either action. There is no automatic backup, failover, or multi-instance database sharing. Do not enter real personal data during the demo.

## Account actions needed

You must authorize an AWS account/profile, choose a region, an existing VPC and compatible subnet, and approve resource costs. The deploying principal needs CloudFormation, EC2, IAM role/profile creation and pass-role, S3 upload/read, and SSM session permissions. The template acknowledges IAM creation with `CAPABILITY_IAM`. Organization policies or encrypted S3 objects using custom KMS keys may require additional permissions. No credentials belong in this repository.

Install AWS CLI v2 and the Session Manager plugin, then authenticate using your institution's supported login (for example `aws sso login --profile YOUR_PROFILE`). Choose your profile and region through environment variables or CLI configuration. Confirm the account with `aws sts get-caller-identity` before creating anything.

1. Run `python3 deploy/package_source.py` from the repository root. This creates `work/JobTrack-source.zip` with the required top-level `JobTrack/` directory. Create or select a private S3 bucket in your region and keep Block Public Access enabled. Upload this ZIP under key `jobtrack/JobTrack-source.zip`. Do not upload the full presentation package or GitHub’s default download ZIP, which uses a different top-level folder.
2. Validate with your authenticated account:

```sh
aws cloudformation validate-template --template-body file://deploy/cloudformation.json
```

3. Replace the capitalized values below. Run from the repository root:

```sh
aws cloudformation deploy --stack-name jobtrack-midpoint \
  --template-file deploy/cloudformation.json --capabilities CAPABILITY_IAM \
  --parameter-overrides VpcId=VPC_ID SubnetId=SUBNET_ID SourceBucket=BUCKET_NAME SourceKey=jobtrack/JobTrack-source.zip
aws cloudformation describe-stacks --stack-name jobtrack-midpoint --query 'Stacks[0].Outputs'
```

4. Wait for SSM to list the instance as online. Stack creation success alone does not verify bootstrap. Start a shell through `aws ssm start-session --target INSTANCE_ID` and check:

```sh
sudo systemctl status jobtrack
sudo journalctl -u jobtrack --no-pager -n 50
sudo tail -n 50 /var/log/cloud-init-output.log
curl http://127.0.0.1:8000/api/health
```

The health response must say `ok`. If bootstrap fails, investigate package availability, S3 permissions, ZIP directory layout, or outbound connectivity. The template has not been run against AWS.

5. Stop the local server first if it occupies port 8000. In a new terminal:

```sh
aws ssm start-session --target INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8000"],"localPortNumber":["8000"]}'
```

Open `http://127.0.0.1:8000`. The extension dashboard address stays the same while the tunnel runs. Repeat the CRUD and refresh checks against this instance. Record the stack ID, instance ID, health result, and date before calling deployment verified.

## Backup, update and cleanup

Before replacement/deletion, use a session to create a consistent SQLite backup with Python's `sqlite3.Connection.backup()` and copy it to a private S3 bucket. Test restoring the backup locally. Do not copy only a live `.sqlite3` file while WAL writes may be active.

For updates, upload a new source ZIP, stop the service, unpack into a new application directory, and change the unit's WorkingDirectory after reviewing the files. Keep the database directory separate. Updating UserData does not reliably rerun the installer on an existing instance. Plan this explicitly rather than treating a stack update as an application rollout.

When the demo is over, back up anything needed and delete the stack with `aws cloudformation delete-stack --stack-name jobtrack-midpoint`. Confirm completion and remove the S3 source object/bucket if no longer needed. Check for other resources and retained backups that may continue to incur charges.

For public production hosting, add authentication and per-user authorization, a hardened application server, TLS, managed database/backups and monitoring before exposing inbound traffic.

## Official references

- [Amazon Linux 2023 AWS CLI v2](https://docs.aws.amazon.com/linux/al2023/ug/awscli2.html)

- [Session Manager port forwarding](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html)
- [EC2 CloudFormation resource](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ec2-instance.html)
- [EBS root volume deletion behavior](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-ec2-instance-ebs.html)
