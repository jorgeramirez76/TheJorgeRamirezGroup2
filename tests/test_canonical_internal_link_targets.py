#!/usr/bin/env python3
"""Guard canonical pages from linking to quarantined or redirect-fallback routes."""

from __future__ import annotations

import html
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE_HOSTS = {"thejorgeramirezgroup.com", "www.thejorgeramirezgroup.com"}
ALLOWED_NOINDEX_TARGETS = {"/sms-terms", "/es/sms-terms"}
NON_DOCUMENT_SUFFIXES = {
    ".avif", ".css", ".csv", ".gif", ".ico", ".jpeg", ".jpg", ".js",
    ".json", ".mjs", ".mp3", ".mp4", ".pdf", ".png", ".svg", ".txt",
    ".webm", ".webp", ".xml", ".zip",
}
HREF_RE = re.compile(r'<a\b[^>]*href=["\']([^"\']+)', re.I)
NOINDEX_RE = re.compile(
    r'<meta\b(?=[^>]*\bname=["\']robots["\'])'
    r'(?=[^>]*\bcontent=["\'][^"\']*\bnoindex\b)[^>]*>',
    re.I,
)
REDIRECT_RE = re.compile(
    r'<meta\b(?=[^>]*\bhttp-equiv=["\']refresh["\'])[^>]*>',
    re.I,
)


def sitemap_urls() -> list[str]:
    urls: list[str] = []
    for relative in ("sitemap.xml", "sitemap-es.xml"):
        root = ET.parse(ROOT / relative).getroot()
        urls.extend(
            (node.text or "").strip()
            for node in root.findall("{*}url/{*}loc")
            if (node.text or "").strip()
        )
    return urls


def route(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path or "/"


def route_file(path: str) -> Path | None:
    relative = path.lstrip("/")
    candidates = [ROOT / "index.html"] if not relative else []
    if relative:
        if relative.endswith(".html"):
            candidates.append(ROOT / relative)
        else:
            candidates.extend(
                [ROOT / f"{relative}.html", ROOT / relative / "index.html"]
            )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


class CanonicalInternalLinkTargetTests(unittest.TestCase):
    def test_sitemap_pages_do_not_link_to_quarantined_or_redirect_fallbacks(self) -> None:
        violations: set[tuple[str, str]] = set()
        for source_url in sitemap_urls():
            source_file = route_file(route(source_url))
            self.assertIsNotNone(source_file, source_url)
            source = source_file.read_text(encoding="utf-8")
            for raw_href in HREF_RE.findall(source):
                href = html.unescape(raw_href.strip())
                if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                    continue
                target_url = urljoin(source_url, href)
                parsed = urlparse(target_url)
                if parsed.netloc.casefold() not in SITE_HOSTS:
                    continue
                target_route = route(target_url)
                if target_route in ALLOWED_NOINDEX_TARGETS:
                    continue
                target_file = route_file(target_route)
                if target_file is None:
                    suffix = Path(parsed.path).suffix.casefold()
                    if suffix not in NON_DOCUMENT_SUFFIXES:
                        violations.add((route(source_url), target_route))
                    continue
                target = target_file.read_text(encoding="utf-8")
                if NOINDEX_RE.search(target) or REDIRECT_RE.search(target):
                    violations.add((route(source_url), target_route))

        self.assertEqual(
            [],
            [f"{source} -> {target}" for source, target in sorted(violations)],
        )


if __name__ == "__main__":
    unittest.main()
