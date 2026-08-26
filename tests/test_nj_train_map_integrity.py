#!/usr/bin/env python3
"""Regression coverage for the source-backed NJ commuter rail map pair."""

from __future__ import annotations

import html
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "nj-train-map-sources.json"
PAGES = {
    "en": ROOT / "nj-train-map.html",
    "es": ROOT / "es" / "nj-train-map.html",
}
CANONICALS = {
    "en": "https://thejorgeramirezgroup.com/nj-train-map",
    "es": "https://thejorgeramirezgroup.com/es/nj-train-map",
}
OFFICIAL_NJT_LINKS = {
    "https://www.njtransit.com/accessibility/System-Map",
    "https://www.njtransit.com/getting-new-york-train",
    "https://www.njtransit.com/printables",
    "https://www.njtransit.com/ride-rail",
    "https://www.njtransit.com/station-park-ride-to",
    "https://www.njtransit.com/travel-alerts-to",
    "https://www.njtransit.com/trip-planner-to",
}
RISKY_SOURCE_PATTERNS = (
    re.compile(r"\bGreatSchools\b", re.I),
    re.compile(r"\b(?:school|district)\s+(?:rating|score|ranking)\b", re.I),
    re.compile(r"\b(?:schools|minSchool|schoolSlider|price|trend|commute|fare|taxBill)\s*:", re.I),
    re.compile(r"\bmedian\s+(?:home\s+)?(?:price|sale\s+price)\b", re.I),
    re.compile(r"\b(?:price|home)\s+appreciation\b", re.I),
    re.compile(r"\bmonthly\s+(?:rail\s+)?pass\b", re.I),
    re.compile(r"\bproperty\s+tax\b", re.I),
    re.compile(r"\$\s*\d"),
)
RISKY_VISIBLE_PATTERNS = (
    re.compile(r"\b(?:all|every|live|faster|cheaper|exclusive)\b", re.I),
    re.compile(r"\b(?:best|weak(?:er)?|top[- ]rated)\s+(?:school|schools|town|towns|line|value)\b", re.I),
    re.compile(r"\b(?:family[- ]friendly|value\s+play|best\s+for\s+famil(?:y|ies))\b", re.I),
    re.compile(r"\b\d+(?:\s*[–-]\s*\d+)?\s*(?:min|mins|minute|minutes)\b", re.I),
    re.compile(r"\b(?:todos?|cada|en\s+vivo|más\s+rápid[oa]s?|más\s+barat[oa]s?|exclusiv[oa]s?)\b", re.I),
    re.compile(r"\b(?:mejores?|débiles?)\s+(?:escuelas?|pueblos?|líneas?)\b", re.I),
)


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


def station_data(source: str) -> list[dict]:
    match = re.search(
        r'<script\b[^>]*id=["\']station-data["\'][^>]*>(.*?)</script>',
        source,
        re.I | re.S,
    )
    if not match:
        return []
    return json.loads(match.group(1))


def sitemap_urls(filename: str) -> set[str]:
    root = ET.parse(ROOT / filename).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


class NjTrainMapIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {language: path.read_text(encoding="utf-8") for language, path in PAGES.items()}

    def test_pages_remain_indexable_canonical_translated_and_submitted(self) -> None:
        self.assertIn(CANONICALS["en"], sitemap_urls("sitemap.xml"))
        self.assertIn(CANONICALS["es"], sitemap_urls("sitemap-es.xml"))
        for language, source in self.sources.items():
            with self.subTest(language=language):
                self.assertIn('<meta name="robots" content="index, follow, max-image-preview:large">', source)
                self.assertEqual(1, source.count(f'<link rel="canonical" href="{CANONICALS[language]}">'))
                self.assertIn(f'hreflang="en-US" href="{CANONICALS["en"]}"', source)
                self.assertIn(f'hreflang="es-US" href="{CANONICALS["es"]}"', source)
                self.assertIn(f'hreflang="x-default" href="{CANONICALS["en"]}"', source)

    def test_risky_rankings_prices_durations_and_steering_are_absent(self) -> None:
        for language, source in self.sources.items():
            text = visible_text(source)
            with self.subTest(language=language):
                for pattern in RISKY_SOURCE_PATTERNS:
                    self.assertIsNone(pattern.search(source), pattern.pattern)
                for pattern in RISKY_VISIBLE_PATTERNS:
                    self.assertIsNone(pattern.search(text), pattern.pattern)

    def test_station_dataset_contains_only_official_stable_fields(self) -> None:
        datasets = {language: station_data(source) for language, source in self.sources.items()}
        self.assertGreaterEqual(len(datasets["en"]), 40)
        self.assertEqual(datasets["en"], datasets["es"])
        allowed = {"id", "name", "lines", "lat", "lng", "guide"}
        station_ids = set()
        for station in datasets["en"]:
            self.assertEqual(set(station), allowed)
            self.assertNotIn(station["id"], station_ids)
            station_ids.add(station["id"])
            self.assertTrue(station["name"].strip())
            self.assertTrue(set(station["lines"]).issubset({"me", "gl", "rv", "ne"}))
            self.assertTrue(39.9 < station["lat"] < 41.1)
            self.assertTrue(-75.0 < station["lng"] < -73.7)
            if station["guide"]:
                self.assertTrue((ROOT / "towns" / f'{station["guide"]}.html').exists())
                self.assertTrue((ROOT / "es" / "towns" / f'{station["guide"]}.html').exists())

    def test_official_sources_and_dated_methodology_are_visible_and_manifested(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual("2026-08-26", manifest["reviewed"])
        self.assertEqual("2026-08-19", manifest["methodology"]["gtfs_snapshot_date"])
        self.assertRegex(manifest["methodology"]["gtfs_archive_sha256"], r"^[0-9a-f]{64}$")
        self.assertGreaterEqual(len(manifest["sources"]), 7)
        for item in manifest["sources"]:
            self.assertEqual("NJ TRANSIT", item["publisher"])
            self.assertEqual("2026-08-26", item["accessed"])
            self.assertTrue(item["fact_supported"].strip())
            host = (urlsplit(item["url"]).hostname or "").lower()
            self.assertIn(host, {"www.njtransit.com", "content.njtransit.com", "developer.njtransit.com"})
        for language, source in self.sources.items():
            with self.subTest(language=language):
                self.assertIn("2026-08-26", source)
                for url in OFFICIAL_NJT_LINKS:
                    self.assertIn(url, source)

    def test_interaction_and_accessibility_contract(self) -> None:
        for language, source in self.sources.items():
            with self.subTest(language=language):
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertEqual(1, len(re.findall(r'<main\b[^>]*id=["\']main["\']', source, re.I)))
                self.assertIn('href="#main"', source)
                ids = re.findall(r'\bid=["\']([^"\']+)', source, re.I)
                self.assertEqual(len(ids), len(set(ids)), "duplicate HTML id")
                self.assertRegex(source, r'<button\b[^>]*class=["\'][^"\']*line-pill[^"\']*["\'][^>]*aria-pressed=')
                self.assertRegex(source, r'<input\b[^>]*type=["\']search["\'][^>]*id=["\']stationSearch["\']')
                self.assertRegex(source, r'id=["\']resultStatus["\'][^>]*aria-live=["\']polite["\']')
                self.assertIn('id="leafletMap"', source)
                self.assertIn('id="stationList"', source)
                self.assertIn("applyFilters", source)
                self.assertIn("selectStation", source)
                self.assertIn("--primary-red: #C41230", source)
                self.assertIn("--gold: #B8962E", source)
                self.assertIn("--dark-bg: #0A0A0A", source)
                self.assertIn("'Playfair Display'", source)
                self.assertIn("'Inter'", source)

    def test_json_ld_is_parseable_and_contains_no_ranking_or_review_schema(self) -> None:
        for language, source in self.sources.items():
            blocks = re.findall(
                r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                source,
                re.I | re.S,
            )
            self.assertGreaterEqual(len(blocks), 2)
            schemas = [json.loads(block) for block in blocks]
            encoded = json.dumps(schemas)
            with self.subTest(language=language):
                self.assertNotIn("Review", encoded)
                self.assertNotIn("AggregateRating", encoded)
                self.assertNotIn("ratingValue", encoded)
                self.assertNotIn("price", encoded.lower())
                self.assertIn("WebApplication", encoded)
                self.assertIn("FAQPage", encoded)


if __name__ == "__main__":
    unittest.main()
