#!/usr/bin/env python3
"""Regression contract for the market-report containment batch."""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.generate_market_report_containment import (  # noqa: E402
    _ensure_vercel_redirects,
    generated_page_paths,
    load_inventory,
)
from tools.market_report_publication_gate import (  # noqa: E402
    ProvenanceError,
    validate_publication_manifest,
)


SITE = "https://thejorgeramirezgroup.com"
MANIFEST_PATH = ROOT / "data" / "market-report-containment.json"
SKIP_DIRS = {
    ".git",
    ".vercel",
    "crm",
    "docs",
    "node_modules",
    "property-leads-system",
}
PALETTE = {"#1A1A1A", "#C41230", "#B8962E", "#FAFAF8"}

EXPECTED_NOINDEX = {
    "basking-ridge",
    "bloomfield",
    "clark",
    "edison",
    "fanwood",
    "florham-park",
    "highland-park",
    "mountain-lakes",
    "mountainside",
    "north-caldwell",
    "nutley",
    "old-bridge",
    "parsippany",
    "roseland",
    "springfield",
    "summit",
    "verona",
}
EXPECTED_REBUILD = {
    "market-report-chatham-nj-2026",
    "market-report-cranford-nj-2026",
    "market-report-denville-nj-2026",
    "market-report-glen-ridge-nj-2026",
    "market-report-linden-nj-2026",
    "market-report-livingston-nj-2026",
    "market-report-madison-nj-2026",
    "market-report-maplewood-nj-2026",
    "market-report-metuchen-nj-2026",
    "market-report-montclair-nj-2026",
    "market-report-morristown-nj-2026",
    "market-report-new-providence-nj-2026",
    "market-report-rahway-nj-2026",
    "market-report-randolph-nj-2026",
    "market-report-scotch-plains-nj-2026",
    "market-report-short-hills-nj-2026",
    "market-report-south-brunswick-nj-2026",
    "market-report-south-orange-nj-2026",
    "market-report-warren-township-nj-2026",
    "market-report-west-orange-nj-2026",
    "market-report-westfield-nj-2026",
    "market-report-woodbridge-nj-2026",
    "essex-county-nj-real-estate-market-2026",
    "hudson-county-real-estate-market-q2-2026",
    "middlesex-county-real-estate-market-q2-2026",
    "morris-county-nj-real-estate-market-2026",
    "union-county-nj-real-estate-market-report-2026",
}
EXPECTED_REDIRECTS = {
    "/blog/chatham-nj-real-estate-market-2025": "/blog/market-report-chatham-nj-2026",
    "/es/blog/chatham-nj-real-estate-market-2025": "/es/blog/market-report-chatham-nj-2026",
    "/blog/westfield-nj-real-estate-market-2025": "/blog/market-report-westfield-nj-2026",
    "/es/blog/westfield-nj-real-estate-market-2025": "/es/blog/market-report-westfield-nj-2026",
    "/blog/essex-county-real-estate-market-q2-2026": "/blog/essex-county-nj-real-estate-market-2026",
    "/es/blog/essex-county-real-estate-market-q2-2026": "/es/blog/essex-county-nj-real-estate-market-2026",
    "/blog/morris-county-real-estate-market-q2-2026": "/blog/morris-county-nj-real-estate-market-2026",
    "/es/blog/morris-county-real-estate-market-q2-2026": "/es/blog/morris-county-nj-real-estate-market-2026",
    "/blog/market-report-millburn-nj-2026": "/blog/market-report-short-hills-nj-2026",
    "/es/blog/market-report-millburn-nj-2026": "/es/blog/market-report-short-hills-nj-2026",
}


def route_file(route: str) -> Path:
    return ROOT / f"{route.lstrip('/')}.html"


def normalized_path(value: str, *, source: Path | None = None) -> str:
    parsed = urlsplit(value)
    path = parsed.path
    if not path.startswith("/") and source is not None:
        relative = (source.parent / path).resolve().relative_to(ROOT.resolve())
        path = "/" + relative.as_posix()
    path = path.rstrip("/") or "/"
    if path.endswith(".html"):
        path = path[:-5]
    return path


def sitemap_urls(name: str) -> set[str]:
    root = ET.parse(ROOT / name).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def integrated_fallback_paths() -> list[Path]:
    """Return the exact integrated 107 fair-housing and 74 town fallbacks."""

    fair_housing = json.loads(
        (ROOT / "data" / "english-fair-housing-quarantine.json").read_text(
            encoding="utf-8"
        )
    )
    town_policy = json.loads(
        (ROOT / "data" / "english-noindex-town-fallbacks.json").read_text(
            encoding="utf-8"
        )
    )
    fair_paths = [ROOT / item["file"] for item in fair_housing["pages"]]
    town_paths = [
        ROOT / "towns" / f"{slug}.html"
        for group in town_policy["groups"]
        for slug in group["slugs"]
    ]
    if len(fair_paths) != 107 or len(set(fair_paths)) != 107:
        raise AssertionError("expected the exact 107-page fair-housing quarantine")
    if len(town_paths) != 74 or len(set(town_paths)) != 74:
        raise AssertionError("expected the exact 74-page town fallback inventory")
    if set(fair_paths) & set(town_paths):
        raise AssertionError("integrated fallback inventories must be disjoint")
    return fair_paths + town_paths


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.refreshes: list[str] = []
        self.hreflangs: list[str] = []
        self.links: list[str] = []
        self.main_count = 0
        self.h1_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        if tag == "link" and values.get("hreflang"):
            self.hreflangs.append(values.get("href", ""))
        if tag == "meta" and values.get("name", "").lower() == "robots":
            self.robots.append(values.get("content", ""))
        if tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            self.refreshes.append(values.get("content", ""))
        if tag == "a":
            self.links.append(values.get("href", ""))
        if tag == "main":
            self.main_count += 1
        if tag == "h1":
            self.h1_count += 1


def parsed_page(path: Path) -> tuple[str, PageParser]:
    source = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(source)
    return source, parser


class MarketReportInventoryTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = load_inventory(MANIFEST_PATH)

    def test_exact_inventory_partition_is_reviewed_and_disjoint(self) -> None:
        self.assertEqual(1, self.inventory["version"])
        self.assertEqual("2026-08-26", self.inventory["reviewedOn"])
        self.assertEqual(5, len(self.inventory["redirectPairs"]))
        self.assertEqual(17, len(self.inventory["noindexTownReports"]))
        self.assertEqual(27, len(self.inventory["rebuildPairs"]))

        redirects = {
            pair["source"][language]: pair["destination"][language]
            for pair in self.inventory["redirectPairs"]
            for language in ("en", "es")
        }
        self.assertEqual(EXPECTED_REDIRECTS, redirects)
        self.assertEqual(
            EXPECTED_NOINDEX,
            {item["slug"] for item in self.inventory["noindexTownReports"]},
        )
        self.assertEqual(EXPECTED_REBUILD, set(self.inventory["rebuildPairs"]))

        noindex_stubs = {
            f"market-report-{slug}-nj-2026" for slug in EXPECTED_NOINDEX
        }
        redirect_blog_stubs = {
            normalized_path(route).removeprefix("/blog/")
            for route in EXPECTED_REDIRECTS
            if route.startswith("/blog/")
        }
        self.assertTrue(noindex_stubs.isdisjoint(EXPECTED_REBUILD))
        self.assertTrue(noindex_stubs.isdisjoint(redirect_blog_stubs))
        self.assertTrue(EXPECTED_REBUILD.isdisjoint(redirect_blog_stubs))

    def test_managed_page_inventory_is_exactly_44_files(self) -> None:
        paths = generated_page_paths(self.inventory, root=ROOT)
        self.assertEqual(44, len(paths))
        self.assertEqual(44, len(set(paths)))
        self.assertTrue(all(path.exists() for path in paths))


class MarketReportRedirectTests(unittest.TestCase):
    def test_future_missing_redirects_follow_the_canonical_host_preamble(self) -> None:
        live_config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        host_preamble = live_config["redirects"][:2]
        unrelated = [
            {
                "source": "/unrelated-exact",
                "destination": "/unrelated-target",
                "permanent": True,
            },
            {
                "source": "/realtor/:slug-nj",
                "destination": "/towns/:slug",
                "permanent": True,
            },
        ]
        source = json.dumps(
            {"redirects": host_preamble + unrelated}, indent=2
        ) + "\n"
        inventory = {
            "redirectPairs": [
                {
                    "source": {
                        "en": "/synthetic-market-report",
                        "es": "/es/synthetic-market-report",
                    },
                    "destination": {
                        "en": "/blog/current-market-report",
                        "es": "/es/blog/current-market-report",
                    },
                }
            ]
        }

        rendered = json.loads(_ensure_vercel_redirects(source, inventory))["redirects"]

        self.assertEqual(host_preamble, rendered[:2])
        managed_sources = {
            "/synthetic-market-report",
            "/synthetic-market-report.html",
            "/es/synthetic-market-report",
            "/es/synthetic-market-report.html",
        }
        self.assertEqual(
            host_preamble + unrelated,
            [rule for rule in rendered if rule["source"] not in managed_sources],
        )
        self.assertEqual(
            managed_sources,
            {rule["source"] for rule in rendered[2:6]},
        )

    def test_ten_language_preserving_redirects_are_permanent_and_one_hop(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirects = {
            item["source"]: item
            for item in config.get("redirects", [])
            if not item.get("has") and ":" not in str(item.get("source", ""))
        }
        for source, destination in EXPECTED_REDIRECTS.items():
            with self.subTest(source=source):
                self.assertEqual(destination, redirects[source].get("destination"))
                self.assertIs(True, redirects[source].get("permanent"))
                self.assertNotIn(destination, redirects, "redirect destination must be final")
                self.assertEqual(source.startswith("/es/"), destination.startswith("/es/"))

                html_source = source + ".html"
                self.assertEqual(destination, redirects[html_source].get("destination"))
                self.assertIs(True, redirects[html_source].get("permanent"))

    def test_redirect_fallbacks_are_small_accessible_and_exact(self) -> None:
        for source_route, destination in EXPECTED_REDIRECTS.items():
            path = route_file(source_route)
            source, parser = parsed_page(path)
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertLess(len(source.encode("utf-8")), 6000)
                self.assertEqual(["noindex, follow"], parser.robots)
                self.assertEqual([SITE + destination], parser.canonicals)
                self.assertEqual([f"0; url={destination}"], parser.refreshes)
                self.assertEqual([], parser.hreflangs)
                self.assertIn(destination, parser.links)
                self.assertEqual(1, parser.main_count)
                self.assertEqual(1, parser.h1_count)
                self.assertIn("window.location.replace", source)
                self.assertNotIn("application/ld+json", source)
                for token in PALETTE:
                    self.assertIn(token, source)
                self.assertIn("'Playfair Display'", source)
                self.assertIn("Inter", source)
                self.assertRegex(source, r"min-height:\s*44px")
                self.assertIn(":focus-visible", source)


class MarketReportNoindexFallbackTests(unittest.TestCase):
    def test_34_noindex_pages_are_compact_useful_and_not_translated_as_alternates(self) -> None:
        inventory = load_inventory(MANIFEST_PATH)
        for item in inventory["noindexTownReports"]:
            slug = item["slug"]
            town_guide_slug = item.get("townGuideSlug", slug)
            for language, prefix in (("en", ""), ("es", "es/")):
                relative = f"{prefix}blog/market-report-{slug}-nj-2026.html"
                path = ROOT / relative
                source, parser = parsed_page(path)
                deployed = "/" + relative.removesuffix(".html")
                town_route = f"/{prefix}towns/{town_guide_slug}"
                valuation_route = f"/{prefix}home-valuation"
                home_route = "/" if language == "en" else "/es/"
                switch_route = "/es/" if language == "en" else "/"
                with self.subTest(relative=relative):
                    self.assertLess(len(source.encode("utf-8")), 10000)
                    self.assertEqual(["noindex, follow"], parser.robots)
                    self.assertEqual([SITE + deployed], parser.canonicals)
                    self.assertEqual([], parser.refreshes)
                    self.assertEqual([], parser.hreflangs)
                    self.assertIn(town_route, parser.links)
                    self.assertIn(valuation_route, parser.links)
                    self.assertIn(f'class="brand" href="{home_route}"', source)
                    self.assertIn(
                        f'class="language" href="{switch_route}"', source
                    )
                    self.assertIn(
                        "https://www.njrealtor.com/research/10k/", parser.links
                    )
                    self.assertIn(
                        "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml",
                        parser.links,
                    )
                    self.assertEqual(1, parser.main_count)
                    self.assertEqual(1, parser.h1_count)
                    self.assertIn('href="#main-content"', source)
                    self.assertIn(item["officialGeography"][language], source)
                    self.assertIn("/css/styles.css", source)
                    self.assertIn("G-KMS6H85LB0", source)
                    self.assertNotIn("application/ld+json", source)
                    for token in PALETTE:
                        self.assertIn(token, source)
                    self.assertIn("'Playfair Display'", source)
                    self.assertIn("Inter", source)
                    self.assertRegex(source, r"min-height:\s*44px")
                    self.assertIn(":focus-visible", source)

    def test_fallback_visible_copy_has_no_unsupported_market_or_steering_claims(self) -> None:
        forbidden = re.compile(
            r"\$\s*\d|\d\s*%|median(?:a|o)?|days? on market|d[ií]as? en el mercado|"
            r"year[- ]over[- ]year|interanual|forecast|pron[oó]stico|appreciat|apreciaci[oó]n|"
            r"school|escuela|family|familia|safe(?:ty)?|seguridad|best|mejor(?:es)?|"
            r"top[- ]rated|perfect|perfect[oa]|\bROI\b|guarantee|garantiz|"
            r"buyer.?s market|seller.?s market|mercado de compradores|mercado de vendedores",
            re.IGNORECASE,
        )
        inventory = load_inventory(MANIFEST_PATH)
        for path in generated_page_paths(inventory, root=ROOT):
            source = path.read_text(encoding="utf-8")
            visible = re.sub(
                r"<script\b.*?</script>|<style\b.*?</style>|<[^>]+>",
                " ",
                source,
                flags=re.IGNORECASE | re.DOTALL,
            )
            visible = html.unescape(" ".join(visible.split()))
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIsNone(forbidden.search(visible), visible)
                self.assertNotRegex(source, r"FAQPage|RealEstateAgent|AggregateRating")

    def test_noindex_and_redirect_sources_are_absent_from_sitemaps(self) -> None:
        english = sitemap_urls("sitemap.xml")
        spanish = sitemap_urls("sitemap-es.xml")
        for slug in EXPECTED_NOINDEX:
            self.assertNotIn(
                f"{SITE}/blog/market-report-{slug}-nj-2026", english
            )
            self.assertNotIn(
                f"{SITE}/es/blog/market-report-{slug}-nj-2026", spanish
            )
        for source in EXPECTED_REDIRECTS:
            submitted = spanish if source.startswith("/es/") else english
            self.assertNotIn(SITE + source, submitted)

    def test_rebuild_pages_remain_indexable_and_submitted(self) -> None:
        english = sitemap_urls("sitemap.xml")
        spanish = sitemap_urls("sitemap-es.xml")
        for stub in EXPECTED_REBUILD:
            for prefix, submitted in (("", english), ("es/", spanish)):
                relative = f"{prefix}blog/{stub}.html"
                source, parser = parsed_page(ROOT / relative)
                deployed = "/" + relative.removesuffix(".html")
                with self.subTest(relative=relative):
                    self.assertNotIn("noindex", " ".join(parser.robots).lower())
                    self.assertEqual([], parser.refreshes)
                    self.assertIn(SITE + deployed, submitted)

    def test_indexable_html_never_links_to_contained_sources(self) -> None:
        forbidden_routes = set(EXPECTED_REDIRECTS)
        forbidden_routes.update(
            f"/blog/market-report-{slug}-nj-2026" for slug in EXPECTED_NOINDEX
        )
        forbidden_routes.update(
            f"/es/blog/market-report-{slug}-nj-2026" for slug in EXPECTED_NOINDEX
        )
        managed = set(generated_page_paths(load_inventory(MANIFEST_PATH), root=ROOT))
        offenders: list[str] = []

        for path in ROOT.rglob("*.html"):
            if path in managed or any(part in SKIP_DIRS for part in path.parts):
                continue
            source, parser = parsed_page(path)
            if "noindex" in " ".join(parser.robots).lower() or parser.refreshes:
                continue
            for href in [*parser.links, *parser.hreflangs]:
                if normalized_path(href, source=path) in forbidden_routes:
                    offenders.append(f"{path.relative_to(ROOT).as_posix()} -> {href}")
        self.assertEqual([], offenders)


class MarketReportGeneratorSafetyTests(unittest.TestCase):
    def test_legacy_generators_are_quarantined_and_cannot_publish_by_default(self) -> None:
        managed = generated_page_paths(load_inventory(MANIFEST_PATH), root=ROOT)
        before = file_hashes(managed)
        for relative in (
            "generate_blog.py",
            "generate_county_reports_and_comparisons.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("market_report_publication_gate", source)
                self.assertNotRegex(
                    source,
                    r"MARKET_TOWNS|COUNTY_TEMPLATE|median_price|yoy_change|"
                    r"market_type|forecast|school_rating",
                )
                result = subprocess.run(
                    [sys.executable, relative],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(2, result.returncode)
                self.assertIn("quarantined", (result.stdout + result.stderr).lower())
        self.assertEqual(before, file_hashes(managed))

    def test_publication_manifest_requires_reviewed_source_provenance(self) -> None:
        with self.assertRaises(ProvenanceError):
            validate_publication_manifest({})
        with self.assertRaises(ProvenanceError):
            validate_publication_manifest(
                {
                    "reviewStatus": "draft",
                    "publicationRights": "unconfirmed",
                    "sources": [],
                    "metrics": [],
                }
            )

        approved = {
            "reviewStatus": "approved",
            "reviewedBy": "Editorial review",
            "reviewedAt": "2026-08-26",
            "publicationRights": "confirmed",
            "sources": [
                {
                    "id": "nj-public-data",
                    "publisher": "New Jersey Division of Taxation",
                    "url": "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml",
                    "accessedAt": "2026-08-26",
                    "geographyType": "municipality",
                    "geographyName": "Example Township",
                    "reportingPeriod": "published source period",
                }
            ],
            "metrics": [
                {
                    "name": "official field label",
                    "value": "source value",
                    "definition": "Meaning copied from the reviewed source notes.",
                    "sourceId": "nj-public-data",
                }
            ],
        }
        self.assertEqual(approved, validate_publication_manifest(approved))

    def test_fallback_generation_check_and_write_are_idempotent(self) -> None:
        paths = generated_page_paths(load_inventory(MANIFEST_PATH), root=ROOT)
        before = file_hashes(paths)
        protected = [
            ROOT / prefix / "blog" / f"{stub}.html"
            for stub in EXPECTED_REBUILD
            for prefix in (Path(), Path("es"))
        ]
        protected_before = file_hashes(protected)
        integrated = integrated_fallback_paths()
        integrated_before = file_hashes(integrated)
        outputs: list[str] = []
        for mode in ("--check", "--check", "--write", "--write"):
            result = subprocess.run(
                [sys.executable, "tools/generate_market_report_containment.py", mode],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            outputs.append(result.stdout)
            self.assertEqual(before, file_hashes(paths))
            self.assertEqual(protected_before, file_hashes(protected))
            self.assertEqual(integrated_before, file_hashes(integrated))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[2], outputs[3])


if __name__ == "__main__":
    unittest.main()
