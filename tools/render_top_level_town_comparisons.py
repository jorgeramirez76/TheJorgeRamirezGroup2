#!/usr/bin/env python3
"""Render the canonical bilingual top-level town comparisons from one manifest."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "top-level-town-comparison-sources.json"
SITE = "https://thejorgeramirezgroup.com"


UI = {
    "en": {
        "lang": "en-US",
        "locale": "en_US",
        "home": "/",
        "alternate_label": "Español",
        "skip": "Skip to main content",
        "nav_overview": "Overview",
        "nav_method": "Method",
        "nav_sources": "Sources",
        "hero_kicker": "Official-record property comparison",
        "reviewed": "Sources checked",
        "educational": "Educational guide",
        "jump_overview": "Record desks",
        "jump_matrix": "Research matrix",
        "jump_method": "Address method",
        "jump_sources": "Source desk",
        "overview_label": "Start with legal geography",
        "overview_heading": "Two place names, two property files",
        "overview_intro": "A useful comparison begins with the legal municipality and parcel—not a broad description of either place. The cards below identify the official record desk for each side.",
        "notice": "This guide does not score municipalities, predict results, or create resident profiles. It organizes current official records and questions for a specific address. The housing decision remains yours.",
        "record_desk": "Municipal record desk",
        "review_records": "What to verify",
        "open_official": "Open official municipal source",
        "matrix_label": "Use the same evidence",
        "matrix_heading": "An address-first research matrix",
        "matrix_intro": "Use the same document categories and the same service date for both properties. Record what the official source says, what remains unknown, and who can confirm it.",
        "matrix_factor": "Record to compare",
        "legal": "Legal municipality",
        "tax": "Assessment and tax bill",
        "transit": "NJ Transit query",
        "education": "NJDOE public reports",
        "land_use": "Zoning and permits",
        "tax_cell": "Retrieve the current parcel assessment and property-tax bill. Read them with New Jersey's official tax definitions and tables; a municipality-wide figure does not replace the parcel record.",
        "education_cell": "Open the current NJDOE School Performance Reports, confirm the reporting entity and address assignment directly, and read the reporting-period definitions. Use the report as a public record, not a recommendation.",
        "method_label": "Repeatable due diligence",
        "method_heading": "Build the comparison from documents",
        "method_intro": "Keep a dated file for each address so later changes in listings, schedules, or public records do not blur the comparison.",
        "steps": [
            ["Resolve the legal record desk", "Confirm the municipality, parcel identifier, property type, and every public office responsible for that address."],
            ["Collect property documents", "Save the current assessment, tax bill, permit and zoning records, disclosures, and available building or association documents."],
            ["Run a dated transit query", "Enter the exact origin, destination, mode, and service date in NJ Transit's planner. Recheck schedules and alerts before relying on a route."],
            ["Read public reports in context", "Confirm the NJDOE reporting entity and address assignment, then read definitions and reporting periods before noting any metric."],
        ],
        "sources_label": "Primary sources only",
        "sources_heading": "Official source desk",
        "sources_intro": "Every link below was checked on the displayed date. Reopen the source when evaluating a property because records and service details can change.",
        "shared": "Statewide research sources",
        "checked": "Checked",
        "faq_label": "Questions to resolve",
        "faq_heading": "Comparison FAQ",
        "resources_label": "Planning tools",
        "resources_heading": "Continue with property-level research",
        "resources_intro": "Use current financing inputs and official program criteria alongside the property documents. Calculator outputs are estimates, not lending terms.",
        "programs": "First-time-buyer program resources",
        "mortgage": "Mortgage calculator",
        "closing": "Closing-cost calculator",
        "cta_heading": "Bring two addresses, not two labels",
        "cta_body": "Jorge can help organize current public sources, property documents, and questions for licensed professionals. You decide which properties to consider.",
        "call": "Call 908-230-7844",
        "consult": "Request a consultation",
        "disclaimer": "Educational information only—not legal, tax, financial, engineering, insurance, education, or transit advice. Verify documents with the responsible agency or licensed professional. Equal Housing Opportunity.",
        "license": "Jorge Ramirez · New Jersey License #1754604 · Keller Williams Premier Properties · Serving Essex, Union, Morris, Somerset, Middlesex, and Hudson counties",
        "faq_questions": [
            "Are {left} and {right} the same municipality?",
            "How should I compare the property-tax records?",
            "How should I compare NJ Transit access?",
            "How should I use NJDOE public reports?",
            "Does this guide recommend one municipality?",
        ],
        "faq_answers": [
            "No assumption should be made from the place names. Confirm the legal municipality and parcel for each specific address, then use the responsible local office.",
            "Use each property's current assessment and tax bill, then consult the New Jersey Division of Taxation definitions and tables. Do not substitute a municipality-wide figure for parcel documents.",
            "Run NJ Transit's trip planner from each specific address with the same destination and service date. Confirm mode, transfers, schedules, and alerts again before travel.",
            "Open the current School Performance Reports, confirm the reporting entity and address assignment directly, and read the definitions and reporting period. The reports are public records, not a recommendation.",
            "No. It organizes official records and property-specific questions. You make the housing decision after reviewing your criteria, documents, and advice from the professionals you select.",
        ],
    },
    "es": {
        "lang": "es-US",
        "locale": "es_US",
        "home": "/es/",
        "alternate_label": "English",
        "skip": "Ir al contenido principal",
        "nav_overview": "Resumen",
        "nav_method": "Método",
        "nav_sources": "Fuentes",
        "hero_kicker": "Comparación inmobiliaria con registros oficiales",
        "reviewed": "Fuentes revisadas",
        "educational": "Guía educativa",
        "jump_overview": "Oficinas de registro",
        "jump_matrix": "Matriz documental",
        "jump_method": "Método por dirección",
        "jump_sources": "Fuentes oficiales",
        "overview_label": "Empieza con la geografía legal",
        "overview_heading": "Dos nombres de lugar, dos expedientes inmobiliarios",
        "overview_intro": "Una comparación útil empieza con el municipio legal y la parcela, no con una descripción general del lugar. Estas tarjetas identifican la oficina oficial de cada lado.",
        "notice": "Esta guía no asigna puntuaciones a municipios, no predice resultados ni crea perfiles de residentes. Organiza registros oficiales vigentes y preguntas para una dirección específica. La decisión de vivienda es tuya.",
        "record_desk": "Oficina de registros municipales",
        "review_records": "Qué verificar",
        "open_official": "Abrir fuente municipal oficial",
        "matrix_label": "Usa la misma evidencia",
        "matrix_heading": "Matriz de investigación por dirección",
        "matrix_intro": "Usa las mismas categorías documentales y la misma fecha de servicio para ambas propiedades. Anota lo que dice la fuente oficial, lo pendiente y quién puede confirmarlo.",
        "matrix_factor": "Registro que se compara",
        "legal": "Municipio legal",
        "tax": "Tasación y factura fiscal",
        "transit": "Consulta de NJ Transit",
        "education": "Informes públicos de NJDOE",
        "land_use": "Zonificación y permisos",
        "tax_cell": "Obtén la tasación vigente y la factura del impuesto de la parcela. Léelas con las definiciones y tablas oficiales de Nueva Jersey; una cifra municipal no sustituye el registro de la parcela.",
        "education_cell": "Abre los School Performance Reports vigentes de NJDOE, confirma directamente la entidad informante y la asignación de la dirección, y lee las definiciones del período. Usa el informe como registro público, no como recomendación.",
        "method_label": "Debida diligencia repetible",
        "method_heading": "Construye la comparación con documentos",
        "method_intro": "Mantén un archivo fechado para cada dirección, de modo que los cambios posteriores en anuncios, horarios o registros públicos no confundan la comparación.",
        "steps": [
            ["Aclara la oficina legal", "Confirma el municipio, el identificador de la parcela, el tipo de propiedad y cada oficina pública responsable de esa dirección."],
            ["Reúne los documentos", "Guarda la tasación vigente, la factura fiscal, los registros de permisos y zonificación, las divulgaciones y los documentos disponibles del edificio o la asociación."],
            ["Consulta el transporte con fecha", "Introduce origen, destino, modo y fecha de servicio exactos en el planificador de NJ Transit. Revisa de nuevo los horarios y avisos antes de usar una ruta."],
            ["Lee los informes en contexto", "Confirma la entidad informante de NJDOE y la asignación de la dirección; después lee definiciones y períodos antes de anotar cualquier métrica."],
        ],
        "sources_label": "Solo fuentes primarias",
        "sources_heading": "Directorio de fuentes oficiales",
        "sources_intro": "Cada enlace se revisó en la fecha indicada. Abre nuevamente la fuente al evaluar una propiedad, porque los registros y detalles de servicio pueden cambiar.",
        "shared": "Fuentes estatales de investigación",
        "checked": "Consultada",
        "faq_label": "Preguntas que debes resolver",
        "faq_heading": "Preguntas sobre la comparación",
        "resources_label": "Herramientas de planificación",
        "resources_heading": "Continúa con la investigación de la propiedad",
        "resources_intro": "Usa datos financieros vigentes y criterios oficiales de los programas junto con los documentos de la propiedad. Los resultados de calculadoras son estimaciones, no condiciones de préstamo.",
        "programs": "Recursos para programas de primera compra",
        "mortgage": "Calculadora hipotecaria",
        "closing": "Calculadora de costos de cierre",
        "cta_heading": "Trae dos direcciones, no dos etiquetas",
        "cta_body": "Jorge puede ayudarte a organizar fuentes públicas vigentes, documentos de las propiedades y preguntas para profesionales con licencia. Tú decides qué propiedades considerar.",
        "call": "Llamar al 908-230-7844",
        "consult": "Solicitar una consulta",
        "disclaimer": "Información educativa solamente; no constituye asesoría legal, fiscal, financiera, de ingeniería, cobertura, educación ni transporte. Verifica los documentos con la agencia responsable o el profesional autorizado. Equal Housing Opportunity.",
        "license": "Jorge Ramirez · Licencia de Nueva Jersey #1754604 · Keller Williams Premier Properties · Servicio en los condados de Essex, Union, Morris, Somerset, Middlesex y Hudson",
        "faq_questions": [
            "¿{left} y {right} son el mismo municipio?",
            "¿Cómo debo comparar los registros del impuesto inmobiliario?",
            "¿Cómo debo comparar el acceso a NJ Transit?",
            "¿Cómo debo usar los informes públicos de NJDOE?",
            "¿Esta guía recomienda un municipio?",
        ],
        "faq_answers": [
            "No se debe suponer nada a partir de los nombres. Confirma el municipio legal y la parcela de cada dirección específica; después consulta la oficina local responsable.",
            "Usa la tasación vigente y la factura fiscal de cada propiedad; después consulta las definiciones y tablas de New Jersey Division of Taxation. No sustituyas los documentos de la parcela por una cifra municipal.",
            "Consulta el planificador de NJ Transit desde cada dirección específica con el mismo destino y fecha de servicio. Confirma nuevamente el modo, los transbordos, los horarios y los avisos antes del viaje.",
            "Abre los School Performance Reports vigentes, confirma directamente la entidad informante y la asignación de la dirección, y lee las definiciones y el período. Son registros públicos, no una recomendación.",
            "No. La guía organiza registros oficiales y preguntas específicas de las propiedades. Tomas la decisión de vivienda después de revisar tus criterios, documentos y la asesoría de los profesionales que elijas.",
        ],
    },
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def source_list(records: list[dict[str, str]], ui: dict[str, object]) -> str:
    return "\n".join(
        f'''<li><a href="{esc(record['url'])}" target="_blank" rel="noopener">{esc(record['publisher'])}</a><span class="tc-source-date">{esc(str(ui['checked']))}: {esc(record['accessed'])}</span></li>'''
        for record in records
    )


def faq_data(ui: dict[str, object], left: str, right: str) -> list[dict[str, str]]:
    questions = [str(value).format(left=left, right=right) for value in ui["faq_questions"]]
    answers = [str(value) for value in ui["faq_answers"]]
    return [{"question": question, "answer": answer} for question, answer in zip(questions, answers)]


def schema_graph(
    *,
    canonical: str,
    copy: dict[str, str],
    ui: dict[str, object],
    language: str,
    faq: list[dict[str, str]],
) -> str:
    home_url = f"{SITE}/es/" if language == "es" else f"{SITE}/"
    home_name = "Inicio" if language == "es" else "Home"
    comparison_name = "Comparación inmobiliaria" if language == "es" else "Property comparison"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": copy["h1"],
                "description": copy["description"],
                "inLanguage": ui["lang"],
                "dateModified": "2026-08-26",
                "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
            },
            {
                "@type": "Article",
                "@id": f"{canonical}#article",
                "url": canonical,
                "mainEntityOfPage": {"@id": f"{canonical}#webpage"},
                "headline": copy["h1"],
                "description": copy["description"],
                "inLanguage": ui["lang"],
                "dateModified": "2026-08-26",
                "image": f"{SITE}/images/hero.jpg",
                "author": {
                    "@type": "Person",
                    "@id": f"{SITE}/#jorge-ramirez",
                    "name": "Jorge Ramirez",
                },
                "publisher": {"@type": "Organization", "name": "The Jorge Ramirez Group"},
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{canonical}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": home_name, "item": home_url},
                    {"@type": "ListItem", "position": 2, "name": comparison_name, "item": canonical},
                ],
            },
            {
                "@type": "FAQPage",
                "@id": f"{canonical}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                    }
                    for item in faq
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def render_page(
    manifest: dict[str, object],
    slug: str,
    language: str,
) -> str:
    comparison = manifest["comparisons"][slug]
    copy = comparison["copy"][language]
    left = manifest["places"][comparison["left"]]
    right = manifest["places"][comparison["right"]]
    left_copy = left["copy"][language]
    right_copy = right["copy"][language]
    ui = UI[language]

    en_url = f"{SITE}/{slug}"
    es_url = f"{SITE}/es/{slug}"
    canonical = es_url if language == "es" else en_url
    alternate_path = f"/{slug}" if language == "es" else f"/es/{slug}"
    home = str(ui["home"])
    contact = f"{home}#contact"
    programs = (
        "/es/blog/first-time-home-buyer-nj-guide"
        if language == "es"
        else "/blog/first-time-home-buyer-nj-guide"
    )
    mortgage = f"/es/tools/mortgage-calculator" if language == "es" else "/tools/mortgage-calculator"
    closing = f"/es/closing-costs-calculator" if language == "es" else "/closing-costs-calculator"
    faq = faq_data(ui, left_copy["label"], right_copy["label"])
    schema = schema_graph(
        canonical=canonical,
        copy=copy,
        ui=ui,
        language=language,
        faq=faq,
    )

    llm_context = (
        f"{copy['query_names']} official records property guide based on municipal, NJ Transit, NJDOE, and New Jersey tax sources checked 2026-08-26. "
        "Address-specific educational research; no municipality scoring or outcome prediction."
        if language == "en"
        else f"Guía de {copy['query_names']} basada en registros oficiales municipales, de NJ Transit, NJDOE e impuestos de Nueva Jersey, revisados el 2026-08-26. Investigación educativa por dirección; sin puntuaciones ni predicciones."
    )

    place_cards = []
    for place, place_copy in ((left, left_copy), (right, right_copy)):
        primary = place["sources"][0]
        place_cards.append(
            f'''<article class="tc-card">
              <p class="tc-card-kicker">{esc(str(ui['record_desk']))} · {esc(place_copy['county'])}</p>
              <h2>{esc(place_copy['label'])}</h2>
              <p>{esc(place_copy['identity'])}</p>
              <p><strong>{esc(str(ui['review_records']))}:</strong> {esc(place_copy['records'])}</p>
              <p class="tc-card-source"><a href="{esc(primary['url'])}" target="_blank" rel="noopener">{esc(str(ui['open_official']))}</a></p>
            </article>'''
        )

    workflow = "\n".join(
        f"<li><strong>{esc(title)}</strong>{esc(body)}</li>"
        for title, body in ui["steps"]
    )
    faq_html = "\n".join(
        f'''<details class="tc-faq"><summary>{esc(item['question'])}</summary><p>{esc(item['answer'])}</p></details>'''
        for item in faq
    )

    return f'''<!doctype html>
<html lang="{esc(str(ui['lang']))}">
<head>
  <meta charset="utf-8">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0A0A0A">
  <title>{esc(copy['title'])}</title>
  <meta name="description" content="{esc(copy['description'])}">
  <meta name="author" content="Jorge Ramirez">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="llm-context" content="{esc(llm_context)}">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="{esc(str(ui['locale']))}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:title" content="{esc(copy['title'])}">
  <meta property="og:description" content="{esc(copy['description'])}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(copy['title'])}">
  <meta name="twitter:description" content="{esc(copy['description'])}">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="alternate" hreflang="en-US" href="{en_url}">
  <link rel="alternate" hreflang="es-US" href="{es_url}">
  <link rel="alternate" hreflang="es" href="{es_url}">
  <link rel="alternate" hreflang="x-default" href="{en_url}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@500;600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/top-level-town-comparisons.css">
  <script type="application/ld+json">
{schema}
  </script>
</head>
<body class="tc-page">
  <!-- Generated by tools/render_top_level_town_comparisons.py from data/top-level-town-comparison-sources.json. -->
  <a class="tc-skip-link" href="#main-content">{esc(str(ui['skip']))}</a>
  <header class="tc-site-header">
    <div class="tc-header-inner">
      <a class="tc-brand" href="{esc(home)}" aria-label="The Jorge Ramirez Group">
        <picture>
          <source srcset="/images/jorge-logo.webp" type="image/webp">
          <img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="190" height="80">
        </picture>
      </a>
      <nav class="tc-header-nav" aria-label="{'Navegación principal' if language == 'es' else 'Primary navigation'}">
        <a href="#overview">{esc(str(ui['nav_overview']))}</a>
        <a href="#method">{esc(str(ui['nav_method']))}</a>
        <a href="#sources">{esc(str(ui['nav_sources']))}</a>
        <a class="tc-language" href="{alternate_path}" lang="{'en' if language == 'es' else 'es'}">{esc(str(ui['alternate_label']))}</a>
      </nav>
    </div>
  </header>

  <main id="main-content" class="tc-main">
    <section class="tc-hero" aria-labelledby="comparison-title">
      <div class="tc-hero-inner">
        <p class="tc-eyebrow">{esc(str(ui['hero_kicker']))}</p>
        <h1 id="comparison-title">{esc(copy['h1'])}</h1>
        <p class="tc-hero-lede">{esc(copy['lede'])}</p>
        <div class="tc-hero-meta"><span>{esc(str(ui['reviewed']))}: {manifest['reviewed']}</span><span>{esc(str(ui['educational']))}</span></div>
      </div>
    </section>

    <nav class="tc-jumpbar" aria-label="{'Secciones de la guía' if language == 'es' else 'Guide sections'}">
      <a href="#overview">{esc(str(ui['jump_overview']))}</a>
      <a href="#matrix">{esc(str(ui['jump_matrix']))}</a>
      <a href="#method">{esc(str(ui['jump_method']))}</a>
      <a href="#sources">{esc(str(ui['jump_sources']))}</a>
    </nav>

    <section id="overview" class="tc-section">
      <div class="tc-shell">
        <p class="tc-section-label">{esc(str(ui['overview_label']))}</p>
        <h2 class="tc-section-heading">{esc(str(ui['overview_heading']))}</h2>
        <p class="tc-section-intro">{esc(str(ui['overview_intro']))}</p>
        <div class="tc-notice"><strong>{'Neutral research note:' if language == 'en' else 'Nota de investigación neutral:'}</strong> {esc(str(ui['notice']))}</div>
        <div class="tc-place-grid">{''.join(place_cards)}</div>
      </div>
    </section>

    <section id="matrix" class="tc-section tc-tinted">
      <div class="tc-shell">
        <p class="tc-section-label">{esc(str(ui['matrix_label']))}</p>
        <h2 class="tc-section-heading">{esc(str(ui['matrix_heading']))}</h2>
        <p class="tc-section-intro">{esc(str(ui['matrix_intro']))}</p>
        <div class="tc-table-wrap" tabindex="0" role="region" aria-label="{'Tabla comparativa de registros' if language == 'es' else 'Record comparison table'}">
          <table class="tc-matrix">
            <thead><tr><th scope="col">{esc(str(ui['matrix_factor']))}</th><th scope="col">{esc(left_copy['label'])}</th><th scope="col">{esc(right_copy['label'])}</th></tr></thead>
            <tbody>
              <tr><th scope="row">{esc(str(ui['legal']))}</th><td>{esc(left_copy['identity'])}</td><td>{esc(right_copy['identity'])}</td></tr>
              <tr><th scope="row">{esc(str(ui['tax']))}</th><td>{esc(str(ui['tax_cell']))}</td><td>{esc(str(ui['tax_cell']))}</td></tr>
              <tr><th scope="row">{esc(str(ui['transit']))}</th><td>{esc(left_copy['transit'])}</td><td>{esc(right_copy['transit'])}</td></tr>
              <tr><th scope="row">{esc(str(ui['education']))}</th><td>{esc(str(ui['education_cell']))}</td><td>{esc(str(ui['education_cell']))}</td></tr>
              <tr><th scope="row">{esc(str(ui['land_use']))}</th><td>{esc(left_copy['records'])}</td><td>{esc(right_copy['records'])}</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section id="method" class="tc-section">
      <div class="tc-shell">
        <p class="tc-section-label">{esc(str(ui['method_label']))}</p>
        <h2 class="tc-section-heading">{esc(str(ui['method_heading']))}</h2>
        <p class="tc-section-intro">{esc(str(ui['method_intro']))}</p>
        <ol class="tc-workflow">{workflow}</ol>
      </div>
    </section>

    <section id="sources" class="tc-section tc-tinted">
      <div class="tc-shell">
        <p class="tc-section-label">{esc(str(ui['sources_label']))}</p>
        <h2 class="tc-section-heading">{esc(str(ui['sources_heading']))}</h2>
        <p class="tc-section-intro">{esc(str(ui['sources_intro']))}</p>
        <div class="tc-sources">
          <section class="tc-source-group" aria-labelledby="left-source-heading"><h3 id="left-source-heading">{esc(left_copy['label'])}</h3><ul class="tc-source-list">{source_list(left['sources'], ui)}</ul></section>
          <section class="tc-source-group" aria-labelledby="right-source-heading"><h3 id="right-source-heading">{esc(right_copy['label'])}</h3><ul class="tc-source-list">{source_list(right['sources'], ui)}</ul></section>
          <section class="tc-source-group tc-shared" aria-labelledby="state-source-heading"><h3 id="state-source-heading">{esc(str(ui['shared']))}</h3><ul class="tc-source-list">{source_list(manifest['shared_sources'], ui)}</ul></section>
        </div>
      </div>
    </section>

    <section class="tc-section" aria-labelledby="faq-heading">
      <div class="tc-shell">
        <p class="tc-section-label">{esc(str(ui['faq_label']))}</p>
        <h2 id="faq-heading" class="tc-section-heading">{esc(str(ui['faq_heading']))}</h2>
        <div class="tc-faq-list">{faq_html}</div>
      </div>
    </section>

    <section class="tc-section tc-tinted" aria-labelledby="resources-heading">
      <div class="tc-shell">
        <p class="tc-section-label">{esc(str(ui['resources_label']))}</p>
        <h2 id="resources-heading" class="tc-section-heading">{esc(str(ui['resources_heading']))}</h2>
        <p class="tc-section-intro">{esc(str(ui['resources_intro']))}</p>
        <div class="tc-resource-grid">
          <a class="tc-resource-link" href="{programs}">{esc(str(ui['programs']))}</a>
          <a class="tc-resource-link" href="{mortgage}">{esc(str(ui['mortgage']))}</a>
          <a class="tc-resource-link" href="{closing}">{esc(str(ui['closing']))}</a>
        </div>
      </div>
    </section>

    <section class="tc-cta" aria-labelledby="cta-heading">
      <div class="tc-cta-inner">
        <h2 id="cta-heading">{esc(str(ui['cta_heading']))}</h2>
        <p>{esc(str(ui['cta_body']))}</p>
        <div class="tc-cta-actions"><a href="tel:908-230-7844">{esc(str(ui['call']))}</a><a class="tc-cta-secondary" href="{contact}">{esc(str(ui['consult']))}</a></div>
        <p class="tc-disclaimer">{esc(str(ui['disclaimer']))}</p>
      </div>
    </section>
  </main>

  <footer class="tc-footer"><p>© 2026 The Jorge Ramirez Group · {esc(str(ui['license']))}</p></footer>
</body>
</html>
'''


def render_alias(target: str) -> str:
    target_url = f"{SITE}/{target}"
    return f'''<!doctype html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0A0A0A">
  <title>Montclair vs Maplewood NJ | Official Records Guide</title>
  <meta name="description" content="This retired reverse-order route now points to the canonical Montclair and Maplewood official-record property comparison.">
  <meta name="robots" content="noindex, follow">
  <meta name="llm-context" content="Retired reverse-order route. Canonical comparison: Montclair vs. Maplewood official records guide, sources checked 2026-08-26.">
  <meta http-equiv="refresh" content="0; url=/{target}">
  <link rel="canonical" href="{target_url}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&amp;family=Playfair+Display:wght@500;600&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/top-level-town-comparisons.css">
  <script>window.location.replace('/{target}');</script>
</head>
<body class="tc-page">
  <!-- Generated redirect fallback. The server configuration owns the permanent redirect. -->
  <a class="tc-skip-link" href="#main-content">Skip to main content</a>
  <header class="tc-site-header"><div class="tc-header-inner"><a class="tc-brand" href="/" aria-label="The Jorge Ramirez Group"><picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="190" height="80"></picture></a></div></header>
  <main id="main-content" class="tc-main">
    <section class="tc-section"><div class="tc-shell"><p class="tc-section-label">Canonical comparison</p><h1 class="tc-section-heading">This comparison has one current home</h1><p class="tc-section-intro">The reverse-order page has been consolidated so search engines and readers use one official-record guide.</p><p><a class="tc-resource-link" href="/{target}">Continue to Montclair vs. Maplewood</a></p></div></section>
  </main>
  <footer class="tc-footer"><p>© 2026 The Jorge Ramirez Group · New Jersey License #1754604 · Keller Williams Premier Properties</p></footer>
</body>
</html>
'''


def expected_outputs(manifest: dict[str, object]) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for slug in sorted(manifest["comparisons"]):
        outputs[ROOT / f"{slug}.html"] = render_page(manifest, slug, "en")
        outputs[ROOT / "es" / f"{slug}.html"] = render_page(manifest, slug, "es")
    for alias, target in manifest["redirects"].items():
        outputs[ROOT / f"{alias}.html"] = render_alias(target)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated HTML differs from disk")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    outputs = expected_outputs(manifest)
    if args.check:
        stale = [path.relative_to(ROOT).as_posix() for path, expected in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != expected]
        if stale:
            print("stale generated comparison output:", file=sys.stderr)
            for relative in stale:
                print(f"  {relative}", file=sys.stderr)
            return 1
        print(f"comparison renderer check passed ({len(outputs)} files)")
        return 0

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"rendered {len(outputs)} comparison files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
