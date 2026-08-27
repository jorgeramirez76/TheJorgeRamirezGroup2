#!/usr/bin/env python3
"""Fail-closed checks for the final luxury, 55+, downsizing, and relocation batch."""

from __future__ import annotations

import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://thejorgeramirezgroup.com"
REVIEW_DATE = "2026-08-27"

ROUTES = {
    "luxury-homes-nj.html": "/luxury-homes-nj",
    "es/luxury-homes-nj.html": "/es/luxury-homes-nj",
    "55-plus-communities-nj.html": "/55-plus-communities-nj",
    "es/55-plus-communities-nj.html": "/es/55-plus-communities-nj",
    "downsizing-nj.html": "/downsizing-nj",
    "es/downsizing-nj.html": "/es/downsizing-nj",
    "blog/moving-from-jersey-city-hoboken-to-suburbs.html": "/blog/moving-from-jersey-city-hoboken-to-suburbs",
}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(r"<script\b[^>]*>.*?</script>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    source = re.sub(r"<[^>]+>", " ", source)
    return re.sub(r"\s+", " ", html.unescape(source)).strip()


def json_ld(source: str) -> list[object]:
    blocks = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source,
        flags=re.I | re.S,
    )
    return [json.loads(html.unescape(block).strip()) for block in blocks]


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.h1_count = 0
        self.h1_in_main = 0
        self.main_depth = 0
        self.main_count = 0
        self.metas: list[dict[str, str]] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "main":
            self.main_count += 1
            self.main_depth += 1
        elif tag == "h1":
            self.h1_count += 1
            if self.main_depth:
                self.h1_in_main += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            self.metas.append(values)
        elif tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag == "main":
            self.main_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data

    def meta(self, attribute: str, value: str) -> str:
        for item in self.metas:
            if item.get(attribute, "").lower() == value.lower():
                return item.get("content", "")
        return ""


class FinalServiceContentTests(unittest.TestCase):
    maxDiff = None

    def test_routes_keep_indexable_surface_brand_and_schema_contract(self) -> None:
        for relative, route in ROUTES.items():
            source = read(relative)
            parser = SurfaceParser()
            parser.feed(source)
            with self.subTest(page=relative):
                self.assertEqual([ORIGIN + route], parser.canonicals)
                self.assertEqual(1, parser.main_count)
                self.assertEqual(1, parser.h1_count)
                self.assertEqual(1, parser.h1_in_main, "H1 must be inside the main landmark")
                self.assertNotIn("noindex", parser.meta("name", "robots").lower())
                self.assertEqual(REVIEW_DATE, parser.meta("name", "last-updated"))
                self.assertEqual(
                    "ai-assisted, source-checked",
                    parser.meta("name", "ai-content-declaration"),
                )
                self.assertNotRegex(source, r"(?i)human[- ](?:authored|reviewed)")
                self.assertIn("Playfair Display", source)
                self.assertIn("Inter", source)
                for color in ("#1a1a1a", "#c41230", "#b8962e", "#fafaf8"):
                    self.assertIn(color, source.lower())
                self.assertGreaterEqual(len(parser.title.strip()), 10)
                self.assertLessEqual(len(parser.title.strip()), 68)
                self.assertTrue(parser.meta("name", "description"))
                self.assertTrue(json_ld(source))

    def test_english_spanish_pairs_keep_canonical_hreflang_and_topic_parity(self) -> None:
        pairs = (
            ("luxury-homes-nj.html", "es/luxury-homes-nj.html", "/luxury-homes-nj"),
            ("55-plus-communities-nj.html", "es/55-plus-communities-nj.html", "/55-plus-communities-nj"),
            ("downsizing-nj.html", "es/downsizing-nj.html", "/downsizing-nj"),
        )
        for english, spanish, route in pairs:
            en = read(english)
            es = read(spanish)
            with self.subTest(pair=route):
                for source in (en, es):
                    self.assertIn(f'hreflang="en-US" href="{ORIGIN + route}"', source)
                    self.assertIn(f'hreflang="es-US" href="{ORIGIN + "/es" + route}"', source)
                    self.assertIn(f'hreflang="x-default" href="{ORIGIN + route}"', source)
                self.assertIn('<html lang="en-US">', en)
                self.assertIn('<html lang="es-US">', es)

        shared_luxury_sources = (
            "https://www.nar.realtor/handbook-on-multiple-listing-policy/current-listings-section-5-multiple-listing-options-for-sellers-policy-statement-8-14",
            "https://www.njtransit.com/schedules-and-fares/",
            "https://msc.fema.gov/portal/home",
            "https://www.nj.gov/dobi/division_consumers/pdf/buyingahome.pdf",
        )
        for relative in ("luxury-homes-nj.html", "es/luxury-homes-nj.html"):
            source = read(relative)
            for url in shared_luxury_sources:
                self.assertIn(url, source, relative)

        shared_55_sources = (
            "https://www.hud.gov/sites/documents/hopa.pdf",
            "https://www.ecfr.gov/current/title-24/subtitle-B/chapter-I/subchapter-A/part-100/subpart-E/section-100.305",
            "https://www.nj.gov/dca/codes/offices/pred.shtml",
            "https://www.nj.gov/treasury/taxation/staynj/index.shtml",
            "https://www.njtransit.com/schedules-and-fares/",
        )
        for relative in ("55-plus-communities-nj.html", "es/55-plus-communities-nj.html"):
            source = read(relative)
            for url in shared_55_sources:
                self.assertIn(url, source, relative)

        shared_downsizing_sources = (
            "https://www.nj.gov/treasury/taxation/staynj/index.shtml",
            "https://www.hud.gov/sites/documents/hopa.pdf",
            "https://www.nj.gov/dca/codes/offices/pred.shtml",
            "https://www.irs.gov/pub/irs-pdf/p523.pdf",
            "https://nj.gov/treasury/unclaimed-property/treasury/taxation/lpt/rtffaqs.shtml",
            "https://www.njconsumeraffairs.gov/pmw",
            "https://www.nj.gov/humanservices/doas/assistance/county-offices/",
        )
        for relative in ("downsizing-nj.html", "es/downsizing-nj.html"):
            source = read(relative)
            for url in shared_downsizing_sources:
                self.assertIn(url, source, relative)

    def test_luxury_pages_use_current_policy_without_inventory_or_outcome_claims(self) -> None:
        en = visible_text(read("luxury-homes-nj.html")).lower()
        es = visible_text(read("es/luxury-homes-nj.html")).lower()
        self.assertIn("policy statement 8.14", en)
        self.assertIn("effective january 1, 2026", en)
        self.assertIn("office exclusive", en)
        self.assertIn("delayed marketing", en)
        self.assertIn("política 8.14", es)
        self.assertIn("vigente el 1 de enero de 2026", es)
        self.assertIn("exclusividad de oficina", es)
        self.assertIn("mercadeo demorado", es)

        for relative in ("luxury-homes-nj.html", "es/luxury-homes-nj.html"):
            source = read(relative)
            text = visible_text(source).lower()
            with self.subTest(page=relative):
                self.assertNotRegex(text, r"\$\s*\d")
                self.assertNotRegex(text, r"\b\d+(?:\.\d+)?\s*%\s*(?:savings?|discount|ahorro|descuento)")
                self.assertNotIn("off-market access", text)
                self.assertNotIn("acceso fuera del mercado", text)
                self.assertNotIn("private listing network", text)
                self.assertNotIn("global buyer reach", text)
                self.assertNotIn("international luxury distribution", text)
                self.assertNotIn("routinely see homes", text)
                self.assertNotIn("mis clientes", text)
                self.assertNotRegex(text, r"\b(?:30|45|60|90)\s*(?:day|days|d[ií]a|d[ií]as)\b")

    def test_hopa_pred_and_stay_nj_caveats_are_complete(self) -> None:
        en = visible_text(read("55-plus-communities-nj.html")).lower()
        es = visible_text(read("es/55-plus-communities-nj.html")).lower()
        for phrase in (
            "at least 80% of occupied units",
            "intent to operate as housing for persons 55 or older",
            "age-verification procedures",
            "november 2, 2026",
            "subject to state budget appropriations",
            "there is no universal rule to sell first or buy first",
        ):
            self.assertIn(phrase, en)
        for phrase in (
            "al menos el 80% de las unidades ocupadas",
            "intención de operar como vivienda para personas de 55 años o más",
            "procedimientos de hud mediante encuestas",
            "2 de noviembre de 2026",
            "dependen del presupuesto estatal",
            "no existe una regla universal de vender o comprar primero",
        ):
            self.assertIn(phrase, es)

        for relative in ("55-plus-communities-nj.html", "es/55-plus-communities-nj.html"):
            text = visible_text(read(relative)).lower()
            with self.subTest(page=relative):
                self.assertNotRegex(text, r"\$\s*\d")
                self.assertNotIn("for most new jersey downsizers, sell first", text)
                self.assertNotIn("para la mayoría de quienes reducen, venda primero", text)
                self.assertNotIn("the usual bridge", text)
                self.assertNotIn("el puente habitual", text)
                self.assertNotRegex(text, r"(?:hoa|association|asociaci[oó]n)[^.!?]{0,100}(?:always|siempre)\s+(?:covers?|cubre)")

    def test_downsizing_pair_rejects_one_move_and_universal_sequence_promises(self) -> None:
        en = visible_text(read("downsizing-nj.html")).lower()
        es = visible_text(read("es/downsizing-nj.html")).lower()
        self.assertIn("there is no universal best sequence", en)
        self.assertIn("no existe una secuencia universal", es)
        self.assertIn("november 2, 2026", en)
        self.assertIn("2 de noviembre de 2026", es)
        for text in (en, es):
            self.assertNotIn("move once instead of twice", text)
            self.assertNotIn("mudarse una sola vez", text)
            self.assertNotIn("without moving twice", text)
            self.assertNotIn("sin mudarse dos veces", text)
            self.assertNotIn("for most new jersey downsizers, sell first", text)

    def test_hudson_relocation_uses_trip_specific_fair_housing_safe_evidence(self) -> None:
        relative = "blog/moving-from-jersey-city-hoboken-to-suburbs.html"
        source = read(relative)
        text = visible_text(source).lower()
        for url in (
            "https://www.njtransit.com/schedules-and-fares/",
            "https://www.njtransit.com/travel-alerts-to",
            "https://www.panynj.gov/path/en/schedules-maps.html",
            "https://www.jerseycitynj.gov/cityhall/housinganddevelopment/cityplanning",
            "https://msc.fema.gov/portal/home",
            "https://www.nj.gov/education/schoolperformance/",
            "https://www.nj.gov/dobi/division_consumers/pdf/buyingahome.pdf",
        ):
            self.assertIn(url, source)
        for phrase in (
            "real starting address and destination entrance",
            "intended origin, destination, day, and time",
            "a station name or line does not establish a commute",
            "use fair-housing-safe location criteria",
            "should not rank a town",
            "not equivalent to a mortgage payment",
        ):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, r"\$\s*\d")
        self.assertNotRegex(text, r"\b\d+\s*(?:-|–|to)\s*\d+\s*(?:minute|minutes|min)\b")
        for stale in (
            "same commute you have now",
            "pick the train line first",
            "best-fit suburbs",
            "strongest value",
            "top states in the country for public education",
            "private-school tuition",
            "trade rent checks for a front door",
            "helped hudson county renters make this exact move",
        ):
            self.assertNotIn(stale, text)

    def test_lead_paths_remain_contextual(self) -> None:
        expected = {
            "luxury-homes-nj.html": ("/home-valuation", "/buy-a-home"),
            "es/luxury-homes-nj.html": ("/home-valuation", "/es/buy-a-home"),
            "55-plus-communities-nj.html": ("/home-valuation", "/downsizing-nj"),
            "es/55-plus-communities-nj.html": ("/home-valuation", "/es/downsizing-nj"),
            "downsizing-nj.html": ("/home-valuation", "/net-proceeds-calculator"),
            "es/downsizing-nj.html": ("/home-valuation", "/net-proceeds-calculator"),
            "blog/moving-from-jersey-city-hoboken-to-suburbs.html": ("/buy-a-home", "/#contact"),
        }
        for relative, paths in expected.items():
            source = read(relative)
            with self.subTest(page=relative):
                for route in paths:
                    self.assertIn(f'href="{route}"', source)

    def test_55_plus_social_metadata_is_synced_to_current_snippet(self) -> None:
        for relative in ("55-plus-communities-nj.html", "es/55-plus-communities-nj.html"):
            parser = SurfaceParser()
            parser.feed(read(relative))
            with self.subTest(page=relative):
                title = parser.title.strip()
                description = parser.meta("name", "description")
                self.assertEqual(title, parser.meta("property", "og:title"))
                self.assertEqual(title, parser.meta("name", "twitter:title"))
                self.assertEqual(description, parser.meta("property", "og:description"))
                self.assertEqual(description, parser.meta("name", "twitter:description"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
