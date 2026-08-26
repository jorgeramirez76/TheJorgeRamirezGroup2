#!/usr/bin/env python3
"""Integrity checks for the bilingual Midtown Direct station-area guide."""

from __future__ import annotations

import html
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "en": ROOT / "blog" / "midtown-direct-towns-nj.html",
    "es": ROOT / "es" / "blog" / "midtown-direct-towns-nj.html",
}
CANONICALS = {
    "en": "https://thejorgeramirezgroup.com/blog/midtown-direct-towns-nj",
    "es": "https://thejorgeramirezgroup.com/es/blog/midtown-direct-towns-nj",
}
MANIFEST = ROOT / "data" / "midtown-direct-guide-sources.json"
GSC_SNIPPETS = ROOT / "data" / "gsc-priority-snippets.json"
SPANISH_SNIPPETS = ROOT / "data" / "spanish-snippet-backlog.json"
REVIEWED = "2026-08-26"
TIMETABLE_EFFECTIVE = "2026-05-31"


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


class MidtownDirectGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {key: path.read_text(encoding="utf-8") for key, path in PAGES.items()}
        cls.texts = {key: visible_text(source) for key, source in cls.sources.items()}

    def test_pages_are_indexable_canonical_and_reciprocal(self) -> None:
        for language, source in self.sources.items():
            with self.subTest(language=language):
                self.assertIn('content="index, follow, max-image-preview:large', source)
                self.assertEqual(
                    1,
                    source.count(f'<link rel="canonical" href="{CANONICALS[language]}">'),
                )
                self.assertIn(f'hreflang="en-US" href="{CANONICALS["en"]}"', source)
                self.assertIn(f'hreflang="es-US" href="{CANONICALS["es"]}"', source)
                self.assertIn(f'hreflang="x-default" href="{CANONICALS["en"]}"', source)

    def test_guide_is_station_planning_not_a_town_ranking(self) -> None:
        required = {
            "en": (
                "A station on the corridor does not mean every train is direct to New York Penn Station.",
                "Short Hills is an unincorporated community within Millburn Township.",
                "Chatham station is in Chatham Borough; Chatham Township is a separate municipality.",
                "Convent Station is a station-area and mailing name in Morris Township.",
                "New Providence and Murray Hill stations are both served by commuter parking lots managed by the Borough of New Providence.",
            ),
            "es": (
                "Estar en una estación del corredor no significa que cada tren sea directo a New York Penn Station.",
                "Short Hills es una comunidad no incorporada dentro de Millburn Township.",
                "La estación Chatham está en Chatham Borough; Chatham Township es un municipio separado.",
                "Convent Station es un nombre de zona de estación y de correo dentro de Morris Township.",
                "Las estaciones New Providence y Murray Hill tienen estacionamientos para viajeros administrados por el Borough of New Providence.",
            ),
        }
        for language, source in self.sources.items():
            text = self.texts[language]
            with self.subTest(language=language):
                self.assertIn('data-selection="illustrative-not-ranked"', source)
                self.assertIn(f'data-service-snapshot="{TIMETABLE_EFFECTIVE}"', source)
                self.assertGreaterEqual(len(re.findall(r'<article\b[^>]*class="station-card"', source)), 10)
                for phrase in required[language]:
                    self.assertIn(phrase, text)

    def test_risky_volatile_and_steering_claims_are_removed(self) -> None:
        source_patterns = (
            r"\$\s*\d",
            r"\b\d+(?:\s*[–-]\s*\d+)?\s*(?:min|mins|minute|minutes|minuto|minutos)\b",
            r"\b(?:median|average|typical)\s+(?:home\s+)?(?:price|value)\b",
            r"\b(?:precio|valor)\s+(?:mediano|promedio|típico)\b",
            r"\b(?:10|20)\s*%\s*(?:premium|prima)\b",
        )
        visible_patterns = (
            r"\b(?:definitive|ultimate|complete)\s+guide\b",
            r"\b(?:every|all)\s+(?:town|station|stop)s?\s+(?:with|has|have)\s+(?:a\s+)?direct\b",
            r"\b(?:best|top[- ]rated|excellent|weak(?:er)?|most valuable|most desirable|most sought[- ]after)\b",
            r"\b(?:safe(?:st)?|low[- ]crime|family[- ]friendly|perfect for families|young families)\b",
            r"\b(?:premium|ROI|return on investment|guarantee[ds]?|outperform(?:s|ed)?|holds? (?:its|their) value)\b",
            r"\b(?:guía definitiva|guía completa|cada pueblo con tren directo)\b",
            r"\b(?:mejores?|excelentes?|más (?:valiosa|deseada|codiciada))\b",
            r"\b(?:segur[oa]s?|baja criminalidad|ideal(?:es)? para familias|familias jóvenes)\b",
            r"\b(?:prima|retorno de inversión|garantizad[oa]s?|protege (?:tu|el) valor)\b",
        )
        for language, source in self.sources.items():
            text = self.texts[language]
            with self.subTest(language=language):
                for pattern in source_patterns:
                    self.assertIsNone(re.search(pattern, source, re.I), pattern)
                for pattern in visible_patterns:
                    self.assertIsNone(re.search(pattern, text, re.I), pattern)

    def test_dated_official_method_and_sources_are_visible(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(REVIEWED, manifest["reviewed"])
        self.assertEqual(TIMETABLE_EFFECTIVE, manifest["methodology"]["timetable_effective"])
        self.assertEqual("2026-08-19", manifest["methodology"]["gtfs_snapshot_date"])
        self.assertGreaterEqual(len(manifest["sources"]), 10)
        allowed_hosts = {
            "www.njtransit.com",
            "content.njtransit.com",
            "developer.njtransit.com",
            "www.nj.gov",
            "www.southorange.org",
            "www.twp.millburn.nj.us",
            "www.newprov.us",
            "www.chathamborough.org",
            "chathamborough.org",
            "www.morristwp.com",
        }
        for item in manifest["sources"]:
            self.assertTrue(item["publisher"].strip())
            self.assertTrue(item["fact_supported"].strip())
            self.assertEqual(REVIEWED, item["accessed"])
            self.assertIn((urlsplit(item["url"]).hostname or "").lower(), allowed_hosts)
            for language, source in self.sources.items():
                with self.subTest(source=item["id"], language=language):
                    self.assertIn(item["url"], source)

        for language, source in self.sources.items():
            text = self.texts[language]
            with self.subTest(language=language):
                self.assertIn("2026-05-31", source)
                self.assertIn("2026-08-19", source)
                self.assertIn("2026-08-26", source)
                self.assertIn("NJ TRANSIT", text)

    def test_homepage_visual_contract_and_accessibility(self) -> None:
        for language, source in self.sources.items():
            with self.subTest(language=language):
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertEqual(1, len(re.findall(r'<main\b[^>]*id="main"', source, re.I)))
                self.assertIn('href="#main"', source)
                ids = re.findall(r'\bid=["\']([^"\']+)', source, re.I)
                self.assertEqual(len(ids), len(set(ids)), "duplicate HTML id")
                self.assertIn("--ink: #1A1A1A", source)
                self.assertIn("--red: #C41230", source)
                self.assertIn("--deep-red: #8B0D22", source)
                self.assertIn("--gold: #B8962E", source)
                self.assertIn("--ivory: #FAFAF8", source)
                self.assertIn("'Playfair Display'", source)
                self.assertIn("'Inter'", source)
                self.assertIn("min-height: 44px", source)
                self.assertIn("min-width: 44px", source)
                self.assertIn(":focus-visible", source)
                self.assertIn(".site-header .nav-wrap { position: static !important", source)
                self.assertIn(".site-header .nav-links", source)
                self.assertIn("position: static !important", source)
                self.assertIn("/images/properties/04-brick-stone.webp", source)
                self.assertNotIn("commute-map-teaser.jpg", source)
                self.assertRegex(source, re.compile(r'<table\b[^>]*>.*?<caption\b', re.I | re.S))

    def test_json_ld_is_parseable_bilingual_and_claim_safe(self) -> None:
        for language, source in self.sources.items():
            blocks = re.findall(
                r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                source,
                re.I | re.S,
            )
            self.assertGreaterEqual(len(blocks), 3)
            parsed = [json.loads(block) for block in blocks]
            encoded = json.dumps(parsed)
            with self.subTest(language=language):
                self.assertIn("FAQPage", encoded)
                self.assertIn("BlogPosting", encoded)
                self.assertIn("BreadcrumbList", encoded)
                self.assertIn("en-US" if language == "en" else "es-US", encoded)
                self.assertIn(REVIEWED, encoded)
                self.assertNotIn("AggregateRating", encoded)
                self.assertNotIn('"Review"', encoded)
                self.assertNotIn("ratingValue", encoded)
                self.assertNotIn("priceRange", encoded)

    def test_gsc_snippet_records_match_the_safe_page_metadata(self) -> None:
        gsc = json.loads(GSC_SNIPPETS.read_text(encoding="utf-8"))
        spanish = json.loads(SPANISH_SNIPPETS.read_text(encoding="utf-8"))
        english_record = next(
            item
            for item in gsc["pages"]
            if item["file"] == "blog/midtown-direct-towns-nj.html"
        )["after"]
        expected = {
            "en": english_record,
            "es": {
                "title": "Estaciones Midtown Direct de NJ: Guía Oficial",
                "description": spanish["pages"]["es/blog/midtown-direct-towns-nj.html"][
                    "description"
                ],
            },
        }
        for language, source in self.sources.items():
            title = re.search(r"<title>(.*?)</title>", source, re.I | re.S)
            description = re.search(
                r'<meta\s+name="description"\s+content="([^"]+)">', source, re.I
            )
            self.assertIsNotNone(title, language)
            self.assertIsNotNone(description, language)
            assert title and description
            self.assertEqual(expected[language]["title"], html.unescape(title.group(1)))
            self.assertEqual(
                expected[language]["description"], html.unescape(description.group(1))
            )
            for field in ("og:description", "twitter:description"):
                self.assertIn(
                    f'{field}" content="{expected[language]["description"]}"',
                    source,
                )


if __name__ == "__main__":
    unittest.main()
