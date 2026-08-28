#!/usr/bin/env python3
"""Regression coverage for the bilingual, fair-housing-safe town comparison."""

from __future__ import annotations

import html
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ACCESSED = "2026-08-26"
PAGE_MODIFIED = "2026-08-27"
EN_URL = "https://thejorgeramirezgroup.com/blog/best-nj-towns-for-families-2026"
ES_URL = "https://thejorgeramirezgroup.com/es/blog/best-nj-towns-for-families"
TOWN_KEYS = {
    "basking-ridge-bernards-township",
    "bernardsville",
    "chatham-borough-and-township",
    "cranford",
    "glen-ridge",
    "madison",
    "maplewood",
    "millburn-short-hills",
    "ridgewood",
    "south-orange",
    "summit",
    "westfield",
}
REQUIRED_CATEGORIES = {
    "municipality",
    "census",
    "school-district",
    "njdoe",
    "transit",
    "property",
}
OFFICIAL_HOSTS = {
    "www.bernards.org",
    "www.bernardsboe.com",
    "www.bernardsville.gov",
    "www.chathamborough.org",
    "chathamtownship.org",
    "www.chatham-nj.org",
    "www.cityofsummit.org",
    "www.cranfordnj.org",
    "www.cranfordschools.org",
    "www.glenridgenj.org",
    "www.glenridge.org",
    "www.hud.gov",
    "www.madisonpublicschools.org",
    "www.maplewoodnj.gov",
    "www.millburn.org",
    "www.nj.gov",
    "nj.gov",
    "www.njoag.gov",
    "www.njtransit.com",
    "content.njtransit.com",
    "www.ridgewoodnj.net",
    "www.rosenet.org",
    "www.rpsnj.us",
    "www.shsd.org",
    "www.somsdk12.org",
    "www.southorange.org",
    "www.summit.k12.nj.us",
    "www.twp.millburn.nj.us",
    "www.westfieldnj.gov",
    "www.westfieldnjk12.org",
    "www.census.gov",
}
RISKY = re.compile(
    r"(?:"
    r"\b(?:top[- ]rated|top\s+schools?|safest|safe\s+(?:town|community)|"
    r"family[- ]friendly|great\s+for\s+families|winner|runner[- ]up|family\s+score)\b|"
    r"\b(?:mejores?\s+escuelas?|m[aá]s\s+segur[oa]s?|ganador[ae]?|"
    r"ideal\s+para\s+familias|apto\s+para\s+familias)\b|"
    r"\b(?:young\s+families|families\s+with\s+children|ni[nñ]os?)\b|"
    r"\b\d+(?:\.\d+)?\s*/\s*10\b|"
    r"\$\s?\d|"
    r"\b\d+\s*(?:minutes?|mins?|minutos?)\b|"
    r"\b(?:crime|crimen|delincuencia)\s+rate\b"
    r")",
    re.IGNORECASE,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", " ", source, flags=re.I | re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def without_legacy_note(source: str) -> str:
    return re.sub(
        r'<aside\b[^>]*class=["\'][^"\']*legacy-query-note[^"\']*["\'][^>]*>.*?</aside>',
        " ",
        source,
        flags=re.I | re.S,
    )


def json_ld(source: str) -> list[object]:
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


class FairHousingTownComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(read("data/nj-town-comparison-sources.json"))
        cls.en = read("blog/best-nj-towns-for-families-2026.html")
        cls.es = read("es/blog/best-nj-towns-for-families.html")
        cls.alias = read("blog/best-nj-towns-for-families.html")

    def test_manifest_has_consistent_current_official_sources_for_every_town(self) -> None:
        self.assertEqual(ACCESSED, self.manifest["accessed"])
        self.assertEqual(TOWN_KEYS, set(self.manifest["towns"]))
        self.assertGreaterEqual(len(self.manifest["guidance"]), 2)

        all_sources = [*self.manifest["guidance"], *self.manifest["shared_sources"]]
        for key, town in self.manifest["towns"].items():
            with self.subTest(town=key):
                self.assertEqual(ACCESSED, town["accessed"])
                self.assertTrue(REQUIRED_CATEGORIES <= {item["category"] for item in town["sources"]})
                all_sources.extend(town["sources"])

        for source in all_sources:
            with self.subTest(url=source["url"]):
                self.assertEqual(
                    {"category", "publisher", "url", "fact_supported", "accessed"},
                    set(source),
                )
                self.assertEqual(ACCESSED, source["accessed"])
                self.assertIn(urlparse(source["url"]).netloc, OFFICIAL_HOSTS)
                self.assertGreaterEqual(len(source["fact_supported"]), 24)

    def test_every_manifest_source_is_a_visible_link_in_both_languages(self) -> None:
        urls = {
            item["url"]
            for item in [*self.manifest["guidance"], *self.manifest["shared_sources"]]
        }
        for town in self.manifest["towns"].values():
            urls.update(item["url"] for item in town["sources"])

        for language, source in (("en", self.en), ("es", self.es)):
            hrefs = set(re.findall(r'<a\b[^>]*href=["\']([^"\']+)', source, re.I))
            with self.subTest(language=language):
                self.assertEqual(set(), urls - hrefs)

    def test_indexable_pages_have_one_reciprocal_canonical_language_cluster(self) -> None:
        expected = ((self.en, EN_URL), (self.es, ES_URL))
        for source, canonical in expected:
            with self.subTest(canonical=canonical):
                self.assertRegex(source, r'<meta\s+name="robots"\s+content="index, follow')
                self.assertNotRegex(source, r'<meta\s+name="robots"[^>]*noindex')
                self.assertEqual(1, len(re.findall(r'<link\s+rel="canonical"', source)))
                self.assertIn(f'<link rel="canonical" href="{canonical}">', source)
                self.assertIn(f'<link rel="alternate" hreflang="en-US" href="{EN_URL}">', source)
                self.assertIn(f'<link rel="alternate" hreflang="es-US" href="{ES_URL}">', source)
                self.assertIn(f'<link rel="alternate" hreflang="es" href="{ES_URL}">', source)
                self.assertIn(f'<link rel="alternate" hreflang="x-default" href="{EN_URL}">', source)

    def test_legacy_alias_is_a_noindex_one_hop_fallback_for_server_redirect(self) -> None:
        self.assertRegex(self.alias, r'<meta\s+name="robots"\s+content="noindex, follow">')
        self.assertEqual(1, len(re.findall(r'<link\s+rel="canonical"', self.alias)))
        self.assertIn(f'<link rel="canonical" href="{EN_URL}">', self.alias)
        self.assertRegex(self.alias, r'http-equiv="refresh"\s+content="0;\s*url=/blog/best-nj-towns-for-families-2026"')
        self.assertIn("window.location.replace('/blog/best-nj-towns-for-families-2026')", self.alias)
        self.assertIn('href="/blog/best-nj-towns-for-families-2026"', self.alias)

        redirects = json.loads(read("vercel.json"))["redirects"]
        exact = [item for item in redirects if item.get("source") == "/blog/best-nj-towns-for-families"]
        self.assertEqual(
            [{"source": "/blog/best-nj-towns-for-families", "destination": "/blog/best-nj-towns-for-families-2026", "permanent": True}],
            exact,
        )

    def test_pages_explain_legacy_intent_without_repeating_targeting_queries(self) -> None:
        for language, source, phrase, neutral_marker in (
            ("en", self.en, "best NJ towns for families", "objective information"),
            ("es", self.es, "mejores pueblos de NJ para familias", "información objetiva"),
        ):
            note = re.search(
                r'<aside\b[^>]*class=["\'][^"\']*legacy-query-note[^"\']*["\'][^>]*>(.*?)</aside>',
                source,
                re.I | re.S,
            )
            with self.subTest(language=language):
                self.assertIsNotNone(note)
                self.assertIn(neutral_marker.casefold(), visible_text(note.group(1)).casefold())
                self.assertNotIn(phrase.casefold(), visible_text(source).casefold())

    def test_visible_copy_and_metadata_avoid_steering_rankings_and_invented_numbers(self) -> None:
        failures: list[str] = []
        for language, source in (("en", self.en), ("es", self.es)):
            candidate = visible_text(without_legacy_note(source))
            candidate += " " + " ".join(
                re.findall(r'<meta\b[^>]*content=["\']([^"\']*)', source, re.I)
            )
            matches = sorted({match.group(0) for match in RISKY.finditer(candidate)})
            if matches:
                failures.append(f"{language}: {', '.join(matches)}")
            if re.search(r'\b(?:ranked|ranking|clasificad[oa]s?)\s+(?:towns?|pueblos?)\b', candidate, re.I):
                failures.append(f"{language}: ranking language")
        self.assertEqual([], failures)

    def test_schema_is_parseable_neutral_and_has_no_scoring_types(self) -> None:
        forbidden = {"ItemList", "Review", "AggregateRating", "Rating"}
        for language, source, canonical in (("en", self.en, EN_URL), ("es", self.es, ES_URL)):
            blocks = json_ld(source)
            nodes = [node for block in blocks for node in schema_nodes(block)]
            types = {node.get("@type") for node in nodes}
            with self.subTest(language=language):
                self.assertTrue(blocks)
                self.assertIn("Article", types)
                self.assertIn("BreadcrumbList", types)
                self.assertFalse(types & forbidden)
                article = next(node for node in nodes if node.get("@type") == "Article")
                self.assertEqual(canonical, article["mainEntityOfPage"])
                self.assertEqual(PAGE_MODIFIED, article["dateModified"])

    def test_objective_framework_and_municipal_distinctions_are_explicit(self) -> None:
        for source in (self.en, self.es):
            for section_id in (
                "fair-housing-note",
                "comparison-framework",
                "town-source-cards",
                "decision-checklist",
            ):
                self.assertIn(f'id="{section_id}"', source)

        english = visible_text(self.en)
        for fact in (
            "Chatham Borough and Chatham Township are separate municipalities",
            "Short Hills is a community within Millburn Township",
            "Basking Ridge is a community within Bernards Township",
            "South Orange–Maplewood School District serves both South Orange and Maplewood",
        ):
            self.assertIn(fact, english)

    def test_brand_accessibility_and_responsive_contract(self) -> None:
        css = read("css/fair-housing-town-comparison.css")
        for token in ("#0A0A0A", "#C41230", "#8B0D22", "#B8962E", "#FAFAF8"):
            self.assertIn(token, css)
        for family in ("Playfair Display", "Inter"):
            self.assertIn(family, css)
        self.assertRegex(css, r"@media\s*\(max-width:\s*700px\)")
        self.assertRegex(css, r"overflow-wrap:\s*anywhere")
        self.assertRegex(css, r"\.official-links a\s*\{[^}]*min-height:\s*44px", re.S)

        for language, source in (("en", self.en), ("es", self.es)):
            with self.subTest(language=language):
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertIn('<a class="skip-link" href="#main">', source)
                self.assertIn('<main id="main">', source)
                self.assertIn('aria-label="Primary navigation"', source)
                self.assertIn('/css/styles.css', source)
                self.assertIn('/css/fair-housing-town-comparison.css', source)
                self.assertIn('<footer', source)


if __name__ == "__main__":
    unittest.main()
