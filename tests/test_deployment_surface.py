#!/usr/bin/env python3
"""Keep private build/audit artifacts out of the static Vercel deployment."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import audit_site


ROOT = Path(__file__).resolve().parents[1]
DEPLOYED_TOWN_IMAGES = {
    "berkeley-heights-1.webp",
    "chatham-borough-1.webp",
    "chatham-township-2.webp",
    "chatham-township-2-640.webp",
    "chatham-township-2-960.webp",
    "cranford-1.webp",
    "denville-1.webp",
    "east-hanover-1.webp",
    "fanwood-1.webp",
    "morris-plains-1.webp",
    "new-providence-1.webp",
    "roselle-park-1.webp",
    "springfield-1.webp",
}


class DeploymentSurfaceTests(unittest.TestCase):
    def test_internal_directories_and_stale_public_files_are_ignored(self) -> None:
        entries = {
            line.strip()
            for line in (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        required = {
            ".git",
            ".gitignore",
            ".gitattributes",
            "CNAME",
            "**/.gitkeep",
            ".claude",
            "node_modules",
            "tests",
            "scripts",
            "data",
            "crm",
            "docs",
            "lead-research",
            "property-leads-system",
            "_posts",
            "tools/blog-automation",
            "tools/seo-optimizer",
            "office-status.json",
            "schema-realtor.json",
            "*.py",
            "*.pyc",
            "*.md",
            "*.log",
            "*.db",
            "*.backup",
        }
        self.assertEqual(set(), required - entries)

    def test_historical_town_photo_archive_is_not_deployed(self) -> None:
        source = (ROOT / ".vercelignore").read_text(encoding="utf-8")
        self.assertIn("images/towns/*.webp", source)
        self.assertIn("images/towns/credits.json", source)
        allowlisted = {
            line.removeprefix("!images/towns/")
            for line in source.splitlines()
            if line.startswith("!images/towns/")
        }
        self.assertEqual(DEPLOYED_TOWN_IMAGES, allowlisted)

        referenced: set[str] = set()
        for path in audit_site.all_html_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            referenced.update(re.findall(r"/images/towns/([A-Za-z0-9._-]+\.webp)", text))
        self.assertEqual(DEPLOYED_TOWN_IMAGES, referenced)

    def test_public_tools_and_downloadable_guides_remain_deployable(self) -> None:
        source = (ROOT / ".vercelignore").read_text(encoding="utf-8")
        self.assertNotIn("\ntools\n", f"\n{source}\n")
        self.assertIn("!guides/*.pdf", source)
        for relative in (
            "tools/commute-scorer.html",
            "tools/home-value-estimator.html",
            "tools/market-comparison-widget.html",
            "tools/mortgage-calculator.html",
            "api/lead.js",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_web_manifest_matches_verified_brand_and_service_area(self) -> None:
        for name in ("manifest.json", "site.webmanifest"):
            with self.subTest(name=name):
                manifest = json.loads((ROOT / name).read_text(encoding="utf-8"))
                self.assertEqual("#1A1A1A", manifest["theme_color"])
                self.assertEqual("#FAFAF8", manifest["background_color"])
                self.assertEqual("standalone", manifest["display"])
                for county in ("Union", "Essex", "Morris", "Hudson", "Middlesex", "Somerset"):
                    self.assertIn(county, manifest["description"])

    def test_legacy_schema_asset_cannot_drift_from_verified_business_facts(self) -> None:
        facts = json.loads((ROOT / "data/site-facts.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schema-realtor.json").read_text(encoding="utf-8"))
        business = facts["business"]
        self.assertEqual(business["directPhone"]["e164"], schema["telephone"])
        self.assertEqual(business["email"], schema["email"])
        self.assertEqual(business["geo"]["latitude"], schema["geo"]["latitude"])
        self.assertEqual(business["geo"]["longitude"], schema["geo"]["longitude"])
        self.assertEqual(business["njRealEstateLicense"], schema["founder"]["identifier"]["value"])
        self.assertEqual(
            {f"{county} County, New Jersey" for county in facts["serviceCounties"]},
            {area["name"] for area in schema["areaServed"]},
        )
        source = json.dumps(schema).lower()
        for unsupported in ("aggregateRating", "priceRange", "off-market", "top-rated", "nahrep"):
            self.assertNotIn(unsupported.lower(), source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
