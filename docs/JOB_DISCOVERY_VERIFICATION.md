# Job discovery verification — November 12, 2026

## Implemented and checked

- 23 Python tests pass (11 existing API + 12 discovery/configuration tests). Five Node extraction tests pass.
- Discovery tests cover persistent caching, local filters, missing credentials, publisher queries and alternate apply links, salary units, malformed listings/URLs, bounded provider failures, stale results, duplicate/concurrent saves, preservation of edits, deletion/resave, HTTP routes and cross-origin write rejection. Fixtures make no external API calls and consume no credits.
- Live Remotive call returned 14 listings on November 12 at 20:26 UTC. Counts change over time. API cache was reused for browser checks.
- Browser: Find jobs loads real results; “React” shows one result; Save imports Senior React Full-stack Developer at Lemon.io; reload retains the saved indicator and search; Applications displays the imported row. Indeed/LinkedIn without a key show an explicit connection prompt. The key itself is excluded from this document and all committed files.

## Limits

- Live JSearch search-v2 retrieval was verified after free-plan activation: 10 Indeed and 10 LinkedIn listings for software engineer in Chicago. The live response used `data.jobs` plus a pagination cursor; the adapter and regression tests now cover this format. Browser source selection displayed the matching publisher names and original URLs. A LinkedIn listing was saved and the saved indicator persisted after reload.
- The account uses Basic at $0/month, with a 200-request monthly hard limit as displayed during activation. No paid plan was selected. Five provider requests were used during integration debugging and verification; subsequent browser checks reused cached results.
- JSEARCH_API_KEY is read from the environment or a private local .env file. Explicit environment settings take precedence. The file is ignored by Git and excluded from archives. The key is never returned by the API or embedded in browser code.
- Remotive is a remote-only, delayed public selection. Indeed/LinkedIn come through JSearch rather than a direct partnership. Fresh clones require the user’s own API configuration.
- Refresh occurs only while the discovery page is open and visible. Existing applications are not automatically submitted or updated from provider listings.
- Docker configuration and source packaging now include jobs.py. Docker was not rerun in this environment.
- Existing AWS deployment and installed Chrome extension verification remain deferred; this feature does not change their status.
