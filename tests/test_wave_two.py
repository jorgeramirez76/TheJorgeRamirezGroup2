#!/usr/bin/env python3
"""Regression contract for the second SEO/GEO remediation wave."""

from __future__ import annotations

import json
import html
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_remediation import (
    ROOT,
    canonical_url,
    deployed_path,
    exact_redirect_sources,
    is_redirect_stub,
    jsonld_nodes,
    public_html,
    read,
    robots_noindex,
)


def title(text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip()) if match else ""


def description(text: str) -> str:
    match = re.search(
        r'<meta\s+[^>]*name=["\']description["\'][^>]*>', text, re.I
    )
    if not match:
        return ""
    content = re.search(r'content=(["\'])(.*?)\1', match.group(0), re.I | re.S)
    return html.unescape(content.group(2).strip()) if content else ""


class WaveTwoContractTests(unittest.TestCase):
    maxDiff = None

    def test_unverified_community_total_is_absent_from_public_pages(self):
        offenders = [
            str(path.relative_to(ROOT))
            for path in public_html()
            if re.search(r"\b138\s+(?:NJ\s+)?communit", read(path), re.I)
        ]
        self.assertEqual([], offenders)

    def test_unverified_agent_volume_and_superlatives_are_absent(self):
        forbidden = {
            "500-home volume": re.compile(
                r"(?:sold|listed|closed|worked with|experience with)[^.<\n]{0,35}"
                r"(?:over\s+)?500\+?\s+(?:homes|houses|properties|sales)|"
                r"(?:over\s+)?500\+?\s+(?:homes|houses|properties|sales)[^.<\n]{0,35}"
                r"(?:sold|listed|closed)",
                re.I,
            ),
            "agent top-rated claim": re.compile(
                r"(?:Jorge Ramirez|The Jorge Ramirez Group)[^.<\n]{0,120}\btop[- ]rated\b|"
                r"\btop[- ]rated\b[^.<\n]{0,120}(?:Jorge Ramirez|real estate agent|Realtor)",
                re.I,
            ),
            "top-agent claim": re.compile(
                r"(?:Jorge Ramirez|The Jorge Ramirez Group)[^.<\n]{0,120}\btop (?:listing |real estate )?agent\b|"
                r"\btop (?:listing |real estate )?agent\b[^.<\n]{0,120}(?:Jorge Ramirez|The Jorge Ramirez Group)",
                re.I,
            ),
        }
        failures: dict[str, list[str]] = {key: [] for key in forbidden}
        for path in public_html():
            text = read(path)
            for label, pattern in forbidden.items():
                if pattern.search(text):
                    failures[label].append(str(path.relative_to(ROOT)))
        self.assertEqual({key: [] for key in forbidden}, failures)

    def test_homepage_schema_is_one_coherent_non_self_review_graph(self):
        text = read(ROOT / "index.html")
        raw_blocks = re.findall(
            r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>',
            text,
            re.I | re.S,
        )
        self.assertEqual(1, len(raw_blocks), "Homepage schema should be one stable @graph")
        payload = json.loads(raw_blocks[0])
        self.assertIsInstance(payload.get("@graph"), list)
        nodes = list(jsonld_nodes(text))
        ids = [node["@id"] for node in nodes if isinstance(node.get("@id"), str)]
        self.assertEqual(len(ids), len(set(ids)), "Homepage schema @id values must be unique")
        types = {
            item
            for node in nodes
            for item in (
                node.get("@type")
                if isinstance(node.get("@type"), list)
                else [node.get("@type")]
            )
        }
        self.assertNotIn("AggregateRating", types)
        self.assertNotIn("Review", types)
        breadcrumbs = [node for node in nodes if node.get("@type") == "BreadcrumbList"]
        self.assertEqual([], breadcrumbs, "The homepage must not claim a Home > Communities breadcrumb")

    def test_homepage_has_no_unverified_volume_or_off_topic_link(self):
        text = read(ROOT / "index.html")
        self.assertNotRegex(text, r"\$\s*18\.4\s*M\+?", "Closed volume needs evidence and an as-of date")
        self.assertNotIn("bongholeo", text.lower())

    def test_current_listing_promises_have_a_real_search_destination(self):
        for name, town in (
            ("summit-nj-homes-for-sale.html", "Summit"),
            ("westfield-nj-homes-for-sale.html", "Westfield"),
        ):
            text = read(ROOT / name)
            promises_current = bool(re.search(r"current\s+(?:MLS\s+)?listings", text, re.I))
            listing_links = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)', text, re.I)
            has_search = any(
                "listings-search" in href and town.lower() in href.lower()
                for href in listing_links
            )
            self.assertFalse(promises_current and not has_search, name)

    def test_sms_terms_has_the_standard_search_and_brand_stack(self):
        text = read(ROOT / "sms-terms.html")
        required = {
            "robots": r'<meta\s+name=["\']robots["\']',
            "GA4": r"G-KMS6H85LB0",
            "shared stylesheet": r'href=["\']/css/styles\.css["\']',
            "LLM context": r'<meta\s+name=["\']llm-context["\']',
            "JSON-LD": r'application/ld\+json',
        }
        missing = [label for label, pattern in required.items() if not re.search(pattern, text, re.I)]
        self.assertEqual([], missing)

    def test_indexable_page_titles_and_descriptions_are_snippet_ready(self):
        bad: list[tuple[str, str, int]] = []
        redirected = exact_redirect_sources()
        for path in public_html():
            text = read(path)
            if (
                robots_noindex(text)
                or is_redirect_stub(text)
                or deployed_path(path) in redirected
                or not canonical_url(text)
            ):
                continue
            page_title = title(text)
            page_description = description(text)
            if not (10 <= len(page_title) <= 68):
                bad.append((str(path.relative_to(ROOT)), "title", len(page_title)))
            if not (40 <= len(page_description) <= 165):
                bad.append((str(path.relative_to(ROOT)), "description", len(page_description)))
        self.assertEqual([], bad)

    def test_known_off_palette_blue_is_absent(self):
        offenders = [
            str(path.relative_to(ROOT))
            for path in public_html()
            if re.search(r"#1a4b8c\b", read(path), re.I)
        ]
        self.assertEqual([], offenders)

    def test_off_topic_ai_sales_product_is_not_in_public_search_inventory(self):
        feature_pages = sorted(
            str(path.relative_to(ROOT))
            for directory in (ROOT / "features", ROOT / "es" / "features")
            if directory.exists()
            for path in directory.glob("*.html")
        )
        self.assertEqual(
            [],
            feature_pages,
            "AI Sales Pipeline product pages do not belong on the real-estate site",
        )

        inventory_files = (
            ROOT / "sitemap.xml",
            ROOT / "sitemap-es.xml",
            ROOT / "vercel.json",
        )
        leaked = [
            str(path.relative_to(ROOT))
            for path in inventory_files
            if re.search(r"(?:/es)?/features/", read(path), re.I)
        ]
        self.assertEqual([], leaked)


if __name__ == "__main__":
    unittest.main(verbosity=2)
