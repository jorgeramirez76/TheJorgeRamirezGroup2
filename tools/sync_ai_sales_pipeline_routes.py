#!/usr/bin/env python3
"""Synchronize legacy AI Sales Pipeline redirects from a reviewed manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "ai-sales-pipeline-route-migration.json"
VERCEL_PATH = ROOT / "vercel.json"
PROGRAMMATIC_MANIFEST_PATH = ROOT / "data" / "programmatic-doorway-retirement.json"
FEATURE_SOURCE = re.compile(r"^/(?:es/)?features/[^/:*()]+(?:\.html)?$")
ALIAS = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class RouteMigrationError(RuntimeError):
    """Raised when the reviewed route contract cannot be applied safely."""


def load_manifest() -> dict[str, Any]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != 1:
        raise RouteMigrationError("unsupported AI Sales Pipeline route schema")
    if payload.get("routeSync") != "tools/sync_ai_sales_pipeline_routes.py":
        raise RouteMigrationError("manifest routeSync does not name this tool")
    if set(payload.get("routePrefixByLanguage", {})) != {"en", "es"}:
        raise RouteMigrationError("manifest must define exact en/es route prefixes")
    if not payload.get("families"):
        raise RouteMigrationError("manifest has no route families")
    return payload


def base_routes(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Expand reviewed families into unique language-preserving clean routes."""

    records: list[dict[str, str]] = []
    seen_sources: set[str] = set()
    seen_family_ids: set[str] = set()
    prefixes = manifest["routePrefixByLanguage"]
    for family in manifest["families"]:
        family_id = str(family.get("id", ""))
        if not ALIAS.fullmatch(family_id) or family_id in seen_family_ids:
            raise RouteMigrationError(f"invalid or duplicate family id: {family_id!r}")
        seen_family_ids.add(family_id)
        aliases = family.get("aliases")
        destinations = family.get("destinationByLanguage")
        if not isinstance(aliases, list) or len(aliases) != 2:
            raise RouteMigrationError(f"{family_id}: exactly two aliases are required")
        if not isinstance(destinations, dict) or set(destinations) != {"en", "es"}:
            raise RouteMigrationError(f"{family_id}: exact en/es destinations are required")
        for alias in aliases:
            if not isinstance(alias, str) or not ALIAS.fullmatch(alias):
                raise RouteMigrationError(f"{family_id}: invalid alias {alias!r}")
            for language in ("en", "es"):
                destination = str(destinations[language])
                parsed = urlsplit(destination)
                if parsed.scheme != "https" or parsed.netloc != "aisalespipeline.com":
                    raise RouteMigrationError(
                        f"{family_id}: destination must use the verified HTTPS product domain"
                    )
                if language == "en" and not re.fullmatch(
                    r"/features/[a-z0-9-]+-real-estate\.html", parsed.path
                ):
                    raise RouteMigrationError(
                        f"{family_id}: English destination must be an exact feature page"
                    )
                if language == "es" and parsed.path != "/es/":
                    raise RouteMigrationError(
                        f"{family_id}: Spanish destination must use the reviewed fallback"
                    )
                source = str(prefixes[language]) + alias
                if source in seen_sources:
                    raise RouteMigrationError(f"duplicate managed route: {source}")
                seen_sources.add(source)
                records.append(
                    {
                        "family": family_id,
                        "language": language,
                        "source": source,
                        "destination": destination,
                    }
                )
    return records


def desired_redirects(manifest: dict[str, Any]) -> list[dict[str, object]]:
    return [
        {
            "source": record["source"],
            "destination": record["destination"],
            "permanent": True,
        }
        for record in base_routes(manifest)
    ]


def _programmatic_sources() -> set[str]:
    if not PROGRAMMATIC_MANIFEST_PATH.exists():
        return set()
    payload = json.loads(PROGRAMMATIC_MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        source
        for page in payload.get("pages", [])
        for source in (str(page.get("path", "")), str(page.get("path", "")) + ".html")
        if source.startswith("/")
    }


def synchronized_vercel(manifest: dict[str, Any], current: str) -> str:
    """Return Vercel config with exactly the reviewed legacy feature redirects."""

    config = json.loads(current)
    redirects = config.get("redirects")
    if not isinstance(redirects, list):
        raise RouteMigrationError("vercel.json redirects must be a list")
    desired = desired_redirects(manifest)
    managed_sources = {
        source
        for record in base_routes(manifest)
        for source in (record["source"], record["source"] + ".html")
    }
    preserved: list[dict[str, Any]] = []
    for rule in redirects:
        if not isinstance(rule, dict):
            raise RouteMigrationError("vercel redirect entries must be objects")
        source = str(rule.get("source", ""))
        if source in managed_sources:
            if rule.get("has"):
                raise RouteMigrationError(f"refusing to replace conditional redirect: {source}")
            continue
        if FEATURE_SOURCE.fullmatch(source):
            raise RouteMigrationError(f"unreviewed feature redirect exists: {source}")
        preserved.append(rule)

    destinations = {str(rule["destination"]) for rule in desired}
    preserved_sources = {str(rule.get("source", "")) for rule in preserved}
    chained = destinations & preserved_sources
    if chained:
        raise RouteMigrationError(f"redirect destinations would chain: {sorted(chained)}")

    # Keep compatibility with the existing deterministic route synchronizers:
    # authority routes stay first, and these exact migration routes stay immediately
    # before the managed programmatic doorway block and all path patterns.
    programmatic = _programmatic_sources()
    insertion_index = len(preserved)
    for index, rule in enumerate(preserved):
        source = str(rule.get("source", ""))
        if source in programmatic or rule.get("has") or any(mark in source for mark in (":", "*", "(")):
            insertion_index = index
            break
    config["redirects"] = preserved[:insertion_index] + desired + preserved[insertion_index:]
    return json.dumps(config, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if vercel.json differs")
    args = parser.parse_args()
    manifest = load_manifest()
    current = VERCEL_PATH.read_text(encoding="utf-8")
    expected = synchronized_vercel(manifest, current)
    if args.check:
        if current != expected:
            print("OUT OF SYNC: vercel.json", file=sys.stderr)
            return 1
        print(
            "AI Sales Pipeline routes synchronized: "
            f"{len(base_routes(manifest))} clean routes, "
            f"{len(desired_redirects(manifest))} redirect sources"
        )
        return 0
    if current != expected:
        VERCEL_PATH.write_text(expected, encoding="utf-8")
        print("WROTE vercel.json")
    print(
        "AI Sales Pipeline route sync complete: "
        f"{len(base_routes(manifest))} clean routes, "
        f"{len(desired_redirects(manifest))} redirect sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
