#!/usr/bin/env python3
"""Focused safety checks for the daily SEO publishing pipeline."""

import argparse
import contextlib
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import daily_blog


class DailyBlogSafetyTests(unittest.TestCase):
    def test_html_href_guard_handles_valid_attribute_syntax(self):
        bad = (
            '<a href="/legacy.html">x</a>',
            '<a href = "/legacy.html?x=1">x</a>',
            '<a\n href\n=\n"/legacy.HTML#x">x</a>',
            '<a href=/legacy.html>x</a>',
        )
        for markup in bad:
            with self.subTest(markup=markup):
                self.assertTrue(daily_blog.contains_html_href(markup))
        self.assertFalse(daily_blog.contains_html_href('<a href="/canonical">x</a>'))

    def test_sitemap_requires_closing_urlset(self):
        with tempfile.TemporaryDirectory() as tmp:
            sitemap = pathlib.Path(tmp, "sitemap.xml")
            sitemap.write_text("<urlset>", encoding="utf-8")
            with mock.patch.object(daily_blog, "SITEMAP", str(sitemap)):
                with self.assertRaisesRegex(RuntimeError, "closing urlset"):
                    daily_blog.prepare_sitemap("test-post", "2026-08-17")

    def test_blog_card_links_are_root_relative_and_extensionless(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = pathlib.Path(tmp, "index.html")
            index.write_text(
                '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px;"></div>',
                encoding="utf-8",
            )
            post = {"h1": "Test", "category": "Guide", "meta_description": "Test"}
            with mock.patch.object(daily_blog, "INDEX", str(index)):
                rendered = daily_blog.prepare_index(post, "test-post")
            self.assertEqual(rendered.count('href="/blog/test-post"'), 2)
            self.assertNotIn(".html", rendered)

    def test_batch_write_restores_files_after_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            paths = [root / name for name in ("a", "b", "c")]
            for path, value in zip(paths, ("A", "B", "C")):
                path.write_text(value, encoding="utf-8")

            real_atomic_write = daily_blog.atomic_write
            calls = 0

            def fail_once(path, content):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("simulated write failure")
                real_atomic_write(path, content)

            with mock.patch.object(daily_blog, "atomic_write", side_effect=fail_once):
                with self.assertRaisesRegex(OSError, "simulated"):
                    daily_blog.write_batch(dict(zip(map(str, paths), ("newA", "newB", "newC"))))

            self.assertEqual([p.read_text(encoding="utf-8") for p in paths], ["A", "B", "C"])

    def test_publish_preflights_parent_sitemap_before_writing(self):
        post = {
            "title": "Test",
            "h1": "Test",
            "meta_description": "Test",
            "keywords": "test",
            "quick_answer": "Test",
            "body_html": " ".join(["word"] * 700),
            "faqs": [{"q": "q", "a": "a"}] * 3,
            "category": "Guide",
        }
        topic = {"slug": "test-post", "geo": "New Jersey"}
        args = argparse.Namespace(dry_run=False, no_push=True)

        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            blog = root / "blog"
            blog.mkdir()
            index = blog / "index.html"
            sitemap = root / "sitemap.xml"
            sitemap_index = root / "sitemap-index.xml"
            state = root / "state.json"
            index.write_text(
                '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px;"></div>',
                encoding="utf-8",
            )
            sitemap.write_text("<urlset></urlset>", encoding="utf-8")
            sitemap_index.write_text("<sitemapindex></sitemapindex>", encoding="utf-8")
            state.write_text('{"used": []}', encoding="utf-8")
            tracked = (index, sitemap, sitemap_index, state)
            baseline = {path: path.read_text(encoding="utf-8") for path in tracked}

            patches = (
                mock.patch.object(daily_blog, "BLOG_DIR", str(blog)),
                mock.patch.object(daily_blog, "INDEX", str(index)),
                mock.patch.object(daily_blog, "SITEMAP", str(sitemap)),
                mock.patch.object(daily_blog, "SITEMAP_INDEX", str(sitemap_index)),
                mock.patch.object(daily_blog, "STATE_FILE", str(state)),
                mock.patch.object(daily_blog, "assemble", return_value='<a href="/canonical">ok</a>'),
                mock.patch.object(daily_blog, "deploy", return_value=True),
            )
            for patcher in patches:
                patcher.start()
                self.addCleanup(patcher.stop)

            with self.assertRaisesRegex(RuntimeError, "sitemap-index"):
                daily_blog.publish(post, topic, {}, args)

            self.assertFalse((blog / "test-post.html").exists())
            self.assertTrue(all(path.read_text(encoding="utf-8") == value for path, value in baseline.items()))

    def test_publish_recovers_precommit_failure_and_preserves_push_failure(self):
        post = {
            "title": "Test", "h1": "Test", "meta_description": "Test",
            "keywords": "test", "quick_answer": "Test",
            "body_html": " ".join(["word"] * 700),
            "faqs": [{"q": "q", "a": "a"}] * 3, "category": "Guide",
        }
        topic = {"slug": "test-post", "geo": "New Jersey"}
        args = argparse.Namespace(dry_run=False, no_push=False)

        for deploy_status, should_keep_outputs in (
            (daily_blog.DEPLOY_PRECOMMIT_FAILED, False),
            (daily_blog.DEPLOY_PUSH_FAILED, True),
        ):
            with self.subTest(deploy_status=deploy_status), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp)
                blog = root / "blog"
                blog.mkdir()
                index = blog / "index.html"
                sitemap = root / "sitemap.xml"
                sitemap_index = root / "sitemap-index.xml"
                state = root / "state.json"
                log_dir = root / "logs"
                index.write_text("old index", encoding="utf-8")
                sitemap.write_text("old sitemap", encoding="utf-8")
                sitemap_index.write_text("old parent", encoding="utf-8")
                state.write_text('{"used": []}', encoding="utf-8")

                with contextlib.ExitStack() as stack:
                    for name, value in (
                        ("BLOG_DIR", str(blog)), ("INDEX", str(index)),
                        ("SITEMAP", str(sitemap)), ("SITEMAP_INDEX", str(sitemap_index)),
                        ("STATE_FILE", str(state)), ("LOG_DIR", str(log_dir)),
                    ):
                        stack.enter_context(mock.patch.object(daily_blog, name, value))
                    stack.enter_context(mock.patch.object(daily_blog, "assemble", return_value='<a href="/canonical">ok</a>'))
                    stack.enter_context(mock.patch.object(daily_blog, "prepare_index", return_value="new index"))
                    stack.enter_context(mock.patch.object(daily_blog, "prepare_sitemap", return_value="new sitemap"))
                    stack.enter_context(mock.patch.object(daily_blog, "prepare_sitemap_index", return_value="new parent"))
                    stack.enter_context(mock.patch.object(daily_blog, "deploy", return_value=deploy_status))
                    result = daily_blog.publish(post, topic, {}, args)

                article = blog / "test-post.html"
                if should_keep_outputs:
                    self.assertEqual(result, daily_blog.DEPLOY_PUSH_FAILED)
                    self.assertTrue(article.exists())
                    self.assertEqual(index.read_text(encoding="utf-8"), "new index")
                    self.assertIn("test-post", json.loads(state.read_text(encoding="utf-8"))["used"])
                else:
                    self.assertFalse(result)
                    self.assertFalse(article.exists())
                    self.assertEqual(index.read_text(encoding="utf-8"), "old index")
                    self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["used"], [])

    def test_main_stops_retrying_after_committed_push_failure(self):
        post_json = json.dumps({"title": "Test"})
        gate_json = json.dumps({"score": 100, "pass": True, "issues": []})
        topic = {"slug": "test-post", "prompt_subject": "Test"}

        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            config = root / "config.json"
            state = root / "state.json"
            config.write_text('{"quality_threshold": 80, "max_attempts": 2}', encoding="utf-8")
            state.write_text('{"used": [], "last_run": null}', encoding="utf-8")
            with contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(daily_blog, "CONFIG_FILE", str(config)))
                stack.enter_context(mock.patch.object(daily_blog, "STATE_FILE", str(state)))
                stack.enter_context(mock.patch.object(daily_blog, "pick_topic", return_value=topic))
                stack.enter_context(mock.patch.object(
                    daily_blog, "generate",
                    side_effect=[(post_json, "test"), (gate_json, "test"),
                                 (post_json, "test"), (gate_json, "test")],
                ))
                publish = stack.enter_context(mock.patch.object(
                    daily_blog, "publish", return_value=daily_blog.DEPLOY_PUSH_FAILED,
                ))
                stack.enter_context(mock.patch.object(daily_blog.sys, "argv", ["daily_blog.py"]))
                daily_blog.main()

            publish.assert_called_once()


if __name__ == "__main__":
    unittest.main()
