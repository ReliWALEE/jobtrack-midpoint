"""Measure read-only JobTrack HTTP latency through a local or forwarded URL.

This creates no application records and sends no source data to another service.
Use fictional demo data when measuring the deployed instance.
"""

import argparse
import json
import math
import statistics
import time
from datetime import datetime, timezone
from urllib.request import urlopen


def request(url):
    started = time.perf_counter()
    with urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"{url}: HTTP {response.status}")
        body = response.read()
    return (time.perf_counter() - started) * 1000, body


def summarize(samples):
    ordered = sorted(samples)
    return {
        "count": len(ordered),
        "mean_ms": round(statistics.mean(ordered), 2),
        "median_ms": round(statistics.median(ordered), 2),
        "p95_ms": round(ordered[math.ceil(0.95 * len(ordered)) - 1], 2),
        "min_ms": round(ordered[0], 2),
        "max_ms": round(ordered[-1], 2),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--output", help="Write the JSON result to this file")
    args = parser.parse_args()
    if not 1 <= args.requests <= 10000 or not 0 <= args.warmup <= 1000:
        parser.error("requests must be 1-10000 and warmup must be 0-1000")

    base = args.base_url.rstrip("/")
    endpoints = {
        "health": "/api/health",
        "list_all": "/api/applications",
        "search_engineer": "/api/applications?q=Engineer",
    }
    _, body = request(base + endpoints["list_all"])
    records = json.loads(body)
    if not isinstance(records, list):
        raise RuntimeError("List endpoint did not return an array")

    results = {}
    for label, path in endpoints.items():
        url = base + path
        for _ in range(args.warmup):
            request(url)
        samples = [request(url)[0] for _ in range(args.requests)]
        results[label] = summarize(samples)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "database_records": len(records),
        "requests_per_endpoint": args.requests,
        "warmup_per_endpoint": args.warmup,
        "method": "sequential GET requests from client to URL; includes SSH tunnel when used",
        "results": results,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
