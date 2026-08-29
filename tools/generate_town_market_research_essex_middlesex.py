#!/usr/bin/env python3
"""Render the reviewed Essex/Middlesex/Somerset town research batch."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "town-market-research-essex-middlesex-somerset.json"
SITE_FACTS = ROOT / "data" / "site-facts.json"
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
PAGE_MODIFIED_ON = "2026-08-27"
AI_DECLARATION = "ai-assisted, source-checked"
RENDERER_NAME = "tools/generate_town_market_research_essex_middlesex.py"
EXPECTED_SLUGS = {
    "glen-ridge",
    "livingston",
    "maplewood",
    "metuchen",
    "montclair",
    "short-hills",
    "south-brunswick",
    "south-orange",
    "warren-township",
    "west-orange",
    "woodbridge",
}
EXPECTED_SOURCE_IDS = {
    "nj-treasury-statistics",
    "nj-treasury-average-residential-2025",
    "nj-treasury-average-residential-2026-context",
    "njr-market-data",
    "njr-public-county-portal",
    "nj-dca-fair-housing",
}
METRIC_LABELS = (
    "# of Line Items",
    "Avg Assessment",
    "Avg Tax Bill",
    "# of Sales",
    "Avg Sales Price",
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1:
        raise ValueError("town market source manifest schemaVersion must be 1")
    if document.get("reviewedOn") != REVIEWED_ON:
        raise ValueError(f"town market sources must be reviewed on {REVIEWED_ON}")
    if document.get("renderer") != RENDERER_NAME:
        raise ValueError("town market manifest points to another renderer")
    direct_answer_rule = document.get("publicationPolicy", {}).get(
        "directAnswerRule", ""
    )
    if not str(direct_answer_rule).startswith("Lead with a 40-60-word"):
        raise ValueError("town market manifest lacks the direct-answer publication rule")

    reports = document.get("reports")
    if not isinstance(reports, list) or len(reports) != 11:
        raise ValueError("town market manifest must contain exactly eleven reports")
    if {item.get("slug") for item in reports} != EXPECTED_SLUGS:
        raise ValueError("town market manifest changed its approved route scope")
    if len({item.get("slug") for item in reports}) != len(reports):
        raise ValueError("town market manifest contains duplicate slugs")

    sources = document.get("sharedSources")
    if not isinstance(sources, list):
        raise ValueError("town market sharedSources must be a list")
    if {item.get("id") for item in sources} != EXPECTED_SOURCE_IDS:
        raise ValueError("town market manifest changed its reviewed shared sources")
    for source in sources:
        if source.get("accessedOn") != REVIEWED_ON:
            raise ValueError(f"source {source.get('id')} lacks the reviewed access date")
        if not str(source.get("url", "")).startswith("https://"):
            raise ValueError(f"source {source.get('id')} is not an HTTPS source")
        for field in ("publisher", "title", "use", "limit"):
            if not str(source.get(field, "")).strip():
                raise ValueError(f"source {source.get('id')} lacks {field}")

    for report in reports:
        slug = report["slug"]
        expected_routes = {
            "en": f"/blog/market-report-{slug}-nj-2026",
            "es": f"/es/blog/market-report-{slug}-nj-2026",
        }
        if report.get("routes") != expected_routes:
            raise ValueError(f"report {slug} changed its canonical routes")
        if report.get("statisticsYear") != 2025:
            raise ValueError(f"report {slug} must use only finalized 2025 statistics")
        statistics = report.get("statistics")
        if not isinstance(statistics, dict) or tuple(statistics) != METRIC_LABELS:
            raise ValueError(f"report {slug} changed the Treasury field labels")
        for label, value in statistics.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"report {slug} has no value for {label}")
        if not str(report.get("treasuryCode", "")).isdigit():
            raise ValueError(f"report {slug} lacks a Treasury district code")
        if not str(report.get("treasuryDistrict", "")).strip():
            raise ValueError(f"report {slug} lacks a Treasury district name")
        for source_key in ("municipalitySource", "censusSource"):
            source = report.get(source_key)
            if not isinstance(source, dict):
                raise ValueError(f"report {slug} lacks {source_key}")
            if source.get("accessedOn") != REVIEWED_ON:
                raise ValueError(f"report {slug} has an unreviewed {source_key}")
            if not str(source.get("url", "")).startswith("https://"):
                raise ValueError(f"report {slug} has an invalid {source_key} URL")
    return document


def load_site_facts() -> dict[str, Any]:
    document = json.loads(SITE_FACTS.read_text(encoding="utf-8"))
    business = document.get("business", {})
    expected = {
        "name": "The Jorge Ramirez Group",
        "agentName": "Jorge Ramirez",
        "njRealEstateLicense": "1754604",
    }
    for key, value in expected.items():
        if business.get(key) != value:
            raise ValueError(f"verified site fact changed: business.{key}")
    if business.get("directPhone", {}).get("e164") != "+19082307844":
        raise ValueError("verified direct phone changed")
    if business.get("email") != "jorge.ramirez@kw.com":
        raise ValueError("verified email changed")
    if business.get("brokerage", {}).get("displayName") != "Keller Williams Premier Properties":
        raise ValueError("verified brokerage changed")
    return business


def page_copy(report: Mapping[str, Any], language: str) -> dict[str, Any]:
    name = report["displayName"]
    county = report["county"]
    district = report["treasuryDistrict"]
    if language == "en":
        return {
            "title": f"{name} Market Research Guide 2026 | 2025 Data",
            "description": (
                f"Research {name}, New Jersey with the finalized 2025 NJ Treasury "
                f"{district} row, direct public sources, current county links, and methodology."
            ),
            "llm": (
                f"Source-led {name}, New Jersey research guide. It publishes only the exact "
                f"finalized 2025 NJ Treasury {district} row, labels all five fields as the source "
                "does, links current public sources, and makes no forecast or property valuation."
            ),
            "skip": "Skip to main content",
            "nav_label": "Primary navigation",
            "menu": "Menu",
            "home": "Home",
            "communities": "Communities",
            "county": f"{county} County",
            "research": "Research",
            "language": "Español",
            "valuation": "Request a home valuation",
            "eyebrow": "Official-source town research",
            "h1": f"{name} real estate research: verified 2025 public data",
            "dek": (
                f"This page’s finalized 2025 New Jersey Treasury source row is {district} in {county} County. "
                f"It reports {report['statistics']['# of Sales']} sales, an average sales price of "
                f"{report['statistics']['Avg Sales Price']}, an average assessment of "
                f"{report['statistics']['Avg Assessment']}, and an average tax bill of "
                f"{report['statistics']['Avg Tax Bill']}. These are historical district averages, "
                "not current listing data or a home valuation."
            ),
            "reviewed": "Sources reviewed",
            "prepared": "The Jorge Ramirez Group · AI-assisted, source-checked",
            "geography_heading": "Start with the exact geography",
            "geography_lead": report["identityEn"],
            "research_note": report["researchNoteEn"],
            "municipal_link": f"Open the {report['municipalitySource']['publisher']} source",
            "census_link": "Open the Census geography source",
            "stats_eyebrow": "Finalized annual source",
            "stats_heading": "2025 NJ Treasury district record",
            "stats_lead": (
                "The five labels and values below reproduce one public district row from the "
                "State's finalized 2025 Average Residential Statistics file."
            ),
            "district_label": "Treasury district",
            "code_label": "C/D code",
            "source_year_label": "Source year",
            "label_note": (
                "The source labels the monetary summary fields “Avg.” This page preserves "
                "those labels and does not substitute a different summary measure."
            ),
            "open_2025": "Open the finalized 2025 Treasury PDF",
            "open_stats": "Open the Treasury statistics library",
            "current_heading": "Use current sources without inventing current values",
            "current_treasury_title": "2026 Treasury file: context only",
            "current_treasury_text": (
                "The State links a current-year file, but at this review it did not expose "
                "the complete tax and sales columns used above. This page therefore does "
                "not calculate, infer, or publish missing 2026 values."
            ),
            "current_treasury_link": "Review the current-year Treasury file",
            "county_title": f"Current {county} County reports",
            "county_text": (
                "New Jersey Realtors provides a public county-report portal. Select the county, "
                "exact period, and available property category at the source. A county result "
                "is not a town result, and this page does not copy member-only tables."
            ),
            "njr_page": "Read the NJ Realtors publication page",
            "njr_portal": "Open the public county-report portal",
            "method_heading": "A repeatable research method",
            "method_steps": (
                "Name the scope first: county, legal municipality or tax district, or individual property.",
                "Record the source, exact field label, reporting year or period, geography, and access date.",
                "Compare only compatible geographies, periods, property categories, and field definitions.",
                "For one home, replace broad context with current comparable properties and verified subject-property facts.",
            ),
            "method_note": (
                "These public averages are historical district context. They are not a listing "
                "price, appraisal, forecast, or prediction of a transaction result."
            ),
            "fair_heading": "Neutral housing research and fair-housing boundary",
            "fair_text": (
                "This guide does not rank municipalities, institutions, or people and does not "
                "use protected characteristics or demographic proxies to direct a housing choice. "
                "Define your own property and location criteria, then verify address-specific records."
            ),
            "fair_link": "New Jersey fair-housing information",
            "next_heading": "Continue at the right level",
            "county_guide": f"Read the {county} County guide",
            "valuation_link": "Request a property-specific valuation",
            "contact_link": "Ask a source or property question",
            "record_heading": "Sources, dates, and correction policy",
            "record_text": (
                f"The source links and the {district} row on this page were reviewed on {REVIEWED_ON}. "
                "Publishers control their definitions, revisions, and availability."
            ),
            "publisher_label": "Published by The Jorge Ramirez Group.",
            "provenance_text": (
                "Prepared with AI assistance; sources were checked on August 26, 2026."
            ),
            "correction": (
                "To report a source-link, district-label, field-label, or transcription issue, "
                "send the page URL and the source in question through the contact section."
            ),
            "credential_heading": "Verified business information",
            "responsible_contact_label": "Licensed business contact",
            "agent_role": "New Jersey real estate salesperson",
            "license_label": "New Jersey real estate license",
            "office_label": "Office",
            "phone_label": "Direct",
            "email_label": "Email",
            "footer_note": "Source-led real estate research across six New Jersey counties.",
            "breadcrumbs": ("Home", "Research", f"{name} market research"),
        }

    return {
        "title": f"Investigación de {name} 2026 | Datos oficiales 2025",
        "description": (
            f"Investigue {name}, Nueva Jersey, con la fila final 2025 de NJ Treasury "
            f"para {district}, fuentes públicas directas, contexto del condado y método."
        ),
        "llm": (
            f"Guía de investigación de {name}, Nueva Jersey, basada en fuentes. Publica solo "
            f"la fila final 2025 del NJ Treasury para {district}, conserva las cinco etiquetas "
            "de la fuente, enlaza fuentes públicas vigentes y no ofrece pronóstico ni valoración."
        ),
        "skip": "Saltar al contenido principal",
        "nav_label": "Navegación principal",
        "menu": "Menú",
        "home": "Inicio",
        "communities": "Comunidades",
        "county": f"Condado de {county}",
        "research": "Investigación",
        "language": "English",
        "valuation": "Solicitar una valoración",
        "eyebrow": "Investigación municipal con fuentes oficiales",
        "h1": f"Investigación inmobiliaria de {name}: datos públicos verificados de 2025",
        "dek": (
            f"Esta guía usa la fila finalizada de 2025 del New Jersey Treasury para {district}, "
            f"en el condado de {county}. Informa {report['statistics']['# of Sales']} ventas, un precio "
            f"de venta promedio de {report['statistics']['Avg Sales Price']}, un avalúo promedio de "
            f"{report['statistics']['Avg Assessment']} y una factura fiscal promedio de "
            f"{report['statistics']['Avg Tax Bill']}. Son promedios históricos del distrito, no datos "
            "vigentes de listados ni una valoración."
        ),
        "reviewed": "Fuentes revisadas",
        "prepared": "The Jorge Ramirez Group · asistencia de IA, fuentes verificadas",
        "geography_heading": "Empiece por la geografía exacta",
        "geography_lead": report["identityEs"],
        "research_note": report["researchNoteEs"],
        "municipal_link": f"Abrir la fuente de {report['municipalitySource']['publisher']}",
        "census_link": "Abrir la fuente geográfica del Censo",
        "stats_eyebrow": "Fuente anual final",
        "stats_heading": "Registro distrital 2025 del NJ Treasury",
        "stats_lead": (
            "Las cinco etiquetas y valores siguientes reproducen una sola fila pública del "
            "archivo final 2025 Average Residential Statistics del Estado."
        ),
        "district_label": "Distrito del Treasury",
        "code_label": "Código C/D",
        "source_year_label": "Año de la fuente",
        "label_note": (
            "La fuente usa “Avg” para sus campos monetarios de resumen. Esta página conserva "
            "esas etiquetas y no las sustituye por otra medida."
        ),
        "open_2025": "Abrir el PDF final 2025 del Treasury",
        "open_stats": "Abrir la biblioteca estadística del Treasury",
        "current_heading": "Use fuentes vigentes sin inventar valores actuales",
        "current_treasury_title": "Archivo 2026 del Treasury: solo contexto",
        "current_treasury_text": (
            "El Estado enlaza un archivo del año actual, pero al revisarlo no exponía todas "
            "las columnas fiscales y de ventas usadas arriba. Por eso esta página no calcula, "
            "infiere ni publica valores faltantes de 2026."
        ),
        "current_treasury_link": "Revisar el archivo vigente del Treasury",
        "county_title": f"Informes vigentes del condado de {county}",
        "county_text": (
            "New Jersey Realtors ofrece un portal público de informes por condado. Seleccione "
            "condado, período exacto y categoría disponible en la fuente. Un resultado del "
            "condado no es municipal y esta página no copia tablas para miembros."
        ),
        "njr_page": "Leer la página de publicación de NJ Realtors",
        "njr_portal": "Abrir el portal público por condado",
        "method_heading": "Método repetible de investigación",
        "method_steps": (
            "Nombre primero el alcance: condado, municipio legal o distrito fiscal, o propiedad individual.",
            "Anote fuente, etiqueta exacta, año o período, geografía y fecha de consulta.",
            "Compare solo geografías, períodos, categorías y definiciones compatibles.",
            "Para una vivienda, sustituya el contexto amplio por comparables vigentes y datos verificados de la propiedad.",
        ),
        "method_note": (
            "Estos promedios públicos son contexto histórico del distrito. No constituyen precio "
            "de lista, tasación profesional, pronóstico ni predicción de un resultado de transacción."
        ),
        "fair_heading": "Investigación neutral y límite de vivienda justa",
        "fair_text": (
            "Esta guía no clasifica municipios, instituciones ni personas y no usa características "
            "protegidas ni sustitutos demográficos para dirigir una elección de vivienda. Defina "
            "sus propios criterios de propiedad y ubicación, y verifique los registros de cada dirección."
        ),
        "fair_link": "Información de vivienda justa de Nueva Jersey",
        "next_heading": "Continúe en el nivel correcto",
        "county_guide": f"Leer la guía del condado de {county}",
        "valuation_link": "Solicitar una valoración específica",
        "contact_link": "Consultar una fuente o propiedad",
        "record_heading": "Fuentes, fechas y política de correcciones",
        "record_text": (
            f"Los enlaces y la fila {district} de esta página se revisaron el {REVIEWED_ON}. "
            "Cada editor controla sus definiciones, revisiones y disponibilidad."
        ),
        "publisher_label": "Publicado por The Jorge Ramirez Group.",
        "provenance_text": (
            "Elaborado con asistencia de IA; fuentes verificadas el 26 de agosto de 2026."
        ),
        "correction": (
            "Para informar un problema de enlace, distrito, etiqueta o transcripción, envíe "
            "la URL de esta página y la fuente correspondiente desde la sección de contacto."
        ),
        "credential_heading": "Información comercial verificada",
        "responsible_contact_label": "Contacto comercial con licencia",
        "agent_role": "Vendedor de bienes raíces con licencia de Nueva Jersey",
        "license_label": "Licencia inmobiliaria de Nueva Jersey",
        "office_label": "Oficina",
        "phone_label": "Teléfono directo",
        "email_label": "Correo",
        "footer_note": "Investigación inmobiliaria con fuentes en seis condados de Nueva Jersey.",
        "breadcrumbs": ("Inicio", "Investigación", f"Investigación de mercado de {name}"),
    }


def schema_graph(
    report: Mapping[str, Any], copy: Mapping[str, Any], business: Mapping[str, Any], language: str
) -> dict[str, Any]:
    route = report["routes"][language]
    canonical = SITE + route
    prefix = "/es" if language == "es" else ""
    home = f"{SITE}/es/" if language == "es" else f"{SITE}/"
    in_language = "es-US" if language == "es" else "en-US"
    address = business["address"]
    org_id = f"{SITE}/#organization"
    agent_id = f"{SITE}/#jorge-ramirez"
    webpage_id = canonical + "#webpage"
    article_id = canonical + "#article"
    breadcrumb_id = canonical + "#breadcrumbs"
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": org_id,
                "name": business["name"],
                "url": SITE,
                "telephone": business["directPhone"]["e164"],
                "email": business["email"],
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": address["street"],
                    "addressLocality": address["city"],
                    "addressRegion": address["region"],
                    "postalCode": address["postalCode"],
                    "addressCountry": address["country"],
                },
            },
            {
                "@type": "Person",
                "@id": agent_id,
                "name": business["agentName"],
                "url": f"{SITE}{prefix}/ai-authority",
                "telephone": business["directPhone"]["e164"],
                "email": business["email"],
                "jobTitle": copy["agent_role"],
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "New Jersey Real Estate License",
                    "value": business["njRealEstateLicense"],
                },
                "worksFor": {"@id": org_id},
            },
            {
                "@type": "WebPage",
                "@id": webpage_id,
                "url": canonical,
                "name": copy["title"],
                "description": copy["description"],
                "inLanguage": in_language,
                "datePublished": report["publishedOn"],
                "dateModified": PAGE_MODIFIED_ON,
                "breadcrumb": {"@id": breadcrumb_id},
                "isPartOf": {"@id": org_id},
                "publisher": {"@id": org_id},
            },
            {
                "@type": "Article",
                "@id": article_id,
                "headline": copy["title"],
                "description": copy["description"],
                "image": {
                    "@type": "ImageObject",
                    "url": SITE + "/images/hero.jpg",
                    "width": 1400,
                    "height": 933,
                },
                "inLanguage": in_language,
                "datePublished": report["publishedOn"],
                "dateModified": PAGE_MODIFIED_ON,
                "mainEntityOfPage": {"@id": webpage_id},
                "author": {"@id": org_id},
                "publisher": {"@id": org_id},
                "articleSection": "New Jersey town market research",
                "citation": [
                    "https://www.nj.gov/treasury/taxation/pdf/lpt/class4/2025AvgResStat.pdf",
                    report["municipalitySource"]["url"],
                    report["censusSource"]["url"],
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": breadcrumb_id,
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": copy["breadcrumbs"][0],
                        "item": home,
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": copy["breadcrumbs"][1],
                        "item": f"{SITE}{prefix}/blog",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": copy["breadcrumbs"][2],
                        "item": canonical,
                    },
                ],
            },
        ],
    }


def external_link(url: str, label: object, class_name: str = "") -> str:
    css = f' class="{esc(class_name)}"' if class_name else ""
    return (
        f'<a{css} href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
        f"{esc(label)}</a>"
    )


def render_page(
    report: Mapping[str, Any], sources: Mapping[str, Mapping[str, Any]],
    business: Mapping[str, Any], language: str
) -> str:
    copy = page_copy(report, language)
    route = report["routes"][language]
    other_language = "es" if language == "en" else "en"
    other_route = report["routes"][other_language]
    canonical = SITE + route
    en_url = SITE + report["routes"]["en"]
    es_url = SITE + report["routes"]["es"]
    prefix = "/es" if language == "es" else ""
    home_route = "/es/" if language == "es" else "/"
    communities_route = "/es/#communities" if language == "es" else "/#communities"
    contact_route = "/es#contact" if language == "es" else "/#contact"
    in_language = "es-US" if language == "es" else "en-US"
    source_2025 = sources["nj-treasury-average-residential-2025"]
    source_2026 = sources["nj-treasury-average-residential-2026-context"]
    source_stats = sources["nj-treasury-statistics"]
    source_njr = sources["njr-market-data"]
    source_portal = sources["njr-public-county-portal"]
    source_fair = sources["nj-dca-fair-housing"]

    metric_help_en = {
        "# of Line Items": "Residential line items in the published district row",
        "Avg Assessment": "Average assessment, exactly as labeled by the source",
        "Avg Tax Bill": "Average tax bill, exactly as labeled by the source",
        "# of Sales": "Sales count in the published annual row",
        "Avg Sales Price": "Average sales price, exactly as labeled by the source",
    }
    metric_help_es = {
        "# of Line Items": "Partidas residenciales en la fila distrital publicada",
        "Avg Assessment": "Avalúo promedio, con la etiqueta exacta de la fuente",
        "Avg Tax Bill": "Factura fiscal promedio, con la etiqueta exacta de la fuente",
        "# of Sales": "Cantidad de ventas en la fila anual publicada",
        "Avg Sales Price": "Precio de venta promedio, con la etiqueta exacta de la fuente",
    }
    metric_help = metric_help_es if language == "es" else metric_help_en
    metric_cards = "\n".join(
        f'''          <div class="metric-card">
            <p class="metric-label">{esc(label)}</p>
            <p class="metric-value">{esc(value)}</p>
            <p class="metric-help">{esc(metric_help[label])}</p>
          </div>'''
        for label, value in report["statistics"].items()
    )
    method_steps = "\n".join(
        f"          <li>{esc(item)}</li>" for item in copy["method_steps"]
    )
    schema = json.dumps(
        schema_graph(report, copy, business, language), ensure_ascii=False, indent=2
    )
    county_guide = f"{prefix}/counties/{report['countyGuideSlug']}"
    address = business["address"]

    return f'''<!DOCTYPE html>
<html lang="{language}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(copy["title"])}</title>
  <meta name="description" content="{esc(copy["description"])}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta name="ai-content-declaration" content="{AI_DECLARATION}">
  <meta name="llm-context" content="{esc(copy['llm'])}">
  <meta name="last-updated" content="{PAGE_MODIFIED_ON}">
  <meta name="geo.region" content="US-NJ">
  <meta name="geo.placename" content="{esc(report['displayName'])}, New Jersey">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="en-US" href="{en_url}">
  <link rel="alternate" hreflang="es-US" href="{es_url}">
  <link rel="alternate" hreflang="x-default" href="{en_url}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{esc(copy['title'])}">
  <meta property="og:description" content="{esc(copy['description'])}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta property="og:site_name" content="The Jorge Ramirez Group">
  <meta property="article:published_time" content="{esc(report['publishedOn'])}">
  <meta property="article:modified_time" content="{PAGE_MODIFIED_ON}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(copy['title'])}">
  <meta name="twitter:description" content="{esc(copy['description'])}">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" href="/apple-touch-icon.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Playfair+Display:wght@500;600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{window.dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <script type="application/ld+json">{schema}</script>
  <style>
    :root {{
      --dark-bg: #0A0A0A;
      --ink: #1A1A1A;
      --red: #C41230;
      --deep-red: #8B0D22;
      --gold: #B8962E;
      --gold-light: #D4AF5A;
      --ivory: #FAFAF8;
      --soft-ivory: #F8F6F2;
      --white: #FFFFFF;
      --muted: #5D5851;
      --line: #E5DED2;
      --display: 'Playfair Display', Georgia, serif;
      --body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; background: var(--ivory); color: var(--ink); font-family: var(--body); line-height: 1.7; }}
    a {{ color: var(--deep-red); text-underline-offset: .2em; }}
    a:hover {{ color: var(--red); }}
    a:focus-visible, button:focus-visible {{ outline: 3px solid #B8962E; outline-offset: 3px; }}
    .skip-link {{ position: fixed; top: -7rem; left: 1rem; z-index: 100; min-height: 44px; padding: .65rem 1rem; background: #FAFAF8; color: #1A1A1A; font-weight: 700; border-radius: 0 0 8px 8px; }}
    .skip-link:focus, .skip-link:focus-visible {{ top: 0; }}
    .market-nav {{ position: relative; z-index: 20; background: #0A0A0A; border-bottom: 1px solid rgba(184,150,46,.38); }}
    .nav-inner {{ width: min(1280px, calc(100% - 2rem)); min-height: 76px; margin: 0 auto; display: flex; align-items: center; gap: 1rem; }}
    .brand {{ min-height: 44px; flex: 0 0 auto; display: inline-flex; align-items: center; color: #FFFFFF; font-family: var(--display); font-size: clamp(1rem, 2vw, 1.35rem); font-weight: 700; line-height: 1.25; text-decoration: none; white-space: nowrap; }}
    .nav-links {{ margin-left: auto; display: flex; align-items: center; gap: .2rem; }}
    .nav-links a, .menu-button {{ min-height: 44px; display: inline-flex; align-items: center; justify-content: center; padding: .58rem .75rem; border-radius: 999px; color: #FFFFFF; font-size: .88rem; font-weight: 600; text-decoration: none; }}
    .nav-links .nav-cta {{ background: linear-gradient(135deg, #C41230, #8B0D22); padding-inline: 1rem; }}
    .language-link {{ border: 1px solid rgba(255,255,255,.55); }}
    .menu-button {{ display: none; margin-left: auto; border: 1px solid rgba(255,255,255,.5); background: transparent; font: inherit; cursor: pointer; }}
    .research-hero {{ position: relative; overflow: hidden; background: #1A1A1A; color: #FFFFFF; }}
    .research-hero::before {{ content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 82% 18%, rgba(212,175,90,.22), transparent 34%), linear-gradient(125deg, transparent 0 58%, rgba(196,18,48,.16)); pointer-events: none; }}
    .hero-inner {{ position: relative; z-index: 1; width: min(1050px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(4.5rem, 9vw, 8rem) 0 clamp(4rem, 7vw, 6rem); }}
    .eyebrow {{ margin: 0 0 1rem; color: #D4AF5A; font-size: .78rem; font-weight: 700; letter-spacing: .17em; text-transform: uppercase; }}
    h1, h2, h3 {{ font-family: var(--display); line-height: 1.15; }}
    h1 {{ max-width: 920px; margin: 0; font-size: clamp(2.5rem, 7vw, 5.45rem); letter-spacing: -.025em; }}
    .dek {{ max-width: 780px; margin: 1.45rem 0 0; color: rgba(255,255,255,.86); font-size: clamp(1.05rem, 2vw, 1.3rem); }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: .65rem; margin-top: 1.75rem; }}
    .hero-meta span {{ min-height: 44px; display: inline-flex; align-items: center; padding: .55rem .85rem; border: 1px solid rgba(212,175,90,.46); border-radius: 999px; background: rgba(255,255,255,.05); font-size: .82rem; }}
    main {{ display: block; }}
    .content {{ width: min(1050px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(3rem, 7vw, 6rem) 0; }}
    .section {{ margin-bottom: clamp(3.5rem, 8vw, 6.5rem); }}
    .section-heading {{ max-width: 830px; margin: 0 0 1rem; font-size: clamp(2rem, 5vw, 3.35rem); }}
    .lead {{ max-width: 800px; color: var(--muted); font-size: 1.08rem; }}
    .local-note {{ margin: 1.4rem 0 0; padding: 1.1rem 1.2rem; background: #FFFFFF; border: 1px solid var(--line); border-left: 4px solid #B8962E; border-radius: 10px; }}
    .button-row {{ display: flex; flex-wrap: wrap; gap: .8rem; margin-top: 1.4rem; }}
    .button {{ min-height: 48px; display: inline-flex; align-items: center; justify-content: center; padding: .72rem 1.15rem; border: 2px solid #C41230; border-radius: 999px; color: #8B0D22; font-weight: 700; text-decoration: none; }}
    .button.primary {{ border-color: #C41230; background: linear-gradient(135deg, #C41230, #8B0D22) !important; color: #FFFFFF; }}
    .stats-section {{ padding: clamp(1.5rem, 4vw, 2.6rem); background: #F8F6F2; border: 1px solid var(--line); border-top: 5px solid #C41230; border-radius: 16px; }}
    .source-kicker {{ margin: 0 0 .55rem; color: #8B0D22; font-size: .76rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }}
    .district-bar {{ display: flex; flex-wrap: wrap; gap: .7rem; margin: 1.4rem 0; }}
    .district-bar span {{ min-height: 44px; display: inline-flex; align-items: center; padding: .58rem .82rem; border: 1px solid rgba(184,150,46,.48); border-radius: 999px; background: #FFFFFF; font-size: .85rem; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .8rem; margin: 1.5rem 0; }}
    .metric-card {{ min-width: 0; padding: 1.15rem; background: #FFFFFF; border: 1px solid var(--line); border-radius: 10px; box-shadow: 0 12px 34px rgba(26,26,26,.045); }}
    .metric-label {{ margin: 0; color: #8B0D22; font-size: .75rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }}
    .metric-value {{ margin: .52rem 0 .4rem; color: #1A1A1A; font-family: var(--display); font-size: clamp(1.4rem, 2.3vw, 2.05rem); font-weight: 700; line-height: 1.05; overflow-wrap: anywhere; }}
    .metric-help {{ margin: 0; color: var(--muted); font-size: .8rem; line-height: 1.45; }}
    .label-note {{ margin: 1.2rem 0 0; padding: 1rem 1.1rem; background: #FFFFFF; border-left: 4px solid #B8962E; }}
    .source-grid, .next-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 1.6rem; }}
    .source-card, .next-card {{ padding: 1.45rem; background: #FFFFFF; border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 14px 40px rgba(26,26,26,.045); }}
    .source-card {{ display: flex; flex-direction: column; border-top: 4px solid #B8962E; }}
    .source-card h3 {{ margin: 0 0 .65rem; font-size: 1.42rem; }}
    .source-card p {{ margin: 0; color: var(--muted); }}
    .source-links {{ margin-top: auto; padding-top: 1rem; display: grid; gap: .3rem; }}
    .source-links a {{ min-height: 44px; display: flex; align-items: center; font-weight: 700; }}
    .method {{ padding: clamp(1.6rem, 4vw, 2.6rem); background: #0A0A0A; color: #FFFFFF; border-radius: 16px; box-shadow: inset 0 0 0 1px rgba(184,150,46,.28); }}
    .method .section-heading {{ color: #FFFFFF; }}
    .method ol {{ margin: 1.4rem 0; padding-left: 1.45rem; }}
    .method li {{ padding: .4rem 0 .4rem .35rem; }}
    .method-note {{ margin: 1.25rem 0 0; padding: 1rem 1.1rem; background: rgba(184,150,46,.13); border: 1px solid rgba(212,175,90,.36); border-radius: 10px; }}
    .fair-note {{ padding: clamp(1.4rem, 4vw, 2.2rem); background: #FFFFFF; border: 1px solid var(--line); border-left: 5px solid #8B0D22; border-radius: 12px; }}
    .fair-note h2 {{ margin-top: 0; font-size: clamp(1.65rem, 4vw, 2.35rem); }}
    .fair-note a {{ min-height: 44px; display: inline-flex; align-items: center; font-weight: 700; }}
    .next-card {{ min-height: 112px; display: flex; align-items: center; }}
    .next-card a {{ min-height: 44px; display: inline-flex; align-items: center; font-weight: 700; }}
    .record {{ padding: 1.4rem; background: #FFFFFF; border: 1px solid var(--line); border-left: 4px solid #C41230; border-radius: 10px; }}
    .record h2 {{ margin-top: 0; font-size: 1.65rem; }}
    .record p:last-child {{ margin-bottom: 0; }}
    .credential {{ margin-top: 1rem; padding: 1.35rem; background: #1A1A1A; color: rgba(255,255,255,.82); border-radius: 10px; }}
    .credential h2 {{ margin: 0 0 .8rem; color: #FFFFFF; font-size: 1.5rem; }}
    .credential-list {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .5rem 1rem; margin: 0; }}
    .credential-list div {{ min-width: 0; }}
    .credential-list dt {{ color: #D4AF5A; font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
    .credential-list dd {{ margin: .18rem 0 0; overflow-wrap: anywhere; }}
    .credential a {{ min-height: 44px; display: inline-flex; align-items: center; color: #FFFFFF; }}
    footer {{ background: #0A0A0A; color: rgba(255,255,255,.78); }}
    .footer-inner {{ width: min(1050px, calc(100% - 2rem)); margin: 0 auto; padding: 2.5rem 0; display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }}
    .footer-inner strong {{ color: #FFFFFF; font-family: var(--display); }}
    .footer-inner p {{ margin: .35rem 0 0; }}
    .footer-inner a {{ min-height: 44px; display: inline-flex; align-items: center; color: #FFFFFF; }}
    @media (max-width: 980px) {{ .metric-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
    @media (max-width: 820px) {{
      .menu-button {{ display: inline-flex; }}
      .nav-links {{ display: none; position: absolute; top: 76px; left: 0; right: 0; margin: 0; padding: .8rem 1rem 1.1rem; flex-direction: column; align-items: stretch; background: #0A0A0A; border-top: 1px solid rgba(184,150,46,.35); }}
      .nav-links.open {{ display: flex; }}
      .nav-links a {{ width: 100%; }}
      .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 560px) {{
      .brand {{ max-width: 230px; }}
      .hero-inner, .content {{ width: min(100% - 1.25rem, 1050px); }}
      .source-grid, .next-grid, .metric-grid, .credential-list {{ grid-template-columns: 1fr; }}
      .button-row {{ flex-direction: column; }}
      .button {{ width: 100%; text-align: center; }}
      .metric-value {{ overflow-wrap: normal; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">{esc(copy['skip'])}</a>
  <nav class="market-nav" aria-label="{esc(copy['nav_label'])}">
    <div class="nav-inner">
      <a class="brand" href="{home_route}">The Jorge Ramirez Group</a>
      <button class="menu-button" type="button" aria-expanded="false" aria-controls="primary-links">{esc(copy['menu'])}</button>
      <div class="nav-links" id="primary-links">
        <a href="{home_route}">{esc(copy['home'])}</a>
        <a href="{communities_route}">{esc(copy['communities'])}</a>
        <a href="{county_guide}">{esc(copy['county'])}</a>
        <a href="{prefix}/blog">{esc(copy['research'])}</a>
        <a class="language-link" href="{other_route}" lang="{other_language}">{esc(copy['language'])}</a>
        <a class="nav-cta" href="{prefix}/home-valuation">{esc(copy['valuation'])}</a>
      </div>
    </div>
  </nav>

  <main id="main" tabindex="-1">
    <article data-market-research-batch="essex-middlesex-somerset" data-publication-policy="official-sources-no-gated-tables">
      <header class="research-hero">
        <div class="hero-inner">
          <p class="eyebrow">{esc(copy['eyebrow'])}</p>
          <h1>{esc(copy['h1'])}</h1>
          <p class="dek" data-direct-answer="finalized-2025-treasury-row">{esc(copy['dek'])}</p>
          <div class="hero-meta">
            <span>{esc(copy['reviewed'])}:&nbsp;<time datetime="{REVIEWED_ON}">{REVIEWED_ON}</time></span>
            <span>{esc(copy['prepared'])}</span>
            <span>{esc(copy['district_label'])}: {esc(report['treasuryDistrict'])}</span>
          </div>
        </div>
      </header>

      <div class="content">
        <section class="section" aria-labelledby="geography-heading">
          <h2 class="section-heading" id="geography-heading">{esc(copy['geography_heading'])}</h2>
          <p class="lead">{esc(copy['geography_lead'])}</p>
          <p class="local-note">{esc(copy['research_note'])}</p>
          <div class="button-row">
            {external_link(report['municipalitySource']['url'], copy['municipal_link'], 'button primary')}
            {external_link(report['censusSource']['url'], copy['census_link'], 'button')}
          </div>
        </section>

        <section class="section stats-section" aria-labelledby="statistics-heading">
          <p class="source-kicker">{esc(copy['stats_eyebrow'])}</p>
          <h2 class="section-heading" id="statistics-heading">{esc(copy['stats_heading'])}</h2>
          <p class="lead">{esc(copy['stats_lead'])}</p>
          <div class="district-bar">
            <span><strong>{esc(copy['district_label'])}:</strong>&nbsp; {esc(report['treasuryDistrict'])}</span>
            <span><strong>{esc(copy['code_label'])}:</strong>&nbsp; {esc(report['treasuryCode'])}</span>
            <span><strong>{esc(copy['source_year_label'])}:</strong>&nbsp; {esc(report['statisticsYear'])}</span>
          </div>
          <div class="metric-grid">
{metric_cards}
          </div>
          <p class="label-note">{esc(copy['label_note'])}</p>
          <div class="button-row">
            {external_link(source_2025['url'], copy['open_2025'], 'button primary')}
            {external_link(source_stats['url'], copy['open_stats'], 'button')}
          </div>
        </section>

        <section class="section" aria-labelledby="current-source-heading">
          <h2 class="section-heading" id="current-source-heading">{esc(copy['current_heading'])}</h2>
          <div class="source-grid">
            <div class="source-card">
              <h3>{esc(copy['current_treasury_title'])}</h3>
              <p>{esc(copy['current_treasury_text'])}</p>
              <div class="source-links">{external_link(source_2026['url'], copy['current_treasury_link'])}</div>
            </div>
            <div class="source-card">
              <h3>{esc(copy['county_title'])}</h3>
              <p>{esc(copy['county_text'])}</p>
              <div class="source-links">
                {external_link(source_njr['url'], copy['njr_page'])}
                {external_link(source_portal['url'], copy['njr_portal'])}
              </div>
            </div>
          </div>
        </section>

        <section class="section method" aria-labelledby="method-heading">
          <h2 class="section-heading" id="method-heading">{esc(copy['method_heading'])}</h2>
          <ol>
{method_steps}
          </ol>
          <p class="method-note">{esc(copy['method_note'])}</p>
        </section>

        <aside class="section fair-note" aria-labelledby="fair-heading">
          <h2 id="fair-heading">{esc(copy['fair_heading'])}</h2>
          <p>{esc(copy['fair_text'])}</p>
          {external_link(source_fair['url'], copy['fair_link'])}
        </aside>

        <section class="section" aria-labelledby="next-heading">
          <h2 class="section-heading" id="next-heading">{esc(copy['next_heading'])}</h2>
          <div class="next-grid">
            <div class="next-card"><a href="{county_guide}">{esc(copy['county_guide'])}</a></div>
            <div class="next-card"><a href="{prefix}/home-valuation">{esc(copy['valuation_link'])}</a></div>
            <div class="next-card"><a href="{contact_route}">{esc(copy['contact_link'])}</a></div>
          </div>
        </section>

        <aside class="record" data-content-provenance="v1" aria-labelledby="record-heading">
          <h2 id="record-heading">{esc(copy['record_heading'])}</h2>
          <p><strong>{esc(copy['publisher_label'])}</strong> {esc(copy['provenance_text'])}</p>
          <p>{esc(copy['record_text'])}</p>
          <p>{esc(copy['correction'])}</p>
        </aside>

        <aside class="credential" aria-labelledby="credential-heading">
          <h2 id="credential-heading">{esc(copy['credential_heading'])}</h2>
          <dl class="credential-list">
            <div><dt>{esc(copy['responsible_contact_label'])}</dt><dd>{esc(business['agentName'])}<br>{esc(copy['agent_role'])}</dd></div>
            <div><dt>{esc(copy['license_label'])}</dt><dd>#{esc(business['njRealEstateLicense'])}</dd></div>
            <div><dt>{esc(copy['office_label'])}</dt><dd>{esc(business['brokerage']['displayName'])}<br>{esc(address['street'])}, {esc(address['city'])}, {esc(address['region'])} {esc(address['postalCode'])}</dd></div>
            <div><dt>{esc(copy['phone_label'])}</dt><dd><a href="tel:{esc(business['directPhone']['e164'])}">{esc(business['directPhone']['display'])}</a></dd></div>
            <div><dt>{esc(copy['email_label'])}</dt><dd><a href="mailto:{esc(business['email'])}">{esc(business['email'])}</a></dd></div>
          </dl>
        </aside>
      </div>
    </article>
  </main>

  <footer>
    <div class="footer-inner">
      <div><strong>The Jorge Ramirez Group · {esc(business['brokerage']['displayName'])}</strong><p>{esc(copy['footer_note'])}</p></div>
      <a href="{contact_route}">{esc(copy['contact_link'])}</a>
    </div>
  </footer>
  <script>
    (() => {{
      const button = document.querySelector('.menu-button');
      const links = document.querySelector('#primary-links');
      if (!button || !links) return;
      const close = () => {{ links.classList.remove('open'); button.setAttribute('aria-expanded', 'false'); }};
      button.addEventListener('click', () => {{
        const open = links.classList.toggle('open');
        button.setAttribute('aria-expanded', String(open));
      }});
      links.addEventListener('click', (event) => {{ if (event.target.closest('a')) close(); }});
      document.addEventListener('keydown', (event) => {{ if (event.key === 'Escape') close(); }});
    }})();
  </script>
  <script src="/js/site-cta.js" defer></script>
</body>
</html>
'''


def targets(
    document: Mapping[str, Any], business: Mapping[str, Any]
) -> list[tuple[Path, str]]:
    sources = {item["id"]: item for item in document["sharedSources"]}
    result: list[tuple[Path, str]] = []
    for report in sorted(document["reports"], key=lambda item: item["slug"]):
        for language in ("en", "es"):
            relative = Path(report["routes"][language].lstrip("/") + ".html")
            expected_parent = Path("blog") if language == "en" else Path("es/blog")
            expected_name = f"market-report-{report['slug']}-nj-2026.html"
            if relative.parent != expected_parent or relative.name != expected_name:
                raise ValueError(f"refusing unexpected output path: {relative}")
            result.append(
                (ROOT / relative, render_page(report, sources, business, language))
            )
    if len(result) != 22 or len({path for path, _ in result}) != 22:
        raise ValueError("renderer target inventory must contain exactly 22 unique files")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail when a managed page is stale")
    mode.add_argument("--write", action="store_true", help="write stale managed pages")
    args = parser.parse_args()

    try:
        rendered = targets(load_manifest(), load_site_facts())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"Town market research manifest error: {error}", file=sys.stderr)
        return 2

    stale = [
        path
        for path, content in rendered
        if not path.exists() or path.read_text(encoding="utf-8") != content
    ]
    if args.check:
        if stale:
            print("Stale town market research pages:")
            for path in stale:
                print(f"- {path.relative_to(ROOT)}")
            return 1
        print("22 town market research pages are current.")
        return 0

    for path, content in rendered:
        if path in stale:
            path.write_text(content, encoding="utf-8")
    print(f"Updated {len(stale)} of 22 town market research pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
