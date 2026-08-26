#!/usr/bin/env python3
"""Synchronize evidence-backed retired and malformed search routes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECOVERY_MANIFEST = ROOT / "data" / "search-console-route-recovery.json"
TOWN_MANIFEST = ROOT / "data" / "indexable-town-risk-decisions.json"
VERCEL_CONFIG = ROOT / "vercel.json"
SITE = "https://thejorgeramirezgroup.com"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_routes() -> dict[str, str]:
    recovery = load_json(RECOVERY_MANIFEST)
    routes = {
        str(item["source"]): str(item["destination"])
        for item in recovery["routes"]
    }
    town_manifest = load_json(TOWN_MANIFEST)
    for item in town_manifest["incomingRedirectFamilies"]:
        source = str(item["source"])
        destination = str(item["destination"])
        existing = routes.setdefault(source, destination)
        if existing != destination:
            raise RuntimeError(f"conflicting redirect destination for {source}")
    return routes


def is_pattern(rule: dict) -> bool:
    source = str(rule.get("source", ""))
    return bool(rule.get("has") or any(mark in source for mark in (":", "*", "(")))


def render_config(config: dict, mappings: dict[str, str]) -> str:
    redirects = config["redirects"]
    seen: set[str] = set()
    for rule in redirects:
        source = str(rule.get("source", ""))
        if source not in mappings:
            continue
        if source in seen:
            raise RuntimeError(f"duplicate managed redirect: {source}")
        rule.clear()
        rule.update(
            source=source,
            destination=mappings[source],
            permanent=True,
        )
        seen.add(source)

    additions = [
        {"source": source, "destination": destination, "permanent": True}
        for source, destination in mappings.items()
        if source not in seen
    ]
    insertion = next(
        (index for index, rule in enumerate(redirects) if is_pattern(rule)),
        len(redirects),
    )
    config["redirects"] = redirects[:insertion] + additions + redirects[insertion:]
    return json.dumps(config, indent=2) + "\n"


def local_path(route: str) -> Path:
    relative = route.strip("/")
    if not relative:
        return ROOT / "index.html"
    html_path = ROOT / f"{relative}.html"
    if html_path.exists():
        return html_path
    return ROOT / relative / "index.html"


def issues() -> list[str]:
    mappings = expected_routes()
    config = load_json(VERCEL_CONFIG)
    problems: list[str] = []
    if config.get("cleanUrls") is not True:
        problems.append("vercel cleanUrls must remain enabled for .html normalization")
    by_source: dict[str, list[dict]] = {}
    for rule in config["redirects"]:
        by_source.setdefault(str(rule.get("source", "")), []).append(rule)
    redirect_sources = set(by_source)
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sitemap += (ROOT / "sitemap-es.xml").read_text(encoding="utf-8")
    for source, destination in mappings.items():
        rules = by_source.get(source, [])
        if len(rules) != 1:
            problems.append(f"{source}: expected one redirect, found {len(rules)}")
            continue
        rule = rules[0]
        if rule.get("destination") != destination or rule.get("permanent") is not True:
            problems.append(f"{source}: redirect mismatch")
        if rule.get("has") or "statusCode" in rule:
            problems.append(f"{source}: exact permanent redirect has extra routing conditions")
        if destination in redirect_sources:
            problems.append(f"{source}: redirect chain through {destination}")
        destination_path = local_path(destination)
        if not destination_path.exists():
            problems.append(f"{source}: destination file missing: {destination}")
            continue
        destination_source = destination_path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*noindex', destination_source, re.I):
            problems.append(f"{source}: destination is noindex: {destination}")
        if f"<loc>{SITE}{destination}</loc>" not in sitemap:
            problems.append(f"{source}: destination is not submitted: {destination}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mappings = expected_routes()
    current = VERCEL_CONFIG.read_text(encoding="utf-8")
    rendered = render_config(load_json(VERCEL_CONFIG), mappings)
    if args.check:
        found = issues()
        if current != rendered:
            found.append("vercel.json differs from deterministic route rendering")
        for item in found:
            print(item, file=sys.stderr)
        return 1 if found else 0
    if current != rendered:
        VERCEL_CONFIG.write_text(rendered, encoding="utf-8")
    found = issues()
    for item in found:
        print(item, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
