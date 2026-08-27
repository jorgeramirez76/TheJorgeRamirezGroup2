#!/usr/bin/env python3
"""Fail-closed evidence and consumer-safety contracts for valuation surfaces."""

from __future__ import annotations

import ast
import html
import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLOG_PATH = "blog/how-much-is-my-nj-home-worth-2026.html"
BLOG_INDEX_PATH = "blog/index.html"
EN_PATH = "home-valuation.html"
ES_PATH = "es/home-valuation.html"
CANONICAL = "https://thejorgeramirezgroup.com/blog/how-much-is-my-nj-home-worth-2026"
H1 = "How Much Is My NJ Home Worth? 2026 Valuation Guide"
EN_DISCLOSURE = (
    "A CMA is a broker price opinion and market estimate. It should not be considered "
    "the equivalent of an appraisal prepared by a New Jersey licensed or certified "
    "real estate appraiser."
)
ES_DISCLOSURE = (
    "Un CMA es una estimación de corretaje y no equivale a una tasación preparada por "
    "un tasador licenciado o certificado en New Jersey."
)

OFFICIAL_SOURCES = {
    "https://www.nj.gov/dobi/bulletins/blt13_05.pdf",
    "https://www.njrealtor.com/research/10k/",
    "https://njar-public.stats.10kresearch.com/docs/mmi/x/report?src=page",
    "https://fred.stlouisfed.org/series/NJSTHPI/",
    "https://www.zillow.com/zestimate/",
    "https://singlefamily.fanniemae.com/media/45516/display",
    "https://guide.freddiemac.com/app/servicing/section/5605.6",
    "https://www.nj.gov/treasury/taxation/lpt/lpt-appeal.shtml",
    "https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf",
    "https://www.njoag.gov/about/divisions-and-offices/division-on-civil-rights-home/know-the-law/njlad/discrimination-in-housing/",
}

BLOG_FORBIDDEN = (
    r"10\s*[-–]\s*20\s*%",
    r"8\s*[-–]\s*15\s*%",
    r"\b6\.8\s*%",
    r"18\s*[-–]\s*22(?:\s+days)?",
    r"\b2\s*[-–]\s*5\s*%\b",
    r"\b3\s+(?:to|[-–])\s*5\s+(?:recent\s+)?(?:sold\s+)?comps?",
    r"\b0?\.5[- ]mile",
    r"\b60\s*[-–]\s*90\s+days",
    r"\b24\s*[-–to]+\s*48\s+hours",
    r"\b2\s*[-–to]+\s*4\s+hours",
    r"\$\s*75\s*[-–]\s*150",
    r"\$\s*40\s*[-–]\s*75",
    r"\$\s*15,?000\s*[-–]\s*25,?000",
    r"\b(?:right|wrong) side\b",
    r"\bschool (?:catchment|district|premium)",
    r"\byoung[- ]family\b",
    r"\btwo[- ]income household\b",
    r"\bprice[- ]insensitive\b",
    r"\bmy (?:own )?flips?\b",
    r"\bhands[- ]on flip experience\b",
    r"\bmost agents tell you\b",
    r"\$\s*(?:712|739|747),?000",
    r"\$\s*47,?000",
    r"\bholds up in most NJ mediation contexts\b",
    r"\bthe only (?:number|way)\b",
)

SIBLING_FORBIDDEN = (
    r"\bspecific[, ]+(?:supportable|defensible) number\b",
    r"\bone specific number\b",
    r"\b24\s*(?:to|[-–])\s*48\s+hours\b",
    r"\b20\s*(?:to|[-–])\s*30\s+minutes\b",
    r"\bmisma lógica que (?:usa|aplica) un tasador\b",
    r"\bsave thousands\b",
    r"\bahorrar miles\b",
    r"\bsuccessful tax appeal\b",
    r"\bappeal your taxes successfully\b",
    r"\bpublic records only\b",
    r"\bworking from public records\b",
    r"\bse calculan con registros públicos\b",
    r"\bevery (?:active|detail|upgrade)\b",
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def schemas(source: str) -> list[dict]:
    blocks = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source,
        flags=re.I | re.S,
    )
    return [json.loads(block) for block in blocks]


class ValuationEvidenceRebuildTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.blog = read(BLOG_PATH)
        cls.blog_index = read(BLOG_INDEX_PATH)
        cls.en = read(EN_PATH)
        cls.es = read(ES_PATH)
        cls.blog_text = visible_text(cls.blog)
        cls.en_text = visible_text(cls.en)
        cls.es_text = visible_text(cls.es)

    def test_blog_keeps_clean_indexing_metadata_and_truthful_snippets(self) -> None:
        self.assertIn(f"<title>{H1}</title>", self.blog)
        self.assertIn(f'<link rel="canonical" href="{CANONICAL}">', self.blog)
        self.assertRegex(self.blog, r'<meta name="robots" content="index, follow,')
        self.assertIn('<meta property="article:modified_time" content="2026-08-27">', self.blog)
        self.assertIn('<h1>' + H1 + '</h1>', self.blog)
        self.assertIn("property-specific range", self.blog.casefold())
        for needle in ("10-20%", "5-step CMA", "real number", "15 NJ towns"):
            with self.subTest(needle=needle):
                self.assertNotIn(needle.casefold(), self.blog.casefold())

    def test_blog_index_snippets_match_the_evidence_led_rebuild(self) -> None:
        route = "/blog/how-much-is-my-nj-home-worth-2026"
        self.assertGreaterEqual(self.blog_index.count(f'href="{route}"'), 3)
        self.assertGreaterEqual(self.blog_index.count(H1), 2)
        cards = [
            block
            for block in re.findall(r"<article\b[^>]*>.*?</article>", self.blog_index, flags=re.S | re.I)
            if f'href="{route}"' in block
        ]
        self.assertEqual(1, len(cards))
        card = cards[0]
        self.assertIn(
            "Learn what a CMA, appraisal, and Zestimate can—and cannot—tell you",
            card,
        )
        self.assertIn('<time datetime="2026-08-27">Updated August 27, 2026</time>', card)
        for pattern in (
            r"5-step CMA",
            r"\$40K\+",
            r"never saw your kitchen",
            r"real agent's CMA method",
        ):
            with self.subTest(pattern=pattern):
                self.assertNotRegex(card, re.compile(pattern, re.I))

    def test_blog_schema_is_limited_to_breadcrumb_and_blogposting(self) -> None:
        nodes = schemas(self.blog)
        self.assertEqual(2, len(nodes))
        self.assertEqual({"BreadcrumbList", "BlogPosting"}, {node.get("@type") for node in nodes})
        article = next(node for node in nodes if node.get("@type") == "BlogPosting")
        self.assertEqual(H1, article["headline"])
        self.assertEqual("2026-04-24", article["datePublished"])
        self.assertEqual("2026-08-27", article["dateModified"])
        self.assertEqual(CANONICAL, article["mainEntityOfPage"]["@id"])
        self.assertEqual("https://thejorgeramirezgroup.com/#jorge-ramirez", article["author"]["@id"])
        self.assertNotRegex(self.blog, r'"@type"\s*:\s*"(?:FAQPage|HowTo)"')

    def test_blog_has_prominent_cma_non_equivalence_and_no_guarantee(self) -> None:
        self.assertIn(EN_DISCLOSURE, self.blog_text)
        self.assertRegex(self.blog_text, r"(?i)property-specific range[^.]*specific (?:property|home)[^.]*date")
        self.assertRegex(self.blog_text, r"(?i)(?:does not|doesn.t) guarantee (?:a )?sale price")

    def test_blog_uses_primary_sources_with_period_and_method_limits(self) -> None:
        for url in OFFICIAL_SOURCES:
            with self.subTest(url=url):
                self.assertIn(f'href="{url}"', self.blog)
        self.assertRegex(self.blog_text, r"July 2026[^.]*\$650,000[^.]*4\.0%")
        self.assertRegex(self.blog_text, r"year to date through July[^.]*\$610,000[^.]*3\.7%")
        self.assertRegex(self.blog_text, r"data is as of August 9, 2026")
        self.assertIn("±4% margin of error at a 95% confidence level", self.blog_text)
        self.assertIn("rolling endpoint", self.blog_text.casefold())
        self.assertIn("statewide benchmark", self.blog_text.casefold())
        self.assertIn("not an estimate for a particular address", self.blog_text.casefold())
        self.assertIn("Sources checked August 27, 2026", self.blog_text)

    def test_blog_describes_zillow_and_market_analysis_without_false_precision(self) -> None:
        text = self.blog_text.casefold()
        for phrase in (
            "public records",
            "multiple listing service",
            "user-submitted",
            "listing data",
            "market trends",
            "multiple times per week",
            "market-supported adjustments",
            "active and pending listings",
            "reasoned range",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertRegex(text, r"zestimate[^.]*not an appraisal")

    def test_blog_routes_decision_specific_uses_to_the_right_professional(self) -> None:
        text = self.blog_text.casefold()
        for phrase in (
            "licensed or certified appraiser",
            "property-tax appeal",
            "court or administrative body",
            "insurance professional",
            "replacement cost",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertIn("does not guarantee an appeal result", text)

    def test_blog_has_none_of_the_disproved_or_unverifiable_claims(self) -> None:
        for pattern in BLOG_FORBIDDEN:
            with self.subTest(pattern=pattern):
                self.assertNotRegex(self.blog_text, re.compile(pattern, re.I))
                self.assertNotRegex(html.unescape(self.blog), re.compile(pattern, re.I))

    def test_service_pages_use_accurate_cma_zillow_and_special_purpose_guidance(self) -> None:
        self.assertIn(EN_DISCLOSURE, self.en_text)
        self.assertIn(ES_DISCLOSURE, self.es_text)
        for source, language in ((self.en, "en"), (self.es, "es")):
            with self.subTest(language=language):
                self.assertIn('href="https://www.zillow.com/zestimate/"', source)
                self.assertIn('href="https://www.nj.gov/dobi/bulletins/blt13_05.pdf"', source)
                self.assertIn('href="https://www.nj.gov/treasury/taxation/lpt/lpt-appeal.shtml"', source)
        self.assertRegex(self.en_text, r"(?i)scope and timing depend on")
        self.assertRegex(self.es_text, r"(?i)el alcance y el plazo dependen de")
        self.assertRegex(self.en_text, r"(?i)does not guarantee (?:a |the )?(?:sale price|tax-appeal result)")
        self.assertRegex(self.es_text, r"(?i)no garantiza (?:un |el )?(?:precio de venta|resultado de una apelación)")

    def test_service_pages_drop_overpromises_and_false_automated_value_claims(self) -> None:
        for relative, text, source in (
            (EN_PATH, self.en_text, self.en),
            (ES_PATH, self.es_text, self.es),
        ):
            for pattern in SIBLING_FORBIDDEN:
                with self.subTest(relative=relative, pattern=pattern):
                    self.assertNotRegex(text, re.compile(pattern, re.I))
                    self.assertNotRegex(html.unescape(source), re.compile(pattern, re.I))

    def test_service_page_schema_and_sitemap_dates_match_the_review(self) -> None:
        for relative, source in ((EN_PATH, self.en), (ES_PATH, self.es)):
            with self.subTest(relative=relative):
                nodes = schemas(source)
                self.assertEqual({"BreadcrumbList", "WebPage"}, {node.get("@type") for node in nodes})
                webpage = next(node for node in nodes if node.get("@type") == "WebPage")
                self.assertEqual("2026-08-27", webpage["dateModified"])
                self.assertNotRegex(source, r'"@type"\s*:\s*"FAQPage"')

        expected = {
            "https://thejorgeramirezgroup.com/es": "2026-08-27",
            "https://thejorgeramirezgroup.com/blog": "2026-08-27",
            "https://thejorgeramirezgroup.com/blog/how-much-is-my-nj-home-worth-2026": "2026-08-27",
            "https://thejorgeramirezgroup.com/home-valuation": "2026-08-27",
            "https://thejorgeramirezgroup.com/es/home-valuation": "2026-08-27",
        }
        actual: dict[str, str] = {}
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for filename in ("sitemap.xml", "sitemap-es.xml"):
            root = ET.fromstring(read(filename))
            for item in root.findall("sm:url", namespace):
                location = item.findtext("sm:loc", default="", namespaces=namespace)
                if location in expected:
                    actual[location] = item.findtext("sm:lastmod", default="", namespaces=namespace)
        self.assertEqual(expected, actual)

    def test_bilingual_intake_is_real_localized_and_has_no_hidden_sla(self) -> None:
        for source, route, intent in (
            (self.en, "/home-valuation", "Home valuation request"),
            (self.es, "/es/home-valuation", "Solicitud de valoración de casa"),
        ):
            with self.subTest(route=route):
                self.assertRegex(source, r'<form\b[^>]*id="valuationForm"[^>]*action="/api/lead"')
                self.assertIn('name="leadType" value="home-valuation"', source)
                self.assertIn(f'name="intent" value="{intent}"', source)
                self.assertIn(f'name="_source" value="{route}"', source)
                self.assertIn(f'name="_next" value="{route}"', source)
                self.assertIn('type="module" src="/js/home-valuation.js"', source)
        client = read("js/home-valuation.js")
        self.assertNotRegex(client, re.compile(r"24\s*(?:to|[-–])\s*48\s+hours", re.I))
        self.assertIn('trim(values._source) || "/home-valuation"', client)
        self.assertIn('trim(values.intent) || "Home valuation request"', client)

    def test_conversion_normalizer_is_idempotent_and_cannot_emit_a_fixed_sla(self) -> None:
        result = subprocess.run(
            ["python3", "scripts/fix_conversion_ux.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("would update 0 HTML files", result.stdout)
        normalizer = read("scripts/fix_conversion_ux.py")
        assignment = next(
            node
            for node in ast.parse(normalizer).body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "VALUATION_PROMISE_REPLACEMENTS"
                for target in node.targets
            )
        )
        replacements = ast.literal_eval(assignment.value)
        for _old, replacement in replacements:
            self.assertNotRegex(replacement, re.compile(r"24\s*(?:to|[-–])\s*48\s+hours", re.I))
            self.assertNotRegex(replacement, re.compile(r"precise value range", re.I))
            self.assertNotRegex(replacement, re.compile(r"rango de valor preciso", re.I))

    def test_the_15_scaled_town_valuation_pages_remain_retired(self) -> None:
        manifest = json.loads(read("data/programmatic-doorway-retirement.json"))
        valuation_pages = [page for page in manifest["pages"] if page["family"] == "home_valuation"]
        self.assertEqual(15, len(valuation_pages))
        for page in valuation_pages:
            with self.subTest(path=page["file"]):
                source = read(page["file"])
                self.assertIn('<meta name="robots" content="noindex, follow">', source)
                self.assertIn('content="0; url=/home-valuation"', source)


if __name__ == "__main__":
    unittest.main()
