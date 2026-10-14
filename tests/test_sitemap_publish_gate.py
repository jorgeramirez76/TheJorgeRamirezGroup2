"""Exercise the actual deployment gate against a disposable candidate site."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = Path("tools/check_technical_seo.py")


class SitemapPublishGateTests(unittest.TestCase):
    def test_build_rejects_missing_article_then_accepts_complete_candidate(self) -> None:
        command = json.loads((ROOT / "vercel.json").read_text())["buildCommand"]
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory)
            # The validator reads HTML, routing and sitemap XML only. Copy the
            # real site contract without touching this working tree or Git.
            paths = list(ROOT.rglob("*.html")) + [
                ROOT / "vercel.json",
                ROOT / "sitemap.xml",
                ROOT / "sitemap-es.xml",
                ROOT / "sitemap-index.xml",
                ROOT / CHECKER,
            ]
            for source in paths:
                target = candidate / source.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)

            sitemap = candidate / "sitemap.xml"
            original = sitemap.read_text()
            slug = "sitemap-gate-regression-fixture"
            canonical = f"https://thejorgeramirezgroup.com/blog/{slug}"
            page = candidate / "blog" / f"{slug}.html"
            # Reuse a valid article, changing only its canonical identity.
            source_slug = "weekend-backyard-fixes-nj-home-sellers-2026"
            source = (candidate / "blog" / f"{source_slug}.html").read_text()
            page.write_text(source.replace(source_slug, slug))

            failed = subprocess.run(command, shell=True, cwd=candidate, capture_output=True, text=True)
            self.assertNotEqual(0, failed.returncode, failed.stdout + failed.stderr)
            self.assertIn(f"indexable canonical page is absent from sitemaps: {canonical}", failed.stdout)
            self.assertTrue((candidate / CHECKER).is_file())
            self.assertEqual(original, sitemap.read_text())

            complete = original.replace("</urlset>", f"  <url><loc>{canonical}</loc></url>\n</urlset>")
            sitemap.write_text(complete)
            passed = subprocess.run(command, shell=True, cwd=candidate, capture_output=True, text=True)
            self.assertEqual(0, passed.returncode, passed.stdout + passed.stderr)
            self.assertIn("technical SEO regression check passed", passed.stdout)
            self.assertFalse((candidate / CHECKER).exists(), "build-only Python must not be publicly served")
            self.assertEqual(complete, sitemap.read_text())
            self.assertTrue(page.is_file())

    def test_only_validator_is_allowlisted_for_build(self) -> None:
        entries = (ROOT / ".vercelignore").read_text().splitlines()
        self.assertIn("*.py", entries)
        self.assertEqual(["!tools/check_technical_seo.py"], [line for line in entries if line.startswith("!") and line.endswith(".py")])
        self.assertGreater(entries.index("!tools/check_technical_seo.py"), entries.index("*.py"))


if __name__ == "__main__":
    unittest.main()
