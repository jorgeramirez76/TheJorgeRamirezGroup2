#!/usr/bin/env python3
"""Exact-inventory contract for the owned English fair-housing cleanup."""

from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from scripts.normalize_english_fair_housing import normalize, target_files
from scripts.quarantine_english_fair_housing_doorways import (
    GSC_EXPORT_SHA256,
    SITE,
    TOWN_ROUTE_DESTINATIONS,
    fallback,
    gsc_snapshot,
    normalized_route,
    quarantine_mapping,
    route_for,
)
from tools.check_english_fair_housing import (
    INVENTORY_PATH,
    ROOT,
    ROBOTS_NOINDEX,
    blocking_issues,
    discover_inventory,
    read,
)


class EnglishFairHousingInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        cls.manifest = json.loads(
            (ROOT / "data" / "english-fair-housing-quarantine.json").read_text(
                encoding="utf-8"
            )
        )
        cls.doorway_manifest = json.loads(
            (ROOT / "data" / "programmatic-doorway-retirement.json").read_text(
                encoding="utf-8"
            )
        )
        cls.mapping = quarantine_mapping()

    def test_inventory_is_exact_and_named_exclusions_are_preserved(self) -> None:
        discovered = discover_inventory()
        expected_owned = set(self.inventory["reviewed"]) | set(self.inventory["quarantined"])
        self.assertEqual(expected_owned, set(discovered.pop("owned")))
        self.assertEqual(self.inventory["excluded"], discovered)
        self.assertEqual(141, len(self.inventory["excluded"]["retired"]))
        self.assertEqual(151, len(self.inventory["excluded"]["redirects"]))
        self.assertEqual(
            {item["file"] for item in self.doorway_manifest["pages"]},
            set(self.inventory["excluded"]["retired_programmatic_doorways"]),
        )
        self.assertEqual(
            52, len(self.inventory["excluded"]["retired_programmatic_doorways"])
        )

    def test_reviewed_pages_and_emitters_have_no_risk_patterns(self) -> None:
        self.assertEqual([], blocking_issues())

    def test_quarantined_pages_are_compact_neutral_noindex_fallbacks(self) -> None:
        for relative in self.inventory["quarantined"]:
            source = read(relative)
            with self.subTest(path=relative):
                self.assertRegex(source, ROBOTS_NOINDEX)
                self.assertNotRegex(source, re.compile(r'<link\b[^>]*hreflang=', re.I))
                self.assertIn('<a class="skip-link" href="#main">', source)
                self.assertIn('<main id="main">', source)
                self.assertIn('/css/styles.css', source)
                self.assertLess(len(re.sub(r"<[^>]+>", " ", source).split()), 260)

    def test_quarantine_manifest_has_exact_clusters_and_dispositions(self) -> None:
        pages = self.manifest["pages"]
        self.assertEqual(107, len(pages))
        self.assertEqual(set(self.mapping), {page["file"] for page in pages})
        self.assertEqual(
            Counter(
                {
                    "scaled-town-buying": 47,
                    "scaled-town-selling": 44,
                    "scaled-neighborhood-ranking": 11,
                    "subjective-school-ranking": 1,
                    "legacy-commuter-ranking": 1,
                    "legacy-three-town-ranking": 1,
                    "duplicate-town-comparison": 1,
                    "unmaintained-school-ranking-comparison": 1,
                }
            ),
            Counter(page["cluster"] for page in pages),
        )
        self.assertEqual(
            Counter({"same-intent-redirect": 16, "static-noindex-fallback": 91}),
            Counter(page["disposition"] for page in pages),
        )

    def test_gsc_snapshot_and_signal_decisions_are_exact(self) -> None:
        pages = {page["path"]: page for page in self.manifest["pages"]}
        metrics, aggregate = gsc_snapshot(self.mapping)
        self.assertEqual(GSC_EXPORT_SHA256, aggregate["sourceExportSha256"])
        self.assertEqual(
            {
                "routes": 16,
                "routesWithRows": 15,
                "lastThreeMonthsClicks": 30,
                "previousThreeMonthsClicks": 27,
                "lastThreeMonthsImpressions": 3606,
                "previousThreeMonthsImpressions": 3624,
            },
            aggregate["trafficPreservedBySameIntentRedirect"],
        )
        self.assertEqual(
            {
                "routes": 91,
                "routesWithRows": 90,
                "lastThreeMonthsClicks": 0,
                "previousThreeMonthsClicks": 0,
                "lastThreeMonthsImpressions": 1478,
                "previousThreeMonthsImpressions": 1216,
            },
            aggregate["staticNoindexFallback"],
        )
        self.assertEqual(aggregate, self.manifest["signalReview"]["gsc"])
        for route, values in metrics.items():
            with self.subTest(route=route):
                self.assertEqual(values, pages[route]["gsc"])
                if values["lastThreeMonthsClicks"] or values["previousThreeMonthsClicks"]:
                    self.assertIn(route, TOWN_ROUTE_DESTINATIONS)

    def test_fallbacks_match_the_deterministic_redirect_contract(self) -> None:
        pages = {page["file"]: page for page in self.manifest["pages"]}
        for relative, destination in self.mapping.items():
            redirect = route_for(relative) in TOWN_ROUTE_DESTINATIONS
            source = read(relative)
            with self.subTest(path=relative):
                self.assertEqual(fallback(destination, redirect=redirect), source)
                self.assertIn(f'<link rel="canonical" href="{SITE}{destination}">', source)
                self.assertIn(f'<meta property="og:url" content="{SITE}{destination}">', source)
                self.assertIn('<meta property="og:title"', source)
                self.assertIn('<meta property="og:description"', source)
                self.assertIn('<meta name="twitter:card" content="summary_large_image">', source)
                self.assertIn('<meta name="twitter:title"', source)
                self.assertIn('<meta name="twitter:description"', source)
                self.assertIn('G-KMS6H85LB0', source)
                self.assertNotIn('application/ld+json', source)
                if redirect:
                    self.assertIn('<meta http-equiv="refresh" content="0; url=', source)
                    self.assertIn("window.location.replace", source)
                    self.assertEqual("same-intent-redirect", pages[relative]["disposition"])
                else:
                    self.assertNotIn('http-equiv="refresh"', source)
                    self.assertNotIn("window.location.replace", source)
                    self.assertEqual("static-noindex-fallback", pages[relative]["disposition"])

    def test_every_redirect_destination_exists_and_remains_indexable(self) -> None:
        for route, destination in TOWN_ROUTE_DESTINATIONS.items():
            candidates = (
                ROOT / f"{destination.lstrip('/')}.html",
                ROOT / destination.lstrip("/") / "index.html",
            )
            target = next((path for path in candidates if path.exists()), None)
            with self.subTest(route=route, destination=destination):
                self.assertIsNotNone(target)
                assert target is not None
                self.assertNotRegex(target.read_text(encoding="utf-8"), ROBOTS_NOINDEX)

    def test_quarantined_routes_are_absent_from_public_inventory(self) -> None:
        sitemap = {
            (loc.text or "").rstrip("/")
            for loc in ET.parse(ROOT / "sitemap.xml").getroot().findall(".//{*}loc")
        }
        blog_index = read("blog/index.html")
        for relative in self.inventory["quarantined"]:
            route = "/" + relative.removesuffix(".html")
            absolute = "https://thejorgeramirezgroup.com" + route
            with self.subTest(route=route):
                self.assertNotIn(absolute.rstrip("/"), sitemap)
                self.assertNotIn(f'href="{route}"', blog_index)

    def test_owned_pages_do_not_link_to_quarantined_routes(self) -> None:
        routes = {route_for(relative) for relative in self.mapping}
        href_re = re.compile(r'\bhref\s*=\s*["\']([^"\']+)["\']', re.I)
        emitter_files = set(self.inventory["emitters"])
        for relative in set(self.inventory["reviewed"]) - emitter_files:
            if not relative.endswith(".html"):
                continue
            source_path = ROOT / relative
            for href in href_re.findall(source_path.read_text(encoding="utf-8")):
                with self.subTest(path=relative, href=href):
                    self.assertNotIn(normalized_route(href, source_path), routes)

    def test_spanish_files_only_drop_reciprocal_links_to_quarantined_routes(self) -> None:
        routes = {route_for(relative) for relative in self.mapping}
        alternate = re.compile(
            r'<link\b[^>]*rel=["\']alternate["\'][^>]*'
            r'hreflang=["\'](?:en-US|x-default)["\'][^>]*href=["\']([^"\']+)',
            re.I,
        )
        for path in sorted((ROOT / "es").rglob("*.html")):
            for href in alternate.findall(path.read_text(encoding="utf-8", errors="replace")):
                with self.subTest(path=path.relative_to(ROOT), href=href):
                    self.assertNotIn(normalized_route(href, path), routes)
        sitemap_es = read("sitemap-es.xml")
        for route in routes:
            with self.subTest(route=route):
                self.assertNotRegex(
                    sitemap_es,
                    re.compile(
                        rf'<xhtml:link\b[^>]*hreflang=["\'](?:en-US|x-default)["\']'
                        rf'[^>]*href=["\']{re.escape(SITE + route)}(?:\.html)?/?["\']',
                        re.I,
                    ),
                )

    def test_emitters_cannot_restore_quarantined_pages(self) -> None:
        source = read("generate_blog.py")
        self.assertIn("QUARANTINE_MANIFEST", source)
        self.assertIn("QUARANTINED_OUTPUTS", source)
        self.assertIn('Path(item["file"]).name', source)
        self.assertIn("if filename in QUARANTINED_OUTPUTS:", source)
        self.assertIn("return", source)
        template = read("tools/blog-automation/template_source.html")
        self.assertIn("buying-a-home-in-new-jersey-2026", template)
        daily = read("tools/blog-automation/daily_blog.py")
        self.assertIn("t = t.replace(OLD_SLUG, slug)", daily)

    def test_normalizer_is_idempotent_on_every_target(self) -> None:
        for path in target_files():
            source = path.read_text(encoding="utf-8", errors="replace")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(source, normalize(source))

    def test_unsafe_markdown_emitters_are_exact_unpublished_archive_stubs(self) -> None:
        archive = json.loads(
            (ROOT / "data" / "english-fair-housing-source-archives.json").read_text(
                encoding="utf-8"
            )
        )
        sources = archive["sources"]
        self.assertEqual(11, len(sources))
        files = {item["file"] for item in sources}
        unpublished_posts = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "_posts").glob("*.md")
            if re.search(r"(?m)^published:\s*false\s*$", path.read_text(encoding="utf-8"))
        }
        self.assertEqual(files, unpublished_posts)

        quarantined = {page["file"] for page in self.manifest["pages"]}
        unsafe_source = re.compile(
            r"\b(?:30|45)\s+minutes?\b|ranked\s*#?1|critical inflection point|"
            r"panic[- ]sell|5\s*%\s+discount|top district|new families|Public The|"
            r"school-district information\s+\*?compare recent property-specific sales|"
            r"projected appreciation|guaranteed? returns?",
            re.I,
        )
        for item in sources:
            source = read(item["file"])
            with self.subTest(path=item["file"]):
                self.assertIn("published: false", source)
                self.assertIn("sitemap: false", source)
                self.assertIn("robots: noindex, nofollow", source)
                self.assertIn(f"]({item['destination']})", source)
                self.assertLess(len(source.split()), 70)
                self.assertNotRegex(source, unsafe_source)
                self.assertFalse(any(line.endswith((" ", "\t")) for line in source.splitlines()))
                if item["public_file"]:
                    self.assertIn(item["public_file"], quarantined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
