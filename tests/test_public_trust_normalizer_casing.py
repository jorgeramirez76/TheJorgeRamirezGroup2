#!/usr/bin/env python3
"""Regression contract for context-aware Spanish capitalization rewrites."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.normalize_public_trust_claims import normalize


ROOT = Path(__file__).resolve().parents[1]
DOWNSIZING = ROOT / "es" / "downsizing-nj.html"
MOVING_GUIDE = ROOT / "es" / "blog" / "moving-from-nyc-to-nj-guide.html"


class PublicTrustNormalizerCasingTests(unittest.TestCase):
    def test_inline_anchor_phrase_stays_lowercase_and_page_is_idempotent(self) -> None:
        cases = (
            (
                DOWNSIZING,
                '<a href="/es/55-plus-communities-nj">'
                'comunidades para mayores de 55</a>',
            ),
            (
                MOVING_GUIDE,
                '<p>Jorge atiende <a href="/es#communities">'
                'comunidades en seis condados de NJ</a>',
            ),
        )

        for path, expected in cases:
            source = path.read_text(encoding="utf-8")
            relative = path.relative_to(ROOT).as_posix()
            normalized, replacements = normalize(source, relative)
            with self.subTest(relative=relative):
                self.assertIn(expected, source)
                self.assertEqual(source, normalized)
                self.assertEqual(0, replacements)

    def test_sentence_initial_and_standalone_ui_labels_are_capitalized(self) -> None:
        original = (
            '<p>138 comunidades atendidas en seis condados.</p>\n'
            '<label>138 comunidades</label>\n'
            '<div>138 comunidades con guías</div>\n'
            '<span class="stat-label">138 comunidades</span>\n'
            '<p>Jorge atiende <a href="/es/communities">'
            '138 comunidades en seis condados</a>.</p>\n'
            '<nav><a href="/es/communities">Comunidades</a></nav>'
        )

        normalized, replacements = normalize(original, "fixture.html")

        self.assertEqual(5, replacements)
        self.assertIn("<p>Comunidades atendidas en seis condados.</p>", normalized)
        self.assertIn("<label>Comunidades</label>", normalized)
        self.assertIn("<div>comunidades con guías</div>", normalized)
        self.assertIn('<span class="stat-label">comunidades</span>', normalized)
        self.assertIn(
            '<p>Jorge atiende <a href="/es/communities">'
            'comunidades en seis condados</a>.</p>',
            normalized,
        )
        self.assertIn('<nav><a href="/es/communities">Comunidades</a></nav>', normalized)


if __name__ == "__main__":
    unittest.main()
