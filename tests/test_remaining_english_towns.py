import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "remaining-english-town-guides.json"


class RemainingEnglishTownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_exact_scope_and_renderer(self):
        self.assertEqual(set(self.data["pages"]), {"middlesex", "woodbridge", "orange", "helmetta"})
        result = subprocess.run(
            ["python3", "scripts/render_remaining_english_towns.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pages_are_indexable_reciprocal_source_guides(self):
        for slug, item in self.data["pages"].items():
            text = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            self.assertIn('name="robots" content="index, follow', text)
            self.assertIn(f'<link rel="canonical" href="https://thejorgeramirezgroup.com/towns/{slug}">', text)
            self.assertIn(f'hreflang="es-US" href="https://thejorgeramirezgroup.com/es/towns/{slug}"', text)
            self.assertIn('/css/town-evidence-guide.css', text)
            self.assertIn('data-source-review="2026-08-26"', text)
            self.assertIn(item["municipal_url"], text)
            self.assertIn(item["record_url"], text)
            for source in self.data["shared_sources"]:
                self.assertIn(source["url"], text)

    def test_legacy_claims_are_absent(self):
        banned = [
            "top dollar", "ai-powered", "right home", "sought-after",
            "great schools", "best schools", "safe neighborhood",
            "proven process", "maximize exposure", "price premium",
        ]
        for slug in self.data["pages"]:
            text = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8").lower()
            for phrase in banned:
                self.assertNotIn(phrase, text, f"{phrase} in towns/{slug}.html")

    def test_spanish_counterparts_remain_reciprocal(self):
        for slug in self.data["pages"]:
            text = (ROOT / "es" / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            self.assertIn(f'hreflang="en-US" href="https://thejorgeramirezgroup.com/towns/{slug}"', text)
            self.assertIn(f'<link rel="canonical" href="https://thejorgeramirezgroup.com/es/towns/{slug}">', text)


if __name__ == "__main__":
    unittest.main()
