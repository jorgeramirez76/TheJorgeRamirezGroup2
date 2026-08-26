#!/usr/bin/env python3
"""Regression contract for the five retained bilingual county research reports."""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
MANIFEST = ROOT / "data" / "county-market-report-sources-2026-08-26.json"
GENERATOR = ROOT / "tools" / "generate_county_market_research.py"
PALETTE = {"#1A1A1A", "#C41230", "#8B0D22", "#B8962E", "#FAFAF8"}

REPORTS = {
    "essex-county-nj-real-estate-market-2026": {
        "county": "Essex",
        "fips": "34013",
        "period": "2026 research path",
        "published": "2026-03-08",
        "directory": "https://essexcountynj.org/",
    },
    "morris-county-nj-real-estate-market-2026": {
        "county": "Morris",
        "fips": "34027",
        "period": "2026 research path",
        "published": "2026-03-08",
        "directory": "https://www.morriscountynj.gov/Residents/Community-Information/Cities-and-Towns",
    },
    "hudson-county-real-estate-market-q2-2026": {
        "county": "Hudson",
        "fips": "34017",
        "period": "Q2 2026 research path",
        "published": "2026-04-16",
        "directory": "https://www.hudsoncountynj.org/",
    },
    "middlesex-county-real-estate-market-q2-2026": {
        "county": "Middlesex",
        "fips": "34023",
        "period": "Q2 2026 research path",
        "published": "2026-04-16",
        "directory": "https://www.middlesexcountynj.gov/government/municipalities",
    },
    "union-county-nj-real-estate-market-report-2026": {
        "county": "Union",
        "fips": "34039",
        "period": "2026 research path",
        "published": "2026-03-08",
        "directory": "https://ucnj.org/municipalities/",
    },
}

COMMON_SOURCES = {
    "https://www.njrealtor.com/research/10k/",
    "https://njar-public.stats.10kresearch.com/reports",
    "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml",
    "https://www.nj.gov/treasury/taxation/pdf/lpt/class4/2025AvgResStat.pdf",
    "https://www.nj.gov/treasury/taxation/lpt/county_equalized.shtml",
    "https://www.nj.gov/dca/codes/reporter/",
    "https://www.census.gov/acs/www/data/data-tables-and-tools/data-profiles/",
}

FORBIDDEN_VISIBLE = re.compile(
    r"\$\s*\d|\b\d+(?:\.\d+)?\s*%|\b\d+\s+(?:days? on market|sales|listings|homes)\b|"
    r"forecast|prediction|predicts?|projected|appreciat|hottest|"
    r"\b(?:best|perfect|ideal)\s+(?:town|market|place|community)|"
    r"top[- ](?:ranked|rated|town|market)|seller.?s market|buyer.?s market|"
    r"act now|before prices|\bfamil(?:y|ies)\b|\bschools?\b|\bsafe(?:ty)?\b|"
    r"crime rate|\bROI\b|guarantee|garantiz|pron[oó]stic|predicci[oó]n|"
    r"apreciaci[oó]n|m[aá]s (?:popular|caliente)|mejor(?:es)? (?:pueblo|mercado|lugar)",
    re.IGNORECASE,
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.hreflangs: list[tuple[str, str]] = []
        self.links: list[str] = []
        self.metas: list[dict[str, str]] = []
        self.main_count = 0
        self.h1_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        if tag == "link" and values.get("hreflang"):
            self.hreflangs.append((values["hreflang"], values.get("href", "")))
        if tag == "meta":
            self.metas.append(values)
            if values.get("name", "").lower() == "robots":
                self.robots.append(values.get("content", ""))
        if tag == "a":
            self.links.append(values.get("href", ""))
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


def protected_market_and_fallback_paths() -> list[Path]:
    market = json.loads(
        (ROOT / "data" / "market-report-containment.json").read_text(encoding="utf-8")
    )
    protected: set[Path] = set()
    for item in market["noindexTownReports"]:
        for prefix in (Path("blog"), Path("es/blog")):
            protected.add(ROOT / prefix / f"market-report-{item['slug']}-nj-2026.html")
    for pair in market["redirectPairs"]:
        for language in ("en", "es"):
            protected.add(ROOT / f"{pair['source'][language].lstrip('/')}.html")
    target_names = {f"{slug}.html" for slug in REPORTS}
    for stub in market["rebuildPairs"]:
        for prefix in (Path("blog"), Path("es/blog")):
            candidate = ROOT / prefix / f"{stub}.html"
            if candidate.name not in target_names:
                protected.add(candidate)

    fair = json.loads(
        (ROOT / "data" / "english-fair-housing-quarantine.json").read_text(
            encoding="utf-8"
        )
    )
    protected.update(ROOT / item["file"] for item in fair["pages"])
    town = json.loads(
        (ROOT / "data" / "english-noindex-town-fallbacks.json").read_text(
            encoding="utf-8"
        )
    )
    protected.update(
        ROOT / "towns" / f"{slug}.html"
        for group in town["groups"]
        for slug in group["slugs"]
    )
    result = sorted(path for path in protected if path.exists())
    if set(result) & set(paths()):
        raise AssertionError("target county pages leaked into the protected set")
    return result


class CountySourceManifestTests(unittest.TestCase):
    def test_manifest_has_exact_reviewed_inventory_and_primary_sources(self) -> None:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(1, document["schemaVersion"])
        self.assertEqual("2026-08-26", document["reviewedOn"])
        self.assertEqual("tools/generate_county_market_research.py", document["renderer"])
        self.assertEqual(set(REPORTS), {item["slug"] for item in document["reports"]})

        sources = {item["url"]: item for item in document["sharedSources"]}
        self.assertTrue(COMMON_SOURCES <= set(sources))
        for item in sources.values():
            self.assertEqual("2026-08-26", item["accessedOn"])
            self.assertTrue(item["url"].startswith("https://"))
            self.assertIn("use", item)
            self.assertIn("limit", item)
        self.assertEqual(
            "direct public county-report portal linked by NJ Realtors; tables are viewed at the source and are not reproduced",
            sources["https://njar-public.stats.10kresearch.com/reports"]["publicationHandling"],
        )

        by_slug = {item["slug"]: item for item in document["reports"]}
        for slug, expected in REPORTS.items():
            item = by_slug[slug]
            self.assertEqual(expected["county"], item["county"])
            self.assertEqual(expected["fips"], item["countyFips"])
            self.assertEqual(expected["period"], item["periodLabel"])
            self.assertEqual(expected["published"], item["publishedOn"])
            self.assertEqual(expected["directory"], item["countyDirectory"]["url"])
            self.assertEqual("2026-08-26", item["countyDirectory"]["accessedOn"])
            self.assertEqual(
                f"https://data.census.gov/table/ACSDP5Y2024.DP04?g=050XX00US{expected['fips']}",
                item["acsHousingProfile"],
            )

    def test_manifest_contains_no_copied_market_values_or_forecast_fields(self) -> None:
        source = MANIFEST.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"\$\s*\d|\b\d+(?:\.\d+)?\s*%")
        document = json.loads(source)
        forbidden_keys = {
            "medianPrice",
            "inventory",
            "daysOnMarket",
            "yearOverYear",
            "forecast",
            "ranking",
        }

        def walk(value: object) -> None:
            if isinstance(value, dict):
                self.assertTrue(forbidden_keys.isdisjoint(value))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(document)


class CountyPageContractTests(unittest.TestCase):
    def test_exact_ten_pages_keep_canonical_routes_and_reciprocal_hreflang(self) -> None:
        self.assertEqual(10, len(paths()))
        english_sitemap = sitemap_urls("sitemap.xml")
        spanish_sitemap = sitemap_urls("sitemap-es.xml")
        for slug in REPORTS:
            en_route = route(slug, "en")
            es_route = route(slug, "es")
            for language, deployed, submitted in (
                ("en", en_route, english_sitemap),
                ("es", es_route, spanish_sitemap),
            ):
                path = ROOT / f"{deployed.lstrip('/')}.html"
                source, parser = parse(path)
                expected = {
                    "en-US": SITE + en_route,
                    "es-US": SITE + es_route,
                    "es": SITE + es_route,
                    "x-default": SITE + en_route,
                }
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertEqual([SITE + deployed], parser.canonicals)
                    self.assertEqual(expected, dict(parser.hreflangs))
                    self.assertIn("index", " ".join(parser.robots).lower())
                    self.assertNotIn("noindex", " ".join(parser.robots).lower())
                    self.assertIn(SITE + deployed, submitted)
                    self.assertEqual(language, re.search(r'<html lang="([^"]+)"', source).group(1))

    def test_metadata_preserves_county_market_intent_and_is_consistent(self) -> None:
        for path in paths():
            source, parser = parse(path)
            title = re.search(r"<title>(.*?)</title>", source, re.I | re.S).group(1)
            description = meta_value(parser, "name", "description")
            self.assertEqual(1, len(description))
            county = REPORTS[path.stem]["county"]
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn(county, title)
                self.assertIn("2026", title)
                self.assertRegex(
                    title.lower(), r"(?:real estate|inmobiliari[oa]|bienes ra[ií]ces)"
                )
                self.assertRegex(title.lower(), r"(?:market|mercado)")
                self.assertNotRegex(title.lower(), r"price|forecast|hottest|precio|pron[oó]stico")
                self.assertNotRegex(description[0].lower(), r"\$|forecast|hottest|pron[oó]stico")
                self.assertEqual([title], meta_value(parser, "property", "og:title"))
                self.assertEqual(description, meta_value(parser, "property", "og:description"))
                self.assertEqual([title], meta_value(parser, "name", "twitter:title"))
                self.assertEqual(description, meta_value(parser, "name", "twitter:description"))

    def test_visible_research_method_separates_county_municipality_and_property(self) -> None:
        treasury_labels = (
            "# of Line Items",
            "Avg Assessment",
            "Avg Tax Bill",
            "# of Sales",
            "Avg Sales Price",
        )
        for path in paths():
            source, parser = parse(path)
            text = visible_text(source)
            language = "es" if path.parts[-3:-1] == ("es", "blog") else "en"
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn('data-geography-scope="county-not-municipality"', source)
                self.assertIn('data-publication-policy="links-not-tables"', source)
                self.assertIn("2026-08-26", source)
                self.assertIn("2025 Average Residential Statistics", text)
                for label in treasury_labels:
                    self.assertIn(label, text)
                self.assertRegex(
                    text,
                    re.compile(
                        r"average is not a median|promedio no es una mediana",
                        re.IGNORECASE,
                    ),
                )
                self.assertRegex(
                    text,
                    re.compile(
                        r"county.*(?:does not|no).*municipalit|condado.*no.*municip",
                        re.IGNORECASE,
                    ),
                )
                self.assertIn("CMA", text)
                self.assertRegex(
                    text,
                    re.compile(
                        r"Correction|Correcciones",
                        re.IGNORECASE,
                    ),
                )
                self.assertIn(REPORTS[path.stem]["directory"], parser.links)
                self.assertIn(
                    f"https://data.census.gov/table/ACSDP5Y2024.DP04?g=050XX00US{REPORTS[path.stem]['fips']}",
                    parser.links,
                )
                self.assertTrue(COMMON_SOURCES <= set(parser.links))

    def test_pages_publish_no_volatile_market_claims_or_steering(self) -> None:
        for path in paths():
            source, _ = parse(path)
            text = visible_text(source)
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(FORBIDDEN_VISIBLE.search(text), text)
                self.assertNotRegex(
                    text,
                    re.compile(
                        r"NJ Realtors.{0,80}(?:permission|authorized us|licensed us)",
                        re.IGNORECASE,
                    ),
                )
                self.assertRegex(
                    text,
                    re.compile(
                        r"do not reproduce|no reproduce",
                        re.IGNORECASE,
                    ),
                )

    def test_schema_is_limited_to_visible_article_and_breadcrumb_content(self) -> None:
        for path in paths():
            source, _ = parse(path)
            blocks = re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                source,
                re.IGNORECASE | re.DOTALL,
            )
            documents = [json.loads(block) for block in blocks]
            types = {document["@type"] for document in documents}
            article = next(item for item in documents if item["@type"] == "BlogPosting")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual({"BlogPosting", "BreadcrumbList"}, types)
                self.assertEqual("2026-08-26", article["dateModified"])
                self.assertEqual(REPORTS[path.stem]["published"], article["datePublished"])
                language = "es" if path.parts[-3:-1] == ("es", "blog") else "en"
                self.assertEqual(SITE + route(path.stem, language), article["url"])
                self.assertNotRegex(source, r"FAQPage|AggregateRating|RealEstateListing|Place")

    def test_pages_follow_homepage_visual_accessibility_and_conversion_contracts(self) -> None:
        for path in paths():
            source, parser = parse(path)
            spanish = path.parts[-3:-1] == ("es", "blog")
            prefix = "/es" if spanish else ""
            county_slug = REPORTS[path.stem]["county"].lower()
            expected_links = {
                f"{prefix}/counties/{county_slug}-county",
                f"{prefix}/home-valuation",
                f"{prefix}/sell-your-home",
                f"{prefix}/contact",
            }
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertLess(len(source.encode("utf-8")), 36_000)
                self.assertEqual(1, parser.main_count)
                self.assertEqual(1, parser.h1_count)
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


class CountyGeneratorSafetyTests(unittest.TestCase):
    def test_generator_is_deterministic_and_preserves_every_other_quarantine(self) -> None:
        self.assertTrue(GENERATOR.exists())
        target_before = hashes(paths())
        protected = protected_market_and_fallback_paths()
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

    def test_legacy_county_generator_remains_fail_closed(self) -> None:
        path = ROOT / "generate_county_reports_and_comparisons.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn("market_report_publication_gate", source)
        self.assertNotRegex(
            source,
            r"COUNTY_TEMPLATE|median_price|yoy_change|days_on_market|forecast|school_rating",
        )
        result = subprocess.run(
            [sys.executable, path.name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("quarantined", (result.stdout + result.stderr).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
