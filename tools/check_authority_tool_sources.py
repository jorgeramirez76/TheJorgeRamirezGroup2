#!/usr/bin/env python3
"""Check every external primary URL in the authority/tools source registry."""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "authority-tools-sources.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
)
ALLOWED_HOSTS = {
    "www.nj.gov",
    "www.consumerfinance.gov",
    "www.njrealtor.com",
}


def records() -> list[dict]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    unique = {record["url"]: record for record in payload["sources"]}
    if len(unique) != len(payload["sources"]):
        raise ValueError("source registry contains duplicate URLs")
    for record in unique.values():
        parsed = urlsplit(record["url"])
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError(f'non-primary or non-HTTPS source: {record["url"]}')
        if record["accessedOn"] != payload["reviewedOn"]:
            raise ValueError(f'source review date drift: {record["id"]}')
    return sorted(unique.values(), key=lambda record: record["id"])


def check(record: dict) -> tuple[dict, int, str, str]:
    completed = subprocess.run(
        [
            "curl",
            "--location",
            "--silent",
            "--show-error",
            "--max-time",
            "25",
            "--retry",
            "1",
            "--retry-all-errors",
            "--user-agent",
            USER_AGENT,
            "--output",
            "/dev/null",
            "--write-out",
            "%{http_code}\t%{url_effective}",
            record["url"],
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    status_text, _, final_url = completed.stdout.strip().partition("\t")
    status = int(status_text) if status_text.isdigit() else 0
    return record, status, final_url, completed.stderr.strip()


def main() -> int:
    source_records = records()
    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(check, record) for record in source_records]
        for future in as_completed(futures):
            results.append(future.result())

    failures = []
    for record, status, final_url, error in sorted(results, key=lambda item: item[0]["id"]):
        final_host = urlsplit(final_url).hostname if final_url else None
        passed = 200 <= status < 400 and final_host in ALLOWED_HOSTS
        print(f'{"PASS" if passed else "FAIL"} {status:03d} {record["id"]} -> {final_url or record["url"]}')
        if not passed:
            failures.append((record["url"], status, final_url, error))
    if failures:
        print(f"authority/tool source check failed: {len(failures)} of {len(source_records)} URL(s)", file=sys.stderr)
        for url, status, final_url, error in failures:
            print(f" - {status:03d} {url} -> {final_url or '-'} {error}", file=sys.stderr)
        return 1
    print(f"authority/tool source check passed: {len(source_records)} URL(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
