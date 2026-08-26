#!/usr/bin/env python3
"""Fail-closed provenance validation for public market-report generation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit


class ProvenanceError(ValueError):
    """Raised when publication evidence is missing, incomplete, or unreviewed."""


def _required_text(value: Mapping[str, Any], key: str, context: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise ProvenanceError(f"{context}.{key} must be a non-empty string")
    return result.strip()


def _required_date(value: Mapping[str, Any], key: str, context: str) -> str:
    result = _required_text(value, key, context)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", result):
        raise ProvenanceError(f"{context}.{key} must use YYYY-MM-DD")
    try:
        date.fromisoformat(result)
    except ValueError as exc:
        raise ProvenanceError(f"{context}.{key} is not a valid date") from exc
    return result


def validate_publication_manifest(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate a reviewed source-to-field record without mutating it.

    Passing this gate establishes only that the evidence record is complete. It does
    not grant a legacy generator permission to write public files.
    """

    if not isinstance(manifest, Mapping):
        raise ProvenanceError("publication manifest must be an object")
    if manifest.get("reviewStatus") != "approved":
        raise ProvenanceError("reviewStatus must be approved")
    _required_text(manifest, "reviewedBy", "manifest")
    _required_date(manifest, "reviewedAt", "manifest")
    if manifest.get("publicationRights") != "confirmed":
        raise ProvenanceError("publicationRights must be confirmed")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ProvenanceError("sources must contain at least one reviewed source")
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        context = f"sources[{index}]"
        if not isinstance(source, Mapping):
            raise ProvenanceError(f"{context} must be an object")
        source_id = _required_text(source, "id", context)
        if source_id in source_ids:
            raise ProvenanceError(f"duplicate source id: {source_id}")
        source_ids.add(source_id)
        _required_text(source, "publisher", context)
        source_url = _required_text(source, "url", context)
        parsed = urlsplit(source_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ProvenanceError(f"{context}.url must be an absolute HTTPS URL")
        _required_date(source, "accessedAt", context)
        _required_text(source, "geographyType", context)
        _required_text(source, "geographyName", context)
        _required_text(source, "reportingPeriod", context)

    metrics = manifest.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise ProvenanceError("metrics must contain at least one sourced field")
    for index, metric in enumerate(metrics):
        context = f"metrics[{index}]"
        if not isinstance(metric, Mapping):
            raise ProvenanceError(f"{context} must be an object")
        _required_text(metric, "name", context)
        _required_text(metric, "value", context)
        _required_text(metric, "definition", context)
        source_id = _required_text(metric, "sourceId", context)
        if source_id not in source_ids:
            raise ProvenanceError(f"{context}.sourceId does not match a source")

    return manifest


def quarantined_generator_main(
    generator_name: str, argv: Sequence[str] | None = None
) -> int:
    """Keep retired generators inert while allowing evidence-file validation."""

    parser = argparse.ArgumentParser(
        description=f"Validate evidence for the quarantined {generator_name} generator."
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        help="JSON evidence file to validate; this never publishes public pages.",
    )
    args = parser.parse_args(argv)

    if args.provenance is not None:
        try:
            document = json.loads(args.provenance.read_text(encoding="utf-8"))
            validate_publication_manifest(document)
        except (OSError, json.JSONDecodeError, ProvenanceError) as exc:
            print(f"Publication evidence rejected: {exc}", file=sys.stderr)
            print(f"The {generator_name} generator remains quarantined.", file=sys.stderr)
            return 2
        print("Publication evidence passed the fail-closed provenance check.")

    print(
        f"The legacy {generator_name} generator is quarantined and cannot write public files.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(quarantined_generator_main("market-report"))
