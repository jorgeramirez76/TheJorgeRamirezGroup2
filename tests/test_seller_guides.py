#!/usr/bin/env python3
"""Regression coverage for the bilingual, source-backed NJ seller guides."""

from __future__ import annotations

import html
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ACCESSED = "2026-08-26"
PAGES = {
    "town-en": ROOT / "blog" / "best-nj-towns-to-sell-home.html",
    "town-es": ROOT / "es" / "blog" / "best-nj-towns-to-sell-home.html",
    "time-en": ROOT / "blog" / "best-time-to-sell-home-nj.html",
    "time-es": ROOT / "es" / "blog" / "best-time-to-sell-home-nj.html",
}
CANONICALS = {
    "town-en": "https://thejorgeramirezgroup.com/blog/best-nj-towns-to-sell-home",
    "town-es": "https://thejorgeramirezgroup.com/es/blog/best-nj-towns-to-sell-home",
    "time-en": "https://thejorgeramirezgroup.com/blog/best-time-to-sell-home-nj",
    "time-es": "https://thejorgeramirezgroup.com/es/blog/best-time-to-sell-home-nj",
}
LANGUAGE_PAIRS = {
    "town": (CANONICALS["town-en"], CANONICALS["town-es"]),
    "time": (CANONICALS["time-en"], CANONICALS["time-es"]),
}
OFFICIAL_HOSTS = {
    "www.njrealtor.com",
    "www.nj.gov",
    "nj.gov",
    "www.njconsumeraffairs.gov",
    "dep.nj.gov",
    "firesolutions.dca.nj.gov",
    "www.census.gov",
}
FORBIDDEN = re.compile(
    r"(?:"
    r"\b(?:guarantee(?:d|s)?|garanti(?:zado|zada|zar)|top[- ]dollar|m[aá]ximo\s+precio|"
    r"multiple\s+offers?|bidding\s+war|guerra\s+de\s+ofertas|hot\s+market|mercado\s+caliente)\b|"
    r"\b(?:top[- ]rated|best|excellent)\s+(?:schools?|district|town|towns|month|season)\b|"
    r"\b(?:mejores?|excelentes?)\s+(?:escuelas?|distritos?|pueblos?|mes(?:es)?|temporadas?)\b|"
    r"\b(?:safe(?:st)?|low[- ]crime|family[- ]friendly|young\s+families|perfect\s+for\s+families)\b|"
    r"\b(?:m[aá]s\s+segur[oa]s?|baja\s+criminalidad|ideal\s+para\s+familias|familias\s+j[oó]venes)\b|"
    r"\b(?:appreciation|apreciaci[oó]n|price\s+growth|crecimiento\s+de\s+precios)\s+(?:will|va\s+a|should|deber[ií]a)\b|"
    r"\b(?:avoid|evite)\s+(?:late\s+)?(?:November|December|January|noviembre|diciembre|enero)\b|"
    r"\b(?:commission|comisi[oó]n)\s+(?:is|es|averages?|promedia)\s*\d|"
    r"\b\d+(?:\.\d+)?\s*%\s+(?:over\s+asking|above\s+asking|sobre\s+el\s+precio)\b|"
    r"\$\s*\d[\d,.]*\s*(?:million|mill[oó]n|M)\b"
    r")",
    re.IGNORECASE,
)


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style|template|noscript)\b[^>]*>.*?</(?:script|style|template|noscript)>",
        " ",
        source,
        flags=re.I | re.S,
    )
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    source = re.sub(r"<[^>]+>", " ", source)
    return re.sub(r"\s+", " ", html.unescape(source)).strip()


def without_legacy_note(source: str) -> str:
    return re.sub(
        r'<aside\b[^>]*class=["\'][^"\']*legacy-query-note[^"\']*["\'][^>]*>.*?</aside>',
        " ",
        source,
        flags=re.I | re.S,
    )


def schema_blocks(source: str) -> list[object]:
    return [
        json.loads(block)
        for block in re.findall(
            r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            source,
            flags=re.I | re.S,
        )
    ]


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


class SellerGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {key: path.read_text(encoding="utf-8") for key, path in PAGES.items()}
        cls.manifest = json.loads(
            (ROOT / "data" / "nj-seller-guides-sources.json").read_text(encoding="utf-8")
        )

    def test_pages_keep_indexable_reciprocal_canonical_routes(self) -> None:
        for key, source in self.sources.items():
            cluster = key.split("-", 1)[0]
            en_url, es_url = LANGUAGE_PAIRS[cluster]
            with self.subTest(page=key):
                self.assertIn('content="index, follow, max-image-preview:large', source)
                self.assertEqual(1, source.count('<link rel="canonical"'))
                self.assertIn(f'<link rel="canonical" href="{CANONICALS[key]}">', source)
                self.assertIn(f'hreflang="en-US" href="{en_url}"', source)
                self.assertIn(f'hreflang="es-US" href="{es_url}"', source)
                self.assertIn(f'hreflang="es" href="{es_url}"', source)
                self.assertIn(f'hreflang="x-default" href="{en_url}"', source)

    def test_metadata_is_current_truthful_and_query_aligned(self) -> None:
        expected_phrases = {
            "town-en": "NJ seller market",
            "town-es": "mercados para vender",
            "time-en": "When to sell",
            "time-es": "Cuándo vender",
        }
        for key, source in self.sources.items():
            title = re.search(r"<title>(.*?)</title>", source, re.I | re.S)
            description = re.search(
                r'<meta\s+name="description"\s+content="([^"]+)"', source, re.I
            )
            with self.subTest(page=key):
                self.assertIsNotNone(title)
                self.assertLessEqual(len(html.unescape(title.group(1)).strip()), 62)
                self.assertIn(expected_phrases[key].casefold(), title.group(1).casefold())
                self.assertIsNotNone(description)
                self.assertGreaterEqual(len(description.group(1)), 120)
                self.assertLessEqual(len(description.group(1)), 165)
                self.assertIn('<meta property="article:modified_time" content="2026-08-26">', source)
                stamp = (
                    "Sources checked August 26, 2026"
                    if key.endswith("en")
                    else "Fuentes verificadas el 26 de agosto de 2026"
                )
                self.assertIn(stamp, source)

    def test_manifest_uses_current_primary_or_official_sources(self) -> None:
        self.assertEqual(ACCESSED, self.manifest["accessed"])
        self.assertEqual({"town-comparison", "sale-timing"}, set(self.manifest["guides"]))
        self.assertGreaterEqual(len(self.manifest["sources"]), 8)
        categories = {item["category"] for item in self.manifest["sources"]}
        self.assertTrue(
            {
                "market-data",
                "property-tax",
                "transfer-fee",
                "brokerage-law",
                "property-disclosure",
                "flood-disclosure",
                "smoke-certification",
                "census-housing",
            }
            <= categories
        )
        for item in self.manifest["sources"]:
            with self.subTest(url=item["url"]):
                self.assertEqual(
                    {"category", "publisher", "url", "fact_supported", "accessed"},
                    set(item),
                )
                self.assertEqual(ACCESSED, item["accessed"])
                self.assertIn(urlparse(item["url"]).netloc, OFFICIAL_HOSTS)
                self.assertGreaterEqual(len(item["fact_supported"]), 32)

    def test_every_manifest_source_is_visible_on_every_guide(self) -> None:
        required = {item["url"] for item in self.manifest["sources"]}
        for key, source in self.sources.items():
            hrefs = set(re.findall(r'<a\b[^>]*href=["\']([^"\']+)', source, re.I))
            with self.subTest(page=key):
                self.assertEqual(set(), required - hrefs)

    def test_copy_avoids_rankings_forecasts_guarantees_and_steering(self) -> None:
        legacy_phrases = {
            "town-en": "best NJ towns to sell a home",
            "town-es": "mejores pueblos de NJ para vender una casa",
            "time-en": "best time to sell a home in NJ",
            "time-es": "mejor momento para vender una casa en NJ",
        }
        failures: list[str] = []
        for key, source in self.sources.items():
            note = re.search(
                r'<aside\b[^>]*class=["\'][^"\']*legacy-query-note[^"\']*["\'][^>]*>(.*?)</aside>',
                source,
                re.I | re.S,
            )
            if note is None or legacy_phrases[key].casefold() not in visible_text(note.group(1)).casefold():
                failures.append(f"{key}: missing transparent legacy-query note")
            candidate = visible_text(without_legacy_note(source))
            candidate += " " + " ".join(
                re.findall(r'<meta\b[^>]*content=["\']([^"\']*)', source, re.I)
            )
            matches = sorted({match.group(0) for match in FORBIDDEN.finditer(candidate)})
            if matches:
                failures.append(f"{key}: {', '.join(matches)}")
        self.assertEqual([], failures)

    def test_pages_explain_property_specific_method_and_source_limits(self) -> None:
        for key, source in self.sources.items():
            text = visible_text(source).casefold()
            with self.subTest(page=key):
                self.assertIn('data-selection="neutral-not-ranked"', source)
                self.assertIn("property-specific" if key.endswith("en") else "específica de la propiedad", text)
                self.assertIn("municipality" if key.endswith("en") else "municipio", text)
                self.assertIn("reporting lag" if key.endswith("en") else "rezago de publicación", text)
                self.assertIn("broker compensation" if key.endswith("en") else "compensación del corredor", text)
                self.assertIn("fully negotiable" if key.endswith("en") else "totalmente negociable", text)

    def test_schema_is_parseable_factual_and_bilingual(self) -> None:
        for key, source in self.sources.items():
            nodes = [node for block in schema_blocks(source) for node in schema_nodes(block)]
            types = {node.get("@type") for node in nodes}
            article = next(node for node in nodes if node.get("@type") == "BlogPosting")
            with self.subTest(page=key):
                self.assertIn("BlogPosting", types)
                self.assertIn("BreadcrumbList", types)
                self.assertIn("FAQPage", types)
                self.assertNotIn("Review", types)
                self.assertNotIn("AggregateRating", types)
                self.assertEqual(CANONICALS[key], article["mainEntityOfPage"])
                self.assertEqual("2026-08-26", article["dateModified"])
                self.assertEqual("en-US" if key.endswith("en") else "es-US", article["inLanguage"])

    def test_homepage_visual_accessibility_and_responsive_contract(self) -> None:
        css = (ROOT / "css" / "fair-housing-town-comparison.css").read_text(encoding="utf-8")
        for token in ("#0A0A0A", "#C41230", "#8B0D22", "#B8962E", "#FAFAF8"):
            self.assertIn(token, css)
        for family in ("Playfair Display", "Inter"):
            self.assertIn(family, css)
        self.assertRegex(css, r"@media\s*\(max-width:\s*700px\)")
        self.assertRegex(css, r"min-height:\s*44px")
        self.assertRegex(css, r":focus-visible")

        for key, source in self.sources.items():
            with self.subTest(page=key):
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertEqual(1, len(re.findall(r'<main\b[^>]*id="main"', source, re.I)))
                self.assertIn('href="#main"', source)
                self.assertIn('aria-label="Primary navigation"', source)
                self.assertIn('/css/styles.css', source)
                self.assertIn('/css/fair-housing-town-comparison.css', source)
                self.assertIn(
                    '.comparison-section--dark .decision-card { color: var(--comparison-text); }',
                    source,
                )
                self.assertRegex(source, re.compile(r'<table\b[^>]*>.*?<caption\b', re.I | re.S))
                ids = re.findall(r'\bid=["\']([^"\']+)', source, re.I)
                self.assertEqual(len(ids), len(set(ids)), "duplicate HTML id")


if __name__ == "__main__":
    unittest.main()
