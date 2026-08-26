#!/usr/bin/env python3
"""Synchronize bilingual authority-hub town discovery with site facts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTS_PATH = ROOT / "data" / "site-facts.json"

PAGES = {
    "en": {
        "path": ROOT / "ai-authority.html",
        "start": "<!-- TOWN PAGES: ORGANIZED BY COUNTY -->",
        "end": '<section class="content-section alt-bg" id="town-comparisons">',
        "prefix": "/towns/",
        "county_order": ("Union", "Morris", "Essex", "Hudson", "Middlesex", "Somerset"),
    },
    "es": {
        "path": ROOT / "es" / "ai-authority.html",
        "start": "<!-- PÁGINAS DE CIUDADES POR CONDADO -->",
        "end": '<section class="content-section alt-bg" id="comparaciones">',
        "prefix": "/es/towns/",
        "county_order": ("Union", "Morris", "Essex", "Hudson", "Middlesex", "Somerset"),
    },
}

TOWN_GRID_RE = re.compile(
    r'(<div\s+class="town-links">)(.*?)(</div>)',
    re.IGNORECASE | re.DOTALL,
)


def town_label(slug: str) -> str:
    return slug.replace("-", " ").title()


def expected_grid(slugs: list[str], prefix: str) -> str:
    links = "\n".join(
        f'          <a href="{prefix}{slug}">{town_label(slug)}</a>' for slug in slugs
    )
    return f'<div class="town-links">\n{links}\n        </div>'


def sync_page(source: str, language: str, inventory: dict[str, list[str]]) -> str:
    config = PAGES[language]
    start = source.find(config["start"])
    end = source.find(config["end"], start)
    if start < 0 or end < 0:
        raise ValueError(f"could not locate authority town section for {language}")

    section = source[start:end]
    matches = list(TOWN_GRID_RE.finditer(section))
    if len(matches) not in {5, 6}:
        raise ValueError(f"expected five or six county grids for {language}, found {len(matches)}")

    counties = config["county_order"]
    if language == "es" and len(matches) == 5:
        # The legacy Spanish page omitted Somerset. Insert its county card before
        # the existing directory link while preserving the page's established UI.
        somerset = expected_grid(inventory["Somerset"], config["prefix"])
        card = (
            "\n      <!-- CONDADO DE SOMERSET -->\n"
            '      <div class="county-section">\n'
            "        <h3>Condado de Somerset (Somerset County)</h3>\n"
            f"        {somerset}\n"
            "      </div>\n"
        )
        marker = '      <p style="margin-top: 14px;">'
        marker_index = section.find(marker)
        if marker_index < 0:
            raise ValueError("could not locate Spanish directory-link marker")
        section = section[:marker_index] + card + "\n" + section[marker_index:]
        matches = list(TOWN_GRID_RE.finditer(section))

    if len(matches) != len(counties):
        raise ValueError(
            f"county-grid mismatch for {language}: {len(matches)} grids vs {len(counties)} facts"
        )

    parts: list[str] = []
    cursor = 0
    for match, county in zip(matches, counties):
        parts.append(section[cursor : match.start()])
        parts.append(expected_grid(inventory[county], config["prefix"]))
        cursor = match.end()
    parts.append(section[cursor:])
    synced_section = "".join(parts)
    return source[:start] + synced_section + source[end:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if either authority hub has drift")
    args = parser.parse_args()

    facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
    inventory = facts["canonicalTownInventory"]["byCounty"]
    changed: list[Path] = []
    for language, config in PAGES.items():
        path = config["path"]
        source = path.read_text(encoding="utf-8")
        synced = sync_page(source, language, inventory)
        if synced == source:
            continue
        changed.append(path)
        if not args.check:
            path.write_text(synced, encoding="utf-8")

    mode = "drift" if args.check else "updated"
    print(f"AI authority hubs: {len(changed)} files {mode}; {sum(map(len, inventory.values()))} towns/language")
    if args.check and changed:
        for path in changed:
            print(path.relative_to(ROOT))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
