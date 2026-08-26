#!/usr/bin/env python3
"""Focused regression coverage for the bilingual NJ first-time-buyer guide."""

from __future__ import annotations

import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "first-time-home-buyer-guide-sources.json"
PAGES = {
    "blog/first-time-home-buyer-nj-guide.html": {
        "lang": "en",
        "canonical": "https://thejorgeramirezgroup.com/blog/first-time-home-buyer-nj-guide",
        "contact": "/contact",
        "search": "/property-search",
        "required_copy": (
            "The contract controls",
            "fully negotiable and not set by law",
            "not legal, tax, financial, insurance, or lending advice",
            "current program page",
            "Loan Estimate",
            "Closing Disclosure",
            "property-specific insurance quote",
            "independent home inspection",
        ),
    },
    "es/blog/first-time-home-buyer-nj-guide.html": {
        "lang": "es",
        "canonical": "https://thejorgeramirezgroup.com/es/blog/first-time-home-buyer-nj-guide",
        "contact": "/es#contact",
        "search": "/property-search",
        "required_copy": (
            "El contrato controla",
            "totalmente negociable y no está fijada por ley",
            "no constituye asesoría legal, tributaria, financiera, de seguros ni de crédito",
            "página vigente del programa",
            "Estimación del Préstamo",
            "Divulgación del Cierre",
            "cotización de seguro para la propiedad específica",
            "inspección independiente de la vivienda",
        ),
    },
}

OFFICIAL_HOSTS = {
    "nj.gov",
    "www.nj.gov",
    "www.consumerfinance.gov",
    "www.hud.gov",
}

PROHIBITED_CLAIMS = re.compile(
    r"(?:"
    r"\$\s*\d|"
    r"\b\d+(?:\.\d+)?\s*%|"
    r"\b(?:credit\s+score|puntaje\s+de\s+cr[eé]dito)\s*\d|"
    r"\b(?:closing\s+costs?|costos?\s+de\s+cierre)\s*(?:are|run|average|promedian|son)\b|"
    r"\b(?:prices?|precios?)\s+(?:will|could|pueden|podr[ií]an)\s+(?:rise|fall|subir|bajar)|"
    r"\b(?:always\s+refinance|siempre\s+puedes?\s+refinanciar)|"
    r"\b(?:guaranteed?\s+approval|aprobaci[oó]n\s+garantizada)|"
    r"\b(?:best|top|safest|family[- ]friendly)\s+(?:town|towns|place|places|school|schools)|"
    r"\b(?:mejores?|m[aá]s\s+segur[oa]s?)\s+(?:pueblos?|lugares?|escuelas?)|"
    r"\b(?:personal\s+letter|carta\s+personal)\s+(?:to|a)\s+(?:the\s+)?(?:seller|sellers|vendedor|vendedores)|"
    r"\b(?:helped|guided|ayudado|guiado)\s+(?:dozens|hundreds|decenas|cientos)\b|"
    r"\b(?:forty|40)\+?\s+homes\b"
    r")",
    re.IGNORECASE,
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.visible_parts: list[str] = []
        self.json_scripts: list[str] = []
        self._hidden_depth = 0
        self._json = False
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.tags.append((tag, values))
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json = True
            self._json_parts = []
        elif tag in {"script", "style", "template", "noscript"}:
            self._hidden_depth += 1

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
        return [attrs for current, attrs in self.tags if current == tag]

    @property
    def visible_text(self) -> str:
        return " ".join(self.visible_parts)


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def parsed(relative: str) -> PageParser:
    parser = PageParser()
    parser.feed(source(relative))
    return parser


def schema_types(value: object) -> set[str]:
    types: set[str] = set()
    if isinstance(value, dict):
        current = value.get("@type")
        if isinstance(current, str):
            types.add(current)
        elif isinstance(current, list):
            types.update(item for item in current if isinstance(item, str))
        for child in value.values():
            types.update(schema_types(child))
    elif isinstance(value, list):
        for child in value:
            types.update(schema_types(child))
    return types


class FirstTimeBuyerGuideTests(unittest.TestCase):
    def test_manifest_contains_only_visible_official_sources(self) -> None:
        self.assertTrue(MANIFEST.exists(), "official-source manifest is missing")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("2026-08-26", manifest["reviewed"])
        self.assertEqual(set(PAGES), set(manifest["pages"]))
        for relative in PAGES:
            with self.subTest(relative=relative):
                page = parsed(relative)
                hrefs = {item.get("href", "") for item in page.attrs("a")}
                records = manifest["pages"][relative]
                self.assertGreaterEqual(len(records), 10)
                for record in records:
                    self.assertEqual(
                        {"url", "publisher", "fact_supported", "accessed"},
                        set(record),
                    )
                    self.assertEqual("2026-08-26", record["accessed"])
                    self.assertTrue(record["publisher"].strip())
                    self.assertTrue(record["fact_supported"].strip())
                    self.assertIn((urlsplit(record["url"]).hostname or "").lower(), OFFICIAL_HOSTS)
                    self.assertIn(record["url"], hrefs)

    def test_metadata_canonical_hreflang_and_schema_are_bilingual_and_factual(self) -> None:
        expected_alternates = {
            ("en-US", "https://thejorgeramirezgroup.com/blog/first-time-home-buyer-nj-guide"),
            ("es-US", "https://thejorgeramirezgroup.com/es/blog/first-time-home-buyer-nj-guide"),
            ("x-default", "https://thejorgeramirezgroup.com/blog/first-time-home-buyer-nj-guide"),
        }
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                raw = source(relative)
                page = parsed(relative)
                self.assertEqual(expected["lang"], page.attrs("html")[0].get("lang"))
                title = " ".join(re.search(r"<title>(.*?)</title>", raw, re.I | re.S).group(1).split())
                self.assertGreaterEqual(len(title), 35)
                self.assertLessEqual(len(title), 65)
                descriptions = [
                    item.get("content", "")
                    for item in page.attrs("meta")
                    if item.get("name") == "description"
                ]
                self.assertEqual(1, len(descriptions))
                self.assertGreaterEqual(len(descriptions[0]), 120)
                self.assertLessEqual(len(descriptions[0]), 165)
                canonicals = [
                    item.get("href", "")
                    for item in page.attrs("link")
                    if item.get("rel") == "canonical"
                ]
                self.assertEqual([expected["canonical"]], canonicals)
                alternates = {
                    (item.get("hreflang"), item.get("href"))
                    for item in page.attrs("link")
                    if item.get("rel") == "alternate"
                }
                self.assertTrue(expected_alternates.issubset(alternates))
                robots = [
                    item.get("content", "")
                    for item in page.attrs("meta")
                    if item.get("name") == "robots"
                ]
                self.assertEqual(1, len(robots))
                self.assertIn("index", robots[0])
                self.assertNotIn("noindex", robots[0])
                schemas = [json.loads(block) for block in page.json_scripts]
                types = set().union(*(schema_types(item) for item in schemas))
                self.assertTrue({"BlogPosting", "BreadcrumbList", "FAQPage"}.issubset(types))
                self.assertFalse({"Review", "AggregateRating", "HowTo"} & types)
                encoded = json.dumps(schemas)
                self.assertNotIn("ratingValue", encoded)
                self.assertIn('"dateModified": "2026-08-26"', encoded)
                self.assertIn(expected["canonical"], encoded)

    def test_financial_legal_and_market_claims_are_durable_and_qualified(self) -> None:
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                page = parsed(relative)
                claims = " ".join([page.visible_text, *page.json_scripts])
                match = PROHIBITED_CLAIMS.search(claims)
                self.assertIsNone(match, match.group(0) if match else "")
                for required in expected["required_copy"]:
                    self.assertIn(required.casefold(), claims.casefold())
                self.assertIn("2026-08-26", claims)

    def test_process_covers_each_due_diligence_checkpoint(self) -> None:
        expected_ids = {
            "budget",
            "lenders",
            "programs",
            "representation",
            "offer",
            "attorney-review",
            "inspection",
            "underwriting",
            "closing",
            "sources",
            "faq",
        }
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                page = parsed(relative)
                ids = [item.get("id", "") for _, item in page.tags if item.get("id")]
                self.assertEqual(len(ids), len(set(ids)), "duplicate HTML id")
                self.assertTrue(expected_ids.issubset(set(ids)))
                self.assertEqual(1, len(page.attrs("main")))
                self.assertEqual("main", page.attrs("main")[0].get("id"))
                self.assertEqual(1, len(page.attrs("h1")))
                self.assertTrue(any(item.get("href") == "#main" for item in page.attrs("a")))
                self.assertIn(expected["contact"], {item.get("href") for item in page.attrs("a")})
                self.assertIn(expected["search"], {item.get("href") for item in page.attrs("a")})
                faq_schemas = []
                for block in page.json_scripts:
                    value = json.loads(block)
                    if isinstance(value, dict) and value.get("@type") == "FAQPage":
                        faq_schemas.append(value)
                self.assertEqual(1, len(faq_schemas))
                questions = faq_schemas[0]["mainEntity"]
                self.assertGreaterEqual(len(questions), 4)
                for question in questions:
                    self.assertIn(question["name"], page.visible_text)
                    self.assertIn(question["acceptedAnswer"]["text"], page.visible_text)

    def test_official_links_and_first_party_calls_to_action_are_safe(self) -> None:
        for relative in PAGES:
            with self.subTest(relative=relative):
                page = parsed(relative)
                official_links = [
                    item
                    for item in page.attrs("a")
                    if (urlsplit(item.get("href", "")).hostname or "").lower() in OFFICIAL_HOSTS
                ]
                self.assertGreaterEqual(len(official_links), 10)
                for link in official_links:
                    self.assertEqual("_blank", link.get("target"))
                    self.assertIn("noopener", link.get("rel", "").split())
                ctas = [item for item in page.attrs("a") if "cta" in item.get("class", "").split()]
                self.assertGreaterEqual(len(ctas), 2)
                for cta in ctas:
                    href = cta.get("href", "")
                    self.assertTrue(href.startswith("/"), href)

    def test_visual_system_responsiveness_and_touch_targets_match_homepage(self) -> None:
        for relative in PAGES:
            with self.subTest(relative=relative):
                raw = source(relative)
                self.assertIn("--primary-red: #C41230", raw)
                self.assertIn("--gold: #B8962E", raw)
                self.assertIn("--dark-bg: #0A0A0A", raw)
                self.assertIn("--dark-gray: #1A1A1A", raw)
                self.assertIn("--ivory: #FAFAF8", raw)
                self.assertIn("'Playfair Display'", raw)
                self.assertIn("'Inter'", raw)
                self.assertIn('class="guide-toc"', raw)
                self.assertRegex(
                    raw,
                    r"\.guide-toc\s*\{[^}]*position:\s*static",
                )
                self.assertRegex(
                    raw,
                    r"\.nav-links\s*\{[^}]*position:\s*static[^}]*flex-direction:\s*row",
                )
                self.assertRegex(raw, r"min-height:\s*44px")
                self.assertIn("@media (max-width: 760px)", raw)
                self.assertIn("@media (prefers-reduced-motion: reduce)", raw)


if __name__ == "__main__":
    unittest.main()
