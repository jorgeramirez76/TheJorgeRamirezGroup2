"""Trust and structured-data regression checks for the bilingual profile pages."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ("ai-authority.html", "es/ai-authority.html")


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
            agents = [node for node in nodes if node.get("@type") == "RealEstateAgent"]
            self.assertEqual(1, len(agents), relative)
            agent = agents[0]
            self.assertEqual("1754604", agent["hasCredential"]["identifier"], relative)
            self.assertEqual(6, len(agent["areaServed"]), relative)
            self.assertNotIn("aggregateRating", agent, relative)
            self.assertNotIn("review", agent, relative)

    def test_pages_keep_one_main_landmark_and_homepage_brand_tokens(self) -> None:
        for relative in PAGES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(1, len(re.findall(r"<main(?:\s|>)", text, re.I)), relative)
            self.assertEqual(1, text.lower().count("</main>"), relative)
            self.assertRegex(text, r'<main\s+id="main"', relative)
            for token in ("#1A1A1A", "#C41230", "#B8962E", "#FAFAF8", "Playfair Display", "Inter"):
                self.assertIn(token, text, f"{relative}: missing {token}")


if __name__ == "__main__":
    unittest.main()
