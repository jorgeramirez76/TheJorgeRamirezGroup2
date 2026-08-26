#!/usr/bin/env python3
"""Regression contract for the six bilingual county service guides."""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "county-guide-sources.json"
GENERATOR = ROOT / "tools" / "generate_county_guides.py"
SITE = "https://thejorgeramirezgroup.com"
PALETTE = {"#1A1A1A", "#C41230", "#8B0D22", "#B8962E", "#FAFAF8"}
SOURCE_IDS = {
    "njr-county-reports",
    "nj-tax-statistics",
    "nj-school-reports",
    "nj-transit-planner",
    "nj-locality-search",
}
RISKY_COPY = re.compile(
    r"AI[- ]powered|sell(?:s|ing)? (?:faster|for more)|under \d+ days|"
    r"multiple offers|maximum exposure|qualified buyers|best schools?|"
    r"perfect for|ideal for|famil(?:y|ies)|safe(?:st|ty)?|crime rate|"
    r"guarantee|predict(?:ion|s|ed)?|appreciat(?:e|ion)|"
    r"hottest market|top[- ]rated|5[- ]star|hundreds of",
    re.IGNORECASE,
)


class GuideParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.hreflangs: list[tuple[str, str]] = []
        self.robots: list[str] = []
        self.links: list[str] = []
        self.ids: list[str] = []
        self.duplicate_attributes: list[str] = []
        self.h1_count = 0
        self.main_count = 0
        self.stylesheets: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        names = [name.lower() for name, _ in attrs]
        if len(names) != len(set(names)):
            self.duplicate_attributes.append(tag)
        values = {name.lower(): value or "" for name, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        if tag == "link" and values.get("hreflang"):
            self.hreflangs.append((values["hreflang"], values.get("href", "")))
        if tag == "link" and "stylesheet" in values.get("rel", "").split():
            self.stylesheets.append(values.get("href", ""))
        if tag == "meta" and values.get("name", "").lower() == "robots":
            self.robots.append(values.get("content", ""))
        if tag == "a":
            self.links.append(values.get("href", ""))
        if tag == "h1":
            self.h1_count += 1
        if tag == "main":
            self.main_count += 1


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def paths() -> list[tuple[dict, str, Path]]:
    result = []
    for county in manifest()["counties"]:
        for language in ("en", "es"):
            prefix = Path("es") if language == "es" else Path()
            result.append(
                (
                    county,
                    language,
                    ROOT / prefix / "counties" / f"{county['slug']}-county.html",
                )
            )
    return result


def route(county: dict, language: str) -> str:
    return f"/{'es/' if language == 'es' else ''}counties/{county['slug']}-county"


def parse(path: Path) -> tuple[str, GuideParser]:
    source = path.read_text(encoding="utf-8")
    parser = GuideParser()
    parser.feed(source)
    return source, parser


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style|template)\b[^>]*>.*?</(?:script|style|template)>",
        " ",
        source,
        flags=re.IGNORECASE | re.DOTALL,
    )
    source = re.sub(r"<!--.*?-->|<[^>]+>", " ", source, flags=re.DOTALL)
    return " ".join(html.unescape(source).split())


def sitemap_urls(name: str) -> set[str]:
    root = ET.parse(ROOT / name).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


class CountyGuideTests(unittest.TestCase):
    def test_manifest_is_exact_and_source_review_is_explicit(self) -> None:
        document = manifest()
        self.assertEqual(1, document["schemaVersion"])
        self.assertEqual("2026-08-26", document["reviewedOn"])
        self.assertEqual("tools/generate_county_guides.py", document["renderer"])
        self.assertEqual(
            {"union", "essex", "morris", "hudson", "middlesex", "somerset"},
            {item["slug"] for item in document["counties"]},
        )
        self.assertEqual(SOURCE_IDS, {item["id"] for item in document["sharedSources"]})
        for item in document["sharedSources"]:
            self.assertTrue(item["url"].startswith("https://"))
            self.assertTrue(item["use"])
            self.assertTrue(item["limit"])
        for county in document["counties"]:
            self.assertTrue(county["directoryUrl"].startswith("https://"))

    def test_all_pages_are_branded_indexable_and_reciprocal(self) -> None:
        source_urls = {item["url"] for item in manifest()["sharedSources"]}
        for county, language, path in paths():
            with self.subTest(path=path.relative_to(ROOT)):
                source, parser = parse(path)
                own_route = route(county, language)
                en_route = route(county, "en")
                es_route = route(county, "es")
                self.assertEqual([SITE + own_route], parser.canonicals)
                self.assertEqual(1, parser.h1_count)
                self.assertEqual(1, parser.main_count)
                self.assertEqual([], parser.duplicate_attributes)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                self.assertTrue(any("index" in item.lower() for item in parser.robots))
                self.assertIn(("en-US", SITE + en_route), parser.hreflangs)
                self.assertIn(("es-US", SITE + es_route), parser.hreflangs)
                self.assertIn(("x-default", SITE + en_route), parser.hreflangs)
                self.assertIn("/css/styles.css", parser.stylesheets)
                self.assertIn("/images/jorge-logo.jpg", source)
                self.assertIn("Playfair Display", source)
                self.assertIn("Inter", source)
                self.assertIn(
                    ".county-research-page .breadcrumbs{position:static;top:auto;"
                    "z-index:auto;width:auto;padding:0;background:transparent;"
                    "backdrop-filter:none;box-shadow:none;transition:none",
                    source,
                )
                for color in PALETTE:
                    self.assertIn(color, source)
                for url in source_urls | {county["directoryUrl"]}:
                    self.assertIn(url, parser.links)
                self.assertIn("data-source-review=\"2026-08-26\"", source)
                self.assertIsNone(RISKY_COPY.search(visible_text(source)))

    def test_pages_link_every_maintained_town_for_their_county(self) -> None:
        facts = json.loads((ROOT / "data" / "site-facts.json").read_text(encoding="utf-8"))
        towns_by_county = facts["business"].get("canonicalTownInventory")
        if towns_by_county is None:
            towns_by_county = facts["canonicalTownInventory"]
        towns_by_county = towns_by_county["byCounty"]
        for county, language, path in paths():
            _, parser = parse(path)
            prefix = "/es" if language == "es" else ""
            for slug in towns_by_county[county["name"]]:
                with self.subTest(path=path.relative_to(ROOT), town=slug):
                    self.assertIn(f"{prefix}/towns/{slug}", parser.links)

    def test_pages_remain_in_the_correct_sitemap(self) -> None:
        english = sitemap_urls("sitemap.xml")
        spanish = sitemap_urls("sitemap-es.xml")
        for county in manifest()["counties"]:
            self.assertIn(SITE + route(county, "en"), english)
            self.assertIn(SITE + route(county, "es"), spanish)

    def test_structured_data_is_valid_json(self) -> None:
        for _, _, path in paths():
            source = path.read_text(encoding="utf-8")
            blocks = re.findall(
                r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
                source,
                flags=re.DOTALL,
            )
            self.assertTrue(blocks, path)
            for block in blocks:
                json.loads(block)

    def test_renderer_is_idempotent(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
