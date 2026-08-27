#!/usr/bin/env python3
"""Fail-closed contracts for the rent/buy and buyer-planning rebuild."""

from __future__ import annotations

import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EN = "rent-vs-buy-nj.html"
ES = "es/rent-vs-buy-nj.html"
COMMUTE = "blog/nj-commute-cost-nyc-2026.html"
CASH = "blog/how-much-money-to-buy-a-house-nj.html"
PROGRAMS = "blog/nj-first-time-home-buyer-programs-2026.html"

NJ_TRANSIT = "https://www.njtransit.com/fares/"
PATH = "https://www.panynj.gov/path/en/fares.html"
PORT_AUTHORITY_TOLLS = "https://www.panynj.gov/bridges-tunnels/en/tolls.html"
CONGESTION = "https://congestionreliefzone.mta.info/tolling"
SUMMIT_PARKING = "https://cityofsummit.org/207/Commuter-Parking"
CFPB_LOAN_ESTIMATE = "https://www.consumerfinance.gov/owning-a-home/loan-estimate/"
CFPB_CLOSING = "https://www.consumerfinance.gov/owning-a-home/closing-disclosure/"
NJDOBI_BUYING = "https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf"
NJHMFA_HOME = "https://www.nj.gov/dca/hmfa/homebuyers-and-renters/homebuyers/"
NJHMFA_2026_FACT = "https://www.nj.gov/dca/hmfa/homebuyers-and-renters/docs/FTHB-ConsumerFactSheet.pdf"

RENT_INPUTS = {
    "purchasePrice", "downPayment", "mortgageRate", "mortgageTerm",
    "plannedYears", "monthlyRent", "annualRentChange", "annualPropertyTax",
    "annualHomeInsurance", "monthlyHoa", "annualMaintenance", "monthlyMortgageInsurance",
    "buyerClosingCosts", "annualAppreciation", "sellerExitCosts",
    "monthlyRentersInsurance", "renterNonrefundableCosts",
    "alternativeInvestment", "annualInvestmentReturn",
}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def text(source: str) -> str:
    source = re.sub(r"<(?:script|style|template|noscript)\b[^>]*>.*?</(?:script|style|template|noscript)>", " ", source, flags=re.I | re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def schemas(source: str) -> list[dict]:
    return [json.loads(block) for block in re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source, flags=re.I | re.S,
    )]


class InputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.inputs: dict[str, dict[str, str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "input":
            values = {key.casefold(): value or "" for key, value in attrs}
            if values.get("id"):
                self.inputs[values["id"]] = values


class DecisionFinanceRebuildTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {name: read(name) for name in (EN, ES, COMMUTE, CASH, PROGRAMS)}

    def test_rent_buy_pages_are_blank_transparent_user_scenarios(self) -> None:
        for relative in (EN, ES):
            source = self.pages[relative]
            parser = InputParser()
            parser.feed(source)
            with self.subTest(path=relative):
                self.assertTrue(RENT_INPUTS.issubset(parser.inputs))
                for input_id in RENT_INPUTS:
                    self.assertNotIn("value", parser.inputs[input_id], input_id)
                self.assertIn('id="rentBuyForm"', source)
                self.assertIn('id="worksheetStatus"', source)
                self.assertIn('aria-live="polite"', source)
                self.assertIn('id="rent-buy-worksheet-script"', source)
                self.assertIn("<noscript>", source)
                self.assertNotRegex(source, re.compile(r"onclick=|calcRentVsBuy\(|\.click\(\)", re.I))
                self.assertNotRegex(source, re.compile(r"(?:Buying|Renting|Comprar|Rentar) wins|(?:verdict|veredicto)|break-even (?:typically|usually)", re.I))
                self.assertNotRegex(source, re.compile(r"Math\.pow\(1\.05|\*\s*0\.0[136]|value=[\"'](?:5|20|30|650000|3800)", re.I))

    def test_rent_buy_metadata_language_and_schema_are_reciprocal(self) -> None:
        expectations = {
            EN: ("en", "https://thejorgeramirezgroup.com/rent-vs-buy-nj"),
            ES: ("es", "https://thejorgeramirezgroup.com/es/rent-vs-buy-nj"),
        }
        for relative, (language, canonical) in expectations.items():
            source = self.pages[relative]
            with self.subTest(path=relative):
                self.assertIn(f'<html lang="{language}">', source)
                self.assertIn(f'<link rel="canonical" href="{canonical}">', source)
                for hreflang, href in (
                    ("en-US", "https://thejorgeramirezgroup.com/rent-vs-buy-nj"),
                    ("es-US", "https://thejorgeramirezgroup.com/es/rent-vs-buy-nj"),
                    ("x-default", "https://thejorgeramirezgroup.com/rent-vs-buy-nj"),
                ):
                    self.assertIn(f'hreflang="{hreflang}" href="{href}"', source)
                nodes = schemas(source)
                self.assertEqual({"WebApplication", "BreadcrumbList"}, {node.get("@type") for node in nodes})
                app = next(node for node in nodes if node.get("@type") == "WebApplication")
                self.assertEqual(canonical, app.get("url"))
                self.assertEqual(language, app.get("inLanguage"))
                self.assertEqual("2026-08-27", app.get("dateModified"))
                self.assertNotRegex(source, r'"@type"\s*:\s*"(?:FAQPage|HowTo)"')

        self.assertIn(
            '<meta property="og:description" content="A transparent worksheet with no prefilled assumptions for comparing the scenarios you enter.">',
            self.pages[EN],
        )
        self.assertNotIn("assumption-free", self.pages[EN].casefold())

    def test_rent_buy_method_exposes_formula_and_material_limits(self) -> None:
        for relative in (EN, ES):
            visible = text(self.pages[relative]).casefold()
            with self.subTest(path=relative):
                for token in ("remaining", "balance", "nominal", "tax", "investment") if relative == EN else ("saldo", "nominal", "impuesto", "inversión", "supuestos"):
                    self.assertIn(token, visible)
                self.assertRegex(visible, r"(?:does not|no) (?:predict|predice)")
                self.assertRegex(visible, r"(?:not (?:financial|tax|legal) advice|no es asesoramiento)")

        self.assertIn(
            "The model compounds only the user-entered day-one alternative investment; it does not automatically invest monthly rent-versus-purchase cost differences, and it does not model investment taxes or fees.",
            text(self.pages[EN]),
        )
        self.assertIn(
            "El modelo capitaliza únicamente la inversión alternativa inicial que ingresas; no invierte automáticamente las diferencias mensuales entre los costos de renta y compra, ni modela impuestos o comisiones de inversión.",
            text(self.pages[ES]),
        )

    def test_commute_page_is_a_blank_source_led_method_not_a_fare_table(self) -> None:
        source = self.pages[COMMUTE]
        visible = text(source)
        parser = InputParser()
        parser.feed(source)
        for input_id in (
            "transitDays", "transitFarePerDay", "stationParkingPerDay",
            "destinationTransitPerDay", "otherTransitMonthly", "drivingDays",
            "tollsPerDay", "drivingParkingPerDay", "fuelPerDay",
            "otherDrivingMonthly", "annualFees", "transitRoundTripMinutes",
            "drivingRoundTripMinutes",
        ):
            self.assertIn(input_id, parser.inputs)
            self.assertNotIn("value", parser.inputs[input_id])
        for url in (NJ_TRANSIT, PATH, PORT_AUTHORITY_TOLLS, CONGESTION, SUMMIT_PARKING):
            self.assertIn(f'href="{url}"', source)
        self.assertIn('id="commute-cost-worksheet-script"', source)
        self.assertIn('id="commuteForm"', source)
        self.assertIn('aria-live="polite"', source)
        self.assertIn("Sources checked August 27, 2026", visible)
        self.assertNotRegex(visible, re.compile(r"\$\s*\d|mortgage (?:interest|equivalent)|afford more house|home price (?:break|savings)|typical(?:ly)? .*commut", re.I))
        self.assertNotRegex(source, r'"@type"\s*:\s*"FAQPage"')

    def test_cash_planning_guide_uses_documents_not_universal_estimates(self) -> None:
        source = self.pages[CASH]
        visible = text(source)
        for url in (CFPB_LOAN_ESTIMATE, CFPB_CLOSING, NJDOBI_BUYING, NJHMFA_HOME):
            self.assertIn(f'href="{url}"', source)
        for category in ("Down payment", "Estimated Cash to Close", "Reserves", "Inspection"):
            self.assertIn(category, visible)
        self.assertIn("Sources checked August 27, 2026", visible)
        self.assertNotRegex(visible, re.compile(r"attorney.{0,50}\$|inspection.{0,50}\$|closing costs?.{0,30}\d\s*[-–%]|minimum credit score|waiting costs more|overpay", re.I))
        self.assertNotRegex(source, r'"@type"\s*:\s*"FAQPage"')

    def test_program_guide_matches_current_dated_njhmfa_material(self) -> None:
        source = self.pages[PROGRAMS]
        visible = text(source)
        for url in (NJHMFA_HOME, NJHMFA_2026_FACT):
            self.assertIn(f'href="{url}"', source)
        for phrase in ("$15,000", "$10,000", "$7,000", "$17,000 to $22,000"):
            self.assertIn(phrase, visible)
        self.assertIn("effective June 17, 2026", visible)
        self.assertIn("Sources checked August 27, 2026", visible)
        self.assertRegex(visible, r"(?i)participating lender.{0,180}(?:verify|confirm)")
        self.assertRegex(visible, r"(?i)(?:income|purchase-price) limits")
        self.assertNotRegex(visible, re.compile(r"(?:credit|FICO) score.{0,30}\b(?:500|580|620|640|740)\b|pre-approval is essential|avoid overpaying|minimum credit score", re.I))
        nodes = schemas(source)
        self.assertEqual({"BlogPosting", "BreadcrumbList"}, {node.get("@type") for node in nodes})
        article = next(node for node in nodes if node.get("@type") == "BlogPosting")
        self.assertEqual("2026-08-27", article.get("dateModified"))

    def test_all_three_articles_keep_canonical_dates_and_article_schema(self) -> None:
        published = {COMMUTE: "2026-06-27", CASH: "2026-07-30", PROGRAMS: "2026-04-30"}
        for relative, date_published in published.items():
            route = relative[:-5]
            source = self.pages[relative]
            with self.subTest(path=relative):
                self.assertIn(f'<link rel="canonical" href="https://thejorgeramirezgroup.com/{route}">', source)
                self.assertIn('<meta property="article:modified_time" content="2026-08-27">', source)
                nodes = schemas(source)
                self.assertEqual({"BlogPosting", "BreadcrumbList"}, {node.get("@type") for node in nodes})
                article = next(node for node in nodes if node.get("@type") == "BlogPosting")
                self.assertEqual(date_published, article.get("datePublished"))
                self.assertEqual("2026-08-27", article.get("dateModified"))
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertEqual(1, len(re.findall(r"<main\b", source, re.I)))


if __name__ == "__main__":
    unittest.main()
