#!/usr/bin/env python3
"""Offline regression tests for the production/source blog inventory guard."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import check_production_source_drift as drift


class FakeFetch:
    def __init__(self, responses: dict[str, drift.FetchResponse | Exception]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def __call__(self, url: str) -> drift.FetchResponse:
        self.calls.append(url)
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


def response(url: str, body: str, *, status: int = 200, headers: dict[str, str] | None = None) -> drift.FetchResponse:
    return drift.FetchResponse(
        requested_url=url,
        final_url=url,
        status=status,
        headers=headers or {},
        body=body,
    )


def page(route: str, *, robots: str = "index, follow", canonical: str | None = None, refresh: bool = False) -> str:
    canonical = canonical if canonical is not None else f"{drift.SITE_ORIGIN}{route}"
    refresh_tag = '<meta http-equiv="refresh" content="0; url=/blog/elsewhere">' if refresh else ""
    return (
        "<!doctype html><html><head>"
        f'<meta name="robots" content="{robots}">'
        f'<link rel="canonical" href="{canonical}">'
        f"{refresh_tag}</head><body>Article</body></html>"
    )


def sitemap(*routes: str) -> str:
    entries = "".join(f"<url><loc>{drift.SITE_ORIGIN}{route}</loc></url>" for route in routes)
    return f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>'


class ProductionSourceDriftTests(unittest.TestCase):
    def make_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "blog").mkdir()
        (root / "vercel.json").write_text(json.dumps({"redirects": []}), encoding="utf-8")
        return temporary, root

    def write_local_page(self, root: Path, slug: str, *, robots: str = "index, follow") -> None:
        route = f"/blog/{slug}"
        (root / "blog" / f"{slug}.html").write_text(
            page(route, robots=robots),
            encoding="utf-8",
        )

    def test_blog_index_only_routes_reproduce_the_five_live_only_post_drift(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        self.write_local_page(root, "owned")
        missing = (
            "/blog/fall-home-prep-signs-nj-sellers-2026",
            "/blog/fall-mortgage-strategy-nj-buyers-2026",
            "/blog/pre-listing-inspection-nj-sellers-2026",
            "/blog/show-ready-home-nj-sellers-30-days-2026",
            "/blog/smart-home-upgrades-nj-home-value-2026",
        )
        index_html = "<html><body>" + "".join(
            f'<a href="{route}.html?source=index#read">Post</a>' for route in missing
        ) + '<a href="owned.html">Owned</a></body></html>'
        responses: dict[str, drift.FetchResponse | Exception] = {
            drift.BLOG_INDEX_URL: response(drift.BLOG_INDEX_URL, index_html),
            drift.SITEMAP_URL: response(drift.SITEMAP_URL, sitemap("/blog/owned")),
        }
        responses.update(
            {
                f"{drift.SITE_ORIGIN}{route}": response(
                    f"{drift.SITE_ORIGIN}{route}",
                    page(route),
                )
                for route in missing
            }
        )
        fetch = FakeFetch(responses)

        report = drift.check_production_source_drift(
            root=root,
            fetch=fetch,
            delay_seconds=0,
        )

        self.assertEqual(missing, report.production_only_indexable)
        self.assertEqual(7, len(fetch.calls))
        self.assertIn(drift.BLOG_INDEX_URL, fetch.calls)
        self.assertIn(drift.SITEMAP_URL, fetch.calls)

    def test_redirect_noindex_meta_refresh_and_other_canonical_are_not_indexable_drift(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        self.write_local_page(root, "owned")
        candidates = ("redirected", "noindex", "refresh", "canonicalized", "header-noindex")
        index_html = "".join(f'<a href="/blog/{slug}">{slug}</a>' for slug in candidates)
        responses: dict[str, drift.FetchResponse | Exception] = {
            drift.BLOG_INDEX_URL: response(drift.BLOG_INDEX_URL, index_html),
            drift.SITEMAP_URL: response(drift.SITEMAP_URL, sitemap("/blog/owned")),
            f"{drift.SITE_ORIGIN}/blog/redirected": drift.FetchResponse(
                requested_url=f"{drift.SITE_ORIGIN}/blog/redirected",
                final_url=f"{drift.SITE_ORIGIN}/blog/owned",
                status=200,
                headers={},
                body=page("/blog/owned"),
            ),
            f"{drift.SITE_ORIGIN}/blog/noindex": response(
                f"{drift.SITE_ORIGIN}/blog/noindex",
                page("/blog/noindex", robots="noindex, follow"),
            ),
            f"{drift.SITE_ORIGIN}/blog/refresh": response(
                f"{drift.SITE_ORIGIN}/blog/refresh",
                page("/blog/refresh", refresh=True),
            ),
            f"{drift.SITE_ORIGIN}/blog/canonicalized": response(
                f"{drift.SITE_ORIGIN}/blog/canonicalized",
                page("/blog/canonicalized", canonical=f"{drift.SITE_ORIGIN}/blog/owned"),
            ),
            f"{drift.SITE_ORIGIN}/blog/header-noindex": response(
                f"{drift.SITE_ORIGIN}/blog/header-noindex",
                page("/blog/header-noindex"),
                headers={"X-Robots-Tag": "noindex, follow"},
            ),
        }

        report = drift.check_production_source_drift(
            root=root,
            fetch=FakeFetch(responses),
            delay_seconds=0,
        )

        self.assertEqual((), report.production_only_indexable)
        self.assertEqual(set(candidates), {route.removeprefix("/blog/") for route in report.production_nonindexable})

    def test_source_only_additions_are_informational_and_do_not_fail(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        self.write_local_page(root, "already-live")
        self.write_local_page(root, "new-reviewed-source")
        fetch = FakeFetch(
            {
                drift.BLOG_INDEX_URL: response(
                    drift.BLOG_INDEX_URL,
                    '<a href="https://www.thejorgeramirezgroup.com/blog/already-live/">Live</a>',
                ),
                drift.SITEMAP_URL: response(
                    drift.SITEMAP_URL,
                    sitemap("/blog/already-live"),
                ),
            }
        )

        report = drift.check_production_source_drift(root=root, fetch=fetch, delay_seconds=0)

        self.assertFalse(report.has_blocking_drift)
        self.assertEqual(("/blog/new-reviewed-source",), report.source_only_indexable)
        self.assertEqual([drift.BLOG_INDEX_URL, drift.SITEMAP_URL], fetch.calls)

    def test_fetch_failure_and_detail_request_cap_fail_closed(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        self.write_local_page(root, "owned")
        failing = FakeFetch(
            {
                drift.BLOG_INDEX_URL: drift.DriftCheckError("production unavailable"),
            }
        )
        with self.assertRaisesRegex(drift.DriftCheckError, "production unavailable"):
            drift.check_production_source_drift(root=root, fetch=failing, delay_seconds=0)

        capped = FakeFetch(
            {
                drift.BLOG_INDEX_URL: response(
                    drift.BLOG_INDEX_URL,
                    '<a href="/blog/one">One</a><a href="/blog/two">Two</a>',
                ),
                drift.SITEMAP_URL: response(drift.SITEMAP_URL, sitemap("/blog/owned")),
            }
        )
        with self.assertRaisesRegex(drift.DriftCheckError, "detail request cap"):
            drift.check_production_source_drift(
                root=root,
                fetch=capped,
                delay_seconds=0,
                max_detail_requests=1,
            )
        self.assertEqual([drift.BLOG_INDEX_URL, drift.SITEMAP_URL], capped.calls)

    def test_malformed_or_empty_discovery_surfaces_fail_closed(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        self.write_local_page(root, "owned")
        malformed = FakeFetch(
            {
                drift.BLOG_INDEX_URL: response(
                    drift.BLOG_INDEX_URL,
                    '<a href="/blog/owned">Owned</a>',
                ),
                drift.SITEMAP_URL: response(drift.SITEMAP_URL, "not xml"),
            }
        )
        with self.assertRaisesRegex(drift.DriftCheckError, "sitemap"):
            drift.check_production_source_drift(root=root, fetch=malformed, delay_seconds=0)

        empty = FakeFetch(
            {
                drift.BLOG_INDEX_URL: response(drift.BLOG_INDEX_URL, "<html></html>"),
                drift.SITEMAP_URL: response(drift.SITEMAP_URL, sitemap()),
            }
        )
        with self.assertRaisesRegex(drift.DriftCheckError, "no blog routes"):
            drift.check_production_source_drift(root=root, fetch=empty, delay_seconds=0)

    def test_cli_refuses_implicit_network_mode(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch.object(drift, "make_live_fetcher") as make_live_fetcher,
            contextlib.redirect_stderr(stderr),
        ):
            status = drift.main([])

        self.assertEqual(2, status)
        self.assertIn("--live", stderr.getvalue())
        make_live_fetcher.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
