# GitHub repository

The private repository is [ReliWALEE/jobtrack-midpoint](https://github.com/ReliWALEE/jobtrack-midpoint). Account authorization and repository creation are complete. Source was uploaded incrementally:

1. [Backend API, SQLite persistence and tests](https://github.com/ReliWALEE/jobtrack-midpoint/commit/bba038934bc278ed2dc8ee4c2b33a8a97efea4f8)
2. [Dashboard, filters, sorting and demo records](https://github.com/ReliWALEE/jobtrack-midpoint/commit/eba8c84dfc6ac910d419d337370a886bf6923ecc)
3. [Chrome extension and extraction tests](https://github.com/ReliWALEE/jobtrack-midpoint/commit/a15274c7edc52dc1a874193fc393c55dcf6a21e6)
4. This handoff adds documentation, deployment configuration, the CI workflow, screenshots and the midpoint presentation.

The workflow runs the Python API/database tests and Node extraction tests on pushes and pull requests. [Open GitHub Actions](https://github.com/ReliWALEE/jobtrack-midpoint/actions) to inspect the actual hosted status for a commit. Local test results appear in `VERIFICATION.md`.

## Clone and run

Authenticate with a GitHub account authorized to read the private repository, then run:

```sh
git clone https://github.com/ReliWALEE/jobtrack-midpoint.git
cd jobtrack-midpoint
python3 server.py
```

Open `http://127.0.0.1:8000`. For later changes, use a normal local commit and push with your own configured Git identity. Check staged files first. Keep `data/`, credentials, local environments and caches untracked. Do not paste tokens into source files. No license or branch-protection policy has been chosen on your behalf.

The presentation lives at `presentation/JobTrack-Midpoint.pptx`. The recording script lives at `docs/DEMO_SCRIPT.md`. No video recording is included, and no live AWS deployment is claimed.
