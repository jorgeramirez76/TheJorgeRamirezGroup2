#!/usr/bin/env python3
"""Regression coverage for the five source-backed priority town guides."""

from __future__ import annotations

import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.check_town_content_quality import TownPage, near_duplicate_groups


TARGETS = {
    "east-brunswick": {
        "name": "East Brunswick",
        "county": "Middlesex County",
        "municipal_host": "eastbrunswick.org",
        "required_facts": (
            "Transportation and Commerce Center",
            "Neilson Plaza",
            "Route 138",
        ),
        "forbidden_facts": ("Dayton", "Deans", "Kendall Park", "Monmouth Junction"),
    },
    "south-brunswick": {
        "name": "South Brunswick",
        "county": "Middlesex County",
        "municipal_host": "southbrunswicknj.gov",
        "required_facts": ("Dayton", "Deans", "Kendall Park", "Monmouth Junction"),
        "forbidden_facts": ("Transportation and Commerce Center", "Neilson Plaza", "Route 138"),
    },
    "west-new-york": {
        "name": "West New York",
        "county": "Hudson County",
        "municipal_host": "westnewyorknj.org",
        "required_facts": ("Bergenline Avenue", "Route 156", "Donnelly Park"),
        "forbidden_facts": ("Anna L. Klein School", "Waterfront Park", "Route 188"),
    },
    "guttenberg": {
        "name": "Guttenberg",
        "county": "Hudson County",
        "municipal_host": "guttenbergnj.org",
        "required_facts": ("Anna L. Klein School", "Waterfront Park", "Route 188"),
        "forbidden_facts": ("Memorial High School", "Donnelly Park", "Route 156"),
    },
    "bloomfield": {
        "name": "Bloomfield",
        "county": "Essex County",
        "municipal_host": "bloomfieldtwpnj.com",
        "required_facts": ("Bloomfield station", "Watsessing Avenue station", "Montclair-Boonton Line"),
        "forbidden_facts": ("Midtown Direct", "Hudson-Bergen Light Rail"),
    },
}

ALLOWED_SOURCE_HOSTS = {
    "www.census.gov",
    "data.census.gov",
    "www.nj.gov",
    "nj.gov",
    "dep.nj.gov",
    "www.njtransit.com",
    "content.njtransit.com",
    "www.eastbrunswick.org",
    "eastbrunswick.org",
    "www.ebnet.org",
    "ebnet.org",
    "southbrunswicknj.gov",
    "www.southbrunswicknj.gov",
    "www.sbschools.org",
    "sbschools.org",
    "www.middlesexcountynj.gov",
    "middlesexcountynj.gov",
    "www.westnewyorknj.org",
    "westnewyorknj.org",
    "www.wnyschools.net",
    "wnyschools.net",
    "www.guttenbergnj.org",
    "guttenbergnj.org",
    "www.alkschool.org",
    "alkschool.org",
    "www.bloomfieldtwpnj.com",
    "bloomfieldtwpnj.com",
    "www.bloomfield.k12.nj.us",
    "bloomfield.k12.nj.us",
    "essexcountyparks.org",
    "www.essexcountyparks.org",
}

PROHIBITED = re.compile(
    r"(?:"
    r"median\s+(?:home|sale)\s+price|days\s+on\s+market|\b\d{1,2}/10\b|"
    r"family[- ]friendly|perfect\s+for\s+famil|ideal\s+for\s+famil|"
    r"strong\s+schools?|top[- ]rated|top\s+(?:real\s+estate\s+)?agent|"
    r"best\s+(?:place|town|neighbou?rhood|school|agent)|"
    r"safe(?:st|ty)?\s+(?:town|community|neighbou?rhood)|crime\s+rate|"
    r"appreciation|reliable\s+returns?|investment\s+opportunit|"
    r"ai[- ]powered|buyer\s+targeting|get\s+top\s+dollar|"
    r"available\s+\d+\s*days|\b7\s+days(?:\s*/?\s*week)?|"
    r"approximately\s+\$[\d,.]+|\$\d{3},\d{3}"
    r")",
    re.IGNORECASE,
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.text_parts: list[str] = []
        self.json_scripts: list[str] = []
        self._json_depth = 0
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.tags.append((tag, values))
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json_depth = 1
            self._json_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_depth:
            self.json_scripts.append("".join(self._json_parts).strip())
            self._json_depth = 0
            self._json_parts = []

    def handle_data(self, data: str) -> None:
        if self._json_depth:
            self._json_parts.append(data)
        else:
            value = " ".join(data.split())
            if value:
                self.text_parts.append(value)

    def attrs(self, tag: str) -> list[dict[str, str]]:
        return [attrs for current, attrs in self.tags if current == tag]

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def page_source(slug: str) -> str:
    return (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")


def parse_page(slug: str) -> PageParser:
    parser = PageParser()
    parser.feed(page_source(slug))
    return parser


def sitemap_urls(name: str) -> set[str]:
    root = ET.parse(ROOT / name).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


def graph_types(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        current = value.get("@type")
        if isinstance(current, str):
            found.add(current)
        elif isinstance(current, list):
            found.update(item for item in current if isinstance(item, str))
        for child in value.values():
            found.update(graph_types(child))
    elif isinstance(value, list):
        for child in value:
            found.update(graph_types(child))
    return found


class OtherPriorityTownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (ROOT / "data" / "other-priority-town-sources.json").read_text(encoding="utf-8")
        )

    def test_pages_remain_indexable_canonical_and_submitted(self) -> None:
        submitted = sitemap_urls("sitemap.xml")
        for slug in TARGETS:
            with self.subTest(slug=slug):
                source = page_source(slug)
                parser = parse_page(slug)
                canonical = f"https://thejorgeramirezgroup.com/towns/{slug}"
                robots = [tag.get("content", "") for tag in parser.attrs("meta") if tag.get("name") == "robots"]
                canonicals = [tag.get("href") for tag in parser.attrs("link") if tag.get("rel") == "canonical"]
                alternates = {
                    (tag.get("hreflang"), tag.get("href"))
                    for tag in parser.attrs("link")
                    if tag.get("rel") == "alternate"
                }
                self.assertTrue(robots and all("noindex" not in value.lower() for value in robots))
                self.assertEqual([canonical], canonicals)
                self.assertIn(("en-US", canonical), alternates)
                self.assertIn(("es-US", f"https://thejorgeramirezgroup.com/es/towns/{slug}"), alternates)
                self.assertIn(("x-default", canonical), alternates)
                self.assertIn(canonical, submitted)
                self.assertNotRegex(source, r'<meta\b[^>]*http-equiv=["\']refresh')

    def test_manifest_and_pages_use_traceable_official_sources(self) -> None:
        self.assertEqual("2026-08-25", self.manifest["accessed"])
        self.assertEqual(set(TARGETS), set(self.manifest["municipalities"]))
        for slug, expected in TARGETS.items():
            with self.subTest(slug=slug):
                parser = parse_page(slug)
                hrefs = {tag.get("href", "") for tag in parser.attrs("a")}
                sources = self.manifest["municipalities"][slug]["sources"]
                self.assertGreaterEqual(len(sources), 8)
                hosts: set[str] = set()
                for item in sources:
                    self.assertEqual({"url", "publisher", "fact_supported", "accessed"}, set(item))
                    self.assertEqual("2026-08-25", item["accessed"])
                    self.assertTrue(item["publisher"].strip())
                    self.assertTrue(item["fact_supported"].strip())
                    host = urlsplit(item["url"]).netloc.lower()
                    hosts.add(host.removeprefix("www."))
                    self.assertIn(host, ALLOWED_SOURCE_HOSTS)
                    self.assertIn(item["url"], hrefs)
                self.assertIn(expected["municipal_host"], hosts)
                self.assertTrue({"nj.gov", "dep.nj.gov"} & hosts)
                self.assertTrue({"www.census.gov", "data.census.gov"} & {urlsplit(i["url"]).netloc for i in sources})

    def test_pages_remove_volatile_claims_and_preserve_municipal_identity(self) -> None:
        for slug, expected in TARGETS.items():
            with self.subTest(slug=slug):
                text = parse_page(slug).text
                self.assertIn(expected["name"], text)
                self.assertIn(expected["county"], text)
                self.assertIsNone(PROHIBITED.search(text), PROHIBITED.search(text).group(0) if PROHIBITED.search(text) else "")
                for fact in expected["required_facts"]:
                    self.assertIn(fact, text)
                for fact in expected["forbidden_facts"]:
                    self.assertNotIn(fact, text)
                for reminder in ("tax", "zoning", "flood", "transit", "school assignment"):
                    self.assertIn(reminder, text.lower())

    def test_pages_are_materially_distinct_under_strict_detector(self) -> None:
        pages = [
            TownPage.from_source(ROOT / "towns" / f"{slug}.html", page_source(slug))
            for slug in TARGETS
        ]
        groups = near_duplicate_groups(pages, threshold=0.70, minimum_words=650)
        self.assertEqual([], groups)

    def test_metadata_json_ld_and_visible_faq_are_consistent(self) -> None:
        titles: set[str] = set()
        descriptions: set[str] = set()
        for slug, expected in TARGETS.items():
            with self.subTest(slug=slug):
                parser = parse_page(slug)
                title_tags = parser.attrs("title")
                # HTMLParser exposes title text through the page text, so read it directly.
                title_match = re.search(r"<title>(.*?)</title>", page_source(slug), re.S | re.I)
                self.assertIsNotNone(title_match)
                title = " ".join(title_match.group(1).split())
                descriptions_for_page = [
                    tag.get("content", "")
                    for tag in parser.attrs("meta")
                    if tag.get("name") == "description"
                ]
                self.assertEqual(1, len(descriptions_for_page))
                description = descriptions_for_page[0]
                self.assertGreaterEqual(len(title), 35)
                self.assertLessEqual(len(title), 65)
                self.assertGreaterEqual(len(description), 120)
                self.assertLessEqual(len(description), 165)
                self.assertIn(expected["name"], title)
                self.assertIn(expected["name"], description)
                titles.add(title)
                descriptions.add(description)
                self.assertGreaterEqual(len(parser.json_scripts), 1)
                schemas = [json.loads(script) for script in parser.json_scripts]
                types = set().union(*(graph_types(schema) for schema in schemas))
                self.assertTrue({"WebPage", "BreadcrumbList", "FAQPage"}.issubset(types))
                self.assertFalse({"Review", "AggregateRating"} & types)
                faq_questions = []
                for schema in schemas:
                    for node in schema.get("@graph", [schema]) if isinstance(schema, dict) else []:
                        if isinstance(node, dict) and node.get("@type") == "FAQPage":
                            faq_questions.extend(item["name"] for item in node.get("mainEntity", []))
                self.assertGreaterEqual(len(faq_questions), 3)
                for question in faq_questions:
                    self.assertIn(question, parser.text)
        self.assertEqual(len(TARGETS), len(titles))
        self.assertEqual(len(TARGETS), len(descriptions))

    def test_brand_shell_and_basic_accessibility_remain_intact(self) -> None:
        for slug in TARGETS:
            with self.subTest(slug=slug):
                source = page_source(slug)
                parser = parse_page(slug)
                html_tags = parser.attrs("html")
                self.assertEqual("en", html_tags[0].get("lang"))
                self.assertIn('href="#main"', source)
                self.assertRegex(source, r'<main\b[^>]*\bid=["\']main["\']')
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertRegex(source, r'<nav\b[^>]*aria-label=["\'][^"\']+["\']')
                self.assertIn("--dark: #0A0A0A", source)
                self.assertIn("--accent: #C41230", source)
                self.assertIn("--gold: #B8962E", source)
                self.assertIn("--light: #F8F6F2", source)
                for image in parser.attrs("img"):
                    self.assertTrue(image.get("alt", "").strip())
                for link in parser.attrs("a"):
                    self.assertTrue(link.get("href", "").strip())
                self.assertIn("@media (max-width: 768px)", source)


if __name__ == "__main__":
    unittest.main()
