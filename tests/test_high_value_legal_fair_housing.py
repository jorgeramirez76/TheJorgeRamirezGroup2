#!/usr/bin/env python3
"""Contracts for the high-value legal, timeline, probate, and comparison rebuild."""

from __future__ import annotations

import html
import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
PAGE_MODIFIED_ON = "2026-08-27"
RELEASE_MODIFIED = {
    "blog/maplewood-vs-south-orange-nj.html",
    "es/blog/maplewood-vs-south-orange-nj.html",
    "blog/summit-vs-westfield-nj.html",
    "es/blog/summit-vs-westfield-nj.html",
}
MANIFEST = ROOT / "data" / "high-value-legal-fair-housing-sources.json"
RENDERER = ROOT / "tools" / "generate_high_value_legal_fair_housing.py"

INDEXABLE = {
    "buyer-agency-agreement-nj.html": "/buyer-agency-agreement-nj",
    "es/buyer-agency-agreement-nj.html": "/es/buyer-agency-agreement-nj",
    "blog/maplewood-vs-south-orange-nj.html": "/blog/maplewood-vs-south-orange-nj",
    "es/blog/maplewood-vs-south-orange-nj.html": "/es/blog/maplewood-vs-south-orange-nj",
    "blog/summit-vs-westfield-nj.html": "/blog/summit-vs-westfield-nj",
    "es/blog/summit-vs-westfield-nj.html": "/es/blog/summit-vs-westfield-nj",
    "blog/nj-home-selling-timeline.html": "/blog/nj-home-selling-timeline",
    "es/blog/nj-home-selling-timeline.html": "/es/blog/nj-home-selling-timeline",
    "blog/probate-real-estate-nj-guide.html": "/blog/probate-real-estate-nj-guide",
    "es/blog/probate-real-estate-nj-guide.html": "/es/blog/probate-real-estate-nj-guide",
    "blog/how-to-appeal-nj-property-taxes-2026.html": "/blog/how-to-appeal-nj-property-taxes-2026",
    "westfield-vs-scotch-plains-nj.html": "/westfield-vs-scotch-plains-nj",
}
FALLBACK = "blog/selling-inherited-house-multiple-heirs-nj.html"
DESTINATION = "/blog/selling-inherited-home-nj"
EXPECTED_FILES = {*INDEXABLE, FALLBACK}

BILINGUAL = {
    "buyer-agency": (
        "/buyer-agency-agreement-nj",
        "/es/buyer-agency-agreement-nj",
    ),
    "maplewood-south-orange": (
        "/blog/maplewood-vs-south-orange-nj",
        "/es/blog/maplewood-vs-south-orange-nj",
    ),
    "summit-westfield": (
        "/blog/summit-vs-westfield-nj",
        "/es/blog/summit-vs-westfield-nj",
    ),
    "selling-timeline": (
        "/blog/nj-home-selling-timeline",
        "/es/blog/nj-home-selling-timeline",
    ),
    "probate": (
        "/blog/probate-real-estate-nj-guide",
        "/es/blog/probate-real-estate-nj-guide",
    ),
}

ALLOWED_SOURCE_HOSTS = {
    "consumerfinance.gov",
    "data.census.gov",
    "irs.gov",
    "nj.gov",
    "scotchplainsnj.gov",
    "ucnj.org",
    "www.cityofsummit.org",
    "www.consumerfinance.gov",
    "www.irs.gov",
    "www.maplewoodnj.gov",
    "www.nar.realtor",
    "www.nj.gov",
    "www.njcourts.gov",
    "www.njoag.gov",
    "www.njtransit.com",
    "www.somsdk12.org",
    "www.southorange.org",
    "www.spfk12.org",
    "www.summit.k12.nj.us",
    "www.westfieldnj.gov",
    "www.westfieldnjk12.org",
}

FORBIDDEN = re.compile(
    r"(?:"
    r"\bmost sellers (?:still )?(?:pay|offer)|\b2\s*[–-]\s*2\.5\s*%|"
    r"\b(?:helped|served|guided|worked with) (?:hundreds|dozens)|"
    r"\b(?:hundreds|dozens) of (?:buyers|sellers|families|transactions)|"
    r"\bsav(?:e|es|ed|ing) \$?\d|\$\d[\d,]*(?:\s*[–-]\s*\$?\d[\d,]*)?\s+in savings|"
    r"\btop dollar|\bproven (?:system|strategy|process)|\bguaranteed?\b|"
    r"\b(?:best|right|perfect|ideal) (?:town|community|neighbou?rhood|place)|"
    r"\b(?:safe|safest|safer) (?:town|community|neighbou?rhood|place)|"
    r"\b(?:excellent|best|top[- ]rated|highly[- ]rated) schools?|"
    r"\bfamily[- ]friendly|\bfamilies with (?:children|kids)|"
    r"\b\d+\s*(?:minutes?|mins?)\s+(?:to|from) (?:NYC|New York|Penn)|"
    r"\bavailable 7 days|\balways (?:available|responsive)|\bpicks? up|"
    r"\bthe executor can (?:sign|sell)|\ball heirs must agree|\bfile a partition|"
    r"\bNJ requires (?:a |an )?attorney|\bfederal law requires a buyer agreement|"
    r"\bla mayor[ií]a de los vendedores (?:paga|ofrece)|"
    r"\b(?:cientos|docenas) de (?:compradores|vendedores|familias|transacciones)|"
    r"\b(?:mejor|ideal|perfect[oa]|correct[oa]) (?:pueblo|municipio|comunidad|barrio|lugar)|"
    r"\bescuelas? (?:excelentes?|mejores?|destacadas?|altamente calificadas?)|"
    r"\bsegur[oa]s? (?:pueblo|municipio|comunidad|barrio)|"
    r"\bideal para familias|\bfamilias con (?:ni[nñ]os|hijos)|"
    r"\bmejor precio posible|\bresultados? garantizad[oa]s?"
    r")",
    re.I,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def json_ld(source: str) -> list[object]:
    return [
        json.loads(block)
        for block in re.findall(
            r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            source,
            flags=re.I | re.S,
        )
    ]


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


class IntegrityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.duplicate_attributes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        names = [name.casefold() for name, _ in attrs]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        self.duplicate_attributes.extend(f"{tag}:{name}" for name in duplicates)
        self.ids.extend(value for name, value in attrs if name.casefold() == "id" and value)


class HighValueLegalFairHousingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.pages = {path: read(path) for path in EXPECTED_FILES}

    def test_manifest_is_current_exact_and_primary_source_only(self) -> None:
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertEqual(REVIEWED_ON, self.manifest["reviewedOn"])
        self.assertEqual("tools/generate_high_value_legal_fair_housing.py", self.manifest["renderer"])
        self.assertEqual(EXPECTED_FILES, set(self.manifest["managedFiles"]))
        self.assertEqual(set(BILINGUAL), set(self.manifest["clusters"]) - {"tax-appeal", "westfield-scotch-plains", "multiple-heirs-alias"})

        source_ids = {item["id"] for item in self.manifest["sources"]}
        self.assertEqual(len(source_ids), len(self.manifest["sources"]))
        for source in self.manifest["sources"]:
            with self.subTest(source=source["id"]):
                self.assertEqual(
                    {"id", "publisher", "title", "url", "kind", "use", "limit", "accessedOn"},
                    set(source),
                )
                self.assertEqual(REVIEWED_ON, source["accessedOn"])
                self.assertEqual("https", urlparse(source["url"]).scheme)
                self.assertIn(urlparse(source["url"]).netloc, ALLOWED_SOURCE_HOSTS)
                self.assertGreaterEqual(len(source["use"]), 24)
                self.assertGreaterEqual(len(source["limit"]), 24)

        for cluster, record in self.manifest["clusters"].items():
            with self.subTest(cluster=cluster):
                self.assertTrue(record["sourceIds"])
                self.assertEqual(set(), set(record["sourceIds"]) - source_ids)

    def test_renderer_check_mode_is_deterministic_and_current(self) -> None:
        result = subprocess.run(
            ["python3", str(RENDERER), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("13 managed pages are current", result.stdout)

    def test_indexable_pages_keep_clean_canonicals_and_language_clusters(self) -> None:
        cluster_by_route = {
            route: pair for pair in BILINGUAL.values() for route in pair
        }
        for relative, route in INDEXABLE.items():
            source = self.pages[relative]
            canonical = SITE + route
            with self.subTest(path=relative):
                self.assertRegex(source, r'<meta\s+name="robots"\s+content="index, follow')
                self.assertNotRegex(source, r'<meta\s+name="robots"[^>]*noindex')
                self.assertEqual(1, len(re.findall(r'<link\s+rel="canonical"', source)))
                self.assertIn(f'<link rel="canonical" href="{canonical}">', source)
                if route in cluster_by_route:
                    en_route, es_route = cluster_by_route[route]
                    self.assertIn(f'<link rel="alternate" hreflang="en-US" href="{SITE}{en_route}">', source)
                    self.assertIn(f'<link rel="alternate" hreflang="es-US" href="{SITE}{es_route}">', source)
                    self.assertIn(f'<link rel="alternate" hreflang="x-default" href="{SITE}{en_route}">', source)
                    if relative.startswith("es/"):
                        self.assertIn(f'<link rel="alternate" hreflang="es" href="{SITE}{es_route}">', source)
                else:
                    self.assertNotIn('hreflang="es-US"', source)
                    self.assertIn(f'<link rel="alternate" hreflang="en-US" href="{canonical}">', source)
                    self.assertIn(f'<link rel="alternate" hreflang="x-default" href="{canonical}">', source)

    def test_pages_enforce_homepage_palette_type_and_accessible_mobile_structure(self) -> None:
        tokens = ("#0A0A0A", "#1A1A1A", "#C41230", "#8B0D22", "#B8962E", "#D4AF5A", "#FAFAF8", "#F8F6F2")
        for relative in INDEXABLE:
            source = self.pages[relative]
            parser = IntegrityParser()
            parser.feed(source)
            with self.subTest(path=relative):
                for token in tokens:
                    self.assertIn(token, source)
                self.assertIn("Playfair Display", source)
                self.assertIn("'Inter'", source)
                self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1.0">', source)
                self.assertIn('<meta name="theme-color" content="#1A1A1A">', source)
                self.assertIn('<meta name="llm-context" content="', source)
                self.assertIn('<a class="skip-link" href="#main">', source)
                self.assertIn('<main id="main" tabindex="-1">', source)
                self.assertIn('class="menu-button"', source)
                self.assertIn('aria-expanded="false"', source)
                self.assertIn('class="button primary btn-primary"', source)
                self.assertIn('class="button secondary cta-button"', source)
                self.assertIn('@media (max-width: 820px)', source)
                self.assertIn('min-height: 44px', source)
                self.assertEqual(1, len(re.findall(r"<h1\b", source, re.I)))
                self.assertEqual([], parser.duplicate_attributes)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                for tag in re.findall(r'<a\b[^>]*target="_blank"[^>]*>', source, re.I):
                    self.assertRegex(tag, r'rel="[^"]*noopener[^"]*noreferrer')

    def test_schema_is_parseable_visible_and_non_promotional(self) -> None:
        forbidden = {"FAQPage", "HowTo", "Review", "Rating", "AggregateRating", "Service", "Offer"}
        for relative, route in INDEXABLE.items():
            source = self.pages[relative]
            nodes = [node for block in json_ld(source) for node in schema_nodes(block)]
            types = {node.get("@type") for node in nodes}
            article = next(node for node in nodes if node.get("@type") == "Article")
            webpage = next(node for node in nodes if node.get("@type") == "WebPage")
            with self.subTest(path=relative):
                self.assertTrue({"Organization", "Person", "WebPage", "Article", "BreadcrumbList"} <= types)
                self.assertFalse(types & forbidden)
                self.assertEqual(SITE + route + "#webpage", article["mainEntityOfPage"]["@id"])
                self.assertEqual(SITE + route, webpage["url"])
                expected_modified = (
                    PAGE_MODIFIED_ON if relative in RELEASE_MODIFIED else REVIEWED_ON
                )
                self.assertEqual(expected_modified, article["dateModified"])
                self.assertEqual(expected_modified, webpage["dateModified"])
                self.assertIn(
                    f'<meta name="last-updated" content="{expected_modified}">',
                    source,
                )
                self.assertIn(
                    f'<meta property="article:modified_time" content="{expected_modified}">',
                    source,
                )
                self.assertIn(article["headline"], visible_text(source))

    def test_every_cluster_source_is_visible_and_copy_avoids_prohibited_claims(self) -> None:
        source_map = {item["id"]: item for item in self.manifest["sources"]}
        for cluster, record in self.manifest["clusters"].items():
            for relative in record["files"]:
                source = self.pages[relative]
                if relative == FALLBACK:
                    continue
                hrefs = set(re.findall(r'<a\b[^>]*href="([^"]+)"', source, re.I))
                missing = {source_map[source_id]["url"] for source_id in record["sourceIds"]} - hrefs
                with self.subTest(cluster=cluster, path=relative):
                    self.assertEqual(set(), missing)
                    self.assertIsNone(FORBIDDEN.search(visible_text(source)))

    def test_buyer_agreement_separates_new_jersey_law_from_mls_policy(self) -> None:
        for relative, phrases in (
            (
                "buyer-agency-agreement-nj.html",
                (
                    "New Jersey law and MLS policy are separate rules",
                    "before, or as soon as reasonably practical after",
                    "fully negotiable and not set by law",
                    "seller, buyer, third party, or compensation shared between brokerage firms",
                    "open house without your own agent",
                    "not legal advice",
                ),
            ),
            (
                "es/buyer-agency-agreement-nj.html",
                (
                    "La ley de Nueva Jersey y la política del MLS son reglas distintas",
                    "antes de comenzar los servicios o tan pronto como sea razonablemente práctico",
                    "totalmente negociable y no la fija la ley",
                    "vendedor, comprador, tercero o mediante reparto entre firmas inmobiliarias",
                    "casa abierta sin su propio agente",
                    "no es asesoramiento legal",
                ),
            ),
        ):
            candidate = visible_text(self.pages[relative])
            for phrase in phrases:
                with self.subTest(path=relative, phrase=phrase):
                    self.assertIn(phrase.casefold(), candidate.casefold())

    def test_timeline_and_probate_pages_state_their_scope_limits(self) -> None:
        requirements = {
            "blog/nj-home-selling-timeline.html": (
                "There is no universal New Jersey closing timetable",
                "Many New Jersey buyers choose an attorney, but state consumer guidance says retaining one is not required",
                "the signed contract controls transaction deadlines",
                "covered mortgage",
                "not legal, tax, lending, title, or inspection advice",
            ),
            "es/blog/nj-home-selling-timeline.html": (
                "No existe un plazo universal de cierre en Nueva Jersey",
                "Muchos compradores de Nueva Jersey optan por un abogado, pero la guía estatal dice que contratarlo no es obligatorio",
                "el contrato firmado controla los plazos de la transacción",
                "hipoteca cubierta",
                "no es asesoramiento legal, fiscal, crediticio, de título ni de inspección",
            ),
            "blog/probate-real-estate-nj-guide.html": (
                "Confirm authority before listing, signing, or accepting an offer",
                "generally uses fair market value at the date of death",
                "exceptions and different valuation rules can apply",
                "not legal or tax advice",
            ),
            "es/blog/probate-real-estate-nj-guide.html": (
                "Confirme la autoridad antes de publicar, firmar o aceptar una oferta",
                "generalmente usa el valor justo de mercado en la fecha del fallecimiento",
                "pueden aplicar excepciones y reglas de valoración distintas",
                "no es asesoramiento legal ni fiscal",
            ),
        }
        for relative, phrases in requirements.items():
            candidate = visible_text(self.pages[relative])
            for phrase in phrases:
                with self.subTest(path=relative, phrase=phrase):
                    self.assertIn(phrase.casefold(), candidate.casefold())

    def test_tax_appeal_deadlines_preserve_current_state_nuance_without_outcome_claims(self) -> None:
        source = visible_text(self.pages["blog/how-to-appeal-nj-property-taxes-2026.html"])
        for phrase in (
            "filed and received on or before April 1",
            "May 1",
            "Burlington, Gloucester, and Monmouth Counties",
            "January 15",
            "verify the current deadline directly",
            "An appeal challenges the assessment, not the tax rate or the bill by itself",
            "not legal or tax advice",
        ):
            self.assertIn(phrase.casefold(), source.casefold())
        self.assertNotRegex(source, re.compile(r"\b(?:save|reduce|lower|cut)\s+\$?\d|guarantee", re.I))

    def test_comparisons_use_address_level_sources_and_fair_housing_boundary(self) -> None:
        comparisons = (
            "blog/maplewood-vs-south-orange-nj.html",
            "es/blog/maplewood-vs-south-orange-nj.html",
            "blog/summit-vs-westfield-nj.html",
            "es/blog/summit-vs-westfield-nj.html",
            "westfield-vs-scotch-plains-nj.html",
        )
        for relative in comparisons:
            candidate = visible_text(self.pages[relative])
            with self.subTest(path=relative):
                self.assertIn("2024-25", candidate)
                self.assertRegex(candidate, re.compile(r"address|direcci[oó]n", re.I))
                self.assertRegex(candidate, re.compile(r"fair housing|vivienda justa", re.I))
                self.assertRegex(candidate, re.compile(r"trip planner|planificador de viajes", re.I))
                self.assertNotRegex(candidate, re.compile(r"\$\s?\d|\b\d+\s*(?:minutes?|minutos?)\b", re.I))

    def test_zero_click_duplicate_is_a_one_hop_noindex_fallback(self) -> None:
        source = self.pages[FALLBACK]
        self.assertIn('<meta name="robots" content="noindex, follow">', source)
        self.assertIn(f'<link rel="canonical" href="{SITE}{DESTINATION}">', source)
        self.assertIn(f'http-equiv="refresh" content="0; url={DESTINATION}"', source)
        self.assertIn(f"window.location.replace('{DESTINATION}')", source)
        self.assertIn(f'href="{DESTINATION}"', source)
        self.assertNotIn("application/ld+json", source)
        self.assertNotIn("hreflang=", source)

        redirects = json.loads(read("vercel.json"))["redirects"]
        exact = [
            item
            for item in redirects
            if item.get("source") in {
                "/blog/selling-inherited-house-multiple-heirs-nj",
                "/blog/selling-inherited-house-multiple-heirs-nj.html",
            }
        ]
        self.assertEqual(
            [
                {
                    "source": "/blog/selling-inherited-house-multiple-heirs-nj",
                    "destination": DESTINATION,
                    "permanent": True,
                },
                {
                    "source": "/blog/selling-inherited-house-multiple-heirs-nj.html",
                    "destination": DESTINATION,
                    "permanent": True,
                },
            ],
            exact,
        )

    def test_sitemap_and_internal_links_preserve_equity_without_duplicate_signals(self) -> None:
        urls = {}
        for sitemap_name in ("sitemap.xml", "sitemap-es.xml"):
            sitemap_root = ET.parse(ROOT / sitemap_name).getroot()
            urls.update({
                (node.find("{*}loc").text or "").rstrip("/"): node
                for node in sitemap_root.findall("{*}url")
            })
        self.assertNotIn(SITE + "/blog/selling-inherited-house-multiple-heirs-nj", urls)
        for route in INDEXABLE.values():
            with self.subTest(route=route):
                self.assertIn(SITE + route, urls)
                node = urls[SITE + route]
                relative = next(
                    path for path, value in INDEXABLE.items() if value == route
                )
                expected_modified = (
                    PAGE_MODIFIED_ON if relative in RELEASE_MODIFIED else REVIEWED_ON
                )
                self.assertEqual(expected_modified, node.find("{*}lastmod").text)
                alternates = {
                    link.attrib["hreflang"]: link.attrib["href"]
                    for link in node.findall("{*}link")
                }
                pair = next((value for value in BILINGUAL.values() if route in value), None)
                if pair:
                    en_route, es_route = pair
                    self.assertEqual(
                        {
                            "en-US": SITE + en_route,
                            "es-US": SITE + es_route,
                            "es": SITE + es_route,
                            "x-default": SITE + en_route,
                        },
                        alternates,
                    )
                else:
                    self.assertEqual(
                        {"en-US": SITE + route, "x-default": SITE + route},
                        alternates,
                    )

        old_targets: list[str] = []
        for path in ROOT.rglob("*.html"):
            if any(part in {".git", ".vercel", "node_modules"} for part in path.parts) or path.relative_to(ROOT).as_posix() == FALLBACK:
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r'href=["\']/blog/selling-inherited-house-multiple-heirs-nj(?:\.html)?["\']', source, re.I):
                old_targets.append(path.relative_to(ROOT).as_posix())
        self.assertEqual([], old_targets)


if __name__ == "__main__":
    unittest.main()
