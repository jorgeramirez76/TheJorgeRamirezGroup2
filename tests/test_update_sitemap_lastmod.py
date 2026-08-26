#!/usr/bin/env python3
"""Focused safety coverage for the sitemap ``lastmod`` maintenance utility."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.update_sitemap_lastmod import (
    InvalidInput,
    main,
    maintain_lastmods,
)


ORIGIN = "https://thejorgeramirezgroup.com"
TEST_DATE = "2026-08-26"


def html_page(
    canonical_path: str,
    *,
    robots: str = "index, follow",
    refresh: bool = False,
) -> str:
    refresh_tag = '<meta http-equiv="refresh" content="0;url=/elsewhere">' if refresh else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta name="robots" content="{robots}">
  {refresh_tag}
  <link rel="canonical" href="{ORIGIN}{canonical_path}">
</head>
<body><main>Fixture</main></body>
</html>
"""


def sitemap(entries: list[tuple[str, str | None]]) -> str:
    blocks = []
    for route, lastmod in entries:
        lastmod_line = "" if lastmod is None else f"    <lastmod>{lastmod}</lastmod>\n"
        blocks.append(
            "  <url>\n"
            f"    <loc>{ORIGIN}{route}</loc>\n"
            f"{lastmod_line}"
            "    <changefreq>monthly</changefreq>\n"
            "  </url>\n"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(blocks)
        + "</urlset>\n"
    )


class SitemapLastmodTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        (self.root / "vercel.json").write_text('{"redirects": []}\n', encoding="utf-8")
        (self.root / "sitemap.xml").write_text(
            sitemap(
                [
                    ("/", "2026-08-01"),
                    ("/blog", "2026-08-02"),
                    ("/towns/lake", "2026-08-03"),
                    ("/already-current", TEST_DATE),
                    ("/without-lastmod", None),
                    ("/not-requested", "2026-08-04"),
                ]
            ),
            encoding="utf-8",
        )
        (self.root / "sitemap-es.xml").write_text(
            sitemap(
                [
                    ("/es", "2026-08-05"),
                    ("/es/blog", "2026-08-06"),
                ]
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def write_page(self, relative: str, canonical_path: str, **kwargs: object) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html_page(canonical_path, **kwargs), encoding="utf-8")
        return path

    def test_check_derives_root_directory_spanish_and_clean_routes_without_writing(self) -> None:
        self.write_page("index.html", "/")
        self.write_page("blog/index.html", "/blog")
        self.write_page("es/index.html", "/es")
        self.write_page("es/blog/index.html", "/es/blog")
        self.write_page("towns/lake.html", "/towns/lake")
        before_en = (self.root / "sitemap.xml").read_bytes()
        before_es = (self.root / "sitemap-es.xml").read_bytes()

        report = maintain_lastmods(
            self.root,
            [
                "index.html",
                "blog/index.html",
                "es/index.html",
                "es/blog/index.html",
                "towns/lake.html",
            ],
            TEST_DATE,
            apply=False,
        )

        self.assertEqual(
            {
                f"{ORIGIN}/",
                f"{ORIGIN}/blog",
                f"{ORIGIN}/es",
                f"{ORIGIN}/es/blog",
                f"{ORIGIN}/towns/lake",
            },
            {page.canonical_url for page in report.pages if page.status == "eligible"},
        )
        self.assertEqual(5, sum(item.status == "would-update" for item in report.urls))
        self.assertEqual(before_en, (self.root / "sitemap.xml").read_bytes())
        self.assertEqual(before_es, (self.root / "sitemap-es.xml").read_bytes())

    def test_apply_changes_only_target_lastmod_text_and_uses_supplied_date_not_mtime(self) -> None:
        page = self.write_page("towns/lake.html", "/towns/lake")
        os.utime(page, (0, 0))
        sitemap_path = self.root / "sitemap.xml"
        before = sitemap_path.read_text(encoding="utf-8")

        report = maintain_lastmods(
            self.root,
            [page],
            TEST_DATE,
            apply=True,
        )

        expected = before.replace(
            "<loc>https://thejorgeramirezgroup.com/towns/lake</loc>\n"
            "    <lastmod>2026-08-03</lastmod>",
            "<loc>https://thejorgeramirezgroup.com/towns/lake</loc>\n"
            f"    <lastmod>{TEST_DATE}</lastmod>",
        )
        self.assertEqual(expected, sitemap_path.read_text(encoding="utf-8"))
        self.assertEqual(["updated"], [item.status for item in report.urls])
        self.assertNotIn("1970", sitemap_path.read_text(encoding="utf-8"))

    def test_current_unmatched_and_missing_lastmod_are_explicit_and_unchanged(self) -> None:
        self.write_page("already-current.html", "/already-current")
        self.write_page("absent.html", "/absent")
        self.write_page("without-lastmod.html", "/without-lastmod")
        before = (self.root / "sitemap.xml").read_bytes()

        report = maintain_lastmods(
            self.root,
            ["already-current.html", "absent.html", "without-lastmod.html"],
            TEST_DATE,
            apply=True,
        )

        self.assertEqual(
            {
                f"{ORIGIN}/already-current": "current",
                f"{ORIGIN}/absent": "unmatched",
                f"{ORIGIN}/without-lastmod": "missing-lastmod",
            },
            {item.canonical_url: item.status for item in report.urls},
        )
        self.assertEqual(before, (self.root / "sitemap.xml").read_bytes())

    def test_nonindexable_noncanonical_and_redirect_pages_are_reported_and_skipped(self) -> None:
        self.write_page("noindex.html", "/noindex", robots="noindex, follow")
        self.write_page("refresh.html", "/refresh", refresh=True)
        self.write_page("alias/index.html", "/towns/lake")
        self.write_page("with-extension.html", "/with-extension.html")
        self.write_page("redirected.html", "/redirected")
        (self.root / "vercel.json").write_text(
            '{"redirects":[{"source":"/redirected","destination":"/towns/lake",'
            '"permanent":true}]}\n',
            encoding="utf-8",
        )

        report = maintain_lastmods(
            self.root,
            [
                "noindex.html",
                "refresh.html",
                "alias/index.html",
                "with-extension.html",
                "redirected.html",
            ],
            TEST_DATE,
            apply=False,
        )

        self.assertEqual(
            {
                "noindex.html": "noindex",
                "refresh.html": "meta-refresh",
                "alias/index.html": "non-self-canonical",
                "with-extension.html": "non-extensionless-canonical",
                "redirected.html": "redirect-source",
            },
            {page.path: page.reason for page in report.pages},
        )
        self.assertEqual([], report.urls)

    def test_invalid_dates_are_rejected_before_any_write(self) -> None:
        self.write_page("index.html", "/")
        before = (self.root / "sitemap.xml").read_bytes()
        for invalid in ("2026-8-26", "2026-02-30", "26-08-2026", "today"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvalidInput):
                    maintain_lastmods(self.root, ["index.html"], invalid, apply=True)
                self.assertEqual(before, (self.root / "sitemap.xml").read_bytes())

    def test_paths_outside_repo_non_html_and_missing_paths_are_rejected_atomically(self) -> None:
        self.write_page("index.html", "/")
        temporary_root = Path(self._temporary.name)
        outside = temporary_root.with_name(f"{temporary_root.name}-outside.html")
        outside.write_text(html_page("/"), encoding="utf-8")
        symlink = self.root / "escaped.html"
        symlink.symlink_to(outside)
        before = (self.root / "sitemap.xml").read_bytes()
        try:
            for invalid in (
                outside,
                "../outside-lastmod-fixture.html",
                "escaped.html",
                "vercel.json",
                "missing.html",
            ):
                with self.subTest(invalid=str(invalid)):
                    with self.assertRaises(InvalidInput):
                        maintain_lastmods(
                            self.root,
                            ["index.html", invalid],
                            TEST_DATE,
                            apply=True,
                        )
                    self.assertEqual(before, (self.root / "sitemap.xml").read_bytes())
        finally:
            outside.unlink(missing_ok=True)

    def test_duplicate_sitemap_locations_are_ambiguous_and_never_modified(self) -> None:
        self.write_page("towns/lake.html", "/towns/lake")
        sitemap_path = self.root / "sitemap.xml"
        duplicated = sitemap_path.read_text(encoding="utf-8").replace(
            "</urlset>",
            "  <url>\n"
            f"    <loc>{ORIGIN}/towns/lake</loc>\n"
            "    <lastmod>2026-08-07</lastmod>\n"
            "  </url>\n"
            "</urlset>",
        )
        sitemap_path.write_text(duplicated, encoding="utf-8")
        before = sitemap_path.read_bytes()

        report = maintain_lastmods(
            self.root,
            ["towns/lake.html"],
            TEST_DATE,
            apply=True,
        )

        self.assertEqual(["ambiguous"], [item.status for item in report.urls])
        self.assertEqual(before, sitemap_path.read_bytes())

    def test_malformed_affected_sitemap_aborts_before_any_language_file_is_written(self) -> None:
        self.write_page("index.html", "/")
        self.write_page("es/index.html", "/es")
        english_before = (self.root / "sitemap.xml").read_bytes()
        (self.root / "sitemap-es.xml").write_text("<urlset><url>", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "not valid XML"):
            maintain_lastmods(
                self.root,
                ["index.html", "es/index.html"],
                TEST_DATE,
                apply=True,
            )

        self.assertEqual(english_before, (self.root / "sitemap.xml").read_bytes())

    def test_cli_check_and_dry_run_report_drift_without_writing(self) -> None:
        self.write_page("index.html", "/")
        before = (self.root / "sitemap.xml").read_bytes()

        for flag in ("--check", "--dry-run"):
            output = io.StringIO()
            with self.subTest(flag=flag), contextlib.redirect_stdout(output):
                result = main(
                    [flag, "--date", TEST_DATE, "index.html"],
                    repo_root=self.root,
                )
            self.assertEqual(1, result)
            self.assertIn("would-update", output.getvalue())
            self.assertIn("sitemap.xml", output.getvalue())
            self.assertEqual(before, (self.root / "sitemap.xml").read_bytes())

    def test_cli_apply_is_explicit_and_reports_success(self) -> None:
        self.write_page("index.html", "/")
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            result = main(
                ["--apply", "--date", TEST_DATE, "index.html"],
                repo_root=self.root,
            )

        self.assertEqual(0, result)
        self.assertIn("updated", output.getvalue())
        self.assertIn(f"<lastmod>{TEST_DATE}</lastmod>", (self.root / "sitemap.xml").read_text())


if __name__ == "__main__":
    unittest.main()
