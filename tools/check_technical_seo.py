#!/usr/bin/env python3
"""Regression checks for canonical URLs, hreflang, sitemaps, and town schema.

The site is deployed by Vercel with clean URLs. These checks model that public
surface rather than treating ``.html`` file names as indexable URLs.
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://thejorgeramirezgroup.com"
EXPECTED_OFFICE_GEO = (40.7157, -74.3601)
SKIP_DIRS = {
    ".git",
    "node_modules",
    "crm",
    "docs",
    "property-leads-system",
    "staging",
}
SITEMAP_NS = {
    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "x": "http://www.w3.org/1999/xhtml",
}
AREA_SERVED_TOWNS = {
    "basking-ridge.html": "Basking Ridge",
    "bedminster.html": "Bedminster",
    "bernards-township.html": "Bernards Township",
    "bernardsville.html": "Bernardsville",
    "bound-brook.html": "Bound Brook",
    "branchburg.html": "Branchburg",
    "bridgewater.html": "Bridgewater",
    "dover.html": "Dover",
    "far-hills.html": "Far Hills",
    "franklin-township.html": "Franklin Township",
    "green-brook.html": "Green Brook",
    "hillsborough.html": "Hillsborough",
    "kenilworth.html": "Kenilworth",
    "manville.html": "Manville",
    "metuchen.html": "Metuchen",
    "millstone.html": "Millstone",
    "montgomery.html": "Montgomery",
    "new-brunswick.html": "New Brunswick",
    "north-brunswick.html": "North Brunswick",
    "north-plainfield.html": "North Plainfield",
    "raritan.html": "Raritan",
    "rocky-hill.html": "Rocky Hill",
    "somerville.html": "Somerville",
    "south-bound-brook.html": "South Bound Brook",
    "washington-township-morris.html": "Washington Township",
}


class SeoParser(HTMLParser):
    """Collect SEO-relevant tags while naturally ignoring markup in scripts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.metas: list[dict[str, str]] = []
        self.anchors: list[dict[str, str]] = []
        self._open_anchors: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "link":
            self.links.append(values)
        elif tag == "meta":
            self.metas.append(values)
        elif tag == "a":
            values["_text"] = ""
            self.anchors.append(values)
            self._open_anchors.append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._open_anchors:
            self._open_anchors.pop()

    def handle_data(self, data: str) -> None:
        if self._open_anchors:
            self._open_anchors[-1]["_text"] += data


def deployed_path(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[: -len("/index.html")]
    return "/" + relative[:-5]


def normalized_path(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path or "/"


def normalized_url(url: str) -> str:
    return ORIGIN + normalized_path(url)


def is_apex_https(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc == "thejorgeramirezgroup.com"


def is_extensionless(url: str) -> bool:
    return not normalized_path(url).endswith(".html")


def requires_town_local_business(source: str) -> bool:
    """Return whether a town page should publish its full local-business graph.

    Compact town fallbacks are intentionally noindex and carry no rich-result
    schema. Requiring the normal town graph on those pages would undo that
    quarantine. Both the managed marker and the exact robots policy are needed
    so an arbitrary noindex page cannot bypass the full-guide regression check.
    """

    managed_fallback = bool(
        re.search(
            r'<body\b[^>]*\bdata-(?:noindex-town-fallback|spanish-town-fallback)=["\']v1["\']',
            source,
            re.IGNORECASE,
        )
    )
    noindex_follow = bool(
        re.search(
            r'<meta\b(?=[^>]*\bname=["\']robots["\'])'
            r'(?=[^>]*\bcontent=["\']\s*noindex\s*,\s*follow\s*["\'])[^>]*>',
            source,
            re.IGNORECASE,
        )
    )
    redirect_fallback = bool(
        re.search(
            r'<meta\b[^>]*\bhttp-equiv=["\']refresh["\']',
            source,
            re.IGNORECASE,
        )
    )
    return not (noindex_follow and (managed_fallback or redirect_fallback))


def json_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from json_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from json_nodes(child)


def json_ld_blocks(text: str) -> list[dict]:
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        text,
        re.IGNORECASE | re.DOTALL,
    )
    return [json.loads(block) for block in blocks]


def main() -> int:
    failures: list[str] = []

    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    redirects = config.get("redirects", [])
    exact_redirects = {
        item["source"]: item["destination"]
        for item in redirects
        if not item.get("has") and ":" not in item["source"]
    }

    pages: dict[str, dict] = {}
    pages_by_url: dict[str, list[dict]] = defaultdict(list)
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        parser = SeoParser()
        parser.feed(text)
        canonical_links = [
            link.get("href", "")
            for link in parser.links
            if "canonical" in link.get("rel", "").split()
        ]
        hreflang_links = [
            (link.get("hreflang", ""), link.get("href", ""))
            for link in parser.links
            if link.get("hreflang") and link.get("href")
        ]
        noindex = any(
            meta.get("name", "").lower() == "robots"
            and "noindex" in meta.get("content", "").lower()
            for meta in parser.metas
        )
        refresh = any(
            meta.get("http-equiv", "").lower() == "refresh" for meta in parser.metas
        )
        record = {
            "path": path,
            "url": deployed_path(path),
            "text": text,
            "canonical_links": canonical_links,
            "canonical": canonical_links[0] if len(canonical_links) == 1 else "",
            "hreflang": hreflang_links,
            "noindex": noindex,
            "refresh": refresh,
            "anchors": parser.anchors,
        }
        relative = path.relative_to(ROOT).as_posix()
        pages[relative] = record
        pages_by_url[record["url"]].append(record)

    def is_indexable(record: dict) -> bool:
        return not record["noindex"] and not record["refresh"] and record["url"] not in exact_redirects

    def is_canonical_page(record: dict) -> bool:
        return (
            is_indexable(record)
            and len(record["canonical_links"]) == 1
            and normalized_path(record["canonical"]) == record["url"]
        )

    def canonical_pages_for(url: str) -> list[dict]:
        return [
            record
            for record in pages_by_url.get(normalized_path(url), [])
            if is_canonical_page(record)
        ]

    # Every JSON-LD block on the deployable surface must remain parseable,
    # not only the town-page business graphs checked later in this script.
    for relative, record in sorted(pages.items()):
        try:
            json_ld_blocks(record["text"])
        except json.JSONDecodeError as error:
            failures.append(f"{relative}: invalid JSON-LD: {error}")

    # Canonical URL format and resolvability.
    for relative, record in sorted(pages.items()):
        if len(record["canonical_links"]) != 1:
            failures.append(
                f"{relative}: expected one canonical, found {len(record['canonical_links'])}"
            )
            continue
        canonical = record["canonical"]
        if not is_apex_https(canonical):
            failures.append(f"{relative}: canonical is not HTTPS apex: {canonical}")
        if not is_extensionless(canonical):
            failures.append(f"{relative}: canonical contains .html: {canonical}")
        if re.search(r"/es/(?:es/)+", normalized_path(canonical)):
            failures.append(f"{relative}: canonical repeats language segment: {canonical}")
        if is_indexable(record) and not canonical_pages_for(canonical):
            failures.append(f"{relative}: canonical target is not an indexable canonical page: {canonical}")

    # Live canonical pages may advertise only real, reciprocal language pages.
    for relative, record in sorted(pages.items()):
        if not is_canonical_page(record):
            continue
        source = normalized_url(record["canonical"])
        languages = Counter(language for language, _ in record["hreflang"])
        for language, count in languages.items():
            if count > 1:
                failures.append(f"{relative}: duplicate hreflang {language} ({count})")
        for language, href in record["hreflang"]:
            if not is_apex_https(href):
                failures.append(f"{relative}: hreflang is not HTTPS apex: {href}")
                continue
            if not is_extensionless(href):
                failures.append(f"{relative}: hreflang contains .html: {href}")
            target_path = normalized_path(href)
            if re.search(r"/es/(?:es/)+", target_path):
                failures.append(f"{relative}: hreflang repeats language segment: {href}")
            if language in {"es", "es-US"} and not target_path.startswith("/es/") and target_path != "/es":
                failures.append(f"{relative}: {language} points outside /es: {href}")
            if language == "en-US" and (target_path.startswith("/es/") or target_path == "/es"):
                failures.append(f"{relative}: en-US points into /es: {href}")
            targets = canonical_pages_for(href)
            if not targets:
                failures.append(f"{relative}: hreflang target is not indexable/canonical: {href}")
                continue
            if not any(
                source in {normalized_url(value) for _, value in target["hreflang"]}
                for target in targets
            ):
                failures.append(f"{relative}: hreflang is not reciprocal with {href}")

    # Internal navigation should go straight to clean URLs. Conversion CTAs are
    # intentionally excluded because they are owned by a separate workstream.
    for relative, record in sorted(pages.items()):
        if relative in {"index.html", "home-valuation.html"}:
            continue
        for anchor in record["anchors"]:
            href = anchor.get("href", "")
            parsed_href = urlparse(href)
            if parsed_href.netloc and parsed_href.netloc != "thejorgeramirezgroup.com":
                continue
            classes = anchor.get("class", "").lower()
            text = " ".join(anchor.get("_text", "").lower().split())
            if any(token in classes for token in ("cta", "btn", "button")) or text.startswith("read more"):
                continue
            if normalized_path(href).endswith(".html"):
                failures.append(f"{relative}: internal link uses .html: {href}")

    placeholder_pattern = re.compile(r"href\s*=\s*[\"\'][^\"\']*\$\{[^\"\']+[\"\']")
    for relative, record in sorted(pages.items()):
        if placeholder_pattern.search(record["text"]):
            failures.append(f"{relative}: href contains a literal template placeholder")

    expected_train_routes = {
        "nj-train-map.html": "'/towns/' + encodeURIComponent(slug)",
        "es/nj-train-map.html": "'/es/towns/' + encodeURIComponent(slug)",
    }
    for relative, expression in expected_train_routes.items():
        if expression not in pages[relative]["text"]:
            failures.append(f"{relative}: generated town route must use {expression}")

    # Static redirect fallbacks should also avoid an extra clean-URL hop.
    for stub in sorted((ROOT / "communities").glob("*/index.html")):
        text = stub.read_text(encoding="utf-8", errors="replace")
        if re.search(r"/towns/[a-z0-9-]+\.html", text):
            failures.append(
                f"{stub.relative_to(ROOT)}: redirect fallback targets a .html URL"
            )

    # Redirect policy: clean public URLs, permanent migrations, no exact chains,
    # and an explicit one-hop route for legacy /realtor/*.html requests.
    if config.get("cleanUrls") is not True or config.get("trailingSlash") is not False:
        failures.append("vercel.json: cleanUrls must be true and trailingSlash false")
    www_redirect = next(
        (
            item
            for item in redirects
            if any(
                condition.get("type") == "host"
                and condition.get("value") == "www.thejorgeramirezgroup.com"
                for condition in item.get("has", [])
            )
        ),
        None,
    )
    if not www_redirect or www_redirect.get("destination") != f"{ORIGIN}/:path*" or not www_redirect.get("permanent"):
        failures.append("vercel.json: www must permanently redirect to the HTTPS apex")
    for item in redirects:
        if not item.get("permanent"):
            failures.append(f"vercel.json: redirect is not permanent: {item.get('source')}")
        destination = item.get("destination", "")
        parsed_destination = urlparse(destination)
        is_local_destination = not parsed_destination.netloc or parsed_destination.netloc in {
            "thejorgeramirezgroup.com",
            "www.thejorgeramirezgroup.com",
        }
        if is_local_destination and normalized_path(destination).endswith(".html"):
            failures.append(
                f"vercel.json: redirect destination contains .html: {item.get('source')} -> {destination}"
            )
        if ":" not in destination and destination in exact_redirects:
            failures.append(
                f"vercel.json: exact redirect chain: {item.get('source')} -> {destination} -> {exact_redirects[destination]}"
            )
    realtor_html_redirect = next(
        (
            item
            for item in redirects
            if item.get("source") == "/realtor/:slug-nj.html"
        ),
        None,
    )
    if (
        not realtor_html_redirect
        or realtor_html_redirect.get("destination") != "/towns/:slug"
        or not realtor_html_redirect.get("permanent")
    ):
        failures.append(
            "vercel.json: /realtor/:slug-nj.html must redirect directly to /towns/:slug"
        )

    # Sitemap entries must be canonical/indexable and reciprocal within XML.
    sitemap_entries: dict[str, tuple[str, set[tuple[str, str]]]] = {}
    seen_sitemap_urls: set[str] = set()
    for sitemap_name in ("sitemap.xml", "sitemap-es.xml"):
        root = ET.parse(ROOT / sitemap_name).getroot()
        for url_element in root.findall("s:url", SITEMAP_NS):
            loc = url_element.findtext("s:loc", namespaces=SITEMAP_NS) or ""
            loc_key = normalized_url(loc)
            if loc_key in seen_sitemap_urls:
                failures.append(f"{sitemap_name}: duplicate sitemap URL: {loc}")
            seen_sitemap_urls.add(loc_key)
            if not is_apex_https(loc) or not is_extensionless(loc):
                failures.append(f"{sitemap_name}: loc is not a clean HTTPS apex URL: {loc}")
            if sitemap_name == "sitemap.xml" and normalized_path(loc).startswith("/es/"):
                failures.append(f"{sitemap_name}: Spanish URL is in English sitemap: {loc}")
            if sitemap_name == "sitemap-es.xml" and not (
                normalized_path(loc).startswith("/es/") or normalized_path(loc) == "/es"
            ):
                failures.append(f"{sitemap_name}: non-Spanish URL is in Spanish sitemap: {loc}")
            if not canonical_pages_for(loc):
                failures.append(f"{sitemap_name}: loc is not indexable/canonical: {loc}")
            alternates = {
                (
                    link.attrib.get("hreflang", ""),
                    normalized_url(link.attrib.get("href", "")),
                )
                for link in url_element.findall("x:link", SITEMAP_NS)
            }
            for language, href in alternates:
                if not is_apex_https(href) or not is_extensionless(href):
                    failures.append(
                        f"{sitemap_name}: {language} alternate is not a clean HTTPS apex URL: {href}"
                    )
                if not canonical_pages_for(href):
                    failures.append(
                        f"{sitemap_name}: {language} alternate is not indexable/canonical: {href}"
                    )
            sitemap_entries[loc_key] = (sitemap_name, alternates)

    for loc, (sitemap_name, alternates) in sorted(sitemap_entries.items()):
        for language, href in alternates:
            target = sitemap_entries.get(href)
            if not target:
                failures.append(
                    f"{sitemap_name}: {loc} alternate {language} is absent from sitemaps: {href}"
                )
                continue
            if loc not in {target_href for _, target_href in target[1]}:
                failures.append(
                    f"{sitemap_name}: {loc} and {href} are not reciprocal in sitemap hreflang"
                )

    # A self-canonical indexable page that is absent from both sitemaps is an
    # accidental discovery/indexing gap. Noindex and redirect fallbacks are
    # excluded by ``is_canonical_page`` above.
    for relative, record in sorted(pages.items()):
        if not is_canonical_page(record):
            continue
        canonical = normalized_url(record["canonical"])
        if canonical not in sitemap_entries:
            failures.append(f"{relative}: indexable canonical page is absent from sitemaps: {canonical}")

    # The index should advertise only the two language-segmented sitemaps.
    sitemap_index = ET.parse(ROOT / "sitemap-index.xml").getroot()
    indexed_sitemaps = {
        normalized_url(element.findtext("s:loc", namespaces=SITEMAP_NS) or "")
        for element in sitemap_index.findall("s:sitemap", SITEMAP_NS)
    }
    expected_sitemaps = {
        f"{ORIGIN}/sitemap.xml",
        f"{ORIGIN}/sitemap-es.xml",
    }
    if indexed_sitemaps != expected_sitemaps:
        failures.append(
            f"sitemap-index.xml: expected {sorted(expected_sitemaps)}, found {sorted(indexed_sitemaps)}"
        )

    # A Summit office address must never be paired with the served town's geo.
    for directory in (ROOT / "towns", ROOT / "es" / "towns"):
        for path in sorted(directory.glob("*.html")):
            relative = path.relative_to(ROOT).as_posix()
            source = path.read_text(encoding="utf-8")
            try:
                blocks = json_ld_blocks(source)
            except json.JSONDecodeError as error:
                failures.append(f"{relative}: invalid JSON-LD: {error}")
                continue
            nodes = [node for block in blocks for node in json_nodes(block)]
            office_nodes = []
            for node in nodes:
                address = node.get("address")
                if not isinstance(address, dict):
                    continue
                street = str(address.get("streetAddress", "")).lower()
                if address.get("addressLocality") != "Summit" or not street.startswith("488 springfield"):
                    continue
                office_nodes.append(node)
                geo = node.get("geo")
                if not isinstance(geo, dict):
                    continue
                try:
                    coordinates = (float(geo["latitude"]), float(geo["longitude"]))
                except (KeyError, TypeError, ValueError):
                    failures.append(f"{relative}: Summit office geo is malformed: {geo}")
                    continue
                if coordinates != EXPECTED_OFFICE_GEO:
                    failures.append(
                        f"{relative}: Summit office address has non-Summit geo {coordinates}"
                    )
            expected_town = AREA_SERVED_TOWNS.get(path.name)
            if expected_town and requires_town_local_business(source):
                matching_business = [
                    node
                    for node in office_nodes
                    if node.get("@type") == "LocalBusiness"
                    and isinstance(node.get("areaServed"), dict)
                    and node["areaServed"].get("name") == expected_town
                    and node["areaServed"].get("@type") in {"City", "Place", "AdministrativeArea"}
                ]
                if not matching_business:
                    failures.append(
                        f"{relative}: LocalBusiness must represent {expected_town} as areaServed"
                    )

    if failures:
        print(f"technical SEO regression check failed: {len(failures)} issue(s)")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print(
        "technical SEO regression check passed: "
        f"{len(pages)} HTML files, {len(sitemap_entries)} sitemap URLs"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
