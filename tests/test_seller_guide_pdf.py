#!/usr/bin/env python3
"""Fail-closed content, design, and reproducibility checks for the seller PDF."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "guides" / "nj-home-seller-guide.pdf"
GENERATOR = ROOT / "tools" / "generate_seller_guide_pdf.py"
EXPECTED_PAGES = 11


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)


class SellerGuidePdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.info = run("pdfinfo", str(PDF)).stdout
        cls.text = run("pdftotext", "-layout", str(PDF), "-").stdout

    def test_pdf_metadata_page_count_and_letter_size(self) -> None:
        self.assertRegex(self.info, r"(?m)^Title:\s+NJ Home Seller Planning Guide\s*$")
        self.assertRegex(
            self.info,
            r"(?m)^Author:\s+The Jorge Ramirez Group\s*$",
        )
        self.assertRegex(self.info, rf"(?m)^Pages:\s+{EXPECTED_PAGES}\s*$")
        self.assertRegex(self.info, r"(?m)^Page size:\s+612 x 792 pts \(letter\)\s*$")
        self.assertRegex(self.info, r"(?m)^Encrypted:\s+no\s*$")

    def test_pdf_uses_only_verified_identity_and_current_primary_sources(self) -> None:
        normalized = re.sub(r"\s+", " ", self.text)
        required = (
            "NJ real estate salesperson #1754604",
            "Full-time Realtor with Keller Williams Premier Properties since 2017",
            "NJDOBI Bulletin 24-11",
            "fully negotiable and not set by law",
            "Seller's Property Condition Disclosure Statement",
            "effective April 20, 2026",
            "NJDEP Flood Risk Notification",
            "NJ Division of Taxation - Realty Transfer Fee",
            "NJ Division of Taxation - GIT/REP FAQs",
            "General educational information",
            "908-230-7844",
            "jorge.ramirez@kw.com",
            "thejorgeramirezgroup.com/home-valuation",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, normalized)

        for url in (
            "https://www.nj.gov/dobi/bulletins/blt24_11.pdf",
            "https://www.njconsumeraffairs.gov/ocp/Pages/regulations.aspx",
            "https://dep.nj.gov/flooddisclosure/",
            "https://www.nj.gov/treasury/taxation/realty.shtml",
            "https://www.nj.gov/treasury/taxation/gitrepfaqs.shtml",
        ):
            with self.subTest(url=url):
                self.assertIn(url, normalized)

    def test_pdf_rejects_old_biography_outcome_timing_and_cost_claims(self) -> None:
        normalized = re.sub(r"\s+", " ", self.text).lower()
        banned = (
            r"buying and renovating homes myself",
            r"\b(?:investor|flipper|landlord)\b",
            r"\b10\s*(?:-|to)\s*14\s+days\b",
            r"usually landing below",
            r"two to three times",
            r"routinely returns",
            r"almost every buyer",
            r"first 8 seconds",
            r"spring is .*strongest",
            r"several percent",
            r"\b30\s*%",
            r"attorney fee",
            r"attorney-review",
            r"exit tax",
            r"no surprises",
            r"walk away",
            r"top dollar",
            r"\bguarantee(?:d|s)?\b",
            r"\broi\b",
            r"\$\s*\d",
        )
        for pattern in banned:
            with self.subTest(pattern=pattern):
                self.assertNotRegex(normalized, pattern)

    def test_generator_is_byte_deterministic_and_matches_committed_pdf(self) -> None:
        checked = run(sys.executable, str(GENERATOR), "--check")
        self.assertIn("seller guide is current and deterministic", checked.stdout)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "seller-guide.pdf"
            run(sys.executable, str(GENERATOR), "--output", str(output))
            self.assertEqual(
                hashlib.sha256(PDF.read_bytes()).hexdigest(),
                hashlib.sha256(output.read_bytes()).hexdigest(),
            )

    def test_check_fails_closed_for_stale_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "seller-guide.pdf"
            output.write_bytes(PDF.read_bytes() + b"stale")
            checked = subprocess.run(
                [sys.executable, str(GENERATOR), "--output", str(output), "--check"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, checked.returncode)
            self.assertIn("seller guide is stale", checked.stderr)

    def test_every_page_renders_and_cover_contains_brand_palette(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / "seller-guide"
            run("pdftoppm", "-png", "-r", "72", str(PDF), str(prefix))
            pages = sorted(Path(temp).glob("seller-guide-*.png"))
            self.assertEqual(EXPECTED_PAGES, len(pages))
            for page in pages:
                with self.subTest(page=page.name):
                    with Image.open(page) as image:
                        self.assertEqual((612, 792), image.size)
                        self.assertGreater(len(image.convert("RGB").getcolors(maxcolors=1_000_000) or []), 20)

            # Content-page running furniture must remain in its safe margins.
            # This catches the former alternating-page defect where a missing
            # left header, top-edge right label, and clipped footer could make
            # a page look vertically shifted even though its MediaBox was valid.
            with Image.open(pages[1]).convert("RGB") as reference:
                invariant_top_left = reference.crop((0, 0, 390, 42)).tobytes()
                invariant_bottom_left = reference.crop((0, 748, 410, 792)).tobytes()

            for page in pages[1:]:
                with self.subTest(page=page.name, check="running-header-footer-geometry"):
                    with Image.open(page).convert("RGB") as image:
                        def count_near(box, target, tolerance=18):
                            return sum(
                                1
                                for pixel in image.crop(box).getdata()
                                if max(abs(pixel[index] - target[index]) for index in range(3)) <= tolerance
                            )

                        def count_nonbackground(box):
                            return sum(
                                1
                                for pixel in image.crop(box).getdata()
                                if max(pixel) < 245
                            )

                        self.assertEqual(
                            invariant_top_left,
                            image.crop((0, 0, 390, 42)).tobytes(),
                            "invariant left header or gold rule was covered or shifted",
                        )
                        self.assertEqual(
                            invariant_bottom_left,
                            image.crop((0, 748, 410, 792)).tobytes(),
                            "invariant left footer or footer rule was covered or shifted",
                        )
                        early_flow_pixels = image.crop((45, 39, 400, 50)).getdata()
                        self.assertTrue(
                            all(max(abs(pixel[index] - (250, 250, 248)[index]) for index in range(3)) <= 2 for pixel in early_flow_pixels),
                            "flow content painted above the safe content boundary",
                        )
                        self.assertGreater(count_nonbackground((400, 17, 568, 31)), 100)
                        self.assertGreater(count_near((45, 34, 567, 37), (184, 150, 46)), 400)
                        self.assertGreater(count_nonbackground((495, 758, 568, 775)), 70)

            with Image.open(pages[0]).convert("RGB") as cover:
                pixels = list(cover.getdata())
                expected = {
                    "ink": (26, 26, 26),
                    "deep red": (196, 18, 48),
                    "gold": (184, 150, 46),
                    "ivory": (250, 250, 248),
                }
                for label, rgb in expected.items():
                    with self.subTest(color=label):
                        count = sum(
                            1
                            for pixel in pixels
                            if max(abs(pixel[index] - rgb[index]) for index in range(3)) <= 3
                        )
                        self.assertGreater(count, 30, f"{label} missing from rendered cover")

    def test_generator_declares_homepage_fonts_palette_logo_and_stable_page_count(self) -> None:
        source = GENERATOR.read_text(encoding="utf-8")
        for token in (
            "#1A1A1A",
            "#C41230",
            "#B8962E",
            "#FAFAF8",
            "Inter-Regular.ttf",
            "Inter-SemiBold.ttf",
            "PlayfairDisplay-SemiBold.ttf",
            "PlayfairDisplay-Bold.ttf",
            'LOGO = ROOT / "images" / "jorge-logo.jpg"',
            f"PAGE_COUNT = {EXPECTED_PAGES}",
            'kwargs["invariant"] = 1',
        ):
            with self.subTest(token=token):
                self.assertIn(token, source)

    def test_pricing_worksheet_uses_distinct_decision_questions(self) -> None:
        source = GENERATOR.read_text(encoding="utf-8")
        self.assertNotIn("Which comparable is most similar, and why?", source)
        self.assertEqual(
            1,
            source.count("Which data date or property difference could change the price range?"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
