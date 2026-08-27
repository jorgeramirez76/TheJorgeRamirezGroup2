#!/usr/bin/env python3
"""Fail-closed alignment between sitemap freshness and explicit page metadata."""

from __future__ import annotations

import datetime as dt
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

from tools.sync_sitemap import meta_values, valid_past_or_present_date


ROOT = Path(__file__).resolve().parents[1]
SITEMAPS = ("sitemap.xml", "sitemap-es.xml")
JSON_LD_MODIFIED_RE = re.compile(
    r'["\']dateModified["\']\s*:\s*["\']([^"\']+)',
    re.IGNORECASE,
)


def page_path_for_url(url: str) -> Path | None:
    clean_path = unquote(urlsplit(url).path).strip("/")
    candidates = (
        (ROOT / "index.html",)
        if not clean_path
        else (ROOT / f"{clean_path}.html", ROOT / clean_path / "index.html")
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def valid_explicit_modified_dates(source: str, *, today: dt.date) -> list[str]:
    metas = meta_values(source)
    raw_candidates = [
        *metas.get("article:modified_time", []),
        *JSON_LD_MODIFIED_RE.findall(source),
        *metas.get("last-updated", []),
    ]
    return [
        accepted
        for value in raw_candidates
        if (accepted := valid_past_or_present_date(value, today)) is not None
    ]


class SitemapLastmodAlignmentTests(unittest.TestCase):
    def test_sitemap_lastmod_does_not_predate_valid_explicit_page_date(self) -> None:
        today = dt.date.today()
        violations: list[str] = []

        for sitemap_name in SITEMAPS:
            root = ET.parse(ROOT / sitemap_name).getroot()
            for url_node in root.findall("{*}url"):
                loc = (url_node.findtext("{*}loc") or "").strip()
                lastmod_raw = (url_node.findtext("{*}lastmod") or "").strip()
                page_path = page_path_for_url(loc)

                self.assertIsNotNone(page_path, f"{loc} has no physical HTML document")
                try:
                    sitemap_date = dt.date.fromisoformat(lastmod_raw)
                except ValueError:
                    violations.append(f"{loc}: invalid or absent sitemap lastmod {lastmod_raw!r}")
                    continue

                source = page_path.read_text(encoding="utf-8", errors="replace")
                explicit_dates = valid_explicit_modified_dates(source, today=today)
                if explicit_dates:
                    newest_explicit = max(dt.date.fromisoformat(value) for value in explicit_dates)
                    if sitemap_date < newest_explicit:
                        violations.append(
                            f"{loc}: sitemap={sitemap_date.isoformat()} "
                            f"explicit={newest_explicit.isoformat()}"
                        )

        self.assertEqual([], violations, "\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
