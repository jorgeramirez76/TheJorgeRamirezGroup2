import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class SitewideHtmlHygieneTests(unittest.TestCase):
    def test_every_html_document_declares_a_mobile_viewport(self):
        missing = []
        for path in ROOT.rglob("*.html"):
            if any(part in {".git", "node_modules"} for part in path.parts):
                continue
            html = path.read_text(encoding="utf-8", errors="replace").lower()
            if 'name="viewport"' not in html and "name='viewport'" not in html:
                missing.append(str(path.relative_to(ROOT)))

        self.assertEqual([], missing, "HTML files missing a viewport: " + ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
