# Public JobTrack class demo in AWS Academy Sandbox

The verified November 13 deployment is at **https://100-58-234-86.sslip.io/** while its AWS Academy Sandbox session, EC2 instance, public IPv4, and DNS remain available. The browser prompts for a shared demo password, kept only in ignored `work/public-demo-login.txt` on the deployment laptop. Do not commit or send that file to GitHub. Use fictional records only: the app has no individual accounts or user isolation.

## Current layout

- CloudFormation stack `jobtrack-final` in `us-east-1` creates EC2, encrypted EBS, and a security group with public TCP 80/443 plus SSH restricted to the operator's `/32`. The app listens on EC2 loopback port 8000.
- Nginx on EC2 redirects HTTP to HTTPS, requires HTTP Basic authentication, and proxies to the app. Let's Encrypt issued the certificate for the public IP's `sslip.io` hostname. Certbot installed a renewal timer; its usefulness depends on the instance and hostname remaining available.
- Private S3 stores the source ZIP. The pre-existing sandbox `myS3Role` instance profile reads it. The five database records are fictional. The earlier 50-request latency measurements used an SSH tunnel, so they do not describe public HTTPS latency.

## Reproduce or recover the public edge

1. Authenticate to the intended AWS Academy Sandbox and confirm its current public EC2 IP, stack status, and credit/session remaining. If the IP changed, construct a new `<dashed-ip>.sslip.io` hostname and verify its DNS A record points to the instance. A new IP needs a new certificate and an updated Nginx host configuration.
2. Confirm `deploy/cloudformation-sandbox.json` is the deployed stack template. Review a CloudFormation change set before executing, ensuring no EC2/EBS replacement. Do not make port 8000 public.
3. Over the restricted SSH connection, install Amazon Linux's `nginx`, `certbot`, and `python3-certbot-nginx` packages. Enable Nginx. Request the certificate with Certbot's Nginx authenticator for the verified hostname while port 80 is publicly reachable. The original issuance used `--non-interactive --agree-tos --register-unsafely-without-email`. Check `/etc/letsencrypt/live/<hostname>/` and the certificate expiry.
4. Generate a unique demo password. Put only its Apache MD5 hash in `/etc/nginx/jobtrack.htpasswd` as `jobtrack:<hash>` with owner `root`, group `nginx`, mode `640`. Store the plaintext only in the ignored local `work/public-demo-login.txt`, mode `600`. Never put it in a URL, command history, slides, poster, or repository. Replace `__PUBLIC_HOST__` in `deploy/nginx-public.conf.template` with the hostname and install it as `/etc/nginx/conf.d/jobtrack.conf`, mode `644`.
5. Run `nginx -t`, reload Nginx, and check `systemctl is-active nginx jobtrack`. From a client without the SSH tunnel, verify HTTP redirects to HTTPS, anonymous `/api/health` returns 401, authenticated health returns 200 and `{"status":"ok","database":"sqlite"}`, and the authenticated dashboard and job-discovery page load. A disposable fictional create/delete check should leave the original record count unchanged. The November 13 result is in `evidence/public-deployment-aws.json`.

The setup script/template does not create individual accounts. The same password reveals and permits edits to every demo record. Back up SQLite consistently before instance or stack deletion. The AWS Academy Sandbox may stop or clean up resources after its time-limited session; recheck immediately before the class presentation.

## Course submission

The 42 × 56 inch poster PDF and nine-slide PPTX were submitted November 13. The receipt and file locations are in `docs/FINAL_STATUS_2026-11-13.md`.
