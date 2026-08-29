#!/usr/bin/env python3
"""Render and audit the complete Spanish town-guide inventory.

The 32 towns in the verified canonical English inventory receive neutral,
Spanish-language research guides that link directly to primary public sources.
All other non-redirect Spanish town routes receive compact noindex/follow
fallbacks. Two established geographic aliases remain one-hop redirects, and
explicit English town-route consolidations are mirrored to their Spanish
counterparts.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlparse, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
MANIFEST_PATH = ROOT / "data" / "spanish-town-risk-decisions.json"
ENGLISH_MANIFEST_PATH = ROOT / "data" / "indexable-town-risk-decisions.json"
GSC_COMPARISON = ROOT / "tests" / "fixtures" / "gsc-spanish-town-pages.csv"
GSC_HISTORICAL = ROOT / "tests" / "fixtures" / "gsc-spanish-town-pages-16m.csv"
SHARE_IMAGE = f"{SITE}/images/hero.jpg"
SHARE_IMAGE_ALT_ES = "Imagen residencial del sitio web de The Jorge Ramirez Group"
SOURCE_REVIEWED_ON = "2026-08-26"
PAGE_MODIFIED_ON = "2026-08-27"
ORGANIZATION_ID = f"{SITE}/#organization"
PERSON_ID = f"{SITE}/#jorge-ramirez"
PROVENANCE_POLICY = {
    "publisher": "The Jorge Ramirez Group",
    "declaration": "ai-assisted, source-checked",
    "sourceCheckedDate": SOURCE_REVIEWED_ON,
    "responsibleContact": "Jorge Ramirez",
    "njRealEstateLicense": "1754604",
    "structuredDataRule": (
        "The WebPage publisher is the Organization; Jorge Ramirez is a Person "
        "who works for that Organization and is not represented as the page author or reviewer."
    ),
}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ESTABLISHED_GEOGRAPHIC_REDIRECTS = {
    "bernards-township": "basking-ridge",
    "short-hills": "millburn",
}


def _english_owned_town_redirects() -> dict[str, str]:
    document = json.loads(ENGLISH_MANIFEST_PATH.read_text(encoding="utf-8"))
    decisions = document.get("decisions")
    if not isinstance(decisions, dict):
        raise RuntimeError("English town decision manifest lacks decisions")

    redirects: dict[str, str] = {}
    for slug, decision in decisions.items():
        if not isinstance(decision, dict) or decision.get("action") != "redirect":
            continue
        destination = str(decision.get("destination", ""))
        match = re.fullmatch(r"/towns/([a-z0-9-]+)", destination)
        if match is None:
            raise RuntimeError(f"{slug}: unsupported English town redirect {destination!r}")
        redirects[str(slug)] = match.group(1)
    return redirects


ENGLISH_OWNER_REDIRECTS = _english_owned_town_redirects()
for alias, destination in ESTABLISHED_GEOGRAPHIC_REDIRECTS.items():
    inherited = ENGLISH_OWNER_REDIRECTS.get(alias)
    if inherited is not None and inherited != destination:
        raise RuntimeError(
            f"{alias}: Spanish geographic alias conflicts with English destination {inherited!r}"
        )
REDIRECTS = {**ESTABLISHED_GEOGRAPHIC_REDIRECTS, **ENGLISH_OWNER_REDIRECTS}

DISPLAY_OVERRIDES = {
    "basking-ridge": "Basking Ridge",
    "berkeley-heights": "Berkeley Heights",
    "bloomfield": "Bloomfield",
    "chatham": "Chatham",
    "chatham-borough": "Chatham Borough",
    "chatham-township": "Chatham Township",
    "cranford": "Cranford",
    "denville": "Denville",
    "east-brunswick": "East Brunswick",
    "east-hanover": "East Hanover",
    "fanwood": "Fanwood",
    "guttenberg": "Guttenberg",
    "helmetta": "Helmetta",
    "hoboken": "Hoboken",
    "jersey-city": "Jersey City",
    "madison": "Madison",
    "maplewood": "Maplewood",
    "middlesex": "Middlesex Borough",
    "millburn": "Millburn Township",
    "montclair": "Montclair",
    "morris-plains": "Morris Plains",
    "morristown": "Morristown",
    "new-providence": "New Providence",
    "newark": "Newark",
    "orange": "Orange",
    "roselle-park": "Roselle Park",
    "south-brunswick": "South Brunswick",
    "springfield": "Springfield",
    "summit": "Summit",
    "west-new-york": "West New York",
    "westfield": "Westfield",
    "woodbridge": "Woodbridge Township",
}

GENERIC_SOURCE_OVERRIDES: dict[str, list[str]] = {
    "helmetta": [
        "https://www.helmettaboro.com/",
        "https://www.nj.gov/dca/codes/",
        "https://www.nj.gov/education/spr/",
        "https://www.njtransit.com/schedules-and-fares",
        "https://dep.nj.gov/flooddisclosure/",
    ],
    "middlesex": [
        "https://www.middlesexboro-nj.gov/",
        "https://www.middlesexboro-nj.gov/finance",
        "https://www.nj.gov/education/spr/",
        "https://www.njtransit.com/schedules-and-fares",
        "https://dep.nj.gov/flooddisclosure/",
    ],
    "orange": [
        "https://www.orangenj.gov/",
        "https://orangenj.gov/355/Zoning-Division",
        "https://www.orangenj.gov/189/Planning-Economic-Development",
        "https://www.nj.gov/education/spr/",
        "https://www.njtransit.com/schedules-and-fares",
        "https://dep.nj.gov/flooddisclosure/",
    ],
    "woodbridge": [
        "https://www.twp.woodbridge.nj.us/27/Government",
        "https://twp.woodbridge.nj.us/m/directory",
        "https://www.nj.gov/education/spr/",
        "https://www.njtransit.com/schedules-and-fares",
        "https://dep.nj.gov/flooddisclosure/",
    ],
}

OFFICIAL_HOST_SUFFIXES = (
    ".gov",
    ".nj.us",
    "nj.gov",
    "census.gov",
    "njtransit.com",
    "panynj.gov",
    "bernards.org",
    "bernardsboe.com",
    "bhpsnj.org",
    "bloomfield.k12.nj.us",
    "bloomfieldtwpnj.com",
    "chatham-nj.org",
    "chathamborough.org",
    "chathamtownship.org",
    "cityofsummit.org",
    "cranfordnj.org",
    "cranfordschools.org",
    "denville.org",
    "denvillenj.gov",
    "easthanoverschools.org",
    "easthanovertownship.com",
    "eastbrunswick.org",
    "ebnet.org",
    "fanwoodnj.org",
    "guttenbergnj.org",
    "helmettaboro.com",
    "hobokennj.gov",
    "jerseycitynj.gov",
    "madisonpublicschools.org",
    "maplewoodnj.gov",
    "middlesexboro-nj.gov",
    "millburn.org",
    "montclairnjusa.org",
    "morrisplainsboro.org",
    "morrisschooldistrict.org",
    "newarknj.gov",
    "newprov.us",
    "npsd.k12.nj.us",
    "orangenj.gov",
    "rosellepark.net",
    "rosenet.org",
    "rpsd.org",
    "sbschools.org",
    "somsdk12.org",
    "southbrunswicknj.gov",
    "spfk12.org",
    "springfield-nj.us",
    "springfieldschools.com",
    "summit.k12.nj.us",
    "twp.millburn.nj.us",
    "twp.woodbridge.nj.us",
    "townofmorristown.org",
    "westfieldnj.gov",
    "westfieldnjk12.org",
    "westnewyorknj.org",
    "wnyschools.net",
)

COMPARISON_PERIODS = {
    "current3m": {
        "clicks": "Last 3 months Clicks",
        "impressions": "Last 3 months Impressions",
        "position": "Last 3 months Position",
    },
    "previous3m": {
        "clicks": "Previous 3 months Clicks",
        "impressions": "Previous 3 months Impressions",
        "position": "Previous 3 months Position",
    },
}
HISTORICAL_PERIODS = {
    "last16m": {
        "clicks": "Clicks",
        "impressions": "Impressions",
        "position": "Position",
    }
}


def display_name(slug: str) -> str:
    return DISPLAY_OVERRIDES.get(slug, " ".join(part.capitalize() for part in slug.split("-")))


def _number(row: Mapping[str, str], column: str) -> float:
    value = (row.get(column) or "0").replace(",", "").replace("%", "").strip()
    try:
        return float(value)
    except ValueError:
        return 0.0


def _spanish_town_slug(value: str, target_slugs: set[str]) -> str | None:
    path = urlsplit(value).path.rstrip("/")
    if path.endswith(".html"):
        path = path[:-5]
    match = re.fullmatch(r"/es/towns/([^/]+)", path)
    if not match or match.group(1) not in target_slugs:
        return None
    return match.group(1)


def fold_gsc_rows(
    rows: Iterable[Mapping[str, str]],
    target_slugs: set[str],
    periods: Mapping[str, Mapping[str, str]],
) -> dict[str, dict[str, dict[str, float | int]]]:
    """Fold clean, .html, and trailing-slash URL variants by town slug."""

    working: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "rows": 0.0,
                "clicks": 0.0,
                "impressions": 0.0,
                "positionWeight": 0.0,
            }
        )
    )
    for row in rows:
        slug = _spanish_town_slug(row.get("Top pages") or "", target_slugs)
        if not slug:
            continue
        for period, columns in periods.items():
            metric = working[slug][period]
            impressions = _number(row, columns["impressions"])
            metric["rows"] += 1
            metric["clicks"] += _number(row, columns["clicks"])
            metric["impressions"] += impressions
            metric["positionWeight"] += _number(row, columns["position"]) * impressions

    folded: dict[str, dict[str, dict[str, float | int]]] = {}
    for slug in sorted(target_slugs):
        folded[slug] = {}
        for period in periods:
            metric = working[slug][period]
            impressions = int(metric["impressions"])
            folded[slug][period] = {
                "rows": int(metric["rows"]),
                "clicks": int(metric["clicks"]),
                "impressions": impressions,
                "position": round(metric["positionWeight"] / impressions, 2) if impressions else 0,
            }
    return folded


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _is_official(url: str) -> bool:
    host = urlparse(url).netloc.casefold()
    if not host:
        return False
    return any(host == suffix or host.endswith("." + suffix.lstrip(".")) for suffix in OFFICIAL_HOST_SUFFIXES)


def _source_type(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.casefold()
    path = parsed.path.casefold()
    if "census.gov" in host:
        return "censo"
    if "njtransit.com" in host or "panynj.gov" in host:
        return "transporte"
    if "education" in path and "nj.gov" in host:
        return "educación estatal"
    if any(
        token in host
        for token in (
            "schools",
            "school",
            "k12",
            "boe",
            "district",
            "bhpsnj",
            "spfk12",
            "npsd",
            "sbschools",
            "somsdk12",
            "mhrd",
            "hpreg",
            "alkschool",
        )
    ):
        return "distrito escolar"
    if "dep.nj.gov" in host or "flood" in path:
        return "divulgación de inundación"
    if "treasury" in path or "taxation" in path:
        return "datos fiscales estatales"
    if any(token in path for token in ("assessor", "tax", "zoning", "planning", "maps", "permit", "building", "finance")):
        return "registro municipal"
    if host == "nj.gov" or host.endswith(".nj.gov"):
        return "agencia estatal"
    return "municipio"


def _source_label(kind: str, town: str, url: str) -> str:
    labels = {
        "censo": "U.S. Census Bureau",
        "transporte": "Planificador y horarios oficiales",
        "educación estatal": "Informes del Departamento de Educación de NJ",
        "distrito escolar": "Sitio oficial del distrito escolar",
        "divulgación de inundación": "Recursos de inundación de NJDEP",
        "datos fiscales estatales": "División de Tributación de Nueva Jersey",
        "registro municipal": f"Registros públicos de {town}",
        "agencia estatal": "Agencia estatal de Nueva Jersey",
        "municipio": f"Portal oficial de {town}",
    }
    if "panynj.gov" in urlparse(url).netloc.casefold():
        return "Horarios y mapas oficiales de PATH"
    return labels[kind]


def _source_purpose(kind: str, town: str) -> str:
    purposes = {
        "censo": f"Confirma la geografía oficial de {town} y permite consultar datos con su periodo de referencia.",
        "transporte": "Permite comprobar rutas, estaciones, horarios, conexiones y avisos para la fecha del viaje.",
        "educación estatal": "Publica informes escolares con metodología, año escolar y contexto estatal.",
        "distrito escolar": "Publica límites, matrícula, calendarios y contactos; confirma la asignación con la dirección completa.",
        "divulgación de inundación": "Reúne recursos estatales para revisar la divulgación y las preguntas de inundación por propiedad.",
        "datos fiscales estatales": "Publica archivos fiscales y de tasación con el año correspondiente.",
        "registro municipal": "Da acceso al departamento responsable de mapas, tasación, uso de suelo, permisos o expedientes locales.",
        "agencia estatal": "Ofrece el recurso público estatal aplicable a la investigación de la propiedad.",
        "municipio": "Es el punto de partida para localizar departamentos, ordenanzas, reuniones y documentos municipales vigentes.",
    }
    return purposes[kind]


def _candidate_links(slug: str) -> list[str]:
    if slug in GENERIC_SOURCE_OVERRIDES:
        return GENERIC_SOURCE_OVERRIDES[slug]
    source = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
    links = re.findall(r'<a\b[^>]*href=["\'](https?://[^"\']+)', source, re.I)
    return [html.unescape(link) for link in links]


def _normalize_source_url(url: str) -> str:
    """Prefer the current public landing page when an official URL moved."""

    cleaned = html.unescape(url).rstrip("#")
    parsed = urlparse(cleaned)
    if parsed.netloc.casefold() == "www.nj.gov" and parsed.path.casefold().startswith(
        "/education/schoolperformance"
    ):
        return "https://www.nj.gov/education/spr/"
    return cleaned


def _selected_sources(slug: str, town: str) -> list[dict[str, str]]:
    unique: list[str] = []
    for url in _candidate_links(slug):
        url = _normalize_source_url(url)
        if url not in unique and _is_official(url):
            unique.append(url)

    by_type: dict[str, list[str]] = defaultdict(list)
    for url in unique:
        by_type[_source_type(url)].append(url)

    order = (
        "municipio",
        "registro municipal",
        "censo",
        "distrito escolar",
        "educación estatal",
        "transporte",
        "divulgación de inundación",
        "datos fiscales estatales",
        "agencia estatal",
    )
    selected: list[str] = []
    municipal_limit = 2 if slug == "chatham" else 1
    for kind in order:
        limit = municipal_limit if kind == "municipio" else 1
        for url in by_type.get(kind, [])[:limit]:
            if url not in selected:
                selected.append(url)
    for url in unique:
        if len(selected) >= 6:
            break
        if url not in selected:
            selected.append(url)
    selected = selected[:7]
    if len(selected) < 4:
        raise RuntimeError(f"{slug}: fewer than four primary official sources: {selected}")

    return [
        {
            "type": _source_type(url),
            "label": _source_label(_source_type(url), town, url),
            "url": url,
            "purpose": _source_purpose(_source_type(url), town),
            "accessed": SOURCE_REVIEWED_ON,
        }
        for url in selected
    ]


def _canonical_inventory() -> tuple[set[str], dict[str, str]]:
    facts = json.loads((ROOT / "data" / "site-facts.json").read_text(encoding="utf-8"))
    county_by_slug = {
        slug: county
        for county, slugs in facts["canonicalTownInventory"]["byCounty"].items()
        for slug in slugs
    }
    return set(county_by_slug), county_by_slug


def _all_spanish_town_slugs() -> set[str]:
    return {path.stem for path in (ROOT / "es" / "towns").glob("*.html")}


def build_manifest() -> dict[str, object]:
    all_slugs = _all_spanish_town_slugs()
    canonical, county_by_slug = _canonical_inventory()
    if len(all_slugs) != 138:
        raise RuntimeError(f"expected 138 Spanish town routes, found {len(all_slugs)}")
    if not canonical <= all_slugs or not set(REDIRECTS) <= all_slugs:
        raise RuntimeError("canonical or redirect inventory is not present in es/towns")

    comparison = fold_gsc_rows(_read_csv(GSC_COMPARISON), all_slugs, COMPARISON_PERIODS)
    historical = fold_gsc_rows(_read_csv(GSC_HISTORICAL), all_slugs, HISTORICAL_PERIODS)
    decisions: dict[str, object] = {}
    for slug in sorted(all_slugs):
        town = display_name(slug)
        gsc = {**comparison[slug], **historical[slug]}
        if slug in canonical:
            action = "rebuild"
            county = county_by_slug[slug]
            sources = _selected_sources(slug, town)
            if slug == "chatham":
                reason = (
                    "The route remains in the current canonical English inventory and is the only "
                    "Spanish town route with a click in the supplied recent comparison; rebuild it "
                    "as a fluent, primary-source guide."
                )
            else:
                reason = (
                    "The route remains in the current canonical English inventory; preserve its "
                    "bilingual search value with a fluent, primary-source guide."
                )
            destination = None
        elif slug in REDIRECTS:
            action = "redirect"
            county = county_by_slug[REDIRECTS[slug]]
            sources = []
            destination = f"/es/towns/{REDIRECTS[slug]}"
            if slug in ESTABLISHED_GEOGRAPHIC_REDIRECTS:
                reason = "The route is a duplicate place-name alias with an established one-hop canonical destination."
            else:
                reason = (
                    "The English town-route owner consolidates this duplicate route into "
                    f"/towns/{REDIRECTS[slug]}; mirror that relationship at the equivalent "
                    "one-hop Spanish destination."
                )
        else:
            action = "quarantine"
            county = ""
            sources = []
            destination = None
            reason = (
                "The route is no longer part of the canonical town inventory and the retired "
                "template lacked sufficient verified local value; retain a compact noindex/follow "
                "fallback without town figures or outcome claims."
            )
        decisions[slug] = {
            "displayName": town,
            "county": county,
            "action": action,
            "destination": destination,
            "reason": reason,
            "gsc": gsc,
            "legacyRiskCategories": [
                "protected-class or lifestyle-proxy targeting",
                "unsupported school or safety characterization",
                "unsourced market figures and investment language",
                "unverified commute durations or route claims",
                "stale or faux first-person expertise language",
            ],
            "sources": sources,
        }

    action_counts = {
        action: sum(1 for item in decisions.values() if item["action"] == action)
        for action in ("rebuild", "quarantine", "redirect")
    }
    return {
        "schemaVersion": 1,
        "effectiveDate": PAGE_MODIFIED_ON,
        "scope": "All rendered HTML routes under es/towns; English and blog market-report files are excluded.",
        "provenancePolicy": dict(PROVENANCE_POLICY),
        "decisionPolicy": {
            "rebuildRule": "Rebuild every route in the current canonical English inventory so reciprocal bilingual routes remain useful and source-backed.",
            "quarantineRule": "Use a compact noindex/follow fallback for every noncanonical route that is neither an established geographic alias nor an English-owner town-route consolidation.",
            "redirectRule": "Keep the two established one-hop geographic aliases and mirror explicit town redirects from the English route owner; never redirect to another redirect or noindex page.",
            "demandRule": "Preserve supplied GSC demand as context, while canonical inventory and content quality determine index eligibility.",
        },
        "evidencePolicy": (
            "Primary public sources only; no gated or scraped market tables, no town-price substitutions, "
            "no rankings, travel-duration promises, forecasts, or demographic targeting."
        ),
        "designContract": {
            "dark": ["#0A0A0A", "#1A1A1A"],
            "red": ["#C41230", "#8B0D22"],
            "gold": ["#B8962E", "#D4AF5A"],
            "ivory": ["#F8F6F2", "#FAFAF8"],
            "headingFont": "Playfair Display",
            "bodyFont": "Inter",
            "minimumControlHeightPx": 44,
        },
        "gscExports": {
            "comparison": {
                "fixture": "tests/fixtures/gsc-spanish-town-pages.csv",
                "sourceExport": "Google Search Console Pages comparison supplied for this remediation",
                "periods": COMPARISON_PERIODS,
            },
            "historical": {
                "fixture": "tests/fixtures/gsc-spanish-town-pages-16m.csv",
                "sourceExport": "Google Search Console Pages historical export supplied for this remediation",
                "periods": HISTORICAL_PERIODS,
            },
        },
        "inventorySummary": {
            "total": len(decisions),
            "actions": action_counts,
            "sitemapEligible": action_counts["rebuild"],
        },
        "decisions": decisions,
    }


def spanish_managed_slugs() -> set[str]:
    """Public generator fence for every Spanish town route."""

    if MANIFEST_PATH.exists():
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return set(data["decisions"])
    return _all_spanish_town_slugs()


def _identity_note(slug: str, town: str, county: str) -> str:
    if slug == "basking-ridge":
        return (
            "Basking Ridge es una comunidad no incorporada dentro de Bernards Township. "
            "Para una vivienda concreta, confirma Bernards Township como municipio registral y usa sus oficinas para el bloque, lote, tasación y uso de suelo."
        )
    if slug == "chatham":
        return (
            "El nombre Chatham puede referirse a Chatham Borough o Chatham Township, dos municipios distintos del Condado de Morris. "
            "La dirección postal por sí sola no identifica qué tasador, mapa o norma local corresponde a la parcela."
        )
    if slug == "millburn":
        return (
            "Esta guía corresponde a Millburn Township. Short Hills es un nombre postal dentro del municipio; "
            "los expedientes de una propiedad deben verificarse con el bloque, lote y oficina municipal responsable."
        )
    return (
        f"Esta ruta corresponde a {town}, en el Condado de {county}. Antes de usar una comparación municipal, "
        "confirma la dirección completa, el bloque y lote, y el municipio que figura en el registro público."
    )


def _alternate_tags(slug: str) -> str:
    english = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
    spanish_url = f"{SITE}/es/towns/{slug}"
    if f'hreflang="es-US" href="{spanish_url}"' not in english:
        return ""
    english_url = f"{SITE}/towns/{slug}"
    return (
        f'  <link rel="alternate" hreflang="en-US" href="{english_url}">\n'
        f'  <link rel="alternate" hreflang="es-US" href="{spanish_url}">\n'
        f'  <link rel="alternate" hreflang="es" href="{spanish_url}">\n'
        f'  <link rel="alternate" hreflang="x-default" href="{english_url}">\n'
    )


def _schema(slug: str, town: str, description: str) -> str:
    canonical = f"{SITE}/es/towns/{slug}"
    title = f"{town}: guía de propiedades | Jorge Ramirez"
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "inLanguage": "es-US",
                "dateModified": PAGE_MODIFIED_ON,
                "about": {"@type": "Place", "name": town},
                "publisher": {"@id": ORGANIZATION_ID},
                "isPartOf": {
                    "@type": "WebSite",
                    "name": "The Jorge Ramirez Group",
                    "url": f"{SITE}/",
                },
            },
            {
                "@type": "Organization",
                "@id": ORGANIZATION_ID,
                "name": PROVENANCE_POLICY["publisher"],
                "url": f"{SITE}/",
                "telephone": "+1-908-230-7844",
                "email": "jorge.ramirez@kw.com",
            },
            {
                "@type": "Person",
                "@id": PERSON_ID,
                "name": PROVENANCE_POLICY["responsibleContact"],
                "url": f"{SITE}/es/ai-authority",
                "jobTitle": "Vendedor de bienes raíces con licencia de Nueva Jersey",
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "Licencia de vendedor de bienes raíces de Nueva Jersey",
                    "value": PROVENANCE_POLICY["njRealEstateLicense"],
                },
                "worksFor": {"@id": ORGANIZATION_ID},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": f"{SITE}/es/"},
                    {"@type": "ListItem", "position": 2, "name": "Comunidades", "item": f"{SITE}/es/communities"},
                    {"@type": "ListItem", "position": 3, "name": town, "item": canonical},
                ],
            },
            {
                "@type": "LocalBusiness",
                "@id": f"{SITE}/#summit-office",
                "name": "The Jorge Ramirez Group",
                "url": f"{SITE}/",
                "parentOrganization": {"@id": ORGANIZATION_ID},
                "telephone": "+1-908-230-7844",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "488 Springfield Ave",
                    "addressLocality": "Summit",
                    "addressRegion": "NJ",
                    "postalCode": "07901",
                    "addressCountry": "US",
                },
                "areaServed": {"@type": "Place", "name": town},
            },
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _source_cards(sources: list[dict[str, str]]) -> str:
    cards = []
    for source in sources:
        cards.append(
            f'''          <article class="town-guide__source-card">
            <p class="town-guide__source-type">{html.escape(source["type"])}</p>
            <h3>{html.escape(source["label"])}</h3>
            <p>{html.escape(source["purpose"])}</p>
            <a href="{html.escape(source["url"], quote=True)}" rel="noopener">Abrir fuente oficial</a>
          </article>'''
        )
    return "\n".join(cards)


def render_rebuild(slug: str, decision: dict[str, object]) -> str:
    town = str(decision["displayName"])
    county = str(decision["county"])
    canonical = f"{SITE}/es/towns/{slug}"
    title = f"{town}: guía de propiedades | Jorge Ramirez"
    description = (
        f"Guía de {town}, NJ, con fuentes públicas para comprobar municipio, parcela, "
        "uso de suelo, educación y transporte por dirección."
    )
    county_href = f"/es/counties/{county.casefold()}-county"
    sources = decision["sources"]
    assert isinstance(sources, list)
    identity = _identity_note(slug, town, county)
    return f'''<!DOCTYPE html>
<html lang="es-US">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0A0A0A">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta name="ai-content-declaration" content="{html.escape(PROVENANCE_POLICY['declaration'], quote=True)}">
  <link rel="canonical" href="{canonical}">
{_alternate_tags(slug)}  <meta property="og:type" content="website">
  <meta property="og:site_name" content="The Jorge Ramirez Group">
  <meta property="og:locale" content="es_US">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:image" content="{SHARE_IMAGE}">
  <meta property="og:image:width" content="1400">
  <meta property="og:image:height" content="933">
  <meta property="og:image:alt" content="{SHARE_IMAGE_ALT_ES}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="{canonical}">
  <meta name="twitter:title" content="{html.escape(title, quote=True)}">
  <meta name="twitter:description" content="{html.escape(description, quote=True)}">
  <meta name="twitter:image" content="{SHARE_IMAGE}">
  <meta name="twitter:image:alt" content="{SHARE_IMAGE_ALT_ES}">
  <meta name="llm-context" content="Guía en español basada en fuentes públicas para investigar una propiedad en {html.escape(town, quote=True)} por dirección y parcela; no publica precios, calificaciones, duraciones ni pronósticos.">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <link rel="icon" href="/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/town-evidence-guide.css">
  <script type="application/ld+json">{_schema(slug, town, description)}</script>
</head>
<body class="town-evidence-guide" data-spanish-town-guide="v1">
  <a class="skip-link" href="#main">Saltar al contenido principal</a>
  <nav class="town-guide__nav" aria-label="Navegación principal">
    <div class="town-guide__nav-inner">
      <a class="town-guide__brand" href="/es/" aria-label="Inicio de The Jorge Ramirez Group">
        <picture>
          <source srcset="/images/jorge-logo.webp" type="image/webp">
          <img src="/images/jorge-logo.jpg" width="250" height="100" alt="The Jorge Ramirez Group">
        </picture>
      </a>
      <ul class="town-guide__nav-links">
        <li><a href="/es/communities">Comunidades</a></li>
        <li><a href="/es#contact">Contactar a Jorge</a></li>
      </ul>
    </div>
  </nav>
  <main id="main" tabindex="-1">
    <section class="town-guide__hero" aria-labelledby="page-title">
      <div class="town-guide__hero-inner">
        <p class="town-guide__eyebrow">Condado de {html.escape(county)} · investigación con fuentes públicas</p>
        <h1 id="page-title">Cómo investigar una propiedad en {html.escape(town)}</h1>
        <p class="town-guide__lede">Un punto de partida práctico para confirmar el municipio, la parcela, los expedientes de uso de suelo, los recursos educativos y el plan de transporte asociado a una dirección.</p>
      </div>
    </section>

    <div class="town-guide__layout">
      <article class="town-guide__article">
        <section class="town-guide__section" aria-labelledby="identity-heading">
          <p class="town-guide__eyebrow">Primero, la identidad registral</p>
          <h2 id="identity-heading">Confirma qué oficina mantiene la parcela</h2>
          <div class="town-guide__notice">
            <p>{html.escape(identity)}</p>
          </div>
          <p>Los nombres postales, los límites escolares y los límites municipales no siempre responden a la misma pregunta. Usa el identificador de parcela y la oficina que conserva el expediente para evitar mezclar datos de jurisdicciones distintas.</p>
        </section>

        <section class="town-guide__section" aria-labelledby="checks-heading">
          <p class="town-guide__eyebrow">Revisión por dirección</p>
          <h2 id="checks-heading">Comprobaciones antes de comparar viviendas</h2>
          <p>Una reseña del municipio no determina el estado físico, el uso legal, los impuestos, el título, los permisos, las obligaciones de una asociación, las condiciones de una póliza, el trayecto de una persona ni el resultado de una transacción. Introduce la dirección exacta en los recursos correspondientes y confirma cada dato sensible al tiempo con la oficina o el profesional responsable.</p>
          <ul class="town-guide__checklist">
            <li>Confirma municipio, bloque, lote, tipo de propiedad y dirección oficial.</li>
            <li>Revisa tasación, mapa fiscal, zona, permisos y expedientes públicos disponibles.</li>
            <li>Contrasta escritura, estudio, título, divulgaciones y documentos de asociación cuando correspondan.</li>
            <li>Comprueba recursos escolares directamente con el distrito y con NJDOE; no uses una puntuación agregada como sustituto.</li>
            <li>Prueba el trayecto con origen, destino, fecha y hora reales en la agencia operadora.</li>
            <li>Aplica la misma lista de preguntas y los mismos criterios objetivos a cada vivienda.</li>
          </ul>
        </section>

        <section class="town-guide__section" aria-labelledby="sources-heading">
          <p class="town-guide__eyebrow">Fuentes consultadas el 26 de agosto de 2026</p>
          <h2 id="sources-heading">Abre las fuentes públicas primarias</h2>
          <p>Los enlaces siguientes conducen a organismos públicos, municipios, distritos u operadores oficiales. Los expedientes y horarios pueden cambiar; confirma la fecha, la parcela, el trámite y el servicio que realmente corresponden.</p>
          <div class="town-guide__sources">
{_source_cards(sources)}
          </div>
        </section>

        <section class="town-guide__section" aria-labelledby="method-heading">
          <p class="town-guide__eyebrow">Método neutral</p>
          <h2 id="method-heading">Separa los hechos de las preferencias</h2>
          <p>Registra en una hoja de trabajo la fuente, la fecha de consulta y el resultado para cada dirección. Mantén aparte tus preferencias personales, como tipo de vivienda, presupuesto, accesibilidad, conexiones de transporte o cercanía a servicios concretos. Así puedes comparar propiedades con un método repetible sin convertir características personales o suposiciones sobre residentes en criterios de vivienda.</p>
          <p>Esta guía no clasifica municipios ni predice precios, horarios, resultados escolares, condiciones de una zona, rendimientos financieros o resultados de una operación. Para cualquier cifra de mercado, solicita un análisis actual que identifique su fuente, periodo, universo de propiedades y método de cálculo.</p>
        </section>
        <aside class="town-guide__notice" data-content-provenance="v1" aria-label="Procedencia del contenido">
          <p><strong>Publicado por The Jorge Ramirez Group.</strong> Contenido elaborado con asistencia de IA y fuentes verificadas el 26 de agosto de 2026. Jorge Ramirez es vendedor de bienes raíces con licencia de Nueva Jersey (#1754604). <a href="/es#contact">Contacta a Jorge o solicita una corrección.</a></p>
        </aside>
      </article>

      <aside class="town-guide__aside" aria-labelledby="aside-heading">
        <h2 id="aside-heading">Qué llevar a la revisión</h2>
        <p>Dirección completa, bloque y lote si están disponibles, tipo de propiedad, preguntas sobre expedientes y la fecha en que necesitas la información.</p>
        <p>La respuesta debe quedar vinculada a esa propiedad y a una fuente identificable.</p>
        <a href="{county_href}">Ver la guía del Condado de {html.escape(county)}</a>
      </aside>
    </div>

    <section class="town-guide__cta" aria-labelledby="contact-heading">
      <div class="town-guide__cta-inner">
        <h2 id="contact-heading">¿Necesitas un plan para una dirección concreta?</h2>
        <p>Envía la dirección y las preguntas de registro o transacción que quieres investigar. Esta página no envía ningún formulario por sí sola.</p>
        <a class="town-guide__button" href="/es#contact">Contactar a Jorge</a>
      </div>
    </section>
  </main>
  <footer class="town-guide__footer">
    <p>The Jorge Ramirez Group · Keller Williams Premier Properties</p>
    <p><a href="/es/">Inicio</a> · <a href="/es/privacy-policy">Política de privacidad</a></p>
  </footer>
</body>
</html>
'''


def _fallback_county(slug: str) -> str:
    try:
        from town_data import COUNTY

        county = COUNTY.get(slug)
        if county:
            return county
    except (ImportError, AttributeError):
        pass
    return "Nueva Jersey"


def render_quarantine(slug: str, decision: dict[str, object]) -> str:
    town = str(decision["displayName"])
    county = _fallback_county(slug)
    canonical = f"{SITE}/es/towns/{slug}"
    title = f"Guía de {town} en revisión | Jorge Ramirez"
    description = (
        f"La guía anterior de {town} está en revisión editorial. Consulta la guía regional "
        "o contacta a Jorge para investigar una propiedad concreta con fuentes actuales."
    )
    if county in {"Union", "Essex", "Morris", "Hudson", "Middlesex", "Somerset"}:
        county_href = f"/es/counties/{county.casefold()}-county"
        county_label = f"Guía del Condado de {county}"
    else:
        county_href = "/es/communities"
        county_label = "Directorio de comunidades"
    return f'''<!DOCTYPE html>
<html lang="es-US">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0A0A0A">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="The Jorge Ramirez Group">
  <meta property="og:locale" content="es_US">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:image" content="{SHARE_IMAGE}">
  <meta property="og:image:width" content="1400">
  <meta property="og:image:height" content="933">
  <meta property="og:image:alt" content="{SHARE_IMAGE_ALT_ES}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="{canonical}">
  <meta name="twitter:title" content="{html.escape(title, quote=True)}">
  <meta name="twitter:description" content="{html.escape(description, quote=True)}">
  <meta name="twitter:image" content="{SHARE_IMAGE}">
  <meta name="twitter:image:alt" content="{SHARE_IMAGE_ALT_ES}">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <link rel="icon" href="/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/town-fallback.css">
</head>
<body class="town-fallback" data-spanish-town-fallback="v1">
  <a href="#main" class="skip-link">Saltar al contenido principal</a>
  <nav class="town-fallback__nav" aria-label="Navegación principal">
    <div class="town-fallback__nav-inner">
      <a class="town-fallback__brand" href="/es/" aria-label="Inicio de The Jorge Ramirez Group">
        <picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" width="250" height="100" alt="The Jorge Ramirez Group"></picture>
      </a>
      <ul class="town-fallback__nav-links"><li><a href="/es/communities">Comunidades</a></li><li><a href="/es#contact" data-contact-link>Contactar a Jorge</a></li></ul>
    </div>
  </nav>
  <main id="main" tabindex="-1">
    <section class="town-fallback__hero" aria-labelledby="page-title">
      <div class="town-fallback__hero-inner">
        <p class="town-fallback__eyebrow">Estado de la guía local</p>
        <h1 id="page-title">La guía detallada de {html.escape(town)} está en revisión</h1>
        <p class="town-fallback__lede">El contenido anterior se retiró porque sus detalles locales no estaban suficientemente verificados. Esta dirección web permanece disponible mientras se revisa un reemplazo conciso y respaldado por fuentes públicas.</p>
      </div>
    </section>
    <section class="town-fallback__content" aria-labelledby="next-step-title">
      <article class="town-fallback__card">
        <h2 id="next-step-title">Empieza con el recurso regional</h2>
        <p>Usa el recurso regional para obtener el contexto que el sitio mantiene actualmente. Si tu pregunta corresponde a una vivienda, compra, venta o traslado concreto, comparte la dirección y el dato que quieres comprobar. La orientación debe basarse en expedientes actuales, información vigente de la propiedad cuando esté disponible y los hechos que proporciones.</p>
        <div class="town-fallback__actions">
          <a class="town-fallback__button town-fallback__button--primary" href="{county_href}">Abrir {html.escape(county_label)}</a>
          <a class="town-fallback__button town-fallback__button--secondary" href="/es#contact">Contactar a Jorge</a>
        </div>
        <p class="town-fallback__note">Esta página de transición se excluye intencionalmente de los sitemaps de búsqueda. No publica cifras locales, puntuaciones, duraciones, perfiles de residentes ni promesas de resultado.</p>
      </article>
    </section>
  </main>
  <footer class="town-fallback__footer"><p>The Jorge Ramirez Group · Keller Williams Premier Properties</p><p><a href="/es/">Inicio</a> · <a href="/es/privacy-policy">Política de privacidad</a></p></footer>
</body>
</html>
'''


def render_redirect(slug: str, decision: dict[str, object]) -> str:
    town = str(decision["displayName"])
    destination = str(decision["destination"])
    target_slug = destination.rsplit("/", 1)[-1]
    target = display_name(target_slug)
    canonical = f"{SITE}{destination}"
    return f'''<!DOCTYPE html>
<html lang="es-US">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0A0A0A">
  <meta name="robots" content="noindex, follow">
  <meta http-equiv="refresh" content="0; url={destination}">
  <link rel="canonical" href="{canonical}">
  <title>Página trasladada a {html.escape(target)} | The Jorge Ramirez Group</title>
  <meta name="description" content="La ruta de {html.escape(town, quote=True)} se consolidó en la guía de {html.escape(target, quote=True)}.">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/town-fallback.css">
  <script>window.location.replace({json.dumps(destination)});</script>
</head>
<body class="town-fallback" data-spanish-town-redirect="v1">
  <a href="#main" class="skip-link">Saltar al contenido principal</a>
  <main id="main" tabindex="-1" class="town-fallback__content">
    <article class="town-fallback__card">
      <p class="town-fallback__eyebrow">{html.escape(town)}</p>
      <h1>Esta página se trasladó</h1>
      <p>Continúa a la guía consolidada de {html.escape(target)}.</p>
      <div class="town-fallback__actions"><a class="town-fallback__button town-fallback__button--primary" href="{destination}">Abrir la guía</a></div>
    </article>
  </main>
</body>
</html>
'''


def render_page(slug: str, decision: dict[str, object]) -> str:
    if decision["action"] == "rebuild":
        return render_rebuild(slug, decision)
    if decision["action"] == "redirect":
        return render_redirect(slug, decision)
    return render_quarantine(slug, decision)


def _sitemap_block(slug: str) -> str:
    canonical = f"{SITE}/es/towns/{slug}"
    alternates = _alternate_tags(slug)
    xhtml = ""
    if alternates:
        english = f"{SITE}/towns/{slug}"
        xhtml = (
            f'    <xhtml:link rel="alternate" hreflang="en-US" href="{english}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="es-US" href="{canonical}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="es" href="{canonical}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{english}"/>\n'
        )
    return (
        "  <url>\n"
        f"    <loc>{canonical}</loc>\n"
        f"    <lastmod>{PAGE_MODIFIED_ON}</lastmod>\n"
        "    <changefreq>weekly</changefreq>\n"
        "    <priority>0.8</priority>\n"
        f"{xhtml}"
        "  </url>\n"
    )


def expected_sitemap(source: str, manifest: dict[str, object]) -> str:
    blocks = re.findall(
        r"^[ \t]*<url>\n.*?^[ \t]*</url>\n",
        source,
        re.MULTILINE | re.DOTALL,
    )
    stripped = source
    for block in blocks:
        if f"{SITE}/es/towns/" in block:
            stripped = stripped.replace(block, "")
    rebuilt = [
        slug
        for slug, item in manifest["decisions"].items()
        if item["action"] == "rebuild"
    ]
    insertion = "".join(_sitemap_block(slug) for slug in sorted(rebuilt))
    body = stripped.rstrip().removesuffix("</urlset>").rstrip()
    return body + "\n" + insertion + "</urlset>\n"


def _write_if_changed(path: Path, value: str) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == value:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return True


def render_all(manifest: dict[str, object]) -> list[Path]:
    changed: list[Path] = []
    for slug, decision in manifest["decisions"].items():
        path = ROOT / "es" / "towns" / f"{slug}.html"
        if _write_if_changed(path, render_page(slug, decision)):
            changed.append(path)
    sitemap = ROOT / "sitemap-es.xml"
    expected = expected_sitemap(sitemap.read_text(encoding="utf-8"), manifest)
    if _write_if_changed(sitemap, expected):
        changed.append(sitemap)
    return changed


def drift(manifest: dict[str, object]) -> list[str]:
    issues: list[str] = []
    if not MANIFEST_PATH.exists() or json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) != manifest:
        issues.append("manifest drift: data/spanish-town-risk-decisions.json")
    for slug, decision in manifest["decisions"].items():
        path = ROOT / "es" / "towns" / f"{slug}.html"
        if not path.exists() or path.read_text(encoding="utf-8") != render_page(slug, decision):
            issues.append(f"page drift: es/towns/{slug}.html")
    sitemap = ROOT / "sitemap-es.xml"
    current = sitemap.read_text(encoding="utf-8")
    if current != expected_sitemap(current, manifest):
        issues.append("sitemap drift: sitemap-es.xml")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report manifest, page, or sitemap drift")
    parser.add_argument("--manifest-only", action="store_true", help="refresh only the versioned decision manifest")
    args = parser.parse_args()

    manifest = build_manifest()
    if args.check:
        issues = drift(manifest)
        for issue in issues:
            print(issue, file=sys.stderr)
        if issues:
            return 1
        actions = manifest["inventorySummary"]["actions"]
        print(
            "Spanish town remediation check passed: "
            f"138 routes, {actions['rebuild']} rebuilds, "
            f"{actions['quarantine']} fallbacks, {actions['redirect']} redirects"
        )
        return 0

    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    manifest_changed = _write_if_changed(MANIFEST_PATH, manifest_text)
    if args.manifest_only:
        print(f"Spanish town manifest changed: {manifest_changed}")
        return 0
    changed = render_all(manifest)
    print(f"Spanish town remediation rendered {len(changed)} changed files; manifest changed: {manifest_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
