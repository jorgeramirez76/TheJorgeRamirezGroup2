import json
import html
import re
import subprocess
import unittest
from itertools import combinations
from pathlib import Path

from tools.check_town_content_quality import normalized_main_text, shingles


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "remaining-english-town-guides.json"
SITE = "https://thejorgeramirezgroup.com"
QUICK_WIN_EXPECTATIONS = {
    "helmetta": {
        "title": "Helmetta NJ Real Estate Agent & Guide | Jorge Ramirez",
        "h1": "Helmetta NJ real estate guide for buyers and sellers",
        "phrases": (
            "Keep a Helmetta parcel tied to the Borough record",
            "Separate the Borough file from construction-code guidance",
            "Label every cross-municipality comparable",
        ),
    },
    "middlesex": {
        "title": "Middlesex Borough NJ Real Estate Agent | Jorge Ramirez",
        "h1": "Middlesex Borough NJ real estate guide for buyers and sellers",
        "phrases": (
            "Middlesex Borough is not Middlesex County",
            "Keep Borough assessment and permit questions in their proper records",
            "Do not blend countywide results into a Borough valuation",
        ),
    },
    "orange": {
        "title": "City of Orange Township NJ Real Estate | Jorge Ramirez",
        "h1": "City of Orange Township NJ real estate guide for buyers and sellers",
        "phrases": (
            "Use the City of Orange Township record",
            "Verify the approved unit count before relying on a multifamily label",
            "Planning a move in the City of Orange Township?",
        ),
    },
}


def schema_nodes(source: str) -> list[dict]:
    nodes: list[dict] = []
    for raw in re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source,
        re.I | re.S,
    ):
        payload = json.loads(raw)
        candidates = payload.get("@graph", [payload]) if isinstance(payload, dict) else []
        nodes.extend(node for node in candidates if isinstance(node, dict))
    return nodes


class RemainingEnglishTownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_exact_scope_and_renderer(self):
        self.assertEqual(set(self.data["pages"]), {"middlesex", "woodbridge", "orange", "helmetta"})
        self.assertEqual(
            set(QUICK_WIN_EXPECTATIONS),
            {
                slug
                for slug, item in self.data["pages"].items()
                if item.get("content_version") == "quick-win-v2"
            },
        )
        self.assertNotIn("content_version", self.data["pages"]["woodbridge"])
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
            expected_sources = item.get("sources", self.data["shared_sources"])
            for source in expected_sources:
                self.assertIn(source["url"], text)

    def test_quick_win_pages_are_distinct_source_supported_guides(self):
        for slug, expected in QUICK_WIN_EXPECTATIONS.items():
            text = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            item = self.data["pages"][slug]
            with self.subTest(slug=slug):
                self.assertIn('data-town-evidence-guide="quick-win-v2"', text)
                self.assertIn(f'<title>{html.escape(expected["title"])}</title>', text)
                self.assertIn(f'<h1 id="page-title">{expected["h1"]}</h1>', text)
                for phrase in expected["phrases"]:
                    self.assertIn(phrase, text)
                for source in item["sources"]:
                    self.assertIn(source["url"], text)
                self.assertNotIn("Planning a Orange", text)
                self.assertNotIn("Orange City Township", text)

    def test_quick_win_pages_publish_verified_business_provenance(self):
        business_id = f"{SITE}/#agent"
        person_id = f"{SITE}/#jorge-ramirez"
        for slug in QUICK_WIN_EXPECTATIONS:
            text = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            nodes = schema_nodes(text)
            web_pages = [node for node in nodes if node.get("@type") == "WebPage"]
            businesses = [
                node
                for node in nodes
                if node.get("@type") == "RealEstateAgent" and node.get("@id") == business_id
            ]
            people = [
                node
                for node in nodes
                if node.get("@type") == "Person" and node.get("@id") == person_id
            ]
            with self.subTest(slug=slug):
                self.assertIn(
                    '<meta name="ai-content-declaration" content="ai-assisted, source-checked">',
                    text,
                )
                self.assertEqual(1, text.count('data-local-agent-trust="v1"'))
                self.assertEqual(1, text.count('data-content-provenance="v1"'))
                self.assertEqual(1, len(web_pages))
                self.assertEqual({"@id": business_id}, web_pages[0].get("publisher"))
                self.assertNotIn("author", web_pages[0])
                self.assertNotIn("reviewedBy", web_pages[0])
                self.assertEqual(1, len(businesses))
                self.assertEqual(1, len(people))
                self.assertEqual({"@id": business_id}, people[0].get("worksFor"))
                self.assertEqual("1754604", people[0].get("identifier", {}).get("value"))

    def test_quick_win_pages_no_longer_share_the_short_template(self):
        normalized = {}
        for slug in QUICK_WIN_EXPECTATIONS:
            source = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
            normalized[slug] = shingles(normalized_main_text(source, slug))
        for left, right in combinations(sorted(normalized), 2):
            left_set = normalized[left]
            right_set = normalized[right]
            similarity = len(left_set & right_set) / len(left_set | right_set)
            with self.subTest(left=left, right=right):
                self.assertLess(similarity, 0.70)

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
