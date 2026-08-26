#!/usr/bin/env python3
"""Fail-closed contract for the authority, FAQ, market, and RTF cleanup wave."""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
MANIFEST_PATH = ROOT / "data" / "authority-tools-sources.json"
RENDERER = ROOT / "tools" / "render_authority_tools.py"
ROUTE_SYNC = ROOT / "tools" / "sync_authority_tools_routes.py"
STYLESHEET = ROOT / "css" / "authority-tools.css"
REVIEWED_ON = "2026-08-26"
LEGAL_TAX_DIRECTIVE = re.compile(
    r"\b(?:must|required to|legally required to) (?:hire|use|retain|sign|file|pay)\b|"
    r"\b(?:executor|administrator) (?:must|can) sign\b|\bpartition action\b|"
    r"\bstepped[- ]up basis\b|\bthree[- ]business[- ]day attorney[- ]review\b",
    re.I,
)

INDEXABLE = {
    "nj-realty-transfer-fee-calculator.html": (
        "en",
        "/nj-realty-transfer-fee-calculator",
        "/es/nj-realty-transfer-fee-calculator",
        "rtf",
    ),
    "es/nj-realty-transfer-fee-calculator.html": (
        "es",
        "/es/nj-realty-transfer-fee-calculator",
        "/nj-realty-transfer-fee-calculator",
        "rtf",
    ),
    "nj-real-estate-questions-answers.html": (
        "en",
        "/nj-real-estate-questions-answers",
        "/es/nj-real-estate-questions-answers",
        "faq",
    ),
    "es/nj-real-estate-questions-answers.html": (
        "es",
        "/es/nj-real-estate-questions-answers",
        "/nj-real-estate-questions-answers",
        "faq",
    ),
    "blog/nj-housing-market-2026-buy-sell-or-wait.html": (
        "en",
        "/blog/nj-housing-market-2026-buy-sell-or-wait",
        None,
        "market-decision",
    ),
}

ALLOWED_SOURCE_HOSTS = {
    "www.nj.gov",
    "www.consumerfinance.gov",
    "www.njrealtor.com",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, list[tuple[str, str | None]], dict[str, str]]] = []
        self.visible_parts: list[str] = []
        self.json_scripts: list[str] = []
        self._hidden_depth = 0
        self._json = False
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        self.tags.append((tag.lower(), attrs, values))
        if tag.lower() == "script" and values.get("type") == "application/ld+json":
            self._json = True
            self._json_parts = []
        elif tag.lower() in {"script", "style", "template", "noscript"}:
            self._hidden_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(
            (tag.lower(), attrs, {key.lower(): value or "" for key, value in attrs})
        )

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._json:
            self.json_scripts.append("".join(self._json_parts).strip())
            self._json = False
            self._json_parts = []
        elif tag.lower() in {"script", "style", "template", "noscript"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._json:
            self._json_parts.append(data)
        elif not self._hidden_depth:
            normalized = " ".join(data.split())
            if normalized:
                self.visible_parts.append(normalized)

    def attrs(self, tag: str) -> list[dict[str, str]]:
        return [values for current, _, values in self.tags if current == tag]

    @property
    def visible_text(self) -> str:
        return html.unescape(" ".join(self.visible_parts))


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def parsed(relative: str) -> PageParser:
    parser = PageParser()
    parser.feed(source(relative))
    return parser


def schema_nodes(parser: PageParser) -> list[dict]:
    nodes: list[dict] = []
    for raw in parser.json_scripts:
        payload = json.loads(raw)
        graph = payload.get("@graph", [payload]) if isinstance(payload, dict) else payload
        if not isinstance(graph, list):
            graph = [graph]
        nodes.extend(node for node in graph if isinstance(node, dict))
    return nodes


class AuthorityToolsCleanupTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.consolidations = cls.manifest["consolidations"]

    def test_manifest_exactly_covers_the_cleanup_wave(self) -> None:
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertEqual(REVIEWED_ON, self.manifest["reviewedOn"])
        self.assertEqual("tools/render_authority_tools.py", self.manifest["renderer"])
        self.assertEqual("tools/sync_authority_tools_routes.py", self.manifest["routeSync"])
        self.assertEqual("tools/check_authority_tool_sources.py", self.manifest["sourceCheck"])
        self.assertEqual(22, len(self.consolidations))
        self.assertEqual(22, len({item["file"] for item in self.consolidations}))
        self.assertEqual(22, len({item["route"] for item in self.consolidations}))
        self.assertEqual(28, len(self.manifest["managedFiles"]))
        self.assertEqual(set(INDEXABLE), set(self.manifest["indexablePages"]))
        self.assertEqual(
            set(self.manifest["managedFiles"]),
            {item["file"] for item in self.consolidations}
            | set(INDEXABLE)
            | {"js/nj-rtf-calculator.js"},
        )
        for record in self.consolidations:
            with self.subTest(route=record["route"]):
                self.assertIn(record["lang"], {"en", "es"})
                self.assertTrue(record["route"].startswith("/"))
                self.assertTrue(record["destination"].startswith("/"))
                self.assertNotEqual(record["route"], record["destination"])
                self.assertTrue(record["reason"].strip())

    def test_renderer_and_route_sync_are_deterministic(self) -> None:
        for script in (RENDERER, ROUTE_SYNC):
            with self.subTest(script=script.name):
                completed = subprocess.run(
                    [sys.executable, str(script), "--check"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_primary_source_registry_is_current_limited_and_visible(self) -> None:
        sources = self.manifest["sources"]
        self.assertEqual(14, len(sources))
        self.assertEqual(14, len({record["id"] for record in sources}))
        for record in sources:
            with self.subTest(source=record["id"]):
                self.assertEqual(
                    {"id", "publisher", "title", "url", "clusters", "use", "limit", "accessedOn"},
                    set(record),
                )
                self.assertEqual(REVIEWED_ON, record["accessedOn"])
                self.assertIn(urlsplit(record["url"]).netloc, ALLOWED_SOURCE_HOSTS)
                self.assertTrue(record["use"].strip())
                self.assertTrue(record["limit"].strip())
                for cluster in record["clusters"]:
                    pages = [name for name, values in INDEXABLE.items() if values[3] == cluster]
                    self.assertTrue(
                        any(record["url"] in parsed(name).attrs("a")[index].get("href", "")
                            for name in pages
                            for index in range(len(parsed(name).attrs("a")))),
                        f'{record["id"]} is not visible in a managed page',
                    )

    def test_retired_pages_are_compact_neutral_noindex_fallbacks(self) -> None:
        for record in self.consolidations:
            with self.subTest(file=record["file"]):
                text = source(record["file"])
                parser = parsed(record["file"])
                robots = [meta.get("content") for meta in parser.attrs("meta") if meta.get("name") == "robots"]
                canonicals = [link.get("href") for link in parser.attrs("link") if link.get("rel") == "canonical"]
                self.assertEqual(["noindex, follow"], robots)
                self.assertEqual([SITE + record["destination"]], canonicals)
                self.assertEqual(1, len(parser.attrs("main")))
                self.assertEqual(1, len(parser.attrs("h1")))
                self.assertIn(record["destination"], {item.get("href") for item in parser.attrs("a")})
                self.assertFalse([meta for meta in parser.attrs("meta") if meta.get("http-equiv", "").lower() == "refresh"])
                self.assertFalse(parser.json_scripts)
                self.assertIn('/css/authority-tools.css', {item.get("href") for item in parser.attrs("link")})
                self.assertIn("G-KMS6H85LB0", text)
                self.assertLess(len(text.encode("utf-8")), 10000)
                self.assertNotRegex(
                    parser.visible_text,
                    r"(?i)top[- ]rated|#\s*1(?!\d)|best\s+(?:agent|realtor)|guaranteed|save\s+thousands|aggregateRating",
                )

    def test_indexable_pages_have_self_canonicals_snippet_metadata_and_language_pairs(self) -> None:
        for relative, (lang, route, alternate, _) in INDEXABLE.items():
            with self.subTest(relative=relative):
                text = source(relative)
                parser = parsed(relative)
                self.assertEqual(lang, parser.attrs("html")[0].get("lang"))
                robots = [meta.get("content", "") for meta in parser.attrs("meta") if meta.get("name") == "robots"]
                self.assertEqual(["index, follow, max-image-preview:large, max-snippet:-1"], robots)
                canonicals = [link.get("href") for link in parser.attrs("link") if link.get("rel") == "canonical"]
                self.assertEqual([SITE + route], canonicals)
                title = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
                self.assertIsNotNone(title)
                title_text = " ".join(title.group(1).split())
                self.assertGreaterEqual(len(title_text), 35)
                self.assertLessEqual(len(title_text), 65)
                descriptions = [meta.get("content", "") for meta in parser.attrs("meta") if meta.get("name") == "description"]
                self.assertEqual(1, len(descriptions))
                self.assertGreaterEqual(len(descriptions[0]), 120)
                self.assertLessEqual(len(descriptions[0]), 165)
                self.assertEqual(1, len(parser.attrs("main")))
                self.assertEqual(1, len(parser.attrs("h1")))
                self.assertIn('/css/authority-tools.css', {item.get("href") for item in parser.attrs("link")})
                self.assertIn("Playfair+Display", text)
                self.assertIn("family=Inter", text)
                self.assertIn("G-KMS6H85LB0", text)
                alternates = {item.get("href") for item in parser.attrs("link") if item.get("rel") == "alternate"}
                if alternate:
                    self.assertIn(SITE + alternate, alternates)

    def test_json_ld_is_valid_minimal_and_matches_visible_faqs(self) -> None:
        for relative in INDEXABLE:
            with self.subTest(relative=relative):
                parser = parsed(relative)
                self.assertEqual(1, len(parser.json_scripts))
                nodes = schema_nodes(parser)
                types = {node.get("@type") for node in nodes}
                self.assertTrue({"Organization", "WebSite", "Person", "WebPage", "Article", "BreadcrumbList", "FAQPage"}.issubset(types))
                self.assertFalse({"Review", "AggregateRating"} & types)
                self.assertNotIn("aggregateRating", parser.json_scripts[0])
                ids = [node.get("@id") for node in nodes if node.get("@id")]
                self.assertEqual(len(ids), len(set(ids)))
                article = next(node for node in nodes if node.get("@type") == "Article")
                self.assertEqual(REVIEWED_ON, article["dateModified"])
                self.assertNotIn("datePublished", article, "Do not invent an original publication date")
                faq = next(node for node in nodes if node.get("@type") == "FAQPage")
                self.assertGreaterEqual(len(faq["mainEntity"]), 4)
                for question in faq["mainEntity"]:
                    self.assertIn(question["name"], parser.visible_text)
                    self.assertIn(question["acceptedAnswer"]["text"], parser.visible_text)

    def test_managed_html_has_unique_ids_attributes_and_safe_external_tabs(self) -> None:
        for relative in [*{item["file"] for item in self.consolidations}, *INDEXABLE]:
            with self.subTest(relative=relative):
                parser = parsed(relative)
                ids = [values["id"] for _, _, values in parser.tags if values.get("id")]
                duplicates = [value for value, count in Counter(ids).items() if count > 1]
                self.assertEqual([], duplicates)
                for tag, raw_attrs, values in parser.tags:
                    names = [name.lower() for name, _ in raw_attrs]
                    self.assertEqual(len(names), len(set(names)), f"duplicate attribute on <{tag}> in {relative}")
                    if tag == "a" and values.get("target") == "_blank":
                        rel = set(values.get("rel", "").split())
                        self.assertTrue({"noopener", "noreferrer"}.issubset(rel))

    def test_homepage_palette_type_and_responsive_accessibility_contract(self) -> None:
        css = STYLESHEET.read_text(encoding="utf-8")
        for token in ("#0A0A0A", "#1A1A1A", "#C41230", "#8B0D22", "#B8962E", "#D4AF5A", "#FAFAF8", "#F8F6F2"):
            self.assertIn(token, css)
        self.assertIn("'Playfair Display'", css)
        self.assertIn("'Inter'", css)
        self.assertRegex(css, r"@media\s*\(max-width:\s*(?:6\d\d|7\d\d|8\d\d|900)px\)")
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertGreaterEqual(len(re.findall(r"min-height:\s*44px", css)), 4)
        self.assertIn("overflow-x: hidden", css)
        self.assertRegex(css, r"body\.at-page \.at-breadcrumb\s*\{[^}]*position:\s*static")
        self.assertRegex(css, r"body\.at-page \.at-footer nav\s*\{[^}]*position:\s*static")

    def test_rtf_calculator_uses_current_schedule_and_exact_boundary_math(self) -> None:
        script = r"""
require('./js/nj-rtf-calculator.js');
const values = [99.99, 100, 150000, 200000, 350000, 350001, 1000000, 1000001, 2000000, 2000001, 2500000, 2750000, 3000000, 3500000, 3500001];
console.log(JSON.stringify(values.map(value => [value, globalThis.JRG_RTF_CALCULATOR.calculate(value)])));
"""
        completed = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=False
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        results = dict(json.loads(completed.stdout))
        expected = {
            99.99: (0, 0),
            100: (200, 0),
            150000: (60000, 0),
            200000: (93500, 0),
            350000: (210500, 0),
            350001: (273980, 0),
            1000000: (957500, 0),
            1000001: (958105, 1000001),
            2000000: (2167500, 2000000),
            2000001: (2168105, 4000002),
            2500000: (2772500, 5000000),
            2750000: (3075000, 6875000),
            3000000: (3377500, 7500000),
            3500000: (3982500, 10500000),
            3500001: (3983105, 12250004),
        }
        for amount, (standard, graduated) in expected.items():
            with self.subTest(amount=amount):
                result = results[amount]
                self.assertEqual(standard, result["standardCents"])
                self.assertEqual(graduated, result["graduatedCents"])
                self.assertEqual(standard + graduated, result["combinedCents"])

    def test_rtf_pages_state_scope_date_classes_and_no_outcome_promise(self) -> None:
        for relative in ("nj-realty-transfer-fee-calculator.html", "es/nj-realty-transfer-fee-calculator.html"):
            with self.subTest(relative=relative):
                parser = parsed(relative)
                visible = parser.visible_text
                self.assertIn("July 10, 2025" if relative.startswith("nj-") else "10 de julio de 2025", visible)
                self.assertRegex(visible, r"(?i)(?:straight percentage|porcentaje recto)")
                property_classes = ("Class 2", "3A", "4A", "4C") if relative.startswith("nj-") else ("clases 2", "3A", "4A", "4C")
                for property_class in property_classes:
                    self.assertIn(property_class, visible)
                self.assertRegex(visible, r"(?i)(?:not a closing quote|no es una cotización de cierre)")
                self.assertRegex(visible, r"(?i)(?:does not decide|no decide).{0,180}(?:exemptions|exenciones)")
                self.assertEqual(3, len(parser.attrs("table")))
                self.assertEqual(3, len(parser.attrs("caption")), "Every fee table needs a visible caption")
        self.assertIn('/es/sell-your-home', {a.get('href') for a in parsed('es/nj-realty-transfer-fee-calculator.html').attrs('a')})

    def test_bilingual_faq_preserves_current_nj_legal_and_fair_housing_nuance(self) -> None:
        english = parsed("nj-real-estate-questions-answers.html").visible_text.lower()
        spanish = parsed("es/nj-real-estate-questions-answers.html").visible_text.lower()
        for phrase in (
            "before providing brokerage services or as soon as reasonably practical",
            "fully negotiable and not set by law",
            "many new jersey buyers retain attorneys, but doing so is not required",
            "does not by itself create an agency relationship",
            "neutral criteria",
        ):
            self.assertIn(phrase, english)
        for phrase in (
            "antes de prestar servicios de corretaje o tan pronto como sea razonablemente práctico",
            "totalmente negociables y no las fija la ley",
            "muchos compradores de nueva jersey contratan abogados, pero no es obligatorio",
            "por sí sola no crea una relación de agencia",
            "criterios neutrales",
        ):
            self.assertIn(phrase, spanish)
        for visible in (english, spanish):
            self.assertNotRegex(visible, r"(?i)mandatory attorney|abogado obligatorio|commission is fixed|comisión fija|best neighborhood|mejor vecindario")

    def test_indexable_pages_avoid_unsupported_legal_or_tax_directives(self) -> None:
        for relative in INDEXABLE:
            with self.subTest(relative=relative):
                self.assertNotRegex(source(relative), LEGAL_TAX_DIRECTIVE)

    def test_market_page_is_a_dated_decision_framework_not_a_forecast(self) -> None:
        visible = parsed("blog/nj-housing-market-2026-buy-sell-or-wait.html").visible_text.lower()
        self.assertIn("there is no responsible statewide answer", visible)
        self.assertIn("completed 2025 new jersey average residential statistics include sales columns", visible)
        self.assertIn("published 2026 file was incomplete", visible)
        self.assertIn("a lender qualification amount is not the same as a personally sustainable budget", visible)
        self.assertIn("does not forecast prices, interest rates, time on market, proceeds, or a closing date", visible)
        self.assertNotRegex(visible, r"(?i)prices? (?:will|are expected to)|rates? (?:will|are expected to)|best month to (?:buy|sell)|guaranteed")

    def test_redirects_are_permanent_complete_unique_and_one_hop(self) -> None:
        config = json.loads(source("vercel.json"))
        redirects = config["redirects"]
        by_source: dict[str, list[dict]] = {}
        for rule in redirects:
            by_source.setdefault(rule["source"], []).append(rule)
        managed_sources = set()
        for record in self.consolidations:
            for route in (record["route"], record["route"] + ".html"):
                managed_sources.add(route)
                self.assertEqual(1, len(by_source.get(route, [])), route)
                rule = by_source[route][0]
                self.assertIs(True, rule.get("permanent"))
                self.assertEqual(record["destination"], rule["destination"])
            self.assertNotIn(record["destination"], managed_sources)
        redirect_sources = set(by_source)
        for record in self.consolidations:
            self.assertNotIn(record["destination"], redirect_sources, f'{record["route"]} would redirect more than once')

    def test_sitemaps_exclude_retired_routes_and_keep_only_indexable_outputs(self) -> None:
        retired = {record["route"] for record in self.consolidations}
        expected_by_file = {
            "sitemap.xml": {values[1] for values in INDEXABLE.values() if values[0] == "en"},
            "sitemap-es.xml": {values[1] for values in INDEXABLE.values() if values[0] == "es"},
        }
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        for filename, expected in expected_by_file.items():
            with self.subTest(filename=filename):
                tree = ET.parse(ROOT / filename)
                locs = {node.text.removeprefix(SITE) for node in tree.findall("s:url/s:loc", namespace)}
                alternates = {node.get("href", "").removeprefix(SITE) for node in tree.findall("s:url/x:link", namespace)}
                self.assertFalse(retired & locs)
                self.assertFalse(retired & alternates)
                self.assertTrue(expected.issubset(locs))
                for route in expected:
                    self.assertEqual(1, sum(item == route for item in locs))

    def test_owned_internal_links_bypass_every_redirected_route(self) -> None:
        retired = {record["route"] for record in self.consolidations}
        for relative in self.manifest["internalLinkFiles"]:
            with self.subTest(relative=relative):
                for anchor in parsed(relative).attrs("a"):
                    href = anchor.get("href", "")
                    path = urlsplit(href).path
                    if href.startswith(SITE):
                        path = urlsplit(href.removeprefix(SITE)).path
                    if path.endswith(".html"):
                        path = path[:-5]
                    self.assertNotIn(path, retired, f"{relative} still links through {path}")
        for relative, routes in self.manifest["hreflangRemovals"].items():
            alternate_paths = {
                urlsplit(link.get("href", "")).path
                for link in parsed(relative).attrs("link")
                if link.get("rel") == "alternate"
            }
            self.assertFalse(set(routes) & alternate_paths)
        for relative in self.manifest["internalLinkFiles"]:
            hrefs = {anchor.get("href", "") for anchor in parsed(relative).attrs("a")}
            self.assertFalse(set(self.manifest["additionalLinkRewrites"]) & hrefs)

    def test_gsc_dispositions_preserve_equity_without_inventing_metrics(self) -> None:
        evidence = self.manifest["gscEvidence"]
        self.assertIn("Last 3 months", evidence["period"])
        self.assertEqual({"clicks": 53, "impressions": 19011}, evidence["propertyTaxDestination"])
        self.assertEqual({"clicks": 35, "impressions": 9523}, evidence["firstTimeBuyerDestination"])
        self.assertEqual({"clicks": 10, "impressions": 1314}, evidence["inheritedHomeDestination"])
        self.assertEqual({"clicks": 0, "impressions": 49}, evidence["questionsAnswersEnglish"])
        self.assertEqual({"clicks": 0, "impressions": 0}, evidence["anchorGuide"])
        self.assertEqual({"clicks": 0, "impressions": 0}, evidence["housingMarketDecision"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
