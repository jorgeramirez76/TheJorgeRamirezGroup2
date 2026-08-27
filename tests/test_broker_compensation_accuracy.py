#!/usr/bin/env python3
"""Fail-closed contracts for NJ broker-compensation explanations and tools."""

from __future__ import annotations

import html
import json
import re
import unittest
from pathlib import Path

from scripts.normalize_spanish_fair_housing import normalize as normalize_spanish


ROOT = Path(__file__).resolve().parents[1]
NJDOBI_BULLETIN = "https://www.nj.gov/dobi/bulletins/blt24_11.pdf"
NJ_RTF = "https://www.nj.gov/treasury/taxation/realty.shtml"
CFPB_SELLER_ADJUSTMENTS = (
    "https://www.consumerfinance.gov/rules-policy/regulations/1026/38/"
)
NJ_GPF_GUIDANCE = (
    "https://www.nj.gov/treasury/taxation/pdf/other_forms/"
    "graduated-percent-fee-exemptions.pdf"
)

ENGLISH = (
    "net-proceeds-calculator.html",
    "blog/how-much-are-closing-costs-nj.html",
    "blog/listing-agent-vs-selling-agent-nj.html",
)
SPANISH = (
    "es/net-proceeds-calculator.html",
    "es/blog/how-much-are-closing-costs-nj.html",
    "es/blog/moving-from-nyc-to-nj-guide.html",
)
CALCULATORS = {
    "net-proceeds-calculator.html": (
        "https://thejorgeramirezgroup.com/net-proceeds-calculator",
        "Enter the broker compensation from your written agreement.",
        "Flat dollar amount ($)",
    ),
    "es/net-proceeds-calculator.html": (
        "https://thejorgeramirezgroup.com/es/net-proceeds-calculator",
        "Ingresa la compensación del corredor de tu acuerdo escrito.",
        "Monto fijo en dólares ($)",
    ),
}

FORBIDDEN = re.compile(
    r"(?:"
    r"\b5\.2\s*%|\bpromedian\s*[≈~]?\s*5\.2|"
    r"\b4\.5\s*(?:-|–|—|a|y)\s*6\s*(?:%|por ciento)|"
    r"\b4\s*%\s*(?:-|–|—|to|a)\s*6\s*%|"
    r"\b8\s*%?\s*(?:-|–|—|to|al)\s*10\s*%|"
    r"\baverage total commission at about|"
    r"\btypical NJ net range\b|\brango neto típico de NJ\b|"
    r"\bel vendedor (?:normalmente|suele) paga las comisiones de ambos agentes\b|"
    r"\bno tiene costo para ti contar con representación\b|"
    r"\boferta fundamentada trato posible\b"
    r")",
    re.I,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>",
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


class BrokerCompensationAccuracyTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {relative: read(relative) for relative in (*ENGLISH, *SPANISH)}

    def test_all_six_surfaces_use_current_njdobi_disclosure_and_primary_source(self) -> None:
        english_phrases = (
            "broker compensation is fully negotiable and not set by law",
            "paid by the seller, buyer, a third party, or through compensation shared between brokerage firms",
            "written brokerage services agreement",
        )
        spanish_phrases = (
            "la compensación del corredor es totalmente negociable y no está fijada por ley",
            "pagarla el vendedor, el comprador o un tercero, o puede distribuirse entre firmas de corretaje",
            "acuerdo escrito de servicios de corretaje",
        )
        for relative in ENGLISH:
            candidate = visible_text(self.pages[relative]).casefold()
            with self.subTest(path=relative):
                self.assertIn(NJDOBI_BULLETIN, self.pages[relative])
                for phrase in english_phrases:
                    self.assertIn(phrase.casefold(), candidate)
        for relative in SPANISH:
            candidate = visible_text(self.pages[relative]).casefold()
            with self.subTest(path=relative):
                self.assertIn(NJDOBI_BULLETIN, self.pages[relative])
                for phrase in spanish_phrases:
                    self.assertIn(phrase.casefold(), candidate)

    def test_old_rate_payment_and_free_representation_claims_cannot_return(self) -> None:
        for relative, source in self.pages.items():
            with self.subTest(path=relative):
                self.assertIsNone(FORBIDDEN.search(html.unescape(source)))

        for relative in (
            "blog/how-much-are-closing-costs-nj.html",
            "es/blog/how-much-are-closing-costs-nj.html",
        ):
            source = self.pages[relative]
            with self.subTest(path=relative):
                for amount in (
                    "$20,000 - $24,000",
                    "$30,000 - $36,000",
                    "$40,000 - $48,000",
                    "$50,000 - $60,000",
                    "$75,000 - $90,000",
                ):
                    self.assertNotIn(amount, source)

    def test_calculators_require_user_supplied_compensation_and_use_canonical_schema(self) -> None:
        for relative, (canonical, validation_message, flat_label) in CALCULATORS.items():
            source = self.pages[relative]
            input_tag = re.search(
                r'<input\b[^>]*id="brokerCompensation"[^>]*>', source, re.I
            )
            method_select = re.search(
                r'<select\b[^>]*id="brokerCompensationMethod"[^>]*>(.*?)</select>',
                source,
                re.I | re.S,
            )
            applications = [
                block
                for block in json_ld(source)
                if isinstance(block, dict) and block.get("@type") == "WebApplication"
            ]
            with self.subTest(path=relative):
                self.assertIsNotNone(input_tag)
                self.assertIsNotNone(method_select)
                assert input_tag is not None
                assert method_select is not None
                self.assertNotRegex(input_tag.group(0), r'\bvalue="')
                self.assertRegex(input_tag.group(0), r"\brequired\b")
                self.assertIn('aria-describedby="brokerCompensationHelp"', input_tag.group(0))
                self.assertRegex(method_select.group(1), r'value="percentage"')
                self.assertRegex(method_select.group(1), r'value="flat"')
                self.assertIn(flat_label, visible_text(method_select.group(0)))
                self.assertIn("brokerCompensationInput.value.trim() === ''", source)
                self.assertIn("brokerCompensationInput.reportValidity()", source)
                self.assertIn(validation_message, source)
                self.assertRegex(
                    source,
                    r"brokerCompensationMethod\s*===\s*'flat'\s*\?\s*"
                    r"brokerCompensationValue\s*:\s*salePrice\s*\*\s*"
                    r"\(brokerCompensationValue\s*/\s*100\)",
                )
                self.assertNotIn("parseFloat(document.getElementById('commission').value) || 0", source)
                self.assertEqual(1, len(applications))
                self.assertEqual(canonical, applications[0]["url"])
                self.assertIn("description", applications[0])
                self.assertRegex(
                    source,
                    r'<div\s+class="results"\s+id="results"[^>]*'
                    r'aria-live="polite"[^>]*aria-labelledby="results-heading"',
                )
                self.assertIn('id="results-heading"', source)
                self.assertIn("(n < 0 ? '-$' : '$')", source)

    def test_calculator_result_copy_separates_user_entries_from_statutory_estimates(self) -> None:
        expectations = {
            "net-proceeds-calculator.html": (
                "All nonstatutory figures shown above came from your entries.",
                "The RTF, possible fee and any confirmed Graduated Percent Fee line are calculator estimates",
                "A possible fee marked not deducted is excluded from the displayed net.",
            ),
            "es/net-proceeds-calculator.html": (
                "Todas las cifras no estatutarias mostradas provienen de tus datos.",
                "La línea RTF, la posible tarifa y cualquier línea confirmada de Graduated Percent Fee son estimaciones de la calculadora",
                "Una posible tarifa marcada como no deducida queda excluida del neto mostrado.",
            ),
        }
        for relative, phrases in expectations.items():
            source = html.unescape(self.pages[relative])
            with self.subTest(path=relative):
                self.assertNotIn("annualTax * (3 / 12)", source)
                self.assertNotIn("closingMisc = 800", source)
                self.assertIn('id="propertyTaxAdjustment"', source)
                self.assertIn('id="propertyTaxAdjustmentDirection"', source)
                self.assertIn('value="debit"', source)
                self.assertIn('value="credit"', source)
                self.assertIn('id="graduatedPercentFeeApplicability"', source)
                self.assertIn('id="otherCosts"', source)
                self.assertIn('id="estimatedTaxPayment"', source)
                self.assertIn(NJ_RTF, source)
                self.assertIn(NJ_GPF_GUIDANCE, source)
                self.assertIn(CFPB_SELLER_ADJUSTMENTS, source)
                self.assertIn("if (!Number.isFinite(price) || price < 100) return 0;", source)
                self.assertIn("input.step = '0.01';", source)
                self.assertNotIn("input.step = isFlat ? '100'", source)
                self.assertIn("function roundCurrency(n)", source)
                for phrase in phrases:
                    self.assertIn(phrase, source)

    def test_closing_cost_tables_exclude_assumed_compensation_and_state_scope(self) -> None:
        expectations = {
            "blog/how-much-are-closing-costs-nj.html": (
                "before negotiated broker compensation",
                "Combined statutory-fee estimate",
                "$3,215",
                "$30,625",
                "It is not a seller total.",
            ),
            "es/blog/how-much-are-closing-costs-nj.html": (
                "antes de la compensación negociada del corredor",
                "Tarifas estatales combinadas",
                "$3,215",
                "$30,625",
                "No es un total del vendedor.",
            ),
        }
        for relative, phrases in expectations.items():
            source = self.pages[relative]
            with self.subTest(path=relative):
                self.assertNotRegex(
                    source,
                    r"<td>\s*(?:Agent Commissions?|Broker Compensation|"
                    r"Comisiones? de Agentes?|Compensación del Corredor)\b",
                )
                for phrase in phrases:
                    self.assertIn(phrase, source)
                self.assertIn(
                    (
                        "broker compensation is fully negotiable and not set by law"
                        if not relative.startswith("es/")
                        else "la compensación del corredor es totalmente negociable y no está fijada por ley"
                    ).casefold(),
                    visible_text(source).casefold(),
                )

    def test_listing_agent_schema_and_llm_copy_do_not_restore_rate_assumptions(self) -> None:
        source = self.pages["blog/listing-agent-vs-selling-agent-nj.html"]
        page_text = visible_text(source)
        schema_text = json.dumps(json_ld(source), ensure_ascii=False).casefold()
        llm = re.search(r'<meta name="llm-context" content="([^"]+)">', source)
        self.assertIsNotNone(llm)
        assert llm is not None
        for candidate in (html.unescape(llm.group(1)).casefold(), page_text.casefold()):
            self.assertIn(
                "broker compensation is fully negotiable and not set by law", candidate
            )
            self.assertIn("written brokerage services agreement", candidate)
        self.assertNotIn("faqpage", schema_text)
        self.assertNotRegex(page_text.casefold(), r"\b(?:owe|total) commission\b")
        self.assertIn("Updated August 27, 2026", page_text)

    def test_spanish_moving_copy_and_owning_normalizer_are_idempotent(self) -> None:
        relative = "es/blog/moving-from-nyc-to-nj-guide.html"
        source = self.pages[relative]
        expected = (
            "Su trabajo es ayudarte a comparar información verificable de cada municipio y, "
            "cuando elijas una propiedad, preparar y negociar una oferta fundamentada."
        )
        legacy = (
            "Su trabajo es ayudarte a encontrar el pueblo que se ajuste a tu vida y luego "
            "negociar el mejor trato posible en la casa que elijas."
        )

        normalized_legacy = normalize_spanish(legacy, relative)

        self.assertIn(expected, source)
        self.assertIn(expected, normalized_legacy)
        self.assertEqual(normalized_legacy, normalize_spanish(normalized_legacy, relative))
        self.assertEqual(source, normalize_spanish(source, relative))


if __name__ == "__main__":
    unittest.main()
