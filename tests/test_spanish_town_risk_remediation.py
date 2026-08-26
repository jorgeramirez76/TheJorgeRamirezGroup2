#!/usr/bin/env python3
"""Regression contract for the Spanish town-guide remediation."""

from __future__ import annotations

import csv
import html
import importlib.util
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SITE = "https://thejorgeramirezgroup.com"
MANIFEST_PATH = ROOT / "data" / "spanish-town-risk-decisions.json"
RENDERER_PATH = ROOT / "scripts" / "remediate_spanish_towns.py"

REDIRECTS = {
    "bernards-township": "basking-ridge",
    "short-hills": "millburn",
}
OFFICIAL_HOST_SUFFIXES = (
    ".gov",
    ".nj.us",
    "nj.gov",
    "census.gov",
    "njtransit.com",
    "panynj.gov",
    "bernards.org",
    "bernardsboe.com",
    "bhpsnj.org",
    "bloomfield.k12.nj.us",
    "bloomfieldtwpnj.com",
    "chatham-nj.org",
    "chathamborough.org",
    "chathamtownship.org",
    "cityofsummit.org",
    "cranfordnj.org",
    "cranfordschools.org",
    "denville.org",
    "denvillenj.gov",
    "easthanoverschools.org",
    "easthanovertownship.com",
    "eastbrunswick.org",
    "ebnet.org",
    "fanwoodnj.org",
    "guttenbergnj.org",
    "helmettaboro.com",
    "hobokennj.gov",
    "jerseycitynj.gov",
    "madisonpublicschools.org",
    "maplewoodnj.gov",
    "middlesexboro-nj.gov",
    "millburn.org",
    "montclairnjusa.org",
    "morrisplainsboro.org",
    "morrisschooldistrict.org",
    "newarknj.gov",
    "newprov.us",
    "npsd.k12.nj.us",
    "orangenj.gov",
    "rosellepark.net",
    "rosenet.org",
    "rpsd.org",
    "sbschools.org",
    "somsdk12.org",
    "southbrunswicknj.gov",
    "spfk12.org",
    "springfield-nj.us",
    "springfieldschools.com",
    "summit.k12.nj.us",
    "twp.millburn.nj.us",
    "twp.woodbridge.nj.us",
    "townofmorristown.org",
    "westfieldnj.gov",
    "westfieldnjk12.org",
    "westnewyorknj.org",
    "wnyschools.net",
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def noindex(source: str) -> bool:
    return bool(
        re.search(
            r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex',
            source,
            re.I,
        )
    )


def sitemap_urls(relative: str) -> set[str]:
    root = ET.parse(ROOT / relative).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


def visible_main(source: str) -> str:
    match = re.search(r"<main\b[^>]*>(.*?)</main>", source, re.I | re.S)
    value = match.group(1) if match else ""
    value = re.sub(
        r"<(?:script|style|template)\b[^>]*>.*?</(?:script|style|template)>",
        " ",
        value,
        flags=re.I | re.S,
    )
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def schema_types(source: str) -> set[str]:
    found: set[str] = set()
    for block in re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source,
        re.I | re.S,
    ):
        payload = json.loads(html.unescape(block))
        nodes = payload.get("@graph", [payload]) if isinstance(payload, dict) else payload
        for node in nodes:
            value = node.get("@type") if isinstance(node, dict) else None
            if isinstance(value, str):
                found.add(value)
            elif isinstance(value, list):
                found.update(item for item in value if isinstance(item, str))
    return found


class SpanishTownRiskRemediationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.decisions = cls.manifest["decisions"]

    def test_manifest_is_exact_complete_and_reproducible(self) -> None:
        all_files = {path.stem for path in (ROOT / "es" / "towns").glob("*.html")}
        self.assertEqual(138, len(all_files))
        self.assertEqual(all_files, set(self.decisions))

        site_facts = json.loads(read("data/site-facts.json"))
        canonical = {
            slug
            for slugs in site_facts["canonicalTownInventory"]["byCounty"].values()
            for slug in slugs
        }
        rebuilt = {slug for slug, item in self.decisions.items() if item["action"] == "rebuild"}
        quarantined = {slug for slug, item in self.decisions.items() if item["action"] == "quarantine"}
        redirected = {
            slug: item["destination"].removeprefix("/es/towns/")
            for slug, item in self.decisions.items()
            if item["action"] == "redirect"
        }
        self.assertEqual(32, len(canonical))
        self.assertEqual(canonical, rebuilt)
        self.assertEqual(104, len(quarantined))
        self.assertEqual(REDIRECTS, redirected)
        self.assertEqual(138, len(rebuilt | quarantined | set(redirected)))
        self.assertEqual("2026-08-26", self.manifest["effectiveDate"])
        self.assertIn("current canonical English inventory", self.manifest["decisionPolicy"]["rebuildRule"])
        self.assertIn("no gated", self.manifest["evidencePolicy"])

        spec = importlib.util.spec_from_file_location("spanish_town_renderer", RENDERER_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertEqual(self.manifest, module.build_manifest())

    def test_gsc_fixture_folds_all_url_variants_and_preserves_demand_context(self) -> None:
        from scripts.remediate_spanish_towns import fold_gsc_rows

        fixtures = (
            (
                "tests/fixtures/gsc-spanish-town-pages.csv",
                self.manifest["gscExports"]["comparison"]["periods"],
            ),
            (
                "tests/fixtures/gsc-spanish-town-pages-16m.csv",
                self.manifest["gscExports"]["historical"]["periods"],
            ),
        )
        for fixture, periods in fixtures:
            with (ROOT / fixture).open(encoding="utf-8-sig", newline="") as handle:
                folded = fold_gsc_rows(csv.DictReader(handle), set(self.decisions), periods)
            for slug, item in self.decisions.items():
                for period in periods:
                    self.assertEqual(item["gsc"][period], folded[slug][period])

        self.assertGreater(self.decisions["chatham"]["gsc"]["previous3m"]["clicks"], 0)
        self.assertEqual("rebuild", self.decisions["chatham"]["action"])
        self.assertGreater(self.decisions["kinnelon"]["gsc"]["last16m"]["clicks"], 0)
        self.assertEqual("quarantine", self.decisions["kinnelon"]["action"])
        self.assertIn("no longer part of the canonical town inventory", self.decisions["kinnelon"]["reason"])

    def test_rebuilt_pages_are_indexable_spanish_source_backed_guides(self) -> None:
        from tools.check_spanish_town_risks import lint_source

        sitemap = sitemap_urls("sitemap-es.xml")
        failures: list[str] = []
        for slug, item in sorted(self.decisions.items()):
            if item["action"] != "rebuild":
                continue
            relative = f"es/towns/{slug}.html"
            source = read(relative)
            canonical = f"{SITE}/es/towns/{slug}"
            if noindex(source) or re.search(r'http-equiv=["\']refresh', source, re.I):
                failures.append(f"{relative}: not indexable")
            if f'<link rel="canonical" href="{canonical}">' not in source:
                failures.append(f"{relative}: canonical mismatch")
            if canonical not in sitemap:
                failures.append(f"{relative}: absent from Spanish sitemap")
            if 'lang="es-US"' not in source or 'data-spanish-town-guide="v1"' not in source:
                failures.append(f"{relative}: renderer/language marker missing")
            if lint_source(source):
                failures.append(f"{relative}: {lint_source(source)}")
            if len(visible_main(source).split()) < 430:
                failures.append(f"{relative}: thin visible content")
            if not {"WebPage", "BreadcrumbList"} <= schema_types(source):
                failures.append(f"{relative}: neutral schema missing")
            if schema_types(source) & {"FAQPage", "Review", "AggregateRating", "Product", "Offer"}:
                failures.append(f"{relative}: unsupported schema")
            hrefs = set(re.findall(r'<a\b[^>]*href=["\']([^"\']+)', source, re.I))
            if len(item["sources"]) < 4:
                failures.append(f"{relative}: too few primary sources")
            for evidence in item["sources"]:
                if evidence["url"] not in hrefs:
                    failures.append(f"{relative}: source not visible: {evidence['url']}")
                host = urlparse(evidence["url"]).netloc.casefold()
                if not any(host == suffix or host.endswith("." + suffix.lstrip(".")) for suffix in OFFICIAL_HOST_SUFFIXES):
                    failures.append(f"{relative}: nonofficial source: {host}")
        self.assertEqual([], failures)

    def test_quarantined_routes_are_compact_safe_fallbacks(self) -> None:
        from tools.check_spanish_town_risks import lint_source

        sitemap = sitemap_urls("sitemap-es.xml")
        failures: list[str] = []
        for slug, item in sorted(self.decisions.items()):
            if item["action"] != "quarantine":
                continue
            relative = f"es/towns/{slug}.html"
            source = read(relative)
            canonical = f"{SITE}/es/towns/{slug}"
            if not noindex(source) or "follow" not in source:
                failures.append(f"{relative}: noindex/follow missing")
            if f'<link rel="canonical" href="{canonical}">' not in source:
                failures.append(f"{relative}: canonical mismatch")
            if canonical in sitemap:
                failures.append(f"{relative}: remains submitted")
            if 'data-spanish-town-fallback="v1"' not in source:
                failures.append(f"{relative}: fallback marker missing")
            if re.search(r'<link\b[^>]*hreflang=|http-equiv=["\']refresh|application/ld\+json', source, re.I):
                failures.append(f"{relative}: stale alternate, redirect, or schema")
            if "G-KMS6H85LB0" not in source or "twitter:card" not in source or "og:title" not in source:
                failures.append(f"{relative}: metadata/analytics incomplete")
            if lint_source(source):
                failures.append(f"{relative}: {lint_source(source)}")
        self.assertEqual([], failures)

    def test_redirects_are_one_hop_noindex_aliases(self) -> None:
        sitemap = sitemap_urls("sitemap-es.xml")
        failures: list[str] = []
        for slug, target in REDIRECTS.items():
            source = read(f"es/towns/{slug}.html")
            destination = f"/es/towns/{target}"
            if not noindex(source) or destination not in source:
                failures.append(f"{slug}: redirect fallback mismatch")
            if "data-spanish-town-redirect=\"v1\"" not in source:
                failures.append(f"{slug}: redirect marker missing")
            if "application/ld+json" in source or "hreflang=" in source:
                failures.append(f"{slug}: redirect has schema/hreflang")
            if f"{SITE}/es/towns/{slug}" in sitemap:
                failures.append(f"{slug}: redirect submitted")
            target_source = read(f"es/towns/{target}.html")
            if noindex(target_source) or re.search(r'http-equiv=["\']refresh', target_source, re.I):
                failures.append(f"{slug}: destination is not one-hop indexable")
        self.assertEqual([], failures)

    def test_hreflang_is_reciprocal_and_sitemap_inventory_is_exact(self) -> None:
        expected = {
            f"{SITE}/es/towns/{slug}"
            for slug, item in self.decisions.items()
            if item["action"] == "rebuild"
        }
        submitted = {url for url in sitemap_urls("sitemap-es.xml") if "/es/towns/" in url}
        self.assertEqual(expected, submitted)

        failures: list[str] = []
        for slug, item in self.decisions.items():
            spanish = read(f"es/towns/{slug}.html")
            if item["action"] != "rebuild":
                if "hreflang=" in spanish:
                    failures.append(f"{slug}: nonindex route has hreflang")
                continue
            english = read(f"towns/{slug}.html")
            reciprocal = f'hreflang="es-US" href="{SITE}/es/towns/{slug}"' in english
            if reciprocal:
                required = (
                    f'hreflang="en-US" href="{SITE}/towns/{slug}"',
                    f'hreflang="es-US" href="{SITE}/es/towns/{slug}"',
                    f'hreflang="x-default" href="{SITE}/towns/{slug}"',
                )
                if not all(value in spanish for value in required):
                    failures.append(f"{slug}: reciprocal alternates incomplete")
            elif "hreflang=" in spanish:
                failures.append(f"{slug}: unilateral alternate")
        self.assertEqual([], failures)

    def test_design_accessibility_and_generator_fences(self) -> None:
        for relative in ("css/town-evidence-guide.css", "css/town-fallback.css"):
            source = read(relative)
            for token in ("#0A0A0A", "#C41230", "#8B0D22", "#B8962E", "#D4AF5A", "#F8F6F2", "Playfair Display", "Inter", "min-height: 44px", ":focus-visible"):
                with self.subTest(file=relative, token=token):
                    self.assertIn(token, source)

        failures: list[str] = []
        for slug in self.decisions:
            source = read(f"es/towns/{slug}.html")
            if len(re.findall(r"<h1\b", source, re.I)) != 1:
                failures.append(f"{slug}: not exactly one H1")
            ids = re.findall(r'\bid=["\']([^"\']+)', source, re.I)
            if len(ids) != len(set(ids)):
                failures.append(f"{slug}: duplicate IDs")
            if 'href="#main"' not in source or 'id="main"' not in source:
                failures.append(f"{slug}: skip target mismatch")
            if re.search(r'class=["\'][^"\']*["\']\s+class=', source, re.I):
                failures.append(f"{slug}: duplicate class attribute")
            if "Auto-translated" in source:
                failures.append(f"{slug}: machine-translation marker remains")
        self.assertEqual([], failures)

        for relative in (
            "apply_town_photos.py",
            "fix_critical_seo.py",
            "fix_spanish_translations.py",
            "scripts/apply_spanish_snippets.py",
            "translate_to_spanish.py",
        ):
            with self.subTest(generator=relative):
                self.assertIn("spanish_managed_slugs", read(relative))

        self.assertIn(
            "spanish-town-fallback",
            read("tools/check_technical_seo.py"),
            "technical SEO must recognize the managed Spanish noindex marker",
        )

    def test_renderer_and_contextual_linter_cli_are_clean(self) -> None:
        commands = (
            [sys.executable, str(RENDERER_PATH), "--check"],
            [sys.executable, str(ROOT / "tools" / "check_spanish_town_risks.py")],
        )
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
