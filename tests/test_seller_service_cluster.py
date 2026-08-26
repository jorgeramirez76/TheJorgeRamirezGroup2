#!/usr/bin/env python3
"""Regression contract for the bilingual seller-service cluster."""

from __future__ import annotations

import copy
import html
import importlib.util
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "seller-service-sources.json"
GENERATOR = ROOT / "tools" / "generate_seller_services.py"
SITE = "https://thejorgeramirezgroup.com"
SLUGS = {
    "sell-your-home",
    "how-we-sell-your-home",
    "expired-listing-help",
    "fsbo-help",
    "cash-offer-nj",
    "relocating-from-nj",
    "divorce-home-sale-nj",
    "sell-rental-property-nj",
}
SOURCE_IDS = {
    "nj-dobi-24-11",
    "nj-treasury-rtf",
    "nj-property-condition-disclosure",
    "njdep-flood-disclosure",
    "epa-lead-disclosure",
    "nj-dca-landlord-tenant",
    "irs-like-kind-exchanges",
    "irs-publication-544",
    "njcourts-divorce",
}
OFFICIAL_HOSTS = {
    "www.nj.gov",
    "nj.gov",
    "www.njconsumeraffairs.gov",
    "dep.nj.gov",
    "www.epa.gov",
    "www.irs.gov",
    "www.njcourts.gov",
}
PALETTE = {"#1A1A1A", "#C41230", "#8B0D22", "#B8962E", "#FAFAF8"}
RISKY_COPY = re.compile(
    r"AI[- ]powered|AI buyer|top dollar|maximum (?:value|exposure|price)|"
    r"sell(?:s|ing)? (?:homes? )?(?:faster|for more money)|"
    r"multiple offers|bidding war|guarantee|best possible|superior results|"
    r"available (?:seven|7) days|always responsive|hundreds of|5[- ]star|"
    r"qualified buyers|without leaving money on the table|"
    r"(?:top[- ]rated|best|great) schools?|family[- ]friendly|young families|"
    r"safe(?:st)? (?:town|community|neighbou?rhood)|perfect for|ideal for|"
    r"precio m[aá]ximo|m[aá]s r[aá]pido|por m[aá]s dinero|ofertas m[uú]ltiples|"
    r"garanti(?:zar|zado|zada)|siempre disponible|cientos de|"
    r"sin dejar dinero sobre la mesa|mejores? escuelas|ideal para familias",
    re.IGNORECASE,
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.hreflangs: list[tuple[str, str]] = []
        self.robots: list[str] = []
        self.links: list[str] = []
        self.ids: list[str] = []
        self.duplicate_attributes: list[str] = []
        self.stylesheets: list[str] = []
        self.h1_count = 0
        self.main_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        names = [name.lower() for name, _ in attrs]
        if len(names) != len(set(names)):
            self.duplicate_attributes.append(tag)
        values = {name.lower(): value or "" for name, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        if tag == "link" and values.get("hreflang"):
            self.hreflangs.append((values["hreflang"], values.get("href", "")))
        if tag == "link" and "stylesheet" in values.get("rel", "").split():
            self.stylesheets.append(values.get("href", ""))
        if tag == "meta" and values.get("name", "").lower() == "robots":
            self.robots.append(values.get("content", ""))
        if tag == "a":
            self.links.append(values.get("href", ""))
        if tag == "h1":
            self.h1_count += 1
        if tag == "main":
            self.main_count += 1


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def route(slug: str, language: str) -> str:
    return f"/{'es/' if language == 'es' else ''}{slug}"


def page_path(slug: str, language: str) -> Path:
    return ROOT / ("es" if language == "es" else "") / f"{slug}.html"


def parse(path: Path) -> tuple[str, PageParser]:
    source = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(source)
    return source, parser


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style|template|noscript)\b[^>]*>.*?</(?:script|style|template|noscript)>",
        " ",
        source,
        flags=re.IGNORECASE | re.DOTALL,
    )
    source = re.sub(r"<!--.*?-->|<[^>]+>", " ", source, flags=re.DOTALL)
    return " ".join(html.unescape(source).split())


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


def sitemap_urls(name: str) -> set[str]:
    root = ET.parse(ROOT / name).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


class SellerServiceClusterTests(unittest.TestCase):
    def test_manifest_is_exact_current_and_fail_closed(self) -> None:
        document = manifest()
        self.assertEqual(1, document["schemaVersion"])
        self.assertEqual("2026-08-26", document["reviewedOn"])
        self.assertEqual("tools/generate_seller_services.py", document["renderer"])
        self.assertEqual(SLUGS, {item["slug"] for item in document["routes"]})
        self.assertEqual(SOURCE_IDS, {item["id"] for item in document["sources"]})
        for item in document["sources"]:
            self.assertEqual("https", urlparse(item["url"]).scheme)
            self.assertIn(urlparse(item["url"]).netloc, OFFICIAL_HOSTS)
            self.assertTrue(item["use"])
            self.assertTrue(item["limit"])
            self.assertTrue(item["useEs"])
            self.assertTrue(item["limitEs"])
        for item in document["routes"]:
            self.assertTrue(set(item["sourceIds"]) <= SOURCE_IDS)
            self.assertGreaterEqual(len(item["sourceIds"]), 3)

        spec = importlib.util.spec_from_file_location("seller_generator", GENERATOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        broken = copy.deepcopy(document)
        broken["routes"] = broken["routes"][:-1]
        with self.assertRaises(ValueError):
            module.validate_manifest(broken)

    def test_all_sixteen_pages_are_indexable_branded_and_reciprocal(self) -> None:
        stylesheet = (ROOT / "css" / "seller-services.css").read_text(encoding="utf-8")
        for token in PALETTE:
            self.assertIn(token, stylesheet)
        for family in ("Playfair Display", "Inter"):
            self.assertIn(family, stylesheet)
        self.assertRegex(stylesheet, r"@media\s*\(max-width:\s*820px\)")
        self.assertRegex(stylesheet, r"min-height:\s*44px")
        self.assertIn(":focus-visible", stylesheet)

        routes = {item["slug"]: item for item in manifest()["routes"]}
        sources = {item["id"]: item for item in manifest()["sources"]}
        for slug in sorted(SLUGS):
            for language in ("en", "es"):
                path = page_path(slug, language)
                with self.subTest(path=path.relative_to(ROOT)):
                    source, parser = parse(path)
                    own = SITE + route(slug, language)
                    en = SITE + route(slug, "en")
                    es = SITE + route(slug, "es")
                    self.assertEqual([own], parser.canonicals)
                    self.assertIn(("en-US", en), parser.hreflangs)
                    self.assertIn(("es-US", es), parser.hreflangs)
                    self.assertIn(("es", es), parser.hreflangs)
                    self.assertIn(("x-default", en), parser.hreflangs)
                    self.assertTrue(any("index" in item.lower() for item in parser.robots))
                    self.assertEqual(1, parser.h1_count)
                    self.assertEqual(1, parser.main_count)
                    self.assertEqual([], parser.duplicate_attributes)
                    self.assertEqual(len(parser.ids), len(set(parser.ids)))
                    self.assertIn("/css/styles.css", parser.stylesheets)
                    self.assertIn("/css/seller-services.css", parser.stylesheets)
                    self.assertIn("/images/jorge-logo.jpg", source)
                    self.assertIn('href="#main"', source)
                    self.assertIn('aria-label="Primary navigation"', source)
                    self.assertIn('data-source-review="2026-08-26"', source)
                    self.assertIn("G-KMS6H85LB0", source)
                    self.assertIn("tel:+19082307844", parser.links)
                    self.assertIn(
                        "/es/home-valuation" if language == "es" else "/home-valuation",
                        parser.links,
                    )
                    for source_id in routes[slug]["sourceIds"]:
                        self.assertIn(sources[source_id]["url"], parser.links)
                        localized_use = sources[source_id]["useEs" if language == "es" else "use"]
                        localized_limit = sources[source_id]["limitEs" if language == "es" else "limit"]
                        self.assertIn(localized_use, visible_text(source))
                        self.assertIn(localized_limit, visible_text(source))

    def test_copy_is_unique_helpful_and_avoids_unsupported_claims(self) -> None:
        fingerprints: set[str] = set()
        required_signatures = {
            "sell-your-home": ("pricing", "precio"),
            "how-we-sell-your-home": ("launch plan", "plan de lanzamiento"),
            "expired-listing-help": ("listing history", "historial del anuncio"),
            "fsbo-help": ("owner-led sale", "venta por cuenta propia"),
            "cash-offer-nj": ("written cash offer", "oferta escrita en efectivo"),
            "relocating-from-nj": ("remote", "distancia"),
            "divorce-home-sale-nj": ("both owners", "ambos propietarios"),
            "sell-rental-property-nj": ("lease", "contrato de arrendamiento"),
        }
        for slug in sorted(SLUGS):
            for language in ("en", "es"):
                source = page_path(slug, language).read_text(encoding="utf-8")
                text = visible_text(source)
                with self.subTest(slug=slug, language=language):
                    self.assertGreaterEqual(len(text.split()), 560)
                    self.assertIsNone(RISKY_COPY.search(text))
                    self.assertIn(required_signatures[slug][0 if language == "en" else 1], text.casefold())
                    disclaimer = (
                        "general education, not legal or tax advice"
                        if language == "en"
                        else "educación general, no asesoría legal ni fiscal"
                    )
                    self.assertIn(disclaimer, text.casefold())
                    fingerprint = re.sub(r"\s+", " ", text.casefold())
                    self.assertNotIn(fingerprint, fingerprints)
                    fingerprints.add(fingerprint)

    def test_metadata_and_schema_are_factual(self) -> None:
        for slug in sorted(SLUGS):
            for language in ("en", "es"):
                source = page_path(slug, language).read_text(encoding="utf-8")
                title = html.unescape(re.search(r"<title>(.*?)</title>", source, re.S).group(1)).strip()
                description = html.unescape(
                    re.search(r'<meta name="description" content="([^"]+)"', source).group(1)
                )
                blocks = [
                    json.loads(block)
                    for block in re.findall(
                        r'<script type="application/ld\+json">(.*?)</script>',
                        source,
                        flags=re.DOTALL,
                    )
                ]
                nodes = [node for block in blocks for node in schema_nodes(block)]
                types = {node.get("@type") for node in nodes}
                service = next(node for node in nodes if node.get("@type") == "Service")
                with self.subTest(slug=slug, language=language):
                    self.assertLessEqual(len(title), 68)
                    self.assertGreaterEqual(len(description), 105)
                    self.assertLessEqual(len(description), 165)
                    self.assertTrue({"WebPage", "Service", "FAQPage", "BreadcrumbList"} <= types)
                    self.assertNotIn("Review", types)
                    self.assertNotIn("AggregateRating", types)
                    self.assertNotIn("Offer", types)
                    self.assertEqual(SITE + route(slug, language), service["url"])
                    self.assertEqual("es-US" if language == "es" else "en-US", service["inLanguage"])

    def test_sitemaps_redirects_and_internal_links_consolidate_fast_route(self) -> None:
        english = sitemap_urls("sitemap.xml")
        spanish = sitemap_urls("sitemap-es.xml")
        for slug in SLUGS:
            self.assertIn(SITE + route(slug, "en"), english)
            self.assertIn(SITE + route(slug, "es"), spanish)
        self.assertNotIn(SITE + "/sell-home-fast-nj", english)
        self.assertNotIn(SITE + "/es/sell-home-fast-nj", spanish)

        redirects = {
            item["source"]: item
            for item in json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))["redirects"]
        }
        expected = {
            "/sell-home-fast-nj": "/sell-your-home",
            "/sell-home-fast-nj.html": "/sell-your-home",
            "/es/sell-home-fast-nj": "/es/sell-your-home",
            "/es/sell-home-fast-nj.html": "/es/sell-your-home",
        }
        for source, destination in expected.items():
            with self.subTest(source=source):
                self.assertEqual(destination, redirects[source]["destination"])
                self.assertIs(True, redirects[source]["permanent"])

        offenders: list[str] = []
        skipped = {"sell-home-fast-nj.html", "es/sell-home-fast-nj.html"}
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT).as_posix()
            if relative in skipped or any(part in {".git", "node_modules", "docs"} for part in path.parts):
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r'href=["\'][^"\']*/sell-home-fast-nj(?:\.html)?(?:[?#][^"\']*)?["\']', source):
                offenders.append(relative)
        self.assertEqual([], offenders)

    def test_renderer_is_idempotent(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
