#!/usr/bin/env python3
"""Focused safeguards for the bilingual New Jersey property-tax guide."""

from __future__ import annotations

import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "property-tax-guide-sources.json"
PAGES = {
    "blog/nj-property-tax-guide.html": {
        "lang": "en",
        "canonical": "https://thejorgeramirezgroup.com/blog/nj-property-tax-guide",
        "contact": "/contact",
        "required": (
            "assessed value",
            "general tax rate",
            "property-specific tax bill",
            "only the assessment—not the amount of tax—can be appealed",
            "educational information, not tax or legal advice",
            "verify the deadline directly with the county board",
        ),
    },
    "es/blog/nj-property-tax-guide.html": {
        "lang": "es",
        "canonical": "https://thejorgeramirezgroup.com/es/blog/nj-property-tax-guide",
        "contact": "/es/#contact",
        "required": (
            "valor tasado",
            "tasa general",
            "factura específica de la propiedad",
            "solo se puede apelar la tasación, no el monto del impuesto",
            "información educativa, no asesoría tributaria ni legal",
            "confirma la fecha límite directamente con la junta tributaria",
        ),
    },
}
CANONICALS = {item["canonical"] for item in PAGES.values()}
ALLOWED_OFFICIAL_HOSTS = {"nj.gov", "www.nj.gov"}

PROHIBITED = re.compile(
    r"(?:"
    r"highest property taxes|lowest property taxes|average property tax bill|"
    r"2025 bills and rates|save (?:you )?thousands|guaranteed savings|"
    r"most expensive tax towns|cheapest tax towns|"
    r"impuestos (?:más altos|más bajos)|factura promedio de impuestos|"
    r"ahorr(?:a|ar) miles|ahorros garantizados|municipios más caros|"
    r"\b138\s+(?:communities|comunidades)\b|"
    r"top[- ]rated|mejor calificado|aggregateRating|reviewRating"
    r")",
    re.IGNORECASE,
)


class GuideParser(HTMLParser):
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
        return html.unescape(" ".join(self.visible_parts))


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def parsed(relative: str) -> GuideParser:
    parser = GuideParser()
    parser.feed(source(relative))
    return parser


def schema_nodes(parser: GuideParser) -> list[dict]:
    nodes: list[dict] = []
    for raw in parser.json_scripts:
        item = json.loads(raw)
        values = item.get("@graph", [item]) if isinstance(item, dict) else item
        if not isinstance(values, list):
            values = [values]
        nodes.extend(value for value in values if isinstance(value, dict))
    return nodes


class PropertyTaxGuideTests(unittest.TestCase):
    def test_official_source_manifest_is_traceable_and_visible(self) -> None:
        self.assertTrue(MANIFEST.exists(), "official-source manifest is missing")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("2026-08-26", manifest["reviewed"])
        self.assertEqual(set(PAGES), set(manifest["pages"]))
        for relative in PAGES:
            with self.subTest(relative=relative):
                records = manifest["pages"][relative]
                self.assertGreaterEqual(len(records), 9)
                hrefs = {item.get("href", "") for item in parsed(relative).attrs("a")}
                for record in records:
                    self.assertEqual(
                        {"url", "publisher", "fact_supported", "accessed"},
                        set(record),
                    )
                    self.assertIn(urlsplit(record["url"]).netloc, ALLOWED_OFFICIAL_HOSTS)
                    self.assertEqual("2026-08-26", record["accessed"])
                    self.assertTrue(record["publisher"].strip())
                    self.assertTrue(record["fact_supported"].strip())
                    self.assertIn(record["url"], hrefs)

    def test_metadata_canonical_hreflang_and_schema_match_visible_content(self) -> None:
        titles: set[str] = set()
        descriptions: set[str] = set()
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                text = source(relative)
                parser = parsed(relative)
                self.assertEqual(expected["lang"], parser.attrs("html")[0].get("lang"))
                title = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
                self.assertIsNotNone(title)
                title_text = " ".join(title.group(1).split())
                self.assertGreaterEqual(len(title_text), 35)
                self.assertLessEqual(len(title_text), 65)
                self.assertNotRegex(title_text, r"\b20\d{2}\b")
                description_values = [
                    item.get("content", "")
                    for item in parser.attrs("meta")
                    if item.get("name") == "description"
                ]
                self.assertEqual(1, len(description_values))
                description = description_values[0]
                self.assertGreaterEqual(len(description), 120)
                self.assertLessEqual(len(description), 165)
                llm_context = [
                    item.get("content", "")
                    for item in parser.attrs("meta")
                    if item.get("name") == "llm-context"
                ]
                self.assertEqual(1, len(llm_context))
                self.assertRegex(llm_context[0].lower(), r"\b(?:official|oficiales)\b")
                canonicals = [
                    item.get("href")
                    for item in parser.attrs("link")
                    if item.get("rel") == "canonical"
                ]
                self.assertEqual([expected["canonical"]], canonicals)
                alternates = {
                    (item.get("hreflang"), item.get("href"))
                    for item in parser.attrs("link")
                    if item.get("rel") == "alternate"
                }
                self.assertIn(
                    ("en-US", "https://thejorgeramirezgroup.com/blog/nj-property-tax-guide"),
                    alternates,
                )
                self.assertIn(
                    ("es-US", "https://thejorgeramirezgroup.com/es/blog/nj-property-tax-guide"),
                    alternates,
                )
                self.assertIn(
                    ("x-default", "https://thejorgeramirezgroup.com/blog/nj-property-tax-guide"),
                    alternates,
                )
                nodes = schema_nodes(parser)
                types = {node.get("@type") for node in nodes}
                self.assertTrue({"BlogPosting", "BreadcrumbList", "FAQPage"}.issubset(types))
                self.assertFalse({"Review", "AggregateRating"} & types)
                self.assertNotIn("aggregateRating", " ".join(parser.json_scripts))
                blog = next(node for node in nodes if node.get("@type") == "BlogPosting")
                self.assertEqual(expected["canonical"], blog["mainEntityOfPage"])
                self.assertEqual("2026-08-26", blog["dateModified"])
                faq = next(node for node in nodes if node.get("@type") == "FAQPage")
                self.assertGreaterEqual(len(faq["mainEntity"]), 5)
                for question in faq["mainEntity"]:
                    self.assertIn(question["name"], parser.visible_text)
                    self.assertIn(
                        question["acceptedAnswer"]["text"],
                        parser.visible_text,
                    )
                titles.add(title_text)
                descriptions.add(description)
        self.assertEqual(2, len(titles))
        self.assertEqual(2, len(descriptions))

    def test_copy_is_parcel_specific_qualified_and_not_promotional(self) -> None:
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                parser = parsed(relative)
                visible = parser.visible_text.lower()
                machine_copy = " ".join(
                    item.get("content", "")
                    for item in parser.attrs("meta")
                    if item.get("name") == "description"
                    or item.get("property", "").startswith(("og:", "twitter:"))
                )
                claims = " ".join([parser.visible_text, machine_copy, *parser.json_scripts])
                match = PROHIBITED.search(claims)
                self.assertIsNone(match, match.group(0) if match else "")
                for phrase in expected["required"]:
                    self.assertIn(phrase, visible)
                self.assertRegex(
                    visible,
                    r"(?:property explorer|explorador estatal de propiedades)",
                )
                self.assertRegex(
                    visible,
                    r"(?:municipal tax collector|recaudador de impuestos municipal)",
                )
                self.assertRegex(
                    visible,
                    r"(?:county board of taxation|junta tributaria del condado)",
                )
                self.assertNotRegex(visible, r"\$\s*\d[\d,.]*")
                self.assertLess(len(source(relative).encode("utf-8")), 65000)

    def test_homepage_visual_language_and_accessibility_contract(self) -> None:
        for relative, expected in PAGES.items():
            with self.subTest(relative=relative):
                text = source(relative)
                parser = parsed(relative)
                for token in (
                    "#0A0A0A",
                    "#1A1A1A",
                    "#C41230",
                    "#B8962E",
                    "#FAFAF8",
                    "Playfair Display",
                    "Inter",
                ):
                    self.assertIn(token, text)
                self.assertIn("G-KMS6H85LB0", text)
                stylesheets = {
                    item.get("href", "")
                    for item in parser.attrs("link")
                    if item.get("rel") == "stylesheet"
                }
                self.assertIn("/css/styles.css", stylesheets)
                self.assertEqual(1, len(re.findall(r"<main(?:\s|>)", text, re.I)))
                self.assertRegex(text, r'<main\s+id=["\']main["\']')
                self.assertEqual(1, len(re.findall(r"<h1(?:\s|>)", text, re.I)))
                self.assertIn('href="#main"', text)
                self.assertRegex(text, r'<nav\b[^>]*aria-label=["\'][^"\']+["\']')
                self.assertIn("min-height: 44px", text)
                self.assertIn("@media (max-width: 680px)", text)
                self.assertIn("@media (prefers-reduced-motion: reduce)", text)
                main_ctas = [
                    item for item in parser.attrs("a") if "button" in item.get("class", "")
                ]
                self.assertGreaterEqual(len(main_ctas), 2)
                self.assertTrue(all(item.get("href", "").startswith("/") for item in main_ctas))
                hrefs = {item.get("href", "") for item in parser.attrs("a")}
                self.assertIn(expected["contact"], hrefs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
