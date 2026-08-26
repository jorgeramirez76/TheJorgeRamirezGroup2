#!/usr/bin/env python3
"""Read the reviewed town-comparison manifest for internal-link rendering."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "top-level-town-comparison-sources.json"
PLACE_TO_CANONICAL_TOWN = {
    "millburn-short-hills": "millburn",
}


def load_comparisons() -> dict[str, object]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def canonical_town(place: str) -> str:
    return PLACE_TO_CANONICAL_TOWN.get(place, place)


def comparison_links(*, language: str = "en") -> list[dict[str, str]]:
    document = load_comparisons()
    prefix = "/es" if language == "es" else ""
    records: list[dict[str, str]] = []
    for slug, comparison in document["comparisons"].items():
        left = comparison["left"]
        right = comparison["right"]
        counties = sorted(
            {
                document["places"][side]["copy"]["en"]["county"].removesuffix(
                    " County"
                )
                for side in (left, right)
            }
        )
        records.append(
            {
                "slug": slug,
                "route": f"{prefix}/{slug}",
                "label": comparison["copy"][language]["h1"],
                "left_town": canonical_town(left),
                "right_town": canonical_town(right),
                "counties": counties,
            }
        )
    return records


def links_for_town(slug: str, *, language: str = "en") -> list[dict[str, str]]:
    return [
        record
        for record in comparison_links(language=language)
        if slug in {record["left_town"], record["right_town"]}
    ]


def links_for_county(county: str, *, language: str = "en") -> list[dict[str, str]]:
    return [
        record
        for record in comparison_links(language=language)
        if county in record["counties"]
    ]
