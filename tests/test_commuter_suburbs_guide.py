#!/usr/bin/env python3
"""Integrity checks for the bilingual, source-backed commuter-town guide."""

from __future__ import annotations

import html
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "en": ROOT / "blog" / "best-nj-suburbs-nyc-commuters.html",
    "es": ROOT / "es" / "blog" / "best-nj-suburbs-nyc-commuters.html",
}
CANONICALS = {
    "en": "https://thejorgeramirezgroup.com/blog/best-nj-suburbs-nyc-commuters",
    "es": "https://thejorgeramirezgroup.com/es/blog/best-nj-suburbs-nyc-commuters",
}
MANIFEST = ROOT / "data" / "commuter-suburbs-guide-sources.json"


def visible_text(source: str) -> str:
    cleaned = re.sub(
        r"<(?:script|style|template|noscript)\b[^>]*>.*?</(?:script|style|template|noscript)>",
        " ",
        source,
        flags=re.I | re.S,
    )
    cleaned = re.sub(r"<!--.*?-->", " ", cleaned, flags=re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return re.sub(r"\s+", " ", html.unescape(cleaned)).strip()


def sitemap_urls(filename: str) -> set[str]:
    root = ET.parse(ROOT / filename).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


class CommuterSuburbsGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {key: path.read_text(encoding="utf-8") for key, path in PAGES.items()}

    def test_pages_are_indexable_canonical_translated_and_submitted(self) -> None:
        self.assertIn(CANONICALS["en"], sitemap_urls("sitemap.xml"))
        self.assertIn(CANONICALS["es"], sitemap_urls("sitemap-es.xml"))
        for language, source in self.sources.items():
            with self.subTest(language=language):
                self.assertIn('content="index, follow, max-image-preview:large', source)
                self.assertEqual(1, source.count(f'<link rel="canonical" href="{CANONICALS[language]}">'))
                self.assertIn(f'hreflang="en-US" href="{CANONICALS["en"]}"', source)
                self.assertIn(f'hreflang="es-US" href="{CANONICALS["es"]}"', source)
                self.assertIn(f'hreflang="x-default" href="{CANONICALS["en"]}"', source)

    def test_guide_avoids_volatile_and_steering_claims(self) -> None:
        risky_source_patterns = (
            r"\bGreatSchools\b",
            r"\b(?:median|average)\s+(?:home\s+)?(?:price|value)\b",
            r"\b(?:appreciat(?:e|ion)|bidding war|hot market)\b",
            r"\$\s*\d",
            r"\b\d+(?:\s*[–-]\s*\d+)?\s*(?:min|mins|minute|minutes)\b",
        )
        risky_visible_patterns = (
            r"\b(?:top[- ]rated|best|excellent|weak(?:er)?)\s+(?:school|schools|district|town|towns|suburb|suburbs)\b",
            r"\b(?:safe(?:st)?|low[- ]crime|family[- ]friendly|perfect for families|young families)\b",
            r"\b(?:mejores?|excelentes?|débiles?)\s+(?:escuelas?|distritos?|pueblos?|suburbios?)\b",
            r"\b(?:segur[oa]s?|baja criminalidad|ideal(?:es)? para familias|familias jóvenes)\b",
        )
        for language, source in self.sources.items():
            text = visible_text(source)
            with self.subTest(language=language):
                for pattern in risky_source_patterns:
                    self.assertIsNone(re.search(pattern, source, re.I), pattern)
                for pattern in risky_visible_patterns:
                    self.assertIsNone(re.search(pattern, text, re.I), pattern)

    def test_selection_is_transit_based_not_a_ranking(self) -> None:
        for language, source in self.sources.items():
            with self.subTest(language=language):
                self.assertGreaterEqual(len(re.findall(r'<article\b[^>]*class="town-card"', source)), 12)
                self.assertIn('data-selection="illustrative-not-ranked"', source)
                self.assertIn("2026-08-19", source)
                self.assertIn("2026-08-26", source)
                self.assertIn("/nj-train-map", source)
                self.assertIn("/communities", source)
                self.assertIn("/property-search", source)
                self.assertIn("/home-valuation", source)
                self.assertIn("/contact", source)

    def test_official_sources_and_methodology_are_manifested(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("2026-08-26", manifest["reviewed"])
        self.assertEqual("2026-08-19", manifest["methodology"]["gtfs_snapshot_date"])
        self.assertGreaterEqual(len(manifest["sources"]), 8)
        allowed_hosts = {
            "www.njtransit.com",
            "developer.njtransit.com",
            "www.panynj.gov",
            "www.nj.gov",
            "www.hud.gov",
        }
        for item in manifest["sources"]:
            self.assertTrue(item["publisher"].strip())
            self.assertTrue(item["fact_supported"].strip())
            self.assertEqual("2026-08-26", item["accessed"])
            self.assertIn((urlsplit(item["url"]).hostname or "").lower(), allowed_hosts)
        required_links = {item["url"] for item in manifest["sources"] if item.get("visible", True)}
        for language, source in self.sources.items():
            with self.subTest(language=language):
                for url in required_links:
                    self.assertIn(url, source)

    def test_accessibility_and_homepage_visual_contract(self) -> None:
        for language, source in self.sources.items():
            with self.subTest(language=language):
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertEqual(1, len(re.findall(r'<main\b[^>]*id="main"', source, re.I)))
                self.assertIn('href="#main"', source)
                ids = re.findall(r'\bid=["\']([^"\']+)', source, re.I)
                self.assertEqual(len(ids), len(set(ids)), "duplicate HTML id")
                self.assertIn("--ink: #1A1A1A", source)
                self.assertIn("--red: #C41230", source)
                self.assertIn("--gold: #B8962E", source)
                self.assertIn("--ivory: #FAFAF8", source)
                self.assertIn("'Playfair Display'", source)
                self.assertIn("'Inter'", source)
                self.assertRegex(source, re.compile(r'<table\b[^>]*>.*?<caption\b', re.I | re.S))

    def test_json_ld_is_parseable_factual_and_bilingual(self) -> None:
        for language, source in self.sources.items():
            blocks = re.findall(
                r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                source,
                re.I | re.S,
            )
            self.assertGreaterEqual(len(blocks), 2)
            parsed = [json.loads(block) for block in blocks]
            encoded = json.dumps(parsed)
            with self.subTest(language=language):
                self.assertIn("FAQPage", encoded)
                self.assertIn("BlogPosting", encoded)
                self.assertNotIn("AggregateRating", encoded)
                self.assertNotIn('"Review"', encoded)
                self.assertNotIn("ratingValue", encoded)
                self.assertNotIn("priceRange", encoded)
                expected = "en-US" if language == "en" else "es-US"
                self.assertIn(expected, encoded)


if __name__ == "__main__":
    unittest.main()
