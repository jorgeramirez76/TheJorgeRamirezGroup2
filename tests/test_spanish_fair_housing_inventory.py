#!/usr/bin/env python3
"""Exact-inventory contract for the Spanish non-town fair-housing cleanup."""

from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import fix_spanish_translations
import translate_to_spanish
from scripts.apply_spanish_snippets import load_pages as load_snippet_pages
from scripts.fix_spanish_internal_links import normalize as normalize_internal_links
from scripts.normalize_spanish_fair_housing import normalize, targets
from scripts.quarantine_spanish_fair_housing_doorways import (
    CLICKED_REDIRECTS,
    GSC_EXPORT_SHA256,
    SITE,
    fallback,
    gsc_snapshot,
    normalized_route,
    quarantine_mapping,
    route_for,
)
from tools.check_spanish_fair_housing import (
    INVENTORY_PATH,
    ROOT,
    audit,
    discover_inventory,
    expected_payload,
    read,
)


ROBOTS_NOINDEX = re.compile(
    r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*\bnoindex\b',
    re.I,
)
HREF = re.compile(r'\bhref\s*=\s*["\']([^"\']+)["\']', re.I)


class SpanishFairHousingInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        cls.manifest = json.loads(
            (ROOT / "data" / "spanish-fair-housing-quarantine.json").read_text(
                encoding="utf-8"
            )
        )
        cls.mapping = quarantine_mapping()

    def test_inventory_is_exact_disjoint_and_named_exclusions_are_preserved(self) -> None:
        discovered = discover_inventory()
        reviewed = set(self.inventory["reviewed"])
        quarantined = set(self.inventory["quarantined"])
        self.assertFalse(reviewed & quarantined)
        self.assertEqual(reviewed | quarantined, set(discovered.pop("owned")))
        self.assertEqual(self.inventory["excluded"], discovered)
        self.assertEqual(expected_payload(), self.inventory)
        self.assertEqual(68, len(reviewed))
        self.assertEqual(105, len(quarantined))
        self.assertEqual(10, len(self.inventory["excluded"]["rebuilt"]))
        self.assertEqual(50, len(self.inventory["excluded"]["market_reports"]))
        self.assertEqual(9, len(self.inventory["excluded"]["redirects"]))
        self.assertEqual(138, len(self.inventory["excluded"]["directories"]))

    def test_public_pages_and_emitters_have_no_contextual_risk(self) -> None:
        self.assertEqual([], audit())

    def test_integrated_comparison_copy_cannot_restore_steering_or_unsupported_claims(self) -> None:
        source = read("es/blog/summit-vs-westfield-nj.html").casefold()
        for phrase in (
            "calificación a+",
            "de los mejores de nueva jersey",
            "orientado a la familia",
            "lugares excepcionales",
            "cientos de consultas",
            "al derecho y al revés",
            "cada vecindario, cada calle",
            "impulsado por la reputación de sus escuelas",
            "las escuelas y el centro de westfield impulsan",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, source)

    def test_manifest_has_exact_clusters_dispositions_and_gsc_decisions(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "gsc-spanish-fair-housing-quarantine-pages.csv"
        self.assertNotIn(b"\r\n", fixture.read_bytes())
        pages = self.manifest["pages"]
        self.assertEqual(105, len(pages))
        self.assertEqual(set(self.mapping), {page["file"] for page in pages})
        self.assertEqual(
            Counter(
                {
                    "scaled-town-buying": 47,
                    "scaled-town-selling": 44,
                    "scaled-neighborhood-profile": 11,
                    "subjective-school-ranking": 1,
                    "unsafe-inherited-seller": 2,
                }
            ),
            Counter(page["cluster"] for page in pages),
        )
        self.assertEqual(
            Counter({"static-noindex-fallback": 104, "same-intent-redirect": 1}),
            Counter(page["disposition"] for page in pages),
        )

        metrics, aggregate = gsc_snapshot(self.mapping)
        self.assertEqual(GSC_EXPORT_SHA256, aggregate["sourceExportSha256"])
        self.assertEqual(
            {
                "routes": 1,
                "routesWithRows": 1,
                "lastThreeMonthsClicks": 1,
                "previousThreeMonthsClicks": 0,
                "lastThreeMonthsImpressions": 20,
                "previousThreeMonthsImpressions": 0,
            },
            aggregate["trafficPreservedBySameIntentRedirect"],
        )
        self.assertEqual(
            {
                "routes": 104,
                "routesWithRows": 55,
                "lastThreeMonthsClicks": 0,
                "previousThreeMonthsClicks": 0,
                "lastThreeMonthsImpressions": 520,
                "previousThreeMonthsImpressions": 112,
            },
            aggregate["staticNoindexFallback"],
        )
        self.assertEqual(aggregate, self.manifest["signalReview"]["gsc"])
        by_route = {page["path"]: page for page in pages}
        for route, values in metrics.items():
            with self.subTest(route=route):
                self.assertEqual(values, by_route[route]["gsc"])
                if values["lastThreeMonthsClicks"] or values["previousThreeMonthsClicks"]:
                    self.assertIn(route, CLICKED_REDIRECTS)

    def test_fallbacks_match_renderer_accessibility_analytics_and_palette_contract(self) -> None:
        pages = {page["file"]: page for page in self.manifest["pages"]}
        for relative, destination in self.mapping.items():
            route = route_for(relative)
            redirect = route in CLICKED_REDIRECTS
            source = read(relative)
            with self.subTest(path=relative):
                self.assertEqual(fallback(destination, redirect=redirect), source)
                self.assertRegex(source, ROBOTS_NOINDEX)
                self.assertNotRegex(source, re.compile(r'<link\b[^>]*hreflang=', re.I))
                self.assertIn('<html lang="es">', source)
                self.assertIn('<a class="skip-link" href="#main">', source)
                self.assertIn('<main id="main">', source)
                self.assertIn('min-height:48px', source)
                self.assertIn('/css/styles.css', source)
                for token in ("#C41230", "#B8962E", "#0A0A0A", "#1A1A1A", "#FAFAF8"):
                    self.assertIn(token, source)
                self.assertIn(f'<link rel="canonical" href="{SITE}{destination}">', source)
                self.assertIn(f'<meta property="og:url" content="{SITE}{destination}">', source)
                self.assertIn('<meta property="og:locale" content="es_US">', source)
                self.assertIn('<meta name="twitter:card" content="summary_large_image">', source)
                self.assertIn("G-KMS6H85LB0", source)
                self.assertNotIn("application/ld+json", source)
                self.assertLess(len(re.sub(r"<[^>]+>", " ", source).split()), 180)
                if redirect:
                    self.assertIn('http-equiv="refresh"', source)
                    self.assertIn("window.location.replace", source)
                    self.assertEqual("same-intent-redirect", pages[relative]["disposition"])
                else:
                    self.assertNotIn('http-equiv="refresh"', source)
                    self.assertNotIn("window.location.replace", source)
                    self.assertEqual("static-noindex-fallback", pages[relative]["disposition"])

    def test_stable_destinations_exist_remain_indexable_and_redirects_are_one_hop(self) -> None:
        redirect_config = json.loads(read("vercel.json"))
        redirect_sources = {
            item["source"].rstrip("/").removesuffix(".html")
            for item in redirect_config.get("redirects", [])
        }
        quarantined_routes = {route_for(relative) for relative in self.mapping}
        for destination in set(self.mapping.values()):
            candidates = (
                ROOT / f"{destination.lstrip('/')}.html",
                ROOT / destination.lstrip("/") / "index.html",
            )
            target = next((path for path in candidates if path.exists()), None)
            with self.subTest(destination=destination):
                self.assertIsNotNone(target)
                assert target is not None
                self.assertNotRegex(target.read_text(encoding="utf-8"), ROBOTS_NOINDEX)
                self.assertNotIn(destination.rstrip("/"), redirect_sources)
        for item in redirect_config.get("redirects", []):
            destination = item.get("destination", "").split("?", 1)[0].rstrip("/").removesuffix(".html")
            self.assertNotIn(destination, quarantined_routes)

    def test_quarantined_routes_are_absent_from_sitemap_blog_and_owned_links(self) -> None:
        sitemap = {
            (loc.text or "").rstrip("/")
            for loc in ET.parse(ROOT / "sitemap-es.xml").getroot().findall(".//{*}loc")
        }
        blog_index = read("es/blog/index.html")
        routes = {route_for(relative) for relative in self.mapping}
        for route in routes:
            absolute = SITE + route
            with self.subTest(route=route):
                self.assertNotIn(absolute.rstrip("/"), sitemap)
                self.assertNotIn(f'href="{route}"', blog_index)
                self.assertNotIn(f'href="{route}.html"', blog_index)

        for relative in self.inventory["reviewed"]:
            if not relative.endswith(".html"):
                continue
            source_path = ROOT / relative
            for href in HREF.findall(source_path.read_text(encoding="utf-8", errors="replace")):
                with self.subTest(path=relative, href=href):
                    self.assertNotIn(normalized_route(href, source_path), routes)

    def test_english_reciprocal_inventory_does_not_advertise_quarantine_routes(self) -> None:
        routes = {SITE + route_for(relative) for relative in self.mapping}
        alternate = re.compile(
            r'<link\b[^>]*rel=["\']alternate["\'][^>]*hreflang=["\'](?:es-US|es)["\'][^>]*>',
            re.I,
        )
        for path in sorted(ROOT.rglob("*.html")):
            relative = path.relative_to(ROOT)
            if relative.parts and relative.parts[0] in {"es", "towns", "realtor", "node_modules"}:
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            for tag in alternate.findall(source):
                with self.subTest(path=relative):
                    self.assertFalse(any(route in tag for route in routes))
        sitemap = read("sitemap.xml")
        for route in routes:
            self.assertNotRegex(
                sitemap,
                re.compile(
                    rf'<xhtml:link\b[^>]*hreflang=["\'](?:es-US|es)["\'][^>]*href=["\']{re.escape(route)}(?:\.html)?/?["\']',
                    re.I,
                ),
            )

    def test_emitters_cannot_restore_reviewed_or_quarantined_outputs(self) -> None:
        managed = set(self.inventory["reviewed"]) | set(self.inventory["quarantined"])
        self.assertEqual(managed, translate_to_spanish.managed_spanish_outputs())
        self.assertFalse(translate_to_spanish.translate_page(ROOT / "buy-a-home.html"))
        self.assertEqual(
            "Agente con Licencia en Nueva Jersey",
            translate_to_spanish.translate_text("Top Rated"),
        )
        self.assertEqual(
            "Agente con Licencia en Nueva Jersey",
            translate_to_spanish.translate_text("5-Star Rated"),
        )
        snippet_pages = set(load_snippet_pages())
        self.assertFalse(snippet_pages & set(self.inventory["quarantined"]))
        with self.assertRaisesRegex(SystemExit, "Archived"):
            fix_spanish_translations.main()

        translator = read("translate_to_spanish.py")
        snippets = read("scripts/apply_spanish_snippets.py")
        copy_tool = read("tools/fix_spanish_copy_quality.py")
        self.assertIn("managed_spanish_outputs", translator)
        self.assertIn("if es_relative in managed_spanish_outputs()", translator)
        self.assertIn("spanish-fair-housing-quarantine.json", snippets)
        self.assertIn("spanish-fair-housing-quarantine.json", copy_tool)

    def test_normalizers_and_renderers_are_idempotent(self) -> None:
        for relative in targets():
            source = read(relative)
            with self.subTest(path=relative):
                self.assertEqual(source, normalize(source, relative))
        for relative in [
            "es/blog/best-nj-suburbs-nyc-commuters.html",
            "es/blog/first-time-home-buyer-nj-guide.html",
        ]:
            source = read(relative)
            self.assertEqual(source, normalize_internal_links(source))

    def test_source_archive_and_spanish_quality_contract_are_explicit(self) -> None:
        archive = json.loads(
            read("data/spanish-fair-housing-source-archives.json")
        )
        self.assertEqual([], archive["unpublished_spanish_content_sources"])
        self.assertEqual(
            ["fix_spanish_translations.py"],
            [item["file"] for item in archive["archived_legacy_emitters"]],
        )
        self.assertEqual([], list((ROOT / "es").rglob("*.md")))
        self.assertNotIn("/es/contact", "\n".join(read(path) for path in self.inventory["reviewed"]))
        self.assertNotIn("/es/terms-of-service", read("es/blog/first-time-home-buyer-nj-guide.html"))

    def test_broken_spanish_route_source_guards_are_exact(self) -> None:
        self.assertEqual(
            '<a href="/es/#contact">Contacto</a>',
            translate_to_spanish.fix_internal_links('<a href="/contact">Contacto</a>'),
        )
        self.assertEqual(
            '<p><a href="/es/privacy-policy">Privacidad</a></p>',
            translate_to_spanish.remove_missing_spanish_policy_links(
                '<p><a href="/es/privacy-policy">Privacidad</a> · '
                '<a href="/es/terms-of-service">Términos</a></p>'
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
