#!/usr/bin/env python3
"""Regression coverage for the bilingual legacy NJ buyer-guide rebuild."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "nj-home-buyer-guide-sources.json"
RENDERER = ROOT / "tools" / "render_nj_home_buyer_guides.py"
STYLESHEET = ROOT / "css" / "nj-home-buyer-guide.css"
PDF = ROOT / "guides" / "nj-home-buyer-guide.pdf"
PDF_RENDERER = ROOT / "tools" / "render_nj_home_buyer_guide_pdf.py"

PAGES = {
    "nj-home-buyer-guide.html": {
        "lang": "en-US",
        "canonical": "https://thejorgeramirezgroup.com/nj-home-buyer-guide",
        "alternate": "https://thejorgeramirezgroup.com/es/nj-home-buyer-guide",
        "home": "/",
        "programs": "/first-time-buyer-nj-programs",
        "mortgage": "/tools/mortgage-calculator",
        "closing": "/closing-costs-calculator",
        "contact": "/#contact",
        "correct_attorney_copy": "New Jersey does not require a home buyer to hire an attorney.",
        "program_copy": "Confirm current eligibility directly with NJHMFA",
        "form_source": "nj-home-buyer-guide",
    },
    "es/nj-home-buyer-guide.html": {
        "lang": "es-US",
        "canonical": "https://thejorgeramirezgroup.com/es/nj-home-buyer-guide",
        "alternate": "https://thejorgeramirezgroup.com/nj-home-buyer-guide",
        "home": "/es",
        "programs": "/es/first-time-buyer-nj-programs",
        "mortgage": "/es/tools/mortgage-calculator",
        "closing": "/es/closing-costs-calculator",
        "contact": "/es/#contact",
        "correct_attorney_copy": "Nueva Jersey no exige que el comprador contrate a un abogado.",
        "program_copy": "Confirma la elegibilidad vigente directamente con NJHMFA",
        "form_source": "es-nj-home-buyer-guide",
    },
}

OFFICIAL_HOSTS = {
    "nj.gov",
    "www.nj.gov",
    "www.consumerfinance.gov",
    "www.hud.gov",
}

EXPECTED_SECTIONS = {
    "overview",
    "roadmap",
    "budget",
    "loan-estimate",
    "programs",
    "representation",
    "property-search",
    "offer",
    "inspection",
    "closing",
    "free-guide",
    "resources",
    "sources",
    "faq",
}

BANNED_LEGACY_STYLE = (
    "#3498db",
    "#2c3e50",
    "#f0f4ff",
    "#2980b9",
    "#1e90ff",
    "rgb(52, 152, 219)",
)

BANNED_CLAIMS = re.compile(
    r"(?:"
    r"\$\s*\d|"
    r"\b\d+(?:\.\d+)?\s*%|"
    r"\b(?:three|3)\s*(?:-|\s)?(?:to|–)\s*(?:twenty|20)\s*percent\b|"
    r"\b(?:two|2)\s*(?:-|\s)?(?:to|–)\s*(?:four|4)\s*percent\b|"
    r"\b(?:hundreds|dozens)\s+of\s+(?:buyers|clients)\b|"
    r"\b(?:cientos|decenas)\s+de\s+(?:compradores|clientes)\b|"
    r"\b(?:NJ|New Jersey)\s+(?:requires?|mandates?)\s+(?:a\s+)?(?:real estate\s+)?attorney\b|"
    r"\b(?:NJ|Nueva Jersey)\s+exige\s+(?:un|a los compradores un)\s+abogado\b|"
    r"\b(?:schools?|school districts?)\b|"
    r"\b(?:escuelas?|distritos? escolares?)\b|"
    r"\b(?:safe(?:st)?|low[- ]crime|family[- ]friendly|best town|desirable communit)\w*\b|"
    r"\b(?:m[aá]s segur[oa]s?|baja criminalidad|ideal para familias|mejor pueblo)\w*\b|"
    r"\b(?:competitive market|hot market|homes? (?:sell|receive offers) within days)\b|"
    r"\b(?:mercado competitivo|mercado caliente|se venden en d[ií]as)\b"
    r")",
    re.IGNORECASE,
)


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
        values = {key: value or "" for key, value in attrs}
        self.tags.append((tag, attrs, values))
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json = True
            self._json_parts = []
        elif tag in {"script", "style", "template", "noscript"}:
            self._hidden_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, attrs, {key: value or "" for key, value in attrs}))

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json:
            self.json_scripts.append("".join(self._json_parts).strip())
            self._json = False
            self._json_parts = []
        elif tag in {"script", "style", "template", "noscript"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._json:
            self._json_parts.append(data)
        elif not self._hidden_depth:
            value = " ".join(data.split())
            if value:
                self.visible_parts.append(value)

    def attrs(self, tag: str) -> list[dict[str, str]]:
        return [values for current, _, values in self.tags if current == tag]

    @property
    def visible_text(self) -> str:
        return " ".join(self.visible_parts)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def parsed(relative: str) -> PageParser:
    parser = PageParser()
    parser.feed(read(relative))
    return parser


def schema_nodes(value: object) -> list[dict[str, object]]:
    nodes: list[dict[str, object]] = []
    if isinstance(value, dict):
        if "@type" in value:
            nodes.append(value)
        for child in value.values():
            nodes.extend(schema_nodes(child))
    elif isinstance(value, list):
        for child in value:
            nodes.extend(schema_nodes(child))
    return nodes


def schema_type(node: dict[str, object]) -> set[str]:
    current = node.get("@type")
    if isinstance(current, str):
        return {current}
    if isinstance(current, list):
        return {item for item in current if isinstance(item, str)}
    return set()


def local_target(href: str) -> Path | None:
    split = urlsplit(href)
    if split.scheme or split.netloc or not split.path.startswith("/"):
        return None
    path = unquote(split.path)
    if path in {"", "/"}:
        return ROOT / "index.html"
    candidate = ROOT / path.lstrip("/")
    if candidate.suffix:
        return candidate
    if candidate.is_dir() and (candidate / "index.html").exists():
        return candidate / "index.html"
    return candidate.with_suffix(".html")


class NJHomeBuyerGuideRebuildTests(unittest.TestCase):
    def test_source_manifest_is_current_primary_and_visible(self) -> None:
        self.assertTrue(MANIFEST.exists(), "dedicated source manifest is missing")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("2026-08-26", manifest["reviewed"])
        self.assertEqual(set(PAGES), set(manifest["pages"]))
        self.assertGreaterEqual(len(manifest["sources"]), 10)
        source_ids = {record["id"] for record in manifest["sources"]}
        self.assertEqual(len(source_ids), len(manifest["sources"]))
        for record in manifest["sources"]:
            self.assertEqual(
                {"id", "url", "publisher", "fact_supported", "accessed", "http_status"},
                set(record),
            )
            self.assertIn((urlsplit(record["url"]).hostname or "").lower(), OFFICIAL_HOSTS)
            self.assertEqual("2026-08-26", record["accessed"])
            self.assertEqual(200, record["http_status"])
            self.assertTrue(record["publisher"].strip())
            self.assertTrue(record["fact_supported"].strip())
        for relative, page_record in manifest["pages"].items():
            with self.subTest(relative=relative):
                self.assertEqual(source_ids, set(page_record["source_ids"]))
                hrefs = {item.get("href", "") for item in parsed(relative).attrs("a")}
                for source in manifest["sources"]:
                    self.assertIn(source["url"], hrefs)

    def test_brand_system_matches_homepage_and_removes_legacy_blue(self) -> None:
        self.assertTrue(STYLESHEET.exists(), "dedicated buyer-guide stylesheet is missing")
        css = STYLESHEET.read_text(encoding="utf-8")
        compact = re.sub(r"\s+", "", css).lower()
        for color in (
            "#0A0A0A",
            "#1A1A1A",
            "#C41230",
            "#8B0D22",
            "#B8962E",
            "#D4AF5A",
            "#FAFAF8",
            "#F8F6F2",
        ):
            self.assertIn(color.lower(), css.lower())
        self.assertIn("'Playfair Display'", css)
        self.assertIn("'Inter'", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertRegex(css, r"@media\s*\(max-width:\s*480px\)")
        self.assertIn("min-height:44px", compact)
        for banned in BANNED_LEGACY_STYLE:
            self.assertNotIn(banned, css.lower())
        for relative in PAGES:
            with self.subTest(relative=relative):
                raw = read(relative)
                self.assertIn('href="/css/styles.css', raw)
                self.assertIn('href="/css/nj-home-buyer-guide.css', raw)
                self.assertLess(
                    raw.index('href="/css/styles.css'),
                    raw.index('href="/css/nj-home-buyer-guide.css'),
                    "page-specific CSS must load after the shared homepage stylesheet",
                )
                self.assertNotIn("<style", raw.lower())
                for banned in BANNED_LEGACY_STYLE:
                    self.assertNotIn(banned, raw.lower())

    def test_metadata_canonical_and_reciprocal_hreflang(self) -> None:
        expected_alternates = {
            ("en-US", "https://thejorgeramirezgroup.com/nj-home-buyer-guide"),
            ("es-US", "https://thejorgeramirezgroup.com/es/nj-home-buyer-guide"),
            ("x-default", "https://thejorgeramirezgroup.com/nj-home-buyer-guide"),
        }
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                page = parsed(relative)
                raw = read(relative)
                self.assertEqual(expected["lang"], page.attrs("html")[0].get("lang"))
                self.assertEqual(1, len(page.attrs("title")))
                title = re.search(r"<title>(.*?)</title>", raw, re.I | re.S).group(1).strip()
                self.assertGreaterEqual(len(title), 40)
                self.assertLessEqual(len(title), 65)
                descriptions = [
                    item.get("content", "")
                    for item in page.attrs("meta")
                    if item.get("name") == "description"
                ]
                self.assertEqual(1, len(descriptions))
                self.assertGreaterEqual(len(descriptions[0]), 120)
                self.assertLessEqual(len(descriptions[0]), 165)
                llm_context = [
                    item.get("content", "")
                    for item in page.attrs("meta")
                    if item.get("name") == "llm-context"
                ]
                self.assertEqual(1, len(llm_context))
                self.assertIn("2026-08-26", llm_context[0])
                self.assertIn("NJHMFA", llm_context[0])
                self.assertIn("Loan Estimate", llm_context[0])
                self.assertEqual(
                    [expected["canonical"]],
                    [
                        item.get("href", "")
                        for item in page.attrs("link")
                        if item.get("rel") == "canonical"
                    ],
                )
                alternates = {
                    (item.get("hreflang"), item.get("href"))
                    for item in page.attrs("link")
                    if item.get("rel") == "alternate"
                }
                self.assertEqual(expected_alternates, alternates)
                robots = [
                    item.get("content", "")
                    for item in page.attrs("meta")
                    if item.get("name") == "robots"
                ]
                self.assertEqual(1, len(robots))
                self.assertIn("index", robots[0])
                self.assertNotIn("noindex", robots[0])
                self.assertNotIn("2025", raw)

    def test_visible_copy_is_document_first_current_and_non_steering(self) -> None:
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                page = parsed(relative)
                claims = " ".join([page.visible_text, *page.json_scripts])
                match = BANNED_CLAIMS.search(claims)
                self.assertIsNone(match, match.group(0) if match else "")
                self.assertIn(expected["correct_attorney_copy"], claims)
                self.assertIn(expected["program_copy"], claims)
                self.assertIn("2026-08-26", claims)
                self.assertIn("Loan Estimate", claims)
                self.assertIn("Closing Disclosure", claims)
                self.assertNotRegex(claims, r"(?i)expert (?:advice|guidance)|asesor[ií]a experta")

    def test_structure_accessibility_and_controls(self) -> None:
        for relative in PAGES:
            with self.subTest(relative=relative):
                page = parsed(relative)
                self.assertEqual(1, len(page.attrs("main")))
                self.assertEqual("main", page.attrs("main")[0].get("id"))
                self.assertEqual(1, len(page.attrs("h1")))
                self.assertEqual(1, len([item for item in page.attrs("meta") if item.get("name") == "viewport"]))
                ids = [values["id"] for _, _, values in page.tags if values.get("id")]
                self.assertEqual(len(ids), len(set(ids)), "duplicate HTML id")
                self.assertTrue(EXPECTED_SECTIONS.issubset(set(ids)))
                self.assertTrue(any(item.get("href") == "#main" for item in page.attrs("a")))
                for tag, attrs, _ in page.tags:
                    names = [name.lower() for name, _ in attrs]
                    self.assertEqual(len(names), len(set(names)), f"duplicate attribute on <{tag}>")
                for image in page.attrs("img"):
                    self.assertTrue(image.get("alt", "").strip())
                    self.assertTrue(image.get("width", "").isdigit())
                    self.assertTrue(image.get("height", "").isdigit())
                for anchor in page.attrs("a"):
                    if anchor.get("target") == "_blank":
                        self.assertIn("noopener", anchor.get("rel", "").split())
                labels = {item.get("for") for item in page.attrs("label") if item.get("for")}
                for field in [*page.attrs("input"), *page.attrs("select"), *page.attrs("textarea")]:
                    if field.get("type") == "hidden":
                        continue
                    self.assertTrue(field.get("id"), "form control lacks id")
                    self.assertIn(field["id"], labels, f"missing explicit label for {field['id']}")
                status = next(item for item in page.attrs("p") if item.get("id") == "lmFormStatus")
                self.assertEqual("alert", status.get("role"))
                self.assertEqual("assertive", status.get("aria-live"))

    def test_links_and_fragments_resolve(self) -> None:
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                page = parsed(relative)
                ids = {values["id"] for _, _, values in page.tags if values.get("id")}
                hrefs = {item.get("href", "") for item in page.attrs("a")}
                for required in (
                    expected["home"],
                    expected["programs"],
                    expected["mortgage"],
                    expected["closing"],
                    expected["contact"],
                    "/guides/nj-home-buyer-guide.pdf",
                ):
                    self.assertIn(required, hrefs)
                for href in hrefs:
                    if not href or href.startswith(("mailto:", "tel:")):
                        continue
                    split = urlsplit(href)
                    if href.startswith("#"):
                        self.assertIn(split.fragment, ids, f"missing fragment {href}")
                    target = local_target(href)
                    if target is not None:
                        self.assertTrue(target.exists(), f"broken internal link {href} -> {target}")
                        if split.fragment and target.resolve() == (ROOT / relative).resolve():
                            self.assertIn(split.fragment, ids, f"missing local fragment {href}")

    def test_lead_magnet_is_bilingual_truthful_and_preserves_download(self) -> None:
        self.assertTrue((ROOT / "guides" / "nj-home-buyer-guide.pdf").exists())
        script = read("js/lead-magnet.js")
        for attribute in ("data-error-name", "data-error-email", "data-sending"):
            self.assertIn(attribute, script)
        self.assertIn("formStatus", script)
        self.assertIn("focus()", script)
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                page = parsed(relative)
                card = next(item for item in page.attrs("section") if item.get("id") == "lmCard")
                self.assertEqual("buyer", card.get("data-guide"))
                self.assertEqual("/guides/nj-home-buyer-guide.pdf", card.get("data-pdf"))
                self.assertEqual(expected["form_source"], card.get("data-source"))
                self.assertTrue(card.get("data-error-name"))
                self.assertTrue(card.get("data-error-email"))
                self.assertTrue(card.get("data-sending"))
                self.assertTrue(card.get("data-consent"))
                self.assertIn("Consent is not a condition", card["data-consent"])
                scripts = {item.get("src") for item in page.attrs("script") if item.get("src")}
                self.assertIn("/js/lead-magnet.js", scripts)
                download_links = [
                    item for item in page.attrs("a")
                    if item.get("href") == "/guides/nj-home-buyer-guide.pdf"
                ]
                self.assertGreaterEqual(len(download_links), 2)

    def test_schema_matches_visible_article_breadcrumbs_and_faq(self) -> None:
        expected_counties = {
            "Union County, New Jersey",
            "Essex County, New Jersey",
            "Morris County, New Jersey",
            "Hudson County, New Jersey",
            "Middlesex County, New Jersey",
            "Somerset County, New Jersey",
        }
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                page = parsed(relative)
                schemas = [json.loads(block) for block in page.json_scripts]
                nodes = [node for schema in schemas for node in schema_nodes(schema)]
                types = set().union(*(schema_type(node) for node in nodes))
                self.assertTrue({"Article", "WebPage", "BreadcrumbList", "FAQPage"}.issubset(types))
                self.assertFalse({"Review", "AggregateRating", "HowTo"} & types)
                encoded = json.dumps(schemas, ensure_ascii=False)
                self.assertIn(expected["canonical"], encoded)
                self.assertIn('"dateModified": "2026-08-26"', encoded)
                self.assertIn('"value": "1754604"', encoded)
                self.assertIn("Keller Williams Premier Properties", encoded)
                for county in expected_counties:
                    self.assertIn(county, encoded)
                faq = next(node for node in nodes if "FAQPage" in schema_type(node))
                for question in faq["mainEntity"]:
                    name = " ".join(question["name"].split())
                    answer = " ".join(question["acceptedAnswer"]["text"].split())
                    self.assertIn(name.casefold(), page.visible_text.casefold())
                    self.assertIn(answer.casefold(), page.visible_text.casefold())

    def test_renderer_is_deterministic_and_owns_both_outputs(self) -> None:
        self.assertTrue(RENDERER.exists(), "dedicated renderer is missing")
        result = subprocess.run(
            [sys.executable, str(RENDERER), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        source = RENDERER.read_text(encoding="utf-8")
        for relative in PAGES:
            self.assertIn(relative, source)
        self.assertIn("GENERATED: render_nj_home_buyer_guides.py", read("nj-home-buyer-guide.html"))
        self.assertIn("GENERATED: render_nj_home_buyer_guides.py", read("es/nj-home-buyer-guide.html"))

    def test_downloadable_pdf_is_current_source_backed_and_deterministic(self) -> None:
        self.assertTrue(PDF.exists(), "downloadable buyer guide is missing")
        self.assertTrue(PDF_RENDERER.exists(), "dedicated PDF renderer is missing")
        info = subprocess.run(
            ["pdfinfo", str(PDF)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, info.returncode, info.stdout + info.stderr)
        self.assertRegex(info.stdout, r"(?m)^Pages:\s+6$")
        extracted = subprocess.run(
            ["pdftotext", "-layout", str(PDF), "-"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, extracted.returncode, extracted.stdout + extracted.stderr)
        text_content = " ".join(extracted.stdout.split())
        for required in (
            "New Jersey does not require a home buyer to hire an attorney.",
            "New Jersey Department of Banking and Insurance",
            "New Jersey Housing and Mortgage Finance Agency",
            "Consumer Financial Protection Bureau",
            "U.S. Department of Housing and Urban Development",
            "Loan Estimate",
            "Closing Disclosure",
            "Reviewed 2026-08-26",
            "License #1754604",
            "Keller Williams Premier Properties",
            "Union, Essex, Morris, Hudson, Middlesex, and Somerset counties",
            "Educational information only; not legal, tax, financial, mortgage, insurance, inspection, title, or engineering advice.",
        ):
            self.assertIn(required, text_content)
        forbidden = re.compile(
            r"(?:"
            r"\$\s*(?:15,?000|15k|17,?000|22,?000)|"
            r"\b(?:3\s*(?:-|–|to)\s*5|2\s*(?:-|–|to)\s*3)\s*%|"
            r"\b\d+(?:\.\d+)?\s*%|"
            r"\b(?:school selection|schools?|school districts?)\b|"
            r"\b138\s+(?:NJ\s+)?communities\b|"
            r"\b(?:hundreds|dozens)\s+of\s+(?:buyers|clients)\b|"
            r"\b(?:attorney required|mandatory attorney review|NJ requires an attorney)\b|"
            r"\b(?:guaranteed|guarantees?|avoid losing money|save money)\b|"
            r"\b(?:thirty|30)\s*(?:-|–|to)\s*(?:sixty|60)\s+days\b"
            r")",
            re.IGNORECASE,
        )
        match = forbidden.search(text_content)
        self.assertIsNone(match, match.group(0) if match else "")
        check = subprocess.run(
            [sys.executable, str(PDF_RENDERER), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)

if __name__ == "__main__":
    unittest.main()
