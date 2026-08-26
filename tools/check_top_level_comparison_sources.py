#!/usr/bin/env python3
"""Check every official URL in the top-level comparison source manifest."""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "top-level-town-comparison-sources.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
)

# These official Granicus sites reject command-line clients while continuing to
# serve and be indexed in normal browser/search contexts. Each URL was opened or
# independently re-crawled on the manifest review date. Keep this list explicit:
# a new 403 must fail until it has been checked outside curl.
VERIFIED_ACCESS_RESTRICTED = {
    "https://www.maplewoodnj.gov/": "2026-08-26",
    "https://www.montclairnjusa.org/Government/Departments/Finance-and-Taxes/Municipal-Assessor": "2026-08-26",
    "https://www.montclairnjusa.org/Government/Departments/Planning-Community-Development": "2026-08-26",
}


def records() -> list[dict[str, str]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    values = [*payload["shared_sources"]]
    for place in payload["places"].values():
        values.extend(place["sources"])
    unique = {record["url"]: record for record in values}
    for url in unique:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError(f"source must use an absolute HTTPS URL: {url}")
    return [unique[url] for url in sorted(unique)]


def check(record: dict[str, str]) -> tuple[dict[str, str], int, str, str]:
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
    error = completed.stderr.strip()
    return record, status, final_url, error


def main() -> int:
    source_records = records()
    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(check, record): record for record in source_records}
        for future in as_completed(futures):
            results.append(future.result())

    failures = []
    access_restricted = []
    for record, status, final_url, error in sorted(results, key=lambda item: item[0]["id"]):
        direct_pass = 200 <= status < 400
        verified_block = (
            status == 403
            and VERIFIED_ACCESS_RESTRICTED.get(record["url"]) == record["accessed"]
        )
        passed = direct_pass or verified_block
        marker = "PASS" if direct_pass else "PASS-ACCESS" if verified_block else "FAIL"
        print(f"{marker} {status:03d} {record['id']} -> {final_url or record['url']}")
        if verified_block:
            access_restricted.append(record["url"])
        if not passed:
            failures.append((record["url"], status, error))

    if failures:
        print(f"official source check failed: {len(failures)} of {len(source_records)} URL(s)", file=sys.stderr)
        for url, status, error in failures:
            print(f" - {status:03d} {url} {error}", file=sys.stderr)
        return 1
    suffix = (
        f"; {len(access_restricted)} official page(s) access-restricted to curl "
        "and independently verified on the manifest review date"
        if access_restricted
        else ""
    )
    print(f"official source check passed: {len(source_records)} URL(s){suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
