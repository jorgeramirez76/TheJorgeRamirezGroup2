#!/usr/bin/env python3
"""Fail-closed contract for retired AI Sales Pipeline feature routes."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "ai-sales-pipeline-route-migration.json"
SYNC = ROOT / "tools" / "sync_ai_sales_pipeline_routes.py"
PRODUCT_HOST = "aisalespipeline.com"
EXPECTED_ENGLISH_BY_FAMILY = {
    "ai-clone-video": "https://aisalespipeline.com/features/ai-clone-video-real-estate.html",
    "ai-email": "https://aisalespipeline.com/features/ai-email-real-estate.html",
    "ai-sms": "https://aisalespipeline.com/features/ai-sms-real-estate.html",
    "ai-voice": "https://aisalespipeline.com/features/ai-voice-calls-real-estate.html",
    "buyer-workflows": "https://aisalespipeline.com/features/buyer-workflows-real-estate.html",
    "custom-ai-brain": "https://aisalespipeline.com/features/custom-ai-brain-real-estate.html",
    "facebook-retargeting": "https://aisalespipeline.com/features/facebook-retargeting-real-estate.html",
    "lead-scoring": "https://aisalespipeline.com/features/lead-scoring-real-estate.html",
    "seller-workflows": "https://aisalespipeline.com/features/seller-workflows-real-estate.html",
}
EXPECTED_ENGLISH_DESTINATIONS = set(EXPECTED_ENGLISH_BY_FAMILY.values())


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def base_routes(manifest: dict) -> dict[str, str]:
    routes: dict[str, str] = {}
    for family in manifest["families"]:
        for alias in family["aliases"]:
            for language in ("en", "es"):
                source = manifest["routePrefixByLanguage"][language] + alias
                routes[source] = family["destinationByLanguage"][language]
    return routes


class AiSalesPipelineRouteMigrationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest()
        cls.routes = base_routes(cls.manifest)
        cls.legacy_addresses = {
            address
            for clean in cls.routes
            for address in (clean, clean + ".html")
        }

    def test_manifest_exactly_describes_the_reviewed_asset(self) -> None:
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertEqual("2026-08-26", self.manifest["reviewedOn"])
        self.assertEqual("tools/sync_ai_sales_pipeline_routes.py", self.manifest["routeSync"])
        self.assertEqual(9, len(self.manifest["families"]))
        self.assertEqual(36, len(self.routes))
        self.assertEqual(72, len(self.legacy_addresses))
        self.assertEqual(10, len(set(self.routes.values())))
        evidence = self.manifest["gscEvidence"]
        self.assertEqual(
            {"last16Months", "last3Months", "googleGenerativeAiLast3Months"},
            set(evidence),
        )
        for window, snapshot in evidence.items():
            with self.subTest(gsc_window=window):
                self.assertNotIn("export", snapshot)
                self.assertIn("Google Search Console", snapshot["provenance"])
                self.assertIn("outside this release repository", snapshot["provenance"])
                self.assertIn("not committed", snapshot["provenance"])
        semantics = self.manifest["vercelRoutingSemantics"]
        self.assertIs(True, semantics["cleanUrls"])
        self.assertEqual(36, semantics["cleanRouteRedirects"])
        self.assertEqual(72, semantics["legacyAddressVariantsCovered"])
        self.assertEqual(1, semantics["cleanAddressHops"])
        self.assertEqual(2, semantics["htmlAddressHops"])
        buyer_routes = {route for route in self.routes if "buyer-workflows" in route}
        self.assertEqual(4, len(buyer_routes))
        self.assertEqual(
            EXPECTED_ENGLISH_BY_FAMILY,
            {
                family["id"]: family["destinationByLanguage"]["en"]
                for family in self.manifest["families"]
            },
        )
        for route, destination in self.routes.items():
            with self.subTest(route=route):
                self.assertRegex(route, r"^/(?:es/)?features/[a-z0-9-]+$")
                parsed = urlsplit(destination)
                self.assertEqual("https", parsed.scheme)
                self.assertEqual(PRODUCT_HOST, parsed.netloc)
                if route.startswith("/es/"):
                    self.assertEqual("/es/", parsed.path)
                else:
                    self.assertRegex(parsed.path, r"^/features/[a-z0-9-]+-real-estate\.html$")
                    self.assertIn(destination, EXPECTED_ENGLISH_DESTINATIONS)

    def test_route_sync_is_deterministic(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SYNC), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_clean_routes_redirect_permanently_and_html_uses_clean_url_normalization(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertIs(True, config.get("cleanUrls"))
        self.assertIs(False, config.get("trailingSlash"))
        redirects = config["redirects"]
        feature_rules = [
            rule
            for rule in redirects
            if re.fullmatch(r"/(?:es/)?features/[^/:*()]+(?:\.html)?", str(rule.get("source", "")))
        ]
        by_source: dict[str, list[dict]] = {}
        for rule in feature_rules:
            by_source.setdefault(str(rule["source"]), []).append(rule)
        self.assertEqual(set(self.routes), set(by_source))
        self.assertFalse(any(source.endswith(".html") for source in by_source))
        all_redirect_sources = {str(rule.get("source", "")) for rule in redirects}
        for source, destination in self.routes.items():
            with self.subTest(source=source):
                self.assertEqual(1, len(by_source[source]))
                rule = by_source[source][0]
                self.assertEqual(destination, rule.get("destination"))
                self.assertIs(True, rule.get("permanent"))
                self.assertNotIn("statusCode", rule)
                self.assertNotIn("has", rule)
                self.assertEqual(PRODUCT_HOST, urlsplit(destination).netloc)
                self.assertNotIn(destination, all_redirect_sources)

        feature_indexes = [
            index
            for index, rule in enumerate(redirects)
            if str(rule.get("source", "")) in self.routes
        ]
        pattern_indexes = [
            index
            for index, rule in enumerate(redirects)
            if index >= 2
            and (
                any(mark in str(rule.get("source", "")) for mark in (":", "*", "("))
                or rule.get("has")
            )
        ]
        self.assertLess(max(feature_indexes), min(pattern_indexes))

        declared_route_rules = sum(
            len(config.get(key, [])) for key in ("redirects", "rewrites", "headers")
        )
        self.assertLess(declared_route_rules, 2048)

        external_html_rules = {
            str(rule["source"]): str(rule["destination"])
            for rule in redirects
            if urlsplit(str(rule.get("destination", ""))).netloc
            and urlsplit(str(rule.get("destination", ""))).path.endswith(".html")
        }
        expected_external_html = {
            source: destination
            for source, destination in self.routes.items()
            if destination.endswith(".html")
        }
        self.assertEqual(expected_external_html, external_html_rules)

    def test_destinations_match_the_verified_product_domain_inventory(self) -> None:
        verification = self.manifest["liveProductionReview"]["verifiedProductDestinations"]
        self.assertEqual(9, verification["englishExactPages"])
        self.assertEqual(200, verification["englishHttpStatus"])
        self.assertEqual(9, verification["spanishExactPagesTested"])
        self.assertEqual(404, verification["spanishExactHttpStatus"])
        self.assertEqual("https://aisalespipeline.com/es/", verification["spanishFallback"])
        self.assertEqual(200, verification["spanishFallbackHttpStatus"])
        english = {
            destination
            for source, destination in self.routes.items()
            if not source.startswith("/es/")
        }
        spanish = {
            destination
            for source, destination in self.routes.items()
            if source.startswith("/es/")
        }
        self.assertEqual(EXPECTED_ENGLISH_DESTINATIONS, english)
        self.assertEqual({"https://aisalespipeline.com/es/"}, spanish)

    def test_feature_pages_stay_deleted_and_out_of_search_inventory(self) -> None:
        self.assertFalse((ROOT / "features").exists())
        self.assertFalse((ROOT / "es" / "features").exists())
        for filename in ("sitemap.xml", "sitemap-es.xml"):
            with self.subTest(filename=filename):
                self.assertNotIn("/features/", (ROOT / filename).read_text(encoding="utf-8"))

    def test_public_html_bypasses_retired_feature_routes(self) -> None:
        offenders: list[tuple[str, str]] = []
        href = re.compile(r'\bhref\s*=\s*["\']([^"\']+)', re.I)
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith((".git/", "node_modules/")):
                continue
            for raw in href.findall(path.read_text(encoding="utf-8", errors="ignore")):
                route = urlsplit(raw).path
                if route.startswith("/features/") or route.startswith("/es/features/"):
                    offenders.append((relative, route))
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main(verbosity=2)
