#!/usr/bin/env python3
"""Safety tests for automatic blog sitemap registration."""

from __future__ import annotations

import datetime as dt
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import sync_sitemap


class SyncSitemapSafetyTests(unittest.TestCase):
    def test_explicit_page_dates_are_used_and_future_or_invalid_dates_are_omitted(self) -> None:
        today = dt.date(2026, 8, 26)
        cases = (
            ('<meta property="article:modified_time" content="2026-08-25">', "2026-08-25"),
            ('<script type="application/ld+json">{"dateModified":"2026-08-24"}</script>', "2026-08-24"),
            ('<meta name="last-updated" content="2026-08-23">', "2026-08-23"),
            ('<meta property="article:modified_time" content="2026-09-01">', None),
            ('<meta name="last-updated" content="soon">', None),
            ("<title>No explicit date</title>", None),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(expected, sync_sitemap.extract_lastmod(source, today=today))

    def test_implementation_never_uses_filesystem_mtime_as_content_freshness(self) -> None:
        source = Path(sync_sitemap.__file__).read_text(encoding="utf-8")
        self.assertNotIn("getmtime", source)
        self.assertNotIn("st_mtime", source)
        self.assertNotIn("fromtimestamp", source)

    def test_registration_is_filtered_deterministic_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "blog").mkdir()
            (root / "sitemap.xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                "</urlset>\n",
                encoding="utf-8",
            )
            (root / "vercel.json").write_text(
                json.dumps(
                    {
                        "redirects": [
                            {
                                "source": "/blog/redirected",
                                "destination": "/blog/current",
                                "permanent": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            def page(slug: str, extra: str = "") -> None:
                (root / "blog" / f"{slug}.html").write_text(
                    f'<meta name="robots" content="index, follow">'
                    f'<link rel="canonical" href="https://thejorgeramirezgroup.com/blog/{slug}">'
                    f"{extra}",
                    encoding="utf-8",
                )

            page("dated", '<meta property="article:modified_time" content="2026-08-20">')
            page("undated")
            page("redirected", '<meta property="article:modified_time" content="2026-08-21">')
            page("future", '<meta property="article:modified_time" content="2026-09-20">')
            (root / "blog" / "noindex.html").write_text(
                '<meta name="robots" content="noindex, follow">'
                '<link rel="canonical" href="https://thejorgeramirezgroup.com/blog/noindex">',
                encoding="utf-8",
            )
            (root / "blog" / "wrong-canonical.html").write_text(
                '<link rel="canonical" href="https://thejorgeramirezgroup.com/blog/elsewhere">',
                encoding="utf-8",
            )

            # Filesystem timestamps are deliberately unrelated to content dates.
            old_timestamp = dt.datetime(2001, 1, 1, tzinfo=dt.timezone.utc).timestamp()
            for path in (root / "blog").glob("*.html"):
                os.utime(path, (old_timestamp, old_timestamp))

            entries = sync_sitemap.missing_blog_entries(
                root=root,
                today=dt.date(2026, 8, 26),
            )
            self.assertEqual(
                [
                    ("/blog/dated", "2026-08-20"),
                    ("/blog/future", None),
                    ("/blog/undated", None),
                ],
                entries,
            )

            applied = sync_sitemap.apply_entries(root=root, entries=entries)
            self.assertEqual(3, applied)
            sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("<lastmod>2026-08-20</lastmod>", sitemap)
            self.assertNotIn("2001-01-01", sitemap)
            self.assertNotRegex(sitemap, r"<loc>[^<]+/(?:future|undated)</loc>\s*<lastmod>")
            self.assertEqual([], sync_sitemap.missing_blog_entries(root=root, today=dt.date(2026, 8, 26)))

    def test_entry_renderer_escapes_urls_and_omits_unknown_lastmod(self) -> None:
        rendered = sync_sitemap.render_entry("/blog/a&b", None)
        self.assertIn("/blog/a&amp;b", rendered)
        self.assertNotIn("lastmod", rendered)

    def test_command_defaults_to_review_only_and_requires_explicit_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "blog").mkdir()
            sitemap_path = root / "sitemap.xml"
            original = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                "</urlset>\n"
            )
            sitemap_path.write_text(original, encoding="utf-8")
            (root / "vercel.json").write_text('{"redirects": []}', encoding="utf-8")
            (root / "blog" / "review-me.html").write_text(
                '<link rel="canonical" '
                'href="https://thejorgeramirezgroup.com/blog/review-me">',
                encoding="utf-8",
            )

            with mock.patch.object(sync_sitemap, "ROOT", root):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    review_status = sync_sitemap.main([])
                self.assertEqual(1, review_status)
                self.assertIn("missing /blog/review-me", output.getvalue())
                self.assertEqual(original, sitemap_path.read_text(encoding="utf-8"))

                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    apply_status = sync_sitemap.main(["--apply"])
                self.assertEqual(0, apply_status)
                self.assertIn("added /blog/review-me", output.getvalue())
                self.assertIn(
                    "<loc>https://thejorgeramirezgroup.com/blog/review-me</loc>",
                    sitemap_path.read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
