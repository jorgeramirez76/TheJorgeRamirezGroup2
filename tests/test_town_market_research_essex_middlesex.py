#!/usr/bin/env python3
"""Regression contract for the Essex/Middlesex/Somerset town research batch."""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
PAGE_MODIFIED_ON = "2026-08-27"
MANIFEST = ROOT / "data" / "town-market-research-essex-middlesex-somerset.json"
RENDERER = ROOT / "tools" / "generate_town_market_research_essex_middlesex.py"

EXPECTED = {
    "glen-ridge": {
        "county": "Essex",
        "district": "GLEN RIDGE TWP",
        "code": "0708",
        "values": ("2,293", "$674,911", "$23,676", "79", "$1,200,070.27"),
    },
    "livingston": {
        "county": "Essex",
        "district": "LIVINGSTON TWP",
        "code": "0710",
        "values": ("10,151", "$729,727", "$18,469", "307", "$1,142,065.20"),
    },
    "maplewood": {
        "county": "Essex",
        "district": "MAPLEWOOD TWP",
        "code": "0711",
        "values": ("6,888", "$807,155", "$19,380", "219", "$908,544.95"),
    },
    "montclair": {
        "county": "Essex",
        "district": "MONTCLAIR TWP",
        "code": "0713",
        "values": ("9,605", "$639,628", "$22,489", "311", "$1,285,489.41"),
    },
    "short-hills": {
        "county": "Essex",
        "district": "MILLBURN TWP",
        "code": "0712",
        "values": ("6,219", "$1,302,529", "$26,298", "207", "$1,945,207.55"),
    },
    "south-orange": {
        "county": "Essex",
        "district": "SOUTH ORANGE VILLAGE TW",
        "code": "0719",
        "values": ("4,353", "$879,273", "$22,720", "153", "$990,016.57"),
    },
    "west-orange": {
        "county": "Essex",
        "district": "WEST ORANGE TWP",
        "code": "0722",
        "values": ("13,326", "$615,472", "$16,168", "180", "$690,053.18"),
    },
    "metuchen": {
        "county": "Middlesex",
        "district": "METUCHEN BORO",
        "code": "1209",
        "values": ("4,601", "$190,473", "$13,819", "67", "$730,566.34"),
    },
    "south-brunswick": {
        "county": "Middlesex",
        "district": "SOUTH BRUNSWICK TWP",
        "code": "1221",
        "values": ("13,366", "$196,320", "$10,951", "301", "$674,347.81"),
    },
    "woodbridge": {
        "county": "Middlesex",
        "district": "WOODBRIDGE TWP",
        "code": "1225",
        "values": ("26,447", "$79,752", "$9,597", "476", "$487,111.87"),
    },
    "warren-township": {
        "county": "Somerset",
        "district": "WARREN TWP",
        "code": "1820",
        "values": ("5,393", "$970,235", "$16,999", "34", "$1,133,999.97"),
    },
}

METRIC_LABELS = (
    "# of Line Items",
    "Avg Assessment",
    "Avg Tax Bill",
    "# of Sales",
    "Avg Sales Price",
)
SOURCE_IDS = {
    "nj-treasury-statistics",
    "nj-treasury-average-residential-2025",
    "nj-treasury-average-residential-2026-context",
    "njr-market-data",
    "njr-public-county-portal",
    "nj-dca-fair-housing",
}
PALETTE = {
    "#0A0A0A",
    "#1A1A1A",
    "#C41230",
    "#8B0D22",
    "#B8962E",
    "#D4AF5A",
    "#FAFAF8",
    "#F8F6F2",
}

FAIR_HOUSING_RISK = re.compile(
    r"\b(?:"
    r"family|families|family[- ]friendly|school|schools|safe town|safest|"
    r"best town|right town|perfect town|top[- ]rated|low[- ]crime|crime rate|"
    r"prestigious|exclusive|guarantee(?:d|s)?|promis(?:e|es|ed|ing)|"
    r"outperform(?:s|ed|ing)?|highest price|will sell|perfect for|"
    r"familia(?:s)?|familiar(?:es)?|escuela(?:s)?|m[aá]s segur[oa]s?|"
    r"pueblo segur[oa]|municipio segur[oa]|mejor(?:es)? (?:pueblo|municipio|localidad)|"
    r"pueblo adecuado|municipio adecuado|ideal para|prestigios[oa]s?|"
    r"exclusiv[oa]s?|garantiz\w*|promet\w*|promesa(?:s)?|mejor precio|"
    r"vender[aá]|performance promise|promesa de rendimiento"
    r")\b",
    re.I,
)


def page_path(slug: str, language: str) -> Path:
    prefix = Path("blog") if language == "en" else Path("es/blog")
    return ROOT / prefix / f"market-report-{slug}-nj-2026.html"


def route(slug: str, language: str) -> str:
    prefix = "/blog" if language == "en" else "/es/blog"
    return f"{prefix}/market-report-{slug}-nj-2026"


def resolve_internal(href: str) -> Path | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return None
    clean = parsed.path
    if clean == "/":
        return ROOT / "index.html"
    if clean.endswith("/"):
        return ROOT / clean.lstrip("/") / "index.html"
    candidate = ROOT / clean.lstrip("/")
    if candidate.suffix:
        return candidate
    html_candidate = ROOT / f"{clean.lstrip('/')}.html"
    if html_candidate.exists():
        return html_candidate
    return candidate / "index.html"


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.hreflangs: dict[str, str] = {}
        self.robots: list[str] = []
        self.viewports: list[str] = []
        self.ids: list[str] = []
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.duplicate_attributes: list[tuple[str, str]] = []
        self.skip_targets: list[str] = []
        self.main_count = 0
        self.h1_count = 0
        self.html_lang = ""
        self.json_blocks: list[str] = []
        self._json_depth = 0
        self._json_buffer: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        names = [name.casefold() for name, _ in attrs]
        for name, count in Counter(names).items():
            if count > 1:
                self.duplicate_attributes.append((tag, name))
        values = {name.casefold(): value or "" for name, value in attrs}
        if tag == "html":
            self.html_lang = values.get("lang", "")
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "main":
            self.main_count += 1
        if tag == "h1":
            self.h1_count += 1
        if tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        if tag == "link" and values.get("hreflang"):
            self.hreflangs[values["hreflang"]] = values.get("href", "")
        if tag == "meta" and values.get("name", "").casefold() == "robots":
            self.robots.append(values.get("content", ""))
        if tag == "meta" and values.get("name", "").casefold() == "viewport":
            self.viewports.append(values.get("content", ""))
        if tag == "a":
            self.links.append(values)
            if "skip-link" in values.get("class", "").split():
                self.skip_targets.append(values.get("href", ""))
        if tag == "img":
            self.images.append(values)
        if tag == "script" and values.get("type", "").casefold() == "application/ld+json":
            self._json_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_depth:
            self.json_blocks.append("".join(self._json_buffer))
            self._json_buffer.clear()
            self._json_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._json_depth:
            self._json_buffer.append(data)


def parse(path: Path) -> tuple[str, AuditParser, list[dict]]:
    source = path.read_text(encoding="utf-8")
    parser = AuditParser()
    parser.feed(source)
    blocks = [json.loads(block) for block in parser.json_blocks]
    return source, parser, blocks


def visible_text(source: str) -> str:
    """Return body copy while excluding CSS, scripts, and structured data."""

    body_match = re.search(r"<body\b[^>]*>(.*?)</body>", source, re.I | re.S)
    body = body_match.group(1) if body_match else source
    body = re.sub(r"<script\b[^>]*>.*?</script>", " ", body, flags=re.I | re.S)
    body = re.sub(r"<style\b[^>]*>.*?</style>", " ", body, flags=re.I | re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", html.unescape(body)).strip()


class TownResearchManifestTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_dated_and_has_the_exact_isolated_scope(self) -> None:
        self.assertEqual(1, self.document["schemaVersion"])
        self.assertEqual(REVIEWED_ON, self.document["reviewedOn"])
        self.assertEqual(
            "tools/generate_town_market_research_essex_middlesex.py",
            self.document["renderer"],
        )
        self.assertEqual(set(EXPECTED), {item["slug"] for item in self.document["reports"]})
        self.assertEqual(11, len(self.document["reports"]))
        self.assertEqual(SOURCE_IDS, {item["id"] for item in self.document["sharedSources"]})
        self.assertTrue(
            self.document["publicationPolicy"]["directAnswerRule"].startswith(
                "Lead with a 40-60-word"
            )
        )

    def test_each_report_keeps_the_exact_2025_treasury_row(self) -> None:
        reports = {item["slug"]: item for item in self.document["reports"]}
        for slug, expected in EXPECTED.items():
            with self.subTest(slug=slug):
                report = reports[slug]
                self.assertEqual(expected["county"], report["county"])
                self.assertEqual(expected["district"], report["treasuryDistrict"])
                self.assertEqual(expected["code"], report["treasuryCode"])
                self.assertEqual(2025, report["statisticsYear"])
                self.assertEqual(
                    dict(zip(METRIC_LABELS, expected["values"])), report["statistics"]
                )
                self.assertEqual(
                    {
                        "en": route(slug, "en"),
                        "es": route(slug, "es"),
                    },
                    report["routes"],
                )

    def test_all_source_records_are_primary_dated_and_scope_limited(self) -> None:
        for source in self.document["sharedSources"]:
            with self.subTest(source=source["id"]):
                self.assertEqual(REVIEWED_ON, source["accessedOn"])
                self.assertTrue(source["url"].startswith("https://"))
                self.assertTrue(source["publisher"])
                self.assertTrue(source["use"])
                self.assertTrue(source["limit"])
        source_map = {item["id"]: item for item in self.document["sharedSources"]}
        self.assertIn("2025AvgResStat.pdf", source_map["nj-treasury-average-residential-2025"]["url"])
        self.assertIn("2026AvgResStat.pdf", source_map["nj-treasury-average-residential-2026-context"]["url"])
        self.assertIn("do not infer", source_map["nj-treasury-average-residential-2026-context"]["limit"].casefold())
        for report in self.document["reports"]:
            for key in ("municipalitySource", "censusSource"):
                source = report[key]
                self.assertEqual(REVIEWED_ON, source["accessedOn"])
                self.assertTrue(source["url"].startswith("https://"))
                self.assertTrue(source["publisher"])
                self.assertTrue(source["use"])


class TownResearchPageTests(unittest.TestCase):
    def test_twenty_two_pages_have_exact_canonical_and_hreflang_contract(self) -> None:
        for slug in EXPECTED:
            for language in ("en", "es"):
                path = page_path(slug, language)
                source, parser, _ = parse(path)
                current = SITE + route(slug, language)
                alternate_language = "es" if language == "en" else "en"
                alternate = SITE + route(slug, alternate_language)
                with self.subTest(slug=slug, language=language):
                    self.assertEqual([current], parser.canonicals)
                    self.assertEqual(
                        {
                            "en-US": SITE + route(slug, "en"),
                            "es-US": SITE + route(slug, "es"),
                            "x-default": SITE + route(slug, "en"),
                        },
                        parser.hreflangs,
                    )
                    self.assertIn(alternate, source)
                    self.assertEqual(["index, follow, max-image-preview:large"], parser.robots)

    def test_pages_render_exact_year_labeled_average_statistics(self) -> None:
        for slug, expected in EXPECTED.items():
            for language in ("en", "es"):
                source, _, _ = parse(page_path(slug, language))
                visible = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.I | re.S)
                visible = re.sub(r"<script\b[^>]*>.*?</script>", " ", visible, flags=re.I | re.S)
                with self.subTest(slug=slug, language=language):
                    self.assertIn('data-market-research-batch="essex-middlesex-somerset"', source)
                    self.assertIn("2025", visible)
                    self.assertIn(expected["district"], visible)
                    self.assertIn(expected["code"], visible)
                    for value in expected["values"]:
                        self.assertIn(value, visible)
                    for label in METRIC_LABELS:
                        self.assertIn(label, visible)
                    self.assertNotRegex(visible.casefold(), r"\bmedian(?:a|o|as|os)?\b")
                    self.assertNotRegex(visible.casefold(), r"\b2026\s+(?:average|promedio)")

    def test_pages_lead_with_a_concise_source_attributed_direct_answer(self) -> None:
        for slug, expected in EXPECTED.items():
            for language in ("en", "es"):
                source, _, _ = parse(page_path(slug, language))
                match = re.search(
                    r'<p class="dek" data-direct-answer="finalized-2025-treasury-row">(.*?)</p>',
                    source,
                    re.I | re.S,
                )
                self.assertIsNotNone(match, f"missing direct answer: {slug} {language}")
                answer = " ".join(
                    html.unescape(re.sub(r"<[^>]+>", " ", match.group(1))).split()
                )
                with self.subTest(slug=slug, language=language):
                    self.assertGreaterEqual(len(answer.split()), 40)
                    self.assertLessEqual(len(answer.split()), 60)
                    self.assertLess(
                        source.index(match.group(0)), source.index('<div class="content">')
                    )
                    self.assertIn("2025", answer)
                    self.assertIn("New Jersey Treasury", answer)
                    self.assertIn(expected["district"], answer)
                    self.assertIn(expected["county"], answer)
                    for value in expected["values"][1:]:
                        self.assertIn(value, answer)
                    self.assertRegex(
                        answer,
                        r"not current listing data|no datos vigentes de listados",
                    )
                    if language == "es":
                        self.assertIn("un avalúo promedio de", answer)
                        self.assertNotIn("una tasación promedio de", answer)
                        self.assertIn(
                            "Avalúo promedio, con la etiqueta exacta de la fuente",
                            source,
                        )

    def test_pages_are_source_led_neutral_and_show_methodology_limits(self) -> None:
        risky = re.compile(
            r"\b(?:safest|safe town|low[- ]crime|crime rate|family[- ]friendly|"
            r"best town|top[- ]rated|prestigious|exclusive|"
            r"m[aá]s segur[oa]|baja criminalidad|tasa de crimen|ideal para familias|"
            r"mejor pueblo|prestigios[oa]|exclusiv[oa])\b",
            re.I,
        )
        for slug in EXPECTED:
            for language in ("en", "es"):
                source, _, _ = parse(page_path(slug, language))
                with self.subTest(slug=slug, language=language):
                    self.assertNotRegex(source, risky)
                    self.assertIn("2026AvgResStat.pdf", source)
                    self.assertIn("2025AvgResStat.pdf", source)
                    self.assertIn("njar-public.stats.10kresearch.com/reports", source)
                    self.assertIn("www.nj.gov/dca/home/discrimination.shtml", source)
                    self.assertIn(REVIEWED_ON, source)
                    self.assertIn("data-publication-policy=\"official-sources-no-gated-tables\"", source)
                    if language == "en":
                        self.assertIn("does not copy member-only tables", source)
                        self.assertIn("does not rank municipalities", source)
                    else:
                        self.assertIn("no copia tablas para miembros", source)
                        self.assertIn("no clasifica municipios", source)

    def test_fair_housing_risky_phrase_sweep_is_zero(self) -> None:
        hits: list[tuple[str, str, str]] = []
        for slug in EXPECTED:
            for language in ("en", "es"):
                source, _, _ = parse(page_path(slug, language))
                text = visible_text(source)
                hits.extend(
                    (slug, language, match.group(0))
                    for match in FAIR_HOUSING_RISK.finditer(text)
                )
                if language == "en":
                    self.assertIn("Define your own property and location criteria", text)
                else:
                    self.assertIn(
                        "Defina sus propios criterios de propiedad y ubicación", text
                    )
                self.assertIn("www.nj.gov/dca/home/discrimination.shtml", source)
        self.assertEqual([], hits, f"managed-page fair-housing phrase hits: {hits}")

    def test_schema_is_grounded_to_the_page_business_and_breadcrumbs(self) -> None:
        image_asset = ROOT / "images" / "hero.jpg"
        self.assertTrue(image_asset.is_file())
        with Image.open(image_asset) as image:
            self.assertEqual((1400, 933), image.size)

        for slug in EXPECTED:
            for language in ("en", "es"):
                current = SITE + route(slug, language)
                source, _, blocks = parse(page_path(slug, language))
                nodes = [node for block in blocks for node in block.get("@graph", [block])]
                by_type = {node.get("@type"): node for node in nodes}
                with self.subTest(slug=slug, language=language):
                    self.assertTrue({"WebPage", "Article", "BreadcrumbList", "Person", "Organization"}.issubset(by_type))
                    self.assertEqual(current, by_type["WebPage"]["url"])
                    self.assertEqual(current + "#webpage", by_type["Article"]["mainEntityOfPage"]["@id"])
                    self.assertEqual(PAGE_MODIFIED_ON, by_type["WebPage"]["dateModified"])
                    self.assertEqual(PAGE_MODIFIED_ON, by_type["Article"]["dateModified"])
                    organization_id = f"{SITE}/#organization"
                    person_id = f"{SITE}/#jorge-ramirez"
                    self.assertEqual("The Jorge Ramirez Group", by_type["Organization"]["name"])
                    self.assertEqual({"@id": organization_id}, by_type["WebPage"]["publisher"])
                    self.assertEqual({"@id": organization_id}, by_type["Article"]["publisher"])
                    self.assertFalse({"author", "reviewedBy"} & set(by_type["WebPage"]))
                    self.assertEqual({"@id": organization_id}, by_type["Article"]["author"])
                    self.assertNotIn("reviewedBy", by_type["Article"])
                    self.assertEqual(
                        {
                            "@type": "ImageObject",
                            "url": f"{SITE}/images/hero.jpg",
                            "width": 1400,
                            "height": 933,
                        },
                        by_type["Article"]["image"],
                    )
                    self.assertEqual(person_id, by_type["Person"]["@id"])
                    self.assertEqual({"@id": organization_id}, by_type["Person"]["worksFor"])
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
                    self.assertNotIn('<meta name="author"', source)
                    self.assertIn(
                        '<meta name="ai-content-declaration" content="ai-assisted, source-checked">',
                        source,
                    )
                    self.assertEqual(1, source.count('data-content-provenance="v1"'))
                    visible = visible_text(source)
                    expected_provenance = (
                        "Published by The Jorge Ramirez Group. Prepared with AI assistance; "
                        "sources were checked on August 26, 2026."
                        if language == "en"
                        else "Publicado por The Jorge Ramirez Group. Elaborado con asistencia de IA; "
                        "fuentes verificadas el 26 de agosto de 2026."
                    )
                    self.assertIn(expected_provenance, visible)
                    self.assertIn("Jorge Ramirez", visible)
                    self.assertIn(by_type["Person"]["jobTitle"], visible)
                    if language == "es":
                        self.assertIn('href="/es#contact"', source)
                        self.assertNotIn('href="/es/#contact"', source)
                        self.assertNotIn('href="/contact"', source)
                    self.assertEqual("Jorge Ramirez", by_type["Person"]["name"])
                    self.assertEqual("1754604", by_type["Person"]["identifier"]["value"])
                    self.assertEqual("+19082307844", by_type["Organization"]["telephone"])
                    self.assertEqual("jorge.ramirez@kw.com", by_type["Organization"]["email"])
                    self.assertEqual("488 Springfield Ave", by_type["Organization"]["address"]["streetAddress"])
                    self.assertNotIn("Review", by_type)
                    self.assertNotIn("AggregateRating", by_type)
                    self.assertNotIn("FAQPage", by_type)

    def test_html_is_accessible_and_has_no_structural_hygiene_errors(self) -> None:
        for slug in EXPECTED:
            for language in ("en", "es"):
                source, parser, _ = parse(page_path(slug, language))
                with self.subTest(slug=slug, language=language):
                    self.assertEqual(language, parser.html_lang)
                    self.assertEqual(1, parser.main_count)
                    self.assertEqual(1, parser.h1_count)
                    self.assertEqual(1, len(parser.viewports))
                    self.assertEqual([], parser.duplicate_attributes)
                    self.assertEqual(len(parser.ids), len(set(parser.ids)))
                    self.assertEqual(["#main"], parser.skip_targets)
                    self.assertIn("main", parser.ids)
                    for image in parser.images:
                        self.assertTrue(image.get("alt", "").strip())
                        self.assertTrue(image.get("width"))
                        self.assertTrue(image.get("height"))
                    for link in parser.links:
                        if link.get("target") == "_blank":
                            self.assertIn("noopener", link.get("rel", "").split())
                        href = link.get("href", "")
                        resolved = resolve_internal(href)
                        if resolved is not None:
                            self.assertTrue(resolved.exists(), f"broken internal link: {href}")
                            fragment = urlsplit(href).fragment
                            if fragment:
                                target_source = resolved.read_text(encoding="utf-8")
                                self.assertRegex(
                                    target_source,
                                    rf'\bid=["\']{re.escape(fragment)}["\']',
                                    f"missing fragment target: {href}",
                                )
                    self.assertIn("min-height: 44px", source)
                    self.assertIn(":focus-visible", source)
                    self.assertRegex(
                        source,
                        r"\.brand\s*\{[^}]*min-height:\s*44px;[^}]*white-space:\s*nowrap;",
                    )
                    self.assertRegex(
                        source,
                        r"\.button\.primary\s*\{[^}]*linear-gradient\(135deg, #C41230, #8B0D22\) !important;",
                    )

    def test_homepage_palette_and_typography_are_preserved(self) -> None:
        for slug in EXPECTED:
            for language in ("en", "es"):
                source, _, _ = parse(page_path(slug, language))
                with self.subTest(slug=slug, language=language):
                    for color in PALETTE:
                        self.assertIn(color, source)
                    self.assertIn("'Playfair Display'", source)
                    self.assertIn("Inter", source)
                    self.assertIn("@media (max-width: 560px)", source)
                    self.assertIn("prefers-reduced-motion", source)

    def test_pages_remain_in_the_correct_sitemaps(self) -> None:
        english_sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        spanish_sitemap = (ROOT / "sitemap-es.xml").read_text(encoding="utf-8")
        for slug in EXPECTED:
            self.assertIn(SITE + route(slug, "en"), english_sitemap)
            self.assertIn(SITE + route(slug, "es"), spanish_sitemap)


class TownResearchGenerationTests(unittest.TestCase):
    def test_renderer_is_deterministic_and_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RENDERER), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("22 town market research pages are current", result.stdout)

    def test_renderer_does_not_modify_pages_during_check(self) -> None:
        paths = [page_path(slug, language) for slug in EXPECTED for language in ("en", "es")]
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        subprocess.run(
            [sys.executable, str(RENDERER), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        self.assertEqual(before, after)

    def test_containment_and_legacy_generators_cannot_overwrite_batch(self) -> None:
        containment = json.loads(
            (ROOT / "data" / "market-report-containment.json").read_text(encoding="utf-8")
        )
        expected_rebuilds = {f"market-report-{slug}-nj-2026" for slug in EXPECTED}
        self.assertTrue(expected_rebuilds.issubset(set(containment["rebuildPairs"])))
        for script in ("generate_blog.py", "generate_county_reports_and_comparisons.py"):
            source = (ROOT / script).read_text(encoding="utf-8")
            self.assertIn("quarantined_generator_main", source)
            result = subprocess.run(
                [sys.executable, script], cwd=ROOT, text=True, capture_output=True, check=False
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("quarantined", result.stderr.casefold())


if __name__ == "__main__":
    unittest.main()
