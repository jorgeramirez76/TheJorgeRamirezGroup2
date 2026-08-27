#!/usr/bin/env python3
"""Regression contract for natural Spanish homepage identity copy."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.normalize_public_trust_claims import normalize


ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = ROOT / "es" / "index.html"
EYEBROW = "Agente inmobiliario con licencia en Nueva Jersey"
HEADSHOT_ALT = (
    "Jorge Ramirez, agente inmobiliario con licencia en Nueva Jersey "
    "para los condados de Union, Essex y Morris"
)


class SpanishHomepageEyebrowTests(unittest.TestCase):
    def test_homepage_uses_natural_identity_copy_without_doubled_location(self) -> None:
        source = HOMEPAGE.read_text(encoding="utf-8")
        eyebrow = re.search(
            r'<span class="hero-eyebrow">([^<]+)</span>',
            source,
        )
        headshot = re.search(
            r'<img src="/images/jorge-ramirez-headshot\.jpg" alt="([^"]+)"',
            source,
        )

        self.assertIsNotNone(eyebrow)
        self.assertIsNotNone(headshot)
        self.assertEqual(EYEBROW, eyebrow.group(1))
        self.assertEqual(HEADSHOT_ALT, headshot.group(1))
        self.assertNotIn("Nueva Jersey en NJ", source)
        self.assertNotIn("Nueva Jersey en los Condados", source)

        normalized, replacements = normalize(source, "es/index.html")
        self.assertEqual(source, normalized)
        self.assertEqual(0, replacements)

    def test_public_trust_normalizer_repairs_original_generated_copy_once(self) -> None:
        original = (
            '<span class="hero-eyebrow">Agente Inmobiliario Destacado en NJ</span>\n'
            '<img src="/images/jorge-ramirez-headshot.jpg" '
            'alt="Jorge Ramirez - Agente Inmobiliario Destacado en los Condados '
            'de Union, Essex y Morris en NJ">'
        )

        updated, replacements = normalize(original, "es/index.html")
        rerun, rerun_replacements = normalize(updated, "es/index.html")

        self.assertIn(f'<span class="hero-eyebrow">{EYEBROW}</span>', updated)
        self.assertIn(f'alt="{HEADSHOT_ALT}"', updated)
        self.assertGreaterEqual(replacements, 4)
        self.assertEqual(updated, rerun)
        self.assertEqual(0, rerun_replacements)


if __name__ == "__main__":
    unittest.main()
