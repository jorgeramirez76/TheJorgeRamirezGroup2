#!/usr/bin/env python3
"""Ensure the duplicate commuter article consolidates into the primary guide."""

from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY = {
    "en": {
        "file": ROOT / "blog" / "top-nyc-commuter-towns-nj-2026.html",
        "path": "/blog/top-nyc-commuter-towns-nj-2026",
        "destination": "/blog/best-nj-suburbs-nyc-commuters",
    },
    "es": {
        "file": ROOT / "es" / "blog" / "top-nyc-commuter-towns-nj-2026.html",
        "path": "/es/blog/top-nyc-commuter-towns-nj-2026",
        "destination": "/es/blog/best-nj-suburbs-nyc-commuters",
    },
}


def sitemap_text(filename: str) -> str:
    return (ROOT / filename).read_text(encoding="utf-8")


class CommuterContentConsolidationTests(unittest.TestCase):
    def test_fallbacks_are_small_exact_accessible_and_noindex(self) -> None:
        risky = re.compile(
            r"\$\s*\d|\b\d+\s*(?:min|mins|minutes?|minutos?)\b|"
            r"GreatSchools|school\s+(?:rating|ranking)|(?:home|house)\s+price|"
            r"family[- ]friendly|safest|fastest",
            re.I,
        )
        for language, item in LEGACY.items():
            source = item["file"].read_text(encoding="utf-8")
            destination = item["destination"]
            with self.subTest(language=language):
                self.assertLess(len(source.encode("utf-8")), 4_000)
                self.assertIn('<meta name="robots" content="noindex, follow">', source)
                self.assertEqual(
                    1,
                    source.count(
                        f'<link rel="canonical" href="https://thejorgeramirezgroup.com{destination}">'
                    ),
                )
                self.assertIn(f'<meta http-equiv="refresh" content="0; url={destination}">', source)
                self.assertIn(f"window.location.replace('{destination}')", source)
                self.assertEqual(1, source.count(f'href="{destination}"'))
                self.assertEqual(1, len(re.findall(r"<main\b", source, re.I)))
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertIn("--ink:#1A1A1A", source)
                self.assertIn("--red:#C41230", source)
                self.assertIn("--gold:#B8962E", source)
                self.assertIn("--ivory:#FAFAF8", source)
                self.assertIsNone(risky.search(source))

    def test_vercel_redirects_are_permanent_and_one_hop(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirects = {
            item["source"]: item
            for item in config.get("redirects", [])
            if not item.get("has") and ":" not in item.get("source", "")
        }
        for item in LEGACY.values():
            for source in (item["path"], item["path"] + ".html"):
                with self.subTest(source=source):
                    self.assertIn(source, redirects)
                    self.assertEqual(item["destination"], redirects[source]["destination"])
                    self.assertIs(True, redirects[source]["permanent"])
                    self.assertNotIn(item["destination"], redirects)

    def test_legacy_urls_are_absent_from_all_sitemap_fields(self) -> None:
        combined = sitemap_text("sitemap.xml") + sitemap_text("sitemap-es.xml")
        for item in LEGACY.values():
            self.assertNotIn(item["path"], combined)

        en_root = ET.parse(ROOT / "sitemap.xml").getroot()
        es_root = ET.parse(ROOT / "sitemap-es.xml").getroot()
        en_locs = {(node.text or "").strip() for node in en_root.findall("{*}url/{*}loc")}
        es_locs = {(node.text or "").strip() for node in es_root.findall("{*}url/{*}loc")}
        self.assertIn(
            "https://thejorgeramirezgroup.com/blog/best-nj-suburbs-nyc-commuters",
            en_locs,
        )
        self.assertIn(
            "https://thejorgeramirezgroup.com/es/blog/best-nj-suburbs-nyc-commuters",
            es_locs,
        )

    def test_primary_guides_do_not_link_back_to_legacy_urls(self) -> None:
        for language, item in LEGACY.items():
            primary = (
                ROOT / "blog" / "best-nj-suburbs-nyc-commuters.html"
                if language == "en"
                else ROOT / "es" / "blog" / "best-nj-suburbs-nyc-commuters.html"
            )
            self.assertNotIn(item["path"], primary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
