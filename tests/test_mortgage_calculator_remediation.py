#!/usr/bin/env python3
"""Focused safeguards for the English and Spanish mortgage calculators."""

from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "mortgage-calculator-sources.json"
PAGES = {
    "tools/mortgage-calculator.html": {
        "lang": "en",
        "canonical": "https://thejorgeramirezgroup.com/tools/mortgage-calculator",
        "source": "/tools/mortgage-calculator",
        "contact": "/contact",
        "required_caveats": (
            "does not determine what you can afford",
            "not a loan offer or loan approval",
            "not legal, tax, financial, or insurance advice",
        ),
        "accepted": "request was accepted by this site's first-party system",
    },
    "es/tools/mortgage-calculator.html": {
        "lang": "es",
        "canonical": "https://thejorgeramirezgroup.com/es/tools/mortgage-calculator",
        "source": "/es/tools/mortgage-calculator",
        "contact": "/es/#contact",
        "required_caveats": (
            "no determina cuánto puedes pagar",
            "no es una oferta ni una aprobación de préstamo",
            "no constituye asesoría legal, tributaria, financiera ni de seguros",
        ),
        "accepted": "solicitud fue aceptada por el sistema propio de este sitio",
    },
}

ALLOWED_OFFICIAL_HOSTS = {
    "www.consumerfinance.gov",
    "www.hud.gov",
    "www.nj.gov",
    "nj.gov",
}

PROHIBITED_CLAIMS = re.compile(
    r"(?:"
    r"most people have no idea|la mayoría de las personas no tiene idea|"
    r"how much (?:home|house) you can afford|cuánta casa puedes pagar|"
    r"cuánto podrías pagar por una casa|"
    r"typical nj effective property tax|tasas efectivas típicas|"
    r"top three nationally|tres estados con la tasa efectiva más alta|"
    r"\b28\s*/\s*36\b|\b28 percent\b|\b36 percent\b|"
    r"\b28 por ciento\b|\b36 por ciento\b|"
    r"attorney[- ]state|estado de abogados|"
    r"most buyers|la mayoría de compradores|most lenders|la mayoría de los prestamistas|"
    r"home prices climb|suben los precios|financially smarter|jugada financiera más inteligente|"
    r"roughly doubles|casi duplica|fair middle ground|punto medio razonable|"
    r"buyers no longer pay|los compradores ya no pagan|"
    r"\$\d[\d,]*\s+(?:to|a)\s+\$\d[\d,]*|"
    r"\b\d+(?:\.\d+)?\s+(?:to|a)\s+\d+(?:\.\d+)?\s+percent\b|"
    r"\b\d+(?:\.\d+)?\s+(?:a|y)\s+\d+(?:\.\d+)?\s+por ciento\b"
    r")",
    re.IGNORECASE,
)


class CalculatorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.visible: list[str] = []
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
        elif tag in {"script", "style"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json:
            self.json_scripts.append("".join(self._json_parts).strip())
            self._json = False
            self._json_parts = []
        elif tag in {"script", "style"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._json:
            self._json_parts.append(data)
        elif not self._hidden_depth:
            value = " ".join(data.split())
            if value:
                self.visible.append(value)

    def attrs(self, tag: str) -> list[dict[str, str]]:
        return [attrs for current, attrs in self.tags if current == tag]

    @property
    def visible_text(self) -> str:
        return " ".join(self.visible)


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def parsed(relative: str) -> CalculatorParser:
    parser = CalculatorParser()
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


class MortgageCalculatorRemediationTests(unittest.TestCase):
    def test_source_manifest_is_official_traceable_and_visible(self) -> None:
        self.assertTrue(MANIFEST.exists(), "official-source manifest is missing")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("2026-08-26", manifest["accessed"])
        self.assertEqual(set(PAGES), set(manifest["pages"]))
        for relative in PAGES:
            with self.subTest(relative=relative):
                hrefs = {item.get("href", "") for item in parsed(relative).attrs("a")}
                records = manifest["pages"][relative]
                self.assertGreaterEqual(len(records), 7)
                for record in records:
                    self.assertEqual(
                        {"url", "publisher", "fact_supported", "accessed"},
                        set(record),
                    )
                    self.assertEqual("2026-08-26", record["accessed"])
                    self.assertTrue(record["publisher"].strip())
                    self.assertTrue(record["fact_supported"].strip())
                    self.assertIn(urlsplit(record["url"]).netloc, ALLOWED_OFFICIAL_HOSTS)
                    self.assertIn(record["url"], hrefs)

    def test_metadata_language_canonical_hreflang_and_schema_are_consistent(self) -> None:
        titles: set[str] = set()
        descriptions: set[str] = set()
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                text = source(relative)
                parser = parsed(relative)
                self.assertEqual(expected["lang"], parser.attrs("html")[0].get("lang"))
                title_match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
                self.assertIsNotNone(title_match)
                title = " ".join(title_match.group(1).split())
                self.assertNotIn("2026", title)
                self.assertGreaterEqual(len(title), 35)
                self.assertLessEqual(len(title), 65)
                descriptions_for_page = [
                    item.get("content", "")
                    for item in parser.attrs("meta")
                    if item.get("name") == "description"
                ]
                self.assertEqual(1, len(descriptions_for_page))
                description = descriptions_for_page[0]
                self.assertGreaterEqual(len(description), 120)
                self.assertLessEqual(len(description), 165)
                canonical = [
                    item.get("href")
                    for item in parser.attrs("link")
                    if item.get("rel") == "canonical"
                ]
                self.assertEqual([expected["canonical"]], canonical)
                alternates = {
                    (item.get("hreflang"), item.get("href"))
                    for item in parser.attrs("link")
                    if item.get("rel") == "alternate"
                }
                self.assertIn(
                    ("en-US", "https://thejorgeramirezgroup.com/tools/mortgage-calculator"),
                    alternates,
                )
                self.assertIn(
                    ("es-US", "https://thejorgeramirezgroup.com/es/tools/mortgage-calculator"),
                    alternates,
                )
                self.assertIn(
                    ("x-default", "https://thejorgeramirezgroup.com/tools/mortgage-calculator"),
                    alternates,
                )
                schemas = [json.loads(item) for item in parser.json_scripts]
                types = set().union(*(schema_types(item) for item in schemas))
                self.assertTrue({"WebPage", "BreadcrumbList", "FAQPage"}.issubset(types))
                self.assertFalse(
                    {"Review", "AggregateRating", "FinancialProduct", "LoanOrCredit"} & types
                )
                faq_questions: list[str] = []
                for item in schemas:
                    nodes = item.get("@graph", [item]) if isinstance(item, dict) else []
                    for node in nodes:
                        if isinstance(node, dict) and node.get("@type") == "FAQPage":
                            faq_questions.extend(
                                entity["name"] for entity in node.get("mainEntity", [])
                            )
                self.assertGreaterEqual(len(faq_questions), 3)
                for question in faq_questions:
                    self.assertIn(question, parser.visible_text)
                titles.add(title)
                descriptions.add(description)
        self.assertEqual(2, len(titles))
        self.assertEqual(2, len(descriptions))

    def test_copy_and_machine_readable_claims_are_neutral_and_durable(self) -> None:
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                parser = parsed(relative)
                metadata = " ".join(
                    item.get("content", "")
                    for item in parser.attrs("meta")
                    if item.get("name") in {"description", "llm-context"}
                    or item.get("property")
                    in {"og:title", "og:description", "twitter:title", "twitter:description"}
                )
                claims = " ".join([parser.visible_text, metadata, *parser.json_scripts])
                match = PROHIBITED_CLAIMS.search(claims)
                self.assertIsNone(match, match.group(0) if match else "")
                for caveat in expected["required_caveats"]:
                    self.assertIn(caveat, claims.lower())

    def test_financial_inputs_have_no_volatile_presets_or_hidden_pmi_assumption(self) -> None:
        financial_ids = {
            "homePrice",
            "downPayment",
            "interestRate",
            "propertyTax",
            "insurance",
            "mortgageInsurance",
            "hoa",
        }
        for relative in PAGES:
            with self.subTest(relative=relative):
                parser = parsed(relative)
                by_id = {item.get("id"): item for item in parser.attrs("input")}
                self.assertTrue(financial_ids.issubset(by_id))
                for field_id in financial_ids:
                    self.assertFalse(by_id[field_id].get("value", "").strip(), field_id)
                text = source(relative)
                self.assertNotIn("0.005", text)
                self.assertNotIn(".005", text)
                self.assertNotRegex(text, r"downPct\s*<\s*0\.20")
                self.assertIn("monthlyMortgageInsurance", text)

    def test_calculator_math_and_first_party_lead_delivery_remain_intact(self) -> None:
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                text = source(relative)
                self.assertRegex(
                    text,
                    r"loanAmount\s*=\s*Math\.max\(0,\s*homePrice\s*-\s*downPayment\)",
                )
                self.assertRegex(text, r"monthlyRate\s*=\s*\(annualRate\s*/\s*100\)\s*/\s*12")
                self.assertIn("Math.pow(1 + monthlyRate, numPayments)", text)
                self.assertRegex(text, r"taxMonthly\s*=\s*annualTax\s*/\s*12")
                self.assertRegex(text, r"insMonthly\s*=\s*annualInsurance\s*/\s*12")
                self.assertRegex(
                    text,
                    r"total\s*=\s*pi\s*\+\s*taxMonthly\s*\+\s*insMonthly\s*\+\s*monthlyMortgageInsurance\s*\+\s*monthlyHOA",
                )
                self.assertIn("window._calcResults", text)
                self.assertIn("fetch('/api/lead'", text)
                self.assertIn("method: 'POST'", text)
                self.assertIn("data.ok === true && data.accepted === true", text)
                self.assertIn(f"_source: '{expected['source']}'", text)
                self.assertNotIn("WEB3FORMS_KEY", text)
                self.assertIn(expected["accepted"], parsed(relative).visible_text.lower())

    def test_brand_and_accessibility_contract(self) -> None:
        for relative in PAGES:
            with self.subTest(relative=relative):
                text = source(relative)
                parser = parsed(relative)
                hrefs = {item.get("href", "") for item in parser.attrs("a")}
                for token in (
                    "#0A0A0A",
                    "#1A1A1A",
                    "#C41230",
                    "#8B0D22",
                    "#B8962E",
                    "#FAFAF8",
                    "Playfair Display",
                    "Inter",
                ):
                    self.assertIn(token, text)
                self.assertEqual(1, len(re.findall(r"<main(?:\s|>)", text, re.I)))
                self.assertRegex(text, r'<main\s+id=["\']main["\']')
                self.assertEqual(1, len(re.findall(r"<h1(?:\s|>)", text, re.I)))
                self.assertIn('href="#main"', text)
                self.assertRegex(text, r'<nav\b[^>]*aria-label=["\'][^"\']+["\']')
                labels = {item.get("for") for item in parser.attrs("label")}
                input_ids = {
                    item.get("id") for item in parser.attrs("input") + parser.attrs("select")
                }
                self.assertTrue(input_ids.issubset(labels))
                self.assertIn('aria-live="polite"', text)
                self.assertIn('type="button"', text)
                self.assertIn("@media (max-width: 600px)", text)
                self.assertIn(PAGES[relative]["contact"], hrefs)


if __name__ == "__main__":
    unittest.main()
