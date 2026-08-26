#!/usr/bin/env python3
"""Regression contract for the retired scaled seller/valuation doorways."""

from __future__ import annotations

import copy
import importlib.util
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
MANIFEST = ROOT / "data" / "programmatic-doorway-retirement.json"
GENERATOR = ROOT / "scripts" / "retire_programmatic_doorways.py"
SITE = "https://thejorgeramirezgroup.com"

SELL_SLUGS = {
    "basking-ridge",
    "bloomfield",
    "chatham",
    "clark",
    "cranford",
    "edison",
    "fanwood",
    "florham-park",
    "glen-ridge",
    "highland-park",
    "linden",
    "livingston",
    "madison",
    "maplewood",
    "metuchen",
    "millburn",
    "montclair",
    "morristown",
    "mountain-lakes",
    "mountainside",
    "new-providence",
    "north-caldwell",
    "nutley",
    "old-bridge",
    "parsippany",
    "rahway",
    "roseland",
    "scotch-plains",
    "short-hills",
    "south-orange",
    "springfield",
    "summit",
    "verona",
    "warren-township",
    "west-orange",
    "westfield",
    "woodbridge",
}
VALUATION_SLUGS = {
    "chatham",
    "cranford",
    "livingston",
    "madison",
    "maplewood",
    "millburn",
    "montclair",
    "new-providence",
    "scotch-plains",
    "short-hills",
    "south-orange",
    "springfield",
    "summit",
    "west-orange",
    "westfield",
}
EXPECTED_FILES = {
    *(f"sell-my-house-{slug}-nj.html" for slug in SELL_SLUGS),
    *(f"home-valuation-{slug}-nj.html" for slug in VALUATION_SLUGS),
}
EXPECTED_ROUTES = {"/" + filename.removesuffix(".html") for filename in EXPECTED_FILES}
EXPLICITLY_PROTECTED_TOWNS = {
    "towns/helmetta.html",
    "towns/middlesex.html",
    "towns/orange.html",
    "towns/woodbridge.html",
}
PROTECTED_LINK_SOURCES = {
    "blog/market-report-livingston-nj-2026.html",
    "blog/market-report-maplewood-nj-2026.html",
    "blog/market-report-montclair-nj-2026.html",
    "blog/market-report-short-hills-nj-2026.html",
    "blog/market-report-south-orange-nj-2026.html",
    "blog/market-report-west-orange-nj-2026.html",
    "towns/woodbridge.html",
}
SKIP_DIRS = {".git", "crm", "docs", "node_modules", "property-leads-system"}


class FallbackParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_langs: list[str] = []
        self.viewports: list[str] = []
        self.robots: list[str] = []
        self.refreshes: list[str] = []
        self.canonicals: list[str] = []
        self.links: list[str] = []
        self.main_count = 0
        self.h1_count = 0
        self.fallback_markers: list[str] = []
        self.visible_text: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag in {"script", "style"}:
            self._ignored_depth += 1
        if tag == "html":
            self.html_langs.append(values.get("lang", ""))
        elif tag == "meta" and values.get("name", "").lower() == "viewport":
            self.viewports.append(values.get("content", ""))
        elif tag == "meta" and values.get("name", "").lower() == "robots":
            self.robots.append(values.get("content", ""))
        elif tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            self.refreshes.append(values.get("content", ""))
        elif tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        elif tag == "a":
            self.links.append(values.get("href", ""))
        elif tag == "main":
            self.main_count += 1
            self.fallback_markers.append(
                values.get("data-programmatic-doorway-fallback", "")
            )
        elif tag == "h1":
            self.h1_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth and data.strip():
            self.visible_text.append(data.strip())


def normalized_internal_path(value: str, *, source: Path) -> str | None:
    parsed = urlsplit(value.strip())
    if parsed.scheme and parsed.netloc:
        if parsed.netloc.lower() not in {
            "thejorgeramirezgroup.com",
            "www.thejorgeramirezgroup.com",
        }:
            return None
        path = parsed.path
    elif value.startswith("/"):
        path = parsed.path
    else:
        return None
    path = re.sub(r"\.html$", "", path.rstrip("/"))
    return path or "/"


def load_generator():
    spec = importlib.util.spec_from_file_location("doorway_retirement", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load doorway retirement generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProgrammaticDoorwayRetirementTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.pages = cls.manifest["pages"]
        cls.by_file = {item["file"]: item for item in cls.pages}

    def test_manifest_exactly_covers_the_known_37_plus_15_root_pages(self) -> None:
        self.assertEqual(37, len(SELL_SLUGS))
        self.assertEqual(15, len(VALUATION_SLUGS))
        self.assertEqual(52, len(self.pages))
        self.assertEqual(52, len(self.by_file))
        self.assertEqual(EXPECTED_FILES, set(self.by_file))
        self.assertEqual(EXPECTED_ROUTES, {item["path"] for item in self.pages})
        self.assertEqual(
            EXPECTED_FILES,
            {
                path.name
                for pattern in ("sell-my-house-*-nj.html", "home-valuation-*-nj.html")
                for path in ROOT.glob(pattern)
            },
        )
        self.assertEqual(
            "5abf49e7ee2d35311504e740a2c1bc428736120c",
            self.manifest["inventory_base_commit"],
        )
        self.assertEqual("2026-08-26", self.manifest["retired_on"])
        for filename, item in self.by_file.items():
            with self.subTest(filename=filename):
                if filename.startswith("sell-my-house-"):
                    self.assertEqual("sell_my_house", item["family"])
                    self.assertEqual("/sell-your-home", item["destination"])
                else:
                    self.assertEqual("home_valuation", item["family"])
                    self.assertEqual("/home-valuation", item["destination"])
                self.assertEqual("/" + filename.removesuffix(".html"), item["path"])

    def test_manifest_records_the_observed_gsc_performance_without_invention(self) -> None:
        evidence = self.manifest["gsc_recent_3_months"]
        self.assertEqual("Google Search Console Pages comparison export", evidence["source"])
        self.assertEqual("2026-08-25", evidence["exported_on"])
        self.assertEqual(0, evidence["clicks"])
        self.assertEqual(
            {"observed_url_variants": 1, "impressions": 3},
            evidence["sell_my_house"],
        )
        self.assertEqual(
            {"observed_url_variants": 21, "impressions": 43},
            evidence["home_valuation"],
        )

    def test_both_url_variants_redirect_permanently_and_directly(self) -> None:
        redirects = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))[
            "redirects"
        ]
        sources = [str(item.get("source", "")) for item in redirects]
        source_set = set(sources)
        expected: dict[str, str] = {}
        for item in self.pages:
            expected[item["path"]] = item["destination"]
            expected[item["path"] + ".html"] = item["destination"]
        self.assertEqual(104, len(expected))
        for source, destination in expected.items():
            with self.subTest(source=source):
                matches = [item for item in redirects if item.get("source") == source]
                self.assertEqual(1, len(matches))
                self.assertEqual(destination, matches[0].get("destination"))
                self.assertIs(True, matches[0].get("permanent"))
                self.assertNotIn(destination, source_set, "redirect destination must be one hop")

        for destination in {"/sell-your-home", "/home-valuation"}:
            destination_source = (ROOT / f"{destination.removeprefix('/')}.html").read_text(
                encoding="utf-8"
            )
            self.assertNotRegex(
                destination_source,
                r'<meta\b[^>]*http-equiv=["\']refresh["\']',
            )
            self.assertNotRegex(
                destination_source,
                r'<meta\b[^>]*name=["\']robots["\'][^>]*noindex',
            )

    def test_every_retired_file_is_a_compact_accessible_safe_fallback(self) -> None:
        risky_visible_language = re.compile(
            r"\b2026\b|\bmedian\b|days?\s+on\s+market|\bDOM\b|\bcash\b|"
            r"\bdiscount\b|\b(?:outcome|guarantee|promise)\b|\bschools?\b|"
            r"\bfamil(?:y|ies)\b|\bsold\b|over\s+asking|\$\s*\d|\d+(?:\.\d+)?\s*%",
            re.IGNORECASE,
        )
        forbidden_schema = re.compile(
            r"application/ld\+json|FAQPage|RealEstateAgent|LocalBusiness|"
            r"AggregateRating|Review|priceRange|\"@type\"",
            re.IGNORECASE,
        )
        palette = {
            "#0A0A0A",
            "#1A1A1A",
            "#C41230",
            "#8B0D22",
            "#B8962E",
            "#D4AF5A",
            "#FAFAF8",
        }
        for filename, item in self.by_file.items():
            path = ROOT / filename
            source = path.read_text(encoding="utf-8")
            parser = FallbackParser()
            parser.feed(source)
            destination = item["destination"]
            with self.subTest(filename=filename):
                self.assertLess(len(source.encode("utf-8")), 5000)
                self.assertEqual(["en"], parser.html_langs)
                self.assertEqual(["width=device-width, initial-scale=1"], parser.viewports)
                self.assertEqual(["noindex, follow"], parser.robots)
                self.assertEqual([f"0; url={destination}"], parser.refreshes)
                self.assertEqual([SITE + destination], parser.canonicals)
                self.assertEqual([destination], parser.links)
                self.assertEqual(1, parser.main_count)
                self.assertEqual(1, parser.h1_count)
                self.assertEqual(["v1"], parser.fallback_markers)
                self.assertIn(
                    f"window.location.replace({json.dumps(destination)})", source
                )
                self.assertTrue(palette.issubset(set(re.findall(r"#[0-9A-Fa-f]{6}", source))))
                self.assertIn("'Playfair Display'", source)
                self.assertIn("Inter", source)
                self.assertIn(
                    "https://fonts.googleapis.com/css2?family=Inter", source
                )
                self.assertIn("width:min(680px,calc(100vw - 48px))", source)
                self.assertIsNone(forbidden_schema.search(source))
                self.assertIsNone(risky_visible_language.search(" ".join(parser.visible_text)))

    def test_retired_routes_are_absent_from_every_sitemap(self) -> None:
        offenders: list[str] = []
        for sitemap in ROOT.glob("sitemap*.xml"):
            document = ET.parse(sitemap).getroot()
            for node in document.iter():
                for candidate in [(node.text or "").strip(), *node.attrib.values()]:
                    path = re.sub(r"\.html$", "", urlsplit(candidate).path.rstrip("/"))
                    if path in EXPECTED_ROUTES:
                        offenders.append(f"{sitemap.name}: {candidate}")
        self.assertEqual([], offenders)

    def test_indexable_internal_links_are_rewired_except_protected_sources(self) -> None:
        manifest_exceptions = {
            item["file"] for item in self.manifest["internal_link_exceptions"]
        }
        self.assertEqual(PROTECTED_LINK_SOURCES, manifest_exceptions)
        offenders: list[str] = []
        retired_files = set(self.by_file)
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT)
            relative_name = relative.as_posix()
            if (
                relative_name in retired_files
                or relative_name in manifest_exceptions
                or any(part in SKIP_DIRS for part in relative.parts)
            ):
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', source, re.I):
                continue
            for href in re.findall(r'href\s*=\s*["\']([^"\']+)', source, re.I):
                if normalized_internal_path(href, source=path) in EXPECTED_ROUTES:
                    offenders.append(f"{relative_name} -> {href}")
        self.assertEqual([], offenders)

    def test_generator_is_fail_closed_scoped_and_current(self) -> None:
        generator = load_generator()
        generator.validate_manifest(copy.deepcopy(self.manifest), root=ROOT)
        invalid = copy.deepcopy(self.manifest)
        invalid["pages"].append(
            {
                "family": "sell_my_house",
                "file": "sell-my-house-invented-nj.html",
                "path": "/sell-my-house-invented-nj",
                "destination": "/sell-your-home",
            }
        )
        with self.assertRaises(generator.RetirementContractError):
            generator.validate_manifest(invalid, root=ROOT)

        managed = generator.managed_output_paths(self.manifest)
        self.assertEqual(
            EXPECTED_FILES
            | {"home-valuation.html", "sell-your-home.html", "sitemap.xml", "vercel.json"},
            managed,
        )
        self.assertTrue(managed.isdisjoint(EXPLICITLY_PROTECTED_TOWNS))
        self.assertFalse(
            any(
                path.startswith("blog/market-report-")
                or "buyer-guide" in path
                or "buyer-nj-programs" in path
                for path in managed
            )
        )

        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn(
            "programmatic doorway retirement current: 52 fallbacks, 104 redirects",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
