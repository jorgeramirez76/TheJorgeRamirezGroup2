#!/usr/bin/env python3
"""Keep public structured data tied to the verified Google profile."""

from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_URL = "https://www.google.com/maps?cid=4574397105419981752"
RETIRED_PROFILE_URL = (
    "https://www.google.com/maps/place/"
    "Jorge+Ramirez+Realtor+-+Keller+Williams+Premier+Properties/"
    "@40.7176144,-74.3613942,16z"
)
RENDERERS = (
    ROOT / "scripts" / "render_remaining_english_towns.py",
    ROOT / "scripts" / "remediate_indexable_towns.py",
)


class JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_json_ld = False
        self.blocks: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self.in_json_ld = True
            self.blocks.append("")

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False

    def handle_data(self, data: str) -> None:
        if self.in_json_ld:
            self.blocks[-1] += data


class GoogleBusinessProfileIdentityTests(unittest.TestCase):
    def test_renderers_own_the_verified_profile_url(self) -> None:
        for path in RENDERERS:
            source = path.read_text(encoding="utf-8")
            self.assertIn(PROFILE_URL, source, path.name)
            self.assertNotIn(RETIRED_PROFILE_URL, source, path.name)

    def test_public_agent_schema_uses_verified_profile_url(self) -> None:
        checked: list[str] = []
        paths = [ROOT / "ai-authority.html", ROOT / "es" / "ai-authority.html"]
        paths.extend(sorted((ROOT / "towns").glob("*.html")))

        for path in paths:
            parser = JsonLdParser()
            source = path.read_text(encoding="utf-8")
            self.assertNotIn(RETIRED_PROFILE_URL, source, path.relative_to(ROOT))
            parser.feed(source)
            for block in parser.blocks:
                payload = json.loads(block)
                nodes = payload.get("@graph", [payload])
                for node in nodes:
                    if node.get("@type") != "RealEstateAgent":
                        continue
                    same_as = node.get("sameAs", [])
                    if any("google.com/maps" in value for value in same_as):
                        self.assertIn(PROFILE_URL, same_as, path.relative_to(ROOT))
                        checked.append(path.relative_to(ROOT).as_posix())

        self.assertGreaterEqual(len(checked), 15)

    def test_authority_pages_use_verified_profile_url(self) -> None:
        for relative in (Path("ai-authority.html"), Path("es/ai-authority.html")):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(PROFILE_URL, source, relative)
            self.assertNotIn(RETIRED_PROFILE_URL, source, relative)

    def test_public_contact_links_open_verified_profile(self) -> None:
        for relative in (Path("index.html"), Path("contact.html")):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(f'href="{PROFILE_URL}"', source, relative)


if __name__ == "__main__":
    unittest.main(verbosity=2)
