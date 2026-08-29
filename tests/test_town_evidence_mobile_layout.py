#!/usr/bin/env python3
"""Regression contract for narrow town-guide navigation layouts."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "css" / "town-evidence-guide.css"
REPRESENTATIVE_PAGES = (
    "towns/summit.html",
    "towns/orange.html",
    "es/towns/summit.html",
    "es/towns/orange.html",
)


class TownEvidenceMobileLayoutTests(unittest.TestCase):
    def test_narrow_navigation_wraps_all_links_instead_of_hiding_them(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        mobile = css[css.index("@media (max-width: 640px)") :]

        self.assertRegex(
            mobile,
            r"\.town-guide__nav-inner\s*\{[^}]*flex-direction:\s*column;",
        )
        self.assertRegex(
            mobile,
            r"\.town-guide__nav-inner\s*\{[^}]*"
            r"width:\s*min\(1160px,\s*calc\(100% - 24px\)\);",
        )
        self.assertRegex(
            mobile,
            r"\.town-guide__nav-links\s*\{[^}]*flex-wrap:\s*wrap;",
        )
        self.assertRegex(
            mobile,
            r"\.town-guide__nav-links\s*\{[^}]*justify-content:\s*center;",
        )
        self.assertNotRegex(
            mobile,
            r"\.town-guide__nav-links\s+li:first-child\s*\{[^}]*display:\s*none;",
        )
        self.assertRegex(
            css,
            r"\.town-guide__nav-links a\s*\{[^}]*min-height:\s*44px;",
        )

    def test_representative_english_and_spanish_pages_use_shared_layout(self) -> None:
        for relative in REPRESENTATIVE_PAGES:
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn('/css/town-evidence-guide.css', source)
                self.assertIn('class="town-guide__nav-inner"', source)
                self.assertIn('class="town-guide__nav-links"', source)
                self.assertRegex(source, r'<nav\b[^>]*aria-label="[^"]+"')

    def test_verified_agent_panel_stacks_cleanly_on_small_screens(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        mobile = css[css.index("@media (max-width: 640px)") :]
        self.assertRegex(
            css,
            r"\.town-guide__agent-card\s*\{[^}]*display:\s*grid;[^}]*"
            r"grid-template-columns:\s*minmax\(0,\s*180px\)\s+minmax\(0,\s*1fr\);",
        )
        self.assertRegex(
            mobile,
            r"\.town-guide__agent-card\s*\{[^}]*grid-template-columns:\s*1fr;",
        )
        self.assertRegex(
            css,
            r"\.town-guide__agent-links a\s*\{[^}]*min-height:\s*44px;",
        )


if __name__ == "__main__":
    unittest.main()
