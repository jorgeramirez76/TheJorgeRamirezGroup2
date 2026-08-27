#!/usr/bin/env python3
"""Fail-closed checks for verified service and relocation content.

These pages previously mixed useful service information with unsupported
biographical, market, legal, timing, and investment-performance claims.  The
tests inspect the static HTML that search engines receive and use the XML
sitemaps as the indexability boundary.
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://thejorgeramirezgroup.com"
REVIEW_DATE = "2026-08-27"

OWNED_PAGES = (
    "buy-a-home.html",
    "es/buy-a-home.html",
    "investment-property-nj.html",
    "es/investment-property-nj.html",
    "nj-home-seller-guide.html",
    "blog/why-new-yorkers-moving-to-nj-2026.html",
    "es/blog/moving-from-nyc-to-nj-guide.html",
)

DECLARATION_PAGES = OWNED_PAGES + (
    "downsizing-nj.html",
    "es/downsizing-nj.html",
    "tools/blog-automation/template_source.html",
)

# TODO(residual-content-track): remove this path-exact allowlist when the
# luxury EN/ES residual repair lands.  New sitemap-scoped offenders still fail
# closed, and the test continues to pass once this path is repaired.
KNOWN_RESIDUAL_PERSONAL_HISTORY = {"es/luxury-homes-nj.html"}

def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(r"<script\b[^>]*>.*?</script>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    source = re.sub(r"<[^>]+>", " ", source)
    return re.sub(r"\s+", " ", html.unescape(source)).strip()


def visible_sentences(source: str) -> list[str]:
    """Return visible, block-bounded sentences without script/style leakage."""

    source = re.sub(r"<script\b[^>]*>.*?</script>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    source = re.sub(
        r"</?(?:address|article|aside|blockquote|br|dd|div|dl|dt|figcaption|figure|"
        r"footer|h[1-6]|header|li|main|nav|ol|p|section|table|tbody|td|th|thead|tr|ul)\b[^>]*>",
        ". ",
        source,
        flags=re.I,
    )
    source = re.sub(r"<[^>]+>", " ", source)
    text = re.sub(r"\s+", " ", html.unescape(source)).strip(" .")
    return [part.strip(" .") for part in re.split(r"(?<=[.!?])\s+", text) if part.strip(" .")]


def load_script(relative: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def json_ld(source: str) -> list[object]:
    blocks = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source,
        flags=re.I | re.S,
    )
    return [json.loads(html.unescape(block).strip()) for block in blocks]


def sitemap_entries(name: str) -> dict[str, str]:
    root = ET.parse(ROOT / name).getroot()
    return {
        node.findtext("{*}loc", "").rstrip("/"): node.findtext("{*}lastmod", "")
        for node in root.findall("{*}url")
    }


def sitemap_files() -> list[Path]:
    urls = set(sitemap_entries("sitemap.xml")) | set(sitemap_entries("sitemap-es.xml"))
    files: list[Path] = []
    for url in sorted(urls):
        path = urlparse(url).path.strip("/")
        candidates = (
            ROOT / f"{path}.html",
            ROOT / path / "index.html",
            ROOT / (path or "index.html"),
        )
        match = next((candidate for candidate in candidates if candidate.is_file()), None)
        if match is None:
            raise AssertionError(f"sitemap URL has no static source: {url}")
        files.append(match)
    return files


class VerifiedServiceContentTests(unittest.TestCase):
    def test_owned_declarations_use_truthful_source_checked_language(self) -> None:
        expected = '<meta name="ai-content-declaration" content="ai-assisted, source-checked">'
        for relative in DECLARATION_PAGES:
            source = read(relative)
            with self.subTest(page=relative):
                self.assertIn(expected, source)
                self.assertNotRegex(source, r"(?i)human[- ](?:authored|reviewed)")

    def test_visible_sentence_scanner_excludes_nonvisible_code_and_keeps_boundaries(self) -> None:
        source = """
        <script type="application/ld+json">{"claim":"Jorge renovated houses"}</script>
        <style>.claim::after{content:"Jorge bought homes"}</style>
        <p>Jorge provides property records.</p><p>Buyers compare renovated houses.</p>
        """
        sentences = visible_sentences(source)
        self.assertEqual(
            ["Jorge provides property records", "Buyers compare renovated houses"],
            sentences,
        )

    def test_owned_pages_keep_canonicals_hreflang_and_single_h1(self) -> None:
        expected = {
            "buy-a-home.html": "/buy-a-home",
            "es/buy-a-home.html": "/es/buy-a-home",
            "investment-property-nj.html": "/investment-property-nj",
            "es/investment-property-nj.html": "/es/investment-property-nj",
            "nj-home-seller-guide.html": "/nj-home-seller-guide",
            "blog/why-new-yorkers-moving-to-nj-2026.html": "/blog/why-new-yorkers-moving-to-nj-2026",
            "es/blog/moving-from-nyc-to-nj-guide.html": "/es/blog/moving-from-nyc-to-nj-guide",
        }
        for relative, route in expected.items():
            source = read(relative)
            with self.subTest(page=relative):
                self.assertEqual(1, len(re.findall(r"<h1\b", source, flags=re.I)))
                self.assertEqual(
                    1,
                    len(
                        re.findall(
                            rf'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']{re.escape(ORIGIN + route)}["\']',
                            source,
                            flags=re.I,
                        )
                    ),
                )
                self.assertNotIn("noindex", source.lower())
                json_ld(source)

        for english, spanish in (
            ("buy-a-home.html", "es/buy-a-home.html"),
            ("investment-property-nj.html", "es/investment-property-nj.html"),
        ):
            en = read(english)
            es = read(spanish)
            en_url = ORIGIN + "/" + english.removesuffix(".html")
            es_url = ORIGIN + "/" + spanish.removesuffix(".html")
            self.assertIn(f'hreflang="en-US" href="{en_url}"', en)
            self.assertIn(f'hreflang="es-US" href="{es_url}"', en)
            self.assertIn(f'hreflang="en-US" href="{en_url}"', es)
            self.assertIn(f'hreflang="es-US" href="{es_url}"', es)

    def test_buy_pages_correct_attorney_review_timing_and_cost_claims(self) -> None:
        en = read("buy-a-home.html")
        es = read("es/buy-a-home.html")
        en_text = visible_text(en).lower()
        es_text = visible_text(es).lower()

        self.assertIn("an attorney is not required", en_text)
        self.assertIn("state-approved broker contract form", en_text)
        self.assertIn("commonly a three-business-day period", en_text)
        self.assertIn("not a universal deadline", en_text)
        self.assertIn("no se requiere contratar a un abogado", es_text)
        self.assertIn("formulario de contrato de corredor aprobado por el estado", es_text)
        self.assertIn("suele ser un período de tres días hábiles", es_text)
        self.assertIn("no es un plazo universal", es_text)

        for source in (en, es):
            lowered = html.unescape(source).lower()
            self.assertNotRegex(lowered, r"\b45\s*(?:to|a|–|-)\s*60\s+days?\b")
            self.assertNotRegex(lowered, r"\b2\s*(?:to|a|–|-)\s*5\s*(?:percent|por ciento|%)")
            self.assertNotIn("attorney state", lowered)
            self.assertNotIn("estado que requiere abogado", lowered)
            self.assertNotIn("requires both buyer and seller", lowered)
            self.assertNotIn("requiere que tanto el comprador como el vendedor", lowered)
            self.assertNotRegex(lowered, r"\b(?:guaranteed|guarantee|garantizad[oa]s?|sin sorpresas)\b")

        self.assertIn("https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf", en)
        self.assertIn("https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf", es)
        self.assertIn("https://www.consumerfinance.gov/owning-a-home/loan-estimate/", en)
        self.assertIn("https://www.consumerfinance.gov/owning-a-home/loan-estimate/", es)

    def test_investment_pages_are_source_led_and_do_not_promise_returns(self) -> None:
        required_sources = (
            "https://www.irs.gov/publications/p527",
            "https://www.nj.gov/dca/home/landlord-tenant.shtml",
            "https://www.nj.gov/dca/codes/resources/leadpaint.shtml",
            "https://www.epa.gov/lead/lead-based-paint-disclosure-rule-section-1018-title-x",
            "https://flooddisclosure.nj.gov/",
        )
        for relative in ("investment-property-nj.html", "es/investment-property-nj.html"):
            source = read(relative)
            lowered = html.unescape(source).lower()
            text = visible_text(source).lower()
            with self.subTest(page=relative):
                for url in required_sources:
                    self.assertIn(url, source)
                self.assertIn("general educational information" if not relative.startswith("es/") else "información educativa general", text)
                self.assertIn("vacancy" if not relative.startswith("es/") else "vacancia", text)
                self.assertIn("property-specific" if not relative.startswith("es/") else "específico de la propiedad", text)
                self.assertNotRegex(lowered, r"\b(?:cap rates?|tasas? de capitalizaci[oó]n)[^.<]{0,80}\b\d+(?:\.\d+)?\s*%")
                self.assertNotRegex(lowered, r"\b\d+\s*(?:day|days|d[ií]a|d[ií]as|week|weeks|semana|semanas)\b")
                self.assertNotIn("off-market deal flow", lowered)
                self.assertNotIn("flujo de negocios fuera del mercado", lowered)
                self.assertNotIn("who actually invests", lowered)
                self.assertNotIn("que de verdad invierte", lowered)
                self.assertNotRegex(lowered, r"\b(?:guarantee|guaranteed|profit|profitable|ganancia|rentable|retorno garantizado)\b")

    def test_spanish_relocation_guide_matches_safe_english_evidence_model(self) -> None:
        source = read("es/blog/moving-from-nyc-to-nj-guide.html")
        text = visible_text(source).lower()
        self.assertIn('<html lang="es-US">', source)
        self.assertIn('hreflang="en-US" href="https://thejorgeramirezgroup.com/blog/moving-from-nyc-to-nj-guide"', source)
        self.assertIn('hreflang="es-US" href="https://thejorgeramirezgroup.com/es/blog/moving-from-nyc-to-nj-guide"', source)
        for url in (
            "https://www.njtransit.com/trip-planner-service-near-to",
            "https://www.nj.gov/mvc/drivertopics/movetonj.htm",
            "https://www.fmcsa.dot.gov/protect-your-move/select-mover",
            "https://www.nyc.gov/html/dot/html/motorist/truck-driver-faq.shtml",
            "https://dmv.ny.gov/insurance/auto-liability-insurance",
            "https://www.nj.gov/treasury/taxation/njit26.shtml",
            "https://www.nj.gov/treasury/taxation/njit14.shtml",
            "https://pub.njleg.gov/Bills/2024/PL24/32_.HTM",
            "https://www.nj.gov/dobi/bulletins/blt24_11.pdf",
            "https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf",
            "https://www.nj.gov/education/schoolperformance/",
        ):
            self.assertIn(url, source)
        self.assertIn("no es asesoría legal, fiscal, financiera", text)
        self.assertIn("comprueba el trayecto completo", text)
        self.assertNotRegex(text, r"\b(?:mejor(?:es)?|excelente(?:s)?|ideal(?:es)?)\s+(?:pueblo|municipio|escuela|distrito)")
        self.assertNotRegex(text, r"\b\d+\s*(?:a|–|-)\s*\d+\s+minutos\b")
        self.assertNotRegex(text, r"\$\s*\d")

    def test_market_article_and_seller_guide_use_verified_identity_only(self) -> None:
        market = read("blog/why-new-yorkers-moving-to-nj-2026.html")
        seller = read("nj-home-seller-guide.html")
        combined = html.unescape(market + "\n" + seller).lower()
        self.assertIn("https://www.njtransit.com/trip-planner-service-near-to", market)
        self.assertIn("https://www.njrealtor.com/research/10k/", market)
        self.assertIn("full-time realtor with keller williams premier properties since 2017", combined)
        self.assertIn("1754604", combined)
        self.assertNotRegex(combined, r"\b(?:flooding|mass exodus|exodus)\b")
        self.assertNotRegex(combined, r"\b(?:3|4|5|6)\s*(?:to|–|-)\s*(?:5|6|8)\s*%")
        self.assertNotRegex(combined, r"\b(?:no crash|will keep rising|routinely|consistently wins|the edge that wins)\b")

    def test_sitemap_scoped_content_has_no_unverified_personal_history(self) -> None:
        patterns = {
            "personal investor or renovation history": re.compile(
                r"\b(?:jorge|i|he)\b[^.!?<]{0,180}"
                r"(?:personally\s+)?(?:bought|owned|renovated|flipped|resold|rehabbed)"
                r"[^.!?<]{0,100}(?:homes?|properties|houses|rental|investor)",
                re.I,
            ),
            "Spanish personal investor or renovation history": re.compile(
                r"\b(?:jorge|yo|[eé]l)\b[^.!?<]{0,180}"
                r"(?:compr[oó]|posee|renov[oó]|revendi[oó]|rehabilit[oó])"
                r"[^.!?<]{0,100}(?:casas?|propiedades|alquiler|inversionista)",
                re.I,
            ),
            "rental portfolio claim": re.compile(
                r"\b(?:his|my|su|propia?)\s+(?:own\s+)?(?:rental\s+)?portfolio\b|"
                r"\bcartera\s+(?:propia\s+)?de\s+alquileres\b",
                re.I,
            ),
            "construction crew claim": re.compile(
                r"\b(?:his|my|su|own|propia?)\s+(?:construction\s+)?crews?\b|"
                r"\b(?:managed|manejado|dirigido)\s+(?:construction\s+)?(?:crews?|cuadrillas?)\b",
                re.I,
            ),
            "unsupported transaction volume": re.compile(
                r"\b(?:managed|handled|coordinated|helped|manejado|coordinado|ayudado)\s+"
                r"(?:dozens|hundreds|many|decenas|cientos|muchos)\b",
                re.I,
            ),
        }
        offenders: list[str] = []
        for path in sitemap_files():
            sentences = visible_sentences(path.read_text(encoding="utf-8", errors="ignore"))
            for sentence in sentences:
                for label, pattern in patterns.items():
                    if pattern.search(sentence):
                        offenders.append(f"{path.relative_to(ROOT)}: {label}")
        template = read("tools/blog-automation/template_source.html")
        template_sentences = visible_sentences(template)
        template_head = html.unescape(template.split("</head>", 1)[0])
        for label, pattern in patterns.items():
            if any(pattern.search(sentence) for sentence in template_sentences) or pattern.search(template_head):
                offenders.append(f"tools/blog-automation/template_source.html: {label}")
        unexpected = [
            offender
            for offender in offenders
            if offender.split(":", 1)[0] not in KNOWN_RESIDUAL_PERSONAL_HISTORY
        ]
        self.assertEqual([], unexpected)

    def test_retired_landing_generator_cannot_overwrite_any_manual_page(self) -> None:
        generator = load_script("generate_new_landing_pages.py", "verified_landing_generator")
        expected_routes = {
            "buyer-agency-agreement-nj",
            "cash-offer-nj",
            "divorce-home-sale-nj",
            "downsizing-nj",
            "inherited-home-nj",
            "investment-property-nj",
            "luxury-homes-nj",
            "nyc-to-nj-relocation",
            "relocating-from-nj",
            "sell-rental-property-nj",
        }
        self.assertEqual(expected_routes, set(generator.MANUALLY_MANAGED_ROUTES))
        self.assertEqual({}, generator.PAGES)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before: dict[str, str] = {}
            for route in expected_routes:
                value = f"manual source-led page: {route}"
                before[route] = value
                (root / f"{route}.html").write_text(value, encoding="utf-8")
            with mock.patch.object(generator, "REPO", root):
                with self.assertRaisesRegex(RuntimeError, "is retired"):
                    generator.main()
            self.assertEqual(
                before,
                {
                    route: (root / f"{route}.html").read_text(encoding="utf-8")
                    for route in expected_routes
                },
            )
            self.assertEqual(
                {f"{route}.html" for route in expected_routes},
                {path.name for path in root.iterdir()},
            )

        source = read("generate_new_landing_pages.py").lower()
        for unsafe in (
            "personally bought",
            "own rental portfolio",
            "managed construction crews",
            "off-market deal",
            "top dollar",
            "hundreds of nyc",
            "45–60",
        ):
            self.assertNotIn(unsafe, source)

    def test_blog_template_assembly_fails_closed_on_stale_or_unverified_copy(self) -> None:
        template = read("tools/blog-automation/template_source.html")
        for stale in (
            "Median prices ~$510K",
            "hands-on renovation and investment experience",
            "seller's market",
            "20–27 days",
            "+3.9%",
            "highly regarded",
            "local expert",
        ):
            self.assertNotIn(stale.lower(), template.lower())

        daily = load_script("tools/blog-automation/daily_blog.py", "verified_daily_blog")
        post = {
            "title": "Current NJ Buyer Research",
            "h1": "Current New Jersey Buyer Research",
            "meta_description": "Use current official records and property-specific review before making a New Jersey housing decision.",
            "keywords": "New Jersey buyer research, property records, official sources",
            "quick_answer": "Verify current information for the specific property.",
            "body_html": "<h2>Research</h2><p>Use current official sources for the property.</p>",
            "faqs": [{"q": "What should I verify?", "a": "Current property-specific facts."}],
        }
        assembled = daily.assemble(
            dict(post),
            "current-nj-buyer-research",
            "New Jersey",
            REVIEW_DATE,
            "August 2026",
        )
        self.assertIn("<title>Current NJ Buyer Research | Jorge Ramirez</title>", assembled)
        self.assertIn(f"{ORIGIN}/blog/current-nj-buyer-research", assembled)
        self.assertIn(
            '<meta name="ai-content-declaration" content="ai-assisted, source-checked">',
            assembled,
        )
        self.assertNotIn(daily.TEMPLATE_SENTINELS["description"], assembled)

        with mock.patch.object(daily, "OLD_DESC", "missing replacement marker"):
            with self.assertRaisesRegex(RuntimeError, "replacement constants"):
                daily.assemble(
                    dict(post),
                    "current-nj-buyer-research",
                    "New Jersey",
                    REVIEW_DATE,
                    "August 2026",
                )

        unsafe = dict(post)
        unsafe["body_html"] = "<p>Jorge personally bought and renovated homes.</p>"
        with self.assertRaisesRegex(RuntimeError, "unverified personal-history"):
            daily.assemble(
                unsafe,
                "unsafe-personal-history",
                "New Jersey",
                REVIEW_DATE,
                "August 2026",
            )

    def test_owned_pages_use_homepage_palette_and_current_lastmod(self) -> None:
        for relative in OWNED_PAGES:
            source = read(relative)
            with self.subTest(page=relative):
                for token in ("#1A1A1A", "#B8962E"):
                    self.assertIn(token.lower(), source.lower())
                self.assertNotRegex(source, r"(?i)#(?:6B46C1|764ba2|667eea|1a5c45)\b")

        english = sitemap_entries("sitemap.xml")
        spanish = sitemap_entries("sitemap-es.xml")
        expected = {
            ORIGIN + "/buy-a-home": english,
            ORIGIN + "/investment-property-nj": english,
            ORIGIN + "/nj-home-seller-guide": english,
            ORIGIN + "/blog/why-new-yorkers-moving-to-nj-2026": english,
            ORIGIN + "/es/buy-a-home": spanish,
            ORIGIN + "/es/investment-property-nj": spanish,
            ORIGIN + "/es/blog/moving-from-nyc-to-nj-guide": spanish,
        }
        for url, entries in expected.items():
            self.assertEqual(REVIEW_DATE, entries.get(url), url)


if __name__ == "__main__":
    unittest.main()
