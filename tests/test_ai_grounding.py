#!/usr/bin/env python3
"""Regression checks for the site's public machine-readable grounding files."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://thejorgeramirezgroup.com"
GROUNDING_FILES = ("llms.txt", "llms-full.txt", "llms-es.txt")
UPDATE_DATE = "2026-08-26"
ALL_NJ_COUNTIES = {
    "Atlantic",
    "Bergen",
    "Burlington",
    "Camden",
    "Cape May",
    "Cumberland",
    "Essex",
    "Gloucester",
    "Hudson",
    "Hunterdon",
    "Mercer",
    "Middlesex",
    "Monmouth",
    "Morris",
    "Ocean",
    "Passaic",
    "Salem",
    "Somerset",
    "Sussex",
    "Union",
    "Warren",
}

REQUIRED_BOTS = (
    "*",
    "Googlebot",
    "Google-Extended",
    "Bingbot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "GPTBot",
    "PerplexityBot",
    "ClaudeBot",
)
REQUIRED_ROBOTS_EXCLUSIONS = {
    "/staging/",
    "/contact?*",
    "/*?interest=*",
    "/*?utm_*",
    "/*?ref=*",
    "/*?source=*",
}

REQUIRED_EN_PATHS = {
    "/communities",
    "/buy-a-home",
    "/sell-your-home",
    "/home-valuation",
    "/property-search",
    "/nj-train-map",
    "/blog/nj-property-tax-guide",
    "/blog/best-nj-towns-for-families-2026",
    "/blog/best-nj-suburbs-nyc-commuters",
    "/blog/best-time-to-sell-home-nj",
    "/blog/midtown-direct-towns-nj",
    "/blog/best-nj-towns-to-sell-home",
    "/cranford-vs-westfield-nj",
    "/tools/mortgage-calculator",
    "/net-proceeds-calculator",
    "/nj-realty-transfer-fee-calculator",
    "/closing-costs-calculator",
    "/rent-vs-buy-nj",
    "/blog/nj-home-selling-costs",
    "/blog/nj-exit-tax-explained",
    "/blog/capital-gains-tax-selling-house-nj",
    "/blog/first-time-home-buyer-nj-guide",
    "/blog/nj-home-selling-timeline",
    "/blog/selling-inherited-home-nj",
    "/blog/moving-from-nyc-to-nj-guide",
    "/contact",
}
REQUIRED_ES_PATHS = {
    "/es",
    "/es/communities",
    "/es/buy-a-home",
    "/es/sell-your-home",
    "/es/home-valuation",
    "/es/property-search",
    "/es/nj-train-map",
    "/es/blog/nj-property-tax-guide",
    "/es/blog/best-nj-suburbs-nyc-commuters",
    "/es/blog/first-time-home-buyer-nj-guide",
    "/es/blog/best-nj-towns-for-families",
    "/es/blog/maplewood-vs-south-orange-nj",
    "/es/cranford-vs-westfield-nj",
    "/es/net-proceeds-calculator",
    "/es/nj-realty-transfer-fee-calculator",
    "/es/closing-costs-calculator",
    "/es/rent-vs-buy-nj",
    "/es/blog/nj-home-selling-costs",
    "/es/blog/nj-home-selling-timeline",
    "/es/blog/moving-from-nyc-to-nj-guide",
}

UNSAFE_PATTERNS = {
    "conflicting inventory counts": r"\b(?:138|103)\b",
    "five-county scope": r"\b(?:five|5)\s+count(?:y|ies)\b|\b(?:cinco|5)\s+condados?\b",
    "obsolete valuation host": r"value\.thejorgeramirezgroup\.com",
    "unsupported association claim": r"\bNAHREP\b",
    "keyword list": r"\b(?:target\s+)?keywords?\b|\bpalabras\s+clave\b",
    "promotional superlative": (
        r"\b(?:leading|top[- ]rated|top\s+(?:agent|realtor)|best\s+(?:agent|realtor|"
        r"real\s+estate\s+agent))\b|\b(?:líder|mejor\s+calificad[oa]|mejor\s+agente)\b"
    ),
    "unsupported market price": r"\$\s*\d",
    "unsupported percentage": r"\b\d+(?:\.\d+)?\s*%",
    "unsupported market or commute time": (
        r"\b\d+(?:\s*[-–]\s*\d+)?\s*(?:minutes?|mins?|days?|months?|hours?)\b|"
        r"\b\d+(?:\s*[-–]\s*\d+)?\s*(?:minutos?|días?|meses?|horas?)\b"
    ),
    "school score or accolade": r"GreatSchools|Blue\s+Ribbon|school\s+(?:rating|score)|calificaci[oó]n\s+escolar",
    "review or rating claim": r"\b(?:reviews?|ratings?|stars?|reseñas?|estrellas?)\b",
    "availability claim": r"24/7|same[- ]day|always\s+available|disponible\s+(?:siempre|todo\s+el\s+d[ií]a)",
    "unsupported biographical claim": r"\b(?:renovation|investor|investment\s+experience|renovaci[oó]n|inversionista)\b",
    "AI-marketing claim": (
        r"(?:\bAI\b|artificial\s+intelligence|inteligencia\s+artificial|\bIA\b).{0,50}"
        r"(?:marketing|targeting|system|powered|impulsad[oa]|ventas?)"
    ),
    "specific legal or program assertion": (
        r"mandatory\s+attorney\s+review|mansion\s+tax|statute[- ]accurate|GIT/REP|NJHMFA|"
        r"revisi[oó]n\s+obligatoria\s+de\s+abogado|impuesto\s+a\s+las\s+mansiones"
    ),
    "volatile market metric": r"\b(?:median\s+(?:price|sale)|days\s+on\s+market|precio\s+mediano|d[ií]as\s+en\s+el\s+mercado)\b",
    "stale year": r"\b202[45]\b",
}


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def parse_robots_groups(source: str) -> list[tuple[list[str], list[tuple[str, str]]]]:
    groups: list[tuple[list[str], list[tuple[str, str]]]] = []
    agents: list[str] = []
    directives: list[tuple[str, str]] = []

    def flush() -> None:
        nonlocal agents, directives
        if agents:
            groups.append((agents, directives))
        agents = []
        directives = []

    for raw_line in source.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = (part.strip() for part in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            if directives:
                flush()
            agents.append(value)
        elif agents:
            directives.append((field, value))
    flush()
    return groups


def first_party_urls(source: str) -> set[str]:
    candidates = re.findall(r"https://(?:www\.)?thejorgeramirezgroup\.com[^\s)>\]}]+", source)
    return {candidate.rstrip(".,;:\"") for candidate in candidates}


def deployed_file(path: str) -> Path | None:
    clean = unquote(path).strip("/")
    candidates = [ROOT / "index.html"] if not clean else [ROOT / f"{clean}.html", ROOT / clean / "index.html"]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


class AiGroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = json.loads(read("data/site-facts.json"))
        cls.documents = {name: read(name) for name in GROUNDING_FILES}

    def test_grounding_files_are_concise_and_current(self) -> None:
        limits = {"llms.txt": 8_000, "llms-full.txt": 16_000, "llms-es.txt": 10_000}
        for name, source in self.documents.items():
            with self.subTest(name=name):
                self.assertLess(len(source.encode("utf-8")), limits[name])
                self.assertIn(f"Last updated: {UPDATE_DATE}", source if name != "llms-es.txt" else source.replace("Última actualización", "Last updated"))

    def test_registry_identity_and_service_area_agree(self) -> None:
        business = self.facts["business"]
        counties = self.facts["serviceCounties"]
        english_county_line = "Service counties: " + ", ".join(counties[:-1]) + ", " + counties[-1] + "."
        spanish_county_line = "Condados de servicio: " + ", ".join(counties[:-1]) + " y " + counties[-1] + "."
        unexpected_counties = ALL_NJ_COUNTIES - set(counties)

        shared_values = (
            business["name"],
            business["agentName"],
            business["directPhone"]["display"],
            business["email"],
            business["njRealEstateLicense"],
            business["brokerage"]["displayName"],
            business["address"]["street"],
            business["address"]["city"],
            business["address"]["postalCode"],
            str(business["fullTimeSince"]),
        )
        for name, source in self.documents.items():
            with self.subTest(name=name):
                for value in shared_values:
                    self.assertIn(value, source)
                self.assertEqual(source.count("1754604"), 1)
                expected_line = spanish_county_line if name == "llms-es.txt" else english_county_line
                self.assertIn(expected_line, source)
                self.assertEqual(source.count(expected_line), 1)
                for county in counties:
                    self.assertIn(county, expected_line)
                for county in unexpected_counties:
                    self.assertIsNone(re.search(rf"\b{re.escape(county)}\b", source))

        self.assertIn(business["approvedExperienceStatement"], self.documents["llms.txt"])
        self.assertIn(business["approvedExperienceStatement"], self.documents["llms-full.txt"])
        self.assertIn(
            "Agente inmobiliario de tiempo completo en Keller Williams Premier Properties desde 2017.",
            self.documents["llms-es.txt"],
        )

    def test_no_volatile_town_inventory_or_unsafe_claims(self) -> None:
        inventory_total = str(self.facts["canonicalTownInventory"]["total"])
        for name, source in self.documents.items():
            with self.subTest(name=name):
                self.assertIsNone(re.search(rf"\b{re.escape(inventory_total)}\b", source))
                for label, pattern in UNSAFE_PATTERNS.items():
                    self.assertIsNone(re.search(pattern, source, re.IGNORECASE | re.DOTALL), label)

    def test_files_disclaim_search_outcomes_and_professional_advice(self) -> None:
        for name in ("llms.txt", "llms-full.txt"):
            source = self.documents[name]
            self.assertIn("does not guarantee indexing, ranking, citation, or use", source)
            self.assertIn("educational, not legal, tax, financial, or lending advice", source)
        spanish = self.documents["llms-es.txt"]
        self.assertIn("no garantiza indexación, posicionamiento, citas ni uso", spanish.lower())
        self.assertIn("educativos; no constituyen asesoría legal, fiscal, financiera ni hipotecaria", spanish)

    def test_spanish_file_uses_basic_idiomatic_spanish(self) -> None:
        spanish = self.documents["llms-es.txt"]
        for phrase in (
            "## Identidad verificada",
            "## Área de servicio",
            "## Recursos en español",
            "Nueva Jersey",
            "inglés y español",
            "Última actualización: 2026-08-26",
        ):
            self.assertIn(phrase, spanish)
        self.assertNotRegex(spanish, r"(?m)^(?:Q|A):")

    def test_required_canonical_resources_are_present(self) -> None:
        english_paths = {
            urlsplit(url).path for name in ("llms.txt", "llms-full.txt") for url in first_party_urls(self.documents[name])
        }
        spanish_paths = {urlsplit(url).path for url in first_party_urls(self.documents["llms-es.txt"])}
        self.assertTrue(REQUIRED_EN_PATHS.issubset(english_paths), REQUIRED_EN_PATHS - english_paths)
        self.assertTrue(REQUIRED_ES_PATHS.issubset(spanish_paths), REQUIRED_ES_PATHS - spanish_paths)

    def test_saved_ai_discovery_priorities_are_exposed_in_grounding_files(self) -> None:
        priorities = json.loads(read("data/gsc-geo-priorities.json"))["aiDiscoveryPaths"]
        english_paths = {
            urlsplit(url).path
            for name in ("llms.txt", "llms-full.txt")
            for url in first_party_urls(self.documents[name])
        }
        spanish_paths = {
            urlsplit(url).path for url in first_party_urls(self.documents["llms-es.txt"])
        }
        missing = []
        for item in priorities:
            path = item["path"]
            available = spanish_paths if path.startswith("/es/") else english_paths
            if path not in available:
                missing.append(path)
        self.assertEqual([], missing)

    def test_every_first_party_link_is_clean_canonical_and_indexable(self) -> None:
        redirect_config = json.loads(read("vercel.json"))
        exact_redirects = {
            item["source"]
            for item in redirect_config.get("redirects", [])
            if not item.get("has") and not re.search(r"[:*]", item.get("source", ""))
        }
        sitemap_urls = set(re.findall(r"<loc>(https://thejorgeramirezgroup\.com[^<]+)</loc>", read("sitemap.xml") + read("sitemap-es.xml")))

        for name, source in self.documents.items():
            for url in first_party_urls(source):
                with self.subTest(name=name, url=url):
                    parsed = urlsplit(url)
                    self.assertEqual(parsed.scheme, "https")
                    self.assertEqual(parsed.netloc, "thejorgeramirezgroup.com")
                    self.assertFalse(parsed.query or parsed.fragment)
                    self.assertNotIn(".html", parsed.path)
                    self.assertNotIn(parsed.path or "/", exact_redirects)

                    target = deployed_file(parsed.path)
                    self.assertIsNotNone(target, "missing local target")
                    html = target.read_text(encoding="utf-8")
                    self.assertIsNone(re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', html, re.I))
                    self.assertIsNone(re.search(r'<meta\b[^>]*http-equiv=["\']refresh["\']', html, re.I))
                    canonical = re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', html, re.I)
                    self.assertIsNotNone(canonical, "target lacks canonical")
                    self.assertEqual(normalize_url(canonical.group(1)), normalize_url(url))
                    sitemap_form = ORIGIN + (parsed.path if parsed.path != "/" else "/")
                    self.assertIn(sitemap_form, sitemap_urls)

    def test_required_crawlers_are_allowed_without_bypassing_exclusions(self) -> None:
        robots = read("robots.txt")
        groups = parse_robots_groups(robots)
        for bot in REQUIRED_BOTS:
            matching = [(agents, directives) for agents, directives in groups if bot.lower() in {agent.lower() for agent in agents}]
            with self.subTest(bot=bot):
                self.assertEqual(len(matching), 1, "crawler must appear in exactly one group")
                directives = matching[0][1]
                self.assertIn(("allow", "/"), directives)
                disallows = {value for field, value in directives if field == "disallow"}
                self.assertTrue(REQUIRED_ROBOTS_EXCLUSIONS.issubset(disallows), REQUIRED_ROBOTS_EXCLUSIONS - disallows)

        self.assertEqual(robots.count(f"Sitemap: {ORIGIN}/sitemap-index.xml"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
