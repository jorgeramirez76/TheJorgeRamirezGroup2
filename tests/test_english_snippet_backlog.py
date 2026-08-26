#!/usr/bin/env python3
"""Regression contract for the English/root snippet-length cleanup."""

from __future__ import annotations

import json
import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data" / "english-snippet-backlog.json"
SKIP_DIRS = {".git", "crm", "node_modules", "property-leads-system"}


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


class EnglishSnippetBacklogTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
        cls.pages: dict[str, dict[str, str]] = mapping["pages"]
        cls.retired_pages = set(mapping.get("retired_pages", []))

    def test_mapping_has_exact_original_backlog_scope(self) -> None:
        self.assertEqual(140, len(self.pages))
        self.assertTrue(all(not path.startswith("es/") for path in self.pages))
        self.assertEqual(66, sum("title" in values for values in self.pages.values()))
        self.assertEqual(
            128,
            sum("description" in values for values in self.pages.values()),
        )

    def test_exact_metadata_lengths_and_social_sync(self) -> None:
        for relative, expected in self.pages.items():
            if relative in self.retired_pages:
                continue
            parser = parse(ROOT / relative)

            if "title" in expected:
                self.assertEqual(expected["title"], parser.title.strip(), relative)
                self.assertGreaterEqual(len(expected["title"]), 10, relative)
                self.assertLessEqual(len(expected["title"]), 68, relative)
                if parser.meta("name", "title"):
                    self.assertEqual(
                        expected["title"], parser.meta("name", "title"), relative
                    )
                for field in ("og:title", "twitter:title"):
                    for social_value in parser.social_values(field):
                        self.assertEqual(
                            expected["title"],
                            social_value,
                            f"{relative} {field}",
                        )

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

    def test_touched_page_titles_and_descriptions_are_unique_sitewide(self) -> None:
        title_owners: dict[str, list[str]] = defaultdict(list)
        description_owners: dict[str, list[str]] = defaultdict(list)

        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            parser = parse(path)
            title_owners[parser.title.strip()].append(relative.as_posix())
            description_owners[parser.meta("name", "description")].append(
                relative.as_posix()
            )

        for relative in self.pages:
            if relative in self.retired_pages:
                continue
            parser = parse(ROOT / relative)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
