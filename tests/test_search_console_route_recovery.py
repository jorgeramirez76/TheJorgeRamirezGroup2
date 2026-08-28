#!/usr/bin/env python3
"""Regression contract for evidence-backed Search Console route recovery."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path

from tools.sync_search_console_route_recovery import render_config


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "search-console-route-recovery.json"
TOWN_MANIFEST = ROOT / "data" / "indexable-town-risk-decisions.json"
SYNC = ROOT / "tools" / "sync_search_console_route_recovery.py"


class SearchConsoleRouteRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.town_manifest = json.loads(TOWN_MANIFEST.read_text(encoding="utf-8"))
        cls.config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        cls.recovery = {
            item["source"]: item["destination"] for item in cls.manifest["routes"]
        }
        cls.retired = {
            item["source"]: item["destination"]
            for item in cls.town_manifest["incomingRedirectFamilies"]
        }
        cls.expected = cls.recovery | cls.retired

    def test_manifest_is_scoped_to_observed_routes_and_current_targets(self) -> None:
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertEqual("2026-08-26", self.manifest["reviewedOn"])
        self.assertIn("Read-only Google Search Console", self.manifest["source"])
        self.assertIn("same-language", self.manifest["policy"])
        self.assertEqual(37, len(self.recovery))
        self.assertEqual(13, len(self.retired))
        self.assertEqual(50, len(self.expected))
        self.assertEqual("/counties/essex-county", self.retired["/blog/neighborhoods-maplewood-nj"])
        self.assertEqual("/es/ai-authority", self.recovery["/blog/es/como-elegir-agente-inmobiliario-nj"])
        self.assertEqual(
            "/blog/best-nj-suburbs-nyc-commuters",
            self.recovery["/blog/nyc-to-nj-commute-guide-2026"],
        )
        for source, destination in self.expected.items():
            with self.subTest(source=source):
                self.assertTrue(source.startswith("/"))
                self.assertTrue(destination.startswith("/"))
                self.assertNotEqual(source, destination)

    def test_all_routes_are_exact_permanent_one_hop_redirects(self) -> None:
        by_source: dict[str, list[dict]] = {}
        for item in self.config["redirects"]:
            by_source.setdefault(str(item.get("source", "")), []).append(item)
        redirect_sources = set(by_source)
        for source, destination in self.expected.items():
            with self.subTest(source=source):
                self.assertEqual(1, len(by_source.get(source, [])))
                rule = by_source[source][0]
                self.assertEqual(destination, rule.get("destination"))
                self.assertIs(True, rule.get("permanent"))
                self.assertNotIn("has", rule)
                self.assertNotIn("statusCode", rule)
                self.assertNotIn(destination, redirect_sources)

    def test_html_variants_use_enabled_clean_url_normalization(self) -> None:
        self.assertNotIn("cleanUrls", self.config)
        self.assertNotIn("trailingSlash", self.config)
        self.assertIn(
            {"source": "/(.*).html", "destination": "/$1", "permanent": True},
            self.config["redirects"],
        )
        exact_sources = {str(item.get("source", "")) for item in self.config["redirects"]}
        for source, destination in self.expected.items():
            if source.endswith(".html"):
                clean = source.removesuffix(".html")
                self.assertEqual(destination, self.expected.get(clean), source)
            elif source + ".html" not in self.expected:
                self.assertNotIn(source + ".html", exact_sources)

    def test_sync_is_deterministic_and_other_managed_route_contracts_are_current(self) -> None:
        commands = (
            [sys.executable, str(SYNC), "--check"],
            [sys.executable, "scripts/retire_programmatic_doorways.py", "--check"],
            [sys.executable, "tools/sync_ai_sales_pipeline_routes.py", "--check"],
        )
        for command in commands:
            with self.subTest(command=command[1]):
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_future_missing_route_is_inserted_after_the_canonical_host_preamble(self) -> None:
        host_preamble = deepcopy(self.config["redirects"][:2])
        unrelated = [
            {
                "source": "/already-managed",
                "destination": "/existing-target",
                "permanent": True,
            },
            {
                "source": "/realtor/:slug-nj",
                "destination": "/towns/:slug",
                "permanent": True,
            },
            {
                "source": "/unrelated-tail",
                "destination": "/tail-target",
                "permanent": True,
            },
        ]
        config = {"redirects": host_preamble + deepcopy(unrelated)}
        mappings = {
            "/already-managed": "/existing-target",
            "/synthetic-missing-route": "/synthetic-target",
        }

        rendered = json.loads(render_config(config, mappings))["redirects"]

        self.assertEqual(host_preamble, rendered[:2])
        self.assertEqual(
            host_preamble + unrelated,
            [rule for rule in rendered if rule["source"] != "/synthetic-missing-route"],
        )
        self.assertLess(
            next(i for i, rule in enumerate(rendered) if rule["source"] == "/synthetic-missing-route"),
            next(i for i, rule in enumerate(rendered) if rule["source"] == "/realtor/:slug-nj"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
