#!/usr/bin/env python3
"""Regression coverage for the five sourced Morris County priority guides."""

from __future__ import annotations

import html
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.check_town_content_quality import TownPage, near_duplicate_groups


ORIGIN = "https://thejorgeramirezgroup.com"
ACCESSED = "2026-08-25"
TARGETS = {
    "chatham-borough": {
        "identity": ("Chatham Borough", "54 Fairmount Avenue"),
        "local": ("Shepard Kollock Park", "Memorial Park", "Front Street"),
    },
    "chatham-township": {
        "identity": ("Chatham Township", "58 Meyersville Road"),
        "local": ("Nash Park", "Shunpike Field", "Colony Pool"),
    },
    "east-hanover": {
        "identity": ("East Hanover Township", "Township government"),
        "local": ("Lurker Park", "East Hanover Township School District"),
    },
    "denville": {
        "identity": ("Denville Township", "Township government"),
        "local": ("Denville Station", "Cook's Pond", "Veterans Memorial Park"),
    },
    "morris-plains": {
        "identity": ("Morris Plains Borough", "Borough government"),
        "local": ("Morris Plains Station", "Watnong Park", "Mountain Way School"),
    },
}
OFFICIAL_HOSTS = {
    "www.chathamborough.org",
    "chathamtownship.org",
    "www.easthanovertownship.com",
    "www.denvillenj.gov",
    "morrisplainsboro.org",
    "www.njtransit.com",
    "www.nj.gov",
    "dep.nj.gov",
    "www.morriscountynj.gov",
    "www.census.gov",
    "www.chatham-nj.org",
    "www.easthanoverschools.org",
    "www.hpreg.org",
    "www.denville.org",
    "www.mhrd.org",
    "sites.google.com",
    "www.morrisschooldistrict.org",
}
REQUIRED_SECTIONS = (
    "municipal identity",
    "transportation research",
    "public-school research",
    "parks and civic resources",
    "property due diligence",
    "buyer decision checklist",
    "seller decision checklist",
)
PROHIBITED = re.compile(
    r"(?:"
    r"\$\s?[\d,]+|"
    r"\b\d+(?:\.\d+)?\s*/\s*10\b|"
    r"\b(?:\d+\s*)?(?:minutes?|mins?)\s+(?:to|from)\b|"
    r"\b(?:median|average)\s+(?:home|sale|list|listing|market|days?)\b|"
    r"\bdays?\s+on\s+market\b|"
    r"\b(?:top[- ]rated|best\s+(?:town|place|school|for)|safest|safe\s+community|"
    r"family[- ]friendly|great\s+for\s+families)\b|"
    r"\b(?:appreciation|inventory|guaranteed returns?|development pipeline)\b|"
    r"\b(?:helped\s+hundreds|sales\s+volume|award[- ]winning)\b|"
    r"AI[- ]powered\s+buyer\s+targeting|"
    r"AggregateRating|openingHoursSpecification|\"@type\"\s*:\s*\"Review\""
    r")",
    re.IGNORECASE,
)


def visible_text(source: str) -> str:
    source = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", " ", source, flags=re.I | re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def json_ld(source: str) -> list[object]:
    return [
        json.loads(block)
        for block in re.findall(
            r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            source,
            flags=re.I | re.S,
        )
    ]


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


class MorrisPriorityTownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_path = ROOT / "data" / "morris-priority-town-sources.json"
        cls.manifest = json.loads(cls.manifest_path.read_text(encoding="utf-8"))
        cls.sitemap_urls = {
            (node.text or "").strip()
            for node in ET.parse(ROOT / "sitemap.xml").getroot().findall("{*}url/{*}loc")
        }

    def test_manifest_has_current_structured_official_sources(self) -> None:
        self.assertEqual(ACCESSED, self.manifest["accessed"])
        self.assertEqual(set(TARGETS), set(self.manifest["towns"]))

        for slug, sources in self.manifest["towns"].items():
            with self.subTest(slug=slug):
                self.assertGreaterEqual(len(sources), 8)
                categories = {source["category"] for source in sources}
                self.assertTrue(
                    {"municipal", "transportation", "schools", "property", "civic"}
                    <= categories
                )
                for source in sources:
                    self.assertEqual(
                        {"category", "publisher", "url", "fact_supported", "accessed"},
                        set(source),
                    )
                    self.assertEqual(ACCESSED, source["accessed"])
                    self.assertIn(urlparse(source["url"]).netloc, OFFICIAL_HOSTS)
                    self.assertGreaterEqual(len(source["fact_supported"]), 24)

    def test_pages_remain_indexable_canonical_and_submitted(self) -> None:
        for slug in TARGETS:
            source = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            canonical = f"{ORIGIN}/towns/{slug}"
            with self.subTest(slug=slug):
                self.assertRegex(source, r'<meta\s+name="robots"\s+content="index, follow')
                self.assertNotRegex(source, r'noindex|http-equiv=["\']refresh')
                self.assertIn(f'<link rel="canonical" href="{canonical}">', source)
                self.assertIn(
                    f'<link rel="alternate" hreflang="en-US" href="{canonical}">', source
                )
                self.assertIn(
                    f'<link rel="alternate" hreflang="es-US" href="{ORIGIN}/es/towns/{slug}">',
                    source,
                )
                self.assertIn(
                    f'<link rel="alternate" hreflang="x-default" href="{canonical}">', source
                )
                self.assertIn(canonical, self.sitemap_urls)

    def test_every_manifest_source_is_cited_on_its_page(self) -> None:
        for slug, sources in self.manifest["towns"].items():
            page = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            for source in sources:
                with self.subTest(slug=slug, url=source["url"]):
                    self.assertIn(source["url"], page)

    def test_pages_have_required_local_sections_and_verification_language(self) -> None:
        for slug, expectations in TARGETS.items():
            source = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            text = visible_text(source)
            with self.subTest(slug=slug):
                for phrase in REQUIRED_SECTIONS + expectations["identity"] + expectations["local"]:
                    self.assertIn(phrase.casefold(), text.casefold())
                for topic in ("tax", "zoning", "flood", "transit", "school assignment"):
                    self.assertRegex(text.casefold(), rf"verify[^.]*\b{re.escape(topic)}\b")

    def test_pages_avoid_volatile_or_steering_claims(self) -> None:
        failures: list[str] = []
        for slug in TARGETS:
            source = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            text = visible_text(source)
            matches = sorted({match.group(0) for match in PROHIBITED.finditer(text + source)})
            if matches:
                failures.append(f"{slug}: {', '.join(matches)}")
        self.assertEqual([], failures)

    def test_json_ld_is_valid_grounded_and_non_promotional(self) -> None:
        for slug in TARGETS:
            source = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            blocks = json_ld(source)
            nodes = [node for block in blocks for node in schema_nodes(block)]
            types = {node.get("@type") for node in nodes}
            with self.subTest(slug=slug):
                self.assertTrue(blocks)
                self.assertIn("WebPage", types)
                self.assertIn("BreadcrumbList", types)
                self.assertIn("FAQPage", types)
                self.assertFalse(
                    types
                    & {
                        "Review",
                        "AggregateRating",
                        "Rating",
                        "LocalBusiness",
                    }
                )
                faq = next(node for node in nodes if node.get("@type") == "FAQPage")
                for question in faq["mainEntity"]:
                    self.assertIn(question["name"], visible_text(source))

    def test_chatham_municipal_entities_are_explicitly_distinct(self) -> None:
        borough = visible_text((ROOT / "towns/chatham-borough.html").read_text(encoding="utf-8"))
        township = visible_text((ROOT / "towns/chatham-township.html").read_text(encoding="utf-8"))

        self.assertIn("separate municipality", borough.casefold())
        self.assertIn("separate municipality", township.casefold())
        self.assertIn("Chatham Station is in Chatham Borough", borough)
        self.assertIn("Chatham Station is in Chatham Borough", township)
        self.assertNotIn("58 Meyersville Road", borough)
        self.assertNotIn("54 Fairmount Avenue", township)
        self.assertNotIn("Shepard Kollock Park", township)
        self.assertNotIn("Nash Park", borough)

    def test_priority_copy_is_materially_distinct_under_strict_detector(self) -> None:
        pages = [
            TownPage.from_source(
                ROOT / "towns" / f"{slug}.html",
                (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8"),
            )
            for slug in TARGETS
        ]
        groups = near_duplicate_groups(pages, threshold=0.82, minimum_words=400)
        self.assertEqual([], groups)

    def test_shared_brand_and_accessibility_foundations_remain_present(self) -> None:
        for slug in TARGETS:
            source = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            with self.subTest(slug=slug):
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertIn('<a class="skip-link" href="#main">', source)
                self.assertIn('<main id="main">', source)
                self.assertIn('aria-label="Primary navigation"', source)
                self.assertIn("<footer", source)
                self.assertIn("/css/styles.css", source)
                for token in ("#0A0A0A", "#C41230", "#8B0D22", "#B8962E", "#F8F6F2"):
                    self.assertIn(token, source)
                for family in ("Playfair Display", "Inter", "Montserrat"):
                    self.assertIn(family, source)
                self.assertRegex(source, r"overflow-wrap:\s*anywhere")


if __name__ == "__main__":
    unittest.main()
