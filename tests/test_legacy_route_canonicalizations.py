#!/usr/bin/env python3
"""Regression contract for evidence-backed legacy route canonicalizations."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path

from tools.sync_legacy_route_canonicalizations import render_config, render_fallback


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "legacy-route-canonicalizations.json"
SYNC = ROOT / "tools" / "sync_legacy_route_canonicalizations.py"
SITE = "https://thejorgeramirezgroup.com"


class LegacyRouteCanonicalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.items = cls.manifest["routes"]
        cls.config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))

    def test_manifest_records_narrow_same_intent_evidence(self) -> None:
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertEqual("2026-08-26", self.manifest["reviewedOn"])
        self.assertEqual(4, len(self.items))
        self.assertIn("clean URL normalizer", self.manifest["policy"])
        self.assertEqual(4, len({item["source"] for item in self.items}))
        self.assertEqual(4, len({item["fallbackFile"] for item in self.items}))
        westfield = next(item for item in self.items if item["source"] == "/westfield-vs-summit-nj")
        self.assertIn("7 clicks and 621 impressions", westfield["evidence"])
        for item in self.items:
            with self.subTest(source=item["source"]):
                self.assertIn(item["language"], {"en", "es"})
                self.assertTrue(item["evidence"])

    def test_clean_routes_are_permanent_one_hop_and_within_route_limit(self) -> None:
        self.assertNotIn("cleanUrls", self.config)
        self.assertNotIn("trailingSlash", self.config)
        self.assertIn(
            {"source": "/(.*).html", "destination": "/$1", "permanent": True},
            self.config["redirects"],
        )
        by_source: dict[str, list[dict]] = {}
        for rule in self.config["redirects"]:
            by_source.setdefault(str(rule.get("source", "")), []).append(rule)
        sources = set(by_source)
        for item in self.items:
            source = item["source"]
            destination = item["destination"]
            with self.subTest(source=source):
                self.assertEqual(1, len(by_source.get(source, [])))
                rule = by_source[source][0]
                self.assertEqual(destination, rule.get("destination"))
                self.assertIs(True, rule.get("permanent"))
                self.assertNotIn("has", rule)
                self.assertNotIn(source + ".html", sources)
                self.assertNotIn(destination, sources)
        declared = sum(len(self.config.get(key, [])) for key in ("redirects", "rewrites", "headers"))
        self.assertLess(declared, 2048)

    def test_fallbacks_are_exact_compact_noindex_outputs_without_hreflang(self) -> None:
        for item in self.items:
            relative = item["fallbackFile"]
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertEqual(render_fallback(item), source)
                self.assertIn('<meta name="robots" content="noindex, follow">', source)
                self.assertIn(f'<link rel="canonical" href="{SITE}{item["destination"]}">', source)
                self.assertIn(f'content="0; url={item["destination"]}"', source)
                self.assertIn("window.location.replace", source)
                self.assertNotIn("hreflang=", source)
                self.assertNotIn("application/ld+json", source)
                self.assertIn('<a class="skip-link" href="#main">', source)
                self.assertIn('<main id="main">', source)
                for token in ("#C41230", "#B8962E", "#0A0A0A", "#1A1A1A", "#FAFAF8"):
                    self.assertIn(token, source)

    def test_nontransactional_noindex_pages_do_not_emit_hreflang(self) -> None:
        allowed = {"thank-you.html", "es/thank-you.html"}
        offenders: list[str] = []
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT).as_posix()
            if ".vercel" in path.relative_to(ROOT).parts:
                continue
            source = path.read_text(encoding="utf-8", errors="ignore")
            if relative in allowed:
                continue
            if re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*noindex', source, re.I) and "hreflang=" in source:
                offenders.append(relative)
        self.assertEqual([], offenders)

    def test_anchorless_fallback_keeps_the_canonical_host_preamble_first(self) -> None:
        host_preamble = deepcopy(self.config["redirects"][:2])
        unrelated = [
            {
                "source": "/unrelated-exact",
                "destination": "/unrelated-target",
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
        items = [
            {
                "source": "/synthetic-legacy-route",
                "destination": "/synthetic-target",
            }
        ]

        rendered = json.loads(render_config(config, items))["redirects"]

        self.assertEqual(host_preamble, rendered[:2])
        self.assertEqual(
            host_preamble + unrelated,
            [rule for rule in rendered if rule["source"] != "/synthetic-legacy-route"],
        )
        self.assertLess(
            next(i for i, rule in enumerate(rendered) if rule["source"] == "/synthetic-legacy-route"),
            next(i for i, rule in enumerate(rendered) if rule["source"] == "/realtor/:slug-nj"),
        )

    def test_sync_is_deterministic(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SYNC), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        doorway = subprocess.run(
            [sys.executable, "scripts/retire_programmatic_doorways.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, doorway.returncode, doorway.stdout + doorway.stderr)
        pipeline = subprocess.run(
            [sys.executable, "tools/sync_ai_sales_pipeline_routes.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, pipeline.returncode, pipeline.stdout + pipeline.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
