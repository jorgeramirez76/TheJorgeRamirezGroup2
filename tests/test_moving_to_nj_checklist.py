from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "blog" / "moving-to-nj-checklist.html"
RENDERER = ROOT / "tools" / "render_moving_to_nj_checklist.py"


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.main = 0
        self.h1 = 0
        self.paragraphs: list[str] = []
        self._paragraph: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "main" and values.get("id") == "main":
            self.main += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "p":
            self._paragraph = []

    def handle_data(self, data: str) -> None:
        if self._paragraph is not None:
            self._paragraph.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._paragraph is not None:
            value = " ".join("".join(self._paragraph).split())
            if value:
                self.paragraphs.append(value)
            self._paragraph = None


class MovingToNjChecklistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PAGE.read_text(encoding="utf-8")

    def test_renderer_is_current(self) -> None:
        result = subprocess.run([sys.executable, str(RENDERER), "--check"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_structure_and_schema(self) -> None:
        parser = Parser()
        parser.feed(self.source)
        self.assertEqual(1, parser.main)
        self.assertEqual(1, parser.h1)
        self.assertEqual(len(parser.paragraphs), len(set(parser.paragraphs)))
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', self.source, re.S)
        self.assertEqual(1, len(blocks))
        json.loads(blocks[0])

    def test_current_primary_sources_and_guardrails(self) -> None:
        for url in (
            "https://www.nj.gov/mvc/drivertopics/movetonj.htm",
            "https://www.nj.gov/mvc/license/6pointid.htm",
            "https://www.nj.gov/mvc/inspection/inspecthow.htm",
            "https://www.nj.gov/mvc/inspection/exemptinsp.htm",
            "https://www.nj.gov/state/elections/voter-registration.shtml",
        ):
            self.assertIn(url, self.source)
        self.assertRegex(self.source, r"within 60 days")
        self.assertRegex(self.source, r"within 14 days")
        self.assertRegex(self.source, r"21 days before an election")
        self.assertNotRegex(self.source, re.compile(r"highest in the country|removes the New York City resident income tax entirely|deadline almost nobody|no walk-ins|license first|far more generous|the trap is|penalty for guessing", re.I))

    def test_homepage_palette_and_fonts(self) -> None:
        for token in ("#1A1A1A", "#0A0A0A", "#C41230", "#8B0D22", "#B8962E", "#D4AF5A", "#FAFAF8", "#F8F6F2", "Playfair Display", "Inter"):
            self.assertIn(token, self.source)


if __name__ == "__main__":
    unittest.main()
