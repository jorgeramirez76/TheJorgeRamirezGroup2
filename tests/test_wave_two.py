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


AI_PIPELINE_MANIFEST = ROOT / "data" / "ai-sales-pipeline-route-migration.json"


def expected_ai_pipeline_redirects() -> dict[str, str]:
    manifest = json.loads(AI_PIPELINE_MANIFEST.read_text(encoding="utf-8"))
    routes: dict[str, str] = {}
    for family in manifest["families"]:
        for alias in family["aliases"]:
            for language in ("en", "es"):
                clean = manifest["routePrefixByLanguage"][language] + alias
                destination = family["destinationByLanguage"][language]
                routes[clean] = destination
    return routes


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


def public_claim_documents() -> list[Path]:
    documents = list(public_html())
    for name in (
        "llms.txt",
        "llms-full.txt",
        "llms-es.txt",
        "schema-realtor.json",
        "manifest.json",
        "site.webmanifest",
    ):
        path = ROOT / name
        if path.exists():
            documents.append(path)
    return documents


def indexable_public_html() -> list[Path]:
    redirected = exact_redirect_sources()
    return [
        path
        for path in public_html()
        if not robots_noindex(read(path))
        and not is_redirect_stub(read(path))
        and deployed_path(path) not in redirected
        and canonical_url(read(path))
    ]


def public_claim_emitters() -> list[Path]:
    names = (
        "api/lead.js",
        "build_communities_page.py",
        "bulk_update_towns.py",
        "fix_site_issues_v2.py",
        "gen_serp_pages.py",
        "generate_blog.py",
        "generate_county_reports_and_comparisons.py",
        "generate_new_landing_pages.py",
        "generate_somerset_towns.py",
        "index.html.backup",
        "js/communities-data.js",
        "js/main.js",
        "optimize_seo.py",
    )
    sources = [ROOT / name for name in names if (ROOT / name).exists()]
    sources.extend(sorted((ROOT / "_posts").glob("*.md")))
    return sources


class WaveTwoContractTests(unittest.TestCase):
    maxDiff = None

    def test_unverified_community_total_is_absent_from_public_pages(self):
        unsupported_total = re.compile(
            r"\b(?:103|109|120|138)\s+(?:(?:NJ|New Jersey)\s+)?(?:communities|towns)\b|"
            r"\b(?:103|109|120|138)\s+(?:comunidades|pueblos|municipios)\b|"
            r"data-target=[\"'](?:103|109|120|138)[\"']|"
            r">(?:103|109|120|138)</[^>]+>[^<]{0,30}<[^>]+>[^<]*(?:communities|towns|comunidades|pueblos|municipios)",
            re.I,
        )
        offenders = [
            str(path.relative_to(ROOT))
            for path in public_claim_documents()
            if unsupported_total.search(read(path))
        ]
        self.assertEqual([], offenders)

    def test_claim_emitters_cannot_restore_wave_two_failures(self):
        forbidden = re.compile(
            r"\b(?:103|109|120|138)\s+(?:(?:NJ|New Jersey)\s+)?"
            r"(?:communities|towns|comunidades|pueblos|municipios)\b|"
            r"\btop[- ]rated\s+(?:(?:NJ|New Jersey)\s+)?"
            r"(?:real estate\s+)?(?:agent|Realtor|agency|team|group)\b|"
            r"(?:Jorge Ramirez|The Jorge Ramirez Group)[^.<\n]{0,120}\b"
            r"(?:top|best) (?:listing |real estate )?agent\b|"
            r"\b(?:I(?:'|’)?ve|I have|Jorge has|we have)\s+helped\s+hundreds\s+of\s+families\b|"
            r"\byears?\s+(?:of\s+)?helping\s+(?:(?:New Jersey|NJ)\s+)?families\b|"
            r"\b(?:active development pipeline|historical appreciation demonstrates reliable returns|healthy inventory levels?)\b|"
            r"\b(?:strong|top(?:[- ]rated|[- ]tier)?)\s+"
            r"school(?:s|\s+districts?|\s+systems?|[- ]districts?|\s+towns?)\b",
            re.I,
        )
        offenders = [
            str(path.relative_to(ROOT))
            for path in public_claim_emitters()
            if forbidden.search(read(path))
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
                r"\btop[- ]rated\s+(?:(?:NJ|New Jersey)\s+)?"
                r"(?:real estate\s+)?(?:agent|Realtor|agency|team|group)\b|"
                r"\b(?:agente|agencia)\s+de\s+bienes\s+ra[ií]ces\s+mejor\s+calificad[oa]\b|"
                r"\bmejor\s+calificad[oa]\s+agente\s+de\s+bienes\s+ra[ií]ces\b|"
                r"\b(?:mejor|destacad[oa])\s+agente(?:\s+inmobiliari[oa])?\b|"
                r"\bagente\s+inmobiliari[oa]\s+(?:de\s+primer\s+nivel|destacad[oa])\b",
                re.I,
            ),
            "top-agent claim": re.compile(
                r"(?:Jorge Ramirez|The Jorge Ramirez Group)[^.<\n]{0,120}\btop (?:listing |real estate )?agent\b|"
                r"\btop (?:listing |real estate )?agent\b[^.<\n]{0,120}(?:Jorge Ramirez|The Jorge Ramirez Group)|"
                r"\bJorge(?: Ramirez)?(?:'s)?[^.<\n]{0,80}\btop-agent network\b|"
                r"\bJorge(?: Ramirez)?(?:'s)?[^.<\n]{0,80}\btop listing agents\b",
                re.I,
            ),
            "best-agent claim": re.compile(
                r"(?:Jorge Ramirez|The Jorge Ramirez Group)[^.<\n]{0,120}\bbest "
                r"(?:listing |real estate )?agent\b|"
                r"\bbest (?:listing |real estate )?agent\b[^.<\n]{0,120}"
                r"(?:Jorge Ramirez|The Jorge Ramirez Group)|"
                r"\bI(?:'m| am)[^.<\n]{0,60}\b(?:the )?best agent\b|"
                r"\bsoy[^.<\n]{0,60}\bel mejor agente\b",
                re.I,
            ),
            "15-year tenure": re.compile(
                r"\b(?:15|fifteen)\+?(?:[- ]year|\s+years?)\s+(?:of\s+)?"
                r"(?:real estate|agent|Realtor|selling|listing|transaction|experience)|"
                r"\b(?:Jorge Ramirez|real estate agent|Realtor)[^.<\n]{0,100}"
                r"\b(?:for|with|over)\s+(?:15|fifteen)\+?\s+years?\b",
                re.I,
            ),
        }
        failures: dict[str, list[str]] = {key: [] for key in forbidden}
        for path in public_claim_documents():
            text = read(path)
            for label, pattern in forbidden.items():
                if pattern.search(text):
                    failures[label].append(str(path.relative_to(ROOT)))
        self.assertEqual({key: [] for key in forbidden}, failures)

    def test_indexable_copy_avoids_unsupported_trust_patterns(self):
        forbidden = {
            "numeric or categorical service scope": re.compile(
                r"\b(?:serves?|serving)\s+(?:all\s+)?(?:the\s+)?\d+\s+(?:NJ\s+)?(?:[A-Z][A-Za-z -]+ County\s+(?:NJ\s+)?)?(?:towns|communities)\b|"
                r"\b\d+\s+(?:NJ\s+)?(?:[A-Z][A-Za-z -]+ County\s+(?:NJ\s+)?)?(?:towns|communities)\s+served\b|"
                r"\batiende\s+(?:a\s+)?(?:(?:todos?|todas?)\s+)?(?:(?:los|las)\s+)?\d+\s+(?:pueblos|comunidades|municipios)\b|"
                r"\batendiendo\s+(?:a\s+)?(?:(?:todos?|todas?)\s+)?(?:(?:los|las)\s+)?\d+\s+(?:pueblos|comunidades|municipios)\b|"
                r"\b\d+\s+(?:pueblos|comunidades|municipios)\s+(?:atendidos?|atendidas?)\b|"
                r"\b\d+\s+(?:pueblos|comunidades|municipios)\s+del\s+Condado\s+de\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+\s+(?:atendidos?|atendidas?)\b|"
                r"\b\d+\s+(?:pueblos|comunidades|municipios)\s+de\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+\s+County\s+(?:atendidos?|atendidas?)\b|"
                r"\b(?:covers?|serves?)\s+(?:all|every)\s+(?:NJ\s+)?(?:[A-Z][A-Za-z -]+ County\s+)?(?:town|community)\b|"
                r"\bcovers?\s+every\s+[A-Z][A-Za-z-]+\s+town\b|"
                r"\batiende\s+(?:a\s+)?(?:todos?|todas?)\s+(?:los|las)\s+(?:pueblos|comunidades|municipios)\b|"
                r"\b(?:cubre\s+cada\s+pueblo|atiende\s+cada\s+comunidad)\b",
                re.I,
            ),
            "categorical block or street knowledge": re.compile(
                r"\b(?:know|knows|knowing)\s+every\s+(?:block|street)\b|"
                r"\bconoce\s+cada\s+(?:cuadra|calle)\b|"
                r"\bconozco\s+cada\s+(?:cuadra|calle)\b",
                re.I,
            ),
            "unsupported family volume or tenure": re.compile(
                r"\b(?:I(?:'|’)?ve|I have|Jorge has|we have)\s+helped\s+hundreds\s+of\s+families\b|"
                r"\byears?\s+(?:of\s+)?helping\s+families\b|"
                r"\b(?:he|ha|han)\s+ayudado\s+a\s+cientos\s+de\s+familias\b|"
                r"\ba[ñn]os\s+ayudando\s+a\s+familias\b",
                re.I,
            ),
            "unsupported market certainty": re.compile(
                r"\bactive development pipeline\b|"
                r"\bhistorical appreciation demonstrates reliable returns\b|"
                r"\bhealthy inventory levels?\b|"
                r"\bcartera activa de desarrollo\b|"
                r"\bla apreciaci[oó]n hist[oó]rica demuestra rendimientos confiables\b|"
                r"\bniveles? de inventario saludables?\b",
                re.I,
            ),
            "unsupported school ranking": re.compile(
                r"\b(?:strong|top(?:[- ]rated|[- ]tier)?)\s+school(?:s|\s+districts?|\s+systems?|[- ]districts?|\s+towns?)\b|"
                r"\b(?:escuelas?(?:\s+p[uú]blicas?)?|distritos?\s+escolares?)\s+"
                r"(?:s[oó]lidas?|fuertes?|de\s+primer\s+nivel|mejor(?:es)?\s+calificad[oa]s?)\b",
                re.I,
            ),
        }
        failures: dict[str, list[str]] = {key: [] for key in forbidden}
        for path in indexable_public_html():
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

    def test_off_topic_ai_sales_product_is_removed_but_legacy_equity_is_preserved(self):
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

        for sitemap in (ROOT / "sitemap.xml", ROOT / "sitemap-es.xml"):
            with self.subTest(sitemap=sitemap.name):
                self.assertNotRegex(read(sitemap), r"(?:/es)?/features/")

        expected = expected_ai_pipeline_redirects()
        redirects = json.loads(read(ROOT / "vercel.json"))["redirects"]
        feature_redirects = {
            str(rule.get("source")): rule
            for rule in redirects
            if re.fullmatch(
                r"/(?:es/)?features/[^/:*()]+(?:\.html)?",
                str(rule.get("source", "")),
            )
        }
        self.assertEqual(set(expected), set(feature_redirects))
        self.assertIs(True, json.loads(read(ROOT / "vercel.json")).get("cleanUrls"))
        self.assertFalse(any(source.endswith(".html") for source in feature_redirects))
        all_sources = {str(rule.get("source", "")) for rule in redirects}
        for source, destination in expected.items():
            with self.subTest(source=source):
                rule = feature_redirects[source]
                self.assertEqual(destination, rule.get("destination"))
                self.assertIs(True, rule.get("permanent"))
                self.assertTrue(destination.startswith("https://aisalespipeline.com/"))
                self.assertNotIn(destination, all_sources)


if __name__ == "__main__":
    unittest.main(verbosity=2)
