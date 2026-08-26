#!/usr/bin/env python3
"""Regression checks for the low-value town-template quarantine."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.check_town_content_quality import (
    REVIEW_MINIMUM_WORDS,
    REVIEW_SIMILARITY,
    fold_gsc_page_rows,
    near_duplicate_groups,
    robots_noindex,
    scan_town_pages,
)


SITE = "https://thejorgeramirezgroup.com"
GSC_EXPORT = Path(
    "/Users/teddy/Documents/Codex/2026-08-25/t/work/gsc_compare/Pages.csv"
)
GSC_EXPORT_SHA256 = "5e66478db75f8693ea762cbeba2fd8d58d63eecbe3d50e71981fcd1f1c80c6f9"

PRIORITY_ENGLISH_SLUGS = {
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

LOW_VALUE_STRICT_SLUGS = {
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


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def sitemap_urls(name: str) -> set[str]:
    root = ET.parse(ROOT / name).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


def json_ld_objects(source: str) -> list[object]:
    blocks = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source,
        flags=re.I | re.S,
    )
    return [json.loads(html.unescape(block).strip()) for block in blocks]


class TownInventoryQuarantineTests(unittest.TestCase):
    def test_policy_partition_is_explicit_and_non_overlapping(self) -> None:
        self.assertEqual(16, len(PRIORITY_ENGLISH_SLUGS))
        self.assertEqual(48, len(LOW_VALUE_STRICT_SLUGS))
        self.assertTrue(PRIORITY_ENGLISH_SLUGS.isdisjoint(LOW_VALUE_STRICT_SLUGS))

    def test_low_value_strict_templates_are_quarantined_in_both_languages(self) -> None:
        english_urls = sitemap_urls("sitemap.xml")
        spanish_urls = sitemap_urls("sitemap-es.xml")
        failures: list[str] = []

        for slug in sorted(LOW_VALUE_STRICT_SLUGS):
            for language, prefix, submitted in (
                ("en", "", english_urls),
                ("es", "es/", spanish_urls),
            ):
                relative = f"{prefix}towns/{slug}.html"
                source = read(relative)
                if not robots_noindex(source):
                    failures.append(f"{relative}: missing noindex")
                if re.search(r'<link\b[^>]*\bhreflang=["\']', source, re.I):
                    failures.append(f"{relative}: still publishes hreflang")
                if f"{SITE}/{prefix}towns/{slug}" in submitted:
                    failures.append(f"{relative}: still submitted in {language} sitemap")

        self.assertEqual([], failures)

    def test_priority_english_pages_remain_indexable_and_submitted(self) -> None:
        english_urls = sitemap_urls("sitemap.xml")
        failures: list[str] = []
        for slug in sorted(PRIORITY_ENGLISH_SLUGS):
            source = read(f"towns/{slug}.html")
            if robots_noindex(source):
                failures.append(f"towns/{slug}.html: unexpectedly noindex")
            if f"{SITE}/towns/{slug}" not in english_urls:
                failures.append(f"towns/{slug}.html: missing from sitemap.xml")
        self.assertEqual([], failures)

    def test_only_priority_rewrite_pages_remain_in_strict_duplicate_groups(self) -> None:
        groups = near_duplicate_groups(
            scan_town_pages(ROOT),
            threshold=REVIEW_SIMILARITY,
            minimum_words=REVIEW_MINIMUM_WORDS,
        )
        failures = []
        for group in groups:
            members = {page.slug for page in group}
            if group[0].language != "en" or not members <= PRIORITY_ENGLISH_SLUGS:
                failures.append(
                    f"{group[0].language}: {', '.join(sorted(members))}"
                )
        self.assertEqual([], failures)

    def test_registry_sitemap_and_communities_hub_match_exactly(self) -> None:
        facts = json.loads(read("data/site-facts.json"))
        inventory = facts["canonicalTownInventory"]
        registered = {
            slug
            for slugs in inventory["byCounty"].values()
            for slug in slugs
        }
        submitted = {
            url.removeprefix(f"{SITE}/towns/")
            for url in sitemap_urls("sitemap.xml")
            if url.startswith(f"{SITE}/towns/")
        }
        hub = read("communities/index.html")
        linked = set(re.findall(r'href=["\']/towns/([^"\']+)["\']', hub))

        self.assertEqual(64, inventory["total"])
        self.assertEqual(inventory["total"], len(registered))
        self.assertEqual(registered, submitted)
        self.assertEqual(registered, linked)
        self.assertIn("64 NJ Communities We Serve", hub)

        item_lists = []
        for obj in json_ld_objects(hub):
            if isinstance(obj, dict):
                entity = obj.get("mainEntity")
                if isinstance(entity, dict) and entity.get("@type") == "ItemList":
                    item_lists.append(entity)
        self.assertEqual([64], [item["numberOfItems"] for item in item_lists])

        matching_quarantine = [
            entry
            for entry in facts["editorialQuarantine"]
            if entry.get("scope") == "town-guide-strict-near-duplicate-cluster"
        ]
        self.assertEqual(1, len(matching_quarantine))
        self.assertEqual(
            LOW_VALUE_STRICT_SLUGS,
            set(matching_quarantine[0]["slugs"]),
        )
        self.assertEqual({"en", "es"}, set(matching_quarantine[0]["languages"]))

    def test_gsc_impact_is_a_reproducible_export_snapshot(self) -> None:
        manifest = json.loads(read("data/gsc-town-quarantine-impact.json"))
        fixture = ROOT / "tests" / "fixtures" / "gsc-town-quarantine-pages.csv"

        self.assertEqual(str(GSC_EXPORT), manifest["sourceExport"])
        self.assertEqual(GSC_EXPORT_SHA256, manifest["sourceExportSha256"])
        self.assertEqual(
            "Historical snapshot calculated from the supplied Search Console export; "
            "metrics are not live or current beyond that export.",
            manifest["snapshotCaveat"],
        )
        self.assertEqual(
            LOW_VALUE_STRICT_SLUGS,
            set(manifest["quarantinedSlugs"]),
        )

        with fixture.open(encoding="utf-8-sig", newline="") as handle:
            folded = fold_gsc_page_rows(csv.DictReader(handle), LOW_VALUE_STRICT_SLUGS)
        totals = {
            "canonicalFamiliesWithRows": len(folded),
            "variantRows": sum(int(metrics["rows"]) for metrics in folded.values()),
            "clicks": sum(int(metrics["clicks"]) for metrics in folded.values()),
            "impressions": sum(
                int(metrics["impressions"]) for metrics in folded.values()
            ),
        }
        self.assertEqual(manifest["totals"], totals)
        self.assertEqual(
            {
                "canonicalFamiliesWithRows": 60,
                "variantRows": 74,
                "clicks": 0,
                "impressions": 135,
            },
            totals,
        )

        if GSC_EXPORT.exists():
            digest = hashlib.sha256(GSC_EXPORT.read_bytes()).hexdigest()
            self.assertEqual(GSC_EXPORT_SHA256, digest)
            with GSC_EXPORT.open(encoding="utf-8-sig", newline="") as handle:
                full_export = fold_gsc_page_rows(
                    csv.DictReader(handle), LOW_VALUE_STRICT_SLUGS
                )
            self.assertEqual(folded, full_export)


if __name__ == "__main__":
    unittest.main()
