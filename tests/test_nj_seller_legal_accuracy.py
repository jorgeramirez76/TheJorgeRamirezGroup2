#!/usr/bin/env python3
"""Fail-closed contracts for the source-led NJ seller legal guides."""

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

PAGES = {
    "blog/selling-a-house-as-executor-nj.html": {
        "route": "/blog/selling-a-house-as-executor-nj",
        "lead_paths": (
            "/blog/selling-inherited-home-nj",
            "/home-valuation",
            "tel:+19082307844",
        ),
    },
    "blog/documents-to-sell-inherited-property-nj.html": {
        "route": "/blog/documents-to-sell-inherited-property-nj",
        "lead_paths": (
            "/blog/selling-inherited-home-nj",
            "/home-valuation",
            "tel:+19082307844",
        ),
    },
    "blog/nj-seller-disclosure-requirements.html": {
        "route": "/blog/nj-seller-disclosure-requirements",
        "lead_paths": (
            "/nj-home-seller-guide",
            "/sell-your-home",
            "tel:+19082307844",
        ),
    },
    "blog/selling-a-house-as-is-in-nj.html": {
        "route": "/blog/selling-a-house-as-is-in-nj",
        "lead_paths": (
            "/home-valuation",
            "/sell-your-home",
            "tel:+19082307844",
        ),
    },
}

EXPECTED_SNIPPETS = {
    "blog/nj-seller-disclosure-requirements.html": (
        "Is a Seller's Disclosure Required in NJ? What You Must Tell Buyers",
        "Review New Jersey seller-disclosure duties, known material defects, "
        "oil-tank questions and the role of legal advice in a home sale.",
    ),
    "blog/selling-a-house-as-is-in-nj.html": (
        "Selling a House As-Is in NJ: What It Does and Does Not Mean",
        "Learn what an as-is sale does and does not change in New Jersey, "
        "including repairs, disclosures, inspections and buyer options.",
    ),
}

TAX_WAIVER = (
    "https://www.nj.gov/treasury/taxation/inheritance-estate/estatetax.shtml"
)
TAX_FILING = (
    "https://www.nj.gov/treasury/taxation/inheritance-estate/"
    "inheritance-taxfilerequirements.shtml"
)
FORM_L9 = (
    "https://www.nj.gov/treasury/taxation/pdf/other_forms/inheritance/itl9.pdf"
)
COURT_RULE = (
    "https://www.njcourts.gov/attorneys/rules-of-court/"
    "application-surrogates-court-probate-or-administration"
)
COURT_DIRECTORY = "https://www.njcourts.gov/public/directories"
FIDUCIARY_STATUTE = "https://pub.njleg.gov/bills/2002/PL03/33_.HTM"
PCDS_STATUTE = "https://pub.njleg.gov/Bills/2024/PL24/32_.HTM"
NJDOBI_BULLETIN = "https://www.nj.gov/dobi/bulletins/blt24_11.pdf"
PCDS_FORM = (
    "https://www.njconsumeraffairs.gov/Documents/"
    "Sellers-Property-Condition-Disclosure-Statement.pdf"
)
PCDS_INSTRUCTIONS = (
    "https://www.njconsumeraffairs.gov/ocp/Documents/"
    "Sellers-Property-Condition-Disclosure-Statement-Instruction-Sheet-August-2024.pdf"
)
NJDOBI_BUYING_GUIDE = (
    "https://www.nj.gov/dobi/division_consumers/pdf/buyingahome.pdf"
)
DCA_FIRE_GUIDANCE = (
    "https://www.nj.gov/dca/news/news/2023/approved/20230310.shtml"
)

FORBIDDEN = re.compile(
    r"(?:"
    r"real estate transfers? always require(?:s)? (?:the )?form 0-1|"
    r"every (?:estate|executor|inherited-property) sale[^.]{0,90}form 0-1|"
    r"estate (?:also )?(?:needs|must obtain) (?:a )?form 0-1|"
    r"form 0-1[^.]{0,60}(?:always|required in every)|"
    r"appointment[^.]{0,120}lets you sign (?:the )?listing|"
    r"you can sell[^.]{0,120}once[^.]{0,80}letters|"
    r"need letters testamentary before (?:you can )?list|"
    r"(?:title company|closing attorney) (?:always|will) (?:want|require|ask)|"
    r"(?:costs?|lose|return(?:ed)?) (?:you )?(?:days|weeks|months)|"
    r"shortens? the timeline|"
    r"most estate closings|"
    r"(?:i|we) (?:have )?(?:helped|handled|sold|closed|watched)|"
    r"my clients?|our clients?|"
    r"\$\s*\d[\d,]*(?:\.\d+)?\s+repair|"
    r"repairs?[^.]{0,100}(?:roi|return on investment|net loss|saves? money)|"
    r"usually (?:costs?|gets?|sells?|nets?|does? better)|"
    r"(?:cash|investor)[ -]offer[^.]{0,100}(?:discount|better|more|less)|"
    r"financed buyer[^.]{0,100}(?:better|more|less)|"
    r"new jersey is an attorney(?:-review)? state|"
    r"in new jersey you will have (?:an )?attorney|"
    r"you (?:must|need to) (?:hire|retain|use) (?:an )?(?:estate |real estate )?attorney|"
    r"as-is does not remove the buyer(?:'s|’s) right to inspect|"
    r"buyer(?:'s|’s) realistic options narrow to|"
    r"all new jersey sellers have (?:an obligation|a duty) to disclose|"
    r"sellers? (?:must|always have to) disclose known latent|"
    r"highest-stakes (?:item|condition)|"
    r"nothing in new jersey prevents you selling a home as-is"
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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "a":
            values = {key.casefold(): value or "" for key, value in attrs}
            if values.get("target") == "_blank":
                rel = set(values.get("rel", "").casefold().split())
                if not {"noopener", "noreferrer"} <= rel:
                    self.ids.append("external-link-missing-rel")
        for key, value in attrs:
            if key.casefold() == "id" and value:
                self.ids.append(value)


class NjSellerLegalAccuracyTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {relative: read(relative) for relative in PAGES}

    def test_canonicals_metadata_schema_and_lead_paths_are_preserved(self) -> None:
        for relative, spec in PAGES.items():
            source = self.sources[relative]
            with self.subTest(path=relative):
                self.assertIn(
                    f'<link rel="canonical" href="{SITE}{spec["route"]}">', source
                )
                self.assertRegex(
                    source,
                    r'<meta\s+name="robots"\s+content="index, follow,',
                )
                self.assertIn(f'content="{REVIEWED_ON}"', source)
                for href in spec["lead_paths"]:
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
                    types & {"FAQPage", "HowTo", "Review", "AggregateRating", "Service", "Offer"}
                )
                article = next(node for node in nodes if node.get("@type") == "Article")
                self.assertEqual(SITE + spec["route"], article.get("url"))
                self.assertEqual(REVIEWED_ON, article.get("dateModified"))
                self.assertIn(article["headline"], visible_text(source))
                self.assertGreaterEqual(len(article.get("citation", [])), 3)

        for relative, (title, description) in EXPECTED_SNIPPETS.items():
            source = self.sources[relative]
            with self.subTest(snippet=relative):
                self.assertIn(f"<title>{html.escape(title, quote=False)}</title>", source)
                self.assertIn(
                    f'<meta name="description" content="{html.escape(description, quote=True)}">',
                    source,
                )

    def test_homepage_palette_accessibility_and_html_integrity(self) -> None:
        palette = ("#1A1A1A", "#2C2C2C", "#C41230", "#8B0D22", "#B8962E", "#FAFAF8", "#F8F6F2")
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
                self.assertNotIn("external-link-missing-rel", parser.ids)
                actual_ids = [value for value in parser.ids if value != "external-link-missing-rel"]
                self.assertEqual(len(actual_ids), len(set(actual_ids)))

    def test_probate_pages_explain_waiver_exceptions_and_authority_limits(self) -> None:
        probate_pages = (
            "blog/selling-a-house-as-executor-nj.html",
            "blog/documents-to-sell-inherited-property-nj.html",
        )
        required_sources = (
            TAX_WAIVER,
            TAX_FILING,
            FORM_L9,
            COURT_RULE,
            COURT_DIRECTORY,
            FIDUCIARY_STATUTE,
            PCDS_FORM,
        )
        for relative in probate_pages:
            source = self.sources[relative]
            text = visible_text(source).casefold()
            with self.subTest(path=relative):
                for url in required_sources:
                    self.assertIn(url, source)
                self.assertIn("tenancy by the entirety", text)
                self.assertIn("bona fide trust", text)
                self.assertIn("l-9 is a request for a waiver, not the waiver", text)
                self.assertIn("l-8 is for qualifying non-real-estate assets", text)
                for concept in (
                    "recorded title",
                    "governing instrument",
                    "appointment",
                    "court order",
                    "specifically disposed",
                ):
                    self.assertIn(concept, text)
                self.assertIn("general information, not legal or tax advice", text)
                self.assertIsNone(FORBIDDEN.search(text), FORBIDDEN.search(text).group(0) if FORBIDDEN.search(text) else "")
                full_source = html.unescape(source)
                self.assertIsNone(
                    FORBIDDEN.search(full_source),
                    FORBIDDEN.search(full_source).group(0)
                    if FORBIDDEN.search(full_source)
                    else "",
                )

        self.assertIn(DCA_FIRE_GUIDANCE, self.sources[probate_pages[1]])

    def test_disclosure_and_as_is_pages_use_current_forms_without_outcome_claims(self) -> None:
        pages = (
            "blog/nj-seller-disclosure-requirements.html",
            "blog/selling-a-house-as-is-in-nj.html",
        )
        for relative in pages:
            source = self.sources[relative]
            text = visible_text(source).casefold()
            with self.subTest(path=relative):
                for url in (
                    PCDS_STATUTE,
                    NJDOBI_BULLETIN,
                    PCDS_FORM,
                    PCDS_INSTRUCTIONS,
                    NJDOBI_BUYING_GUIDE,
                ):
                    self.assertIn(url, source)
                self.assertIn("effective april 20, 2026", text)
                self.assertIn("to the best of the seller's knowledge", text)
                self.assertIn("executor, administrator or trustee", text)
                self.assertIn("not a warranty", text)
                self.assertIn("not a substitute for an inspection", text)
                self.assertIn("general information, not legal advice", text)
                self.assertIsNone(FORBIDDEN.search(text), FORBIDDEN.search(text).group(0) if FORBIDDEN.search(text) else "")
                full_source = html.unescape(source)
                self.assertIsNone(
                    FORBIDDEN.search(full_source),
                    FORBIDDEN.search(full_source).group(0)
                    if FORBIDDEN.search(full_source)
                    else "",
                )

        as_is = visible_text(
            self.sources["blog/selling-a-house-as-is-in-nj.html"]
        ).casefold()
        for concept in (
            "does not, by itself, decide disclosure duties",
            "does not, by itself, create or remove an inspection contingency",
            "written contract controls",
            "property-specific bids",
        ):
            self.assertIn(concept, as_is)


if __name__ == "__main__":
    unittest.main()
