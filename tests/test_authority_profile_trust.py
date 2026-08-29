"""Trust and structured-data regression checks for the bilingual profile pages."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.parse import urljoin, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = ("ai-authority.html", "es/ai-authority.html")
ORIGIN = "https://thejorgeramirezgroup.com"
PERSON_ID = f"{ORIGIN}/#jorge-ramirez"


def jsonld_nodes(text: str) -> list[dict]:
    nodes: list[dict] = []
    for raw in re.findall(
        r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>',
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        value = json.loads(raw)
        if isinstance(value, dict):
            nodes.append(value)
    return nodes


class AuthorityProfileTrustTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = json.loads((ROOT / "data" / "site-facts.json").read_text(encoding="utf-8"))
        sitemap_source = (ROOT / "sitemap.xml").read_text(encoding="utf-8") + (ROOT / "sitemap-es.xml").read_text(encoding="utf-8")
        cls.sitemap_paths = {
            urlsplit(url).path.rstrip("/") or "/"
            for url in re.findall(r"<loc>(https://thejorgeramirezgroup\.com[^<]+)</loc>", sitemap_source)
        }
        cls.redirect_sources = {
            item["source"]
            for item in json.loads((ROOT / "vercel.json").read_text(encoding="utf-8")).get("redirects", [])
            if not item.get("has")
            and not item.get("missing")
            and not re.search(r"[:*]", item.get("source", ""))
        }

    def test_pages_use_verified_identity_copy_and_sources(self) -> None:
        for relative in PAGES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            lowered = text.lower()
            self.assertIn("1754604", text, relative)
            self.assertIn("2017", text, relative)
            self.assertIn("somerset", lowered, relative)
            self.assertIn("https://www16.state.nj.us/DOBI_LicSearch/recSearch.jsp", text, relative)
            self.assertIn("https://kscore.kw.com/enroll/", text, relative)

    def test_self_serving_rating_markup_and_unverified_claims_are_absent(self) -> None:
        forbidden = (
            "aggregaterating",
            '"@type": "review"',
            "reviewrating",
            "5.0 on google",
            "5.0 en google",
            "12 reviews",
            "12 reseñas",
            "ai authority",
            "agente inmobiliario con ia",
            "ai retargeting",
            "retargeting con ia",
            "top dollar",
            "mejor precio posible",
            "top real estate agent",
            "miembro nahrep",
            "138 comunidades",
        )
        for relative in PAGES:
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, text, f"{relative}: {phrase}")

    def test_profile_schema_is_factual_and_has_six_counties(self) -> None:
        for relative in PAGES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            nodes = jsonld_nodes(text)
            people = [node for node in nodes if node.get("@type") == "Person"]
            self.assertEqual(1, len(people), relative)
            person = people[0]
            self.assertEqual(PERSON_ID, person["@id"], relative)
            self.assertEqual("1754604", person["hasCredential"]["identifier"], relative)
            self.assertEqual(6, len(person["areaServed"]), relative)
            self.assertNotIn("aggregateRating", person, relative)
            self.assertNotIn("review", person, relative)

    def test_pages_keep_one_main_landmark_and_homepage_brand_tokens(self) -> None:
        for relative in PAGES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(1, len(re.findall(r"<main(?:\s|>)", text, re.I)), relative)
            self.assertEqual(1, text.lower().count("</main>"), relative)
            self.assertRegex(text, r'<main\s+id="main"', relative)
            for token in ("#1A1A1A", "#C41230", "#B8962E", "#FAFAF8", "Playfair Display", "Inter"):
                self.assertIn(token, text, f"{relative}: missing {token}")

    def test_town_discovery_is_limited_to_the_canonical_inventory(self) -> None:
        inventory = self.facts["canonicalTownInventory"]["byCounty"]
        order = ("Union", "Morris", "Essex", "Hudson", "Middlesex", "Somerset")
        configs = {
            "ai-authority.html": (
                "<!-- TOWN PAGES: ORGANIZED BY COUNTY -->",
                '<section class="content-section alt-bg" id="town-comparisons">',
                "/towns/",
            ),
            "es/ai-authority.html": (
                "<!-- PÁGINAS DE CIUDADES POR CONDADO -->",
                '<section class="content-section alt-bg" id="comparaciones">',
                "/es/towns/",
            ),
        }
        for relative, (start_marker, end_marker, prefix) in configs.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            section = source[source.index(start_marker) : source.index(end_marker)]
            grids = re.findall(
                r'<div\s+class="town-links">(.*?)</div>', section, re.I | re.S
            )
            self.assertEqual(6, len(grids), relative)
            all_paths: list[str] = []
            for county, grid in zip(order, grids):
                actual = re.findall(r'href=["\']([^"\']+)["\']', grid)
                expected = [prefix + slug for slug in inventory[county]]
                self.assertEqual(expected, actual, f"{relative}: {county}")
                all_paths.extend(actual)
            self.assertEqual(self.facts["canonicalTownInventory"]["total"], len(all_paths))
            self.assertEqual(len(all_paths), len(set(all_paths)))

    def test_every_internal_authority_link_is_direct_indexable_and_canonical(self) -> None:
        current_paths = {
            "ai-authority.html": "/ai-authority",
            "es/ai-authority.html": "/es/ai-authority",
        }
        for relative, current_path in current_paths.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            for href in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']', source, re.I):
                if href.startswith(("tel:", "mailto:", "http://", "https://")):
                    continue
                parsed = urlsplit(urljoin(f"{ORIGIN}{current_path}", href))
                path = parsed.path.rstrip("/") or "/"
                with self.subTest(relative=relative, href=href):
                    self.assertNotIn(path, self.redirect_sources)
                    self.assertIn(path, self.sitemap_paths)
                    clean = path.strip("/")
                    candidates = (
                        [ROOT / "index.html"]
                        if not clean
                        else [ROOT / f"{clean}.html", ROOT / clean / "index.html"]
                    )
                    target = next((candidate for candidate in candidates if candidate.is_file()), None)
                    self.assertIsNotNone(target)
                    html = target.read_text(encoding="utf-8")
                    self.assertNotRegex(html, r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex')
                    self.assertNotRegex(html, r'<meta\b[^>]*http-equiv=["\']refresh["\']')
                    canonical = re.search(
                        r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)',
                        html,
                        re.I,
                    )
                    self.assertIsNotNone(canonical)
                    canonical_path = urlsplit(canonical.group(1)).path.rstrip("/") or "/"
                    self.assertEqual(path, canonical_path)

    def test_authority_hub_synchronizer_has_no_drift(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "sync_ai_authority_hubs.py"), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
