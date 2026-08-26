#!/usr/bin/env python3
"""Guard custom navigation from the global homepage ``nav`` selector."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NestedNavigationIsolationTests(unittest.TestCase):
    def test_county_directory_header_and_breadcrumb_are_explicitly_scoped(self) -> None:
        source = (ROOT / "counties" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<body class="county-index-page">', source)
        self.assertIn(
            ".county-index-page > header > nav { position:static; top:auto; "
            "z-index:auto;",
            source,
        )
        self.assertIn(
            '.county-index-page main > nav[aria-label="Breadcrumb"] { '
            "position:static; top:auto; z-index:auto;",
            source,
        )
        for reset in (
            "padding:0",
            "background:transparent",
            "backdrop-filter:none",
            "box-shadow:none",
            "transition:none",
        ):
            self.assertGreaterEqual(source.count(reset), 2, reset)

    def test_county_directory_uses_the_homepage_visual_system(self) -> None:
        source = (ROOT / "counties" / "index.html").read_text(encoding="utf-8")
        for token in (
            "#0A0A0A",
            "#1A1A1A",
            "#C41230",
            "#8B0D22",
            "#B8962E",
            "#D4AF5A",
            "#FAFAF8",
            "'Playfair Display'",
            "'Inter'",
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
