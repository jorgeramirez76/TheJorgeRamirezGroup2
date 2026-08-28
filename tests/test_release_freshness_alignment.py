#!/usr/bin/env python3
"""Guard page-modified and source-review date separation for this release."""

from __future__ import annotations

import importlib.util
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_MODIFIED_ON = "2026-08-27"


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def routes_from_manifest(relative: str) -> set[str]:
    document = load_json(relative)
    return {
        route.lstrip("/") + ".html"
        for report in document["reports"]
        for route in report["routes"].values()
    }


def editorial_visual_paths() -> set[str]:
    path = ROOT / "tools/apply_editorial_visuals.py"
    spec = importlib.util.spec_from_file_location("release_editorial_visuals", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load editorial visual manifest")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return set(module.PAGE_VISUALS)


def release_paths() -> set[str]:
    indexable_towns = load_json("data/indexable-town-risk-decisions.json")
    spanish_towns = load_json("data/spanish-town-risk-decisions.json")
    return (
        editorial_visual_paths()
        | routes_from_manifest("data/county-market-report-sources-2026-08-26.json")
        | routes_from_manifest("data/town-market-research-essex-middlesex-somerset.json")
        | routes_from_manifest("data/union-morris-town-market-sources-2026-08-26.json")
        | {
            f"towns/{slug}.html"
            for slug, decision in indexable_towns["decisions"].items()
            if decision["action"] == "rebuild"
        }
        | {
            f"es/towns/{slug}.html"
            for slug, decision in spanish_towns["decisions"].items()
            if decision["action"] == "rebuild"
        }
        | {
            f"towns/{slug}.html"
            for slug in (
                "berkeley-heights",
                "chatham-borough",
                "chatham-township",
                "cranford",
                "denville",
                "east-hanover",
                "fanwood",
                "morris-plains",
                "new-providence",
                "roselle-park",
                "springfield",
            )
        }
    )


def sitemap_lastmods() -> dict[str, str]:
    result: dict[str, str] = {}
    for filename in ("sitemap.xml", "sitemap-es.xml"):
        root = ET.parse(ROOT / filename).getroot()
        for node in root.findall("{*}url"):
            loc = node.find("{*}loc")
            lastmod = node.find("{*}lastmod")
            if loc is not None and loc.text and lastmod is not None and lastmod.text:
                result[loc.text.rstrip("/")] = lastmod.text
    return result


class ReleaseFreshnessAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = release_paths()

    def test_release_inventory_is_exactly_147_indexable_pages(self) -> None:
        self.assertEqual(147, len(self.paths))
        for relative in sorted(self.paths):
            with self.subTest(relative=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                self.assertNotRegex(
                    source,
                    r'<meta\b[^>]*name="robots"[^>]*content="[^"]*noindex',
                )
                self.assertRegex(source, r'<link\s+rel="canonical"\s+href="[^"]+"')

    def test_schema_meta_and_sitemap_modified_dates_are_aligned(self) -> None:
        lastmods = sitemap_lastmods()
        for relative in sorted(self.paths):
            with self.subTest(relative=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                canonical = re.search(
                    r'<link\s+rel="canonical"\s+href="([^"]+)"', source
                ).group(1).rstrip("/")
                schema_dates = re.findall(
                    r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"', source
                )
                self.assertGreaterEqual(len(schema_dates), 1)
                self.assertEqual({PAGE_MODIFIED_ON}, set(schema_dates))
                for pattern in (
                    r'<meta\s+property="article:modified_time"\s+content="([^"]+)"',
                    r'<meta\s+name="last-updated"\s+content="([^"]+)"',
                ):
                    values = re.findall(pattern, source, flags=re.I)
                    if values:
                        self.assertEqual({PAGE_MODIFIED_ON}, set(values))
                self.assertEqual(PAGE_MODIFIED_ON, lastmods.get(canonical))

    def test_factual_review_and_access_dates_remain_distinct(self) -> None:
        expected = {
            "data/seller-service-sources.json": ("reviewedOn", "2026-08-26"),
            "data/county-market-report-sources-2026-08-26.json": ("reviewedOn", "2026-08-26"),
            "data/town-market-research-essex-middlesex-somerset.json": ("reviewedOn", "2026-08-26"),
            "data/union-morris-town-market-sources-2026-08-26.json": ("reviewedOn", "2026-08-26"),
            "data/union-priority-town-sources.json": ("accessed", "2026-08-25"),
            "data/other-priority-town-sources.json": ("accessed", "2026-08-25"),
        }
        for relative, (field, value) in expected.items():
            with self.subTest(relative=relative):
                self.assertEqual(value, load_json(relative)[field])

        self.assertEqual(
            "2026-08-26",
            load_json("data/indexable-town-risk-decisions.json")["provenancePolicy"][
                "sourceCheckedDate"
            ],
        )
        self.assertEqual(
            "2026-08-26",
            load_json("data/spanish-town-risk-decisions.json")["provenancePolicy"][
                "sourceCheckedDate"
            ],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
