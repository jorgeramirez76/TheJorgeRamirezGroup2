#!/usr/bin/env python3
"""Regression coverage for top-level routes exposed by legacy blog cards."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = "/sell-your-home"
RECOVERY_ROUTES = {
    "/interior-design-trends-2026-nj-sellers",
    "/interior-design-trends-2026-nj-sellers.html",
    "/affordable-upgrades-home-value-nj-2026",
    "/affordable-upgrades-home-value-nj-2026.html",
}


def compile_source(source: str) -> re.Pattern[str]:
    """Compile the named parameters used by the repository's Vercel routes."""

    pieces: list[str] = []
    cursor = 0
    for match in re.finditer(r":([A-Za-z0-9_]+)(\*)?", source):
        pieces.append(re.escape(source[cursor : match.start()]))
        name, star = match.groups()
        pieces.append(f"(?P<{name}>{'.*' if star else '[^/]+'})")
        cursor = match.end()
    pieces.append(re.escape(source[cursor:]))
    return re.compile("^" + "".join(pieces) + "$")


def substitute(destination: str, values: dict[str, str]) -> str:
    for name, value in values.items():
        destination = destination.replace(f":{name}*", value)
        destination = destination.replace(f":{name}", value)
    return destination


class LiveRelativeCardRedirectRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        cls.redirects = cls.config["redirects"]
        cls.compiled = [
            (rule, compile_source(str(rule["source"]))) for rule in cls.redirects
        ]

    def first_apex_redirect(self, path: str) -> tuple[int, dict, str] | None:
        """Return the first route that applies to an apex-host request."""

        for index, (rule, pattern) in enumerate(self.compiled):
            # Host/query/cookie conditions do not apply to the plain apex URL
            # being recovered by this contract.
            if rule.get("has") or rule.get("missing"):
                continue
            match = pattern.fullmatch(path)
            if match:
                return (
                    index,
                    rule,
                    substitute(str(rule["destination"]), match.groupdict()),
                )
        return None

    def test_all_four_exact_routes_are_unique_permanent_and_direct(self) -> None:
        for source in sorted(RECOVERY_ROUTES):
            matches = [rule for rule in self.redirects if rule.get("source") == source]
            with self.subTest(source=source):
                self.assertEqual(1, len(matches))
                self.assertEqual(DESTINATION, matches[0].get("destination"))
                self.assertIs(True, matches[0].get("permanent"))
                self.assertNotIn("has", matches[0])
                self.assertNotIn("missing", matches[0])

    def test_exact_rules_win_first_match_and_precede_catchalls(self) -> None:
        catchall_indexes = [
            index
            for index, rule in enumerate(self.redirects)
            if rule.get("source") == "/:path*"
        ]
        self.assertTrue(catchall_indexes, "expected the host canonicalization catchalls")

        for source in sorted(RECOVERY_ROUTES):
            result = self.first_apex_redirect(source)
            with self.subTest(source=source):
                self.assertIsNotNone(result)
                index, rule, destination = result
                self.assertEqual(source, rule["source"])
                self.assertEqual(DESTINATION, destination)
                self.assertLess(index, min(catchall_indexes))

    def test_clean_urls_and_raw_html_requests_both_resolve_one_hop(self) -> None:
        self.assertIs(True, self.config.get("cleanUrls"))
        for html_source in sorted(route for route in RECOVERY_ROUTES if route.endswith(".html")):
            clean_source = html_source.removesuffix(".html")
            with self.subTest(source=html_source):
                raw_result = self.first_apex_redirect(html_source)
                normalized_result = self.first_apex_redirect(clean_source)
                self.assertIsNotNone(raw_result)
                self.assertIsNotNone(normalized_result)
                self.assertEqual(DESTINATION, raw_result[2])
                self.assertEqual(DESTINATION, normalized_result[2])

        self.assertIsNone(
            self.first_apex_redirect(DESTINATION),
            "the recovery destination must not start another redirect hop",
        )

    def test_destination_is_the_indexable_self_canonical_seller_page(self) -> None:
        target = ROOT / "sell-your-home.html"
        source = target.read_text(encoding="utf-8")
        self.assertNotRegex(
            source,
            r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex',
        )
        self.assertNotRegex(source, r'<meta\b[^>]*http-equiv=["\']refresh["\']')
        canonical = re.search(
            r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)',
            source,
            re.IGNORECASE,
        )
        self.assertIsNotNone(canonical)
        self.assertEqual(DESTINATION, urlsplit(canonical.group(1)).path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
