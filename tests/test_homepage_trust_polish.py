#!/usr/bin/env python3
"""Homepage-only trust, attribution, and touch-target regression checks."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = ROOT / "index.html"


class HomepageTrustPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = HOMEPAGE.read_text(encoding="utf-8")

    def test_unsupported_service_claims_are_absent(self) -> None:
        forbidden = (
            "i work 7 days a week",
            "available 7 days a week",
            "nyc commuter market specialist",
            "ai-powered",
            "ai powered",
            "knows this market cold",
            "invests here himself",
            "personally bought, renovated, and sold",
            "hands-on investor experience",
            "hands-on renovation &amp; investment experience",
            "hands-on experience on multiple sides of the table",
            "like an investor would",
            "bought and sold homes across nj as an investor",
            "known investor eye",
            "24–48 hours",
            "only on this site",
            "every nj commuter town",
            "no other nj agent",
            "42 sold homes",
            "public record · verified",
            "competitive-market win",
            "priced right from day one",
            "right school district",
            "without overpaying",
            "most sellers leave money on the table",
            "most agents get at least one",
            "almost always fixable",
            "many fsbo sellers end up",
            "the best homes in nj never",
            "12 other offers",
            "you won't overpay",
            "the #1 reason sellers",
            "many of my best results",
            "5.2%",
            "60–90 days",
            "mandatory 3-business-day",
            "2–3x faster",
            "$1,095,000",
            "10–20%",
            "5–13% more",
            "most nj real estate attorneys recommend",
            "best nj towns for families",
        )

        homepage = self.source.lower()
        present = [claim for claim in forbidden if claim in homepage]
        self.assertEqual([], present)
        self.assertIn("Here are the facts:", self.source)
        self.assertNotIn("What I can verify is", self.source)

    def test_market_and_transaction_copy_is_durable_and_attributed(self) -> None:
        self.assertIn("Third-Party Profile Snapshot", self.source)
        self.assertIn("Third-party profile data can change", self.source)
        self.assertIn("Reference tool · Not a live NJ Transit feed", self.source)
        self.assertIn("There is no universal best month", self.source)
        self.assertIn("brokerage compensation, which is negotiable and not set by law", self.source)
        self.assertIn("https://www.nj.gov/treasury/taxation/realty.shtml", self.source)
        self.assertNotIn("thejorgeramirezgroup.com/home-valuation.html", self.source)

    def test_homepage_design_tokens_remain_unchanged(self) -> None:
        for token in (
            "--primary-red:#C41230",
            "--dark-red:#8B0D22",
            "--gold:#B8962E",
            "--gold-light:#D4AF5A",
            "--black:#000000",
            "--light-gray:#F8F6F2",
            "--font-display:'Playfair Display'",
            "--font-body:'Inter'",
        ):
            self.assertIn(token, self.source)

    def test_search_and_social_titles_are_brand_first_and_consistent(self) -> None:
        expected = "Jorge Ramirez, NJ Realtor | The Jorge Ramirez Group"
        self.assertIn(f"<title>{expected}</title>", self.source)
        self.assertIn(f'<meta name="title" content="{expected}">', self.source)
        self.assertIn(f'<meta property="og:title" content="{expected}">', self.source)
        self.assertIn(f'<meta property="twitter:title" content="{expected}">', self.source)
        self.assertLessEqual(len(expected), 60)
        for county in ("Union", "Essex", "Morris", "Hudson", "Middlesex", "Somerset"):
            self.assertIn(county, self.source.split('<meta name="description"', 1)[1].split(">", 1)[0])

    def test_town_guide_copy_uses_durable_six_county_language(self) -> None:
        self.assertNotRegex(self.source, r"\b112\b")
        self.assertIn("Local Guides Across Six New Jersey Counties", self.source)
        self.assertIn("Explore Local NJ Town Guides", self.source)

    def test_testimonials_do_not_claim_an_unverified_platform_source(self) -> None:
        self.assertNotRegex(self.source, re.compile(r"Google Reviews?", re.IGNORECASE))
        self.assertNotIn("See All Reviews on Zillow", self.source)
        self.assertEqual(5, self.source.count(">Client testimonial</div>"))
        self.assertIn("Visit Jorge's Zillow Profile", self.source)

    def test_every_resource_link_has_a_44_pixel_touch_target(self) -> None:
        self.assertRegex(
            self.source,
            re.compile(
                r"\.resource-card\s+a\s*\{[^}]*"
                r"display\s*:\s*inline-flex\s*;[^}]*"
                r"align-items\s*:\s*center\s*;[^}]*"
                r"min-height\s*:\s*44px\s*;",
                re.IGNORECASE | re.DOTALL,
            ),
        )
        self.assertIn(
            '<a href="/communities" class="resource-link">Explore Towns →</a>',
            self.source,
        )

    def test_town_guide_card_uses_durable_source_language(self) -> None:
        self.assertIn(
            "Start with local housing context and links to municipal, transit, and school resources.",
            self.source,
        )
        self.assertNotIn(
            "Schools, property taxes, commute times, median prices, and neighborhood feel",
            self.source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
