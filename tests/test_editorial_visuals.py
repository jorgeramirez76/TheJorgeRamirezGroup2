"""Regression coverage for contextual imagery on long-form priority pages."""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "apply_editorial_visuals.py"
SPEC = importlib.util.spec_from_file_location("apply_editorial_visuals", TOOL_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load apply_editorial_visuals.py")
VISUALS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VISUALS)


class EditorialVisualTests(unittest.TestCase):
    def test_manifest_covers_the_reviewed_priority_surface(self) -> None:
        self.assertEqual(len(VISUALS.PAGE_VISUALS), 38)
        for required in (
            "blog/first-time-home-buyer-nj-guide.html",
            "es/blog/first-time-home-buyer-nj-guide.html",
            "blog/nj-property-tax-guide.html",
            "es/blog/nj-property-tax-guide.html",
            "home-valuation.html",
            "es/home-valuation.html",
            "sell-rental-property-nj.html",
            "es/sell-rental-property-nj.html",
        ):
            self.assertIn(required, VISUALS.PAGE_VISUALS)

    def test_every_manifest_page_has_one_responsive_contextual_visual(self) -> None:
        for relative, kind in VISUALS.PAGE_VISUALS.items():
            with self.subTest(page=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                base, height = VISUALS.ASSETS[kind]
                language = "es" if relative.startswith("es/") else "en"
                expected_alt = VISUALS.ALT[kind][language]

                self.assertEqual(source.count(VISUALS.START), 1)
                self.assertEqual(source.count(VISUALS.END), 1)
                self.assertEqual(source.count(f'data-editorial-visual="{kind}"'), 1)
                self.assertIn(
                    f'srcset="{base}-768.webp 768w, {base}-1280.webp 1280w"',
                    source,
                )
                self.assertIn(
                    f'<img src="{base}-1280.webp" width="1280" height="{height}" '
                    f'loading="lazy" decoding="async" alt="{expected_alt}">',
                    source,
                )
                self.assertNotRegex(
                    source,
                    rf'<img src="{re.escape(base)}-1280\.webp"[^>]*fetchpriority="high"',
                )

    def test_visual_release_dates_are_distinct_from_source_review_dates(self) -> None:
        for relative in VISUALS.PAGE_VISUALS:
            with self.subTest(page=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                modified = re.findall(
                    r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"', source
                )
                self.assertGreaterEqual(len(modified), 1)
                self.assertEqual({VISUALS.PAGE_MODIFIED_ON}, set(modified))
                for pattern in (
                    r'<meta\s+property="article:modified_time"\s+content="([^"]+)"',
                    r'<meta\s+name="last-updated"\s+content="([^"]+)"',
                ):
                    values = re.findall(pattern, source, flags=re.I)
                    if values:
                        self.assertEqual({VISUALS.PAGE_MODIFIED_ON}, set(values))

        for relative in (
            "sell-your-home.html",
            "es/sell-your-home.html",
            "sell-rental-property-nj.html",
            "es/sell-rental-property-nj.html",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('data-source-review="2026-08-26"', source)

    def test_referenced_assets_are_small_local_webp_files(self) -> None:
        for base, _ in set(VISUALS.ASSETS.values()):
            for width in (768, 1280):
                with self.subTest(asset=base, width=width):
                    path = ROOT / f"{base.lstrip('/')}-{width}.webp"
                    self.assertTrue(path.is_file(), path)
                    payload = path.read_bytes()
                    self.assertGreater(len(payload), 8_000)
                    self.assertLess(len(payload), 200_000)
                    self.assertEqual(payload[:4], b"RIFF")
                    self.assertEqual(payload[8:12], b"WEBP")

    def test_alt_text_is_descriptive_without_promotional_claims(self) -> None:
        for kind, translations in VISUALS.ALT.items():
            for language, alt in translations.items():
                with self.subTest(kind=kind, language=language):
                    self.assertGreaterEqual(len(alt.split()), 10)
                    self.assertLessEqual(len(alt.split()), 32)
                    self.assertNotRegex(alt.lower(), r"\b(best|mejor|guarantee|garantiz|luxury|lujo)\b")

    def test_global_figure_style_preserves_brand_and_mobile_containment(self) -> None:
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".jrg-editorial-figure", css)
        for token in ("#1A1A1A", "#8B0D22", "#C41230", "#B8962E"):
            self.assertIn(token, css)
        self.assertIn("aspect-ratio: 3 / 2", css)
        self.assertIn("width: calc(100% - 32px)", css)


if __name__ == "__main__":
    unittest.main()
