#!/usr/bin/env python3
"""Render reviewed bilingual Union and Morris town market-research pages.

The renderer is intentionally narrow and fail closed. It writes only the 22
approved routes in its dated source manifest. Municipality values come only
from reviewed rows in New Jersey's finalized 2025 Average Residential
Statistics table; changing county reports stay at their original public source.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

try:
    from tools.market_report_publication_gate import (
        ProvenanceError,
        validate_publication_manifest,
    )
except ModuleNotFoundError:  # Direct execution places tools/ at sys.path[0].
    from market_report_publication_gate import (
        ProvenanceError,
        validate_publication_manifest,
    )


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "union-morris-town-market-sources-2026-08-26.json"
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
PAGE_MODIFIED_ON = "2026-08-27"
RENDERER = "tools/generate_union_morris_town_market_research.py"
METRIC_KEYS = {
    "lineItems",
    "averageAssessment",
    "averageTaxBill",
    "numberOfSales",
    "averageSalesPrice",
}
SOURCE_IDS = {
    "nj-treasury-property-tax-statistics",
    "nj-treasury-average-residential-2025",
    "njr-market-data",
    "njr-public-county-portal",
    "nj-dca-construction-reporter",
    "census-acs-data-profiles",
}
EXPECTED = {
    "market-report-cranford-nj-2026": ("Cranford", "Union", "2003"),
    "market-report-linden-nj-2026": ("Linden", "Union", "2009"),
    "market-report-new-providence-nj-2026": ("New Providence", "Union", "2011"),
    "market-report-rahway-nj-2026": ("Rahway", "Union", "2013"),
    "market-report-scotch-plains-nj-2026": ("Scotch Plains", "Union", "2016"),
    "market-report-westfield-nj-2026": ("Westfield", "Union", "2020"),
    "market-report-chatham-nj-2026": ("Chatham", "Morris", "1404"),
    "market-report-denville-nj-2026": ("Denville", "Morris", "1408"),
    "market-report-madison-nj-2026": ("Madison", "Morris", "1417"),
    "market-report-morristown-nj-2026": ("Morristown", "Morris", "1424"),
    "market-report-randolph-nj-2026": ("Randolph", "Morris", "1432"),
}


def indexable_town_slugs() -> set[str]:
    facts = json.loads((ROOT / "data" / "site-facts.json").read_text(encoding="utf-8"))
    return {
        slug
        for slugs in facts["canonicalTownInventory"]["byCounty"].values()
        for slug in slugs
    }


INDEXABLE_TOWN_SLUGS = indexable_town_slugs()
FORBIDDEN_KEYS = {
    "medianPrice",
    "daysOnMarket",
    "activeListings",
    "yearOverYear",
    "marketType",
    "forecast",
    "ranking",
    "schoolRating",
    "crimeRate",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _https(value: object, context: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{context} must be an absolute HTTPS URL")
    return value


def _walk_forbidden(value: object, context: str = "manifest") -> None:
    if isinstance(value, dict):
        overlap = FORBIDDEN_KEYS.intersection(value)
        if overlap:
            raise ValueError(f"{context} contains forbidden market fields: {sorted(overlap)}")
        for key, child in value.items():
            _walk_forbidden(child, f"{context}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, f"{context}[{index}]")


def _validate_metric(key: str, metric: object, slug: str) -> dict:
    if not isinstance(metric, dict):
        raise ValueError(f"{slug}.{key} must be an object")
    if set(metric) != {"value", "sourceId", "definition"}:
        raise ValueError(f"{slug}.{key} has unexpected fields")
    value = metric.get("value")
    if not isinstance(value, str):
        raise ValueError(f"{slug}.{key}.value must be a string")
    pattern = r"\d+\.\d{2}" if key == "averageSalesPrice" else r"\d+"
    if re.fullmatch(pattern, value) is None:
        raise ValueError(f"{slug}.{key}.value has an invalid format")
    if metric.get("sourceId") != "nj-treasury-average-residential-2025":
        raise ValueError(f"{slug}.{key} does not reference the approved State table")
    definition = metric.get("definition")
    if not isinstance(definition, str) or "2025" not in definition:
        raise ValueError(f"{slug}.{key} lacks a dated definition")
    return metric


def load_manifest(path: Path = MANIFEST) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("town market source manifest must be an object")
    if document.get("schemaVersion") != 1:
        raise ValueError("town market source manifest schemaVersion must be 1")
    if document.get("reviewedOn") != REVIEWED_ON:
        raise ValueError(f"town market sources must be reviewed on {REVIEWED_ON}")
    if document.get("renderer") != RENDERER:
        raise ValueError("town market source manifest points to another renderer")
    direct_answer_rule = document.get("publicationPolicy", {}).get(
        "directAnswerRule", ""
    )
    if not str(direct_answer_rule).startswith("Lead with a 40-60-word"):
        raise ValueError("town market source manifest lacks the direct-answer rule")
    if document.get("reviewStatus") != "approved":
        raise ProvenanceError("reviewStatus must be approved")
    if document.get("reviewedAt") != REVIEWED_ON:
        raise ProvenanceError(f"reviewedAt must be {REVIEWED_ON}")
    if document.get("publicationRights") != "confirmed":
        raise ProvenanceError("publicationRights must be confirmed")
    _walk_forbidden(document)

    sources = document.get("sources")
    if not isinstance(sources, list):
        raise ValueError("manifest sources must be a list")
    source_by_id = {item.get("id"): item for item in sources if isinstance(item, dict)}
    if set(source_by_id) != SOURCE_IDS or len(source_by_id) != len(sources):
        raise ValueError("manifest must contain the exact reviewed shared sources")
    for source_id, source in source_by_id.items():
        if source.get("accessedAt") != REVIEWED_ON:
            raise ValueError(f"source {source_id} has an unreviewed access date")
        _https(source.get("url"), f"source {source_id}.url")
        for field in ("publisher", "geographyType", "geographyName", "reportingPeriod"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f"source {source_id}.{field} must be populated")

    reports = document.get("reports")
    if not isinstance(reports, list):
        raise ValueError("manifest reports must be a list")
    by_slug = {item.get("slug"): item for item in reports if isinstance(item, dict)}
    if set(by_slug) != set(EXPECTED) or len(by_slug) != len(reports):
        raise ValueError("manifest must contain the exact approved town reports")

    treasury = source_by_id["nj-treasury-average-residential-2025"]
    for slug, (name, county, district_code) in EXPECTED.items():
        report = by_slug[slug]
        if (report.get("name"), report.get("county"), report.get("districtCode")) != (
            name,
            county,
            district_code,
        ):
            raise ValueError(f"{slug} changed its reviewed geography or district row")
        if report.get("sourceAccessedOn") != REVIEWED_ON:
            raise ValueError(f"{slug} lacks the reviewed source access date")
        for field in (
            "officialGeography",
            "officialGeographyEs",
            "officialMunicipalityTitle",
            "boundaryNote",
            "boundaryNoteEs",
            "publishedOn",
        ):
            if not isinstance(report.get(field), str) or not report[field].strip():
                raise ValueError(f"{slug}.{field} must be populated")
        _https(report.get("officialMunicipalityUrl"), f"{slug}.officialMunicipalityUrl")
        _https(report.get("acsHousingProfile"), f"{slug}.acsHousingProfile")
        if "ACSDP5Y2024.DP04" not in report["acsHousingProfile"]:
            raise ValueError(f"{slug} must use the reviewed 2024 ACS DP04 profile")
        expected_routes = {
            "en": f"/blog/{slug}",
            "es": f"/es/blog/{slug}",
        }
        if report.get("routes") != expected_routes:
            raise ValueError(f"{slug} changed its canonical routes")
        metrics = report.get("metrics")
        if not isinstance(metrics, dict) or set(metrics) != METRIC_KEYS:
            raise ValueError(f"{slug} must contain the exact five State table fields")
        reviewed_metrics = []
        for key in sorted(METRIC_KEYS):
            metric = _validate_metric(key, metrics[key], slug)
            reviewed_metrics.append(
                {
                    "name": f"{slug}.{key}",
                    "value": metric["value"],
                    "definition": metric["definition"],
                    "sourceId": metric["sourceId"],
                }
            )
        # Reuse the shared publication fence for every rendered municipality.
        validate_publication_manifest(
            {
                "reviewStatus": document["reviewStatus"],
                "reviewedBy": document["reviewedBy"],
                "reviewedAt": document["reviewedAt"],
                "publicationRights": document["publicationRights"],
                "sources": [treasury],
                "metrics": reviewed_metrics,
            }
        )
    return document


def metric_values(report: dict) -> dict[str, str]:
    return {key: report["metrics"][key]["value"] for key in METRIC_KEYS}


def page_copy(report: dict, language: str) -> dict[str, object]:
    name = report["name"]
    county = report["county"]
    official = report["officialGeography"]
    values = metric_values(report)
    sales = f"{int(values['numberOfSales']):,}"
    average_sales_price = f"${float(values['averageSalesPrice']):,.2f}"
    average_assessment = f"${int(values['averageAssessment']):,}"
    average_tax_bill = f"${int(values['averageTaxBill']):,}"
    if language == "en":
        return {
            "title": f"{name} Market Research Guide 2026 | 2025 Data",
            "description": (
                f"Research the {name}, NJ real estate market with the finalized 2025 State row, "
                f"official local records, and a clear path to current {county} County reports."
            ),
            "llm": (
                f"Reviewed municipality research for {official}, New Jersey. Published values are "
                "the finalized 2025 State table averages, not 2026 town listing data or a property valuation."
            ),
            "skip": "Skip to main content",
            "nav_label": "Primary navigation",
            "menu": "Menu",
            "home": "Home",
            "town_guide": f"{name} guide",
            "official_sources_cta": "Official town sources",
            "county_guide": f"{county} County guide",
            "research": "Research",
            "contact": "Contact",
            "language": "Español",
            "valuation": "Request a home valuation",
            "eyebrow": "Official-source municipality research",
            "h1": f"{name}, NJ market research guide 2026: finalized 2025 public data",
            "dek": (
                f"This page’s finalized 2025 New Jersey Treasury source row is {official} "
                f"(C/D {report['districtCode']}) in {county} County. It reports {sales} sales, "
                f"an average sales price of {average_sales_price}, an average assessment of "
                f"{average_assessment}, and an average tax bill of {average_tax_bill}. These are "
                "historical taxing-district averages, not current listing data or a home valuation."
            ),
            "reviewed": "Sources reviewed",
            "prepared": "Prepared by Jorge Ramirez",
            "snapshot_heading": "The finalized 2025 State row",
            "snapshot_intro": (
                f"New Jersey's 2025 Average Residential Statistics table publishes a taxing-district row for {official}, "
                f"C/D {report['districtCode']}. The values below preserve the State's labels and are an average, not a median."
            ),
            "final_note": (
                "This is finalized 2025 tax-administration data. It is not a 2026 listing-service result, "
                "a count of active listings, or a value for a particular home."
            ),
            "line_items": "# of Line Items",
            "line_items_help": "Residential line items represented by the published district row.",
            "assessment": "Avg Assessment",
            "assessment_help": "The State table's average assessment; it is not an asking price or appraisal.",
            "tax_bill": "Avg Tax Bill",
            "tax_help": "The State table's average tax bill; an individual bill depends on the property record.",
            "sales": "# of Sales",
            "sales_help": "The 2025 field in the State row; it is not current for-sale inventory.",
            "sales_price": "Avg Sales Price",
            "sales_price_help": "The State table's 2025 average sales price, not a median or current CMA.",
            "read_row": "Open the official 2025 table",
            "stats_directory": "Property Tax Statistics directory",
            "scope_heading": "Keep the geography and the question aligned",
            "municipality_label": "Municipality record",
            "municipality_text": report["boundaryNote"],
            "county_label": f"{county} County context",
            "county_text": (
                f"A {county} County result does not become a {name} town result. "
                "At the public portal, keep the selected county, period, and property category attached to every number."
            ),
            "property_label": "Individual property",
            "property_text": (
                "A property-specific CMA needs current comparable properties plus the subject property's condition, "
                "features, location, and timing. A municipality average cannot answer that question."
            ),
            "current_heading": "How to check changing 2026 conditions",
            "current_intro": (
                "New Jersey Realtors links to a public state-and-county reporting portal. Municipality reports are described "
                "as a member resource, so this page does not scrape or reproduce those reports. Use this workflow instead:"
            ),
            "current_steps": (
                "Open the New Jersey Realtors market-data page and follow its public reporting link.",
                f"Select {county} County, the exact reporting period, and the available property category.",
                "Record the source label and period before comparing it with another report.",
                f"Treat the result as county context only; do not assign it to {name} or to an individual address.",
                "Return to the original source before a decision because public reports can be revised or replaced.",
            ),
            "njr_directory": "New Jersey Realtors market-data page",
            "njr_portal": "Open the public county-report portal",
            "publication_note": (
                "We link to the public source and do not reproduce its report tables. "
                "No affiliation or endorsement is implied."
            ),
            "source_heading": f"A source stack for {name} research",
            "source_intro": (
                "Each source answers a different question. Keep its geography, release, field label, and access date in your notes."
            ),
            "official_title": f"{official} records",
            "official_text": (
                "Use the official municipality site to locate the appropriate tax, construction, planning, zoning, or public-record office. "
                "Confirm the block, lot, and legal municipality for property-specific work."
            ),
            "official_link": f"Open the official {name} website",
            "acs_title": "Census ACS housing profile DP04",
            "acs_text": (
                "The 2024 ACS five-year Selected Housing Characteristics profile provides survey context for the named geography. "
                "ACS values are estimates for that release, not current transactions or appraisals."
            ),
            "acs_docs": "How ACS Data Profiles work",
            "acs_profile": f"Open the {official} DP04 search",
            "dca_title": "New Jersey DCA Construction Reporter",
            "dca_text": (
                "Permit and certificate activity reported by local officials can help document construction activity. "
                "It is not current listing inventory and does not describe a future sale."
            ),
            "dca_link": "Open the Construction Reporter",
            "method_heading": "A reproducible comparison method",
            "method_steps": (
                f"Name the geography first: {official}, {county} County, or one property.",
                "Write down the publisher, table or report name, release period, selected category, and access date.",
                "Compare identical field labels only. Keep an average separate from a median and a survey estimate separate from a transaction.",
                "Use municipal and DCA records to investigate local property or construction questions; do not turn permit activity into listing inventory.",
                "Use current comparable properties and property details for a CMA; do not substitute a municipality or county figure.",
            ),
            "method_note": (
                "The State row is quoted as published. The remaining sections are a research method and direct source map, "
                "not a copied market table or a property valuation. Compare homes only using the lawful property and transaction "
                "criteria you choose; this page does not rate people or neighborhoods."
            ),
            "next_heading": "Continue at the right level",
            "town_cta": f"Read the {name} community guide",
            "county_cta": f"Read the {county} County guide",
            "value_cta": "Request an address-specific valuation",
            "contact_cta": "Ask a source or property question",
            "record_heading": "Source record, updates, and corrections",
            "record_text": (
                f"All links and the {official} row on this page were reviewed on {REVIEWED_ON}. "
                "The publisher controls definitions, revisions, and availability."
            ),
            "correction": (
                "Correction note: If a source link, district row, field label, period, or geography statement needs attention, "
                "send this page URL and the source in question through the contact page."
            ),
            "footer_note": "Reviewed municipality sources and property-specific guidance in New Jersey.",
            "breadcrumbs": ("Home", "Research", f"{name} market research"),
        }

    return {
        "title": f"Investigación de {name} 2026 | Datos oficiales 2025",
        "description": (
            f"Investigue el mercado inmobiliario de {name}, NJ con la fila estatal final de 2025, "
            f"registros oficiales y acceso a informes vigentes del condado de {county}."
        ),
        "llm": (
            f"Guía de investigación municipal para {report['officialGeographyEs']}, Nueva Jersey. "
            "Los valores publicados son promedios de la tabla estatal finalizada de 2025, no datos "
            "de listados de 2026 ni una valoración de una propiedad."
        ),
        "skip": "Saltar al contenido principal",
        "nav_label": "Navegación principal",
        "menu": "Menú",
        "home": "Inicio",
        "town_guide": f"Guía de {name}",
        "official_sources_cta": "Fuentes oficiales del municipio",
        "county_guide": f"Guía del condado de {county}",
        "research": "Investigación",
        "contact": "Contacto",
        "language": "English",
        "valuation": "Solicitar una valoración",
        "eyebrow": "Investigación municipal con fuentes oficiales",
        "h1": f"Investigación inmobiliaria de {name}, NJ en 2026: datos públicos verificados de 2025",
        "dek": (
            f"La fila finalizada de 2025 del New Jersey Treasury usa la geografía oficial "
            f"“{report['officialGeographyEs']}” (C/D {report['districtCode']}), condado de {county}. "
            f"Informa {sales} ventas, un precio de venta promedio de {average_sales_price}, un "
            f"avalúo promedio de {average_assessment} y una factura fiscal promedio de "
            f"{average_tax_bill}. Son promedios históricos del distrito fiscal, no listados "
            "vigentes ni una valoración."
        ),
        "reviewed": "Fuentes revisadas",
        "prepared": "Preparado por Jorge Ramirez",
        "snapshot_heading": "La fila estatal finalizada de 2025",
        "snapshot_intro": (
            f"La tabla 2025 Average Residential Statistics de Nueva Jersey publica una fila del distrito fiscal para "
            f"{official}, C/D {report['districtCode']}. Los valores conservan las etiquetas del Estado; cada valor rotulado "
            "como promedio es un promedio, no una mediana."
        ),
        "final_note": (
            "Esta es información finalizada de administración tributaria correspondiente a 2025. No es un dato de 2026 de un servicio de listados, "
            "un conteo de propiedades disponibles ni el valor de una vivienda particular."
        ),
        "line_items": "# of Line Items",
        "line_items_help": "Partidas residenciales representadas por la fila publicada del distrito.",
        "assessment": "Avg Assessment",
        "assessment_help": "El avalúo promedio de la tabla estatal; no es precio de oferta ni tasación.",
        "tax_bill": "Avg Tax Bill",
        "tax_help": "La factura fiscal promedio de la tabla estatal; la factura individual depende del registro de la propiedad.",
        "sales": "# of Sales",
        "sales_help": "El campo de 2025 de la fila estatal; no es inventario vigente en venta.",
        "sales_price": "Avg Sales Price",
        "sales_price_help": "El precio de venta promedio de 2025 en la tabla, no una mediana ni un análisis comparativo vigente.",
        "read_row": "Abrir la tabla oficial de 2025",
        "stats_directory": "Directorio de estadísticas del impuesto a la propiedad",
        "scope_heading": "Mantenga alineadas la geografía y la pregunta",
        "municipality_label": "Registro municipal",
        "municipality_text": report["boundaryNoteEs"],
        "county_label": f"Contexto del condado de {county}",
        "county_text": (
            f"Un dato del condado de {county} no es un dato municipal de {name}. "
            "En el portal público, conserve el condado, el período y la categoría seleccionada junto a cada cifra."
        ),
        "property_label": "Propiedad individual",
        "property_text": (
            "Un análisis comparativo de mercado para una propiedad requiere comparables vigentes y detalles sobre condición, "
            "características, ubicación y fecha. Un promedio municipal no responde esa pregunta."
        ),
        "current_heading": "Cómo revisar las condiciones cambiantes de 2026",
        "current_intro": (
            "New Jersey Realtors enlaza a un portal público de informes estatales y por condado. Los informes municipales se describen "
            "como un recurso para miembros, por lo que esta página no extrae ni reproduce esos informes. Use este proceso:"
        ),
        "current_steps": (
            "Abra la página de datos de mercado de New Jersey Realtors y siga su enlace público de informes.",
            f"Seleccione el condado de {county}, el período exacto y la categoría de propiedad disponible.",
            "Anote la etiqueta de la fuente y el período antes de compararlo con otro informe.",
            f"Trate el resultado solo como contexto del condado; no lo asigne a {name} ni a una dirección individual.",
            "Vuelva a la fuente original antes de decidir, porque los informes públicos pueden revisarse o reemplazarse.",
        ),
        "njr_directory": "Página de datos de mercado de New Jersey Realtors",
        "njr_portal": "Abrir el portal público de informes por condado",
        "publication_note": (
            "Enlazamos a la fuente pública y no reproducimos sus tablas. "
            "No se implica afiliación ni respaldo."
        ),
        "source_heading": f"Fuentes para investigar {name}",
        "source_intro": (
            "Cada fuente responde una pregunta distinta. Conserve en sus notas la geografía, publicación, etiqueta y fecha de consulta."
        ),
        "official_title": f"Registros de {official}",
        "official_text": (
            "Use el sitio oficial del municipio para localizar la oficina fiscal, de construcción, planificación, zonificación o registros públicos. "
            "Confirme el bloque, lote y municipio legal para investigar una propiedad."
        ),
        "official_link": f"Abrir el sitio oficial de {name}",
        "acs_title": "Perfil de vivienda DP04 de la ACS del Censo",
        "acs_text": (
            "El perfil de cinco años 2024 Selected Housing Characteristics ofrece contexto de encuesta para la geografía indicada. "
            "Los valores de la ACS son estimaciones de esa publicación, no transacciones ni tasaciones vigentes."
        ),
        "acs_docs": "Cómo funcionan los Data Profiles de la ACS",
        "acs_profile": f"Abrir la búsqueda DP04 de {official}",
        "dca_title": "Construction Reporter del DCA de Nueva Jersey",
        "dca_text": (
            "La actividad de permisos y certificados informada por autoridades locales puede documentar construcción. "
            "No es inventario vigente de propiedades ni describe una venta futura."
        ),
        "dca_link": "Abrir Construction Reporter",
        "method_heading": "Método de comparación reproducible",
        "method_steps": (
            f"Defina primero la geografía: {official}, el condado de {county} o una propiedad.",
            "Anote la entidad, la tabla o informe, el período, la categoría seleccionada y la fecha de consulta.",
            "Compare solo etiquetas idénticas. Mantenga un promedio separado de una mediana y una estimación de encuesta separada de una transacción.",
            "Use registros municipales y del DCA para preguntas locales de propiedad o construcción; no convierta permisos en inventario.",
            "Use comparables vigentes y detalles de la propiedad para un análisis comparativo; no sustituya una cifra municipal o del condado.",
        ),
        "method_note": (
            "La fila estatal se presenta tal como fue publicada. Las demás secciones son un método y un mapa de fuentes directas, "
            "no una tabla copiada ni una valoración de propiedad. Compare viviendas solo según los criterios lícitos de propiedad "
            "y transacción que usted elija; esta página no clasifica personas ni vecindarios."
        ),
        "next_heading": "Continúe en la escala correcta",
        "town_cta": f"Leer la guía comunitaria de {name}",
        "county_cta": f"Leer la guía del condado de {county}",
        "value_cta": "Solicitar una valoración para una dirección",
        "contact_cta": "Preguntar sobre una fuente o propiedad",
        "record_heading": "Registro de fuentes, actualizaciones y correcciones",
        "record_text": (
            f"Todos los enlaces y la fila de {official} de esta página se revisaron el {REVIEWED_ON}. "
            "Cada entidad fuente controla sus definiciones, revisiones y disponibilidad."
        ),
        "correction": (
            "Correcciones: Si un enlace, fila de distrito, etiqueta, período o explicación geográfica requiere atención, "
            "envíe la URL de esta página y la fuente correspondiente mediante la sección de contacto."
        ),
        "footer_note": "Fuentes municipales revisadas y orientación específica para propiedades en Nueva Jersey.",
        "breadcrumbs": ("Inicio", "Investigación", f"Mercado de {name}"),
    }


def render_page(report: dict, sources: dict[str, dict], language: str) -> str:
    copy = page_copy(report, language)
    values = metric_values(report)
    name = report["name"]
    county = report["county"]
    town_slug = report["slug"].removeprefix("market-report-").removesuffix("-nj-2026")
    county_slug = county.lower()
    route = report["routes"][language]
    other_language = "es" if language == "en" else "en"
    other_route = report["routes"][other_language]
    canonical = SITE + route
    en_url = SITE + report["routes"]["en"]
    es_url = SITE + report["routes"]["es"]
    prefix = "/es" if language == "es" else ""
    home = "/es/" if language == "es" else "/"
    contact = "/es#contact" if language == "es" else "/contact"
    html_lang = "es" if language == "es" else "en"
    in_language = "es-US" if language == "es" else "en-US"
    if town_slug in INDEXABLE_TOWN_SLUGS:
        town_research_route = f"{prefix}/towns/{town_slug}"
        town_research_label = copy["town_guide"]
        town_research_cta = copy["town_cta"]
    else:
        town_research_route = "#source-heading"
        town_research_label = copy["official_sources_cta"]
        town_research_cta = copy["official_sources_cta"]

    article_schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": copy["title"],
        "description": copy["description"],
        "url": canonical,
        "mainEntityOfPage": canonical,
        "image": {
            "@type": "ImageObject",
            "url": f"{SITE}/images/hero.jpg",
            "width": 1400,
            "height": 933,
        },
        "inLanguage": in_language,
        "datePublished": report["publishedOn"],
        "dateModified": PAGE_MODIFIED_ON,
        "author": {
            "@type": "Person",
            "@id": f"{SITE}/#jorge-ramirez",
            "name": "Jorge Ramirez",
        },
        "publisher": {
            "@type": "Organization",
            "@id": f"{SITE}/#organization",
            "name": "The Jorge Ramirez Group",
            "url": SITE,
        },
    }
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": copy["breadcrumbs"][0], "item": SITE + home},
            {"@type": "ListItem", "position": 2, "name": copy["breadcrumbs"][1], "item": SITE + prefix + "/blog"},
            {"@type": "ListItem", "position": 3, "name": copy["breadcrumbs"][2], "item": canonical},
        ],
    }
    metrics = (
        (copy["line_items"], f"{int(values['lineItems']):,}", copy["line_items_help"], "line-items"),
        (copy["assessment"], f"${int(values['averageAssessment']):,}", copy["assessment_help"], "average-assessment"),
        (copy["tax_bill"], f"${int(values['averageTaxBill']):,}", copy["tax_help"], "average-tax-bill"),
        (copy["sales"], f"{int(values['numberOfSales']):,}", copy["sales_help"], "number-of-sales"),
        (copy["sales_price"], f"${float(values['averageSalesPrice']):,.2f}", copy["sales_price_help"], "average-sales-price"),
    )
    metric_cards = "\n".join(
        f'''            <div class="metric-card" data-source-field="{field}">
              <p class="metric-label">{esc(label)}</p>
              <p class="metric-value">{esc(value)}</p>
              <p>{esc(help_text)}</p>
            </div>'''
        for label, value, help_text, field in metrics
    )
    current_steps = "\n".join(f"              <li>{esc(item)}</li>" for item in copy["current_steps"])
    method_steps = "\n".join(f"              <li>{esc(item)}</li>" for item in copy["method_steps"])
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
  <meta name="llm-context" content="{esc(copy['llm'])}">
  <meta name="last-updated" content="{PAGE_MODIFIED_ON}">
  <meta name="geo.region" content="US-NJ">
  <meta name="geo.placename" content="{esc(name)}, New Jersey">
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
  <meta property="article:published_time" content="{esc(report['publishedOn'])}">
  <meta property="article:modified_time" content="{PAGE_MODIFIED_ON}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(copy["title"])}">
  <meta name="twitter:description" content="{esc(copy["description"])}">
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
  <script type="application/ld+json">{article_json}</script>
  <script type="application/ld+json">{breadcrumb_json}</script>
  <style>
    :root {{
      --black: #0A0A0A;
      --ink: #1A1A1A;
      --red: #C41230;
      --deep-red: #8B0D22;
      --gold: #B8962E;
      --light-gold: #D4AF5A;
      --paper: #F8F6F2;
      --ivory: #FAFAF8;
      --white: #FFFFFF;
      --muted: #5E5A54;
      --line: #E3DDD2;
      --display: 'Playfair Display', Georgia, serif;
      --body: 'Inter', sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; overflow-x: hidden; background: var(--ivory); color: var(--ink); font-family: var(--body); line-height: 1.7; }}
    p, li, a {{ overflow-wrap: anywhere; }}
    a {{ color: var(--deep-red); text-underline-offset: .18em; }}
    a:hover {{ color: var(--red); }}
    a:focus-visible, button:focus-visible {{ outline: 3px solid var(--gold); outline-offset: 3px; }}
    .skip-link {{ position: fixed; left: 1rem; top: -7rem; z-index: 100; min-height: 44px; padding: .65rem 1rem; background: var(--light-gold); color: var(--black); font-weight: 700; border-radius: 0 0 8px 8px; }}
    .skip-link:focus, .skip-link:focus-visible {{ top: 0; }}
    .site-nav {{ position: relative; z-index: 20; padding: 0; background: var(--black); border-bottom: 1px solid rgba(184,150,46,.42); }}
    .market-nav-inner {{ width: min(1320px, calc(100% - 2rem)); min-height: 76px; margin: 0 auto; display: flex; align-items: center; gap: 1rem; }}
    .market-brand {{ flex: 0 0 auto; white-space: nowrap; color: var(--white); font-family: var(--display); font-size: clamp(1rem, 2vw, 1.35rem); font-weight: 700; text-decoration: none; }}
    .market-brand span {{ color: var(--light-gold); }}
    .market-nav-links {{ margin-left: auto; display: flex; align-items: center; gap: .15rem; }}
    .market-nav-links a, .market-menu-button {{ min-height: 44px; display: inline-flex; align-items: center; justify-content: center; padding: .55rem .68rem; border-radius: 999px; color: var(--white); font-size: .84rem; font-weight: 600; text-decoration: none; }}
    .market-nav-links .market-nav-cta {{ background: linear-gradient(135deg, var(--red), var(--deep-red)); padding-inline: .9rem; }}
    .market-lang-link {{ border: 1px solid rgba(255,255,255,.52); }}
    .market-menu-button {{ display: none; margin-left: auto; border: 1px solid rgba(255,255,255,.48); background: transparent; font: inherit; cursor: pointer; }}
    .hero {{ position: relative; overflow: hidden; background: var(--ink); color: var(--white); }}
    .hero::after {{ content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 86% 18%, rgba(212,175,90,.22), transparent 34%), linear-gradient(128deg, transparent 0 58%, rgba(196,18,48,.17)); pointer-events: none; }}
    .hero-inner {{ position: relative; z-index: 1; width: min(1080px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(4.5rem, 9vw, 8rem) 0 clamp(4rem, 7vw, 6rem); }}
    .eyebrow {{ margin: 0 0 1rem; color: var(--light-gold); font-size: .78rem; font-weight: 700; letter-spacing: .17em; text-transform: uppercase; }}
    h1, h2, h3 {{ font-family: var(--display); line-height: 1.15; }}
    h1 {{ max-width: 920px; margin: 0; font-size: clamp(2.45rem, 7vw, 5.35rem); letter-spacing: -.025em; }}
    .dek {{ max-width: 780px; margin: 1.5rem 0 0; color: rgba(255,255,255,.86); font-size: clamp(1.05rem, 2vw, 1.28rem); }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: .65rem; margin-top: 1.75rem; }}
    .hero-meta span {{ min-height: 44px; display: inline-flex; align-items: center; padding: .55rem .85rem; border: 1px solid rgba(212,175,90,.48); border-radius: 999px; background: rgba(255,255,255,.05); font-size: .82rem; }}
    main {{ display: block; }}
    .content {{ width: min(1080px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(3rem, 7vw, 6rem) 0; }}
    .section {{ margin-bottom: clamp(3.75rem, 8vw, 6.75rem); }}
    .section > h2 {{ max-width: 840px; margin: 0 0 1rem; font-size: clamp(2rem, 5vw, 3.35rem); }}
    .lead {{ max-width: 800px; color: var(--muted); font-size: 1.08rem; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .9rem; margin-top: 1.8rem; }}
    .metric-card {{ min-width: 0; padding: 1.25rem; background: var(--white); border: 1px solid var(--line); border-top: 4px solid var(--gold); border-radius: 12px; box-shadow: 0 16px 42px rgba(26,26,26,.055); }}
    .metric-label {{ margin: 0; color: var(--deep-red); font-size: .76rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }}
    .metric-value {{ margin: .45rem 0 .7rem; color: var(--black); font-family: var(--display); font-size: clamp(1.45rem, 3vw, 2.15rem); font-weight: 700; line-height: 1.05; }}
    .metric-card p:last-child {{ margin: 0; color: var(--muted); font-size: .92rem; }}
    .notice {{ margin-top: 1.3rem; padding: 1.05rem 1.2rem; border-left: 4px solid var(--red); background: var(--paper); }}
    .button-row {{ display: flex; flex-wrap: wrap; gap: .8rem; margin-top: 1.4rem; }}
    .button {{ min-height: 48px; display: inline-flex; align-items: center; justify-content: center; padding: .72rem 1.1rem; border: 2px solid var(--red); border-radius: 999px; color: var(--deep-red); font-weight: 700; text-decoration: none; text-align: center; }}
    .button.btn-primary {{ border-color: var(--red); background: linear-gradient(135deg, var(--red), var(--deep-red)); color: var(--white); }}
    .scope-grid, .source-grid, .next-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin-top: 1.8rem; }}
    .scope-card, .source-card, .next-card {{ min-width: 0; padding: 1.45rem; background: var(--white); border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 14px 38px rgba(26,26,26,.045); }}
    .scope-card {{ border-top: 4px solid var(--gold); }}
    .scope-card h3, .source-card h3 {{ margin: 0 0 .65rem; font-size: 1.32rem; }}
    .scope-card p, .source-card p {{ margin: 0; color: var(--muted); }}
    .workflow {{ margin: 1.75rem 0; padding: 1.6rem 1.6rem 1.6rem 3.2rem; background: var(--white); border: 1px solid var(--line); border-top: 4px solid var(--gold); border-radius: 12px; box-shadow: 0 18px 50px rgba(26,26,26,.055); }}
    .workflow li {{ padding: .34rem 0 .34rem .35rem; }}
    .source-card {{ display: flex; flex-direction: column; }}
    .source-links {{ margin-top: auto; padding-top: 1rem; }}
    .source-links a {{ min-height: 44px; display: flex; align-items: center; font-weight: 700; }}
    .method {{ padding: clamp(1.65rem, 4vw, 2.6rem); background: var(--black); color: var(--white); border-radius: 16px; box-shadow: inset 0 0 0 1px rgba(212,175,90,.27); }}
    .method h2 {{ color: var(--white); }}
    .method ol {{ margin: 1.4rem 0; padding-left: 1.45rem; }}
    .method li {{ padding: .42rem 0 .42rem .3rem; }}
    .method-note {{ margin: 1.2rem 0 0; padding: 1rem 1.1rem; background: rgba(184,150,46,.14); border: 1px solid rgba(212,175,90,.38); border-radius: 10px; }}
    .next-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .next-card {{ min-height: 112px; display: flex; align-items: center; }}
    .next-card a {{ min-height: 44px; display: inline-flex; align-items: center; font-weight: 700; }}
    .record {{ padding: 1.45rem; background: var(--paper); border: 1px solid var(--line); border-left: 4px solid var(--deep-red); border-radius: 10px; }}
    .record h2 {{ margin-top: 0; font-size: 1.68rem; }}
    .record p:last-child {{ margin-bottom: 0; }}
    footer {{ background: var(--ink); color: rgba(255,255,255,.78); }}
    .footer-inner {{ width: min(1080px, calc(100% - 2rem)); margin: 0 auto; padding: 2.5rem 0; display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }}
    .footer-inner strong {{ color: var(--white); font-family: var(--display); }}
    .footer-inner p {{ margin: .35rem 0 0; }}
    .footer-inner a {{ min-height: 44px; display: inline-flex; align-items: center; color: var(--white); }}
    @media (max-width: 1280px) {{
      .market-menu-button {{ display: inline-flex; }}
      .market-nav-links {{ display: none; position: absolute; top: 76px; left: 0; right: 0; margin: 0; padding: .8rem 1rem 1.1rem; flex-direction: column; align-items: stretch; background: var(--black); border-top: 1px solid rgba(184,150,46,.34); }}
      .market-nav-links.open {{ display: flex; }}
      .market-nav-links a {{ width: 100%; }}
    }}
    @media (max-width: 980px) {{
      .metric-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    }}
    @media (max-width: 820px) {{
      .scope-grid, .source-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .next-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 600px) {{
      .market-brand {{ flex: 1 1 auto; min-width: 0; max-width: none; white-space: normal; line-height: 1.05; }}
      .market-menu-button {{ flex: 0 0 auto; }}
      .metric-grid, .scope-grid, .source-grid, .next-grid {{ grid-template-columns: minmax(0, 1fr); }}
      .hero-inner, .content {{ width: min(100% - 1.25rem, 1080px); }}
      .button-row {{ flex-direction: column; }}
      .button {{ width: 100%; }}
      .workflow {{ padding: 1.35rem 1.15rem 1.35rem 2.5rem; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">{esc(copy["skip"])}</a>
  <nav class="site-nav" aria-label="{esc(copy['nav_label'])}">
    <div class="market-nav-inner">
      <a class="market-brand" href="{home}">THE JORGE RAMIREZ <span>GROUP</span></a>
      <button class="market-menu-button" type="button" aria-expanded="false" aria-controls="primary-links">{esc(copy['menu'])}</button>
      <div class="market-nav-links" id="primary-links">
        <a href="{home}">{esc(copy['home'])}</a>
        <a href="{town_research_route}">{esc(town_research_label)}</a>
        <a href="{prefix}/counties/{county_slug}-county">{esc(copy['county_guide'])}</a>
        <a href="{prefix}/blog">{esc(copy['research'])}</a>
        <a href="{contact}">{esc(copy['contact'])}</a>
        <a class="market-lang-link" href="{other_route}" lang="{'es' if language == 'en' else 'en'}">{esc(copy['language'])}</a>
        <a class="market-nav-cta" href="{prefix}/home-valuation">{esc(copy['valuation'])}</a>
      </div>
    </div>
  </nav>

  <main id="main" tabindex="-1">
    <article data-geography-scope="municipality" data-publication-policy="reviewed-primary-sources">
      <header class="hero">
        <div class="hero-inner">
          <p class="eyebrow">{esc(copy['eyebrow'])}</p>
          <h1>{esc(copy['h1'])}</h1>
          <p class="dek" data-direct-answer="finalized-2025-treasury-row">{esc(copy['dek'])}</p>
          <div class="hero-meta">
            <span>{esc(copy['reviewed'])}: <time datetime="{REVIEWED_ON}">{REVIEWED_ON}</time></span>
            <span>{esc(copy['prepared'])}</span>
          </div>
        </div>
      </header>

      <div class="content">
        <section class="section" aria-labelledby="snapshot-heading">
          <h2 id="snapshot-heading">{esc(copy['snapshot_heading'])}</h2>
          <p class="lead">{esc(copy['snapshot_intro'])}</p>
          <div class="metric-grid">
{metric_cards}
          </div>
          <p class="notice">{esc(copy['final_note'])}</p>
          <div class="button-row">
            <a class="button btn-primary" href="{esc(sources['nj-treasury-average-residential-2025']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['read_row'])}</a>
            <a class="button" href="{esc(sources['nj-treasury-property-tax-statistics']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['stats_directory'])}</a>
          </div>
        </section>

        <section class="section" aria-labelledby="scope-heading">
          <h2 id="scope-heading">{esc(copy['scope_heading'])}</h2>
          <div class="scope-grid">
            <div class="scope-card"><h3>{esc(copy['municipality_label'])}</h3><p>{esc(copy['municipality_text'])}</p></div>
            <div class="scope-card"><h3>{esc(copy['county_label'])}</h3><p>{esc(copy['county_text'])}</p></div>
            <div class="scope-card"><h3>{esc(copy['property_label'])}</h3><p>{esc(copy['property_text'])}</p></div>
          </div>
        </section>

        <section class="section" aria-labelledby="current-heading">
          <h2 id="current-heading">{esc(copy['current_heading'])}</h2>
          <p class="lead">{esc(copy['current_intro'])}</p>
          <ol class="workflow">
{current_steps}
          </ol>
          <div class="button-row">
            <a class="button" href="{esc(sources['njr-market-data']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['njr_directory'])}</a>
            <a class="button btn-primary" href="{esc(sources['njr-public-county-portal']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['njr_portal'])}</a>
          </div>
          <p class="notice">{esc(copy['publication_note'])}</p>
        </section>

        <section class="section" aria-labelledby="source-heading">
          <h2 id="source-heading">{esc(copy['source_heading'])}</h2>
          <p class="lead">{esc(copy['source_intro'])}</p>
          <div class="source-grid">
            <div class="source-card">
              <h3>{esc(copy['official_title'])}</h3><p>{esc(copy['official_text'])}</p>
              <div class="source-links"><a href="{esc(report['officialMunicipalityUrl'])}" target="_blank" rel="noopener noreferrer">{esc(copy['official_link'])}</a></div>
            </div>
            <div class="source-card">
              <h3>{esc(copy['acs_title'])}</h3><p>{esc(copy['acs_text'])}</p>
              <div class="source-links">
                <a href="{esc(sources['census-acs-data-profiles']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['acs_docs'])}</a>
                <a href="{esc(report['acsHousingProfile'])}" target="_blank" rel="noopener noreferrer">{esc(copy['acs_profile'])}</a>
              </div>
            </div>
            <div class="source-card">
              <h3>{esc(copy['dca_title'])}</h3><p>{esc(copy['dca_text'])}</p>
              <div class="source-links"><a href="{esc(sources['nj-dca-construction-reporter']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['dca_link'])}</a></div>
            </div>
          </div>
        </section>

        <section class="section method" aria-labelledby="method-heading">
          <h2 id="method-heading">{esc(copy['method_heading'])}</h2>
          <ol>
{method_steps}
          </ol>
          <p class="method-note">{esc(copy['method_note'])}</p>
        </section>

        <section class="section" aria-labelledby="next-heading">
          <h2 id="next-heading">{esc(copy['next_heading'])}</h2>
          <div class="next-grid">
            <div class="next-card"><a href="{town_research_route}">{esc(town_research_cta)}</a></div>
            <div class="next-card"><a href="{prefix}/counties/{county_slug}-county">{esc(copy['county_cta'])}</a></div>
            <div class="next-card"><a href="{prefix}/home-valuation">{esc(copy['value_cta'])}</a></div>
            <div class="next-card"><a href="{contact}">{esc(copy['contact_cta'])}</a></div>
          </div>
        </section>

        <aside class="record" aria-labelledby="record-heading">
          <h2 id="record-heading">{esc(copy['record_heading'])}</h2>
          <p>{esc(copy['record_text'])}</p>
          <p>{esc(copy['correction'])}</p>
        </aside>
      </div>
    </article>
  </main>

  <footer>
    <div class="footer-inner">
      <div><strong>The Jorge Ramirez Group · Keller Williams Premier Properties</strong><p>{esc(copy['footer_note'])}</p></div>
      <a href="{contact}">{esc(copy['contact_cta'])}</a>
    </div>
  </footer>
  <script>
    (() => {{
      const menuButton = document.querySelector('.market-menu-button');
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
    sources = {item["id"]: item for item in document["sources"]}
    result: list[tuple[Path, str]] = []
    for report in sorted(document["reports"], key=lambda item: item["slug"]):
        for language in ("en", "es"):
            relative = Path(report["routes"][language].lstrip("/") + ".html")
            expected_parent = Path("es/blog") if language == "es" else Path("blog")
            if relative.parent != expected_parent or relative.stem not in EXPECTED:
                raise ValueError(f"refusing unexpected output path: {relative}")
            result.append((ROOT / relative, render_page(report, sources, language)))
    if len(result) != 22 or len({path for path, _ in result}) != 22:
        raise ValueError("renderer must produce exactly 22 unique files")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if a managed page is stale")
    mode.add_argument("--write", action="store_true", help="write stale managed pages")
    args = parser.parse_args()

    try:
        rendered = targets(load_manifest())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"Town market research manifest error: {error}", file=sys.stderr)
        return 2

    stale = [path for path, content in rendered if not path.exists() or path.read_text(encoding="utf-8") != content]
    if args.check:
        if stale:
            print("Stale Union and Morris town market research pages:")
            for path in stale:
                print(f"- {path.relative_to(ROOT)}")
            return 1
        print("22 Union and Morris town market research pages are current.")
        return 0

    for path, content in rendered:
        if path in stale:
            path.write_text(content, encoding="utf-8")
    print(f"Updated {len(stale)} Union and Morris town market research pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
