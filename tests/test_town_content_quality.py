#!/usr/bin/env python3
"""Regression tests for scaled and unsupported town-guide content."""

from __future__ import annotations

import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.check_town_content_quality import (
    TownPage,
    blocking_issues,
    fold_gsc_page_rows,
    near_duplicate_groups,
    scan_town_pages,
)


HIGH_RISK_SLUGS = {
    "cranbury",
    "montville",
    "pequannock-township",
    "roseland",
    "south-river",
    "warren-township",
    "watchung",
    "west-caldwell",
    "winfield",
}
UNSUPPORTED_TOWN_BOILERPLATE = re.compile(
    r"(?:"
    r"helped\s+hundreds|"
    r"healthy\s+inventory|"
    r"active\s+development\s+pipeline|"
    r"reliable\s+returns|"
    r"best\s+(?:neighborhood\s+)?for\s+families|"
    r"he\s+ayudado\s+a\s+cientos|"
    r"inventario\s+saludable|"
    r"niveles\s+de\s+inventario\s+saludables|"
    r"(?:proyectos?|canal)\s+de\s+desarrollo\s+activ|"
    r"rendimientos\s+confiables|"
    r"mejor\s+(?:vecindario\s+)?para\s+(?:las\s+)?familias"
    r")",
    re.IGNORECASE,
)


def is_noindex(source: str) -> bool:
    robots = re.findall(
        r'<meta\b[^>]*\bname=["\']robots["\'][^>]*>', source, flags=re.IGNORECASE
    )
    return any(re.search(r'\bcontent=["\'][^"\']*\bnoindex\b', tag, re.I) for tag in robots)


def sitemap_urls(name: str) -> set[str]:
    root = ET.parse(ROOT / name).getroot()
    return {(node.text or "").strip() for node in root.findall("{*}url/{*}loc")}


class TownContentQualityTests(unittest.TestCase):
    def test_gsc_impact_folds_clean_html_and_trailing_slash_variants(self) -> None:
        rows = [
            {
                "Top pages": "https://thejorgeramirezgroup.com/towns/cranbury",
                "Last 3 months Clicks": "1",
                "Last 3 months Impressions": "4",
                "Last 3 months Position": "10",
            },
            {
                "Top pages": "https://thejorgeramirezgroup.com/towns/cranbury.html",
                "Last 3 months Clicks": "0",
                "Last 3 months Impressions": "7",
                "Last 3 months Position": "20",
            },
            {
                "Top pages": "https://thejorgeramirezgroup.com/towns/cranbury/",
                "Last 3 months Clicks": "2",
                "Last 3 months Impressions": "3",
                "Last 3 months Position": "30",
            },
            {
                "Top pages": "https://thejorgeramirezgroup.com/es/towns/cranbury.html",
                "Last 3 months Clicks": "0",
                "Last 3 months Impressions": "2",
                "Last 3 months Position": "5",
            },
        ]

        folded = fold_gsc_page_rows(rows, {"cranbury"})

        self.assertEqual(3, folded["/towns/cranbury"]["clicks"])
        self.assertEqual(14, folded["/towns/cranbury"]["impressions"])
        self.assertAlmostEqual(270 / 14, folded["/towns/cranbury"]["position"], places=3)
        self.assertEqual(2, folded["/es/towns/cranbury"]["impressions"])

    def test_detector_finds_town_swapped_near_exact_pages(self) -> None:
        shared = " ".join(
            f"verified local sentence number {number} with practical buyer context"
            for number in range(80)
        )
        montville = TownPage.from_source(
            ROOT / "towns" / "montville.html",
            f"<main><p>Montville {shared}</p></main>",
        )
        roseland = TownPage.from_source(
            ROOT / "towns" / "roseland.html",
            f"<main><p>Roseland {shared}</p></main>",
        )

        groups = near_duplicate_groups(
            [montville, roseland], threshold=0.98, minimum_words=100
        )

        self.assertEqual(
            [["towns/montville.html", "towns/roseland.html"]],
            [[str(page.path.relative_to(ROOT)) for page in group] for group in groups],
        )

    def test_gate_rejects_unsupported_indexable_boilerplate(self) -> None:
        page = TownPage.from_source(
            ROOT / "towns" / "example.html",
            "<main><p>I've helped hundreds of families. The town maintains healthy inventory."
            " Historical appreciation demonstrates reliable returns.</p></main>",
        )

        issues = blocking_issues([page])

        self.assertEqual(1, len(issues))
        self.assertIn("helped hundreds", issues[0])
        self.assertIn("healthy inventory", issues[0])
        self.assertIn("reliable returns", issues[0])

    def test_live_indexable_long_form_guides_pass_the_quality_gate(self) -> None:
        pages = scan_town_pages(ROOT)
        self.assertEqual([], blocking_issues(pages))

    def test_high_risk_scaled_guides_are_quarantined(self) -> None:
        english_urls = sitemap_urls("sitemap.xml")
        spanish_urls = sitemap_urls("sitemap-es.xml")

        failures: list[str] = []
        for slug in sorted(HIGH_RISK_SLUGS):
            for language, prefix in (("en", ""), ("es", "es/")):
                relative = f"{prefix}towns/{slug}.html"
                source = (ROOT / relative).read_text(encoding="utf-8")
                if not is_noindex(source):
                    failures.append(f"{relative}: missing noindex")
                if re.search(r'<link\b[^>]*\bhreflang=["\']', source, re.I):
                    failures.append(f"{relative}: still publishes hreflang")

                url = f"https://thejorgeramirezgroup.com/{prefix}towns/{slug}"
                submitted = spanish_urls if language == "es" else english_urls
                if url in submitted:
                    failures.append(f"{relative}: still submitted in sitemap")

        self.assertEqual([], failures)

    def test_unsupported_boilerplate_is_never_indexable(self) -> None:
        failures: list[str] = []
        paths = [
            *sorted((ROOT / "towns").glob("*.html")),
            *sorted((ROOT / "es" / "towns").glob("*.html")),
        ]
        for path in paths:
            source = path.read_text(encoding="utf-8", errors="replace")
            if is_noindex(source):
                continue
            matches = sorted(
                {match.group(0).lower() for match in UNSUPPORTED_TOWN_BOILERPLATE.finditer(source)}
            )
            if matches:
                failures.append(f"{path.relative_to(ROOT)}: {', '.join(matches)}")
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
