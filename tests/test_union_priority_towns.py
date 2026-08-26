#!/usr/bin/env python3
"""Regression coverage for the six source-backed Union County town guides."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from itertools import combinations
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.check_town_content_quality import (
    REVIEW_MINIMUM_WORDS,
    REVIEW_SIMILARITY,
    near_duplicate_groups,
    scan_town_pages,
)

MANIFEST_PATH = ROOT / "data" / "union-priority-town-sources.json"
SLUGS = (
    "berkeley-heights",
    "cranford",
    "fanwood",
    "new-providence",
    "roselle-park",
    "springfield",
)
REQUIRED_SOURCE_CATEGORIES = {
    "municipal",
    "transit",
    "schools",
    "parks_civic",
    "property_due_diligence",
}
ALLOWED_OFFICIAL_HOSTS = {
    "content.njtransit.com",
    "fanwoodnj.org",
    "springfield-nj.us",
    "ucnj.org",
    "www.berkeleyheights.gov",
    "www.bhpsnj.org",
    "www.cranfordnj.org",
    "www.cranfordschools.org",
    "www.newprov.us",
    "www.nj.gov",
    "www.njtransit.com",
    "www.npsd.k12.nj.us",
    "www.rosellepark.net",
    "www.rpsd.org",
    "www.spfk12.org",
    "www.springfieldschools.com",
}
PROHIBITED_COPY = re.compile(
    r"(?:"
    r"\b(?:top|best|leading|premier|elite)[- ]rated\b|"
    r"\b(?:safe|safest|family[- ]friendly|best\s+(?:place|town|neighbou?rhood)\s+for\s+famil(?:y|ies))\b|"
    r"\b(?:school|district)\s+(?:rating|score)\b|"
    r"\b\d+(?:\.\d+)?\s*/\s*10\b|"
    r"\bmedian\s+(?:home\s+)?(?:price|sale\s+price)\b|"
    r"\bdays?\s+on\s+market\b|"
    r"\b\d+\s*(?:minutes?|mins?)\s+(?:to|from)\s+(?:NYC|Manhattan|New York)\b|"
    r"\b(?:appreciation|reliable\s+returns?|inventory|development\s+pipeline)\b|"
    r"\b(?:AI[- ]powered|buyer\s+targeting|proven\s+results?|helped\s+hundreds)\b|"
    r"\bavailable\s+(?:8\s*a\.?m\.?|seven|7)\b"
    r")",
    re.IGNORECASE,
)


def parse_sitemap(name: str) -> set[str]:
    document = ET.parse(ROOT / name).getroot()
    return {(node.text or "").strip() for node in document.findall("{*}url/{*}loc")}


def visible_main_text(source: str) -> str:
    main = re.search(r"<main\b[^>]*>(.*?)</main>", source, re.I | re.S)
    if not main:
        return ""
    text = re.sub(r"<(?:script|style|template)\b[^>]*>.*?</(?:script|style|template)>", " ", main.group(1), flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def normalized_distinctive_text(source: str, slug: str) -> set[str]:
    text = visible_main_text(source).lower().replace(slug.replace("-", " "), " townname ")
    text = re.sub(r"\b\d[\d,.#-]*\b", " number ", text)
    words = re.findall(r"[a-z]+", text)
    return {" ".join(words[index : index + 7]) for index in range(max(0, len(words) - 6))}


class UnionPriorityTownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.pages = {
            slug: (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            for slug in SLUGS
        }

    def test_pages_remain_indexable_canonical_and_submitted(self) -> None:
        sitemap = parse_sitemap("sitemap.xml")
        for slug, source in self.pages.items():
            canonical = f"https://thejorgeramirezgroup.com/towns/{slug}"
            with self.subTest(slug=slug):
                robots = re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)', source, re.I)
                self.assertIsNotNone(robots)
                self.assertNotIn("noindex", robots.group(1).lower())
                self.assertEqual(1, len(re.findall(r'<link\b[^>]*rel=["\']canonical["\'][^>]*', source, re.I)))
                self.assertIn(f'<link rel="canonical" href="{canonical}">', source)
                self.assertIn(f'hreflang="en-US" href="{canonical}"', source)
                self.assertIn(canonical, sitemap)

    def test_each_page_uses_covered_official_sources(self) -> None:
        self.assertEqual("2026-08-25", self.manifest["accessed"])
        towns = self.manifest["towns"]
        self.assertEqual(set(SLUGS), set(towns))
        for slug, town in towns.items():
            categories = {source["category"] for source in town["sources"]}
            with self.subTest(slug=slug):
                self.assertTrue(REQUIRED_SOURCE_CATEGORIES.issubset(categories))
                self.assertGreaterEqual(len(town["sources"]), 5)
                for source in town["sources"]:
                    self.assertTrue(source["publisher"].strip())
                    self.assertTrue(source["fact_supported"].strip())
                    self.assertEqual("2026-08-25", source["accessed"])
                    host = (urlsplit(source["url"]).hostname or "").lower()
                    self.assertIn(host, ALLOWED_OFFICIAL_HOSTS, f"{slug}: non-official host {host}")
                    self.assertIn(source["url"], self.pages[slug])

    def test_copy_avoids_volatile_ranked_or_steering_claims(self) -> None:
        for slug, source in self.pages.items():
            text = visible_main_text(source)
            with self.subTest(slug=slug):
                self.assertIsNone(PROHIBITED_COPY.search(text), PROHIBITED_COPY.search(text))
                self.assertNotRegex(text, r"\$\s*\d")
                self.assertIn("Verify", text)
                self.assertIn("official", text.lower())

    def test_pages_are_materially_distinct(self) -> None:
        fingerprints = {
            slug: normalized_distinctive_text(source, slug)
            for slug, source in self.pages.items()
        }
        for left, right in combinations(SLUGS, 2):
            union = fingerprints[left] | fingerprints[right]
            similarity = len(fingerprints[left] & fingerprints[right]) / len(union)
            with self.subTest(left=left, right=right):
                self.assertLess(similarity, 0.45)
                self.assertNotEqual(
                    hashlib.sha256(visible_main_text(self.pages[left]).encode()).hexdigest(),
                    hashlib.sha256(visible_main_text(self.pages[right]).encode()).hexdigest(),
                )

    def test_priority_pages_clear_the_repository_strict_detector(self) -> None:
        groups = near_duplicate_groups(
            scan_town_pages(ROOT),
            threshold=REVIEW_SIMILARITY,
            minimum_words=REVIEW_MINIMUM_WORDS,
        )
        flagged = {
            page.slug
            for group in groups
            for page in group
            if page.language == "en" and page.slug in SLUGS
        }
        self.assertEqual(set(), flagged)

    def test_metadata_schema_and_accessibility_basics(self) -> None:
        for slug, source in self.pages.items():
            with self.subTest(slug=slug):
                title = re.search(r"<title>(.*?)</title>", source, re.I | re.S).group(1).strip()
                description = re.search(r'<meta\b[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)', source, re.I).group(1)
                self.assertLessEqual(len(title), 65)
                self.assertGreaterEqual(len(description), 120)
                self.assertLessEqual(len(description), 165)
                self.assertEqual(1, len(re.findall(r'<h1\b', source, re.I)))
                self.assertEqual(1, len(re.findall(r'<main\b[^>]*id=["\']main["\']', source, re.I)))
                ids = re.findall(r'\bid=["\']([^"\']+)', source, re.I)
                self.assertEqual(len(ids), len(set(ids)), "duplicate HTML id")
                self.assertIn('href="#main"', source)
                self.assertIn('class="topnav"', source)
                self.assertIn('class="cta-final"', source)
                self.assertIn("--accent: #C41230", source)
                self.assertIn("--gold: #B8962E", source)
                blocks = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', source, re.I | re.S)
                self.assertGreaterEqual(len(blocks), 1)
                schemas = [json.loads(block) for block in blocks]
                encoded = json.dumps(schemas)
                self.assertNotIn("AggregateRating", encoded)
                self.assertNotRegex(encoded, r'"@type"\s*:\s*"Review"')
                self.assertIn("FAQPage", encoded)


if __name__ == "__main__":
    unittest.main()
