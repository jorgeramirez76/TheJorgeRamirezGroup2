#!/usr/bin/env python3
"""Regression checks for public business facts and editorial trust signals.

The site is static, so these tests intentionally use only the Python standard
library and inspect the generated HTML that search engines actually receive.
"""

from __future__ import annotations

import html
import json
import re
import unittest
from datetime import datetime
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
FACTS_PATH = ROOT / "data" / "site-facts.json"


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(r"<script\b[^>]*>.*?</script>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    source = re.sub(r"<[^>]+>", " ", source)
    return re.sub(r"\s+", " ", html.unescape(source)).strip()


def json_ld_objects(source: str) -> list[object]:
    blocks = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source,
        flags=re.I | re.S,
    )
    return [json.loads(html.unescape(block).strip()) for block in blocks]


class ContentIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
        cls.inventory = cls.facts["canonicalTownInventory"]

    def test_inventory_is_unique_and_totals_32(self) -> None:
        by_county = self.inventory["byCounty"]
        slugs = [slug for towns in by_county.values() for slug in towns]
        self.assertEqual(32, self.inventory["total"])
        self.assertEqual(self.inventory["total"], len(slugs))
        self.assertEqual(len(slugs), len(set(slugs)), "town appears in more than one county")
        self.assertEqual(
            {"Union", "Essex", "Morris", "Hudson", "Middlesex", "Somerset"},
            set(by_county),
        )

    def test_inventory_matches_english_sitemap_town_urls(self) -> None:
        sitemap_slugs = set(
            re.findall(
                r"<loc>https://thejorgeramirezgroup\.com/towns/([^<]+)</loc>",
                read("sitemap.xml"),
            )
        )
        registered = {
            slug
            for towns in self.inventory["byCounty"].values()
            for slug in towns
        }
        self.assertEqual(registered, sitemap_slugs)

    def test_deployed_communities_hub_matches_inventory_and_county_membership(self) -> None:
        # Static previews and Vercel clean-URL routing can select different
        # source files for `/communities`; both must be generated identically.
        source = read("communities/index.html")
        self.assertEqual(source, read("communities.html"))
        registered = {
            slug
            for towns in self.inventory["byCounty"].values()
            for slug in towns
        }
        hub_slugs = set(re.findall(r'href=["\']/towns/([^"\']+)["\']', source))
        self.assertEqual(registered, hub_slugs)

        for county, expected in self.inventory["byCounty"].items():
            match = re.search(
                rf'<section\b[^>]*data-county=["\']{re.escape(county)}["\'][^>]*>(.*?)</section>',
                source,
                flags=re.I | re.S,
            )
            self.assertIsNotNone(match, f"missing {county} section")
            section = match.group(1)
            actual = set(re.findall(r'href=["\']/towns/([^"\']+)["\']', section))
            self.assertEqual(set(expected), actual, f"wrong {county} membership")
            self.assertRegex(section, rf'class=["\']count["\']>{len(expected)} towns<')

        self.assertIn("32 NJ Community Guides", source)
        self.assertNotRegex(source, r"\b138\s+(?:NJ\s+)?(?:communities|towns)\b")
        schemas = json_ld_objects(source)
        item_lists = []
        for obj in schemas:
            if isinstance(obj, dict):
                entity = obj.get("mainEntity")
                if isinstance(entity, dict) and entity.get("@type") == "ItemList":
                    item_lists.append(entity)
        self.assertTrue(item_lists, "communities page is missing ItemList data")
        self.assertEqual([32], [item["numberOfItems"] for item in item_lists])

    def test_spanish_communities_hub_matches_indexable_inventory(self) -> None:
        source = read("es/communities/index.html")
        self.assertEqual(source, read("es/communities.html"))
        registered = {
            slug
            for towns in self.inventory["byCounty"].values()
            for slug in towns
        }
        hub_slugs = set(
            re.findall(r'class=["\']town-card["\'][^>]*href=["\']/es/towns/([^"\']+)', source)
        )
        self.assertEqual(registered, hub_slugs)
        self.assertNotRegex(source, r' class=["\']town-card["\'][^>]*href=["\']/towns/')
        self.assertIn("32 guías de comunidades de NJ", source)

        item_lists = []
        for obj in json_ld_objects(source):
            if isinstance(obj, dict):
                entity = obj.get("mainEntity")
                if isinstance(entity, dict) and entity.get("@type") == "ItemList":
                    item_lists.append(entity)
        self.assertEqual([32], [item["numberOfItems"] for item in item_lists])
        schema_urls = {
            item["url"].removeprefix("https://thejorgeramirezgroup.com/es/towns/")
            for item in item_lists[0]["itemListElement"]
        }
        self.assertEqual(registered, schema_urls)

    def test_communities_hubs_use_the_homepage_palette(self) -> None:
        for relative in ("communities/index.html", "es/communities/index.html"):
            source = read(relative)
            self.assertNotRegex(source, r"(?i)#(?:1a3a5c|2c5f8d|f5b942|ffc857)\b")
            for token in ("#C41230", "#B8962E", "#1A1A1A", "#FAFAF8"):
                self.assertIn(token, source, f"{relative} is missing {token}")
            self.assertIn("'Playfair Display', Georgia, serif", source)
            self.assertRegex(source, r"\.town-card \.arrow \{[^}]*min-height: 44px")

    def test_basking_ridge_relationship_is_somerset_not_morris(self) -> None:
        relationship = self.facts["placeRelationships"]["basking-ridge"]
        self.assertEqual("Somerset", relationship["county"])
        self.assertEqual("bernards-township", relationship["municipality"])
        self.assertIn("basking-ridge", self.inventory["byCounty"]["Somerset"])
        self.assertNotIn("basking-ridge", self.inventory["byCounty"]["Morris"])

    def test_stable_nap_and_experience_facts(self) -> None:
        business = self.facts["business"]
        self.assertEqual("908-230-7844", business["directPhone"]["display"])
        self.assertEqual("+19082307844", business["directPhone"]["e164"])
        self.assertEqual("jorge.ramirez@kw.com", business["email"])
        self.assertEqual("488 Springfield Ave", business["address"]["street"])
        self.assertEqual("Summit", business["address"]["city"])
        self.assertEqual("NJ", business["address"]["region"])
        self.assertEqual("07901", business["address"]["postalCode"])
        self.assertEqual("1754604", business["njRealEstateLicense"])
        self.assertEqual(2017, business["fullTimeSince"])

        old_phone = "908-317-3227"
        offenders = [
            str(path.relative_to(ROOT))
            for path in ROOT.rglob("*.html")
            if old_phone in path.read_text(encoding="utf-8", errors="ignore")
        ]
        self.assertEqual([], offenders, f"obsolete direct phone remains in {offenders}")

    def test_authority_page_uses_all_service_counties_and_clean_footer(self) -> None:
        source = read("ai-authority.html")
        text = visible_text(source)
        for county in self.facts["serviceCounties"]:
            self.assertIn(f"{county} County", text)
        self.assertNotIn("2©", text)
        self.assertNotRegex(source, r"\b138\s+communities\b")
        agents = [
            obj
            for obj in json_ld_objects(source)
            if isinstance(obj, dict) and obj.get("@type") == "RealEstateAgent"
        ]
        self.assertEqual(1, len(agents))
        served = {place["name"] for place in agents[0]["areaServed"]}
        self.assertEqual(
            {f"{county} County, NJ" for county in self.facts["serviceCounties"]},
            served,
        )

    def test_blog_has_no_unverified_agent_experience_or_volume_claims(self) -> None:
        experience_patterns = [
            re.compile(
                r"\b(?:after|in|based on)\s+(?:15|fifteen)\+?\s+years?\s+(?:of\s+)?"
                r"(?:selling|listing|showing|walking|helping|working|real estate|transactions?|closings?)",
                re.I,
            ),
            re.compile(
                r"\bI(?:'ve| have)\s+(?:been|spent|worked|helped|sold|walked|listed|managed)"
                r"[^.!?]{0,160}\b(?:for|over|in)\s+(?:15|fifteen)\+?\s+years?\b",
                re.I,
            ),
            re.compile(
                r"\b(?:15|fifteen)\+?\s+years?\s+(?:of\s+)?"
                r"(?:selling|listing|showing|real estate|experience|helping|working|walking|"
                r"pre-listing|seller experience)",
                re.I,
            ),
            re.compile(
                r"\b(?:real estate\s+)?agent[^.!?<]{0,80}\bwith\s+"
                r"(?:15|fifteen)\+?\s+years?\b",
                re.I,
            ),
            re.compile(
                r"\b(?:a|an)\s+(?:15|fifteen)-year\s+(?:NJ\s+)?"
                r"(?:real estate\s+)?agent\b",
                re.I,
            ),
            re.compile(r"\b(?:15|fifteen)\s+years?\s+of\s+watching\s+offers\b", re.I),
            re.compile(r"\b(?:from|based on|what I know from)\s+(?:15|fifteen)\+?\s+years?\s+of\s+(?:transactions?|closings?|showing|listing|selling)", re.I),
            re.compile(r"\b(?:15|fifteen)\+?\s+years?\s+in\s+NJ\s+real estate\b", re.I),
            re.compile(
                r"\bI(?:'ve| have)\s+dealt\s+with[^.!?]{0,140}\bin\s+"
                r"(?:15|fifteen)\+?\s+years?\b",
                re.I,
            ),
            re.compile(
                r"\bIn\s+my\s+experience\s+(?:selling|listing|showing|helping)"
                r"[^.!?]{0,160}\bfor\s+(?:15|fifteen)\+?\s+years?\b",
                re.I,
            ),
            re.compile(
                r"\b(?:in|after)\s+my\s+\d+\+?\s+years?\s+(?:of\s+)?"
                r"(?:selling|listing|showing|helping|working|real estate)\b",
                re.I,
            ),
        ]
        volume_patterns = [
            re.compile(
                r"\b500\+\s+(?:(?:NJ|New Jersey)\s+)?(?:homes?(?:\s+sold)?|transactions?|closings?|sales?|"
                r"families|sellers?|buyers?|homeowners?)\b",
                re.I,
            ),
            re.compile(r"\b(?:sold|listed|closed|handled|helped)\s+500\+\s+(?:(?:NJ|New Jersey)\s+)?", re.I),
            re.compile(
                r"\b(?:sold|listed|closed|handled|helped)\s+(?:over|more than)\s+500\s+"
                r"(?:homes?|transactions?|closings?|sales?|families|sellers?|buyers?|homeowners?)\b",
                re.I,
            ),
            re.compile(
                r"\b(?:over|more than)\s+500\s+(?:homes?|transactions?|closings?|sales?|"
                r"families|sellers?|buyers?|homeowners?)(?:\s+(?:sold|listed|closed))?\b",
                re.I,
            ),
            re.compile(r"\b500\s+homes?\s+(?:sold|listed|closed)\b", re.I),
            re.compile(
                r"\b(?:hundreds|thousands)\s+of\s+(?:homes?|transactions?|closings?|"
                r"clients?|sellers?|buyers?)\b",
                re.I,
            ),
        ]
        explicit_non_agent_context = re.compile(
            r"\b(?:years? old|HVAC|furnace|air conditioner|roof|water heater|appliance|"
            r"dishwasher|front door|household|home is over|system is over|"
            r"absorbing creative-class)\b",
            re.I,
        )
        offenders: list[str] = []
        claim_paths = list((ROOT / "blog").rglob("*")) + list((ROOT / "docs").rglob("*"))
        for path in sorted(claim_paths):
            if path.suffix.lower() not in {".html", ".md"}:
                continue
            source = path.read_text(encoding="utf-8", errors="ignore")
            claim_texts = (visible_text(source), html.unescape(source))
            found = False
            for text in claim_texts:
                for pattern in experience_patterns + volume_patterns:
                    for match in pattern.finditer(text):
                        if explicit_non_agent_context.search(match.group(0)):
                            continue
                        found = True
                        break
                    if found:
                        break
                if found:
                    break
            if found:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders, "unverified agent claims remain:\n" + "\n".join(offenders))

    def test_verified_content_corrections(self) -> None:
        market = read("blog/nj-housing-market-peak-august-2026.html")
        self.assertNotIn("Summit (Morris County)", market)
        self.assertIn('content="noindex, follow"', market)
        self.assertIn('href="/blog/best-time-to-sell-home-nj"', market)

        basking = visible_text(read("towns/basking-ridge.html"))
        self.assertNotRegex(basking, r"(?i)\b(?:55|65)\s*(?:-|–)?\s*minutes?\b")
        self.assertIn("Gladstone Branch", basking)
        self.assertIn("check the current NJ TRANSIT schedule", basking)

        green_brook_source = read("towns/green-brook.html")
        green_brook = visible_text(green_brook_source)
        self.assertIn('data-noindex-town-fallback="v1"', green_brook_source)
        self.assertNotRegex(green_brook, r"(?i)\bGreen Brook (?:train )?station\b")
        self.assertNotRegex(green_brook, r"(?i)\b55\s*(?:-|–)?\s*(?:min|minutes?)\b")
        self.assertNotIn("Gladstone Branch", green_brook)
        self.assertNotIn("NJ TRANSIT", green_brook)

        west_orange_source = read("towns/west-orange.html")
        west_orange = visible_text(west_orange_source)
        self.assertIn('data-noindex-town-fallback="v1"', west_orange_source)
        self.assertNotRegex(west_orange, r"(?i)NJ Transit service:\s*Midtown Direct")
        self.assertNotRegex(west_orange, r"(?i)\b\d+\s*(?:-|–)?\s*minutes?\b")

    def test_self_authored_agent_lists_are_noindex_with_disclosure(self) -> None:
        for county in ("essex", "morris", "union"):
            relative = f"best-real-estate-agents-{county}-county-nj-2026.html"
            source = read(relative)
            self.assertRegex(
                source,
                r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*\bnoindex\b',
            )
            self.assertIn("first-party marketing content", visible_text(source))
            self.assertRegex(
                source,
                rf'<link\s+rel=["\']canonical["\']\s+href=["\']https://thejorgeramirezgroup\.com/{re.escape(relative.removesuffix(".html"))}(?:\.html)?["\']',
            )

    def test_spanish_millburn_buyer_article_is_quarantined(self) -> None:
        relative = "es/blog/buying-home-millburn-nj-2026.html"
        source = read(relative)
        self.assertRegex(
            source,
            r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*\bnoindex\b',
        )
        self.assertRegex(
            source,
            r'<link\s+rel=["\']canonical["\']\s+href=["\']https://thejorgeramirezgroup\.com/es/blog/buying-home-millburn-nj-2026(?:\.html)?["\']',
        )

    def test_spanish_pages_have_no_fatal_mechanical_breakage(self) -> None:
        problems: list[str] = []
        for path in sorted((ROOT / "es").rglob("*.html")):
            source = path.read_text(encoding="utf-8", errors="ignore")
            relative = str(path.relative_to(ROOT))
            for tag in ("html", "head", "body"):
                opens = len(re.findall(rf"<{tag}\b", source, flags=re.I))
                closes = len(re.findall(rf"</{tag}>", source, flags=re.I))
                if (opens, closes) != (1, 1):
                    problems.append(f"{relative}: {tag} tags {opens}/{closes}")
            for tag in ("style", "script"):
                opens = len(re.findall(rf"<{tag}\b", source, flags=re.I))
                closes = len(re.findall(rf"</{tag}>", source, flags=re.I))
                if opens != closes:
                    problems.append(f"{relative}: unbalanced {tag} tags {opens}/{closes}")
            try:
                json_ld_objects(source)
            except json.JSONDecodeError as exc:
                problems.append(f"{relative}: invalid JSON-LD ({exc.msg})")
        self.assertEqual([], problems, "\n".join(problems))

    def test_article_last_updated_signals_do_not_conflict(self) -> None:
        problems: list[str] = []
        for path in sorted((ROOT / "blog").glob("*.html")):
            source = path.read_text(encoding="utf-8", errors="ignore")
            article_modified = re.search(
                r'<meta\s+property=["\']article:modified_time["\']\s+content=["\']([^"\']+)',
                source,
                flags=re.I,
            )
            last_updated = re.search(
                r'<meta\s+name=["\']last-updated["\']\s+content=["\']([^"\']+)',
                source,
                flags=re.I,
            )
            blog_modified: Optional[str] = None
            try:
                for obj in json_ld_objects(source):
                    if not isinstance(obj, dict):
                        continue
                    candidates = obj.get("@graph", [obj])
                    if not isinstance(candidates, list):
                        candidates = [obj]
                    for candidate in candidates:
                        if not isinstance(candidate, dict):
                            continue
                        types = candidate.get("@type", [])
                        if isinstance(types, str):
                            types = [types]
                        if {"Article", "BlogPosting"}.intersection(types):
                            blog_modified = candidate.get("dateModified")
                            break
            except json.JSONDecodeError:
                continue

            signals = {
                value
                for value in (
                    article_modified.group(1)[:10] if article_modified else None,
                    last_updated.group(1)[:10] if last_updated else None,
                    blog_modified[:10] if blog_modified else None,
                )
                if value
            }
            if len(signals) > 1:
                problems.append(f"{path.relative_to(ROOT)}: {sorted(signals)}")

            pill = re.search(
                r"Last updated</span>\s*(?:&nbsp;|·|\s)*.*?"
                r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                r"(?:\s+(\d{1,2}),?)?\s+(20\d{2})",
                source,
                flags=re.I | re.S,
            )
            if pill and last_updated:
                month = datetime.strptime(pill.group(1), "%B").month
                expected_prefix = f"{pill.group(3)}-{month:02d}"
                if not last_updated.group(1).startswith(expected_prefix):
                    problems.append(
                        f"{path.relative_to(ROOT)}: visible {pill.group(1)} {pill.group(3)} "
                        f"vs meta {last_updated.group(1)}"
                    )

        costs = read("blog/nj-home-selling-costs.html")
        if "Updated March 2026" in costs:
            problems.append("blog/nj-home-selling-costs.html: stale Updated March 2026 byline")
        self.assertEqual([], problems, "\n".join(problems))


if __name__ == "__main__":
    unittest.main(verbosity=2)
