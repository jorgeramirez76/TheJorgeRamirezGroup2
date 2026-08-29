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
                mock.patch.object(self.module, "production_source_preflight") as preflight,
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
            preflight.assert_not_called()
            deploy.assert_not_called()

    def test_reviewed_publish_fails_closed_before_any_source_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            blog = root / "blog"
            blog.mkdir()
            index = blog / "index.html"
            sitemap = root / "sitemap.xml"
            state = root / "state.json"
            index.write_text("unchanged index", encoding="utf-8")
            sitemap.write_text("unchanged sitemap", encoding="utf-8")
            args = types.SimpleNamespace(dry_run=False, no_push=False, publish_reviewed=True)

            with (
                mock.patch.object(self.module, "BLOG_DIR", str(blog)),
                mock.patch.object(self.module, "INDEX", str(index)),
                mock.patch.object(self.module, "SITEMAP", str(sitemap)),
                mock.patch.object(self.module, "STATE_FILE", str(state)),
                mock.patch.object(self.module, "assemble", return_value="<html>reviewed</html>"),
                mock.patch.object(self.module, "production_source_preflight", return_value=False) as preflight,
                mock.patch.object(self.module, "add_to_index") as add_to_index,
                mock.patch.object(self.module, "add_to_sitemap") as add_to_sitemap,
                mock.patch.object(self.module, "deploy") as deploy,
                mock.patch.object(self.module, "log"),
            ):
                self.assertFalse(self.module.publish(self.post, self.topic, {}, args))

            self.assertFalse((blog / "review-required.html").exists())
            self.assertEqual("unchanged index", index.read_text(encoding="utf-8"))
            self.assertEqual("unchanged sitemap", sitemap.read_text(encoding="utf-8"))
            self.assertFalse(state.exists())
            preflight.assert_called_once_with()
            add_to_index.assert_not_called()
            add_to_sitemap.assert_not_called()
            deploy.assert_not_called()

    def test_reviewed_publish_propagates_deploy_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            blog = root / "blog"
            blog.mkdir()
            state = root / "state.json"
            args = types.SimpleNamespace(dry_run=False, no_push=False, publish_reviewed=True)

            with (
                mock.patch.object(self.module, "BLOG_DIR", str(blog)),
                mock.patch.object(self.module, "STATE_FILE", str(state)),
                mock.patch.object(self.module, "assemble", return_value="<html>reviewed</html>"),
                mock.patch.object(self.module, "production_source_preflight", return_value=True),
                mock.patch.object(self.module, "add_to_index"),
                mock.patch.object(self.module, "add_to_sitemap"),
                mock.patch.object(self.module, "deploy", return_value=False),
                mock.patch.object(self.module, "log") as log,
            ):
                self.assertFalse(self.module.publish(self.post, self.topic, {}, args))

            self.assertTrue((blog / "review-required.html").is_file())
            self.assertTrue(state.is_file())
            self.assertTrue(any("FAILED" in call.args[0] for call in log.call_args_list))

    def test_live_preflight_is_explicit_and_subprocess_failure_blocks_publication(self) -> None:
        completed = types.SimpleNamespace(returncode=1, stdout="", stderr="live drift")
        with (
            mock.patch.object(self.module.subprocess, "run", return_value=completed) as run,
            mock.patch.object(self.module, "log") as log,
        ):
            self.assertFalse(self.module.production_source_preflight())

        command = run.call_args.args[0]
        self.assertEqual(self.module.sys.executable, command[0])
        self.assertEqual(self.module.PRODUCTION_DRIFT_GUARD, command[1])
        self.assertEqual("--live", command[2])
        self.assertEqual(self.module.REPO, run.call_args.kwargs["cwd"])
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertTrue(any("live drift" in call.args[0] for call in log.call_args_list))

    def test_deploy_fails_closed_on_staging_or_commit_error(self) -> None:
        failure = types.SimpleNamespace(returncode=1, stdout="", stderr="blocked")
        with (
            mock.patch.object(self.module.subprocess, "run", return_value=failure) as run,
            mock.patch.object(self.module, "log") as log,
        ):
            self.assertFalse(self.module.deploy("review-required"))
        self.assertEqual("add", run.call_args.args[0][1])
        self.assertTrue(any("STAGING FAILED" in call.args[0] for call in log.call_args_list))

        success = types.SimpleNamespace(returncode=0, stdout="", stderr="")
        with (
            mock.patch.object(self.module.subprocess, "run", side_effect=[success, failure]) as run,
            mock.patch.object(self.module, "log") as log,
        ):
            self.assertFalse(self.module.deploy("review-required"))
        commands = [call.args[0][1] for call in run.call_args_list]
        self.assertEqual(["add", "commit"], commands)
        self.assertTrue(any("COMMIT FAILED" in call.args[0] for call in log.call_args_list))

    def test_deploy_uses_canonical_remote_and_never_rebases_after_rejection(self) -> None:
        success = types.SimpleNamespace(returncode=0, stdout="", stderr="")
        rejection = types.SimpleNamespace(returncode=1, stdout="", stderr="rejected")
        with (
            mock.patch.object(self.module.subprocess, "run", side_effect=[success, success, rejection]) as run,
            mock.patch.object(self.module, "log") as log,
        ):
            self.assertFalse(self.module.deploy("review-required"))

        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual("add", commands[0][1])
        self.assertEqual("commit", commands[1][1])
        self.assertEqual(
            ["git", "push", self.module.PUBLISH_REMOTE, self.module.PUBLISH_BRANCH],
            commands[2],
        )
        self.assertFalse(any(command[1] in {"pull", "rebase"} for command in commands))
        self.assertTrue(any("PUSH FAILED" in call.args[0] for call in log.call_args_list))

    def test_generated_content_cannot_enable_reviewed_publish_flag(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            self.module.main(["--publish-reviewed"])
        self.assertEqual(2, raised.exception.code)

    def test_prompt_requires_neutral_fair_housing_framing(self) -> None:
        topic = {
            "prompt_subject": "comparing New Jersey housing options",
        }
        prompt = self.module.build_prompt(topic)
        self.assertIn("Follow fair-housing rules", prompt)
        self.assertIn("proxy audiences", prompt)
        self.assertIn("Present official school", prompt)

    def test_validator_rejects_steering_language_before_publication(self) -> None:
        self.post["body_html"] += (
            "<p>This family-friendly community has top-rated schools and is "
            "perfect for young professionals.</p>"
        )
        self.assertEqual(
            "fair-housing review required: protected-audience targeting",
            self.module.validate(self.post),
        )

    def test_validator_accepts_neutral_official_source_research(self) -> None:
        self.post["body_html"] += (
            "<p>Review address-level assignments and current NJDOE School "
            "Performance Reports directly. Compare NJ Transit schedules, "
            "municipal services, housing type, price, and property condition.</p>"
        )
        self.assertIsNone(self.module.validate(self.post))


if __name__ == "__main__":
    unittest.main()
