#!/usr/bin/env python3
"""Repair reviewed missing and cross-language routes in Spanish public HTML."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ES = ROOT / "es"
MISSING_TERMS = re.compile(
    r'\s*(?:·\s*)?<a\s+href=["\']/es/terms-of-service["\'][^>]*>.*?</a>',
    re.IGNORECASE | re.DOTALL,
)
TRANSLATED_DESTINATIONS = {
    "/home-valuation": "/es/home-valuation",
    "/property-search": "/es/property-search",
}


def normalize(document: str) -> str:
    document = document.replace('href="/es/contact"', 'href="/es/#contact"')
    document = document.replace("href='/es/contact'", "href='/es/#contact'")
    for english, spanish in TRANSLATED_DESTINATIONS.items():
        document = document.replace(f'href="{english}"', f'href="{spanish}"')
        document = document.replace(f"href='{english}'", f"href='{spanish}'")
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
