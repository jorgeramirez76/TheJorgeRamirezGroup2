from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
HUBS = (
    "blog/index.html",
    "es/blog/index.html",
    "counties/index.html",
    "thank-you.html",
    "es/thank-you.html",
)
BLOG_HUBS = ("blog/index.html", "es/blog/index.html")
CANONICALS = {
    "blog/index.html": "https://thejorgeramirezgroup.com/blog",
    "es/blog/index.html": "https://thejorgeramirezgroup.com/es/blog",
    "counties/index.html": "https://thejorgeramirezgroup.com/counties",
    "thank-you.html": "https://thejorgeramirezgroup.com/thank-you",
    "es/thank-you.html": "https://thejorgeramirezgroup.com/es/thank-you",
}
JSON_LD = re.compile(
    r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class VisibleTextParser(HTMLParser):
    SKIP = {"head", "script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())


class DirectoryLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_directory = False
        self.nested_sections = 0
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "section":
            if self.in_directory:
                self.nested_sections += 1
            elif attributes.get("id") == "blog-directory":
                self.in_directory = True
                return
        if self.in_directory and tag == "a" and attributes.get("href"):
            split = urlsplit(attributes["href"])
            self.hrefs.append(split.path.rstrip("/") or "/")

    def handle_endtag(self, tag: str) -> None:
        if tag != "section" or not self.in_directory:
            return
        if self.nested_sections:
            self.nested_sections -= 1
        else:
            self.in_directory = False


def visible_text(source: str) -> str:
    parser = VisibleTextParser()
    parser.feed(source)
    return " ".join(parser.parts)


def directory_hrefs(source: str) -> list[str]:
    parser = DirectoryLinkParser()
    parser.feed(source)
    return parser.hrefs


def json_ld(source: str) -> list[dict]:
    return [json.loads(match) for match in JSON_LD.findall(source)]


class ContentHubCleanupTests(unittest.TestCase):
    def test_all_owned_hubs_use_truthful_provenance_and_brand_tokens(self) -> None:
        declaration = '<meta name="ai-content-declaration" content="ai-assisted, source-checked">'
        for relative in HUBS:
            with self.subTest(path=relative):
                source = read(relative)
                self.assertEqual(1, source.count(declaration))
                self.assertNotIn("human-authored", source.lower())
                for token in ("#C41230", "#B8962E", "#FAFAF8", "Playfair Display", "Inter"):
                    self.assertIn(token, source, f"{relative}: missing brand token {token}")

    def test_canonicals_and_noindex_semantics_are_preserved(self) -> None:
        for relative, canonical in CANONICALS.items():
            with self.subTest(path=relative):
                source = read(relative)
                self.assertIn(f'<link rel="canonical" href="{canonical}">', source)
        for relative in BLOG_HUBS + ("counties/index.html",):
            self.assertRegex(read(relative), r'<meta name="robots" content="index, follow')
        for relative in ("thank-you.html", "es/thank-you.html"):
            self.assertRegex(read(relative), r'<meta name="robots" content="noindex(?:[,"]|$)')

    def test_blog_directories_have_unique_maintained_destinations(self) -> None:
        minimums = {"blog/index.html": 50, "es/blog/index.html": 40}
        for relative in BLOG_HUBS:
            with self.subTest(path=relative):
                hrefs = directory_hrefs(read(relative))
                self.assertGreaterEqual(len(hrefs), minimums[relative])
                duplicates = {href: count for href, count in Counter(hrefs).items() if count > 1}
                self.assertEqual({}, duplicates)
                missing = []
                for href in hrefs:
                    path = href.lstrip("/")
                    candidates = (ROOT / f"{path}.html", ROOT / path / "index.html")
                    if not any(candidate.is_file() for candidate in candidates):
                        missing.append(href)
                self.assertEqual([], missing)

    def test_rent_versus_buy_links_use_the_maintained_routes(self) -> None:
        english = read("blog/index.html")
        spanish = read("es/blog/index.html")
        self.assertIn('href="/rent-vs-buy-nj"', english)
        self.assertIn('href="/es/rent-vs-buy-nj"', spanish)
        self.assertNotIn("/blog/renting-vs-buying-nj-2026", english)
        self.assertNotIn("/es/blog/renting-vs-buying-nj-2026", spanish)

    def test_visible_hub_copy_excludes_stale_and_risky_claims(self) -> None:
        forbidden = {
            "blog/index.html": (
                "$563k",
                "67.7%",
                "all 183 guides",
                "homes that sell fastest",
                "they are the cleanest",
                "school district analysis",
                "public data, safety & value",
                "home prices ranked",
                "why new yorkers are flooding",
                "lowest-tax commuter towns",
                "which makes more money",
                "every town with a direct train to",
                "absentee owners &",
            ),
            "es/blog/index.html": (
                "las 180 guías",
                "las casas que se venden más rápido",
                "son las más limpias",
                "análisis de distritos escolares",
                "mercados más rápidos",
                "muchos se arrepienten",
                "¿cuál gana más dinero?",
                "¿qué ciudad es mejor para ti?",
                "cada pueblo con tren directo",
            ),
            "counties/index.html": (
                "each county has its own personality",
                "price band, and buyer profile",
                "urban-lifestyle end",
                "meaningful discount",
                "priced out of brooklyn",
                "flagship school towns",
                "families upgrading",
                "forever-home phase",
                "nyc exiles",
                "want a real yard",
            ),
        }
        for relative, phrases in forbidden.items():
            text = " ".join(visible_text(read(relative)).lower().split())
            for phrase in phrases:
                with self.subTest(path=relative, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_county_hub_is_objective_and_has_no_legacy_blue_styles(self) -> None:
        source = read("counties/index.html")
        text = visible_text(source).lower()
        self.assertNotIn("#1a4f8b", source.lower())
        for phrase in ("property-specific", "official transit", "housing choice remains yours"):
            self.assertIn(phrase, text)
        self.assertIn("it is not a neighborhood ranking or recommendation", text)

    def test_json_ld_is_valid_and_spanish_hub_schema_matches_page_type(self) -> None:
        for relative in HUBS:
            with self.subTest(path=relative):
                self.assertTrue(json_ld(read(relative)))

        spanish = json_ld(read("es/blog/index.html"))
        nodes = []
        for item in spanish:
            nodes.extend(item.get("@graph", [item]))
        types = {node.get("@type") for node in nodes}
        self.assertIn("Blog", types)
        self.assertIn("CollectionPage", types)
        self.assertIn("BreadcrumbList", types)
        self.assertNotIn("BlogPosting", types)
        languages = {node.get("inLanguage") for node in nodes if node.get("inLanguage")}
        self.assertEqual({"es-US"}, languages)
        collection = next(node for node in nodes if node.get("@type") == "CollectionPage")
        self.assertEqual("2026-08-27", collection.get("dateModified"))


if __name__ == "__main__":
    unittest.main()
