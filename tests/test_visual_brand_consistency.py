"""Focused regressions for homepage-aligned typography and blog resource links."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLOG_SOURCE = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")
VALUATION_SOURCE = (ROOT / "home-valuation.html").read_text(encoding="utf-8")
FONT_STYLESHEET = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
    "&family=Montserrat:wght@300;400;500;600;700"
    "&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400"
    "&display=swap"
)


def css_rule(source: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]*)\}}", source)
    if match is None:
        raise AssertionError(f"Missing CSS rule for {selector}")
    return match.group("body")


class VisualBrandConsistencyTests(unittest.TestCase):
    def test_blog_index_title_uses_the_display_type_token(self) -> None:
        self.assertIn(
            '<h1 class="blog-index-title">New Jersey Real Estate Blog</h1>',
            BLOG_SOURCE,
        )
        title_rule = css_rule(BLOG_SOURCE, ".blog-index-title")
        self.assertRegex(title_rule, r"font-family\s*:\s*var\(--font-display\b")

    def test_blog_index_loads_the_same_display_font_family_it_declares(self) -> None:
        self.assertIn('<link rel="preconnect" href="https://fonts.googleapis.com">', BLOG_SOURCE)
        self.assertIn(
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            BLOG_SOURCE,
        )
        self.assertIn(
            f'<link href="{FONT_STYLESHEET}" rel="stylesheet" media="print" '
            'onload="this.media=\'all\'">',
            BLOG_SOURCE,
        )
        self.assertIn(
            f'<noscript><link href="{FONT_STYLESHEET}" rel="stylesheet"></noscript>',
            BLOG_SOURCE,
        )

    def test_valuation_hero_title_uses_the_display_type_token(self) -> None:
        title_rule = css_rule(VALUATION_SOURCE, ".val-hero h1")
        self.assertRegex(title_rule, r"font-family\s*:\s*var\(--font-display\b")

    def test_blog_related_resource_ctas_use_accessible_brand_tokens(self) -> None:
        self.assertEqual(2, BLOG_SOURCE.count('class="related-resource-link"'))
        link_rule = css_rule(BLOG_SOURCE, ".related-links .related-resource-link")
        for contract in (
            r"display\s*:\s*inline-flex",
            r"align-items\s*:\s*center",
            r"min-height\s*:\s*44px",
            r"background\s*:\s*var\(--dark-red\b",
            r"color\s*:\s*var\(--white\b",
            r"border-radius\s*:\s*var\(--radius-pill\b",
        ):
            self.assertRegex(link_rule, contract)

    def test_blog_brokerage_disclosure_keeps_its_distinct_link_treatment(self) -> None:
        disclosure = re.search(
            r'<aside\b[^>]*aria-label="Real estate brokerage disclosure"[^>]*>'
            r"(?P<body>.*?)</aside>",
            BLOG_SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(disclosure)
        disclosure_body = disclosure.group("body")
        self.assertIn("color:#1a4f8b", disclosure_body)
        self.assertNotIn("related-resource-link", disclosure_body)


if __name__ == "__main__":
    unittest.main()
