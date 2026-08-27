from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(relative: str, module_name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LegacyClaimGeneratorSafetyTests(unittest.TestCase):
    def test_flip_scrubber_is_read_only_and_fails_closed(self) -> None:
        source = (ROOT / "scrub_flip_count.py").read_text(encoding="utf-8")
        self.assertNotIn("write_text(", source)
        self.assertNotIn("open(path, 'w'", source)
        self.assertIn("data/site-facts.json", source)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.html"
            original = "<p>Jorge personally flipped 60+ homes.</p>"
            path.write_text(original, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scrub_flip_count.py"), str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(1, result.returncode)
            self.assertEqual(original, path.read_text(encoding="utf-8"))
            self.assertIn("Refusing automatic substitutions", result.stderr)

    def test_legacy_critical_fixer_cannot_create_reviews(self) -> None:
        source = (ROOT / "fix_critical_seo.py").read_text(encoding="utf-8")
        for fabricated_fragment in (
            "$47,000 over asking",
            "expired listing with another agent for 90 days",
            "His investor background meant he caught things",
            "got us $30K above",
        ):
            self.assertNotIn(fabricated_fragment, source)

        module = load_script("fix_critical_seo.py", "retired_review_schema_fixer")
        self.assertEqual(0, module.fix_c8_review_schema())


if __name__ == "__main__":
    unittest.main()
