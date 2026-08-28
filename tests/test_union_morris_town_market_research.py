#!/usr/bin/env python3
"""Regression contract for retained Union and Morris town market research."""

from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
PAGE_MODIFIED_ON = "2026-08-27"
MANIFEST = ROOT / "data" / "union-morris-town-market-sources-2026-08-26.json"
GENERATOR = ROOT / "tools" / "generate_union_morris_town_market_research.py"
PALETTE = {
    "#0A0A0A",
    "#1A1A1A",
    "#C41230",
    "#8B0D22",
    "#B8962E",
    "#D4AF5A",
    "#F8F6F2",
    "#FAFAF8",
}

REPORTS = {
    "market-report-cranford-nj-2026": {
        "name": "Cranford",
        "official": "Cranford Township",
        "county": "Union",
        "code": "2003",
        "published": "2026-03-08",
        "official_url": "https://www.cranfordnj.org/",
        "metrics": (7502, 189413, 13729, 170, "809972.65"),
    },
    "market-report-linden-nj-2026": {
        "name": "Linden",
        "official": "Linden City",
        "county": "Union",
        "code": "2009",
        "published": "2026-03-09",
        "official_url": "https://www.linden-nj.gov/",
        "metrics": (10226, 133862, 9832, 327, "556332.91"),
    },
    "market-report-new-providence-nj-2026": {
        "name": "New Providence",
        "official": "New Providence Borough",
        "county": "Union",
        "code": "2011",
        "published": "2026-03-09",
        "official_url": "https://www.newprov.us/",
        "metrics": (3756, 309624, 16231, 91, "1001056.55"),
    },
    "market-report-rahway-nj-2026": {
        "name": "Rahway",
        "official": "Rahway City",
        "county": "Union",
        "code": "2013",
        "published": "2026-03-09",
        "official_url": "https://www.cityofrahway.org/",
        "metrics": (7330, 137596, 10435, 120, "497987.50"),
    },
    "market-report-scotch-plains-nj-2026": {
        "name": "Scotch Plains",
        "official": "Scotch Plains Township",
        "county": "Union",
        "code": "2016",
        "published": "2026-03-08",
        "official_url": "https://scotchplainsnj.gov/",
        "metrics": (7413, 128077, 15818, 219, "878329.03"),
    },
    "market-report-westfield-nj-2026": {
        "name": "Westfield",
        "official": "Westfield Town",
        "county": "Union",
        "code": "2020",
        "published": "2026-03-08",
        "official_url": "https://www.westfieldnj.gov/",
        "metrics": (9290, 826690, 18948, 274, "1305037.09"),
    },
    "market-report-chatham-nj-2026": {
        "name": "Chatham",
        "official": "Chatham Borough",
        "county": "Morris",
        "code": "1404",
        "published": "2026-03-08",
        "official_url": "https://www.chathamborough.org/",
        "metrics": (2702, 997082, 16960, 94, "1221072.16"),
    },
    "market-report-denville-nj-2026": {
        "name": "Denville",
        "official": "Denville Township",
        "county": "Morris",
        "code": "1408",
        "published": "2026-03-09",
        "official_url": "https://www.denvillenj.gov/",
        "metrics": (6189, 410847, 11459, 166, "697051.48"),
    },
    "market-report-madison-nj-2026": {
        "name": "Madison",
        "official": "Madison Borough",
        "county": "Morris",
        "code": "1417",
        "published": "2026-03-08",
        "official_url": "https://www.rosenet.org/",
        "metrics": (4282, 705283, 15897, 104, "1291398.17"),
    },
    "market-report-morristown-nj-2026": {
        "name": "Morristown",
        "official": "Morristown Town",
        "county": "Morris",
        "code": "1424",
        "published": "2026-03-08",
        "official_url": "https://www.townofmorristown.org/",
        "metrics": (3613, 635270, 11181, 128, "788408.26"),
    },
    "market-report-randolph-nj-2026": {
        "name": "Randolph",
        "official": "Randolph Township",
        "county": "Morris",
        "code": "1432",
        "published": "2025-03-01",
        "official_url": "https://www.randolphnj.org/",
        "metrics": (7395, 493400, 14467, 239, "833332.49"),
    },
}

COMMON_SOURCES = {
    "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml",
    "https://www.nj.gov/treasury/taxation/pdf/lpt/class4/2025AvgResStat.pdf",
    "https://www.njrealtor.com/research/10k/",
    "https://njar-public.stats.10kresearch.com/reports",
    "https://www.nj.gov/dca/codes/reporter/",
    "https://www.census.gov/acs/www/data/data-tables-and-tools/data-profiles/",
}

FORBIDDEN_VISIBLE = re.compile(
    r"forecast|prediction|projected|appreciat(?:e|ion)|hottest|hot market|"
    r"seller.?s market|buyer.?s market|act now|before prices|"
    r"\b(?:best|perfect|ideal)\s+(?:town|place|community|market)|"
    r"top[- ](?:ranked|rated)|\bfamily[- ]friendly\b|\bschools?\b|"
    r"\bsafe(?:ty)?\b|crime rate|guarantee|"
    r"pron[oó]stic|predicci[oó]n|proyectad|apreciaci[oó]n|mercado caliente|"
    r"mercado (?:de|para) vendedores|mercado (?:de|para) compradores|"
    r"mejor(?:es)? (?:pueblo|lugar|comunidad|mercado)|"
    r"familiar|escuelas?|segur(?:o|a|idad)|tasa de criminalidad|garantiz",
    re.IGNORECASE,
)

FAIR_HOUSING_RISKY_VISIBLE = re.compile(
    r"\bfamil(?:y|ies)\b|\bfamilias?\b|\bfamily[- ]friendly\b|\bfamiliar(?:es)?\b|"
    r"\bschools?\b|\bescuelas?\b|"
    r"\b(?:safe|safest|safety)\s+(?:town|city|community|neighbou?rhood|place)\b|"
    r"\bsegur(?:o|a|os|as|idad)\b|\bcrime(?:\s+rate)?\b|\bcriminalidad\b|"
    r"\b(?:best|ideal|perfect|right)\s+(?:town|city|community|neighbou?rhood|place)\b|"
    r"\b(?:mejor|ideal|perfect[oa])\s+(?:pueblo|ciudad|comunidad|vecindario|lugar)\b|"
    r"\btop[- ](?:ranked|rated)\b|\b(?:ranked|rated)\s+#?\d+\b|"
    r"\bguarantee(?:d|s)?\b|\bpromise(?:d|s)?\b|\bgarantiz\w*\b|\bpromet\w*\b|"
    r"\bwill\s+(?:sell|appreciate|outperform)\b|\b(?:se vender[aá]|se apreciar[aá])\b",
    re.IGNORECASE,
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.hreflangs: list[tuple[str, str]] = []
        self.links: list[str] = []
        self.anchors: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.metas: list[dict[str, str]] = []
        self.ids: list[str] = []
        self.duplicate_attributes: list[str] = []
        self.main_count = 0
        self.h1_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        names = [name.lower() for name, _ in attrs]
        if len(names) != len(set(names)):
            self.duplicate_attributes.append(tag)
        values = {key.lower(): value or "" for key, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        if tag == "link" and values.get("hreflang"):
            self.hreflangs.append((values["hreflang"], values.get("href", "")))
        if tag == "meta":
            self.metas.append(values)
        if tag == "a":
            self.links.append(values.get("href", ""))
            self.anchors.append(values)
        if tag == "img":
            self.images.append(values)
        if tag == "main":
            self.main_count += 1
        if tag == "h1":
            self.h1_count += 1


def paths() -> list[Path]:
    return [
        ROOT / prefix / f"{slug}.html"
        for slug in REPORTS
        for prefix in (Path("blog"), Path("es/blog"))
    ]


def route(slug: str, language: str) -> str:
    return f"/{'es/' if language == 'es' else ''}blog/{slug}"


def parse(path: Path) -> tuple[str, PageParser]:
    source = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(source)
    return source, parser


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style|template)\b[^>]*>.*?</(?:script|style|template)>",
        " ",
        source,
        flags=re.IGNORECASE | re.DOTALL,
    )
    source = re.sub(r"<!--.*?-->|<[^>]+>", " ", source, flags=re.DOTALL)
    return " ".join(html.unescape(source).split())


def meta_value(parser: PageParser, key: str, value: str) -> list[str]:
    return [item.get("content", "") for item in parser.metas if item.get(key) == value]


def sitemap_urls(name: str) -> set[str]:
    root = ET.parse(ROOT / name).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


def hashes(items: list[Path]) -> dict[str, str]:
    return {
        item.relative_to(ROOT).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in items
    }


def protected_paths() -> list[Path]:
    target = set(paths())
    candidates: set[Path] = set()
    containment = json.loads(
        (ROOT / "data" / "market-report-containment.json").read_text(encoding="utf-8")
    )
    for item in containment["noindexTownReports"]:
        for prefix in (Path("blog"), Path("es/blog")):
            candidates.add(ROOT / prefix / f"market-report-{item['slug']}-nj-2026.html")
    for pair in containment["redirectPairs"]:
        for language in ("en", "es"):
            candidates.add(ROOT / f"{pair['source'][language].lstrip('/')}.html")
    for stub in containment["rebuildPairs"]:
        for prefix in (Path("blog"), Path("es/blog")):
            candidates.add(ROOT / prefix / f"{stub}.html")
    for item in json.loads(
        (ROOT / "data" / "county-market-report-sources-2026-08-26.json").read_text(
            encoding="utf-8"
        )
    )["reports"]:
        for language in ("en", "es"):
            candidates.add(ROOT / f"{item['routes'][language].lstrip('/')}.html")
    candidates.update(
        ROOT / item["file"]
        for item in json.loads(
            (ROOT / "data" / "english-fair-housing-quarantine.json").read_text(
                encoding="utf-8"
            )
        )["pages"]
    )
    result = sorted(path for path in candidates - target if path.exists())
    if set(result) & target:
        raise AssertionError("managed town reports leaked into the protected set")
    return result


def load_generator_module():
    spec = importlib.util.spec_from_file_location("town_market_generator", GENERATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load town market generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TownMarketManifestTests(unittest.TestCase):
    def test_manifest_is_exact_reviewed_primary_source_inventory(self) -> None:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(1, document["schemaVersion"])
        self.assertEqual(REVIEWED_ON, document["reviewedOn"])
        self.assertEqual(REVIEWED_ON, document["reviewedAt"])
        self.assertEqual("approved", document["reviewStatus"])
        self.assertEqual("confirmed", document["publicationRights"])
        self.assertEqual(
            "tools/generate_union_morris_town_market_research.py",
            document["renderer"],
        )
        self.assertTrue(
            document["publicationPolicy"]["directAnswerRule"].startswith(
                "Lead with a 40-60-word"
            )
        )
        self.assertEqual(set(REPORTS), {item["slug"] for item in document["reports"]})

        sources = {item["url"]: item for item in document["sources"]}
        self.assertTrue(COMMON_SOURCES <= set(sources))
        for item in sources.values():
            self.assertEqual(REVIEWED_ON, item["accessedAt"])
            self.assertTrue(item["url"].startswith("https://"))
            self.assertTrue(item["publisher"])
            self.assertTrue(item["reportingPeriod"])

        by_slug = {item["slug"]: item for item in document["reports"]}
        for slug, expected in REPORTS.items():
            item = by_slug[slug]
            self.assertEqual(expected["name"], item["name"])
            self.assertEqual(expected["official"], item["officialGeography"])
            self.assertEqual(expected["county"], item["county"])
            self.assertEqual(expected["code"], item["districtCode"])
            self.assertEqual(expected["published"], item["publishedOn"])
            self.assertEqual(expected["official_url"], item["officialMunicipalityUrl"])
            self.assertIn("ACSDP5Y2024.DP04", item["acsHousingProfile"])
            self.assertIn(expected["official"].replace(" ", "+"), item["acsHousingProfile"])
            self.assertEqual(
                {"en": route(slug, "en"), "es": route(slug, "es")},
                item["routes"],
            )
            expected_values = expected["metrics"]
            keys = (
                "lineItems",
                "averageAssessment",
                "averageTaxBill",
                "numberOfSales",
                "averageSalesPrice",
            )
            for key, expected_value in zip(keys, expected_values):
                metric = item["metrics"][key]
                self.assertEqual(str(expected_value), metric["value"])
                self.assertEqual("nj-treasury-average-residential-2025", metric["sourceId"])
                self.assertIn("2025", metric["definition"])

    def test_manifest_rejects_unreviewed_or_incomplete_evidence(self) -> None:
        module = load_generator_module()
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
        mutations = []
        wrong_review = json.loads(json.dumps(document))
        wrong_review["reviewStatus"] = "draft"
        mutations.append(wrong_review)
        missing_metric = json.loads(json.dumps(document))
        del missing_metric["reports"][0]["metrics"]["averageSalesPrice"]
        mutations.append(missing_metric)
        wrong_route = json.loads(json.dumps(document))
        wrong_route["reports"][0]["routes"]["en"] = "/blog/other"
        mutations.append(wrong_route)
        non_https = json.loads(json.dumps(document))
        non_https["sources"][0]["url"] = "http://example.com"
        mutations.append(non_https)

        for index, mutation in enumerate(mutations):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "manifest.json"
                path.write_text(json.dumps(mutation), encoding="utf-8")
                with self.assertRaises((ValueError, module.ProvenanceError)):
                    module.load_manifest(path)


class TownMarketPageTests(unittest.TestCase):
    def test_exact_pages_keep_indexability_canonical_hreflang_and_sitemaps(self) -> None:
        self.assertEqual(22, len(paths()))
        english_sitemap = sitemap_urls("sitemap.xml")
        spanish_sitemap = sitemap_urls("sitemap-es.xml")
        for slug in REPORTS:
            en_route = route(slug, "en")
            es_route = route(slug, "es")
            expected_hreflang = {
                "en-US": SITE + en_route,
                "es-US": SITE + es_route,
                "es": SITE + es_route,
                "x-default": SITE + en_route,
            }
            for language, deployed, submitted in (
                ("en", en_route, english_sitemap),
                ("es", es_route, spanish_sitemap),
            ):
                path = ROOT / f"{deployed.lstrip('/')}.html"
                source, parser = parse(path)
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertEqual([SITE + deployed], parser.canonicals)
                    self.assertEqual(expected_hreflang, dict(parser.hreflangs))
                    self.assertEqual(language, re.search(r'<html lang="([^"]+)"', source).group(1))
                    robots = " ".join(meta_value(parser, "name", "robots")).lower()
                    self.assertIn("index", robots)
                    self.assertNotIn("noindex", robots)
                    self.assertIn(SITE + deployed, submitted)

    def test_metadata_keeps_town_market_intent_without_volatile_claims(self) -> None:
        from tools.audit_spanish_quality import PATTERNS, visibleish_text

        for path in paths():
            source, parser = parse(path)
            expected = REPORTS[path.stem]
            title = html.unescape(re.search(r"<title>(.*?)</title>", source, re.S).group(1))
            h1 = html.unescape(re.search(r"<h1[^>]*>(.*?)</h1>", source, re.S).group(1))
            description = meta_value(parser, "name", "description")
            llm_context = meta_value(parser, "name", "llm-context")
            spanish = path.parts[-3:-1] == ("es", "blog")
            schemas = [
                json.loads(block)
                for block in re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    source,
                    flags=re.I | re.S,
                )
            ]
            article = next(item for item in schemas if item["@type"] == "BlogPosting")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(1, len(description))
                self.assertEqual(1, len(llm_context))
                self.assertIn(expected["name"], title)
                self.assertIn("2026", title)
                self.assertIn("2025", title)
                self.assertIn("2026", h1)
                self.assertIn("2025", h1)
                self.assertRegex(title.lower(), r"market research|investigaci[oó]n")
                self.assertRegex(h1.lower(), r"finalized 2025 public data|datos p[uú]blicos verificados de 2025")
                self.assertNotRegex(title, r"(?:Real Estate Market|Mercado inmobiliario).*2026(?!.*2025)")
                self.assertNotRegex(title.lower(), r"median|forecast|precio mediano|pron[oó]stico")
                self.assertEqual([title], [html.unescape(x) for x in meta_value(parser, "property", "og:title")])
                self.assertEqual(description, meta_value(parser, "property", "og:description"))
                self.assertEqual([title], [html.unescape(x) for x in meta_value(parser, "name", "twitter:title")])
                self.assertEqual(description, meta_value(parser, "name", "twitter:description"))
                self.assertEqual(title, html.unescape(article["headline"]))
                if spanish:
                    self.assertRegex(llm_context[0], r"^Guía de investigación municipal para ")
                    self.assertNotRegex(
                        llm_context[0],
                        r"Reviewed municipality research|Published values are|town listing data|property valuation",
                    )
                else:
                    self.assertRegex(llm_context[0], r"^Reviewed municipality research for ")

        leaked = visibleish_text(
            '<meta name="llm-context" content="Reviewed municipality research for a town. '
            'Published values are finalized averages, not town listing data or a property valuation.">'
        )
        self.assertRegex(leaked, re.compile(PATTERNS["english_context_words"], re.I))

    def test_visible_metrics_are_exactly_labeled_2025_averages(self) -> None:
        for path in paths():
            source, parser = parse(path)
            text = visible_text(source)
            expected = REPORTS[path.stem]
            line_items, assessment, tax_bill, sales, sales_price = expected["metrics"]
            formatted = {
                f"{line_items:,}",
                f"${assessment:,}",
                f"${tax_bill:,}",
                f"{sales:,}",
                f"${float(sales_price):,.2f}",
            }
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn(expected["official"], text)
                self.assertIn(f"C/D {expected['code']}", text)
                for value in formatted:
                    self.assertIn(value, text)
                self.assertRegex(text, re.compile(r"average, not a median|promedio, no una mediana", re.I))
                self.assertRegex(
                    text,
                    re.compile(r"finalized 2025|(?:fila estatal|informaci[oó]n) finalizada[^.]*2025", re.I),
                )
                self.assertRegex(text, re.compile(r"not a 2026 listing-service|no es un dato de 2026", re.I))
                self.assertIn(REVIEWED_ON, text)
                self.assertTrue(COMMON_SOURCES <= set(parser.links))
                self.assertIn(expected["official_url"], parser.links)

    def test_pages_lead_with_a_concise_source_attributed_direct_answer(self) -> None:
        for path in paths():
            source, _ = parse(path)
            expected = REPORTS[path.stem]
            line_items, assessment, tax_bill, sales, sales_price = expected["metrics"]
            direct_values = {
                f"${assessment:,}",
                f"${tax_bill:,}",
                f"{sales:,}",
                f"${float(sales_price):,.2f}",
            }
            match = re.search(
                r'<p class="dek" data-direct-answer="finalized-2025-treasury-row">(.*?)</p>',
                source,
                re.I | re.S,
            )
            self.assertIsNotNone(match, path)
            answer = " ".join(
                html.unescape(re.sub(r"<[^>]+>", " ", match.group(1))).split()
            )
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertGreaterEqual(len(answer.split()), 40)
                self.assertLessEqual(len(answer.split()), 60)
                self.assertLess(
                    source.index(match.group(0)), source.index('<div class="content">')
                )
                self.assertIn("2025", answer)
                self.assertIn("New Jersey Treasury", answer)
                self.assertIn(expected["county"], answer)
                self.assertIn(f"C/D {expected['code']}", answer)
                for value in direct_values:
                    self.assertIn(value, answer)
                self.assertRegex(
                    answer,
                    r"not current listing data|no listados vigentes",
                )
                if path.parts[-3:-1] == ("es", "blog"):
                    self.assertIn("un avalúo promedio de", answer)
                    self.assertNotIn("una tasación promedio de", answer)
                    self.assertIn(
                        "El avalúo promedio de la tabla estatal; no es precio de oferta ni tasación.",
                        source,
                    )

    def test_pages_explain_scope_method_updates_and_property_limits(self) -> None:
        for path in paths():
            source, _ = parse(path)
            text = visible_text(source)
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn('data-geography-scope="municipality"', source)
                self.assertIn('data-publication-policy="reviewed-primary-sources"', source)
                self.assertRegex(text, re.compile(r"county.*(?:does not|no).*town|condado.*no.*municip", re.I))
                self.assertRegex(text, re.compile(r"CMA|an[aá]lisis comparativo", re.I))
                self.assertRegex(text, re.compile(r"Return to the original source|Vuelva a la fuente original", re.I))
                self.assertRegex(text, re.compile(r"Corrections?|Correcciones", re.I))
                self.assertRegex(text, re.compile(r"do not reproduce|no reproducimos", re.I))
                self.assertRegex(
                    text,
                    re.compile(r"criteria you choose|criterios .* que usted elija", re.I),
                )
                self.assertIsNone(FORBIDDEN_VISIBLE.search(text), text)

    def test_fair_housing_wording_sweep_has_zero_risky_phrases(self) -> None:
        findings: list[tuple[str, str]] = []
        for path in paths():
            source, _ = parse(path)
            text = visible_text(source)
            findings.extend(
                (path.relative_to(ROOT).as_posix(), match.group(0))
                for match in FAIR_HOUSING_RISKY_VISIBLE.finditer(text)
            )
        self.assertEqual([], findings, f"fair-housing risky phrase count: {len(findings)}")

    def test_schema_matches_visible_article_and_breadcrumb_content_only(self) -> None:
        for path in paths():
            source, _ = parse(path)
            documents = [
                json.loads(block)
                for block in re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    source,
                    flags=re.I | re.S,
                )
            ]
            types = {item["@type"] for item in documents}
            article = next(item for item in documents if item["@type"] == "BlogPosting")
            language = "es" if path.parts[-3:-1] == ("es", "blog") else "en"
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual({"BlogPosting", "BreadcrumbList"}, types)
                self.assertEqual(REPORTS[path.stem]["published"], article["datePublished"])
                self.assertEqual(PAGE_MODIFIED_ON, article["dateModified"])
                self.assertIn(
                    f'<meta name="last-updated" content="{PAGE_MODIFIED_ON}">',
                    source,
                )
                self.assertIn(
                    f'<meta property="article:modified_time" content="{PAGE_MODIFIED_ON}">',
                    source,
                )
                self.assertIn(
                    f'<time datetime="{REVIEWED_ON}">{REVIEWED_ON}</time>',
                    source,
                )
                self.assertEqual(SITE + route(path.stem, language), article["url"])
                self.assertNotRegex(
                    source,
                    r'"@type"\s*:\s*"(?:FAQPage|AggregateRating|Review|RealEstateListing)"',
                )

    def test_homepage_design_accessibility_and_mobile_contract(self) -> None:
        for path in paths():
            source, parser = parse(path)
            spanish = path.parts[-3:-1] == ("es", "blog")
            prefix = "/es" if spanish else ""
            town_slug = path.stem.removeprefix("market-report-").removesuffix("-nj-2026")
            county_slug = REPORTS[path.stem]["county"].lower()
            expected_links = {
                f"{prefix}/towns/{town_slug}",
                f"{prefix}/counties/{county_slug}-county",
                f"{prefix}/home-valuation",
                "/es#contact" if spanish else "/contact",
            }
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertLess(len(source.encode("utf-8")), 42_000)
                self.assertEqual(1, parser.main_count)
                self.assertEqual(1, parser.h1_count)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                self.assertEqual([], parser.duplicate_attributes)
                self.assertIn('href="#main"', source)
                self.assertTrue(expected_links <= set(parser.links))
                self.assertIn("/css/styles.css", source)
                self.assertIn("/js/site-cta.js", source)
                self.assertIn("G-KMS6H85LB0", source)
                for token in PALETTE:
                    self.assertIn(token, source)
                self.assertIn("'Playfair Display'", source)
                self.assertIn("'Inter'", source)
                self.assertRegex(source, r"min-height:\s*(?:44|48|52)px")
                self.assertIn(":focus-visible", source)
                self.assertIn("overflow-wrap", source)
                self.assertIn("minmax(0, 1fr)", source)
                brand_rule = re.search(r"\.market-brand\s*\{(?P<body>[^}]*)\}", source)
                self.assertIsNotNone(brand_rule)
                self.assertIn("flex: 0 0 auto", brand_rule.group("body"))
                self.assertIn("white-space: nowrap", brand_rule.group("body"))
                self.assertRegex(
                    source,
                    re.compile(
                        r"@media\s*\(max-width:\s*1280px\).*?"
                        r"\.market-menu-button\s*\{[^}]*display:\s*inline-flex.*?"
                        r"\.market-nav-links\s*\{[^}]*display:\s*none",
                        re.S,
                    ),
                )
                self.assertIn(
                    ".market-brand { flex: 1 1 auto; min-width: 0; max-width: none; "
                    "white-space: normal; line-height: 1.05; }",
                    source,
                )
                self.assertIn(
                    ".market-menu-button { flex: 0 0 auto; }",
                    source,
                )

    def test_links_fragments_images_and_interactive_names_are_valid(self) -> None:
        for path in paths():
            source, parser = parse(path)
            viewport = meta_value(parser, "name", "viewport")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(["width=device-width, initial-scale=1.0"], viewport)
                for image in parser.images:
                    self.assertIn("alt", image)
                    self.assertTrue(image["alt"].strip())
                for anchor in parser.anchors:
                    href = anchor.get("href", "")
                    self.assertTrue(href)
                    self.assertFalse(href.lower().startswith("javascript:"))
                    if anchor.get("target") == "_blank":
                        self.assertIn("noopener", anchor.get("rel", "").split())
                    if not href.startswith("/") and not href.startswith("#"):
                        self.assertEqual("https", urlsplit(href).scheme)
                        continue
                    parsed = urlsplit(href)
                    route_path = parsed.path
                    target = path
                    if route_path:
                        if route_path == "/":
                            target = ROOT / "index.html"
                        elif route_path.endswith("/"):
                            target = ROOT / route_path.lstrip("/") / "index.html"
                        else:
                            clean = ROOT / route_path.lstrip("/")
                            if clean.is_dir():
                                target = clean / "index.html"
                            else:
                                target = clean if clean.suffix else Path(str(clean) + ".html")
                    self.assertTrue(target.exists(), f"broken internal link {href} in {path}")
                    if parsed.fragment:
                        _, target_parser = parse(target)
                        self.assertIn(
                            parsed.fragment,
                            target_parser.ids,
                            f"broken fragment {href} in {path}",
                        )

                for tag in ("a", "button"):
                    pattern = re.compile(
                        rf"<{tag}\b(?P<attrs>[^>]*)>(?P<body>.*?)</{tag}>",
                        re.I | re.S,
                    )
                    for match in pattern.finditer(source):
                        body = re.sub(r"<[^>]+>", " ", match.group("body"))
                        body = " ".join(html.unescape(body).split())
                        aria = re.search(
                            r'\baria-label=["\']([^"\']+)["\']',
                            match.group("attrs"),
                            re.I,
                        )
                        self.assertTrue(body or (aria and aria.group(1).strip()))


class TownMarketGeneratorTests(unittest.TestCase):
    def test_generator_is_deterministic_idempotent_and_narrow(self) -> None:
        self.assertTrue(GENERATOR.exists())
        target_before = hashes(paths())
        protected = protected_paths()
        protected_before = hashes(protected)
        outputs: list[str] = []
        for mode in ("--check", "--check", "--write", "--write"):
            result = subprocess.run(
                [sys.executable, str(GENERATOR.relative_to(ROOT)), mode],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            outputs.append(result.stdout)
            self.assertEqual(target_before, hashes(paths()))
            self.assertEqual(protected_before, hashes(protected))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[2], outputs[3])

    def test_legacy_generators_remain_quarantined(self) -> None:
        for relative in ("generate_blog.py", "generate_county_reports_and_comparisons.py"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("market_report_publication_gate", source)
            result = subprocess.run(
                [sys.executable, relative],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("quarantined", (result.stdout + result.stderr).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
