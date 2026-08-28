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
    FORMER_BULK_REDIRECTS,
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
        redirect("/api/lead.js", "/api/lead"),
        redirect("/nj-real-estate-agent", "/ai-authority"),
        redirect("/nj-real-estate-agent.html", "/ai-authority"),
        redirect(
            "/features/ai-email",
            "https://aisalespipeline.com/features/ai-email-real-estate.html",
        ),
        redirect("/communities/basking-ridge", "/towns/basking-ridge"),
    ]
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
        "css/styles.css",
        "404.html",
    ):
        path = static / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    (output / "functions" / "api" / "lead.func").mkdir(parents=True)
    return output


class CompiledVercelRoutingTests(unittest.TestCase):
    def test_generated_build_output_is_excluded_from_source_audits(self) -> None:
        generated = ROOT / ".vercel" / "output" / "static" / "generated.html"
        self.assertTrue(audit_site.is_internal_source(generated))
        self.assertFalse(audit_deep._is_content(str(generated)))
        self.assertIn(".vercel", check_everything.SKIP_DIR_NAMES)
        self.assertIn(".vercel", check_technical_seo.SKIP_DIRS)

    def test_checked_in_source_uses_the_host_first_explicit_contract(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertEqual([], source_contract_issues(config))

    def test_compiled_fixture_covers_static_function_and_migration_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = write_output(Path(directory))
            self.assertEqual([], compiled_contract_issues(compiled_fixture(), output))

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
