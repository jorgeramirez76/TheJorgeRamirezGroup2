#!/usr/bin/env python3
"""Contract for evidence-led remediation of the remaining English town pages."""

from __future__ import annotations

import csv
import html
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SITE = "https://thejorgeramirezgroup.com"
MANIFEST_PATH = ROOT / "data" / "indexable-town-risk-decisions.json"
RENDERER_PATH = ROOT / "scripts" / "remediate_indexable_towns.py"

CANDIDATES = {
    "basking-ridge", "bernards-township", "boonton-township", "caldwell", "chatham",
    "dunellen", "edison", "elizabeth", "florham-park", "glen-ridge", "hoboken",
    "jefferson", "jersey-city", "livingston", "long-hill", "madison", "maplewood",
    "metuchen", "middlesex-borough", "millburn", "montclair", "morris-township",
    "morristown", "mountainside", "new-brunswick", "newark", "north-caldwell",
    "nutley", "parsippany-troy-hills", "peapack-gladstone", "perth-amboy", "plainfield",
    "plainsboro", "roselle", "scotch-plains", "short-hills", "south-orange", "summit",
    "union", "washington-township-morris", "weehawken", "west-orange", "westfield", "wharton",
}
REBUILDS = {
    "basking-ridge", "chatham", "hoboken", "jersey-city", "madison", "maplewood",
    "millburn", "montclair", "morristown", "newark", "summit", "westfield",
}
REDIRECTS = {
    "bernards-township": "basking-ridge",
    "short-hills": "millburn",
}
QUARANTINES = CANDIDATES - REBUILDS - set(REDIRECTS)
PROTECTED_PRIORITY = {
    "berkeley-heights", "bloomfield", "chatham-borough", "chatham-township", "cranford",
    "denville", "east-brunswick", "east-hanover", "fanwood", "guttenberg", "morris-plains",
    "new-providence", "roselle-park", "south-brunswick", "springfield", "west-new-york",
}
EXISTING_MANAGED_NOINDEX_COUNT = 74
OFFICIAL_HOST_SUFFIXES = (
    ".gov", ".nj.us", "nj.gov", "census.gov", "njtransit.com", "panynj.gov",
    "bernards.org", "chathamborough.org", "chathamtownship.org", "cityofsummit.org",
    "hobokennj.gov", "jerseycitynj.gov", "maplewoodnj.gov", "montclairnjusa.org",
    "newarknj.gov", "rosenet.org", "townofmorristown.org", "twp.millburn.nj.us",
    "westfieldnj.gov", "bernardsboe.com", "chatham-nj.org",
    "madisonpublicschools.org", "somsdk12.org", "millburn.org",
    "summit.k12.nj.us", "westfieldnjk12.org",
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def noindex(source: str) -> bool:
    return bool(re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*\bnoindex\b', source, re.I))


def redirect_stub(source: str) -> bool:
    return bool(re.search(r'<meta\b[^>]*http-equiv=["\']refresh["\']', source, re.I))


def sitemap_urls(relative: str = "sitemap.xml") -> set[str]:
    root = ET.parse(ROOT / relative).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


def visible_main(source: str) -> str:
    match = re.search(r"<main\b[^>]*>(.*?)</main>", source, re.I | re.S)
    value = match.group(1) if match else ""
    value = re.sub(r"<(?:script|style|template)\b[^>]*>.*?</(?:script|style|template)>", " ", value, flags=re.I | re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


class IndexableTownRiskRemediationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_has_exact_inventory_actions_and_evidence_policy(self) -> None:
        decisions = self.manifest["decisions"]
        self.assertEqual(CANDIDATES, set(decisions))
        self.assertEqual(REBUILDS, {slug for slug, item in decisions.items() if item["action"] == "rebuild"})
        self.assertEqual(REDIRECTS, {
            slug: item["destination"].removeprefix("/towns/")
            for slug, item in decisions.items() if item["action"] == "redirect"
        })
        self.assertEqual(QUARANTINES, {slug for slug, item in decisions.items() if item["action"] == "quarantine"})
        self.assertEqual("2026-08-26", self.manifest["effectiveDate"])
        self.assertEqual(
            "clicks in either comparison period > 0 OR impressions in either comparison period >= 100",
            self.manifest["decisionPolicy"]["measuredDemandRule"],
        )
        self.assertIn("Basking Ridge", self.manifest["decisionPolicy"]["relationshipException"])

        for slug, item in decisions.items():
            with self.subTest(slug=slug):
                self.assertEqual({"current3m", "previous3m", "last16m"}, set(item["gsc"]))
                self.assertIn("internalInboundCount", item["linkEvidence"])
                self.assertEqual(
                    "not available in supplied exports",
                    item["linkEvidence"]["externalBacklinkEvidence"],
                )
                self.assertEqual(["clickmingo.com"], item["linkEvidence"]["legacyExternalHosts"])
                self.assertEqual(0, item["linkEvidence"]["legacyOfficialSourceLinkCount"])

    def test_gsc_snapshot_reproduces_both_periods_and_historical_context(self) -> None:
        from tools.check_indexable_town_risks import fold_gsc_rows

        exports = self.manifest["gscExports"]
        for export_id, fixture in (
            ("comparison", "tests/fixtures/gsc-indexable-town-pages.csv"),
            ("historical", "tests/fixtures/gsc-indexable-town-pages-16m.csv"),
        ):
            with (ROOT / fixture).open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            folded = fold_gsc_rows(rows, CANDIDATES, exports[export_id]["periods"])
            for slug in CANDIDATES:
                for period in exports[export_id]["periods"]:
                    expected = self.manifest["decisions"][slug]["gsc"][period]
                    self.assertEqual(expected, folded[f"/towns/{slug}"][period])

    def test_incoming_clicked_redirect_families_land_outside_town_quarantine(self) -> None:
        expected = {
            "/blog/neighborhoods-maplewood-nj": "/counties/essex-county",
            "/blog/neighborhoods-livingston-nj": "/counties/essex-county",
            "/blog/neighborhoods-montclair-nj": "/counties/essex-county",
            "/blog/neighborhoods-millburn-nj": "/counties/essex-county",
            "/blog/neighborhoods-summit-nj": "/counties/union-county",
            "/blog/neighborhoods-scotch-plains-nj": "/counties/union-county",
            "/blog/neighborhoods-basking-ridge-nj": "/counties/somerset-county",
            "/blog/neighborhoods-madison-nj": "/counties/morris-county",
            "/blog/buying-home-montclair-nj-2026": "/buy-a-home",
            "/blog/buying-home-randolph-nj-2026": "/buy-a-home",
            "/blog/buying-home-jersey-city-nj-2026": "/buy-a-home",
            "/blog/buying-home-rahway-nj-2026": "/buy-a-home",
            "/blog/selling-home-maplewood-nj-2026": "/sell-your-home",
        }
        actual = {item["source"]: item["destination"] for item in self.manifest["incomingRedirectFamilies"]}
        self.assertEqual(expected, actual)
        for destination in actual.values():
            self.assertFalse(destination.startswith("/towns/"))
            local = ROOT / (destination.removeprefix("/") + ".html")
            self.assertTrue(local.exists(), destination)
            self.assertFalse(noindex(local.read_text(encoding="utf-8")), destination)

    def test_layer_aware_linter_checks_visible_metadata_and_jsonld(self) -> None:
        from tools.check_indexable_town_risks import lint_source

        synthetic = '''<!doctype html><html><head>
          <meta name="description" content="A safe community with a guaranteed return">
          <style>.family{color:red}</style><script>const claim = "top schools";</script>
          <script type="application/ld+json">{"description":"Ten minute commute and top schools"}</script>
          </head><body><main><h1>Example</h1><p>Ideal for young professionals.</p></main></body></html>'''
        findings = lint_source(synthetic)
        layers = {(finding["rule"], finding["layer"]) for finding in findings}
        self.assertIn(("protected_or_proxy_targeting", "visible"), layers)
        self.assertIn(("safety_or_crime", "metadata"), layers)
        self.assertIn(("forecast_or_guarantee", "metadata"), layers)
        self.assertIn(("commute_duration", "jsonld"), layers)
        self.assertIn(("school_rank_or_subjective", "jsonld"), layers)
        self.assertNotIn(("protected_or_proxy_targeting", "style_or_script"), layers)

    def test_rebuilt_routes_are_indexable_neutral_source_backed_pages(self) -> None:
        from tools.check_indexable_town_risks import lint_source

        submitted = sitemap_urls()
        failures: list[str] = []
        for slug in sorted(REBUILDS):
            relative = f"towns/{slug}.html"
            source = read(relative)
            decision = self.manifest["decisions"][slug]
            canonical = f"{SITE}/towns/{slug}"
            if noindex(source) or redirect_stub(source):
                failures.append(f"{relative}: not indexable")
            if f'<link rel="canonical" href="{canonical}">' not in source:
                failures.append(f"{relative}: canonical mismatch")
            if canonical not in submitted:
                failures.append(f"{relative}: not submitted")
            if re.search(r'<link\b[^>]*hreflang=', source, re.I):
                failures.append(f"{relative}: stale untranslated hreflang")
            if lint_source(source):
                failures.append(f"{relative}: {lint_source(source)}")
            if 'data-town-evidence-guide="v1"' not in source:
                failures.append(f"{relative}: missing renderer marker")
            hrefs = set(re.findall(r'<a\b[^>]*href=["\']([^"\']+)', source, re.I))
            for source_item in decision["sources"]:
                if source_item["url"] not in hrefs:
                    failures.append(f"{relative}: source not visible: {source_item['url']}")
                host = urlparse(source_item["url"]).netloc.casefold()
                if not any(host == suffix or host.endswith("." + suffix.lstrip(".")) for suffix in OFFICIAL_HOST_SUFFIXES):
                    failures.append(f"{relative}: nonofficial host: {host}")
            blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)
            types = set()
            for block in blocks:
                payload = json.loads(block)
                for node in payload.get("@graph", [payload]):
                    types.add(node.get("@type"))
            if not {"WebPage", "BreadcrumbList"} <= types:
                failures.append(f"{relative}: neutral schema missing")
            if types & {"ItemList", "Review", "AggregateRating", "Rating"}:
                failures.append(f"{relative}: scoring schema present")

        self.assertEqual([], failures)

    def test_quarantines_are_compact_noindex_fallbacks_and_absent_from_hubs(self) -> None:
        submitted = sitemap_urls()
        hub_sources = read("communities.html") + read("communities/index.html")
        failures: list[str] = []
        for slug in sorted(QUARANTINES):
            relative = f"towns/{slug}.html"
            source = read(relative)
            words = len(visible_main(source).split())
            if not noindex(source) or redirect_stub(source):
                failures.append(f"{relative}: not a noindex fallback")
            if 'data-noindex-town-fallback="v1"' not in source:
                failures.append(f"{relative}: marker missing")
            if not 80 <= words <= 220:
                failures.append(f"{relative}: {words} words")
            if re.search(r'application/ld\+json|schema\.org|hreflang=', source, re.I):
                failures.append(f"{relative}: search enhancement remains")
            canonical = f"{SITE}/towns/{slug}"
            if canonical in submitted:
                failures.append(f"{relative}: still in sitemap")
            if re.search(rf'href=["\']/towns/{re.escape(slug)}(?:["\'/])', hub_sources):
                failures.append(f"{relative}: still in hub")
        self.assertEqual([], failures)

    def test_duplicate_geographies_are_one_hop_and_language_consistent(self) -> None:
        config = json.loads(read("vercel.json"))
        redirects = {item["source"]: item["destination"] for item in config["redirects"]}
        sources = set(redirects)
        submitted_en = sitemap_urls("sitemap.xml")
        submitted_es = sitemap_urls("sitemap-es.xml")
        failures: list[str] = []
        for slug, destination_slug in REDIRECTS.items():
            for prefix in ("", "es/"):
                route = f"/{prefix}towns/{slug}"
                destination = f"/{prefix}towns/{destination_slug}"
                source = read(f"{prefix}towns/{slug}.html")
                if redirects.get(route) != destination:
                    failures.append(f"{route}: server redirect mismatch")
                if destination in sources:
                    failures.append(f"{route}: destination is another redirect")
                if destination not in source:
                    failures.append(f"{route}: fallback redirect mismatch")
                submitted = submitted_es if prefix else submitted_en
                if SITE + route in submitted:
                    failures.append(f"{route}: redirect source submitted")

            for legacy_prefix in ("/realtor/", "/communities/"):
                source = f"{legacy_prefix}{slug}{'-nj' if legacy_prefix == '/realtor/' else ''}"
                self.assertEqual(f"/towns/{destination_slug}", redirects[source])
                self.assertNotIn(redirects[source], sources)

    def test_old_managed_fallbacks_and_priority_guides_remain_protected(self) -> None:
        old_policy = json.loads(read("data/english-noindex-town-fallbacks.json"))
        old_slugs = {slug for group in old_policy["groups"] for slug in group["slugs"]}
        self.assertEqual(EXISTING_MANAGED_NOINDEX_COUNT, len(old_slugs))
        self.assertTrue(old_slugs.isdisjoint(CANDIDATES))
        self.assertTrue(PROTECTED_PRIORITY.isdisjoint(CANDIDATES))
        submitted = sitemap_urls()
        for slug in PROTECTED_PRIORITY:
            source = read(f"towns/{slug}.html")
            self.assertFalse(noindex(source), slug)
            self.assertIn(f"{SITE}/towns/{slug}", submitted)

    def test_renderer_is_deterministic_idempotent_and_has_a_drift_check(self) -> None:
        spec = importlib.util.spec_from_file_location("indexable_town_remediation", RENDERER_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader if spec else None)
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            first = renderer.render_pages(root=output_root)
            first_bytes = {
                slug: (output_root / "towns" / f"{slug}.html").read_bytes()
                for slug in CANDIDATES
            }
            second = renderer.render_pages(root=output_root)
            second_bytes = {
                slug: (output_root / "towns" / f"{slug}.html").read_bytes()
                for slug in CANDIDATES
            }
            self.assertEqual(44, len(first))
            self.assertEqual([], second)
            self.assertEqual(first_bytes, second_bytes)
            self.assertEqual([], renderer.check_pages(root=output_root))
            for slug, generated in first_bytes.items():
                self.assertEqual(generated, (ROOT / "towns" / f"{slug}.html").read_bytes())

        result = subprocess.run(
            [sys.executable, str(RENDERER_PATH), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_legacy_generators_cannot_overwrite_managed_routes(self) -> None:
        bulk = read("bulk_update_towns.py")
        photos = read("apply_town_photos.py")
        critical = read("fix_critical_seo.py")
        missing = read("generate_missing_towns.py")
        old_hub = read("build_communities_page.py")

        for source in (bulk, photos, critical):
            self.assertIn("MANAGED_TOWN_RISK_SLUGS", source)
            self.assertIn("managed_slugs", source)
        self.assertIn("remediate_indexable_towns.py", missing)
        self.assertNotRegex(
            missing,
            r"median_price|commute_minutes|schools_rating|top-ranked|default choice",
        )
        self.assertIn("sync_communities_from_facts.py", old_hub)
        self.assertNotRegex(
            old_hub,
            r"COUNTY_BLURBS|school ratings|median prices|commuter family",
        )


if __name__ == "__main__":
    unittest.main()
