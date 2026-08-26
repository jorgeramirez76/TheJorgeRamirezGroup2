import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "tools/commute-scorer.html", ROOT / "es/tools/commute-scorer.html"]


class CommuteComparisonTests(unittest.TestCase):
    def test_renderer_is_deterministic(self):
        result = subprocess.run(
            ["python3", "tools/render_commute_comparison.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pages_are_bilingual_indexable_counterparts(self):
        expected = {
            PAGES[0]: ("en", "https://thejorgeramirezgroup.com/tools/commute-scorer"),
            PAGES[1]: ("es", "https://thejorgeramirezgroup.com/es/tools/commute-scorer"),
        }
        for page, (language, canonical) in expected.items():
            text = page.read_text(encoding="utf-8")
            self.assertIn(f'<html lang="{language}">', text)
            self.assertIn(f'<link rel="canonical" href="{canonical}">', text)
            self.assertIn('hreflang="en-US"', text)
            self.assertIn('hreflang="es-US"', text)
            self.assertIn('name="robots" content="index, follow', text)
            self.assertIn('/js/commute-comparison.js', text)

    def test_tool_is_neutral_and_visitor_entered(self):
        banned = [
            "best town", "right town", "helped hundreds", "price premium",
            "top commuter towns", "ideal para familias", "mejores escuelas",
            "ahorra $", "10–15", "60 to 75 minutes", "multi-year waiting lists",
        ]
        for page in PAGES:
            lowered = page.read_text(encoding="utf-8").lower()
            for phrase in banned:
                self.assertNotIn(phrase.lower(), lowered, f"{phrase} in {page}")
            self.assertIn("data-commute-form", lowered)
            self.assertIn("data-field=\"scheduled_ride\"", lowered)
            self.assertIn("data-field=\"fare_tolls\"", lowered)

    def test_source_manifest_is_official_and_rendered(self):
        data = json.loads((ROOT / "data/commute-planner-sources.json").read_text(encoding="utf-8"))
        self.assertEqual(data["reviewed"], "2026-08-26")
        self.assertGreaterEqual(len(data["sources"]), 4)
        allowed_hosts = ("https://www.njtransit.com/", "https://www.panynj.gov/")
        page_text = "\n".join(page.read_text(encoding="utf-8") for page in PAGES)
        for source in data["sources"]:
            self.assertTrue(source["url"].startswith(allowed_hosts))
            self.assertIn(source["url"], page_text)
            for suffix in ("en", "es"):
                self.assertTrue(source[f"use_{suffix}"])
                self.assertTrue(source[f"limit_{suffix}"])

    def test_every_number_control_has_a_label(self):
        for page in PAGES:
            text = page.read_text(encoding="utf-8")
            ids = re.findall(r'<input id="([^"]+)"[^>]*type="number"', text)
            self.assertEqual(len(ids), 22)
            for field_id in ids:
                self.assertIn(f'<label for="{field_id}">', text)

    def test_breadcrumb_nav_cannot_inherit_the_global_fixed_nav(self):
        required_reset = (
            ".commute-page .breadcrumbs{position:static;top:auto;z-index:auto;"
            "width:auto;padding:0;background:transparent;backdrop-filter:none;"
            "box-shadow:none;transition:none"
        )
        for page in PAGES:
            self.assertIn(required_reset, page.read_text(encoding="utf-8"), page)


if __name__ == "__main__":
    unittest.main()
