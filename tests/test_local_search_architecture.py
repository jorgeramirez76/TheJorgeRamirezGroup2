#!/usr/bin/env python3
"""Contracts for county, town, and comparison discovery pathways."""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def links(source: str) -> set[str]:
    return set(re.findall(r'<a\b[^>]*href=["\']([^"\']+)', source, re.I))


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style|template|noscript)\b[^>]*>.*?</(?:script|style|template|noscript)>",
        " ",
        source,
        flags=re.I | re.S,
    )
    source = re.sub(r"<!--.*?-->|<[^>]+>", " ", source, flags=re.S)
    return " ".join(html.unescape(source).split())


def sitemap_town_slugs() -> set[str]:
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    prefix = f"{SITE}/towns/"
    return {
        (node.text or "").strip().removeprefix(prefix)
        for node in root.findall("{*}url/{*}loc")
        if (node.text or "").strip().startswith(prefix)
    }


class LocalSearchArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = json.loads(read("data/site-facts.json"))
        cls.comparisons = json.loads(read("data/top-level-town-comparison-sources.json"))

    def test_every_submitted_town_has_regional_and_conversion_pathways(self) -> None:
        county_by_town = {
            slug: county
            for county, slugs in self.facts["canonicalTownInventory"]["byCounty"].items()
            for slug in slugs
        }
        self.assertEqual(set(county_by_town), sitemap_town_slugs())

        failures: list[str] = []
        for slug, county in sorted(county_by_town.items()):
            source = read(f"towns/{slug}.html")
            hrefs = links(source)
            county_route = f"/counties/{county.lower()}-county"
            if county_route not in hrefs:
                failures.append(f"{slug}: missing {county_route}")
            if not ({"/buy-a-home", "/property-search"} & hrefs):
                failures.append(f"{slug}: missing buyer pathway")
            if not ({"/sell-your-home", "/home-valuation"} & hrefs):
                failures.append(f"{slug}: missing seller pathway")
        self.assertEqual([], failures)

    def test_town_directory_is_a_substantive_discovery_hub(self) -> None:
        source = read("towns/index.html")
        hrefs = links(source)
        submitted = sitemap_town_slugs()
        self.assertTrue({f"/towns/{slug}" for slug in submitted} <= hrefs)
        self.assertGreaterEqual(len(visible_text(source).split()), 300)
        for route in (
            "/communities",
            "/counties",
            "/buy-a-home",
            "/sell-your-home",
            "/home-valuation",
        ):
            self.assertIn(route, hrefs)

        comparison_routes = {
            f"/{slug}" for slug in self.comparisons["comparisons"]
        }
        self.assertTrue(comparison_routes <= hrefs)

    def test_gsc_priority_comparisons_have_contextual_links_from_both_town_sides(self) -> None:
        expected = {
            "/cranford-vs-westfield-nj": {"cranford", "westfield"},
            "/montclair-vs-maplewood-nj": {"montclair", "maplewood"},
            "/short-hills-vs-westfield-nj": {"millburn", "westfield"},
            "/new-providence-vs-berkeley-heights-nj": {
                "new-providence",
                "berkeley-heights",
            },
            "/millburn-vs-summit-nj": {"millburn", "summit"},
            "/jersey-city-vs-hoboken-nj": {"jersey-city", "hoboken"},
        }
        for route, town_slugs in expected.items():
            for slug in town_slugs:
                with self.subTest(route=route, slug=slug):
                    self.assertIn(route, links(read(f"towns/{slug}.html")))

    def test_priority_town_pathway_sync_is_deterministic_and_branded(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/sync_priority_town_pathways.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        css = read("css/local-search-pathways.css")
        for token in ("#1A1A1A", "#8B0D22", "#B8962E", "#D4AF5A", "#FAFAF8"):
            self.assertIn(token, css)
        self.assertIn("'Playfair Display'", css)
        self.assertIn("'Inter'", css)

    def test_communities_hubs_explain_the_directory_and_link_the_research_layers(self) -> None:
        for relative in ("communities.html", "es/communities.html"):
            with self.subTest(relative=relative):
                source = read(relative)
                hrefs = links(source)
                description = re.search(
                    r'<meta\b[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)',
                    source,
                    re.I,
                )
                self.assertIsNotNone(description)
                self.assertGreaterEqual(len(description.group(1)), 120)
                self.assertLessEqual(len(description.group(1)), 165)
                if relative.startswith("es/"):
                    for county in self.facts["canonicalTownInventory"]["byCounty"]:
                        self.assertIn(
                            f"/es/counties/{county.lower()}-county", hrefs
                        )
                    self.assertIn("/es/buy-a-home", hrefs)
                    self.assertIn("/es/sell-your-home", hrefs)
                else:
                    self.assertIn("/towns", hrefs)
                    self.assertIn("/counties", hrefs)

    def test_county_guides_match_local_intent_and_surface_relevant_comparisons(self) -> None:
        comparisons_by_county: dict[str, set[str]] = {
            county: set()
            for county in self.facts["canonicalTownInventory"]["byCounty"]
        }
        for slug, comparison in self.comparisons["comparisons"].items():
            counties = {
                self.comparisons["places"][side]["copy"]["en"]["county"].removesuffix(" County")
                for side in (comparison["left"], comparison["right"])
            }
            for county in counties:
                comparisons_by_county[county].add(f"/{slug}")

        for county, expected_comparisons in comparisons_by_county.items():
            relative = f"counties/{county.lower()}-county.html"
            source = read(relative)
            hrefs = links(source)
            title = html.unescape(re.search(r"<title>(.*?)</title>", source, re.I | re.S).group(1))
            h1 = visible_text(re.search(r"<h1\b[^>]*>.*?</h1>", source, re.I | re.S).group(0))
            with self.subTest(county=county):
                self.assertRegex(title.casefold(), rf"{county.casefold()} county nj real estate guide")
                self.assertLessEqual(len(title), 65)
                self.assertIn("real estate guide", h1.casefold())
                self.assertIn("buyers and sellers", h1.casefold())
                self.assertIn("/towns", hrefs)
                self.assertTrue(expected_comparisons <= hrefs)

    def test_spanish_county_guides_use_the_existing_local_directory(self) -> None:
        for county in self.facts["canonicalTownInventory"]["byCounty"]:
            relative = f"es/counties/{county.lower()}-county.html"
            hrefs = links(read(relative))
            with self.subTest(county=county):
                self.assertIn("/es/communities", hrefs)
                self.assertNotIn("/es/towns", hrefs)

    def test_inserted_local_pathways_remain_fair_housing_neutral(self) -> None:
        risky = re.compile(
            r"\b(?:best schools?|top[- ]rated|safest|safe neighborhood|"
            r"family[- ]friendly|ideal for families|young professionals|crime rate)\b",
            re.I,
        )
        sources = [read("towns/index.html")]
        sources.extend(
            read(f"counties/{county.lower()}-county.html")
            for county in self.facts["canonicalTownInventory"]["byCounty"]
        )
        self.assertIsNone(risky.search(" ".join(visible_text(item) for item in sources)))

    def test_spanish_relationship_redirects_keep_destination_context(self) -> None:
        from scripts.remediate_indexable_towns import render_redirect_stub

        redirects = {
            "bernards-township": "/es/towns/basking-ridge",
            "short-hills": "/es/towns/millburn",
        }
        for slug, destination in redirects.items():
            with self.subTest(slug=slug):
                expected = render_redirect_stub(slug, destination, language="es")
                source = read(f"es/towns/{slug}.html")
                self.assertEqual(expected, source)
                self.assertIn('lang="es-US"', source)
                self.assertIn('data-spanish-town-redirect="v1"', source)
                self.assertIn('class="skip-link"', source)
                self.assertIn(destination, source)


if __name__ == "__main__":
    unittest.main()
