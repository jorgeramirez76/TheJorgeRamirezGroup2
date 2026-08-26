#!/usr/bin/env python3
"""Render the reviewed bilingual county market-research pages.

This renderer is intentionally narrow. It reads a dated provenance manifest and
writes only the ten approved county routes. It never stores or publishes copied
market tables, hardcoded listing-service values, or forward-looking claims.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "county-market-report-sources-2026-08-26.json"
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
EXPECTED_SLUGS = {
    "essex-county-nj-real-estate-market-2026",
    "morris-county-nj-real-estate-market-2026",
    "hudson-county-real-estate-market-q2-2026",
    "middlesex-county-real-estate-market-q2-2026",
    "union-county-nj-real-estate-market-report-2026",
}
EXPECTED_SOURCE_IDS = {
    "njr-market-data",
    "njr-public-county-portal",
    "nj-treasury-property-tax-statistics",
    "nj-treasury-average-residential-2025",
    "nj-treasury-equalization-tables",
    "nj-dca-construction-reporter",
    "census-acs-data-profiles",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_manifest() -> dict:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1:
        raise ValueError("county source manifest schemaVersion must be 1")
    if document.get("reviewedOn") != REVIEWED_ON:
        raise ValueError(f"county sources must be reviewed on {REVIEWED_ON}")
    if document.get("renderer") != "tools/generate_county_market_research.py":
        raise ValueError("county source manifest points to another renderer")

    reports = document.get("reports", [])
    if {item.get("slug") for item in reports} != EXPECTED_SLUGS:
        raise ValueError("county source manifest must contain the exact approved reports")
    source_ids = {item.get("id") for item in document.get("sharedSources", [])}
    if source_ids != EXPECTED_SOURCE_IDS:
        raise ValueError("county source manifest must contain the exact reviewed sources")

    for source in document["sharedSources"]:
        if source.get("accessedOn") != REVIEWED_ON:
            raise ValueError(f"source {source.get('id')} lacks the reviewed access date")
        if not str(source.get("url", "")).startswith("https://"):
            raise ValueError(f"source {source.get('id')} is not an HTTPS primary source")
    for report in reports:
        if report.get("countyDirectory", {}).get("accessedOn") != REVIEWED_ON:
            raise ValueError(f"report {report.get('slug')} has an unreviewed directory")
        expected_routes = {
            "en": f"/blog/{report['slug']}",
            "es": f"/es/blog/{report['slug']}",
        }
        if report.get("routes") != expected_routes:
            raise ValueError(f"report {report.get('slug')} changed its canonical routes")
    return document


def page_copy(report: dict, language: str) -> dict[str, object]:
    county = report["county"]
    q2 = report["periodLabel"].startswith("Q2")
    if language == "en":
        period_short = "Q2 2026" if q2 else "2026"
        title = (
            f"{county} County Real Estate Market Q2 2026 | Research"
            if q2
            else f"{county} County NJ Real Estate Market 2026 | Research Guide"
        )
        description = (
            f"Official-source guide to the {county} County real estate market in {period_short}, "
            "with clear county, municipality, and property-level boundaries."
        )
        return {
            "title": title,
            "description": description,
            "lang_label": "Español",
            "skip": "Skip to main content",
            "nav_label": "Primary navigation",
            "menu": "Menu",
            "home": "Home",
            "counties": "County guides",
            "blog": "Research",
            "contact": "Contact",
            "nav_cta": "Request a home valuation",
            "eyebrow": "Official-source county research",
            "h1": f"{county} County real estate market: {period_short} research guide",
            "dek": (
                f"A repeatable way to research the {county} County market at its original sources—"
                "without freezing a changing report into an undated claim."
            ),
            "reviewed": "Sources reviewed",
            "byline": "Prepared by Jorge Ramirez",
            "start": "Start with the current county report",
            "start_intro": (
                "New Jersey Realtors provides a public path to state and county reports. "
                "Use the source controls so the county, reporting period, and available property category are explicit."
            ),
            "q2_note": (
                "For this Q2 research route, choose a Q2 or year-to-date option only when the portal offers that exact label; "
                "record the label you actually selected."
                if q2
                else "For a 2026 review, record the exact month, year-to-date range, or other period displayed by the source."
            ),
            "steps": (
                "Open the New Jersey Realtors market-data page.",
                "Follow its link to the direct public county-report portal.",
                f"Select {county} County, then the exact period and available property category.",
                "Keep the source's metric labels and period together in your notes; do not combine unlike periods.",
            ),
            "njr_page": "New Jersey Realtors market-data page",
            "portal": "Open the public county-report portal",
            "publication_note": (
                "We link directly to the public source. We do not reproduce its report tables, "
                "and no affiliation or endorsement is implied."
            ),
            "scope": "Three different questions require three different scopes",
            "county_label": "County",
            "county_text": (
                f"A {county} County result is a county-level reference. A county result does not describe every municipality."
            ),
            "municipality_label": "Municipality",
            "municipality_text": (
                "Use official county or municipal records for the legal municipality. County labels, municipality names, "
                "mailing names, and ZIP labels are not interchangeable."
            ),
            "property_label": "Property",
            "property_text": (
                "A property-specific CMA needs current comparable properties plus the subject property's condition, "
                "features, location, and timing. County context is not a property valuation."
            ),
            "sources_heading": "Use each source for the question it can answer",
            "source_intro": (
                "These links supply different kinds of evidence. Read the geography, period, field label, and source notes before comparing anything."
            ),
            "njr_title": "Public State and County Reports",
            "njr_text": (
                "Current county report selection at the source. Confirm the county, period, and property category every time you open it."
            ),
            "treasury_title": "2025 Average Residential Statistics",
            "treasury_text": (
                "The official table uses these labels: # of Line Items, Avg Assessment, Avg Tax Bill, # of Sales, and Avg Sales Price. "
                "An average is not a median. District rows are not one countywide value and are not a current CMA."
            ),
            "tax_stats": "Property Tax Statistics landing page",
            "avg_pdf": "Open the 2025 official PDF",
            "equal_title": "County Equalization Tables",
            "equal_text": (
                "Use equalization material in its property-tax administration context. It is not a listing price or appraisal."
            ),
            "dca_title": "New Jersey DCA Construction Reporter",
            "dca_text": (
                "Building-permit and certificate activity reported by local officials can add development context. "
                "It is not a count of current homes for sale or a statement about future results."
            ),
            "acs_title": "Census ACS housing profile DP04",
            "acs_text": (
                "Use the 2024 ACS five-year Selected Housing Characteristics profile for county context. "
                "ACS values are survey estimates for the named release, not current transactions or appraisals."
            ),
            "acs_docs": "How ACS Data Profiles work",
            "acs_profile": f"Open the {county} County DP04 profile",
            "official_title": f"{county} County official directory",
            "official_text": (
                "Use the county's official site to verify municipality names and find the appropriate local office or record source."
            ),
            "method_heading": "A defensible comparison workflow",
            "method_items": (
                "Name the geography first: county, legal municipality, or individual property.",
                "Record the source, release, selected period, property category, and access date.",
                "Compare only identical metric labels and compatible periods; keep averages distinct from medians.",
                "Return to the original source before making a decision because public reports can be revised or replaced.",
            ),
            "method_note": (
                "This page is a source map and research method. It does not publish a copied market table, municipality ranking, or property valuation."
            ),
            "next_heading": "Continue at the right level",
            "county_cta": f"Read the {county} County guide",
            "value_cta": "Request a property-specific valuation",
            "sell_cta": "Review the home-selling process",
            "contact_cta": "Ask a county or property question",
            "record_heading": "Sources, access date, and corrections",
            "record_text": (
                f"All source links on this {county} County guide were reviewed on {REVIEWED_ON}. "
                "The source publisher controls its definitions, release schedule, availability, and revisions."
            ),
            "correction": (
                "Correction note: If a source link, source label, period, or geography statement needs attention, "
                "send the page URL and the source in question through the contact page."
            ),
            "footer_text": "The Jorge Ramirez Group · Keller Williams Premier Properties",
            "footer_note": "County research links and property-specific guidance in New Jersey.",
            "breadcrumbs": ("Home", "Research", f"{county} County market research"),
        }

    period_short = "Q2 de 2026" if q2 else "2026"
    title = (
        f"Mercado inmobiliario del condado de {county}: Q2 2026"
        if q2
        else f"Mercado inmobiliario del condado de {county} 2026 | Fuentes"
    )
    description = (
        f"Guía de fuentes oficiales para investigar el mercado inmobiliario del condado de {county} en {period_short}, "
        "con límites claros por condado, municipio y propiedad."
    )
    return {
        "title": title,
        "description": description,
        "lang_label": "English",
        "skip": "Saltar al contenido principal",
        "nav_label": "Navegación principal",
        "menu": "Menú",
        "home": "Inicio",
        "counties": "Guías por condado",
        "blog": "Investigación",
        "contact": "Contacto",
        "nav_cta": "Solicitar una valoración",
        "eyebrow": "Investigación del condado con fuentes oficiales",
        "h1": f"Mercado inmobiliario del condado de {county}: guía de investigación {period_short}",
        "dek": (
            f"Un método repetible para investigar el mercado del condado de {county} en sus fuentes originales, "
            "sin convertir un informe cambiante en una afirmación sin fecha."
        ),
        "reviewed": "Fuentes revisadas",
        "byline": "Preparado por Jorge Ramirez",
        "start": "Comience con el informe vigente del condado",
        "start_intro": (
            "New Jersey Realtors ofrece una ruta pública a informes estatales y de condado. "
            "Use los controles de la fuente para identificar el condado, el período y la categoría de propiedad disponible."
        ),
        "q2_note": (
            "Para esta ruta de Q2, elija una opción de Q2 o del año hasta la fecha solo si el portal muestra esa etiqueta exacta; "
            "anote la etiqueta que seleccionó."
            if q2
            else "Para una revisión de 2026, anote el mes, el período del año hasta la fecha u otra fecha exacta que muestre la fuente."
        ),
        "steps": (
            "Abra la página de datos de mercado de New Jersey Realtors.",
            "Siga su enlace al portal público directo de informes por condado.",
            f"Seleccione el condado de {county}, el período exacto y la categoría de propiedad disponible.",
            "Mantenga juntas en sus notas las etiquetas y el período de la fuente; no combine períodos distintos.",
        ),
        "njr_page": "Página de datos de mercado de New Jersey Realtors",
        "portal": "Abrir el portal público de informes por condado",
        "publication_note": (
            "Enlazamos directamente a la fuente pública. Este sitio no reproduce sus tablas "
            "y no implica afiliación ni respaldo."
        ),
        "scope": "Tres preguntas distintas requieren tres escalas distintas",
        "county_label": "Condado",
        "county_text": (
            f"Un resultado del condado de {county} sirve como referencia del condado. Un dato del condado no describe cada municipio."
        ),
        "municipality_label": "Municipio",
        "municipality_text": (
            "Use registros oficiales del condado o municipio para confirmar el municipio legal. El condado, el municipio, "
            "el nombre postal y el código postal no son equivalentes."
        ),
        "property_label": "Propiedad",
        "property_text": (
            "Un CMA específico para una propiedad requiere comparables vigentes y detalles sobre condición, características, "
            "ubicación y fecha. El contexto del condado no es una valoración de la propiedad."
        ),
        "sources_heading": "Use cada fuente para la pregunta que puede responder",
        "source_intro": (
            "Estos enlaces aportan tipos de evidencia distintos. Revise la geografía, el período, la etiqueta y las notas de la fuente antes de comparar."
        ),
        "njr_title": "Informes públicos estatales y por condado",
        "njr_text": (
            "Selección de informes vigentes por condado en la fuente. Confirme el condado, el período y la categoría de propiedad cada vez."
        ),
        "treasury_title": "2025 Average Residential Statistics",
        "treasury_text": (
            "La tabla oficial usa estas etiquetas: # of Line Items, Avg Assessment, Avg Tax Bill, # of Sales y Avg Sales Price. "
            "Un promedio no es una mediana. Las filas de distritos no forman un único dato del condado ni un CMA vigente."
        ),
        "tax_stats": "Página de estadísticas del impuesto a la propiedad",
        "avg_pdf": "Abrir el PDF oficial de 2025",
        "equal_title": "Tablas de igualación por condado",
        "equal_text": (
                "Use el material de igualación dentro de su contexto de administración tributaria. No es un precio de lista ni una tasación."
        ),
        "dca_title": "Construction Reporter del DCA de Nueva Jersey",
        "dca_text": (
            "La actividad de permisos y certificados informada por autoridades locales añade contexto sobre construcción. "
            "No representa la oferta vigente de viviendas ni resultados futuros."
        ),
        "acs_title": "Perfil de vivienda DP04 de la ACS del Censo",
        "acs_text": (
            "Use el perfil de cinco años 2024 Selected Housing Characteristics como contexto del condado. "
            "Los datos de la ACS son estimaciones de encuesta para esa publicación, no transacciones ni tasaciones vigentes."
        ),
        "acs_docs": "Cómo funcionan los Data Profiles de la ACS",
        "acs_profile": f"Abrir el perfil DP04 del condado de {county}",
        "official_title": f"Directorio oficial del condado de {county}",
        "official_text": (
            "Use el sitio oficial del condado para confirmar nombres de municipios y encontrar la oficina o registro local correspondiente."
        ),
        "method_heading": "Método de comparación verificable",
        "method_items": (
            "Defina primero la geografía: condado, municipio legal o propiedad individual.",
            "Anote la fuente, la publicación, el período, la categoría de propiedad y la fecha de consulta.",
            "Compare solo etiquetas idénticas y períodos compatibles; mantenga separados promedios y medianas.",
            "Vuelva a la fuente original antes de decidir, porque los informes públicos pueden revisarse o reemplazarse.",
        ),
        "method_note": (
            "Esta página es un mapa de fuentes y un método de investigación. No publica tablas copiadas, clasificaciones de municipios ni una valoración."
        ),
        "next_heading": "Continúe en la escala correcta",
        "county_cta": f"Leer la guía del condado de {county}",
        "value_cta": "Solicitar una valoración específica",
        "sell_cta": "Revisar el proceso de venta",
        "contact_cta": "Hacer una pregunta sobre el condado o la propiedad",
        "record_heading": "Fuentes, fecha de consulta y correcciones",
        "record_text": (
            f"Todos los enlaces de esta guía del condado de {county} se revisaron el {REVIEWED_ON}. "
            "Cada entidad fuente controla sus definiciones, calendario, disponibilidad y revisiones."
        ),
        "correction": (
            "Correcciones: Si un enlace, una etiqueta, un período o una explicación geográfica requiere atención, "
            "envíe la URL de esta página y la fuente correspondiente mediante la página de contacto."
        ),
        "footer_text": "The Jorge Ramirez Group · Keller Williams Premier Properties",
        "footer_note": "Fuentes por condado y orientación específica para propiedades en Nueva Jersey.",
        "breadcrumbs": ("Inicio", "Investigación", f"Mercado del condado de {county}"),
    }


def render_page(report: dict, sources: dict[str, dict], language: str) -> str:
    copy = page_copy(report, language)
    county = report["county"]
    county_slug = county.lower()
    route = report["routes"][language]
    other_language = "es" if language == "en" else "en"
    other_route = report["routes"][other_language]
    canonical = SITE + route
    en_url = SITE + report["routes"]["en"]
    es_url = SITE + report["routes"]["es"]
    prefix = "/es" if language == "es" else ""
    html_lang = "es" if language == "es" else "en"
    in_language = "es-US" if language == "es" else "en-US"
    directory = report["countyDirectory"]

    article_schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": copy["title"],
        "description": copy["description"],
        "url": canonical,
        "mainEntityOfPage": canonical,
        "inLanguage": in_language,
        "datePublished": report["publishedOn"],
        "dateModified": REVIEWED_ON,
        "author": {
            "@type": "Person",
            "@id": f"{SITE}/#agent",
            "name": "Jorge Ramirez",
            "url": f"{SITE}{prefix}/ai-authority",
        },
        "publisher": {
            "@type": "Organization",
            "name": "The Jorge Ramirez Group at Keller Williams Premier Properties",
            "url": SITE,
        },
        "articleSection": "County market research",
    }
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": copy["breadcrumbs"][0],
                "item": f"{SITE}{prefix or '/'}",
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
    }

    steps = "\n".join(f"              <li>{esc(item)}</li>" for item in copy["steps"])
    method_items = "\n".join(
        f"              <li>{esc(item)}</li>" for item in copy["method_items"]
    )
    article_json = json.dumps(article_schema, ensure_ascii=False, indent=2)
    breadcrumb_json = json.dumps(breadcrumb_schema, ensure_ascii=False, indent=2)

    return f'''<!DOCTYPE html>
<html lang="{html_lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(copy["title"])}</title>
  <meta name="description" content="{esc(copy["description"])}">
  <meta name="author" content="Jorge Ramirez">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="llm-context" content="Official-source research guide for the {esc(county)} County, New Jersey real estate market. It distinguishes county reports, municipality records, and a property-specific CMA; no copied market tables or forward-looking claims are published.">
  <meta name="last-updated" content="{REVIEWED_ON}">
  <meta name="geo.region" content="US-NJ">
  <meta name="geo.placename" content="{esc(county)} County, New Jersey">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="en-US" href="{en_url}">
  <link rel="alternate" hreflang="es-US" href="{es_url}">
  <link rel="alternate" hreflang="es" href="{es_url}">
  <link rel="alternate" hreflang="x-default" href="{en_url}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{esc(copy["title"])}">
  <meta property="og:description" content="{esc(copy["description"])}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta property="og:site_name" content="The Jorge Ramirez Group">
  <meta property="article:published_time" content="{esc(report["publishedOn"])}">
  <meta property="article:modified_time" content="{REVIEWED_ON}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(copy["title"])}">
  <meta name="twitter:description" content="{esc(copy["description"])}">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" href="/apple-touch-icon.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <script type="application/ld+json">{article_json}</script>
  <script type="application/ld+json">{breadcrumb_json}</script>
  <style>
    :root {{
      --ink: #1A1A1A;
      --red: #C41230;
      --deep-red: #8B0D22;
      --gold: #B8962E;
      --ivory: #FAFAF8;
      --white: #FFFFFF;
      --muted: #5E5A54;
      --line: #E6E0D5;
      --display: 'Playfair Display', Georgia, serif;
      --body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; background: var(--ivory); color: var(--ink); font-family: var(--body); line-height: 1.7; }}
    a {{ color: var(--deep-red); text-underline-offset: .18em; }}
    a:hover {{ color: var(--red); }}
    a:focus-visible, button:focus-visible {{ outline: 3px solid #B8962E; outline-offset: 3px; }}
    .skip-link {{ position: fixed; left: 1rem; top: -6rem; z-index: 100; padding: .65rem 1rem; background: #FAFAF8; color: #1A1A1A; font-weight: 700; border-radius: 0 0 8px 8px; }}
    .skip-link:focus, .skip-link:focus-visible {{ top: 0 !important; left: 1rem !important; }}
    .site-nav {{ position: relative; z-index: 20; background: #1A1A1A; border-bottom: 1px solid rgba(184,150,46,.35); }}
    .nav-inner {{ width: min(1180px, calc(100% - 2rem)); min-height: 76px; margin: 0 auto; display: flex; align-items: center; gap: 1.25rem; }}
    .brand {{ color: var(--white); font-family: var(--display); font-size: clamp(1rem, 2vw, 1.35rem); font-weight: 700; text-decoration: none; }}
    .nav-links {{ margin-left: auto; display: flex; align-items: center; gap: .25rem; }}
    .nav-links a, .menu-button {{ min-height: 44px; display: inline-flex; align-items: center; justify-content: center; padding: .6rem .8rem; border-radius: 999px; color: var(--white); font-size: .9rem; font-weight: 600; text-decoration: none; }}
    .nav-links .nav-cta {{ background: linear-gradient(135deg, #C41230, #8B0D22); padding-inline: 1rem; }}
    .lang-link {{ border: 1px solid rgba(255,255,255,.5); }}
    .menu-button {{ display: none; margin-left: auto; border: 1px solid rgba(255,255,255,.45); background: transparent; font: inherit; cursor: pointer; }}
    .hero {{ position: relative; overflow: hidden; background: #1A1A1A; color: var(--white); }}
    .hero::after {{ content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 84% 18%, rgba(184,150,46,.22), transparent 34%), linear-gradient(125deg, transparent 0 60%, rgba(196,18,48,.14)); pointer-events: none; }}
    .hero-inner {{ position: relative; z-index: 1; width: min(1050px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(4.5rem, 9vw, 8rem) 0 clamp(4rem, 7vw, 6rem); }}
    .eyebrow {{ margin: 0 0 1rem; color: #B8962E; font-size: .78rem; font-weight: 700; letter-spacing: .17em; text-transform: uppercase; }}
    h1, h2, h3 {{ font-family: var(--display); line-height: 1.15; }}
    h1 {{ max-width: 900px; margin: 0; font-size: clamp(2.45rem, 7vw, 5.5rem); letter-spacing: -.025em; }}
    .dek {{ max-width: 760px; margin: 1.5rem 0 0; color: rgba(255,255,255,.85); font-size: clamp(1.05rem, 2vw, 1.3rem); }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: .65rem; margin-top: 1.75rem; }}
    .hero-meta span {{ min-height: 44px; display: inline-flex; align-items: center; padding: .55rem .85rem; border: 1px solid rgba(184,150,46,.45); border-radius: 999px; background: rgba(255,255,255,.05); font-size: .82rem; }}
    main {{ display: block; }}
    .content {{ width: min(1050px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(3rem, 7vw, 6rem) 0; }}
    .section {{ margin-bottom: clamp(3.5rem, 8vw, 6.5rem); }}
    .section > h2 {{ max-width: 790px; margin: 0 0 1rem; font-size: clamp(2rem, 5vw, 3.35rem); }}
    .lead {{ max-width: 780px; color: var(--muted); font-size: 1.08rem; }}
    .workflow {{ margin: 1.75rem 0; padding: 1.6rem 1.6rem 1.6rem 3.2rem; background: var(--white); border: 1px solid var(--line); border-top: 4px solid #B8962E; border-radius: 12px; box-shadow: 0 18px 50px rgba(26,26,26,.06); }}
    .workflow li {{ padding: .3rem 0 .3rem .35rem; }}
    .button-row {{ display: flex; flex-wrap: wrap; gap: .8rem; margin-top: 1.4rem; }}
    .button {{ min-height: 48px; display: inline-flex; align-items: center; justify-content: center; padding: .7rem 1.1rem; border: 2px solid #C41230; border-radius: 999px; color: var(--deep-red); font-weight: 700; text-decoration: none; }}
    .button.btn-primary {{ border-color: #C41230; background: linear-gradient(135deg, #C41230, #8B0D22); color: var(--white); }}
    .notice {{ margin-top: 1.3rem; padding: 1rem 1.15rem; border-left: 4px solid #C41230; background: #FFFFFF; }}
    .scope-grid, .source-grid, .next-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin-top: 1.8rem; }}
    .scope-card, .source-card, .next-card {{ padding: 1.45rem; background: #FFFFFF; border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 14px 40px rgba(26,26,26,.045); }}
    .scope-card {{ border-top: 4px solid #B8962E; }}
    .scope-card h3, .source-card h3 {{ margin: 0 0 .65rem; font-size: 1.32rem; }}
    .scope-card p, .source-card p {{ margin: 0; color: var(--muted); }}
    .source-card {{ display: flex; flex-direction: column; }}
    .source-card .source-links {{ margin-top: auto; padding-top: 1rem; }}
    .source-links a {{ min-height: 44px; display: flex; align-items: center; font-weight: 700; }}
    .method {{ padding: clamp(1.6rem, 4vw, 2.5rem); background: #1A1A1A; color: var(--white); border-radius: 16px; box-shadow: inset 0 0 0 1px rgba(184,150,46,.25); }}
    .method h2 {{ color: var(--white); }}
    .method ol {{ margin: 1.4rem 0; padding-left: 1.45rem; }}
    .method li {{ padding: .4rem 0 .4rem .3rem; }}
    .method-note {{ margin: 1.2rem 0 0; padding: 1rem 1.1rem; background: rgba(184,150,46,.12); border: 1px solid rgba(184,150,46,.35); border-radius: 10px; }}
    .next-card {{ min-height: 112px; display: flex; align-items: center; }}
    .next-card a {{ min-height: 44px; display: inline-flex; align-items: center; font-weight: 700; }}
    .record {{ padding: 1.4rem; background: #FFFFFF; border: 1px solid var(--line); border-left: 4px solid #8B0D22; border-radius: 10px; }}
    .record h2 {{ margin-top: 0; font-size: 1.65rem; }}
    .record p:last-child {{ margin-bottom: 0; }}
    footer {{ background: #1A1A1A; color: rgba(255,255,255,.78); }}
    .footer-inner {{ width: min(1050px, calc(100% - 2rem)); margin: 0 auto; padding: 2.5rem 0; display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }}
    .footer-inner strong {{ color: #FFFFFF; font-family: var(--display); }}
    .footer-inner p {{ margin: .35rem 0 0; }}
    .footer-inner a {{ min-height: 44px; display: inline-flex; align-items: center; color: #FFFFFF; }}
    @media (max-width: 820px) {{
      .menu-button {{ display: inline-flex; }}
      .nav-links {{ display: none; position: absolute; top: 76px; left: 0; right: 0; margin: 0; padding: .8rem 1rem 1.1rem; flex-direction: column; align-items: stretch; background: #1A1A1A; border-top: 1px solid rgba(184,150,46,.3); }}
      .nav-links.open {{ display: flex; }}
      .nav-links a {{ width: 100%; }}
      .scope-grid, .source-grid {{ grid-template-columns: 1fr 1fr; }}
      .next-grid {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 560px) {{
      .brand {{ max-width: 230px; }}
      .scope-grid, .source-grid, .next-grid {{ grid-template-columns: 1fr; }}
      .hero-inner, .content {{ width: min(100% - 1.25rem, 1050px); }}
      .button-row {{ flex-direction: column; }}
      .button {{ width: 100%; text-align: center; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">{esc(copy["skip"])}</a>
  <nav class="site-nav" aria-label="{esc(copy['nav_label'])}">
    <div class="nav-inner">
      <a class="brand" href="{prefix or '/'}">The Jorge Ramirez Group</a>
      <button class="menu-button" type="button" aria-expanded="false" aria-controls="primary-links">{esc(copy['menu'])}</button>
      <div class="nav-links" id="primary-links">
        <a href="{prefix or '/'}">{esc(copy["home"])}</a>
        <a href="{prefix}/counties/{county_slug}-county">{esc(copy["counties"])}</a>
        <a href="{prefix}/blog">{esc(copy["blog"])}</a>
        <a href="{prefix}/contact">{esc(copy["contact"])}</a>
        <a class="lang-link" href="{other_route}" lang="{'es' if language == 'en' else 'en'}">{esc(copy["lang_label"])}</a>
        <a class="nav-cta" href="{prefix}/home-valuation">{esc(copy["nav_cta"])}</a>
      </div>
    </div>
  </nav>

  <main id="main" tabindex="-1">
    <article data-geography-scope="county-not-municipality" data-publication-policy="links-not-tables">
      <header class="hero">
        <div class="hero-inner">
          <p class="eyebrow">{esc(copy["eyebrow"])}</p>
          <h1>{esc(copy["h1"])}</h1>
          <p class="dek">{esc(copy["dek"])}</p>
          <div class="hero-meta">
            <span>{esc(copy["reviewed"])}: <time datetime="{REVIEWED_ON}">{REVIEWED_ON}</time></span>
            <span>{esc(copy["byline"])}</span>
          </div>
        </div>
      </header>

      <div class="content">
        <section class="section" aria-labelledby="current-report">
          <h2 id="current-report">{esc(copy["start"])}</h2>
          <p class="lead">{esc(copy["start_intro"])}</p>
          <ol class="workflow">
{steps}
          </ol>
          <p>{esc(copy["q2_note"])}</p>
          <div class="button-row">
            <a class="button" href="{esc(sources['njr-market-data']['url'])}" rel="noopener">{esc(copy["njr_page"])}</a>
            <a class="button btn-primary" href="{esc(sources['njr-public-county-portal']['url'])}" rel="noopener">{esc(copy["portal"])}</a>
          </div>
          <p class="notice">{esc(copy["publication_note"])}</p>
        </section>

        <section class="section" aria-labelledby="scope-heading">
          <h2 id="scope-heading">{esc(copy["scope"])}</h2>
          <div class="scope-grid">
            <div class="scope-card">
              <h3>{esc(copy["county_label"])}</h3>
              <p>{esc(copy["county_text"])}</p>
            </div>
            <div class="scope-card">
              <h3>{esc(copy["municipality_label"])}</h3>
              <p>{esc(copy["municipality_text"])}</p>
            </div>
            <div class="scope-card">
              <h3>{esc(copy["property_label"])}</h3>
              <p>{esc(copy["property_text"])}</p>
            </div>
          </div>
        </section>

        <section class="section" aria-labelledby="source-heading">
          <h2 id="source-heading">{esc(copy["sources_heading"])}</h2>
          <p class="lead">{esc(copy["source_intro"])}</p>
          <div class="source-grid">
            <div class="source-card">
              <h3>{esc(copy["njr_title"])}</h3>
              <p>{esc(copy["njr_text"])}</p>
              <div class="source-links"><a href="{esc(sources['njr-public-county-portal']['url'])}" rel="noopener">{esc(copy["portal"])}</a></div>
            </div>
            <div class="source-card">
              <h3>{esc(copy["treasury_title"])}</h3>
              <p>{esc(copy["treasury_text"])}</p>
              <div class="source-links">
                <a href="{esc(sources['nj-treasury-property-tax-statistics']['url'])}" rel="noopener">{esc(copy["tax_stats"])}</a>
                <a href="{esc(sources['nj-treasury-average-residential-2025']['url'])}" rel="noopener">{esc(copy["avg_pdf"])}</a>
              </div>
            </div>
            <div class="source-card">
              <h3>{esc(copy["equal_title"])}</h3>
              <p>{esc(copy["equal_text"])}</p>
              <div class="source-links"><a href="{esc(sources['nj-treasury-equalization-tables']['url'])}" rel="noopener">{esc(copy["equal_title"])}</a></div>
            </div>
            <div class="source-card">
              <h3>{esc(copy["dca_title"])}</h3>
              <p>{esc(copy["dca_text"])}</p>
              <div class="source-links"><a href="{esc(sources['nj-dca-construction-reporter']['url'])}" rel="noopener">{esc(copy["dca_title"])}</a></div>
            </div>
            <div class="source-card">
              <h3>{esc(copy["acs_title"])}</h3>
              <p>{esc(copy["acs_text"])}</p>
              <div class="source-links">
                <a href="{esc(sources['census-acs-data-profiles']['url'])}" rel="noopener">{esc(copy["acs_docs"])}</a>
                <a href="{esc(report['acsHousingProfile'])}" rel="noopener">{esc(copy["acs_profile"])}</a>
              </div>
            </div>
            <div class="source-card">
              <h3>{esc(copy["official_title"])}</h3>
              <p>{esc(copy["official_text"])}</p>
              <div class="source-links"><a href="{esc(directory['url'])}" rel="noopener">{esc(directory['title'])}</a></div>
            </div>
          </div>
        </section>

        <section class="section method" aria-labelledby="method-heading">
          <h2 id="method-heading">{esc(copy["method_heading"])}</h2>
          <ol>
{method_items}
          </ol>
          <p class="method-note">{esc(copy["method_note"])}</p>
        </section>

        <section class="section" aria-labelledby="next-heading">
          <h2 id="next-heading">{esc(copy["next_heading"])}</h2>
          <div class="next-grid">
            <div class="next-card"><a href="{prefix}/counties/{county_slug}-county">{esc(copy["county_cta"])}</a></div>
            <div class="next-card"><a href="{prefix}/home-valuation">{esc(copy["value_cta"])}</a></div>
            <div class="next-card"><a href="{prefix}/sell-your-home">{esc(copy["sell_cta"])}</a></div>
            <div class="next-card"><a href="{prefix}/contact">{esc(copy["contact_cta"])}</a></div>
          </div>
        </section>

        <aside class="record" aria-labelledby="record-heading">
          <h2 id="record-heading">{esc(copy["record_heading"])}</h2>
          <p>{esc(copy["record_text"])}</p>
          <p>{esc(copy["correction"])}</p>
        </aside>
      </div>
    </article>
  </main>

  <footer>
    <div class="footer-inner">
      <div><strong>{esc(copy["footer_text"])}</strong><p>{esc(copy["footer_note"])}</p></div>
      <a href="{prefix}/contact">{esc(copy["contact_cta"])}</a>
    </div>
  </footer>
  <script>
    (() => {{
      const menuButton = document.querySelector('.menu-button');
      const primaryLinks = document.querySelector('#primary-links');
      if (!menuButton || !primaryLinks) return;
      menuButton.addEventListener('click', () => {{
        const isOpen = primaryLinks.classList.toggle('open');
        menuButton.setAttribute('aria-expanded', String(isOpen));
      }});
    }})();
  </script>
  <script src="/js/site-cta.js" defer></script>
</body>
</html>
'''


def targets(document: dict) -> list[tuple[Path, str]]:
    sources = {item["id"]: item for item in document["sharedSources"]}
    rendered: list[tuple[Path, str]] = []
    for report in sorted(document["reports"], key=lambda item: item["slug"]):
        for language in ("en", "es"):
            relative = Path(report["routes"][language].lstrip("/") + ".html")
            allowed_prefix = Path("es/blog") if language == "es" else Path("blog")
            if relative.parent != allowed_prefix or relative.stem not in EXPECTED_SLUGS:
                raise ValueError(f"refusing unexpected output path: {relative}")
            rendered.append((ROOT / relative, render_page(report, sources, language)))
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail when a managed page is stale")
    mode.add_argument("--write", action="store_true", help="write stale managed pages")
    args = parser.parse_args()

    try:
        rendered = targets(load_manifest())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"County market research manifest error: {error}", file=sys.stderr)
        return 2

    stale = [path for path, content in rendered if not path.exists() or path.read_text(encoding="utf-8") != content]
    if args.check:
        if stale:
            print("Stale county market research pages:")
            for path in stale:
                print(f"- {path.relative_to(ROOT)}")
            return 1
        print(f"{len(rendered)} county market research pages are current.")
        return 0

    for path, content in rendered:
        if path in stale:
            path.write_text(content, encoding="utf-8")
    print(f"Updated {len(stale)} county market research pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
