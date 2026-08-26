#!/usr/bin/env python3
"""Regression contract for the reviewed Spanish snippet-length cleanup."""

from __future__ import annotations

import importlib.util
import json
import re
import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data" / "spanish-snippet-backlog.json"
SCRIPT = ROOT / "scripts" / "apply_spanish_snippets.py"
SPANISH_TOWN_MANIFEST = ROOT / "data" / "spanish-town-risk-decisions.json"
SKIP_DIRS = {".git", "crm", "node_modules", "property-leads-system"}

ENGLISH_BOILERPLATE = re.compile(
    r"\b(?:real estate|market report|buying (?:a )?home|selling (?:a )?home|"
    r"home buyer|home seller|school district|call jorge|ranked by|best towns|"
    r"top towns|free guide)\b",
    re.IGNORECASE,
)
UNSUPPORTED_OR_STEERING = re.compile(
    r"\b(?:mejor(?:es)?|máxim[oa]s?|garantiz\w*|comprobad\w*|"
    r"expert[oa]s?|familias?|top|best|ranked)\b",
    re.IGNORECASE,
)
UNSUPPORTED_NUMBER = re.compile(
    r"(?:\$\s?[\d,.]+|\b\d+\s*(?:minutos?|min|días?)\b|\b\d+\s*/\s*10\b)",
    re.IGNORECASE,
)


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title = ""
        self.metas: list[dict[str, str]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            self.metas.append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data

    def meta(self, attribute: str, value: str) -> str:
        for item in self.metas:
            if item.get(attribute, "").lower() == value:
                return item.get("content", "")
        return ""

    def social_values(self, field: str) -> list[str]:
        return [
            item.get("content", "")
            for item in self.metas
            if (item.get("name") or item.get("property") or "").lower() == field
        ]


def parse(path: Path) -> HeadParser:
    parser = HeadParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser


class SpanishSnippetBacklogTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
        cls.pages: dict[str, dict[str, str]] = cls.mapping["pages"]
        town_manifest = json.loads(SPANISH_TOWN_MANIFEST.read_text(encoding="utf-8"))
        cls.managed_town_paths = {
            f"es/towns/{slug}.html" for slug in town_manifest["decisions"]
        }

    def test_mapping_has_exact_original_backlog_scope(self) -> None:
        self.assertEqual(self.mapping["expected_pages"], len(self.pages))
        self.assertEqual(36, len(self.pages))
        self.assertTrue(all(path.startswith("es/") for path in self.pages))
        self.assertEqual(
            self.mapping["expected_title_updates"],
            sum("title" in values for values in self.pages.values()),
        )
        self.assertEqual(15, self.mapping["expected_title_updates"])
        self.assertEqual(
            self.mapping["expected_description_updates"],
            sum("description" in values for values in self.pages.values()),
        )
        self.assertEqual(25, self.mapping["expected_description_updates"])

    def test_exact_values_lengths_and_existing_social_tags_are_synced(self) -> None:
        for relative, expected in self.pages.items():
            if relative in self.managed_town_paths:
                source = (ROOT / relative).read_text(encoding="utf-8")
                self.assertRegex(
                    source,
                    r'data-spanish-town-(?:guide|fallback|redirect)="v1"',
                    relative,
                )
                continue
            parser = parse(ROOT / relative)
            if "noindex" in parser.meta("name", "robots").lower():
                # Managed fair-housing fallbacks intentionally replace obsolete
                # indexable snippets with a compact archive metadata contract.
                continue

            if "title" in expected:
                title = expected["title"]
                self.assertEqual(title, parser.title.strip(), relative)
                self.assertGreaterEqual(len(title), 10, relative)
                self.assertLessEqual(len(title), 68, relative)
                for field in ("og:title", "twitter:title"):
                    for social_value in parser.social_values(field):
                        self.assertEqual(title, social_value, f"{relative} {field}")

            if "description" in expected:
                description = parser.meta("name", "description")
                self.assertEqual(expected["description"], description, relative)
                self.assertGreaterEqual(len(description), 40, relative)
                self.assertLessEqual(len(description), 165, relative)
                for field in ("og:description", "twitter:description"):
                    for social_value in parser.social_values(field):
                        self.assertEqual(
                            description,
                            social_value,
                            f"{relative} {field}",
                        )

    def test_reviewed_values_avoid_boilerplate_and_unsupported_claims(self) -> None:
        for relative, metadata in self.pages.items():
            for field, value in metadata.items():
                self.assertIsNone(
                    ENGLISH_BOILERPLATE.search(value),
                    f"English boilerplate in {relative} {field}: {value}",
                )
                self.assertIsNone(
                    UNSUPPORTED_OR_STEERING.search(value),
                    f"unsupported or steering language in {relative} {field}: {value}",
                )
                self.assertIsNone(
                    UNSUPPORTED_NUMBER.search(value),
                    f"unsupported number in {relative} {field}: {value}",
                )

    def test_touched_page_metadata_is_unique_sitewide(self) -> None:
        title_owners: dict[str, list[str]] = defaultdict(list)
        description_owners: dict[str, list[str]] = defaultdict(list)

        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            parser = parse(path)
            if "noindex" in parser.meta("name", "robots").lower():
                continue
            title_owners[parser.title.strip()].append(relative.as_posix())
            description_owners[parser.meta("name", "description")].append(
                relative.as_posix()
            )

        for relative in self.pages:
            if relative in self.managed_town_paths:
                continue
            parser = parse(ROOT / relative)
            if "noindex" in parser.meta("name", "robots").lower():
                continue
            self.assertEqual(
                [relative],
                title_owners[parser.title.strip()],
                f"duplicate title: {parser.title.strip()}",
            )
            self.assertEqual(
                [relative],
                description_owners[parser.meta("name", "description")],
                f"duplicate description: {parser.meta('name', 'description')}",
            )

    def test_renderer_handles_alternate_meta_markup_and_is_idempotent(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        spec = importlib.util.spec_from_file_location("apply_spanish_snippets", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader if spec else None)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        sample = """<!doctype html><html><head>
<title>Título anterior</title>
<meta content='Descripción anterior' name='description'>
<meta content='Título anterior' name='og:title'>
<meta property='og:title' content='Título anterior'>
<meta name='twitter:title' content='Título anterior'>
<meta content='Descripción anterior' name='og:description'>
<meta property='og:description' content='Descripción anterior'>
<meta name='twitter:description' content='Descripción anterior'>
</head></html>"""
        expected = {
            "title": "Título de prueba en español",
            "description": "Descripción de prueba en español para comprobar el reemplazo.",
        }
        once = module.render(sample, expected)
        twice = module.render(once, expected)
        self.assertEqual(once, twice)

        parser = HeadParser()
        parser.feed(once)
        self.assertEqual(expected["title"], parser.title.strip())
        self.assertEqual(expected["description"], parser.meta("name", "description"))
        self.assertEqual(
            [expected["title"], expected["title"]],
            parser.social_values("og:title"),
        )
        self.assertEqual(
            [expected["description"], expected["description"]],
            parser.social_values("og:description"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
