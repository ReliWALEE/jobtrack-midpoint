# Job discovery verification — November 12, 2026

## Implemented and checked

- 21 Python tests pass (11 existing API + 10 discovery tests). Five Node extraction tests pass.
- Discovery tests cover persistent caching, local filters, missing credentials, publisher queries and alternate apply links, salary units, malformed listings/URLs, bounded provider failures, stale results, duplicate/concurrent saves, preservation of edits, deletion/resave, HTTP routes and cross-origin write rejection. Fixtures make no external API calls and consume no credits.
- Live Remotive call returned 14 listings on November 12 at 20:26 UTC. Counts change over time. API cache was reused for browser checks.
- Browser: Find jobs loads real results; “React” shows one result; Save imports Senior React Full-stack Developer at Lemon.io; reload retains the saved indicator and search; Applications displays the imported row. Indeed/LinkedIn without a key show an explicit connection prompt. No provider credentials are present in this verification.

## Limits

- JSearch request/response handling and publisher filtering are fixture tested. No live JSearch API key is configured, so live Indeed/LinkedIn retrieval remains unverified and unavailable until the user connects one.
- Remotive is a remote-only, delayed public selection. It is not a substitute claim for an active Indeed/LinkedIn connection.
- Refresh occurs only while the discovery page is open and visible. Existing applications are not automatically submitted or updated from provider listings.
- Docker configuration and source packaging now include jobs.py. Docker was not rerun in this environment.
- Existing AWS deployment and installed Chrome extension verification remain deferred; this feature does not change their status.
