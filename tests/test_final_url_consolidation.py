#!/usr/bin/env python3
"""Fail-closed contract for the final same-intent URL consolidations."""

from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
SITEMAPS = {"sitemap.xml": 157, "sitemap-es.xml": 127}
CONSOLIDATIONS = (
    (
        "/blog/renting-vs-buying-nj-2026",
        "blog/renting-vs-buying-nj-2026.html",
        "/rent-vs-buy-nj",
        "rent-vs-buy-nj.html",
    ),
    (
        "/best-real-estate-agents-essex-county-nj-2026",
        "best-real-estate-agents-essex-county-nj-2026.html",
        "/counties/essex-county",
        "counties/essex-county.html",
    ),
    (
        "/best-real-estate-agents-morris-county-nj-2026",
        "best-real-estate-agents-morris-county-nj-2026.html",
        "/counties/morris-county",
        "counties/morris-county.html",
    ),
)
BRAND_TOKENS = ("#0A0A0A", "#1A1A1A", "#C41230", "#B8962E", "#FAFAF8")
RISKY_COPY = (
    "best real estate agent",
    "best realtor",
    "top real estate agent",
    "top-rated",
    "ranked",
    "#1",
    "number one",
    "guaranteed results",
    "aggregaterating",
    "ratingvalue",
    "reviewcount",
)


class HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.visible_parts: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "template", "noscript"}:
            self._hidden_depth += 1
        if tag == "a":
            values = {key.casefold(): value or "" for key, value in attrs}
            if values.get("href"):
                self.hrefs.append(values["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "template", "noscript"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth:
            normalized = " ".join(data.split())
            if normalized:
                self.visible_parts.append(normalized)

    @property
    def visible_text(self) -> str:
        return " ".join(self.visible_parts)


def sitemap_urls(path: Path) -> list[str]:
    return [
        (node.text or "").strip()
        for node in ET.parse(path).getroot().findall("{*}url/{*}loc")
    ]


class FinalUrlConsolidationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        cls.redirects = cls.config["redirects"]
        cls.by_source: dict[str, list[dict[str, object]]] = {}
        for rule in cls.redirects:
            cls.by_source.setdefault(str(rule.get("source", "")), []).append(rule)
        cls.urls_by_sitemap = {
            filename: sitemap_urls(ROOT / filename) for filename in SITEMAPS
        }

    def test_consolidation_rules_follow_host_guards_and_precede_normalization(self) -> None:
        self.assertNotIn("bulkRedirectsPath", self.config)
        self.assertFalse((ROOT / "vercel-bulk-redirects.json").exists())
        expected = []
        for clean_source, _fallback, destination, _destination_file in CONSOLIDATIONS:
            for source in (clean_source, clean_source + ".html"):
                rule = {
                    "source": source,
                    "destination": destination,
                    "permanent": True,
                }
                expected.append(rule)
                with self.subTest(source=source):
                    self.assertEqual([rule], self.by_source.get(source))
            with self.subTest(destination=destination):
                self.assertNotIn(destination, self.by_source)
        indexes = [self.redirects.index(rule) for rule in expected]
        self.assertEqual(sorted(indexes), indexes)
        self.assertGreaterEqual(min(indexes), 2)
        self.assertLess(max(indexes), len(self.redirects) - 7)

    def test_fallbacks_are_compact_neutral_noindex_documents(self) -> None:
        for _source, fallback, destination, _destination_file in CONSOLIDATIONS:
            content = (ROOT / fallback).read_text(encoding="utf-8")
            folded = content.casefold()
            parser = HrefParser()
            parser.feed(content)
            visible = parser.visible_text.casefold()
            with self.subTest(fallback=fallback):
                self.assertLess(len(content.encode("utf-8")), 8_192)
                self.assertIn('<meta name="robots" content="noindex, follow">', content)
                self.assertIn(
                    '<meta name="ai-content-declaration" content="ai-assisted, source-checked">',
                    content,
                )
                self.assertIn(f'<link rel="canonical" href="{SITE}{destination}">', content)
                self.assertIn(f'content="0; url={destination}"', content)
                self.assertIn(f"window.location.replace('{destination}')", content)
                self.assertRegex(content, rf'<a\b[^>]*href="{re.escape(destination)}"')
                self.assertEqual(1, len(re.findall(r"<main\b", content, re.I)))
                self.assertEqual(1, len(re.findall(r"<h1\b", content, re.I)))
                self.assertNotIn("hreflang=", folded)
                self.assertNotIn("application/ld+json", folded)
                for token in BRAND_TOKENS:
                    self.assertIn(token, content)
                for phrase in RISKY_COPY:
                    candidate = visible if phrase == "#1" else folded
                    self.assertNotIn(phrase, candidate)

    def test_sitemaps_publish_only_the_three_maintained_destinations(self) -> None:
        all_urls: list[str] = []
        for filename, expected_count in SITEMAPS.items():
            urls = self.urls_by_sitemap[filename]
            with self.subTest(filename=filename):
                self.assertEqual(expected_count, len(urls))
                self.assertEqual([], [url for url, count in Counter(urls).items() if count > 1])
            all_urls.extend(urls)
        self.assertEqual(284, len(all_urls))
        self.assertEqual(284, len(set(all_urls)))

        english_urls = self.urls_by_sitemap["sitemap.xml"]
        for source, _fallback, destination, _destination_file in CONSOLIDATIONS:
            for obsolete in (source, source + ".html"):
                with self.subTest(obsolete=obsolete):
                    self.assertNotIn(SITE + obsolete, all_urls)
            with self.subTest(destination=destination):
                self.assertEqual(1, english_urls.count(SITE + destination))

    def test_destinations_remain_indexable_and_self_canonical(self) -> None:
        for _source, _fallback, destination, destination_file in CONSOLIDATIONS:
            content = (ROOT / destination_file).read_text(encoding="utf-8")
            robots = re.findall(
                r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)',
                content,
                re.I,
            )
            with self.subTest(destination=destination):
                self.assertEqual(1, len(robots))
                self.assertTrue(robots[0].casefold().startswith("index, follow"), robots[0])
                self.assertNotIn("noindex", robots[0].casefold())
                self.assertIn(f'<link rel="canonical" href="{SITE}{destination}">', content)
                self.assertNotRegex(content, r'<meta\b[^>]*http-equiv=["\']refresh["\']')

    def test_no_html_page_links_to_an_obsolete_source(self) -> None:
        obsolete_slugs = tuple(source.lstrip("/") for source, *_rest in CONSOLIDATIONS)
        ignored_parts = {".git", ".vercel", "node_modules", "coverage", "tmp"}
        offenders: list[str] = []
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT)
            if ignored_parts.intersection(relative.parts):
                continue
            parser = HrefParser()
            parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
            for href in parser.hrefs:
                href_path = urlsplit(href).path.lstrip("/")
                if any(slug in href_path for slug in obsolete_slugs):
                    offenders.append(f"{relative.as_posix()}: {href}")
        self.assertEqual([], offenders)

    def test_blog_hubs_use_the_maintained_rent_vs_buy_route(self) -> None:
        for relative in ("blog/index.html", "es/blog/index.html"):
            content = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertNotIn("renting-vs-buying-nj-2026", content)
        self.assertIn('href="/rent-vs-buy-nj"', (ROOT / "blog/index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
