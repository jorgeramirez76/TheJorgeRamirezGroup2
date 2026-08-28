#!/usr/bin/env python3
"""Regression tests for the Vercel Build Output routing contract."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

import audit_deep
import audit_site
import check_everything
from tools import check_technical_seo
from tools.check_compiled_vercel_routes import (
    CANONICAL_ORIGIN,
    DIRECTORY_INDEX_PREEMPTIONS,
    FORMER_BULK_REDIRECTS,
    compiled_asset_issues,
    compiled_contract_issues,
    source_contract_issues,
)


ROOT = Path(__file__).resolve().parents[1]


def redirect(source: str, destination: str) -> dict:
    return {
        "src": "^" + re.escape(source) + "$",
        "headers": {"Location": destination},
        "status": 308,
    }


def compiled_fixture() -> dict:
    routes = [
        {
            "src": "^(?:/(.*))$",
            "headers": {"Location": f"{CANONICAL_ORIGIN}/$1"},
            "status": 308,
            "has": [{"type": "host", "value": {"eq": "www.thejorgeramirezgroup.com"}}],
        },
        {
            "src": "^(?:/(.*))$",
            "headers": {"Location": f"{CANONICAL_ORIGIN}/$1"},
            "status": 308,
            "has": [{"type": "host", "value": {"suf": ".vercel.app"}}],
        },
    ]
    routes.extend(
        redirect(rule["source"], rule["destination"])
        for rule in DIRECTORY_INDEX_PREEMPTIONS
    )
    routes.extend(
        [
            redirect("/api/lead.js", "/api/lead"),
            redirect("/nj-real-estate-agent", "/ai-authority"),
            redirect("/nj-real-estate-agent.html", "/ai-authority"),
            redirect(
                "/features/ai-email",
                "https://aisalespipeline.com/features/ai-email-real-estate.html",
            ),
            redirect("/communities/basking-ridge", "/towns/basking-ridge"),
            {
                "src": "^/communities(?:/([^/]+?))\\.html$",
                "headers": {"Location": "/towns/$1"},
                "status": 308,
            },
        ]
    )
    routes.extend(redirect(source, destination) for source, destination in FORMER_BULK_REDIRECTS)
    routes.extend(
        [
            {
                "src": "^(?:/((?:[^/]+?)(?:/(?:[^/]+?))*))?/index\\.html/$",
                "headers": {"Location": "/$1"},
                "status": 308,
            },
            {
                "src": "^(?:/((?:[^/]+?)(?:/(?:[^/]+?))*))?/index/$",
                "headers": {"Location": "/$1"},
                "status": 308,
            },
            {
                "src": "^(?:/((?:[^/]+?)(?:/(?:[^/]+?))*))?/index\\.html$",
                "headers": {"Location": "/$1"},
                "status": 308,
            },
            {
                "src": "^(?:/((?:[^/]+?)(?:/(?:[^/]+?))*))?/index$",
                "headers": {"Location": "/$1"},
                "status": 308,
            },
            {"src": "^(?:/(.*))\\.html/$", "headers": {"Location": "/$1"}, "status": 308},
            {"src": "^(?:/(.*))\\.html$", "headers": {"Location": "/$1"}, "status": 308},
            {"src": "^(?:/(.*))/$", "headers": {"Location": "/$1"}, "status": 308},
            {"handle": "filesystem"},
            {"src": "^/$", "dest": "/index.html", "check": True},
            {"src": "^(?:/(.*))$", "dest": "/$1.html", "check": True},
            {"src": "^(?:/(.*))$", "dest": "/$1/index.html", "check": True},
            {"src": "^/api(/.*)?$", "status": 404},
            {"handle": "error"},
            {"status": 404, "src": "^(?!/api).*$", "dest": "/404.html"},
        ]
    )
    return {"version": 3, "routes": routes}


def write_output(root: Path) -> Path:
    output = root / ".vercel" / "output"
    static = output / "static"
    for relative in (
        "index.html",
        "ai-authority.html",
        "blog/index.html",
        "communities/index.html",
        "css/styles.css",
        "404.html",
    ):
        path = static / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    (output / "functions" / "api" / "lead.func").mkdir(parents=True)
    return output


class CompiledVercelRoutingTests(unittest.TestCase):
    def test_repo_root_recursive_scanners_exclude_generated_build_output(self) -> None:
        root_scan = re.compile(
            r"\b(?:ROOT|REPO|BASE_DIR|root)\.rglob\(|"
            r"\b(?:ROOT|REPO|BASE_DIR|root)\.glob\(\s*[\"'][^\"']*\*\*|"
            r"\bos\.walk\("
        )
        offenders: list[str] = []
        for path in ROOT.rglob("*.py"):
            relative = path.relative_to(ROOT)
            if {".git", ".vercel", "node_modules"}.intersection(relative.parts):
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            if root_scan.search(source) and ".vercel" not in source:
                offenders.append(relative.as_posix())
        self.assertEqual([], offenders)

    def test_generated_build_output_is_excluded_from_source_audits(self) -> None:
        generated = ROOT / ".vercel" / "output" / "static" / "generated.html"
        self.assertTrue(audit_site.is_internal_source(generated))
        self.assertFalse(audit_deep._is_content(str(generated)))
        self.assertIn(".vercel", check_everything.SKIP_DIR_NAMES)
        self.assertIn(".vercel", check_technical_seo.SKIP_DIRS)

    def test_nested_internal_tool_html_is_excluded_from_technical_seo(self) -> None:
        for relative in (
            "tools/blog-automation/template_source.html",
            "tools/blog-automation/nested/generated.html",
            "tools/seo-optimizer/report.html",
        ):
            with self.subTest(relative=relative):
                self.assertTrue(check_technical_seo.is_skipped_html(ROOT / relative))

        self.assertFalse(
            check_technical_seo.is_skipped_html(ROOT / "tools/mortgage-calculator.html")
        )

    def test_checked_in_source_uses_the_host_first_explicit_contract(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertEqual([], source_contract_issues(config))

    def test_compiled_fixture_covers_static_function_and_migration_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = write_output(Path(directory))
            self.assertEqual([], compiled_contract_issues(compiled_fixture(), output))

    def test_compiled_asset_closure_catches_missing_srcset_variants(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = write_output(Path(directory))
            page = output / "static" / "index.html"
            page.write_text(
                '<img src="/images/towns/chatham-township-2.webp" '
                'srcset="/images/towns/chatham-township-2-640.webp 640w, '
                '/images/towns/chatham-township-2-960.webp 960w">',
                encoding="utf-8",
            )
            issues = compiled_asset_issues(output)
            self.assertEqual(3, len(issues))
            self.assertTrue(
                any("chatham-township-2-640.webp" in issue for issue in issues),
                issues,
            )
            for filename in (
                "chatham-township-2.webp",
                "chatham-township-2-640.webp",
                "chatham-township-2-960.webp",
            ):
                asset = output / "static" / "images" / "towns" / filename
                asset.parent.mkdir(parents=True, exist_ok=True)
                asset.write_bytes(b"fixture")
            self.assertEqual([], compiled_asset_issues(output))

    def test_compiled_clean_url_route_before_host_guards_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = write_output(Path(directory))
            compiled = compiled_fixture()
            compiled["routes"].insert(
                0,
                {
                    "src": "^/(.*)\\.html/?$",
                    "headers": {"Location": "/$1"},
                    "status": 308,
                },
            )
            issues = compiled_contract_issues(compiled, output)
            self.assertTrue(
                any("host" in issue or "canonical" in issue for issue in issues),
                issues,
            )

    def test_managed_wildcard_cannot_capture_a_directory_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = write_output(Path(directory))
            compiled = compiled_fixture()
            compiled["routes"] = [
                route
                for route in compiled["routes"]
                if route.get("src") != "^/communities/index\\.html$"
            ]
            issues = compiled_contract_issues(compiled, output)
            self.assertTrue(
                any("directory-index" in issue for issue in issues),
                issues,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
