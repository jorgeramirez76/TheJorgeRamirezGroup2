#!/usr/bin/env python3
"""Fail-closed contracts for the scoped NJ financial/legal accuracy pass."""

from __future__ import annotations

import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NJDOBI_BUYING_GUIDE = "https://www.nj.gov/dobi/division_consumers/pdf/buyingahome.pdf"
NJDOBI_COMPENSATION = "https://www.nj.gov/dobi/bulletins/blt24_11.pdf"
NJ_GIT_REP = "https://nj.gov/treasury/taxation/gitrepfaqs.shtml"
NJ_GIT_REP_WWW = "https://www.nj.gov/treasury/taxation/gitrepfaqs.shtml"
NJ_RTF = "https://www.nj.gov/treasury/taxation/realty.shtml"
CFPB_LOAN_ESTIMATE = (
    "https://www.consumerfinance.gov/ask-cfpb/what-is-a-loan-estimate-en-1995/"
)
CFPB_CLOSING_DISCLOSURE = (
    "https://www.consumerfinance.gov/ask-cfpb/what-is-a-closing-disclosure-en-1983/"
)
IRS_HOME_SALE = "https://www.irs.gov/taxtopics/tc701"
NJ_HOME_SALE = "https://www.nj.gov/treasury/taxation/njit10.shtml"
NJ_PROPERTY_TAX_RELIEF_FAQ = (
    "https://www.nj.gov/treasury/taxation/propertytaxrelieffaq.shtml"
)
NJ_PAS1_INSTRUCTIONS = "https://www.nj.gov/treasury/taxation/pdf/25-pas1in.pdf"

PAGES = {
    "closing-costs-calculator.html": "/closing-costs-calculator",
    "es/closing-costs-calculator.html": "/es/closing-costs-calculator",
    "net-proceeds-calculator.html": "/net-proceeds-calculator",
    "es/net-proceeds-calculator.html": "/es/net-proceeds-calculator",
    "blog/nj-exit-tax-explained.html": "/blog/nj-exit-tax-explained",
    "blog/capital-gains-tax-selling-house-nj.html": (
        "/blog/capital-gains-tax-selling-house-nj"
    ),
    "blog/how-much-are-closing-costs-nj.html": (
        "/blog/how-much-are-closing-costs-nj"
    ),
    "es/blog/how-much-are-closing-costs-nj.html": (
        "/es/blog/how-much-are-closing-costs-nj"
    ),
    "blog/listing-agent-vs-selling-agent-nj.html": (
        "/blog/listing-agent-vs-selling-agent-nj"
    ),
    "blog/stay-nj-senior-property-tax-relief.html": (
        "/blog/stay-nj-senior-property-tax-relief"
    ),
}

BUYER_CALCULATORS = (
    "closing-costs-calculator.html",
    "es/closing-costs-calculator.html",
)
SELLER_CALCULATORS = (
    "net-proceeds-calculator.html",
    "es/net-proceeds-calculator.html",
)
FINANCING_GUIDES = (
    "blog/how-much-are-closing-costs-nj.html",
    "es/blog/how-much-are-closing-costs-nj.html",
)

FORBIDDEN = re.compile(
    r"(?:"
    r"\bnew jersey is an attorney(?:-review)? state\b|"
    r"\bnj is an attorney(?:-review)? state\b|"
    r"\bnj requires an attorney\b|"
    r"\b(?:nj|nueva jersey) es un estado de abogado\b|"
    r"\bnj requiere un abogado\b|"
    r"\bnot optional in practice\b|\bno es opcional en la pr[aá]ctica\b|"
    r"\brealistic estimate\b|\bestimado realista\b|"
    r"\btypical nj range\b|\brango t[ií]pico (?:para|de) nj\b|"
    r"\bmost (?:new jersey |home )?sellers (?:owe nothing|are exempt)\b|"
    r"\bprobably not yours\b|"
    r"\btypically has nothing withheld\b|\busually has nothing withheld\b|"
    r"\boften a substantial part of it\b|"
    r"\bthe difference comes back\b|"
    r"\bfull seller net sheet\b|\bhoja neta completa\b|"
    r"\binspection credits?[^.<]{0,80}\b1\s*[–—-]\s*2\s*%"
    r")",
    re.I,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style|template|noscript)\b[^>]*>.*?</(?:script|style|template|noscript)>",
        " ",
        source,
        flags=re.I | re.S,
    )
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def json_ld(source: str) -> list[object]:
    return [
        json.loads(block)
        for block in re.findall(
            r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>'
            r"(.*?)</script>",
            source,
            flags=re.I | re.S,
        )
    ]


def schema_nodes(value: object) -> list[dict[str, object]]:
    nodes: list[dict[str, object]] = []
    if isinstance(value, dict):
        nodes.append(value)
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                nodes.extend(schema_nodes(item))
    elif isinstance(value, list):
        for item in value:
            nodes.extend(schema_nodes(item))
    return nodes


class InputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.inputs: dict[str, dict[str, str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "input":
            return
        values = {key.lower(): value or "" for key, value in attrs}
        if values.get("id"):
            self.inputs[values["id"]] = values


class FinancialLegalAccuracyTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {relative: read(relative) for relative in PAGES}

    def test_all_scoped_pages_remain_canonical_indexable_and_schema_valid(self) -> None:
        site = "https://thejorgeramirezgroup.com"
        for relative, route in PAGES.items():
            source = self.sources[relative]
            with self.subTest(path=relative):
                self.assertIn(
                    f'<link rel="canonical" href="{site}{route}">', source
                )
                self.assertRegex(
                    source,
                    r'<meta\s+name="robots"\s+content="index, follow,',
                )
                blocks = json_ld(source)
                self.assertGreaterEqual(len(blocks), 1)
                self.assertNotRegex(source, r'"@type"\s*:\s*"FAQPage"')
                self.assertIn("2026-08-27", source)

    def test_attorney_review_is_optional_and_sourced_not_mandated(self) -> None:
        relevant = (*BUYER_CALCULATORS, *SELLER_CALCULATORS, *FINANCING_GUIDES,
                    "blog/listing-agent-vs-selling-agent-nj.html")
        for relative in relevant:
            source = self.sources[relative]
            text = visible_text(source).casefold()
            with self.subTest(path=relative):
                self.assertIn(NJDOBI_BUYING_GUIDE, source)
                if relative.startswith("es/"):
                    self.assertIn("si eliges consultar a un abogado", text)
                else:
                    self.assertIn("if you choose to consult an attorney", text)
                self.assertIsNone(FORBIDDEN.search(html.unescape(source)))

    def test_buyer_calculators_are_blank_user_entered_document_worksheets(self) -> None:
        input_ids = (
            "loanCosts",
            "titleSettlement",
            "governmentFees",
            "prepaids",
            "initialEscrow",
            "attorneyFee",
            "inspectionAppraisal",
            "otherBuyerCosts",
            "credits",
        )
        old_assumptions = (
            "loanType",
            "downPct",
            "price * 0.005",
            "loanAmount * 0.0075",
            "loanAmount * 0.0175",
            "loanAmount * 0.0215",
            "annualTax * 0.25",
            "loanAmount * 0.07 / 365",
            "$18,231",
            "$138,000",
        )
        for relative in BUYER_CALCULATORS:
            source = self.sources[relative]
            parser = InputParser()
            parser.feed(source)
            applications = [
                node
                for block in json_ld(source)
                for node in schema_nodes(block)
                if node.get("@type") == "WebApplication"
            ]
            with self.subTest(path=relative):
                for input_id in input_ids:
                    self.assertIn(input_id, parser.inputs)
                    self.assertNotIn("value", parser.inputs[input_id])
                    self.assertEqual("0", parser.inputs[input_id].get("min"))
                for old in old_assumptions:
                    self.assertNotIn(old, source)
                self.assertIn(CFPB_LOAN_ESTIMATE, source)
                self.assertIn(CFPB_CLOSING_DISCLOSURE, source)
                self.assertIn('id="worksheetStatus"', source)
                self.assertIn('aria-live="polite"', source)
                self.assertEqual(1, len(applications))
                self.assertEqual(
                    "https://thejorgeramirezgroup.com" + PAGES[relative],
                    applications[0].get("url"),
                )
                description = json.dumps(applications[0]).lower()
                self.assertTrue(
                    "user-entered" in description
                    or "ingresados por el usuario" in description
                )

    def test_seller_calculators_use_dynamic_compensation_bounds_and_blank_costs(self) -> None:
        blank_ids = (
            "salePrice",
            "payoff",
            "brokerCompensation",
            "attorney",
            "propertyTaxAdjustment",
            "otherCosts",
            "concessions",
            "estimatedTaxPayment",
        )
        for relative in SELLER_CALCULATORS:
            source = self.sources[relative]
            parser = InputParser()
            parser.feed(source)
            with self.subTest(path=relative):
                for input_id in blank_ids:
                    self.assertIn(input_id, parser.inputs)
                    self.assertNotIn("value", parser.inputs[input_id])
                self.assertEqual("100", parser.inputs["brokerCompensation"].get("max"))
                self.assertIn("input.max = '100'", source)
                self.assertIn("input.removeAttribute('max')", source)
                self.assertNotIn("annualTax * (3 / 12)", source)
                self.assertNotIn("closingMisc = 800", source)
                self.assertNotIn("value=\"2000\"", source)
                self.assertNotIn("value=\"12000\"", source)
                self.assertIn(NJDOBI_COMPENSATION, source)
                self.assertTrue(NJ_GIT_REP in source or NJ_GIT_REP_WWW in source)
                self.assertIn(NJ_RTF, source)
                self.assertRegex(
                    visible_text(source),
                    r"(?i)(?:estimated NJ Realty Transfer Fee|"
                    r"Impuesto de Transferencia Inmobiliaria de NJ estimado)",
                )

    def test_git_rep_and_home_sale_guidance_is_conditional_and_primary_sourced(self) -> None:
        git_pages = (
            *SELLER_CALCULATORS,
            "blog/nj-exit-tax-explained.html",
            "blog/capital-gains-tax-selling-house-nj.html",
        )
        for relative in git_pages:
            source = self.sources[relative]
            with self.subTest(path=relative):
                self.assertTrue(NJ_GIT_REP in source or NJ_GIT_REP_WWW in source)
                self.assertIsNone(FORBIDDEN.search(html.unescape(source)))
                self.assertRegex(
                    visible_text(source),
                    r"(?i)(?:not (?:tax or legal|legal or tax|tax|legal) advice|"
                    r"no (?:es )?asesoramiento (?:fiscal o legal|legal o fiscal|fiscal|legal))",
                )

        capital = self.sources["blog/capital-gains-tax-selling-house-nj.html"]
        self.assertIn(IRS_HOME_SALE, capital)
        self.assertIn(NJ_HOME_SALE, capital)
        for phrase in (
            "Most New Jersey sellers owe nothing",
            "Usually not.",
            "ordinary outcome for most people",
            "neither government taxes it",
            "then get it back",
        ):
            self.assertNotIn(phrase, html.unescape(capital))

    def test_closing_guides_use_disclosures_not_provider_price_assumptions(self) -> None:
        for relative in FINANCING_GUIDES:
            source = self.sources[relative]
            text = html.unescape(source)
            with self.subTest(path=relative):
                self.assertIn(CFPB_LOAN_ESTIMATE, source)
                self.assertIn(CFPB_CLOSING_DISCLOSURE, source)
                self.assertNotRegex(text, r"\$18,231|\$138,000|\b2\s*%\s*(?:to|a|–|-)\s*5\s*%")
                self.assertNotRegex(text, r"\b0\.5%\s+(?:of|del)\b|\b0\.75%\b")
                self.assertRegex(
                    visible_text(source),
                    r"(?i)(?:before negotiated broker compensation|"
                    r"antes de la compensación negociada del corredor)",
                )

    def test_stay_nj_reconciles_application_and_current_budget_guidance(self) -> None:
        source = self.sources["blog/stay-nj-senior-property-tax-relief.html"]
        text = visible_text(source)
        self.assertIn(NJ_PROPERTY_TAX_RELIEF_FAQ, source)
        self.assertIn(NJ_PAS1_INSTRUCTIONS, source)
        self.assertIn("November 2, 2026", text)
        self.assertRegex(text, r"under \$500,000 to file")
        self.assertRegex(text, r"income up to \$200,000")
        self.assertRegex(text, r"subject to (?:State Budget|annual State Budget) appropriations")
        self.assertIn("Taxation determines eligibility", text)
        for stale in (
            "Stay NJ pays eligible",
            "$6,500",
            "$5,000",
            "$4,000",
            "I have sat with enough NJ homeowners",
            "The money is usually not the deciding factor",
        ):
            self.assertNotIn(stale, html.unescape(source))

    def test_homepage_brand_tokens_and_accessible_results_are_preserved(self) -> None:
        for relative in (*BUYER_CALCULATORS, *SELLER_CALCULATORS):
            source = self.sources[relative]
            with self.subTest(path=relative):
                for token in ("#C41230", "#B8962E", "#FAFAF8", "Playfair Display", "Inter"):
                    self.assertIn(token, source)
                for off_palette in ("#28a745", "#c0392b", "#a0b8ff", "#f0f4ff"):
                    self.assertNotIn(off_palette, source.casefold())
                self.assertRegex(source, r'<main\s+id="main"')
                self.assertRegex(source, r'class="results"\s+id="results"[^>]*aria-live="polite"')
                self.assertIn('id="results-heading"', source)


if __name__ == "__main__":
    unittest.main()
