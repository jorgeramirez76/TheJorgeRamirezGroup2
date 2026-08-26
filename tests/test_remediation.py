#!/usr/bin/env python3
"""Regression tests for the August 2026 SEO/GEO remediation.

These tests intentionally exercise rendered-source outcomes instead of the
implementation scripts that produce them. They protect the public contract:
working conversion paths, coherent canonical/international signals, accurate
business entities, and accessible page structure.
"""

from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://thejorgeramirezgroup.com"
SKIP_DIRS = {".git", "crm", "node_modules", "property-leads-system"}
SUMMIT_LAT = 40.7157
SUMMIT_LON = -74.3601


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def public_html() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*.html")
        if not any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts)
    ]


def robots_noindex(text: str) -> bool:
    tag = re.search(r'<meta\s+[^>]*name=["\']robots["\'][^>]*>', text, re.I)
    return bool(tag and re.search(r'content=["\'][^"\']*noindex', tag.group(0), re.I))


def is_redirect_stub(text: str) -> bool:
    return bool(re.search(r'<meta\s+[^>]*http-equiv=["\']refresh["\']', text, re.I))


def canonical_url(text: str) -> str | None:
    match = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*>', text, re.I)
    if not match:
        return None
    href = re.search(r'href=["\']([^"\']+)', match.group(0), re.I)
    return href.group(1) if href else None


def hreflang_urls(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for tag in re.findall(r'<link\s+[^>]*hreflang=["\'][^"\']+["\'][^>]*>', text, re.I):
        language = re.search(r'hreflang=["\']([^"\']+)', tag, re.I)
        href = re.search(r'href=["\']([^"\']+)', tag, re.I)
        if language and href:
            result[language.group(1).lower()] = href.group(1)
    return result


def url_to_local_file(url: str) -> Path | None:
    split = urlsplit(url)
    if split.netloc and split.netloc not in {"thejorgeramirezgroup.com", "www.thejorgeramirezgroup.com"}:
        return None
    path = split.path.strip("/")
    if not path:
        candidates = [ROOT / "index.html"]
    else:
        if path.endswith(".html"):
            candidates = [ROOT / path]
        else:
            candidates = [ROOT / f"{path}.html", ROOT / path / "index.html", ROOT / path]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def jsonld_nodes(text: str):
    def walk(value):
        if isinstance(value, dict):
            yield value
            for nested in value.values():
                yield from walk(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from walk(nested)

    for raw in re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', text, re.I | re.S):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        yield from walk(payload)


def sitemap_documents() -> list[Path]:
    entry = ROOT / "sitemap-index.xml"
    if not entry.exists():
        return [ROOT / "sitemap.xml", ROOT / "sitemap-es.xml"]

    found: list[Path] = []
    queue = [entry]
    seen: set[Path] = set()
    while queue:
        document = queue.pop()
        if document in seen or not document.exists():
            continue
        seen.add(document)
        tree = ET.parse(document)
        root = tree.getroot()
        if root.tag.endswith("sitemapindex"):
            for loc in root.findall("{*}sitemap/{*}loc"):
                local = url_to_local_file(loc.text or "")
                if local and local.suffix == ".xml":
                    queue.append(local)
        else:
            found.append(document)
    return sorted(found)


def sitemap_urls() -> set[str]:
    urls: set[str] = set()
    for document in sitemap_documents():
        root = ET.parse(document).getroot()
        urls.update((loc.text or "").strip() for loc in root.findall("{*}url/{*}loc"))
    return {url for url in urls if url}


def deployed_path(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[: -len("/index.html")]
    return "/" + relative[:-5]


def exact_redirect_sources() -> set[str]:
    config = json.loads(read(ROOT / "vercel.json"))
    return {
        item["source"]
        for item in config.get("redirects", [])
        if not item.get("has") and ":" not in item.get("source", "")
    }


class RemediationContractTests(unittest.TestCase):
    maxDiff = None

    def test_dead_valuation_subdomain_is_not_referenced(self):
        offenders = [
            str(path.relative_to(ROOT))
            for path in public_html()
            if "value.thejorgeramirezgroup.com" in read(path)
        ]
        self.assertEqual([], offenders)

    def test_home_valuation_has_a_first_party_intake(self):
        text = read(ROOT / "home-valuation.html")
        self.assertRegex(text, r'<form\b[^>]*(?:action=["\']/api/lead["\']|id=["\'][^"\']*valuation)')
        self.assertNotIn("value.thejorgeramirezgroup.com", text)
        self.assertRegex(text, r'(?:success|thank-you)', "A visible or scripted success state is required")

    def test_homepage_has_real_main_landmark_and_skip_target(self):
        text = read(ROOT / "index.html")
        self.assertRegex(text, r'<a[^>]+href=["\']#main["\'][^>]*>')
        self.assertEqual(1, len(re.findall(r'<main\b[^>]*\bid=["\']main["\']', text, re.I)))

    def test_every_canonical_town_page_has_main_landmark(self):
        missing = []
        for path in sorted((ROOT / "towns").glob("*.html")):
            text = read(path)
            if robots_noindex(text) or is_redirect_stub(text):
                continue
            if not re.search(r'<main\b|role=["\']main["\']', text, re.I):
                missing.append(path.name)
        self.assertEqual([], missing)

    def test_mobile_hero_video_is_not_preloaded_automatically(self):
        text = read(ROOT / "index.html")
        script = read(ROOT / "js" / "main.js")
        for tag in re.findall(r'<video\b[^>]*>', text, re.I):
            self.assertNotRegex(tag, r'preload=["\']auto["\']')
        self.assertNotRegex(text, r'<video\b[^>]*\bautoplay\b', "Large hero video must not autoplay unconditionally")
        self.assertNotRegex(script, r'\.preload\s*=\s*["\']auto["\']')

    def test_indexable_canonicals_use_https_apex_clean_urls(self):
        bad = []
        for path in public_html():
            text = read(path)
            if robots_noindex(text) or is_redirect_stub(text):
                continue
            canonical = canonical_url(text)
            if not canonical:
                continue
            split = urlsplit(canonical)
            if split.scheme != "https" or split.netloc != "thejorgeramirezgroup.com" or split.path.endswith(".html"):
                bad.append((str(path.relative_to(ROOT)), canonical))
        self.assertEqual([], bad)

    def test_sitemaps_list_only_existing_indexable_clean_canonicals(self):
        bad = []
        for url in sorted(sitemap_urls()):
            local = url_to_local_file(url)
            if urlsplit(url).netloc != "thejorgeramirezgroup.com" or urlsplit(url).path.endswith(".html"):
                bad.append((url, "not clean apex URL"))
                continue
            if not local:
                bad.append((url, "missing local destination"))
                continue
            text = read(local)
            if robots_noindex(text) or is_redirect_stub(text):
                bad.append((url, "noindex/redirect destination"))
                continue
            canonical = canonical_url(text)
            if canonical and canonical.rstrip("/") != url.rstrip("/"):
                bad.append((url, f"canonical is {canonical}"))
        self.assertEqual([], bad)

    def test_sitemap_hreflang_alternates_only_reference_indexable_canonicals(self):
        bad = []
        for document in sitemap_documents():
            root = ET.parse(document).getroot()
            for link in root.findall("{*}url/{*}link"):
                url = (link.attrib.get("href") or "").strip()
                language = (link.attrib.get("hreflang") or "").strip()
                local = url_to_local_file(url)
                if not url or not local:
                    bad.append((document.name, language, url, "missing local destination"))
                    continue
                text = read(local)
                if robots_noindex(text) or is_redirect_stub(text):
                    bad.append((document.name, language, url, "noindex/redirect destination"))
                    continue
                canonical = canonical_url(text)
                if canonical and canonical.rstrip("/") != url.rstrip("/"):
                    bad.append((document.name, language, url, f"canonical is {canonical}"))
        self.assertEqual([], bad)

    def test_hreflang_targets_exist_and_are_reciprocal(self):
        bad = []
        submitted = {url.rstrip("/") for url in sitemap_urls()}
        redirected = exact_redirect_sources()
        for source in public_html():
            source_text = read(source)
            if (
                robots_noindex(source_text)
                or is_redirect_stub(source_text)
                or deployed_path(source) in redirected
            ):
                continue
            source_canonical = canonical_url(source_text)
            if not source_canonical or source_canonical.rstrip("/") not in submitted:
                continue
            alternates = hreflang_urls(source_text)
            for language, target_url in alternates.items():
                if language == "x-default":
                    continue
                if target_url.rstrip("/") not in submitted:
                    bad.append((str(source.relative_to(ROOT)), language, target_url, "not submitted"))
                    continue
                target = url_to_local_file(target_url)
                if not target:
                    bad.append((str(source.relative_to(ROOT)), language, target_url, "missing"))
                    continue
                target_text = read(target)
                if robots_noindex(target_text) or is_redirect_stub(target_text):
                    bad.append((str(source.relative_to(ROOT)), language, target_url, "not indexable"))
                    continue
                if source_canonical:
                    reciprocal = {url.rstrip("/") for url in hreflang_urls(target_text).values()}
                    if source_canonical.rstrip("/") not in reciprocal:
                        bad.append((str(source.relative_to(ROOT)), language, target_url, "not reciprocal"))
        self.assertEqual([], bad)

    def test_no_malformed_language_or_template_paths_remain(self):
        pattern = re.compile(r'(?:/es/(?:blog|towns)/es/|/(?:blog|towns)/es/|\$\{s\.slug\})')
        offenders = []
        for path in [*public_html(), *ROOT.glob("*.xml"), *ROOT.glob("*.js")]:
            if pattern.search(read(path)):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)

    def test_summit_business_address_never_uses_target_town_coordinates(self):
        bad = []
        for path in sorted((ROOT / "towns").glob("*.html")):
            for node in jsonld_nodes(read(path)):
                address = node.get("address")
                if not isinstance(address, dict) or not str(address.get("streetAddress", "")).startswith("488 Springfield"):
                    continue
                geo = node.get("geo")
                if not isinstance(geo, dict):
                    continue
                try:
                    lat = float(geo.get("latitude"))
                    lon = float(geo.get("longitude"))
                except (TypeError, ValueError):
                    bad.append((path.name, geo))
                    continue
                if abs(lat - SUMMIT_LAT) > 0.001 or abs(lon - SUMMIT_LON) > 0.001:
                    bad.append((path.name, geo))
        self.assertEqual([], bad)

    def test_communities_hub_matches_canonical_town_inventory(self):
        text = read(ROOT / "communities" / "index.html")
        linked = {
            re.sub(r'\.html$', '', href.split("#", 1)[0].split("?", 1)[0]).rstrip("/")
            for href in re.findall(r'href=["\'](/towns/[^"\']+)', text, re.I)
        }
        submitted = {
            urlsplit(url).path.rstrip("/")
            for url in sitemap_urls()
            if urlsplit(url).path.startswith("/towns/")
        }
        self.assertEqual(submitted, linked)
        claim = re.search(r'\b(\d+)\s+(?:NJ\s+)?Communit(?:y|ies)\b', text, re.I)
        self.assertIsNotNone(claim, "Communities hub needs a visible inventory count")
        self.assertEqual(len(linked), int(claim.group(1)))

    def test_verified_entity_and_experience_errors_are_removed(self):
        forbidden = {
            "Summit (Morris County)": [],
            "500 E Clay Ave": [],
            "© 2©": [],
        }
        experience = (
            re.compile(
                r"\b(?:after|in|based on)\s+(?:15|fifteen)\+?\s+years?\s+(?:of\s+)?"
                r"(?:selling|listing|showing|walking|helping|working|real estate|transactions?|closings?)",
                re.I,
            ),
            re.compile(
                r"\bI(?:'ve| have)\s+(?:been|spent|worked|helped|sold|walked|listed|managed)"
                r"[^.!?]{0,160}\b(?:for|over|in)\s+(?:15|fifteen)\+?\s+years?\b",
                re.I,
            ),
            re.compile(
                r"\b(?:15|fifteen)\+?\s+years?\s+(?:of\s+)?"
                r"(?:selling|listing|showing|real estate|experience|helping|working|walking|pre-listing)",
                re.I,
            ),
        )
        experience_offenders = []
        for path in public_html():
            text = read(path)
            for phrase in forbidden:
                if phrase in text:
                    forbidden[phrase].append(str(path.relative_to(ROOT)))
            if any(pattern.search(text) for pattern in experience):
                experience_offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual({key: [] for key in forbidden}, forbidden)
        self.assertEqual([], experience_offenders)

    def test_known_broken_spanish_article_is_quarantined(self):
        text = read(ROOT / "es" / "blog" / "buying-home-millburn-nj-2026.html")
        self.assertTrue(robots_noindex(text))

    def test_self_authored_best_agent_pages_are_not_independent_rankings(self):
        bad = []
        for path in sorted(ROOT.glob("best-real-estate-agents-*-county-nj-2026.html")):
            text = read(path)
            transparent = "methodology" in text.lower() and "disclosure" in text.lower()
            if not robots_noindex(text) and not transparent:
                bad.append(path.name)
        self.assertEqual([], bad)

    def test_homepage_schema_has_unique_entities_and_no_false_breadcrumb(self):
        text = read(ROOT / "index.html")
        ids = [node["@id"] for node in jsonld_nodes(text) if isinstance(node.get("@id"), str)]
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        self.assertEqual([], duplicates)
        for node in jsonld_nodes(text):
            node_type = node.get("@type")
            if node_type == "BreadcrumbList":
                labels = [str(item.get("name", "")) for item in node.get("itemListElement", []) if isinstance(item, dict)]
                self.assertNotIn("Communities", labels)
            if node_type in {"LocalBusiness", "RealEstateAgent"}:
                self.assertNotIn("aggregateRating", node)

    def test_summit_current_listings_claim_is_backed_by_listings(self):
        path = ROOT / "summit-nj-homes-for-sale.html"
        text = read(path)
        title = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
        claims_current = bool(title and "current listings" in title.group(1).lower())
        has_feed = bool(re.search(r'\b(?:idx|mls-listing|listing-feed)\b|<iframe\b', text, re.I))
        self.assertFalse(claims_current and not has_feed)

    def test_homepage_has_no_off_topic_civic_project_link(self):
        self.assertNotIn("bongholeo.com", read(ROOT / "index.html").lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
