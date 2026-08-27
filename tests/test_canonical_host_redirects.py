#!/usr/bin/env python3
"""Fail-closed contract for serving one public hostname on Vercel."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_HOST = "thejorgeramirezgroup.com"
CANONICAL_ORIGIN = f"https://{CANONICAL_HOST}"
WWW_HOST = "www.thejorgeramirezgroup.com"
VERCEL_HOST = "thejorgeramirezgroup.vercel.app"


def condition_matches(condition: dict, hostname: str) -> bool:
    if condition.get("type") != "host":
        return False
    value = condition.get("value")
    if isinstance(value, str):
        return re.fullmatch(value, hostname) is not None
    if not isinstance(value, dict):
        return False
    if set(value) == {"eq"}:
        return hostname == value["eq"]
    if set(value) == {"suf"}:
        return hostname.endswith(str(value["suf"]))
    return False


def rule_matches_host(rule: dict, hostname: str) -> bool:
    conditions = rule.get("has", [])
    return len(conditions) == 1 and condition_matches(conditions[0], hostname)


def match_source(source: str, path: str) -> re.Match[str] | None:
    if source == "/(.*)":
        return re.fullmatch(source, path)
    if source == path:
        return re.fullmatch(re.escape(source), path)
    return None


def apply_redirect(rule: dict, path: str) -> str | None:
    match = match_source(str(rule.get("source", "")), path)
    if match is None:
        return None
    destination = str(rule.get("destination", ""))
    for index, value in enumerate(match.groups(), start=1):
        destination = destination.replace(f"${index}", value)
    return destination


class CanonicalHostRedirectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.redirects = json.loads(
            (ROOT / "vercel.json").read_text(encoding="utf-8")
        )["redirects"]
        cls.host_rules = [
            rule
            for rule in cls.redirects
            if rule.get("source") == "/(.*)"
            and rule.get("destination") == f"{CANONICAL_ORIGIN}/$1"
            and any(condition.get("type") == "host" for condition in rule.get("has", []))
        ]

    def first_redirect(self, hostname: str, path: str) -> tuple[int, dict, str] | None:
        for index, rule in enumerate(self.redirects):
            if rule.get("has") and not rule_matches_host(rule, hostname):
                continue
            if rule.get("missing"):
                continue
            destination = apply_redirect(rule, path)
            if destination is not None:
                return index, rule, destination
        return None

    def test_www_and_all_vercel_hosts_are_permanent_first_match_guards(self) -> None:
        self.assertEqual(2, len(self.host_rules))
        self.assertEqual(self.host_rules, self.redirects[:2])
        self.assertEqual(
            [{"eq": WWW_HOST}, {"suf": ".vercel.app"}],
            [rule["has"][0]["value"] for rule in self.host_rules],
        )
        for rule in self.host_rules:
            self.assertEqual("/(.*)", rule["source"])
            self.assertEqual(f"{CANONICAL_ORIGIN}/$1", rule["destination"])
            self.assertIs(True, rule.get("permanent"))
            self.assertNotIn("statusCode", rule)

        for hostname in (
            WWW_HOST,
            VERCEL_HOST,
            "thejorgeramirezgroup-git-main-example.vercel.app",
            "nested.preview.vercel.app",
        ):
            with self.subTest(hostname=hostname):
                self.assertEqual(
                    1,
                    sum(rule_matches_host(rule, hostname) for rule in self.host_rules),
                )

    def test_root_nested_paths_and_queries_keep_the_same_public_address(self) -> None:
        query = "utm_source=canonical-test&lead=1"
        for hostname in (WWW_HOST, VERCEL_HOST, "preview.branch.vercel.app"):
            for path in ("/", "/towns/summit", "/es/blog/nj-property-tax-guide"):
                with self.subTest(hostname=hostname, path=path):
                    result = self.first_redirect(hostname, path)
                    self.assertIsNotNone(result)
                    index, rule, destination = result
                    self.assertLess(index, 2)
                    self.assertEqual(CANONICAL_ORIGIN + path, destination)
                    self.assertNotIn("?", rule["destination"])
                    self.assertEqual(f"{CANONICAL_ORIGIN}{path}?{query}", f"{destination}?{query}")

    def test_apex_and_lookalike_hosts_cannot_enter_a_redirect_loop(self) -> None:
        for hostname in (
            CANONICAL_HOST,
            "notvercel.app",
            "vercel.app",
            "preview.vercel.app.example.com",
            "www.thejorgeramirezgroup.com.example.com",
        ):
            with self.subTest(hostname=hostname):
                self.assertFalse(
                    any(rule_matches_host(rule, hostname) for rule in self.host_rules)
                )
        self.assertIsNone(self.first_redirect(CANONICAL_HOST, "/"))

    def test_host_guard_precedes_legacy_and_ai_sales_pipeline_redirects(self) -> None:
        cases = {
            "/nj-real-estate-agent": "/ai-authority",
            "/features/ai-email": (
                "https://aisalespipeline.com/features/ai-email-real-estate.html"
            ),
        }
        for path, apex_destination in cases.items():
            with self.subTest(path=path, host=CANONICAL_HOST):
                result = self.first_redirect(CANONICAL_HOST, path)
                self.assertIsNotNone(result)
                index, rule, destination = result
                self.assertGreaterEqual(index, 2)
                self.assertEqual(path, rule["source"])
                self.assertFalse(rule.get("has"))
                self.assertEqual(apex_destination, destination)

            for hostname in (WWW_HOST, VERCEL_HOST):
                with self.subTest(path=path, host=hostname):
                    result = self.first_redirect(hostname, path)
                    self.assertIsNotNone(result)
                    index, rule, destination = result
                    self.assertLess(index, 2)
                    self.assertTrue(rule.get("has"))
                    self.assertEqual(CANONICAL_ORIGIN + path, destination)


if __name__ == "__main__":
    unittest.main(verbosity=2)
