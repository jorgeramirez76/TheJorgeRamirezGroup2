#!/usr/bin/env python3
"""Fail-closed technical, accessibility, asset, and link contract for sitemaps."""

from __future__ import annotations

import json
import posixpath
import re
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
SITEMAPS = ("sitemap.xml", "sitemap-es.xml")
IGNORED_SCHEMES = {"mailto", "tel", "sms", "data"}


def sitemap_urls() -> list[str]:
    return [
        (node.text or "").strip()
        for filename in SITEMAPS
        for node in ET.parse(ROOT / filename).getroot().findall("{*}url/{*}loc")
    ]


def public_path(url: str) -> str:
    return urlsplit(url).path.rstrip("/") or "/"


def page_file(route: str) -> Path | None:
    path = urlsplit(route).path
    relative = path.strip("/")
    candidates = [ROOT / "index.html"] if not relative else [
        ROOT / f"{relative}.html",
        ROOT / relative / "index.html",
        ROOT / relative,
    ]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.images: list[dict[str, str]] = []
        self.assets: list[tuple[str, str]] = []
        self.headings: list[int] = []
        self.landmarks = 0
        self.skip_hrefs: list[str] = []
        self.iframes: list[dict[str, str]] = []
        self.title_count = 0
        self.title_parts: list[str] = []
        self._in_title = False
        self.descriptions: list[str] = []
        self.canonicals: list[str] = []
        self.html_lang: list[str] = []
        self.viewport_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        present = {key.lower() for key, _ in attrs}
        values = {key.lower(): value or "" for key, value in attrs}
        values["_present"] = " ".join(sorted(present))
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "html":
            self.html_lang.append(values.get("lang", ""))
        if tag == "title":
            self.title_count += 1
            self._in_title = True
        if tag == "meta":
            if values.get("name", "").casefold() == "description":
                self.descriptions.append(values.get("content", "").strip())
            if values.get("name", "").casefold() == "viewport":
                self.viewport_count += 1
        if tag == "link":
            rel = values.get("rel", "").casefold().split()
            if "canonical" in rel:
                self.canonicals.append(values.get("href", ""))
            if any(token in rel for token in ("stylesheet", "icon", "preload")):
                if values.get("href"):
                    self.assets.append(("link", values["href"]))
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"])
            if "skip" in values.get("class", "").casefold():
                self.skip_hrefs.append(values["href"])
        if tag == "img":
            self.images.append(values)
        if tag == "iframe":
            self.iframes.append(values)
        if tag == "main" or values.get("role", "").casefold() == "main":
            self.landmarks += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag in {"img", "script", "source", "video", "audio", "iframe"}:
            if values.get("src"):
                self.assets.append((tag, values["src"]))
        if tag in {"img", "source"} and values.get("srcset"):
            for candidate in values["srcset"].split(","):
                asset = candidate.strip().split()[0]
                if asset:
                    self.assets.append((f"{tag}-srcset", asset))
        if tag == "video" and values.get("poster"):
            self.assets.append(("video-poster", values["poster"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def parse(path: Path) -> SurfaceParser:
    parser = SurfaceParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser


def resolve_route(current: str, href: str) -> str | None:
    parsed = urlsplit(href)
    if parsed.scheme in IGNORED_SCHEMES or href.startswith("//"):
        return None
    if parsed.scheme:
        if parsed.scheme != "https" or parsed.netloc not in {
            "thejorgeramirezgroup.com",
            "www.thejorgeramirezgroup.com",
        }:
            return None
        path = parsed.path
    else:
        path = parsed.path
    if not path:
        return current
    if not path.startswith("/"):
        path = posixpath.normpath(posixpath.join(posixpath.dirname(current), path))
        if not path.startswith("/"):
            path = "/" + path
    return path.rstrip("/") or "/"


class FullSurfaceTechnicalContractTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.urls = sitemap_urls()
        cls.pages: dict[str, tuple[Path, SurfaceParser]] = {}
        for url in cls.urls:
            route = public_path(url)
            path = page_file(route)
            if path is not None:
                cls.pages[route] = (path, parse(path))
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        cls.config = config
        cls.redirects = {
            str(item.get("source")): str(item.get("destination"))
            for item in config["redirects"]
            if not item.get("has")
            and not any(mark in str(item.get("source", "")) for mark in (":", "*", "("))
        }

    def test_sitemaps_have_exactly_285_unique_resolvable_canonical_pages(self) -> None:
        self.assertEqual(285, len(self.urls))
        self.assertEqual(len(self.urls), len(set(self.urls)))
        self.assertEqual({public_path(url) for url in self.urls}, set(self.pages))
        for url in self.urls:
            parsed = urlsplit(url)
            self.assertEqual("https", parsed.scheme, url)
            self.assertEqual("thejorgeramirezgroup.com", parsed.netloc, url)
            self.assertFalse(parsed.path.endswith(".html"), url)

    def test_metadata_headings_landmarks_and_skip_targets_are_well_formed(self) -> None:
        titles: dict[str, str] = {}
        descriptions: dict[str, str] = {}
        failures: list[str] = []
        for route, (path, parser) in sorted(self.pages.items()):
            relative = path.relative_to(ROOT).as_posix()
            if parser.title_count != 1 or not parser.title:
                failures.append(f"{relative}: title count/content")
            if len(parser.descriptions) != 1 or not parser.descriptions[0]:
                failures.append(f"{relative}: description count/content")
            if len(parser.canonicals) != 1:
                failures.append(f"{relative}: canonical count {len(parser.canonicals)}")
            elif public_path(parser.canonicals[0]) != route:
                failures.append(f"{relative}: canonical mismatch {parser.canonicals[0]}")
            if len(parser.html_lang) != 1 or not parser.html_lang[0]:
                failures.append(f"{relative}: missing document language")
            if parser.viewport_count != 1:
                failures.append(f"{relative}: viewport count {parser.viewport_count}")
            if parser.headings.count(1) != 1:
                failures.append(f"{relative}: h1 count {parser.headings.count(1)}")
            for previous, current in zip(parser.headings, parser.headings[1:]):
                if current > previous + 1:
                    failures.append(f"{relative}: heading skip h{previous} to h{current}")
                    break
            if parser.landmarks != 1:
                failures.append(f"{relative}: main landmark count {parser.landmarks}")
            duplicate_ids = sorted(key for key, count in Counter(parser.ids).items() if count > 1)
            if duplicate_ids:
                failures.append(f"{relative}: duplicate ids {duplicate_ids}")
            for href in parser.skip_hrefs:
                fragment = unquote(urlsplit(href).fragment)
                if not fragment or fragment not in parser.ids:
                    failures.append(f"{relative}: unresolved skip link {href}")
            for iframe in parser.iframes:
                if not iframe.get("title", "").strip():
                    failures.append(f"{relative}: iframe lacks title {iframe.get('src')}")
            titles[route] = parser.title.casefold()
            descriptions[route] = parser.descriptions[0].casefold() if parser.descriptions else ""
        duplicate_titles = [value for value, count in Counter(titles.values()).items() if count > 1]
        duplicate_descriptions = [
            value for value, count in Counter(descriptions.values()).items() if count > 1
        ]
        self.assertEqual([], duplicate_titles, "duplicate canonical titles")
        self.assertEqual([], duplicate_descriptions, "duplicate canonical descriptions")
        self.assertEqual([], failures)

    def test_canonical_images_are_local_sized_and_layout_stable(self) -> None:
        failures: list[str] = []
        for route, (path, parser) in sorted(self.pages.items()):
            relative = path.relative_to(ROOT).as_posix()
            for image in parser.images:
                present = set(image.get("_present", "").split())
                src = image.get("src", "")
                if "alt" not in present:
                    failures.append(f"{relative}: image lacks alt: {src}")
                for dimension in ("width", "height"):
                    if not re.fullmatch(r"[1-9][0-9]*", image.get(dimension, "")):
                        failures.append(f"{relative}: image lacks numeric {dimension}: {src}")
                parsed = urlsplit(src)
                if parsed.scheme and parsed.netloc not in {
                    "thejorgeramirezgroup.com",
                    "www.thejorgeramirezgroup.com",
                }:
                    failures.append(f"{relative}: remote runtime image: {src}")
        self.assertEqual([], failures)

    def test_internal_links_assets_fragments_and_orphan_graph_resolve(self) -> None:
        failures: list[str] = []
        incoming = {route: 0 for route in self.pages}
        parser_cache: dict[Path, SurfaceParser] = {}
        for route, (path, parser) in sorted(self.pages.items()):
            relative = path.relative_to(ROOT).as_posix()
            for raw in parser.hrefs:
                target_route = resolve_route(route, raw)
                if target_route is None:
                    continue
                target = page_file(target_route)
                if target is None and target_route not in self.redirects:
                    failures.append(f"{relative}: unresolved link {raw}")
                    continue
                if target_route in incoming and target_route != route:
                    incoming[target_route] += 1
                fragment = unquote(urlsplit(raw).fragment)
                if fragment and target is not None:
                    target_parser = parser_cache.setdefault(target, parse(target))
                    if fragment not in target_parser.ids:
                        failures.append(f"{relative}: unresolved fragment {raw}")
            for kind, raw in parser.assets:
                parsed = urlsplit(raw)
                if parsed.scheme in {"http", "https"}:
                    if parsed.netloc not in {
                        "thejorgeramirezgroup.com",
                        "www.thejorgeramirezgroup.com",
                    }:
                        continue
                    asset_path = ROOT / parsed.path.lstrip("/")
                elif parsed.scheme or raw.startswith("//"):
                    continue
                elif parsed.path.startswith("/"):
                    asset_path = ROOT / parsed.path.lstrip("/")
                else:
                    asset_path = path.parent / parsed.path
                if parsed.path and not asset_path.is_file():
                    failures.append(f"{relative}: missing {kind} asset {raw}")
        orphans = sorted(route for route, count in incoming.items() if count == 0)
        self.assertEqual([], orphans, "canonical sitemap pages without an inbound canonical link")
        self.assertEqual([], failures)

    def test_runtime_images_and_homepage_loading_are_first_party_and_bounded(self) -> None:
        forbidden = "images.unsplash.com"
        source_files = [ROOT / "js" / "main.js", ROOT / "tools" / "blog-automation" / "daily_blog.py"]
        source_files.extend(path for path, _ in self.pages.values())
        source_files.extend((ROOT / "css").glob("*.css"))
        for path in source_files:
            self.assertNotIn(forbidden, path.read_text(encoding="utf-8", errors="ignore"), path)

        optimized = {
            "images/blog-hero/value-2026-1280.webp": 250_000,
            "images/blog-hero/commute-2026-1280.webp": 150_000,
            "images/blog-hero/families-2026-1280.webp": 150_000,
            "images/blog-hero/decluttering-living-room-768.webp": 100_000,
        }
        for relative, maximum in optimized.items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertLess(path.stat().st_size, maximum, relative)
        for path in (ROOT / "images" / "county-cards").glob("*.webp"):
            self.assertLess(path.stat().st_size, 60_000, path.name)
        self.assertEqual(6, len(list((ROOT / "images" / "county-cards").glob("*.webp"))))

        legacy_body_images = {
            "/images/blog-hero/value-2026.jpg",
            "/images/blog-hero/commute-2026.jpg",
            "/images/blog-hero/families-2026.jpg",
        }
        for path, parser in self.pages.values():
            used = {image.get("src", "") for image in parser.images}
            used.update(raw for kind, raw in parser.assets if "srcset" in kind)
            self.assertTrue(legacy_body_images.isdisjoint(used), path)
        css = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "css").glob("*.css"))
        for image in legacy_body_images:
            self.assertNotIn(image, css)

        main_js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
        self.assertNotIn("cdn.jsdelivr.net/npm/lenis", main_js)
        self.assertIn("navigator.connection", main_js)
        self.assertIn("prefers-reduced-motion: reduce", main_js)
        self.assertIn("requestIdleCallback", main_js)
        self.assertIn("county-hero-photo[data-bg]", main_js)
        self.assertIn(".reveal-tile[data-reveal-img]", main_js)
        self.assertIn(".listing-img[data-listing-img]", main_js)
        self.assertNotRegex(main_js, r"slides\.forEach\([^)]*loadSlide")
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("lenis.min.js", homepage)
        self.assertNotIn("enhance.js", homepage)
        self.assertNotIn("--reveal-img: url(", homepage)
        self.assertNotIn('class="listing-img" style="background-image:', homepage)

    def test_baseline_security_and_cache_headers_remain_enabled(self) -> None:
        global_rule = next(item for item in self.config["headers"] if item["source"] == "/(.*)")
        headers = {item["key"].casefold(): item["value"] for item in global_rule["headers"]}
        self.assertEqual("nosniff", headers["x-content-type-options"])
        self.assertEqual("SAMEORIGIN", headers["x-frame-options"])
        self.assertEqual("strict-origin-when-cross-origin", headers["referrer-policy"])
        self.assertIn("max-age=31536000", headers["strict-transport-security"])
        self.assertEqual("geolocation=(), microphone=(), camera=()", headers["permissions-policy"])
        asset_rules = [
            item for item in self.config["headers"]
            if item["source"].startswith("/(.*)\\.(webp")
        ]
        self.assertEqual(1, len(asset_rules))
        self.assertIn("immutable", asset_rules[0]["headers"][0]["value"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
