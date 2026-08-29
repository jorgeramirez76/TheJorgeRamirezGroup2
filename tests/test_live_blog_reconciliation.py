#!/usr/bin/env python3
"""Regression contract for the 2026-08-29 production/source blog drift."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "live-blog-reconciliation-2026-08-29.json"
SITE = "https://thejorgeramirezgroup.com"
SKIP_DIRS = {".git", ".vercel", "crm", "node_modules", "property-leads-system"}
EXPECTED = {
    "/blog/fall-home-prep-signs-nj-sellers-2026": (
        "/blog/best-time-to-sell-home-nj",
        "8351523e9575b46f031970417b7929d61b4f1d1bdd26f2fbbf11ac693119b55a",
    ),
    "/blog/fall-mortgage-strategy-nj-buyers-2026": (
        "/blog/first-time-home-buyer-nj-guide",
        "ee50b16b52f46d289068787b04a92fbe8404ec667c3c4e8ed5e45b2891362d08",
    ),
    "/blog/pre-listing-inspection-nj-sellers-2026": (
        "/sell-your-home",
        "94ef012e43e2270b59ef2f188f0bb87882a3665423dbc376403923a23012b569",
    ),
    "/blog/show-ready-home-nj-sellers-30-days-2026": (
        "/sell-your-home",
        "e23a1e2631f24c83ef4951824f3aa919e66399f81adf884c7e698ffcb5394797",
    ),
    "/blog/smart-home-upgrades-nj-home-value-2026": (
        "/sell-your-home",
        "08993d624f85a63b95b4617122d0c4f974cc3b3984671d4840bc8610dc05fc16",
    ),
}


def normalized_path(url: str, *, source: Path) -> str | None:
    parsed = urlsplit(url.strip())
    if parsed.scheme and parsed.netloc:
        if parsed.netloc.lower() not in {
            "thejorgeramirezgroup.com",
            "www.thejorgeramirezgroup.com",
        }:
            return None
        path = parsed.path
    elif url.startswith("/"):
        path = parsed.path
    elif parsed.scheme or url.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    elif source.parent == ROOT / "blog":
        path = "/blog/" + parsed.path.removeprefix("./")
    else:
        return None
    return re.sub(r"\.html$", "", path.rstrip("/")) or "/"


class LiveBlogReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.pages = cls.manifest["pages"]
        cls.by_path = {item["path"]: item for item in cls.pages}

    def test_manifest_is_exact_traceable_and_fail_closed(self) -> None:
        self.assertEqual("live-blog-source-drift-2026-08-29", self.manifest["incident_id"])
        self.assertEqual("retire_to_reviewed_evergreen_guides", self.manifest["disposition"])
        self.assertEqual(set(EXPECTED), set(self.by_path))
        self.assertEqual(len(self.pages), len(self.by_path))
        self.assertRegex(self.manifest["evidence"]["blog_index_sha256"], r"^[0-9a-f]{64}$")
        for route, (destination, sha256) in EXPECTED.items():
            with self.subTest(route=route):
                page = self.by_path[route]
                self.assertEqual(destination, page["destination"])
                self.assertEqual(sha256, page["sha256"])
                self.assertEqual(f"{SITE}{route}", page["source_url"])
                self.assertGreaterEqual(len(page["issues"]), 4)

    def test_each_route_has_a_small_noindex_local_fallback(self) -> None:
        for route, page in self.by_path.items():
            relative = page["file"]
            destination = page["destination"]
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(route=route):
                self.assertEqual(f"blog/{route.rsplit('/', 1)[-1]}.html", relative)
                self.assertLess(len(source), 5000)
                self.assertIn('<meta name="robots" content="noindex, follow">', source)
                self.assertIn(f'<link rel="canonical" href="{SITE}{destination}">', source)
                self.assertIn(f'content="0; url={destination}"', source)
                self.assertIn(f'href="{destination}"', source)
                self.assertIn(f'window.location.replace("{destination}")', source)
                for color in ("#1A1A1A", "#C41230", "#B8962E", "#FAFAF8"):
                    self.assertIn(color, source)
                self.assertIn("'Playfair Display'", source)
                self.assertIn("Inter", source)
                self.assertNotIn("application/ld+json", source)
                self.assertNotRegex(source, r'https?://(?:images\.)?unsplash\.com')

    def test_exact_and_html_routes_redirect_permanently(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirects = {
            item["source"]: item
            for item in config["redirects"]
            if not item.get("has") and ":" not in item["source"] and "*" not in item["source"]
        }
        for route, page in self.by_path.items():
            for source in (route, f"{route}.html"):
                with self.subTest(source=source):
                    self.assertIn(source, redirects)
                    self.assertEqual(page["destination"], redirects[source]["destination"])
                    self.assertIs(True, redirects[source]["permanent"])

    def test_routes_are_absent_from_indexable_discovery_surfaces(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        blog_index = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")
        for route in self.by_path:
            with self.subTest(route=route):
                self.assertNotIn(f"<loc>{SITE}{route}</loc>", sitemap)
                self.assertNotRegex(
                    blog_index,
                    rf'href=["\'](?:{re.escape(SITE)})?{re.escape(route)}(?:\.html)?(?:[?#][^"\']*)?["\']',
                )

    def test_indexable_html_does_not_link_to_retired_live_routes(self) -> None:
        fallback_files = {item["file"] for item in self.pages}
        offenders: list[str] = []
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT)
            if relative.as_posix() in fallback_files or any(part in SKIP_DIRS for part in relative.parts):
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', source, re.I):
                continue
            for href in re.findall(r'href\s*=\s*["\']([^"\']+)', source, re.I):
                if normalized_path(href, source=path) in self.by_path:
                    offenders.append(f"{relative.as_posix()} -> {href}")
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
