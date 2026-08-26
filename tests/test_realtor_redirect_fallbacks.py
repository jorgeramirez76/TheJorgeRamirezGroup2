#!/usr/bin/env python3
"""Regression contract for the retired realtor doorway-page layer."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
REALTOR_DIR = ROOT / "realtor"
VERCEL_PATH = ROOT / "vercel.json"
GENERATOR = ROOT / "gen_realtor_pages.py"
SITE_ORIGIN = "https://thejorgeramirezgroup.com"
TOWN_RULE = re.compile(r"^/realtor/([a-z0-9-]+)-nj$")
ALIASES = {
    "bernards-township": "basking-ridge",
    "short-hills": "millburn",
}


class FallbackParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.refreshes: list[str] = []
        self.links: list[str] = []
        self.main_count = 0
        self.h1_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        elif tag == "meta" and values.get("name", "").lower() == "robots":
            self.robots.append(values.get("content", ""))
        elif tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            self.refreshes.append(values.get("content", ""))
        elif tag == "a":
            self.links.append(values.get("href", ""))
        elif tag == "main":
            self.main_count += 1
        elif tag == "h1":
            self.h1_count += 1


def redirect_inventory() -> tuple[dict[str, str], list[dict[str, object]]]:
    config = json.loads(VERCEL_PATH.read_text(encoding="utf-8"))
    redirects = config.get("redirects", [])
    expected: dict[str, str] = {}
    for item in redirects:
        match = TOWN_RULE.fullmatch(str(item.get("source", "")))
        if not match:
            continue
        slug = match.group(1)
        expected[f"{slug}-nj.html"] = str(item.get("destination", ""))
    expected["index.html"] = "/communities"
    return expected, redirects


class RealtorRedirectFallbackTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.expected, cls.redirects = redirect_inventory()

    def test_inventory_matches_the_138_town_redirects_plus_hub(self) -> None:
        self.assertEqual(139, len(self.expected))
        self.assertEqual(138, len(self.expected) - 1)
        actual = {path.name for path in REALTOR_DIR.glob("*.html")}
        self.assertEqual(set(self.expected), actual)

        for filename, destination in self.expected.items():
            if filename == "index.html":
                self.assertEqual("/communities", destination)
                self.assertTrue((ROOT / "communities.html").exists())
                continue
            slug = filename.removesuffix("-nj.html")
            target_slug = ALIASES.get(slug, slug)
            self.assertEqual(f"/towns/{target_slug}", destination)
            target = ROOT / "towns" / f"{target_slug}.html"
            self.assertTrue(target.exists())
            self.assertNotRegex(
                target.read_text(encoding="utf-8"),
                r'<meta\b[^>]*http-equiv=["\']refresh["\']',
            )

    def test_vercel_redirect_coverage_is_permanent_and_one_hop(self) -> None:
        wildcard = [
            item
            for item in self.redirects
            if item.get("source") == "/realtor/:slug-nj.html"
        ]
        self.assertEqual(
            [
                {
                    "source": "/realtor/:slug-nj.html",
                    "destination": "/towns/:slug",
                    "permanent": True,
                }
            ],
            wildcard,
        )

        hub = [item for item in self.redirects if item.get("source") == "/realtor"]
        self.assertEqual(
            [{"source": "/realtor", "destination": "/communities", "permanent": True}],
            hub,
        )

        clean_rules = {
            item["source"]: item
            for item in self.redirects
            if TOWN_RULE.fullmatch(str(item.get("source", "")))
        }
        self.assertEqual(138, len(clean_rules))
        all_sources = {str(item.get("source", "")) for item in self.redirects}
        for filename, destination in self.expected.items():
            if filename == "index.html":
                continue
            slug = filename.removesuffix("-nj.html")
            source = f"/realtor/{slug}-nj"
            item = clean_rules[source]
            self.assertIs(True, item.get("permanent"))
            self.assertEqual(destination, item.get("destination"))
            self.assertNotIn(destination, all_sources, "destination must not redirect again")

    def test_each_file_is_a_small_exact_noindex_redirect_fallback(self) -> None:
        forbidden = re.compile(
            r"FAQPage|RealEstateAgent|AggregateRating|Review|priceRange|"
            r"median|market\s+(?:price|report|data)|school\s+(?:rating|score)|"
            r"commute\s+(?:time|minutes?)|homes?\s+for\s+sale|top[- ]rated|"
            r"licensed\s+(?:NJ\s+)?Realtor|\$\s*\d",
            re.IGNORECASE,
        )
        for filename, destination in self.expected.items():
            path = REALTOR_DIR / filename
            source = path.read_text(encoding="utf-8")
            parser = FallbackParser()
            parser.feed(source)
            with self.subTest(filename=filename):
                self.assertLess(len(source.encode("utf-8")), 5000)
                self.assertEqual([SITE_ORIGIN + destination], parser.canonicals)
                self.assertEqual(["noindex, follow"], parser.robots)
                self.assertEqual([f"0;url={destination}"], parser.refreshes)
                self.assertEqual([destination], parser.links)
                self.assertEqual(1, parser.main_count)
                self.assertEqual(1, parser.h1_count)
                self.assertIn(
                    f"window.location.replace({json.dumps(destination)})", source
                )
                self.assertNotIn("application/ld+json", source.lower())
                self.assertIsNone(forbidden.search(source))

    def test_realtor_urls_are_absent_from_sitemaps(self) -> None:
        offenders: list[str] = []
        for sitemap in ROOT.glob("sitemap*.xml"):
            document = ET.parse(sitemap).getroot()
            for node in document.iter():
                candidates = [(node.text or "").strip(), *node.attrib.values()]
                for url in candidates:
                    path = urlsplit(url).path
                    if path.rstrip("/") == "/realtor" or path.startswith("/realtor/"):
                        offenders.append(f"{sitemap.name}: {url}")
        self.assertEqual([], offenders)

    def test_generator_is_redirect_only_and_idempotent(self) -> None:
        source = GENERATOR.read_text(encoding="utf-8")
        self.assertIn("redirect-only compatibility fallbacks", source)
        self.assertNotIn("from town_data import", source)
        self.assertNotRegex(source, r"build_(?:schema|faqs)|extract_data|FAQPage")
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("139 redirect fallbacks are current", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
