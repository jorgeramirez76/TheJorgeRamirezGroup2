#!/usr/bin/env python3
"""Fail-closed contracts for NJ tax-record and buyer due-diligence guides."""

from __future__ import annotations

import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-27"

TAX_PAGES = {
    "blog/nj-property-taxes-lowest-commuter-towns-2026.html": {
        "route": "/blog/nj-property-taxes-lowest-commuter-towns-2026",
        "lead_paths": ("/buy-a-home", "/home-valuation", "/#contact"),
    },
    "blog/most-affordable-nj-towns-near-nyc-2026.html": {
        "route": "/blog/most-affordable-nj-towns-near-nyc-2026",
        "lead_paths": (
            "/nj-home-buyer-guide",
            "/home-valuation",
            "/towns/roselle-park",
            "/#contact",
        ),
        "context_paths": (
            "/blog/moving-from-jersey-city-hoboken-to-suburbs",
            "/blog/moving-to-nj-checklist",
            "/blog/nj-property-tax-rate-vs-what-you-actually-pay",
        ),
    },
}

BUYER_PAGES = {
    "blog/buying-a-home-in-new-jersey-2026.html": {
        "route": "/blog/buying-a-home-in-new-jersey-2026",
        "lead_paths": (
            "/buy-a-home",
            "/contact",
            "/nj-home-buyer-guide",
            "/buyer-agency-agreement-nj",
            "/closing-costs-calculator",
            "/communities",
        ),
    },
    "blog/nj-buyer-agency-inspection-offer-guide-2026.html": {
        "route": "/blog/nj-buyer-agency-inspection-offer-guide-2026",
        "lead_paths": (
            "/buy-a-home",
            "/contact",
            "/nj-home-buyer-guide",
            "/buyer-agency-agreement-nj",
            "/closing-costs-calculator",
            "/blog/nj-attorney-review-real-estate",
        ),
    },
}

PAGES = TAX_PAGES | BUYER_PAGES

TAX_STATS = "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml"
TAX_2025 = (
    "https://www.nj.gov/treasury/taxation/pdf/lpt/class4/2025AvgResStat.pdf"
)
TAX_2026 = (
    "https://www.nj.gov/treasury/taxation/pdf/lpt/class4/2026AvgResStat.pdf"
)
TAX_APPEAL = "https://www.nj.gov/treasury/taxation/lpt/lpt-appeal.shtml"
TAX_RIGHTS = "https://www.nj.gov/treasury/taxation/lpt/lpt-tpbors.shtml"
NJ_TRANSIT = "https://www.njtransit.com/schedules-and-fares"

NJDOBI_BULLETIN = "https://www.nj.gov/dobi/bulletins/blt24_11.pdf"
NJDOBI_GUIDE = "https://www.nj.gov/dobi/division_consumers/pdf/buyingahome.pdf"
BROKERAGE_LAW = "https://pub.njleg.gov/Bills/2024/PL24/32_.HTM"
CFPB_LOAN_ESTIMATE = "https://www.consumerfinance.gov/owning-a-home/loan-estimate/"
CFPB_CLOSING_DISCLOSURE = (
    "https://www.consumerfinance.gov/owning-a-home/closing-disclosure/"
)
CFPB_COMPARE = "https://www.consumerfinance.gov/owning-a-home/compare/"
PCDS_FORM = (
    "https://www.njconsumeraffairs.gov/Documents/"
    "Sellers-Property-Condition-Disclosure-Statement.pdf"
)
NJDEP_FLOOD = "https://dep.nj.gov/flooddisclosure/"
NJDEP_FLOOD_TOOL = "https://dep.nj.gov/climatechange/flood-tool/"
HOME_INSPECTOR_FAQ = "https://www.njconsumeraffairs.gov/hom/Pages/FAQ.aspx"
LICENSE_LOOKUP = "https://www.njconsumeraffairs.gov/Pages/verification.aspx"

TAX_STALE = re.compile(
    r"(?:"
    r"the cheapest|cheapest places|lowest-tax|lowest property taxes?|"
    r"(?:towns?|places?)\s*,?\s*ranked|ranking the towns|best towns?|"
    r"premium neighbors?|solid schools?|good town|top schools?|"
    r"family-friendly|young(?:er)? buyers?|twenties|thirties|"
    r"(?:safe|safety|crime) ranking|one-seat ride|workable commute|"
    r"reasonable commute|entry point left|more efficient budget|"
    r"i live in roselle park|i(?:'|’)ve watched|my own purchase|"
    r"2\.23%|67\.7%|\$3,000|\$4,900|\$21,000|"
    r"rahway has the lowest|redfin[^.]{0,80}median"
    r")",
    re.I,
)

BUYER_STALE = re.compile(
    r"(?:"
    r"winning without panic|buyers? (?:who are )?winning|win (?:a|the) house|"
    r"beat a (?:slightly )?higher|stronger offer|certainty matters|"
    r"best homes|move quickly|move fast|before touring homes|before you tour|"
    r"must sign[^.]{0,80}before touring|"
    r"attorney (?:selected|ready) before|major protection|"
    r"attorney is required|new jersey is an attorney state|"
    r"waive (?:the )?(?:inspection|protections?)|inspection cap|"
    r"inspection credit|appraisal gap|desired school|competitive towns?|"
    r"town-by-town competition|easy to trust|giving away protections|"
    r"\$725,?000|\$675,?000|45 days|appreciat(?:e|ion)"
    r")",
    re.I,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style|template|noscript)\b[^>]*>.*?"
        r"</(?:script|style|template|noscript)>",
        " ",
        source,
        flags=re.I | re.S,
    )
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


class IntegrityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.external_rel_errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.casefold(): value or "" for key, value in attrs}
        if tag.casefold() == "a" and values.get("target") == "_blank":
            rel = set(values.get("rel", "").casefold().split())
            if not {"noopener", "noreferrer"} <= rel:
                self.external_rel_errors.append(values.get("href", ""))
        if values.get("id"):
            self.ids.append(values["id"])


class NjBuyerTaxSourceAccuracyTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {relative: read(relative) for relative in PAGES}

    def test_indexability_canonicals_schema_and_lead_paths(self) -> None:
        for relative, spec in PAGES.items():
            source = self.sources[relative]
            text = visible_text(source)
            with self.subTest(path=relative):
                self.assertIn(
                    f'<link rel="canonical" href="{SITE}{spec["route"]}">', source
                )
                self.assertRegex(source, r'<meta\s+name="robots"\s+content="index, follow,')
                self.assertIn(f'<meta name="last-updated" content="{REVIEWED_ON}">', source)
                for href in spec["lead_paths"]:
                    self.assertIn(f'href="{href}"', source)
                for href in spec.get("context_paths", ()):
                    self.assertIn(f'href="{href}"', source)

                blocks = [
                    json.loads(block)
                    for block in re.findall(
                        r'<script\b[^>]*type="application/ld\+json"[^>]*>'
                        r"(.*?)</script>",
                        source,
                        flags=re.I | re.S,
                    )
                ]
                nodes = [node for block in blocks for node in schema_nodes(block)]
                types = {node.get("@type") for node in nodes}
                self.assertTrue(
                    {"Organization", "Person", "WebPage", "Article", "BreadcrumbList"}
                    <= types
                )
                self.assertFalse(
                    types
                    & {
                        "FAQPage",
                        "HowTo",
                        "Review",
                        "AggregateRating",
                        "Service",
                        "Offer",
                        "ItemList",
                    }
                )
                article = next(node for node in nodes if node.get("@type") == "Article")
                self.assertEqual(SITE + spec["route"], article.get("url"))
                self.assertEqual(REVIEWED_ON, article.get("dateModified"))
                self.assertIn(article["headline"], text)
                self.assertGreaterEqual(len(article.get("citation", [])), 5)

    def test_homepage_palette_accessibility_and_html_integrity(self) -> None:
        palette = (
            "#1A1A1A",
            "#2C2C2C",
            "#C41230",
            "#8B0D22",
            "#B8962E",
            "#FAFAF8",
            "#F8F6F2",
        )
        for relative, source in self.sources.items():
            parser = IntegrityParser()
            parser.feed(source)
            with self.subTest(path=relative):
                for token in palette:
                    self.assertIn(token, source)
                for family in ("Playfair Display", "Inter"):
                    self.assertIn(family, source)
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertEqual(1, len(re.findall(r'<main\b[^>]*id="main"', source, re.I)))
                self.assertIn('href="#main"', source)
                self.assertIn('tabindex="-1"', source)
                self.assertIn(":focus-visible", source)
                self.assertIn("min-height:44px", source.replace(" ", ""))
                self.assertFalse(parser.external_rel_errors)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))

    def test_tax_pages_use_complete_official_statistics_without_rankings(self) -> None:
        required_sources = (
            TAX_STATS,
            TAX_2025,
            TAX_2026,
            TAX_APPEAL,
            TAX_RIGHTS,
            NJ_TRANSIT,
        )
        expected_rows = {
            "Garwood": ("$11,725", "14", "$703,055.57"),
            "Linden": ("$9,832", "327", "$556,332.91"),
            "Rahway": ("$10,435", "120", "$497,987.50"),
            "Roselle": ("$11,229", "187", "$482,843.58"),
            "Roselle Park": ("$11,417", "101", "$516,054.47"),
            "Union": ("$10,849", "390", "$560,510.13"),
        }
        for relative in TAX_PAGES:
            source = self.sources[relative]
            text = visible_text(source)
            lowered = text.casefold()
            with self.subTest(path=relative):
                for url in required_sources:
                    self.assertIn(url, source)
                for phrase in (
                    "latest complete statewide table available as of August 27, 2026",
                    "2025 Average Residential Statistics",
                    "average, not a median",
                    "not current listings",
                    "not a parcel-specific tax bill",
                    "Effective Tax Rate is a statistical comparison",
                    "not use it to calculate a property tax bill",
                    "verify the current parcel",
                ):
                    self.assertIn(phrase.casefold(), lowered)
                for town, values in expected_rows.items():
                    self.assertIn(town, text)
                    for value in values:
                        self.assertIn(value, text)
                table_body = visible_text(
                    re.search(r"<tbody>(.*?)</tbody>", source, re.I | re.S).group(1)
                )
                town_positions = [table_body.index(town) for town in expected_rows]
                self.assertEqual(town_positions, sorted(town_positions))
                title = re.search(r"<title>(.*?)</title>", source, re.I | re.S).group(1)
                description = re.search(
                    r'<meta name="description" content="([^"]+)"', source, re.I
                ).group(1)
                self.assertNotRegex(html.unescape(title + " " + description), TAX_STALE)
                self.assertNotRegex(text, TAX_STALE)

    def test_buyer_pages_state_current_agency_contract_and_cost_boundaries(self) -> None:
        required_sources = (
            NJDOBI_BULLETIN,
            NJDOBI_GUIDE,
            BROKERAGE_LAW,
            CFPB_LOAN_ESTIMATE,
            CFPB_CLOSING_DISCLOSURE,
            CFPB_COMPARE,
            PCDS_FORM,
            NJDEP_FLOOD,
            NJDEP_FLOOD_TOOL,
            HOME_INSPECTOR_FAQ,
            LICENSE_LOOKUP,
        )
        for relative in BUYER_PAGES:
            source = self.sources[relative]
            text = visible_text(source)
            lowered = text.casefold()
            with self.subTest(path=relative):
                for url in required_sources:
                    self.assertIn(url, source)
                for phrase in (
                    "before, or as soon as reasonably practical after",
                    "fully negotiable and not set by law",
                    "an attorney is not a requirement",
                    "If a contract of sale is prepared by a real estate licensee",
                    "the written contract controls",
                    "Loan Estimate",
                    "Closing Disclosure",
                    "does not calculate actual risk",
                    "general information, not legal, financial or tax advice",
                ):
                    self.assertIn(phrase.casefold(), lowered)
                self.assertNotRegex(text, BUYER_STALE)
                self.assertNotRegex(text, r"\$\s*\d")
                self.assertNotRegex(text, r"\b\d+(?:\.\d+)?\s*%")

    def test_every_page_labels_method_scope_and_review_date(self) -> None:
        for relative, source in self.sources.items():
            text = visible_text(source).casefold()
            with self.subTest(path=relative):
                self.assertIn("sources checked august 27, 2026", text)
                self.assertIn("property-specific", text)
                self.assertIn("no outcome is promised", text)
                self.assertNotIn("human-authored content", text)


if __name__ == "__main__":
    unittest.main()
