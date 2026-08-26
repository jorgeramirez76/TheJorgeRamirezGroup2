#!/usr/bin/env python3
"""Fail-closed contracts for stable person and business JSON-LD identities."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://thejorgeramirezgroup.com"
BUSINESS_ID = f"{ORIGIN}/#agent"
PERSON_ID = f"{ORIGIN}/#jorge-ramirez"
SKIP_DIRS = {".git", "node_modules", "crm", "docs", "property-leads-system", "staging"}
PERSON_REFERENCE_KEYS = {"author", "creator", "founder", "mainEntity"}
JSON_LD_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def public_html_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if not (set(path.relative_to(ROOT).parts) & SKIP_DIRS)
    )


def jsonld_payloads(path: Path) -> list[object]:
    source = path.read_text(encoding="utf-8", errors="strict")
    return [json.loads(raw) for raw in JSON_LD_RE.findall(source)]


def walk(value: object, parent_key: str | None = None):
    if isinstance(value, dict):
        yield value, parent_key
        for key, child in value.items():
            yield from walk(child, key)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child, parent_key)


def entity_types(node: dict) -> set[str]:
    value = node.get("@type")
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    return set()


def represents_jorge(node: dict) -> bool:
    types = entity_types(node)
    return node.get("name") == "Jorge Ramirez" and bool(
        types & {"Person", "RealEstateAgent"}
    )


class SchemaEntityIdentityTests(unittest.TestCase):
    def test_named_person_nodes_share_one_stable_identifier(self) -> None:
        personal_nodes: list[str] = []
        for path in public_html_files():
            for payload in jsonld_payloads(path):
                for node, _ in walk(payload):
                    if represents_jorge(node):
                        personal_nodes.append(str(path.relative_to(ROOT)))
                        self.assertEqual(
                            PERSON_ID,
                            node.get("@id"),
                            f"personal entity drift in {path.relative_to(ROOT)}",
                        )
        self.assertTrue(personal_nodes, "no Jorge person entities were found")

    def test_business_identifier_never_represents_or_references_the_person(self) -> None:
        business_occurrences = 0
        for path in public_html_files():
            for payload in jsonld_payloads(path):
                for node, parent_key in walk(payload):
                    if node.get("@id") != BUSINESS_ID:
                        continue
                    business_occurrences += 1
                    self.assertFalse(
                        represents_jorge(node),
                        f"business ID assigned to Jorge in {path.relative_to(ROOT)}",
                    )
                    self.assertFalse(
                        set(node) == {"@id"} and parent_key in PERSON_REFERENCE_KEYS,
                        f"business ID used as {parent_key} in {path.relative_to(ROOT)}",
                    )
        self.assertGreater(business_occurrences, 0)

    def test_verified_business_contract_retains_business_identifier(self) -> None:
        standalone = json.loads((ROOT / "schema-realtor.json").read_text(encoding="utf-8"))
        self.assertEqual(BUSINESS_ID, standalone["@id"])
        self.assertEqual("The Jorge Ramirez Group", standalone["name"])

        for relative in ("index.html", "es/index.html"):
            agents = []
            for payload in jsonld_payloads(ROOT / relative):
                agents.extend(
                    node
                    for node, _ in walk(payload)
                    if "RealEstateAgent" in entity_types(node)
                    and node.get("@id") == BUSINESS_ID
                )
            self.assertEqual(1, len(agents), relative)
            self.assertEqual("The Jorge Ramirez Group", agents[0].get("name"), relative)

    def test_schema_identifier_synchronizer_has_no_drift(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "sync_schema_entity_ids.py"), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_person_schema_generators_emit_the_person_identifier(self) -> None:
        generators = (
            "generate_new_landing_pages.py",
            "scripts/rebuild_commuter_suburbs_guide.py",
            "tools/blog-automation/daily_blog.py",
            "tools/generate_county_market_research.py",
            "tools/generate_high_value_legal_fair_housing.py",
            "tools/generate_seller_editorial_rebuild.py",
            "tools/generate_town_market_research_essex_middlesex.py",
            "tools/generate_union_morris_town_market_research.py",
            "tools/render_top_level_town_comparisons.py",
        )
        for relative in generators:
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("#jorge-ramirez", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
