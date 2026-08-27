#!/usr/bin/env python3
"""Regression contract for context-aware community capitalization rewrites."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.normalize_public_trust_claims import normalize


ROOT = Path(__file__).resolve().parents[1]
DOWNSIZING = ROOT / "es" / "downsizing-nj.html"
MOVING_GUIDE = ROOT / "es" / "blog" / "moving-from-nyc-to-nj-guide.html"


class PublicTrustNormalizerCasingTests(unittest.TestCase):
    def test_english_inline_anchor_phrase_stays_lowercase(self) -> None:
        original = (
            '<p>Jorge serves <a href="/communities">'
            'communities across six New Jersey counties</a>.</p>'
        )

        normalized, replacements = normalize(original, "fixture.html")

        self.assertEqual(original, normalized)
        self.assertEqual(0, replacements)

    def test_english_numeric_claim_casing_is_structural_and_idempotent(self) -> None:
        original = (
            '<p>138 communities served across six counties.</p>\n'
            '<h2>138 communities across New Jersey</h2>\n'
            '<label>138 communities</label>\n'
            '<p>All 138 communities are represented.</p>\n'
            '<h3>All 138 NJ communities</h3>\n'
            '<label>All 138 communities</label>\n'
            '<div>138 communities with published guides</div>\n'
            '<span class="stat-label">138 communities</span>\n'
            '<p>Jorge serves <a href="/communities">'
            '138 communities across six counties</a>.</p>\n'
            '<p>Jorge serves <a href="/communities">'
            'all 138 communities</a>.</p>\n'
            '<nav><a href="/communities">Communities</a></nav>'
        )

        normalized, replacements = normalize(original, "fixture.html")
        normalized_again, second_replacements = normalize(normalized, "fixture.html")

        self.assertEqual(10, replacements)
        self.assertIn("<p>Communities served across six counties.</p>", normalized)
        self.assertIn("<h2>Communities across New Jersey</h2>", normalized)
        self.assertIn("<label>Communities</label>", normalized)
        self.assertIn(
            "<p>Communities across six New Jersey counties are represented.</p>",
            normalized,
        )
        self.assertIn(
            "<h3>Communities across six New Jersey counties</h3>", normalized
        )
        self.assertIn(
            "<label>Communities across six New Jersey counties</label>", normalized
        )
        self.assertIn("<div>communities with published guides</div>", normalized)
        self.assertIn('<span class="stat-label">communities</span>', normalized)
        self.assertIn(
            '<p>Jorge serves <a href="/communities">'
            'communities across six counties</a>.</p>',
            normalized,
        )
        self.assertIn(
            '<p>Jorge serves <a href="/communities">'
            'communities across six New Jersey counties</a>.</p>',
            normalized,
        )
        self.assertIn('<nav><a href="/communities">Communities</a></nav>', normalized)
        self.assertEqual(normalized, normalized_again)
        self.assertEqual(0, second_replacements)

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
            '<p>Todas las 138 comunidades están representadas.</p>\n'
            '<h2>Todas las 138 comunidades</h2>\n'
            '<label>Todas las 138 comunidades</label>\n'
            '<div>138 comunidades con guías</div>\n'
            '<span class="stat-label">138 comunidades</span>\n'
            '<p>Jorge atiende <a href="/es/communities">'
            '138 comunidades en seis condados</a>.</p>\n'
            '<p>Jorge atiende <a href="/es/communities">'
            'todas las 138 comunidades</a>.</p>\n'
            '<nav><a href="/es/communities">Comunidades</a></nav>'
        )

        normalized, replacements = normalize(original, "fixture.html")
        normalized_again, second_replacements = normalize(normalized, "fixture.html")

        self.assertEqual(9, replacements)
        self.assertIn("<p>Comunidades atendidas en seis condados.</p>", normalized)
        self.assertIn("<label>Comunidades</label>", normalized)
        self.assertIn(
            "<p>Comunidades en seis condados de Nueva Jersey están representadas.</p>",
            normalized,
        )
        self.assertIn(
            "<h2>Comunidades en seis condados de Nueva Jersey</h2>", normalized
        )
        self.assertIn(
            "<label>Comunidades en seis condados de Nueva Jersey</label>", normalized
        )
        self.assertIn("<div>comunidades con guías</div>", normalized)
        self.assertIn('<span class="stat-label">comunidades</span>', normalized)
        self.assertIn(
            '<p>Jorge atiende <a href="/es/communities">'
            'comunidades en seis condados</a>.</p>',
            normalized,
        )
        self.assertIn(
            '<p>Jorge atiende <a href="/es/communities">'
            'comunidades en seis condados de Nueva Jersey</a>.</p>',
            normalized,
        )
        self.assertIn('<nav><a href="/es/communities">Comunidades</a></nav>', normalized)
        self.assertEqual(normalized, normalized_again)
        self.assertEqual(0, second_replacements)


if __name__ == "__main__":
    unittest.main()
