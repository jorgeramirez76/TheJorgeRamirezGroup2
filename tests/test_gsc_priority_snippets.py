#!/usr/bin/env python3
"""Contract for the GSC-prioritized title and description refresh."""

from __future__ import annotations

import json
import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data" / "gsc-priority-snippets.json"
QUARANTINE = ROOT / "data" / "english-fair-housing-quarantine.json"
SITE = "https://thejorgeramirezgroup.com"


class HeadParser(HTMLParser):
    """Collect only metadata needed by the snippet contract."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title = ""
        self.metas: list[dict[str, str]] = []
        self.canonical = ""

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            self.metas.append(values)
        elif tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonical = values.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data

    def meta(self, field: str) -> str:
        attribute, value = field.split(":", 1)
        for item in self.metas:
            if item.get(attribute, "").lower() == value:
                return item.get("content", "")
        return ""


class GscPrioritySnippetTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
        cls.quarantined = {
            page["file"]: page
            for page in json.loads(QUARANTINE.read_text(encoding="utf-8"))["pages"]
        }

    def test_mapping_reconciles_canonicalized_gsc_totals(self) -> None:
        pages = self.mapping["pages"]
        self.assertEqual(20, self.mapping["selected_canonical_pages"])
        self.assertEqual(20, len(pages))
        self.assertEqual(20, len({page["file"] for page in pages}))
        self.assertEqual(20, len({page["canonical"] for page in pages}))

        for page in pages:
            self.assertEqual(
                page["last_three_month_impressions"],
                sum(row["impressions"] for row in page["source_rows"]),
                page["file"],
            )
            self.assertEqual(
                page["last_three_month_clicks"],
                sum(row["clicks"] for row in page["source_rows"]),
                page["file"],
            )

        self.assertEqual(
            self.mapping["aggregate_last_three_month_impressions"],
            sum(page["last_three_month_impressions"] for page in pages),
        )
        self.assertEqual(
            self.mapping["aggregate_last_three_month_clicks"],
            sum(page["last_three_month_clicks"] for page in pages),
        )
        self.assertEqual(70443, self.mapping["aggregate_last_three_month_impressions"])
        self.assertEqual(336, self.mapping["aggregate_last_three_month_clicks"])

    def test_priority_pages_use_unique_snippet_ready_metadata(self) -> None:
        titles: list[str] = []
        descriptions: list[str] = []

        for page in self.mapping["pages"]:
            parser = HeadParser()
            parser.feed((ROOT / page["file"]).read_text(encoding="utf-8"))
            expected = page["after"]

            if page["file"] in self.quarantined:
                archived = self.quarantined[page["file"]]
                self.assertIn("noindex", parser.meta("name:robots").lower())
                self.assertEqual(SITE + archived["destination"], parser.canonical)
                continue

            self.assertNotEqual(page["before"], expected, page["file"])
            self.assertEqual(expected["title"], parser.title.strip(), page["file"])
            self.assertEqual(
                expected["description"],
                parser.meta("name:description"),
                page["file"],
            )
            self.assertEqual(page["canonical"], parser.canonical, page["file"])
            self.assertGreaterEqual(len(expected["title"]), 10, page["file"])
            self.assertLessEqual(len(expected["title"]), 68, page["file"])
            self.assertGreaterEqual(len(expected["description"]), 40, page["file"])
            self.assertLessEqual(len(expected["description"]), 165, page["file"])

            for field in page["sync_fields"]:
                expected_value = (
                    expected["description"]
                    if field.endswith(":description")
                    else expected["title"]
                )
                self.assertEqual(expected_value, parser.meta(field), page["file"])

            titles.append(expected["title"])
            descriptions.append(expected["description"])

        self.assertEqual(len(titles), len(set(titles)), "priority titles must be unique")
        self.assertEqual(
            len(descriptions),
            len(set(descriptions)),
            "priority descriptions must be unique",
        )

        title_owners: dict[str, list[str]] = defaultdict(list)
        description_owners: dict[str, list[str]] = defaultdict(list)
        skip_dirs = {
            ".git",
            ".vercel",
            "crm",
            "node_modules",
            "property-leads-system",
        }
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT)
            if any(part in skip_dirs for part in relative.parts):
                continue
            parser = HeadParser()
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
            if "noindex" in parser.meta("name:robots").lower():
                continue
            title_owners[parser.title.strip()].append(relative.as_posix())
            description_owners[parser.meta("name:description")].append(
                relative.as_posix()
            )

        for page in self.mapping["pages"]:
            if page["file"] in self.quarantined:
                continue
            self.assertEqual(
                [page["file"]],
                title_owners[page["after"]["title"]],
                f"title is duplicated: {page['after']['title']}",
            )
            self.assertEqual(
                [page["file"]],
                description_owners[page["after"]["description"]],
                f"description is duplicated: {page['after']['description']}",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
