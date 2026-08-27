from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "tools" / "render_property_research_pages.py"
PAGES = (
    "property-search.html",
    "es/property-search.html",
    "tools/market-comparison-widget.html",
    "es/tools/market-comparison-widget.html",
)


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.main_ids: list[str] = []
        self.h1 = 0
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(str(values["id"]))
        if tag == "main" and values.get("id"):
            self.main_ids.append(str(values["id"]))
        if tag == "h1":
            self.h1 += 1


class PropertyResearchPageTests(unittest.TestCase):
    def test_renderer_is_current(self) -> None:
        result = subprocess.run([sys.executable, str(RENDERER), "--check"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_structure_brand_and_metadata(self) -> None:
        palette = {"#1A1A1A", "#0A0A0A", "#C41230", "#8B0D22", "#B8962E", "#D4AF5A", "#FAFAF8", "#F8F6F2", "#FFFFFF"}
        for relative in PAGES:
            source = (ROOT / relative).read_text(encoding="utf-8")
            parser = StructureParser()
            parser.feed(source)
            with self.subTest(relative=relative):
                self.assertEqual(["main"], parser.main_ids)
                self.assertEqual(1, parser.h1)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                self.assertTrue(palette.issubset(set(re.findall(r"#[0-9A-Fa-f]{6}", source))))
                self.assertIn("Playfair Display", source)
                self.assertIn("Inter", source)
                self.assertIn('rel="canonical"', source)
                self.assertIn('hreflang="en-US"', source)
                self.assertIn('hreflang="es-US"', source)
                for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S):
                    json.loads(block)

    def test_property_search_is_truthful_and_uses_official_sources(self) -> None:
        for relative in ("property-search.html", "es/property-search.html"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("https://thejorgeramirezgroup.kw.com/listings-search/?city=Summit", source)
            self.assertIn("https://thejorgeramirezgroup.kw.com/listings-search/?city=Westfield", source)
            for url in (
                "https://www.njtransit.com/trip-planner-to",
                "https://www.nj.gov/education/schoolperformance/",
                "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml",
                "https://msc.fema.gov/portal/home",
            ):
                self.assertIn(url, source)
            self.assertNotRegex(source, re.compile(r"15[–-]25%|top NJ Monthly|best town|premium 1|value play", re.I))

    def test_comparison_worksheet_has_only_blank_user_fields(self) -> None:
        for relative in ("tools/market-comparison-widget.html", "es/tools/market-comparison-widget.html"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(16, len(re.findall(r"<textarea\b", source)))
            self.assertEqual(0, len(re.findall(r"<textarea\b[^>]*>\s*[^<\s]", source)))
            self.assertNotIn("localStorage", source)
            self.assertNotRegex(source, re.compile(r"week or two|spring market|lower-rate town|every week|price per square foot corrects|auto-translated", re.I))


if __name__ == "__main__":
    unittest.main()
