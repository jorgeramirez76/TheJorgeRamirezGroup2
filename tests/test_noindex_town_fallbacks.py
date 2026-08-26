#!/usr/bin/env python3
"""Regression contract for compact English noindex town fallbacks."""

from __future__ import annotations

import html
import importlib.util
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SITE = "https://thejorgeramirezgroup.com"
POLICY_PATH = ROOT / "data" / "english-noindex-town-fallbacks.json"
RENDERER_PATH = ROOT / "scripts" / "render_noindex_town_fallbacks.py"

STRICT_DUPLICATE_SLUGS = {
    "bayonne",
    "boonton",
    "butler",
    "carteret",
    "chester-borough",
    "chester-township",
    "clark",
    "dover",
    "east-newark",
    "garwood",
    "hanover",
    "harding",
    "harrison",
    "highland-park",
    "hillside",
    "jamesburg",
    "kearny",
    "kenilworth",
    "kinnelon",
    "lincoln-park",
    "linden",
    "mendham-borough",
    "mendham-township",
    "milltown",
    "mine-hill",
    "monroe-township",
    "mount-arlington",
    "mount-olive",
    "mountain-lakes",
    "netcong",
    "north-bergen",
    "north-brunswick",
    "old-bridge",
    "piscataway",
    "rahway",
    "randolph",
    "riverdale",
    "rockaway-borough",
    "rockaway-township",
    "roxbury",
    "sayreville",
    "secaucus",
    "south-amboy",
    "south-plainfield",
    "spotswood",
    "union-city",
    "verona",
    "victory-gardens",
}

WRONG_TOWN_SOMERSET_SLUGS = {
    "bedminster",
    "bernardsville",
    "bound-brook",
    "branchburg",
    "bridgewater",
    "far-hills",
    "franklin-township",
    "green-brook",
    "hillsborough",
    "manville",
    "millstone",
    "montgomery",
    "north-plainfield",
    "raritan",
    "rocky-hill",
    "somerville",
    "south-bound-brook",
}

HIGH_RISK_LONG_FORM_SLUGS = {
    "cranbury",
    "montville",
    "pequannock-township",
    "roseland",
    "south-river",
    "warren-township",
    "watchung",
    "west-caldwell",
    "winfield",
}

PROTECTED_PRIORITY_SLUGS = {
    "berkeley-heights",
    "bloomfield",
    "chatham-borough",
    "chatham-township",
    "cranford",
    "denville",
    "east-brunswick",
    "east-hanover",
    "fanwood",
    "guttenberg",
    "morris-plains",
    "new-providence",
    "roselle-park",
    "south-brunswick",
    "springfield",
    "west-new-york",
}

EXPECTED_SLUGS = (
    STRICT_DUPLICATE_SLUGS
    | WRONG_TOWN_SOMERSET_SLUGS
    | HIGH_RISK_LONG_FORM_SLUGS
)

RISKY_COPY = re.compile(
    r"(?:"
    r"\b(?:best|strongest|top[- ]rated|top dollar|rank(?:ed|ing|ings)?|family|families|family-friendly)\b|"
    r"\b(?:school|schools|school district|safe|safety|crime rate)\b|"
    r"\b(?:median|average sale|inventory|days on market|commute time)\b|"
    r"\b(?:appreciation|return on investment|roi|guarantee[ds]?)\b|"
    r"\b(?:young professionals|empty nesters|retirees)\b|"
    r"\$\s*\d|\b\d+(?:\.\d+)?\s*%"
    r")",
    re.IGNORECASE,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def robots_noindex(source: str) -> bool:
    tags = re.findall(
        r'<meta\b[^>]*\bname=["\']robots["\'][^>]*>', source, re.IGNORECASE
    )
    return any(re.search(r'\bcontent=["\'][^"\']*\bnoindex\b', tag, re.I) for tag in tags)


def visible_main_text(source: str) -> str:
    match = re.search(r"<main\b[^>]*>(.*?)</main>", source, re.I | re.S)
    body = match.group(1) if match else ""
    body = re.sub(r"<(?:script|style|template)\b[^>]*>.*?</(?:script|style|template)>", " ", body, flags=re.I | re.S)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", html.unescape(body)).strip()


def sitemap_urls() -> set[str]:
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


class NoindexTownFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        cls.groups = {group["id"]: set(group["slugs"]) for group in cls.policy["groups"]}

    def test_policy_enumerates_the_exact_current_english_noindex_inventory(self) -> None:
        actual = {
            path.stem
            for path in (ROOT / "towns").glob("*.html")
            if robots_noindex(path.read_text(encoding="utf-8", errors="replace"))
        }

        self.assertEqual(74, len(EXPECTED_SLUGS))
        self.assertEqual(EXPECTED_SLUGS, actual)
        self.assertEqual(STRICT_DUPLICATE_SLUGS, self.groups["strict-near-duplicate-template"])
        self.assertEqual(WRONG_TOWN_SOMERSET_SLUGS, self.groups["wrong-town-somerset-clones"])
        self.assertEqual(HIGH_RISK_LONG_FORM_SLUGS, self.groups["scaled-long-form-template"])
        self.assertEqual(
            PROTECTED_PRIORITY_SLUGS,
            set(self.policy["protectedSourceBackedPrioritySlugs"]),
        )
        self.assertTrue(EXPECTED_SLUGS.isdisjoint(PROTECTED_PRIORITY_SLUGS))

    def test_every_route_is_a_compact_accessible_fallback(self) -> None:
        failures: list[str] = []
        for slug in sorted(EXPECTED_SLUGS):
            relative = f"towns/{slug}.html"
            source = read(relative)
            text = visible_main_text(source)
            headings = [int(level) for level in re.findall(r"<h([1-6])\b", source, re.I)]
            ids = re.findall(r'\bid=["\']([^"\']+)', source, re.I)

            if not source.lstrip().lower().startswith("<!doctype html>"):
                failures.append(f"{relative}: missing doctype")
            if not re.search(r'<html\b[^>]*\blang=["\']en["\']', source, re.I):
                failures.append(f"{relative}: missing English language declaration")
            if not re.search(r'<body\b[^>]*\bdata-noindex-town-fallback=["\']v1["\']', source, re.I):
                failures.append(f"{relative}: missing fallback marker")
            if not re.search(r'<a\b[^>]*href=["\']#main["\'][^>]*class=["\'][^"\']*skip-link', source, re.I):
                failures.append(f"{relative}: missing skip link")
            if not re.search(r'<nav\b[^>]*aria-label=["\']Primary["\']', source, re.I):
                failures.append(f"{relative}: missing labeled primary navigation")
            if not re.search(r'<main\b[^>]*id=["\']main["\'][^>]*tabindex=["\']-1["\']', source, re.I):
                failures.append(f"{relative}: missing focusable main landmark")
            if headings != [1, 2]:
                failures.append(f"{relative}: expected h1/h2 hierarchy, got {headings}")
            if len(ids) != len(set(ids)):
                failures.append(f"{relative}: duplicate IDs")
            if not 80 <= len(text.split()) <= 220:
                failures.append(f"{relative}: fallback has {len(text.split())} visible main words")
            if len(source.encode("utf-8")) > 16_000:
                failures.append(f"{relative}: fallback is not compact")

        self.assertEqual([], failures)

    def test_search_signals_and_destination_links_are_safe_and_specific(self) -> None:
        from town_data import COUNTY

        submitted = sitemap_urls()
        county_guides = self.policy["countyGuides"]
        failures: list[str] = []

        for slug in sorted(EXPECTED_SLUGS):
            relative = f"towns/{slug}.html"
            source = read(relative)
            canonical = f"{SITE}/towns/{slug}"
            county = COUNTY[slug]
            county_href = county_guides[county]["href"]

            if not re.search(
                r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\']noindex, follow["\']',
                source,
                re.I,
            ):
                failures.append(f"{relative}: robots must be exactly noindex, follow")
            if f'<link rel="canonical" href="{canonical}">' not in source:
                failures.append(f"{relative}: missing self-canonical")
            if canonical in submitted or f"{canonical}.html" in submitted:
                failures.append(f"{relative}: submitted in sitemap")
            if re.search(r'<link\b[^>]*hreflang=', source, re.I):
                failures.append(f"{relative}: noindex fallback publishes hreflang")
            if not re.search(rf'href=["\']{re.escape(county_href)}["\']', source):
                failures.append(f"{relative}: missing {county} County guide link")
            if not re.search(r'href=["\']/contact["\']', source):
                failures.append(f"{relative}: missing contact path")
            county_file = ROOT / f"{county_href.removeprefix('/')}.html"
            if not county_file.exists():
                failures.append(f"{relative}: county destination does not exist")

        self.assertEqual([], failures)

    def test_fallbacks_publish_no_rich_results_or_risky_local_claims(self) -> None:
        failures: list[str] = []
        for slug in sorted(EXPECTED_SLUGS):
            relative = f"towns/{slug}.html"
            source = read(relative)
            text = visible_main_text(source)
            matched = RISKY_COPY.search(text)

            if re.search(r"application/ld\+json|schema\.org|itemscope|itemtype=", source, re.I):
                failures.append(f"{relative}: rich-result schema remains")
            if re.search(r'<meta\b[^>]*name=["\'](?:keywords|llm-context)["\']', source, re.I):
                failures.append(f"{relative}: scaled-search metadata remains")
            if matched:
                failures.append(f"{relative}: risky copy remains ({matched.group(0)!r})")
            if re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", source, re.I):
                failures.append(f"{relative}: hidden doorway copy marker")

        self.assertEqual([], failures)

    def test_pages_use_the_homepage_palette_type_and_interaction_contract(self) -> None:
        css = read("css/town-fallback.css")
        for token in (
            "--primary-red: #C41230",
            "--dark-red: #8B0D22",
            "--gold: #B8962E",
            "--gold-light: #D4AF5A",
            "--dark-bg: #0A0A0A",
            "--ivory: #F8F6F2",
            "--font-display: 'Playfair Display'",
            "--font-body: 'Inter'",
            "min-height: 44px",
            ":focus-visible",
            "background: linear-gradient(135deg, var(--primary-red), var(--dark-red)) !important;",
        ):
            self.assertIn(token, css)

        for slug in sorted(EXPECTED_SLUGS):
            source = read(f"towns/{slug}.html")
            self.assertIn('<link rel="stylesheet" href="/css/styles.css">', source)
            self.assertIn('<link rel="stylesheet" href="/css/town-fallback.css">', source)
            self.assertNotRegex(source, r'<(?:main|section|article|a)\b[^>]*\bstyle=')

    def test_protected_source_backed_priority_guides_remain_indexable_and_submitted(self) -> None:
        submitted = sitemap_urls()
        failures: list[str] = []
        for slug in sorted(PROTECTED_PRIORITY_SLUGS):
            source = read(f"towns/{slug}.html")
            if robots_noindex(source):
                failures.append(f"towns/{slug}.html: unexpectedly noindex")
            if f"{SITE}/towns/{slug}" not in submitted:
                failures.append(f"towns/{slug}.html: missing from sitemap")
        self.assertEqual([], failures)

    def test_renderer_is_deterministic_idempotent_and_matches_committed_pages(self) -> None:
        spec = importlib.util.spec_from_file_location("town_fallback_renderer", RENDERER_PATH)
        if spec is None or spec.loader is None:
            self.fail("unable to load fallback renderer")
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            first = renderer.render_fallbacks(root=output_root)
            first_bytes = {
                slug: (output_root / "towns" / f"{slug}.html").read_bytes()
                for slug in sorted(EXPECTED_SLUGS)
            }
            second = renderer.render_fallbacks(root=output_root)
            second_bytes = {
                slug: (output_root / "towns" / f"{slug}.html").read_bytes()
                for slug in sorted(EXPECTED_SLUGS)
            }

            self.assertEqual(74, len(first))
            self.assertEqual([], second)
            self.assertEqual(first_bytes, second_bytes)
            self.assertEqual([], renderer.check_fallbacks(root=output_root))
            for slug, generated in first_bytes.items():
                self.assertEqual(generated, (ROOT / "towns" / f"{slug}.html").read_bytes())

    def test_legacy_generation_and_mutation_paths_are_fenced(self) -> None:
        somerset_generator = read("generate_somerset_towns.py")
        quarantine_generator = read("scripts/quarantine_low_value_towns.py")
        bulk_updater = read("bulk_update_towns.py")
        quality_gate = read("tools/check_town_content_quality.py")

        self.assertIn("render_noindex_town_fallbacks", somerset_generator)
        self.assertNotRegex(
            somerset_generator,
            r"median|schools_rating|commute_minutes|translate_to_spanish",
        )
        self.assertIn("render_noindex_town_fallbacks", quarantine_generator)
        self.assertNotIn("LOW_VALUE_STRICT_SLUGS = {", quarantine_generator)
        self.assertIn("MANAGED_NOINDEX_SLUGS", bulk_updater)
        self.assertIn("noindex_fallback_issues", quality_gate)

    def test_quality_gate_rejects_unsafe_copy_hidden_behind_noindex(self) -> None:
        from tools.check_town_content_quality import (
            NOINDEX_FALLBACK_RISKY_COPY,
            TownPage,
            noindex_fallback_issues,
        )

        unsafe = TownPage.from_source(
            ROOT / "towns" / "unsafe-example.html",
            '<meta name="robots" content="noindex, follow">'
            '<main><h1>Unsafe example</h1><p>Top-rated schools and a guaranteed '
            'return make this the best place for families.</p></main>',
        )
        issues = noindex_fallback_issues([unsafe])

        self.assertEqual(1, len(issues))
        self.assertIn("missing compact fallback marker", issues[0])
        self.assertIn("risky local claims", issues[0])
        self.assertIsNotNone(NOINDEX_FALLBACK_RISKY_COPY.search("strongest rankings"))

    def test_technical_seo_requires_local_schema_only_for_full_town_guides(self) -> None:
        from tools.check_technical_seo import requires_town_local_business

        fallback = read("towns/bedminster.html")
        self.assertFalse(requires_town_local_business(fallback))
        self.assertTrue(
            requires_town_local_business(
                '<meta name="robots" content="index, follow"><main>Full guide</main>'
            )
        )
        self.assertTrue(
            requires_town_local_business(
                '<meta name="robots" content="noindex, follow"><main>Other page</main>'
            )
        )
        self.assertTrue(
            requires_town_local_business(
                '<body data-noindex-town-fallback="v1"><main>Unmanaged robots</main>'
            )
        )

    def test_existing_quarantine_manifest_covers_the_full_fallback_policy(self) -> None:
        facts = json.loads(read("data/site-facts.json"))
        scopes = {
            entry.get("scope"): entry
            for entry in facts["editorialQuarantine"]
            if entry.get("scope", "").startswith("town-guide-")
        }
        covered = {
            slug
            for entry in scopes.values()
            for slug in entry.get("slugs", [])
        }

        self.assertEqual(EXPECTED_SLUGS, covered)
        for entry in scopes.values():
            self.assertEqual("compact-noindex-fallback-live", entry["reviewStatus"])
            self.assertEqual(
                "scripts/render_noindex_town_fallbacks.py",
                entry["fallbackRenderer"],
            )


if __name__ == "__main__":
    unittest.main()
