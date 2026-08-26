#!/usr/bin/env python3
"""Repair the two reviewed missing-route patterns in Spanish public HTML."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ES = ROOT / "es"
MISSING_TERMS = re.compile(
    r'\s*(?:·\s*)?<a\s+href=["\']/es/terms-of-service["\'][^>]*>.*?</a>',
    re.IGNORECASE | re.DOTALL,
)


def normalize(document: str) -> str:
    document = document.replace('href="/es/contact"', 'href="/es/#contact"')
    document = document.replace("href='/es/contact'", "href='/es/#contact'")
    return MISSING_TERMS.sub("", document)


def main() -> int:
    changed: list[str] = []
    for path in sorted(ES.rglob("*.html")):
        source = path.read_text(encoding="utf-8", errors="replace")
        updated = normalize(source)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
            changed.append(path.relative_to(ROOT).as_posix())
    print(f"changed_files={len(changed)}")
    for relative in changed:
        print(relative)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
