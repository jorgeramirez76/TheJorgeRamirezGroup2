#!/usr/bin/env python3
"""Release gates for the bilingual top-level town-comparison rebuild."""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
REVIEWED = "2026-08-26"
MANIFEST = ROOT / "data" / "top-level-town-comparison-sources.json"
RENDERER = ROOT / "tools" / "render_top_level_town_comparisons.py"
SOURCE_CHECKER = ROOT / "tools" / "check_top_level_comparison_sources.py"
STYLESHEET = ROOT / "css" / "top-level-town-comparisons.css"

SLUGS = (
    "chatham-vs-madison-nj",
    "cranford-vs-garwood-nj",
    "cranford-vs-westfield-nj",
    "jersey-city-vs-hoboken-nj",
    "millburn-vs-summit-nj",
    "montclair-vs-glen-ridge-nj",
    "montclair-vs-maplewood-nj",
    "new-providence-vs-berkeley-heights-nj",
    "short-hills-vs-chatham-nj",
    "short-hills-vs-westfield-nj",
    "summit-vs-new-providence-nj",
)

PAGES = tuple(
    item
    for slug in SLUGS
    for item in (f"{slug}.html", f"es/{slug}.html")
)

OFFICIAL_HOSTS = {
    "garwood.org",
    "hobokennj.gov",
    "www.hobokennj.gov",
    "www.berkeleyheights.gov",
    "www.chathamborough.org",
    "www.cityofsummit.org",
    "www.cranfordnj.org",
    "www.glenridgenj.org",
    "www.jerseycitynj.gov",
    "www.maplewoodnj.gov",
    "www.montclairnjusa.org",
    "www.newprov.us",
    "www.nj.gov",
    "www.njtransit.com",
    "www.rosenet.org",
    "www.twp.millburn.nj.us",
    "www.westfieldnj.gov",
    "chathamtownship.org",
}

BANNED_COPY = re.compile(
    r"(?:"
    r"\b(?:best|better|winner|ideal|perfect|fit|fits|audience|demographic)\b|"
    r"\b(?:family|families|children|kids|young professionals|retirees?)\b|"
    r"\b(?:safe|safest|crime|low[- ]crime|school quality|better schools?|top[- ]rated schools?)\b|"
    r"\b(?:mejor|mejores|ganador[ae]?|ideal|perfect[oa]|encaja|audiencia|demogr[aá]fic[oa])\b|"
    r"\b(?:familias?|ni[nñ]os?|j[oó]venes profesionales|jubilad[oa]s?)\b|"
    r"\b(?:segur[oa]s?|criminalidad|calidad escolar|mejores escuelas?)\b|"
    r"\b(?:appreciat(?:e|ion)|outperform|return on investment|investment upside)\b|"
    r"\b(?:apreciaci[oó]n|superar[aá]?|retorno de inversi[oó]n|potencial de inversi[oó]n)\b|"
    r"\b(?:exact commute|commute time|travel time)\b|"
    r"\b(?:tiempo exacto de viaje|tiempo de traslado)\b|"
    r"\$\s?\d|\b\d+(?:\.\d+)?\s*%|\b\d+\s*(?:minutes?|mins?|minutos?)\b|"
    r"\b(?:ranked?|ranking|clasificad[oa]s?|clasificaci[oó]n)\b"
    r")",
    re.I,
)

BANNED_STYLE = (
    "#3498db",
    "#2980b9",
    "#1e90ff",
    "#2c3e50",
    "#f0f4ff",
    "rgb(52, 152, 219)",
)


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, list[tuple[str, str | None]], dict[str, str]]] = []
        self.visible: list[str] = []
        self.json_blocks: list[str] = []
        self._hidden = 0
        self._json = False
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.tags.append((tag, attrs, values))
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json = True
            self._json_parts = []
        elif tag in {"script", "style", "template", "noscript"}:
            self._hidden += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, attrs, {key: value or "" for key, value in attrs}))

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json:
            self.json_blocks.append("".join(self._json_parts).strip())
            self._json = False
            self._json_parts = []
        elif tag in {"script", "style", "template", "noscript"} and self._hidden:
            self._hidden -= 1

    def handle_data(self, data: str) -> None:
        if self._json:
            self._json_parts.append(data)
        elif not self._hidden:
            value = " ".join(data.split())
            if value:
                self.visible.append(value)

    def attrs(self, tag: str) -> list[dict[str, str]]:
        return [values for current, _, values in self.tags if current == tag]

    @property
    def text(self) -> str:
        return " ".join(self.visible)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def parse(relative: str) -> Parser:
    value = Parser()
    value.feed(read(relative))
    return value


def schema_nodes(value: object):
    if isinstance(value, dict):
        if "@type" in value:
            yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


def schema_types(node: dict[str, object]) -> set[str]:
    value = node.get("@type")
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    return set()


def local_target(href: str) -> Path | None:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not parts.path.startswith("/"):
        return None
    decoded = unquote(parts.path)
    if decoded in {"", "/"}:
        return ROOT / "index.html"
    candidate = ROOT / decoded.lstrip("/")
    if candidate.suffix:
        return candidate
    if candidate.is_dir() and (candidate / "index.html").exists():
        return candidate / "index.html"
    return candidate.with_suffix(".html")


class TopLevelTownComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_current_primary_and_complete(self) -> None:
        self.assertTrue(SOURCE_CHECKER.exists(), "live official-source checker is missing")
        self.assertEqual(REVIEWED, self.manifest["reviewed"])
        self.assertEqual(set(SLUGS), set(self.manifest["comparisons"]))
        self.assertEqual(
            {"maplewood-vs-montclair-nj": "montclair-vs-maplewood-nj"},
            self.manifest["redirects"],
        )
        self.assertEqual(14, len(self.manifest["places"]))
        source_records = [*self.manifest["shared_sources"]]
        for key, place in self.manifest["places"].items():
            with self.subTest(place=key):
                self.assertEqual({"en", "es"}, set(place["copy"]))
                self.assertGreaterEqual(len(place["sources"]), 1)
                source_records.extend(place["sources"])
        for record in source_records:
            with self.subTest(url=record["url"]):
                self.assertEqual(
                    {"id", "publisher", "url", "fact_supported", "accessed"},
                    set(record),
                )
                self.assertEqual(REVIEWED, record["accessed"])
                self.assertIn((urlsplit(record["url"]).hostname or "").lower(), OFFICIAL_HOSTS)
                self.assertGreaterEqual(len(record["fact_supported"]), 28)
        for slug, comparison in self.manifest["comparisons"].items():
            with self.subTest(slug=slug):
                self.assertIn(comparison["left"], self.manifest["places"])
                self.assertIn(comparison["right"], self.manifest["places"])
                self.assertEqual({"en", "es"}, set(comparison["copy"]))

    def test_brand_stylesheet_matches_homepage_system(self) -> None:
        css = STYLESHEET.read_text(encoding="utf-8")
        compact = re.sub(r"\s+", "", css).lower()
        for color in (
            "#0A0A0A",
            "#1A1A1A",
            "#C41230",
            "#8B0D22",
            "#B8962E",
            "#D4AF5A",
            "#FAFAF8",
            "#F8F6F2",
        ):
            self.assertIn(color.lower(), css.lower())
        self.assertIn("'Playfair Display'", css)
        self.assertIn("'Inter'", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertRegex(css, r"@media\s*\(max-width:\s*480px\)")
        self.assertIn("min-height:44px", compact)
        header_nav = re.search(r"\.tc-header-nav\s*\{([^}]*)\}", css, re.S)
        self.assertIsNotNone(header_nav)
        header_nav_rules = re.sub(r"\s+", "", header_nav.group(1)).lower()
        for reset in ("position:static", "width:auto", "padding:0", "background:transparent"):
            self.assertIn(reset, header_nav_rules)
        for banned in BANNED_STYLE:
            self.assertNotIn(banned, css.lower())
        for relative in PAGES:
            raw = read(relative)
            self.assertIn('srcset="/images/jorge-logo.webp"', raw)
            self.assertIn('href="/css/styles.css"', raw)
            self.assertIn('href="/css/top-level-town-comparisons.css"', raw)
            self.assertLess(
                raw.index('href="/css/styles.css"'),
                raw.index('href="/css/top-level-town-comparisons.css"'),
            )
            self.assertNotIn("<style", raw.lower())
            for banned in BANNED_STYLE:
                self.assertNotIn(banned, raw.lower())

    def test_indexable_pages_have_reciprocal_metadata_and_structure(self) -> None:
        for relative in PAGES:
            with self.subTest(relative=relative):
                page = parse(relative)
                raw = read(relative)
                slug = Path(relative).stem
                en_url = f"https://thejorgeramirezgroup.com/{slug}"
                es_url = f"https://thejorgeramirezgroup.com/es/{slug}"
                canonical = es_url if relative.startswith("es/") else en_url
                self.assertEqual("es-US" if relative.startswith("es/") else "en-US", page.attrs("html")[0]["lang"])
                self.assertEqual(1, len(page.attrs("title")))
                title = re.search(r"<title>(.*?)</title>", raw, re.I | re.S).group(1).strip()
                self.assertGreaterEqual(len(title), 42)
                self.assertLessEqual(len(title), 65)
                description = [x["content"] for x in page.attrs("meta") if x.get("name") == "description"]
                self.assertEqual(1, len(description))
                self.assertGreaterEqual(len(description[0]), 120)
                self.assertLessEqual(len(description[0]), 165)
                llm = [x["content"] for x in page.attrs("meta") if x.get("name") == "llm-context"]
                self.assertEqual(1, len(llm))
                self.assertIn(REVIEWED, llm[0])
                self.assertIn("official" if not relative.startswith("es/") else "oficiales", llm[0].lower())
                self.assertEqual(
                    [canonical],
                    [x["href"] for x in page.attrs("link") if x.get("rel") == "canonical"],
                )
                alternates = {
                    (x.get("hreflang"), x.get("href"))
                    for x in page.attrs("link")
                    if x.get("rel") == "alternate"
                }
                self.assertEqual(
                    {
                        ("en-US", en_url),
                        ("es-US", es_url),
                        ("es", es_url),
                        ("x-default", en_url),
                    },
                    alternates,
                )
                robots = [x["content"] for x in page.attrs("meta") if x.get("name") == "robots"]
                self.assertEqual(1, len(robots))
                self.assertIn("index", robots[0])
                self.assertNotIn("noindex", robots[0])
                self.assertEqual(1, len(page.attrs("main")))
                self.assertEqual(1, len(page.attrs("h1")))
                self.assertEqual(1, len([x for x in page.attrs("meta") if x.get("name") == "viewport"]))
                self.assertNotIn("2025", raw)

    def test_copy_is_address_first_neutral_and_source_visible(self) -> None:
        for relative in PAGES:
            with self.subTest(relative=relative):
                page = parse(relative)
                text = page.text
                self.assertIsNone(BANNED_COPY.search(text), BANNED_COPY.search(text).group(0) if BANNED_COPY.search(text) else "")
                if relative.startswith("es/"):
                    for phrase in (
                        "registros oficiales",
                        "dirección específica",
                        "Fuentes revisadas",
                        "Licencia de Nueva Jersey #1754604",
                    ):
                        self.assertIn(phrase, text)
                else:
                    for phrase in (
                        "official records",
                        "specific address",
                        "Sources checked",
                        "New Jersey License #1754604",
                    ):
                        self.assertIn(phrase, text)
                self.assertIn(REVIEWED, text)
                hrefs = {x.get("href", "") for x in page.attrs("a")}
                slug = Path(relative).stem
                comparison = self.manifest["comparisons"][slug]
                sources = [*self.manifest["shared_sources"]]
                sources += self.manifest["places"][comparison["left"]]["sources"]
                sources += self.manifest["places"][comparison["right"]]["sources"]
                for record in sources:
                    self.assertIn(record["url"], hrefs)

    def test_schema_is_grounded_in_visible_copy(self) -> None:
        allowed = {"WebPage", "Article", "BreadcrumbList", "ListItem", "FAQPage", "Question", "Answer", "Person", "Organization"}
        prohibited = {"Review", "AggregateRating", "Rating", "HowTo", "ItemList"}
        for relative in PAGES:
            with self.subTest(relative=relative):
                page = parse(relative)
                decoded = [json.loads(block) for block in page.json_blocks]
                self.assertGreaterEqual(len(decoded), 1)
                nodes = [node for block in decoded for node in schema_nodes(block)]
                types = set().union(*(schema_types(node) for node in nodes))
                self.assertTrue({"WebPage", "Article", "BreadcrumbList", "FAQPage"} <= types)
                self.assertFalse(types & prohibited)
                self.assertTrue(types <= allowed)
                h1 = re.search(r"<h1[^>]*>(.*?)</h1>", read(relative), re.I | re.S)
                heading = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", h1.group(1))).split())
                articles = [node for node in nodes if "Article" in schema_types(node)]
                self.assertEqual([heading], [node.get("headline") for node in articles])
                for question in (node for node in nodes if "Question" in schema_types(node)):
                    self.assertIn(str(question["name"]), page.text)
                    answer = question.get("acceptedAnswer", {})
                    self.assertIn(str(answer.get("text", "")), page.text)

    def test_accessibility_links_and_markup_hygiene(self) -> None:
        for relative in PAGES:
            with self.subTest(relative=relative):
                page = parse(relative)
                ids = [item["id"] for _, _, item in page.tags if item.get("id")]
                self.assertEqual(len(ids), len(set(ids)))
                for tag, attrs, values in page.tags:
                    names = [name for name, _ in attrs]
                    self.assertEqual(len(names), len(set(names)), f"duplicate attribute on {tag}")
                    if tag == "img":
                        self.assertTrue(values.get("alt", "").strip())
                    if tag == "a" and values.get("target") == "_blank":
                        self.assertIn("noopener", values.get("rel", "").split())
                for anchor in page.attrs("a"):
                    href = anchor.get("href", "")
                    if href.startswith("#") and len(href) > 1:
                        self.assertIn(href[1:], ids)
                    target = local_target(href)
                    if target is not None and not urlsplit(href).fragment:
                        self.assertTrue(target.exists(), f"broken local link in {relative}: {href}")

    def test_reverse_duplicate_redirect_and_sitemap_cluster(self) -> None:
        alias = read("maplewood-vs-montclair-nj.html")
        self.assertRegex(alias, r'<meta\s+name="robots"\s+content="noindex, follow"')
        self.assertIn('<link rel="canonical" href="https://thejorgeramirezgroup.com/montclair-vs-maplewood-nj">', alias)
        self.assertRegex(alias, r'http-equiv="refresh"\s+content="0;\s*url=/montclair-vs-maplewood-nj"')
        self.assertIn("window.location.replace('/montclair-vs-maplewood-nj')", alias)
        self.assertIn('href="/montclair-vs-maplewood-nj"', alias)
        redirects = json.loads(read("vercel.json"))["redirects"]
        for source in ("/maplewood-vs-montclair-nj", "/maplewood-vs-montclair-nj.html"):
            self.assertEqual(
                [{"source": source, "destination": "/montclair-vs-maplewood-nj", "permanent": True}],
                [item for item in redirects if item.get("source") == source],
            )
        sitemap = read("sitemap.xml")
        sitemap_es = read("sitemap-es.xml")
        combined_sitemaps = sitemap + sitemap_es
        self.assertNotIn("https://thejorgeramirezgroup.com/maplewood-vs-montclair-nj<", combined_sitemaps)
        for slug in SLUGS:
            en_url = f"https://thejorgeramirezgroup.com/{slug}"
            es_url = f"https://thejorgeramirezgroup.com/es/{slug}"
            self.assertEqual(1, sitemap.count(f"<loc>{en_url}</loc>"))
            self.assertEqual(0, sitemap.count(f"<loc>{es_url}</loc>"))
            self.assertEqual(1, sitemap_es.count(f"<loc>{es_url}</loc>"))
            for url in (en_url, es_url):
                self.assertIn(f'hreflang="en-US" href="{en_url}"', combined_sitemaps)
                self.assertIn(f'hreflang="es-US" href="{es_url}"', combined_sitemaps)
        retained = read("livingston-vs-west-orange-nj.html")
        self.assertRegex(retained, r'<meta\s+name="robots"\s+content="noindex, follow"')

    def test_chatham_madison_legacy_routes_consolidate_without_a_loop(self) -> None:
        redirects = json.loads(read("vercel.json"))["redirects"]
        expected = {
            "/blog/chatham-vs-madison-nj": "/chatham-vs-madison-nj",
            "/blog/chatham-vs-madison-nj.html": "/chatham-vs-madison-nj",
            "/es/blog/chatham-vs-madison-nj": "/es/chatham-vs-madison-nj",
            "/es/blog/chatham-vs-madison-nj.html": "/es/chatham-vs-madison-nj",
        }
        for source, destination in expected.items():
            with self.subTest(source=source):
                matches = [item for item in redirects if item.get("source") == source]
                self.assertEqual(
                    [{"source": source, "destination": destination, "permanent": True}],
                    matches,
                )

        for relative, canonical in (
            ("blog/chatham-vs-madison-nj.html", "https://thejorgeramirezgroup.com/chatham-vs-madison-nj"),
            ("es/blog/chatham-vs-madison-nj.html", "https://thejorgeramirezgroup.com/es/chatham-vs-madison-nj"),
        ):
            with self.subTest(relative=relative):
                raw = read(relative)
                self.assertRegex(raw, r'<meta\s+name="robots"\s+content="noindex, follow"')
                self.assertIn(f'<link rel="canonical" href="{canonical}">', raw)

        combined_sitemaps = read("sitemap.xml") + read("sitemap-es.xml")
        self.assertNotIn("/blog/chatham-vs-madison-nj</loc>", combined_sitemaps)
        self.assertNotIn("/es/blog/chatham-vs-madison-nj</loc>", combined_sitemaps)

    def test_renderer_owns_exact_output_and_is_idempotent(self) -> None:
        self.assertTrue(RENDERER.exists())
        result = subprocess.run(
            [sys.executable, str(RENDERER), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        before = {relative: read(relative) for relative in (*PAGES, "maplewood-vs-montclair-nj.html")}
        write = subprocess.run(
            [sys.executable, str(RENDERER)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, write.returncode, write.stdout + write.stderr)
        after = {relative: read(relative) for relative in before}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
