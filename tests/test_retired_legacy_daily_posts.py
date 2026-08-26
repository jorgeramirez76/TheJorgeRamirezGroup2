#!/usr/bin/env python3
"""Regression contract for the retired legacy daily-content cluster."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "retired-legacy-daily-posts.json"
SITE = "https://thejorgeramirezgroup.com"
SKIP_DIRS = {".git", "crm", "node_modules", "property-leads-system"}


def normalized_path(url: str, *, source: Path) -> str | None:
    value = url.strip()
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc:
        if parsed.netloc.lower() not in {
            "thejorgeramirezgroup.com",
            "www.thejorgeramirezgroup.com",
        }:
            return None
        path = parsed.path
    elif value.startswith("/"):
        path = parsed.path
    elif source.parent == ROOT / "blog":
        path = "/blog/" + parsed.path.removeprefix("./")
    else:
        return None
    path = re.sub(r"\.html$", "", path.rstrip("/"))
    return path or "/"


class RetiredLegacyDailyPostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.pages = cls.manifest["pages"]
        cls.routes = {item["path"] for item in cls.pages}

    def test_manifest_is_complete_traceable_and_performance_grounded(self) -> None:
        self.assertEqual(139, len(self.pages))
        self.assertEqual(139, len(self.routes))
        self.assertEqual("legacy-house-outlook-daily", self.manifest["workflow_id"])
        self.assertEqual("2026-08-26", self.manifest["retired_on"])
        self.assertEqual(1, self.manifest["gsc_recent_3_months"]["clicks"])
        self.assertEqual(74, self.manifest["gsc_recent_3_months"]["impressions"])
        allowed = {
            "/buy-a-home",
            "/sell-your-home",
            "/communities",
            "/towns/roselle",
            "/blog/first-time-home-buyer-nj-guide",
            "/blog/nj-property-tax-guide",
            "/blog/best-time-to-sell-home-nj",
        }
        self.assertTrue(all(item["destination"] in allowed for item in self.pages))

    def test_every_retired_route_is_a_small_noindex_homepage_palette_fallback(self) -> None:
        for item in self.pages:
            relative = item["file"]
            destination = item["destination"]
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertLess(len(source), 5000)
                self.assertRegex(
                    source,
                    r'<meta\s+name="robots"\s+content="noindex, follow">',
                )
                self.assertIn(f'<link rel="canonical" href="{SITE}{destination}">', source)
                self.assertIn(f'content="0; url={destination}"', source)
                self.assertIn(f'href="{destination}"', source)
                self.assertIn("window.location.replace", source)
                for color in ("#1A1A1A", "#C41230", "#B8962E", "#FAFAF8"):
                    self.assertIn(color, source)
                self.assertIn("'Playfair Display'", source)
                self.assertIn("Inter", source)
                self.assertNotIn("application/ld+json", source)
                self.assertNotIn("human-authored", source)

    def test_retired_routes_are_absent_from_sitemap_and_blog_index(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        index = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("<!-- AUTO ", index)
        for route in self.routes:
            with self.subTest(route=route):
                self.assertNotIn(f"<loc>{SITE}{route}</loc>", sitemap)
                self.assertNotRegex(
                    index,
                    rf'href=["\'](?:{re.escape(SITE)})?{re.escape(route)}(?:\.html)?(?:[?#][^"\']*)?["\']',
                )

    def test_indexable_html_does_not_link_to_retired_routes(self) -> None:
        retired_files = {item["file"] for item in self.pages}
        offenders: list[str] = []
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT)
            if relative.as_posix() in retired_files or any(part in SKIP_DIRS for part in relative.parts):
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', source, re.I):
                continue
            for href in re.findall(r'href\s*=\s*["\']([^"\']+)', source, re.I):
                if normalized_path(href, source=path) in self.routes:
                    offenders.append(f"{relative.as_posix()} -> {href}")
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
