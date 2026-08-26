#!/usr/bin/env python3
"""The scheduled blog job must never publish an unreviewed AI draft."""

from __future__ import annotations

import importlib.util
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "blog-automation" / "daily_blog.py"


def load_module():
    spec = importlib.util.spec_from_file_location("daily_blog", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DailyBlogReviewGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.post = {
            "title": "Reviewed title",
            "h1": "Reviewed headline",
            "meta_description": "A sufficiently descriptive summary for a reviewed New Jersey real estate article.",
            "keywords": "New Jersey real estate",
            "quick_answer": "Review property-specific facts before making a decision.",
            "body_html": "<p>" + ("useful context " * 700) + "</p>",
            "faqs": [
                {"q": "Question one?", "a": "Answer one."},
                {"q": "Question two?", "a": "Answer two."},
                {"q": "Question three?", "a": "Answer three."},
            ],
        }
        self.topic = {
            "slug": "review-required",
            "geo": "New Jersey",
            "category": "Guide",
        }

    def test_scheduled_mode_writes_review_artifact_but_not_public_site(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            blog = root / "blog"
            logs = root / "logs"
            blog.mkdir()
            (blog / "index.html").write_text("unchanged index", encoding="utf-8")
            (root / "sitemap.xml").write_text("unchanged sitemap", encoding="utf-8")

            args = types.SimpleNamespace(
                dry_run=False,
                no_push=False,
                publish_reviewed=False,
            )
            with (
                mock.patch.object(self.module, "BLOG_DIR", str(blog)),
                mock.patch.object(self.module, "INDEX", str(blog / "index.html")),
                mock.patch.object(self.module, "SITEMAP", str(root / "sitemap.xml")),
                mock.patch.object(self.module, "LOG_DIR", str(logs)),
                mock.patch.object(self.module, "STATE_FILE", str(root / "state.json")),
                mock.patch.object(self.module, "assemble", return_value="<html>review draft</html>"),
                mock.patch.object(self.module, "deploy") as deploy,
                mock.patch.object(self.module, "log"),
            ):
                self.assertTrue(self.module.publish(self.post, self.topic, {}, args))

            self.assertEqual(
                "<html>review draft</html>",
                (logs / "REVIEW-review-required.html").read_text(encoding="utf-8"),
            )
            self.assertFalse((blog / "review-required.html").exists())
            self.assertEqual("unchanged index", (blog / "index.html").read_text(encoding="utf-8"))
            self.assertEqual("unchanged sitemap", (root / "sitemap.xml").read_text(encoding="utf-8"))
            self.assertFalse((root / "state.json").exists())
            deploy.assert_not_called()

    def test_generated_content_cannot_enable_reviewed_publish_flag(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            self.module.main(["--publish-reviewed"])
        self.assertEqual(2, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
