#!/usr/bin/env python3
"""Fail-closed contracts for the bilingual seller-editorial consolidation."""

from __future__ import annotations

import html
import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
MANIFEST = ROOT / "data" / "seller-editorial-rebuild.json"
RENDERER = ROOT / "tools" / "generate_seller_editorial_rebuild.py"

INDEXABLE = {
    "blog/expired-listing-nj-what-to-do.html": "/blog/expired-listing-nj-what-to-do",
    "es/blog/expired-listing-nj-what-to-do.html": "/es/blog/expired-listing-nj-what-to-do",
    "blog/absentee-owner-nj-sell-rental-property.html": "/blog/absentee-owner-nj-sell-rental-property",
    "es/blog/absentee-owner-nj-sell-rental-property.html": "/es/blog/absentee-owner-nj-sell-rental-property",
    "blog/nj-home-selling-costs.html": "/blog/nj-home-selling-costs",
    "es/blog/nj-home-selling-costs.html": "/es/blog/nj-home-selling-costs",
    "blog/how-to-sell-your-home-in-new-jersey-without-an-agent-2026.html": "/blog/how-to-sell-your-home-in-new-jersey-without-an-agent-2026",
    "es/blog/how-to-sell-your-home-in-new-jersey-without-an-agent-2026.html": "/es/blog/how-to-sell-your-home-in-new-jersey-without-an-agent-2026",
    "blog/fsbo-vs-realtor-new-jersey.html": "/blog/fsbo-vs-realtor-new-jersey",
    "es/blog/fsbo-vs-realtor-new-jersey.html": "/es/blog/fsbo-vs-realtor-new-jersey",
    "blog/downsizing-your-nj-home.html": "/blog/downsizing-your-nj-home",
    "es/blog/downsizing-your-nj-home.html": "/es/blog/downsizing-your-nj-home",
    "blog/decluttering-items-home-value-nj.html": "/blog/decluttering-items-home-value-nj",
    "es/blog/decluttering-items-home-value-nj.html": "/es/blog/decluttering-items-home-value-nj",
}

BILINGUAL = {
    "expired-listing": (
        "/blog/expired-listing-nj-what-to-do",
        "/es/blog/expired-listing-nj-what-to-do",
    ),
    "rental-property": (
        "/blog/absentee-owner-nj-sell-rental-property",
        "/es/blog/absentee-owner-nj-sell-rental-property",
    ),
    "selling-costs": (
        "/blog/nj-home-selling-costs",
        "/es/blog/nj-home-selling-costs",
    ),
    "fsbo-process": (
        "/blog/how-to-sell-your-home-in-new-jersey-without-an-agent-2026",
        "/es/blog/how-to-sell-your-home-in-new-jersey-without-an-agent-2026",
    ),
    "fsbo-comparison": (
        "/blog/fsbo-vs-realtor-new-jersey",
        "/es/blog/fsbo-vs-realtor-new-jersey",
    ),
    "downsizing": (
        "/blog/downsizing-your-nj-home",
        "/es/blog/downsizing-your-nj-home",
    ),
    "decluttering": (
        "/blog/decluttering-items-home-value-nj",
        "/es/blog/decluttering-items-home-value-nj",
    ),
}

CONSOLIDATED = {
    "/blog/how-to-sell-house-fast-nj": "/sell-your-home",
    "/es/blog/how-to-sell-house-fast-nj": "/es/sell-your-home",
    "/blog/how-long-to-sell-a-house-nj": "/blog/nj-home-selling-timeline",
    "/blog/selling-your-home-summit-nj-guide": "/sell-your-home",
    "/es/blog/selling-your-home-summit-nj-guide": "/es/sell-your-home",
    "/blog/nj-real-estate-market-2025-sellers-guide": "/blog/best-nj-towns-to-sell-home",
    "/es/blog/nj-real-estate-market-2025-sellers-guide": "/es/blog/best-nj-towns-to-sell-home",
    "/blog/the-truth-about-fsbo-in-nj-2026": "/blog/fsbo-vs-realtor-new-jersey",
    "/es/blog/the-truth-about-fsbo-in-nj-2026": "/es/blog/fsbo-vs-realtor-new-jersey",
}

FALLBACK_FILES = {
    f"{source.lstrip('/')}.html": destination
    for source, destination in CONSOLIDATED.items()
}
EXPECTED_FILES = set(INDEXABLE) | set(FALLBACK_FILES)

REWIRED_SURFACES = (
    "home-valuation.html",
    "blog/index.html",
    "es/blog/index.html",
    "blog/nj-seller-disclosure-requirements.html",
    "es/sell-home-fast-nj.html",
)

ALLOWED_HOSTS = {
    "dep.nj.gov",
    "firesolutions.dca.nj.gov",
    "nj.gov",
    "www.epa.gov",
    "www.irs.gov",
    "www.nj.gov",
    "www.njconsumeraffairs.gov",
    "www.njrealtor.com",
}

FORBIDDEN = re.compile(
    r"(?:"
    r"\b(?:guarantee(?:d|s)?|garanti(?:zar|zado|zada)|top dollar|maximum price|best possible terms)\b|"
    r"\b(?:sell(?:s|ing)? faster|sell(?:s|ing)? for more|more money in your pocket)\b|"
    r"\b(?:available (?:seven|7) days|always responsive|always picks? up)\b|"
    r"\b(?:AI[- ]powered|AI buyer targeting|finds? buyers proactively)\b|"
    r"\b(?:best|perfect|ideal|safe(?:st)?) (?:town|community|neighbou?rhood|place)\b|"
    r"\b(?:great|excellent|top[- ]rated|best) schools?\b|"
    r"\b(?:family[- ]friendly|young families|retirees?|empty[- ]nesters?)\b|"
    r"\b(?:familias j[oó]venes|jubilad[oa]s?|nidos? vac[ií]os?|ideal para familias)\b|"
    r"\b(?:mejor|perfect[oa]|ideal|m[aá]s segur[oa]) (?:pueblo|municipio|comunidad|barrio|lugar)\b|"
    r"\b(?:escuelas? excelentes?|mejores? escuelas?|escuelas? destacadas?)\b|"
    r"\b(?:commission|comisi[oó]n) (?:is|es|averages?|promedia) \d|"
    r"\b\d+(?:\.\d+)?\s*%\s+(?:more|less|higher|lower|over asking|sobre el precio)\b|"
    r"\$\s*\d[\d,.]*(?:\s*[–-]\s*\$?\s*\d[\d,.]*)?\s+(?:in savings|de ahorro)\b|"
    r"\b(?:must|required to|legally required to) (?:hire|use|retain|sign|file|pay)\b|"
    r"\b(?:debe|obligad[oa] a) (?:contratar|usar|firmar|presentar|pagar)\b|"
    r"\b(?:fixed|typical|average|usual) (?:days?|weeks?|months?) (?:to|until) (?:sell|close)\b"
    r")",
    re.I,
)


class IntegrityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.duplicate_attributes: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        names = [name.casefold() for name, _ in attrs]
        self.duplicate_attributes.extend(
            f"{tag}:{name}" for name in sorted({name for name in names if names.count(name) > 1})
        )
        self.ids.extend(value for name, value in attrs if name.casefold() == "id" and value)
        if tag.casefold() == "a":
            self.links.extend(value or "" for name, value in attrs if name.casefold() == "href")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


class SellerEditorialRebuildTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.pages = {path: read(path) for path in EXPECTED_FILES}

    def test_manifest_is_exact_current_and_source_led(self) -> None:
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertEqual(REVIEWED_ON, self.manifest["reviewedOn"])
        self.assertEqual("tools/generate_seller_editorial_rebuild.py", self.manifest["renderer"])
        self.assertEqual(EXPECTED_FILES, set(self.manifest["managedFiles"]))
        self.assertEqual(set(BILINGUAL), set(self.manifest["retainedClusters"]))
        self.assertEqual(CONSOLIDATED, self.manifest["consolidations"])

        source_ids = {item["id"] for item in self.manifest["sources"]}
        self.assertEqual(len(source_ids), len(self.manifest["sources"]))
        self.assertGreaterEqual(len(source_ids), 10)
        for item in self.manifest["sources"]:
            with self.subTest(source=item["id"]):
                self.assertEqual(
                    {"id", "publisher", "title", "url", "kind", "use", "limit", "accessedOn"},
                    set(item),
                )
                self.assertEqual(REVIEWED_ON, item["accessedOn"])
                self.assertEqual("https", urlparse(item["url"]).scheme)
                self.assertIn(urlparse(item["url"]).netloc, ALLOWED_HOSTS)
                self.assertGreaterEqual(len(item["use"]), 28)
                self.assertGreaterEqual(len(item["limit"]), 28)

        for cluster, record in self.manifest["retainedClusters"].items():
            with self.subTest(cluster=cluster):
                self.assertEqual(set(BILINGUAL[cluster]), {record["en"]["route"], record["es"]["route"]})
                self.assertTrue(record["sourceIds"])
                self.assertEqual(set(), set(record["sourceIds"]) - source_ids)
                for language in ("en", "es"):
                    evidence = record[language]["searchConsole"]
                    self.assertEqual({"clicks", "impressions"}, set(evidence))
                    self.assertGreaterEqual(evidence["clicks"], 0)
                    self.assertGreaterEqual(evidence["impressions"], 0)

    def test_renderer_check_is_deterministic(self) -> None:
        result = subprocess.run(
            ["python3", str(RENDERER), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("23 managed seller-editorial pages are current", result.stdout)

    def test_indexable_pages_have_clean_bilingual_signals_and_current_metadata(self) -> None:
        pair_by_route = {route: pair for pair in BILINGUAL.values() for route in pair}
        for relative, route in INDEXABLE.items():
            source = self.pages[relative]
            en_route, es_route = pair_by_route[route]
            canonical = SITE + route
            with self.subTest(path=relative):
                self.assertRegex(source, r'<meta name="robots" content="index, follow')
                self.assertNotIn("noindex", source)
                self.assertEqual(1, source.count('<link rel="canonical"'))
                self.assertIn(f'<link rel="canonical" href="{canonical}">', source)
                self.assertIn(f'hreflang="en-US" href="{SITE}{en_route}"', source)
                self.assertIn(f'hreflang="es-US" href="{SITE}{es_route}"', source)
                self.assertIn(f'hreflang="x-default" href="{SITE}{en_route}"', source)
                if relative.startswith("es/"):
                    self.assertIn(f'hreflang="es" href="{SITE}{es_route}"', source)
                self.assertIn('<meta property="article:modified_time" content="2026-08-26">', source)
                self.assertIn("Sources checked August 26, 2026" if not relative.startswith("es/") else "Fuentes verificadas el 26 de agosto de 2026", source)

    def test_homepage_design_accessibility_and_html_integrity(self) -> None:
        css = read("css/fair-housing-town-comparison.css")
        for token in ("#0A0A0A", "#1A1A1A", "#C41230", "#8B0D22", "#B8962E", "#D4AF5A", "#FAFAF8"):
            self.assertIn(token, css)
        for family in ("Playfair Display", "Inter"):
            self.assertIn(family, css)
        self.assertRegex(css, r"@media\s*\(max-width:\s*700px\)")
        self.assertIn("min-height: 44px", css)
        self.assertIn(":focus-visible", css)
        self.assertIn(".comparison-brand img", css)
        self.assertIn(".comparison-menu", css)
        self.assertIn(".seller-editorial-page .comparison-nav__links.is-open", css)
        nav_rule = re.search(r"\.comparison-nav\s*\{(?P<body>.*?)\}", css, re.S)
        self.assertIsNotNone(nav_rule)
        nav_css = nav_rule.group("body")
        for declaration in (
            "position: sticky",
            "width: 100%",
            "padding: 0",
            "background: var(--comparison-ink)",
            "backdrop-filter: none",
            "box-shadow: none",
            "font-family: 'Inter', sans-serif",
        ):
            self.assertIn(declaration, nav_css)

        for relative in INDEXABLE:
            source = self.pages[relative]
            parser = IntegrityParser()
            parser.feed(source)
            with self.subTest(path=relative):
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertEqual(1, len(re.findall(r'<main\b[^>]*id="main"', source, re.I)))
                self.assertIn('href="#main"', source)
                self.assertIn('aria-label="Primary navigation"', source)
                self.assertIn('class="seller-editorial-page"', source)
                self.assertIn('class="comparison-menu"', source)
                self.assertIn('aria-controls="seller-editorial-navigation"', source)
                self.assertIn('id="seller-editorial-navigation"', source)
                self.assertIn('/images/jorge-logo.webp', source)
                self.assertIn('/images/jorge-logo.jpg', source)
                self.assertIn('<script defer src="/js/site-cta.js"></script>', source)
                self.assertIn('/css/styles.css', source)
                self.assertIn('/css/fair-housing-town-comparison.css', source)
                self.assertIn("family=Playfair+Display", source)
                self.assertIn("family=Inter", source)
                if relative.startswith("es/"):
                    self.assertNotIn('href="/es/contact"', source)
                    self.assertIn('href="/es/#contact"', source)
                self.assertEqual([], parser.duplicate_attributes)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                for tag in re.findall(r'<a\b[^>]*target="_blank"[^>]*>', source, re.I):
                    self.assertRegex(tag, r'rel="[^"]*noopener[^"]*noreferrer')

    def test_visible_copy_is_grounded_neutral_and_not_legal_or_tax_advice(self) -> None:
        for relative in INDEXABLE:
            source = self.pages[relative]
            text = visible_text(source)
            with self.subTest(path=relative):
                self.assertIsNone(FORBIDDEN.search(text), FORBIDDEN.search(text).group(0) if FORBIDDEN.search(text) else "")
                if relative.startswith("es/"):
                    self.assertIn("educación general", text.casefold())
                    self.assertIn("asesoría legal ni fiscal", text.casefold())
                    self.assertIn("características protegidas", text.casefold())
                else:
                    self.assertIn("general education", text.casefold())
                    self.assertIn("not legal or tax advice", text.casefold())
                    self.assertIn("protected characteristics", text.casefold())

    def test_schema_is_parseable_factual_and_matches_visible_article(self) -> None:
        forbidden = {"FAQPage", "HowTo", "Review", "Rating", "AggregateRating", "Service", "Offer"}
        for relative, route in INDEXABLE.items():
            source = self.pages[relative]
            blocks = [
                json.loads(block)
                for block in re.findall(
                    r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                    source,
                    flags=re.I | re.S,
                )
            ]
            nodes = [node for block in blocks for node in schema_nodes(block)]
            types = {node.get("@type") for node in nodes}
            article = next(node for node in nodes if node.get("@type") == "Article")
            with self.subTest(path=relative):
                self.assertTrue({"Organization", "Person", "WebPage", "Article", "BreadcrumbList"} <= types)
                self.assertFalse(types & forbidden)
                self.assertEqual(SITE + route, article["url"])
                self.assertEqual(REVIEWED_ON, article["dateModified"])
                self.assertIn(article["headline"], visible_text(source))
                self.assertTrue(article["citation"])

    def test_cluster_sources_are_visible_on_both_languages(self) -> None:
        source_map = {item["id"]: item["url"] for item in self.manifest["sources"]}
        for cluster, record in self.manifest["retainedClusters"].items():
            expected = {source_map[source_id] for source_id in record["sourceIds"]}
            for language in ("en", "es"):
                relative = record[language]["file"]
                hrefs = set(re.findall(r'<a\b[^>]*href="([^"]+)"', self.pages[relative], re.I))
                with self.subTest(cluster=cluster, language=language):
                    self.assertEqual(set(), expected - hrefs)

    def test_consolidations_are_one_hop_permanent_and_fallbacks_are_neutral(self) -> None:
        config = json.loads(read("vercel.json"))
        redirects = {
            item["source"]: item
            for item in config["redirects"]
            if not item.get("has")
        }
        redirect_sources = set(redirects)
        for source, destination in CONSOLIDATED.items():
            for variant in (source, source + ".html"):
                with self.subTest(source=variant):
                    self.assertIn(variant, redirects)
                    self.assertEqual(destination, redirects[variant]["destination"])
                    self.assertIs(True, redirects[variant]["permanent"])
                    self.assertNotIn(destination, redirect_sources)

            relative = source.lstrip("/") + ".html"
            fallback = self.pages[relative]
            with self.subTest(fallback=relative):
                self.assertIn('<meta name="robots" content="noindex, follow">', fallback)
                self.assertNotRegex(fallback, r'http-equiv="refresh"')
                self.assertIn(f'<link rel="canonical" href="{SITE}{destination}">', fallback)
                self.assertIn(f'href="{destination}"', fallback)
                self.assertEqual(1, len(re.findall(r"<h1\b", fallback, re.I)))
                self.assertIn('class="archive-header"', fallback)
                self.assertIn('class="archive-footer"', fallback)
                self.assertIn('id="main"', fallback)
                self.assertIn('/images/jorge-logo.webp', fallback)
                self.assertIn('/images/jorge-logo.jpg', fallback)
                self.assertIn('family=Playfair+Display', fallback)
                self.assertIn('family=Inter', fallback)
                self.assertIn('<script defer src="/js/site-cta.js"></script>', fallback)

    def test_sitemap_has_only_retained_canonicals_from_owned_scope(self) -> None:
        entries = {}
        for sitemap in ("sitemap.xml", "sitemap-es.xml"):
            root = ET.parse(ROOT / sitemap).getroot()
            entries.update(
                {
                    (node.findtext("{*}loc") or "").strip(): node
                    for node in root.findall("{*}url")
                }
            )
        for route in INDEXABLE.values():
            with self.subTest(route=route):
                self.assertIn(SITE + route, entries)
        for source in CONSOLIDATED:
            with self.subTest(source=source):
                self.assertNotIn(SITE + source, entries)

        for en_route, es_route in BILINGUAL.values():
            for route in (en_route, es_route):
                entry = entries[SITE + route]
                alternates = {
                    (node.attrib.get("hreflang"), node.attrib.get("href"))
                    for node in entry.findall("{*}link")
                }
                self.assertIn(("en-US", SITE + en_route), alternates)
                self.assertIn(("es-US", SITE + es_route), alternates)
                self.assertIn(("x-default", SITE + en_route), alternates)

    def test_owned_internal_link_surfaces_do_not_enter_retired_routes(self) -> None:
        retired_href = re.compile(
            r'href="(?:https://thejorgeramirezgroup\.com)?'
            r'/(?:es/)?blog/(?:how-to-sell-house-fast-nj|how-long-to-sell-a-house-nj|'
            r'selling-your-home-summit-nj-guide|nj-real-estate-market-2025-sellers-guide|'
            r'the-truth-about-fsbo-in-nj-2026)(?:\.html)?(?:[#?][^"]*)?"',
            re.I,
        )
        retired_integration_href = re.compile(
            r'href="/(?:es/)?blog/(?:top-nyc-commuter-towns-nj-2026|'
            r'selling-your-home-summit-nj-guide|nj-property-tax-guide-homeowners)'
            r'(?:\.html)?(?:[#?][^"]*)?"|'
            r'href="/(?:es/)?towns/(?:short-hills|bernards-township)(?:\.html)?(?:[#?][^"]*)?"|'
            r'href="/tools/home-value-estimator(?:\.html)?(?:[#?][^"]*)?"',
            re.I,
        )
        for relative in REWIRED_SURFACES:
            with self.subTest(path=relative):
                source = read(relative)
                self.assertIsNone(retired_href.search(source))
                self.assertIsNone(retired_integration_href.search(source))
                parser = IntegrityParser()
                parser.feed(source)
                self.assertEqual([], parser.duplicate_attributes)
                if relative in {"blog/index.html", "es/blog/index.html"}:
                    header_nav = re.search(r"body\s*>\s*header\s*>\s*nav\s*\{(?P<body>.*?)\}", source, re.S)
                    self.assertIsNotNone(header_nav)
                    header_nav_css = header_nav.group("body")
                    for declaration in (
                        "position: static",
                        "width: 100%",
                        "padding: .75rem 0 0",
                        "background: transparent",
                        "backdrop-filter: none",
                        "box-shadow: none",
                    ):
                        self.assertIn(declaration, header_nav_css)


if __name__ == "__main__":
    unittest.main()
