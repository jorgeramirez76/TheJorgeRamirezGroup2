#!/usr/bin/env python3
"""Regression checks for the evidence-backed GSC and entity-consistency fixes."""

from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://thejorgeramirezgroup.com"
SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
LEGACY_COORDINATES = ("40.7195", "-74.3648")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def sitemap_paths() -> set[str]:
    result: set[str] = set()
    for name in ("sitemap.xml", "sitemap-es.xml"):
        root = ET.fromstring(read(name))
        result.update(
            urlsplit(node.text or "").path.rstrip("/") or "/"
            for node in root.findall(".//s:loc", SITEMAP_NS)
        )
    return result


def deployed_file(path: str) -> Path | None:
    clean = path.strip("/")
    candidates = [ROOT / "index.html"] if not clean else [ROOT / f"{clean}.html", ROOT / clean / "index.html"]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def jsonld_nodes(value: object):
    if isinstance(value, dict):
        if "@type" in value:
            yield value
        for child in value.values():
            yield from jsonld_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from jsonld_nodes(child)


def homepage_jsonld(relative: str) -> list[dict]:
    blocks = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        read(relative),
        re.I | re.S,
    )
    payloads = [json.loads(block) for block in blocks]
    return [node for payload in payloads for node in jsonld_nodes(payload)]


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.add(href)


class GscGeoRemediationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = json.loads(read("data/site-facts.json"))
        cls.priorities = json.loads(read("data/gsc-geo-priorities.json"))
        cls.submitted = sitemap_paths()
        cls.redirects = {
            item["source"]
            for item in json.loads(read("vercel.json")).get("redirects", [])
            if not re.search(r"[:*]", item.get("source", ""))
        }

    def test_verified_office_coordinates_are_the_only_legacy_geo_emitters(self) -> None:
        geo = self.facts["business"]["geo"]
        expected_position = f'{geo["latitude"]};{geo["longitude"]}'
        expected_icbm = f'{geo["latitude"]}, {geo["longitude"]}'
        geo_meta_pages: set[str] = set()

        public_sources = [
            path
            for path in ROOT.rglob("*.html")
            if not ({".git", ".vercel", "node_modules", "tmp"} & set(path.relative_to(ROOT).parts))
        ]
        for path in public_sources:
            source = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                for legacy in LEGACY_COORDINATES:
                    self.assertNotIn(legacy, source)

                positions = re.findall(
                    r'<meta\b[^>]*name=["\']geo\.position["\'][^>]*content=["\']([^"\']+)',
                    source,
                    re.I,
                )
                icbm = re.findall(
                    r'<meta\b[^>]*name=["\']ICBM["\'][^>]*content=["\']([^"\']+)',
                    source,
                    re.I,
                )
                if positions or icbm:
                    geo_meta_pages.add(path.relative_to(ROOT).as_posix())
                    self.assertEqual([expected_position], positions)
                    self.assertEqual([expected_icbm], icbm)

        self.assertTrue(
            {
                "index.html",
                "es/index.html",
                "home-valuation.html",
                "es/home-valuation.html",
            }.issubset(geo_meta_pages)
        )
        emitter = read("generate_new_landing_pages.py")
        self.assertIn(expected_position, emitter)
        self.assertIn(expected_icbm, emitter)
        for legacy in LEGACY_COORDINATES:
            self.assertNotIn(legacy, emitter)

    def test_homepage_business_schema_uses_one_verified_entity_per_language(self) -> None:
        business = self.facts["business"]
        expected_counties = {
            f"{county} County, New Jersey" for county in self.facts["serviceCounties"]
        }
        expected_geo = (business["geo"]["latitude"], business["geo"]["longitude"])

        for relative in ("index.html", "es/index.html"):
            nodes = homepage_jsonld(relative)
            with self.subTest(relative=relative):
                agents = [
                    node
                    for node in nodes
                    if node.get("@type") == "RealEstateAgent"
                    and node.get("@id") == f"{ORIGIN}/#agent"
                ]
                self.assertEqual(1, len(agents))
                agent = agents[0]
                self.assertEqual(business["name"], agent.get("name"))
                self.assertEqual(business["directPhone"]["e164"], agent.get("telephone"))
                self.assertEqual(business["email"], agent.get("email"))
                self.assertEqual(
                    {
                        "streetAddress": business["address"]["street"],
                        "addressLocality": business["address"]["city"],
                        "addressRegion": business["address"]["region"],
                        "postalCode": business["address"]["postalCode"],
                        "addressCountry": business["address"]["country"],
                    },
                    {key: value for key, value in agent["address"].items() if key != "@type"},
                )
                self.assertEqual(
                    expected_geo,
                    (float(agent["geo"]["latitude"]), float(agent["geo"]["longitude"])),
                )
                self.assertEqual(expected_counties, {area["name"] for area in agent["areaServed"]})
                encoded = json.dumps(nodes)
                self.assertNotIn("priceRange", encoded)
                self.assertNotIn("BreadcrumbList", {node.get("@type") for node in nodes})

    def test_gsc_internal_link_manifest_is_complete_and_links_clean_targets(self) -> None:
        clusters = self.priorities["internalLinkClusters"]
        targets = [item for cluster in clusters for item in cluster["targets"]]
        totals = self.priorities["internalLinkTotals"]
        self.assertEqual(totals["targets"], len(targets))
        self.assertEqual(totals["targets"], len({item["path"] for item in targets}))
        self.assertEqual(totals["clicks"], sum(item["clicks"] for item in targets))
        self.assertEqual(totals["impressions"], sum(item["impressions"] for item in targets))
        self.assertEqual(totals["aiImpressions"], sum(item["aiImpressions"] for item in targets))

        for cluster in clusters:
            parser = AnchorParser()
            parser.feed(read(cluster["source"]))
            for item in cluster["targets"]:
                path = item["path"]
                with self.subTest(source=cluster["source"], target=path):
                    self.assertIn(path, parser.hrefs)
                    self.assertNotIn(".html", path)
                    self.assertIn(path, self.submitted)
                    self.assertNotIn(path, self.redirects)
                    target = deployed_file(path)
                    self.assertIsNotNone(target)
                    source = target.read_text(encoding="utf-8")
                    self.assertNotRegex(source, r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex')
                    canonical = re.search(
                        r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)',
                        source,
                        re.I,
                    )
                    self.assertIsNotNone(canonical)
                    self.assertEqual(path, urlsplit(canonical.group(1)).path.rstrip("/") or "/")

        english = AnchorParser()
        english.feed(read("index.html"))
        self.assertIn("/ai-authority", english.hrefs)
        authority = AnchorParser()
        authority.feed(read("ai-authority.html"))
        self.assertIn("/es/ai-authority#comparaciones", authority.hrefs)

    def test_performance_and_coverage_summaries_are_internally_consistent(self) -> None:
        performance = self.priorities["performanceSummary"]
        recent = performance["recent"]
        prior = performance["prior"]
        query = performance["queryExport"]
        pages = performance["pageExport"]
        self.assertEqual(519, recent["clicks"])
        self.assertEqual(103892, recent["impressions"])
        self.assertEqual(200, prior["clicks"])
        self.assertEqual(51299, prior["impressions"])
        self.assertAlmostEqual(100 * recent["clicks"] / recent["impressions"], recent["ctrPercent"], places=2)
        self.assertAlmostEqual(100 * prior["clicks"] / prior["impressions"], prior["ctrPercent"], places=2)
        self.assertAlmostEqual(100 * query["clicks"] / recent["clicks"], query["shareOfPropertyClicksPercent"], places=2)
        self.assertAlmostEqual(100 * query["impressions"] / recent["impressions"], query["shareOfPropertyImpressionsPercent"], places=2)
        self.assertIs(False, query["hasPageDimension"])
        self.assertGreaterEqual(pages["clicks"], recent["clicks"])
        self.assertGreaterEqual(pages["impressions"], recent["impressions"])

        coverage = self.priorities["indexCoverageDisposition"]
        for issue, expected in (
            (coverage["notFound"], 52),
            (coverage["crawledNotIndexed"], 258),
            (coverage["googleChoseDifferentCanonical"], 44),
        ):
            dispositions = sum(
                value
                for key, value in issue.items()
                if key != "sourceRows" and isinstance(value, int)
            )
            self.assertEqual(expected, issue["sourceRows"])
            self.assertEqual(expected, dispositions)

        ai = self.priorities["aiAppearanceSummary"]
        self.assertEqual(ai["reportImpressions"], sum(ai["deviceImpressions"].values()))
        self.assertGreater(ai["pageRowImpressions"], ai["reportImpressions"])

    def test_ai_discovery_paths_are_current_indexable_canonicals(self) -> None:
        priorities = self.priorities["aiDiscoveryPaths"]
        self.assertEqual(priorities, sorted(priorities, key=lambda item: item["aiImpressions"], reverse=True))
        for item in priorities:
            path = item["path"]
            with self.subTest(path=path):
                self.assertGreater(item["aiImpressions"], 0)
                self.assertIn(path, self.submitted)
                self.assertNotIn(path, self.redirects)
                self.assertIsNotNone(deployed_file(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
