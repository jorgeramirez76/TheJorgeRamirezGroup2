#!/usr/bin/env python3
"""Fail-closed guard for the retired flip-count marketing scrubber.

This file used to replace an unverified numeric flip claim with other
unverified investor and renovation claims. It intentionally performs no
rewrites now. It only reports prohibited numeric flip-count language so an
editor can replace the surrounding sentence with a fact approved in
``data/site-facts.json``.

Usage: python3 scrub_flip_count.py [file ...]
       With no paths, scan public HTML and JSON files in the repository.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROHIBITED = re.compile(
    r"(?:"
    r"(?:60\+|60[ -]plus|sixty[ -]plus|over\s+60|m[aá]s\s+de\s+60)"
    r"[^\n<>]{0,100}(?:flip|flipp|home|house|propert|cas|viviend)"
    r"|"
    r"(?:flip|flipp|home|house|propert|cas|viviend)"
    r"[^\n<>]{0,100}(?:60\+|60[ -]plus|sixty[ -]plus|over\s+60|m[aá]s\s+de\s+60)"
    r")",
    re.IGNORECASE,
)


def default_targets() -> list[Path]:
    targets: list[Path] = []
    for suffix in ("*.html", "*.json"):
        targets.extend(ROOT.rglob(suffix))
    return sorted(
        path
        for path in targets
        if ".git" not in path.parts
        and ".vercel" not in path.parts
        and "node_modules" not in path.parts
    )


def main() -> int:
    supplied = [Path(value).resolve() for value in sys.argv[1:]]
    targets = supplied or default_targets()
    findings: list[tuple[Path, int, str]] = []

    for path in targets:
        if not path.is_file():
            print(f"Missing file: {path}", file=sys.stderr)
            return 2
        source = path.read_text(encoding="utf-8", errors="replace")
        for match in PROHIBITED.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            excerpt = " ".join(match.group(0).split())
            findings.append((path, line, excerpt[:180]))

    for path, line, excerpt in findings:
        try:
            display = path.relative_to(ROOT)
        except ValueError:
            display = path
        print(f"{display}:{line}: {excerpt}")

    if findings:
        print(
            "Refusing automatic substitutions. Replace each complete sentence "
            "with an approved fact from data/site-facts.json.",
            file=sys.stderr,
        )
        return 1

    print(f"Verified {len(targets)} public files; no numeric flip-count claims found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
