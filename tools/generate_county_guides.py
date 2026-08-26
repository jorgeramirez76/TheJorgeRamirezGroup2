#!/usr/bin/env python3
"""Render the six reviewed bilingual county service guides."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from local_search_links import links_for_county


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "county-guide-sources.json"
FACTS = ROOT / "data" / "site-facts.json"
REVIEWED_ON = "2026-08-26"
SITE = "https://thejorgeramirezgroup.com"


def esc(value: object, *, quote: bool = False) -> str:
    return html.escape(str(value), quote=quote)


def load_data() -> tuple[dict, dict]:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1:
        raise ValueError("county guide source manifest schemaVersion must be 1")
    if document.get("reviewedOn") != REVIEWED_ON:
        raise ValueError(f"county guide sources must be reviewed on {REVIEWED_ON}")
    if document.get("renderer") != "tools/generate_county_guides.py":
        raise ValueError("county guide source manifest points to another renderer")
    expected = {"union", "essex", "morris", "hudson", "middlesex", "somerset"}
    if {item.get("slug") for item in document.get("counties", [])} != expected:
        raise ValueError("county guide manifest must contain the six service counties")
    if {item.get("id") for item in document.get("sharedSources", [])} != {
        "njr-county-reports",
        "nj-tax-statistics",
        "nj-school-reports",
        "nj-transit-planner",
        "nj-locality-search",
    }:
        raise ValueError("county guide source inventory is incomplete")
    for source in document["sharedSources"]:
        for field in ("titleEs", "useEs", "limitEs"):
            if not str(source.get(field, "")).strip():
                raise ValueError(f"county guide source {source.get('id')} lacks {field}")
    return document, facts


def display_town(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def language_copy(language: str, county: dict) -> dict:
    name = county["name"]
    if language == "en":
        return {
            "lang": "en",
            "locale": "en_US",
            "county_name": f"{name} County",
            "nav_label": "Primary navigation",
            "breadcrumb_label": "Breadcrumb",
            "credentials_label": "Page credentials",
            "research_sequences_label": "Buyer and seller research sequences",
            "license_label": "NJ License",
            "title": f"{name} County NJ Real Estate Guide | Jorge Ramirez",
            "description": (
                f"Official-source {name} County NJ real estate guide for buyers and sellers, "
                "with town comparisons, public records, transit research, and local next steps."
            ),
            "llm": (
                f"Official-source {name} County, New Jersey real estate research guide from "
                "licensed NJ agent Jorge Ramirez. It separates county context, municipality "
                "records, and property-specific analysis and makes no price or timing promise."
            ),
            "skip": "Skip to main content",
            "nav": {
                "home": "Home",
                "buy": "Buy",
                "sell": "Sell",
                "communities": "Communities",
                "research": "Research",
                "language": "En Español",
                "value": "Get Home Value",
                "menu": "Toggle navigation menu",
                "call": "Call Jorge at 908-230-7844",
            },
            "crumbs": ("Home", "County guides", f"{name} County"),
            "eyebrow": f"{name} County · official-source real estate research",
            "h1": f"{name} County real estate guide for buyers and sellers",
            "hero": (
                "Use county reports, municipal records, state tax tables, district reports, "
                "and live transit tools before treating a regional headline as a fact about one property."
            ),
            "badges": (
                "Sources reviewed August 26, 2026",
                "NJ license #1754604",
                "Full-time Realtor since 2017",
            ),
            "market_cta": "Open the county market research guide",
            "source_cta": "Start with the public county reports",
            "hero_value_cta": "Request a property-specific value review",
            "scope_title": "Start with the geography, then narrow to the address",
            "scope_intro": (
                f"A {name} County statistic is regional context. It does not describe every "
                "municipality, neighborhood label, property type, or individual address."
            ),
            "scope_cards": (
                (
                    "County",
                    "Use a county report for a dated regional reference. Keep the period and property category attached to any figure you record.",
                ),
                (
                    "Municipality or locality",
                    "Confirm the legal municipality. A postal or neighborhood name may sit inside a differently named municipality with different records.",
                ),
                (
                    "Property",
                    "Verify the parcel, assessment, permits, condition, disclosures, and genuinely comparable sales for the address itself.",
                ),
            ),
            "research_title": "Five source checks that answer different questions",
            "research_cards": (
                ("Market reports", "Select the county, reporting period, and available property category. Do not reuse county figures as town-level facts."),
                ("Property-tax records", "Read the state table labels and the current municipal record. An average is not a parcel's bill or a valuation."),
                ("District reports", "Search the state report system, then confirm the current district and attendance assignment for the specific address."),
                ("Transit", "Test the actual origin, destination, departure time, transfers, and current service notices in NJ TRANSIT's tools."),
                ("Place identity", "Use state and county directories to distinguish a legal municipality from a locality, postal name, or informal neighborhood label."),
            ),
            "towns_title": f"Maintained {name} County local guides",
            "towns_intro": (
                "These are the maintained local guides currently published on this site, not a complete list of every county municipality. "
                "Use the official county directory for the full government list."
            ),
            "directory": "Open the official county directory",
            "all_towns": "Browse all maintained NJ town guides",
            "comparisons_title": f"Address-first comparisons connected to {name} County",
            "comparisons_intro": (
                "Use the same municipal, property-record, transportation, and personal-criteria worksheet for both places. "
                "These guides do not rank communities or substitute a broad place name for an address review."
            ),
            "buyer_title": "A buyer research sequence",
            "buyer_steps": (
                "Confirm the legal municipality and the property's exact address.",
                "Check live transit options for the trips that matter to you.",
                "Review current district reports and verify the address assignment directly.",
                "Read the current tax record, assessment history, and available permit records.",
                "Compare recent, property-specific sales and active alternatives with the same property type and relevant features.",
            ),
            "seller_title": "A seller pricing sequence",
            "seller_steps": (
                "Document the property's condition, updates, constraints, and timing priorities.",
                "Separate county headlines from municipality- and property-specific evidence.",
                "Compare recent closed sales, pending evidence when available, and current competing listings.",
                "Review presentation, disclosure, access, and launch decisions before selecting a list-price strategy.",
                "Recheck the evidence when market conditions or the competing inventory changes.",
            ),
            "buyer_cta": "Plan a NJ home search",
            "seller_cta": "Request a property-specific value review",
            "sources_title": "Source notebook",
            "sources_intro": (
                "Each source has a defined job and a limit. Open the original source, record its date and geography, "
                "and avoid extending it beyond what it actually reports."
            ),
            "use": "Use",
            "limit": "Limit",
            "reviewed": "Source links reviewed August 26, 2026. Recheck live records before making a decision.",
            "contact_eyebrow": "Property-specific help",
            "contact_title": f"Bring the {name} County research down to one address",
            "contact_text": (
                "Jorge can organize current comparable sales, property details, and your timing priorities into a review that is specific to the home—not a countywide promise."
            ),
            "contact_primary": "Ask Jorge about a property",
            "contact_secondary": "Call 908-230-7844",
            "footer_blurb": "Full-time Realtor with Keller Williams Premier Properties since 2017.",
            "footer_research": "Research",
            "footer_services": "Services",
            "footer_contact": "Contact",
            "privacy": "Privacy Policy",
            "rights": "All rights reserved.",
        }

    return {
        "lang": "es",
        "locale": "es_US",
        "county_name": f"Condado de {name}",
        "nav_label": "Navegación principal",
        "breadcrumb_label": "Ruta de navegación",
        "credentials_label": "Credenciales de la página",
        "research_sequences_label": "Secuencias de investigación para compradores y vendedores",
        "license_label": "Licencia de NJ",
        "title": f"Guía de Bienes Raíces: Condado de {name} NJ | Jorge Ramirez",
        "description": (
            f"Guía inmobiliaria del Condado de {name} para compradores y vendedores, con fuentes oficiales, "
            "comparaciones de pueblos, transporte y análisis de una propiedad."
        ),
        "llm": (
            f"Guía de investigación inmobiliaria del Condado de {name}, Nueva Jersey, con fuentes "
            "oficiales y Jorge Ramirez, agente con licencia en NJ. Distingue el contexto del condado, "
            "los registros municipales y el análisis de una propiedad; no promete precio ni plazo."
        ),
        "skip": "Saltar al contenido principal",
        "nav": {
            "home": "Inicio",
            "buy": "Comprar",
            "sell": "Vender",
            "communities": "Comunidades",
            "research": "Recursos",
            "language": "English",
            "value": "Valor de Mi Casa",
            "menu": "Abrir o cerrar el menú",
            "call": "Llamar a Jorge al 908-230-7844",
        },
        "crumbs": ("Inicio", "Guías de condados", f"Condado de {name}"),
        "eyebrow": f"Condado de {name} · investigación inmobiliaria con fuentes oficiales",
        "h1": f"Guía de bienes raíces del Condado de {name} para compradores y vendedores",
        "hero": (
            "Use informes del condado, registros municipales, tablas estatales de impuestos, informes de distritos "
            "y herramientas de transporte en vivo antes de tratar un titular regional como dato de una propiedad."
        ),
        "badges": (
            "Fuentes revisadas el 26 de agosto de 2026",
            "Licencia de NJ #1754604",
            "Realtor a tiempo completo desde 2017",
        ),
        "market_cta": "Abrir la guía de investigación del mercado",
        "source_cta": "Empezar con los informes públicos del condado",
        "hero_value_cta": "Solicitar una revisión específica del valor",
        "scope_title": "Empiece con la geografía y termine en la dirección",
        "scope_intro": (
            f"Una estadística del Condado de {name} sirve como contexto regional. No describe cada municipio, "
            "nombre de vecindario, tipo de propiedad ni dirección individual."
        ),
        "scope_cards": (
            ("Condado", "Use un informe del condado como referencia regional con fecha. Mantenga el período y la categoría de propiedad junto a cualquier dato."),
            ("Municipio o localidad", "Confirme el municipio legal. Un nombre postal o de vecindario puede pertenecer a un municipio con otro nombre y otros registros."),
            ("Propiedad", "Verifique la parcela, tasación fiscal, permisos, condición, divulgaciones y ventas realmente comparables de esa dirección."),
        ),
        "research_title": "Cinco verificaciones que responden preguntas distintas",
        "research_cards": (
            ("Informes de mercado", "Seleccione el condado, período y categoría disponible. No presente un dato del condado como si fuera municipal."),
            ("Registros de impuestos", "Lea las etiquetas de las tablas estatales y el registro municipal actual. Un promedio no es la factura ni el valor de una parcela."),
            ("Informes de distritos", "Busque en el sistema estatal y confirme directamente el distrito y la asignación vigente de la dirección."),
            ("Transporte", "Pruebe origen, destino, hora, transbordos y avisos actuales en las herramientas de NJ TRANSIT."),
            ("Identidad del lugar", "Use directorios estatales y del condado para distinguir un municipio legal de una localidad, nombre postal o vecindario informal."),
        ),
        "towns_title": f"Guías locales mantenidas del Condado de {name}",
        "towns_intro": (
            "Estas son las guías locales que este sitio mantiene actualmente, no una lista completa de todos los municipios del condado. "
            "Use el directorio oficial para la lista gubernamental completa."
        ),
        "directory": "Abrir el directorio oficial del condado",
        "all_towns": "Ver todas las guías de pueblos de NJ",
        "comparisons_title": f"Comparaciones por dirección relacionadas con el Condado de {name}",
        "comparisons_intro": (
            "Use la misma lista de registros municipales, propiedad, transporte y criterios personales para ambos lugares. "
            "Estas guías no clasifican comunidades ni sustituyen la revisión de una dirección."
        ),
        "buyer_title": "Secuencia de investigación para compradores",
        "buyer_steps": (
            "Confirme el municipio legal y la dirección exacta de la propiedad.",
            "Revise opciones de transporte en vivo para los viajes importantes para usted.",
            "Consulte los informes actuales del distrito y confirme directamente la asignación de la dirección.",
            "Lea el registro fiscal actual, el historial de tasación y los permisos disponibles.",
            "Compare ventas recientes y alternativas activas del mismo tipo de propiedad y con características relevantes.",
        ),
        "seller_title": "Secuencia de precios para vendedores",
        "seller_steps": (
            "Documente condición, mejoras, limitaciones y prioridades de tiempo de la propiedad.",
            "Separe los titulares del condado de la evidencia municipal y de la propiedad.",
            "Compare ventas cerradas recientes, evidencia pendiente cuando esté disponible y anuncios competidores actuales.",
            "Revise presentación, divulgaciones, acceso y lanzamiento antes de seleccionar una estrategia de precio.",
            "Vuelva a comprobar la evidencia cuando cambien las condiciones o el inventario competidor.",
        ),
        "buyer_cta": "Planear una búsqueda de vivienda en NJ",
        "seller_cta": "Solicitar una revisión específica del valor",
        "sources_title": "Cuaderno de fuentes",
        "sources_intro": (
            "Cada fuente tiene una función y un límite. Abra la fuente original, anote su fecha y geografía, "
            "y no la extienda más allá de lo que realmente informa."
        ),
        "use": "Uso",
        "limit": "Límite",
        "reviewed": "Enlaces revisados el 26 de agosto de 2026. Vuelva a comprobar los registros en vivo antes de decidir.",
        "contact_eyebrow": "Ayuda específica para una propiedad",
        "contact_title": f"Lleve la investigación del Condado de {name} a una dirección",
        "contact_text": (
            "Jorge puede organizar ventas comparables actuales, detalles de la propiedad y sus prioridades de tiempo en una revisión específica para la vivienda, no una promesa de todo el condado."
        ),
        "contact_primary": "Preguntar a Jorge sobre una propiedad",
        "contact_secondary": "Llamar al 908-230-7844",
        "footer_blurb": "Realtor a tiempo completo con Keller Williams Premier Properties desde 2017.",
        "footer_research": "Investigación",
        "footer_services": "Servicios",
        "footer_contact": "Contacto",
        "privacy": "Política de Privacidad",
        "rights": "Todos los derechos reservados.",
    }


def source_cards(document: dict, county: dict, copy: dict) -> str:
    sources = [
        {
            "title": county["directoryTitle"],
            "publisher": f"{county['name']} County",
            "url": county["directoryUrl"],
            "use": (
                "Use the county directory to locate the legal municipality and responsible public office."
                if copy["lang"] == "en"
                else "Use el directorio para ubicar el municipio legal y la oficina pública correspondiente."
            ),
            "limit": (
                "A directory identifies government resources; it does not describe a property's market value or condition."
                if copy["lang"] == "en"
                else "Un directorio identifica recursos gubernamentales; no describe el valor ni la condición de una propiedad."
            ),
        },
        *document["sharedSources"],
    ]
    cards = []
    for item in sources:
        title = item.get("titleEs", item["title"]) if copy["lang"] == "es" else item["title"]
        use = item.get("useEs", item["use"]) if copy["lang"] == "es" else item["use"]
        limit = item.get("limitEs", item["limit"]) if copy["lang"] == "es" else item["limit"]
        cards.append(
            f'''<article class="source-card">
              <p class="source-publisher">{esc(item["publisher"])}</p>
              <h3><a href="{esc(item["url"], quote=True)}" rel="noopener">{esc(title)}</a></h3>
              <p><strong>{esc(copy["use"])}:</strong> {esc(use)}</p>
              <p><strong>{esc(copy["limit"])}:</strong> {esc(limit)}</p>
            </article>'''
        )
    return "\n".join(cards)


def render(document: dict, facts: dict, county: dict, language: str) -> str:
    copy = language_copy(language, county)
    name = county["name"]
    slug = county["slug"]
    prefix = "/es" if language == "es" else ""
    own_route = f"{prefix}/counties/{slug}-county"
    en_route = f"/counties/{slug}-county"
    es_route = f"/es/counties/{slug}-county"
    county_hub_route = "/es/communities" if language == "es" else "/counties"
    town_hub_route = "/es/communities" if language == "es" else "/towns"
    alternate_route = en_route if language == "es" else es_route
    alternate_label = "English" if language == "es" else "ES"
    market_route = None
    if county.get("marketReportSlug"):
        market_route = f"{prefix}/blog/{county['marketReportSlug']}"

    town_inventory = facts["canonicalTownInventory"]["byCounty"][name]
    town_links = "\n".join(
        f'<a class="town-link" href="{prefix}/towns/{esc(town, quote=True)}">{esc(display_town(town))}</a>'
        for town in town_inventory
    )
    scope_cards = "\n".join(
        f'<article class="scope-card"><span>{index:02d}</span><h3>{esc(title)}</h3><p>{esc(text)}</p></article>'
        for index, (title, text) in enumerate(copy["scope_cards"], start=1)
    )
    research_cards = "\n".join(
        f'<article class="research-card"><h3>{esc(title)}</h3><p>{esc(text)}</p></article>'
        for title, text in copy["research_cards"]
    )
    buyer_steps = "\n".join(f"<li>{esc(step)}</li>" for step in copy["buyer_steps"])
    seller_steps = "\n".join(f"<li>{esc(step)}</li>" for step in copy["seller_steps"])
    badges = "\n".join(f"<span>{esc(item)}</span>" for item in copy["badges"])

    related_comparisons = links_for_county(name, language=language)
    comparison_markup = ""
    if related_comparisons:
        comparison_links = "\n".join(
            f'<a class="town-link" href="{esc(item["route"], quote=True)}">{esc(item["label"])}</a>'
            for item in related_comparisons
        )
        comparison_markup = f'''
    <section class="county-section" aria-labelledby="comparisons-title">
      <div class="county-wrap">
        <div class="section-heading"><span>{esc(copy["county_name"])}</span><h2 id="comparisons-title">{esc(copy["comparisons_title"])}</h2><p>{esc(copy["comparisons_intro"])}</p></div>
        <div class="town-grid">{comparison_links}</div>
      </div>
    </section>'''

    if market_route:
        research_link = (
            f'<a class="button button--outline" href="{market_route}">{esc(copy["market_cta"])}</a>'
        )
    else:
        research_link = (
            f'<a class="button button--outline" href="{document["sharedSources"][0]["url"]}" rel="noopener">'
            f'{esc(copy["source_cta"])}</a>'
        )
    hero_links = (
        f'<a class="button button--primary" href="{prefix}/home-valuation">{esc(copy["hero_value_cta"])}</a>'
        + research_link
        + f'<a class="button button--outline" href="{esc(county["directoryUrl"], quote=True)}" rel="noopener">{esc(copy["directory"])}</a>'
    )

    structured = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": SITE + own_route + "#webpage",
                "url": SITE + own_route,
                "name": copy["title"],
                "description": copy["description"],
                "inLanguage": "es-US" if language == "es" else "en-US",
                "dateModified": REVIEWED_ON,
                "about": {"@type": "AdministrativeArea", "name": f"{name} County, New Jersey"},
                "author": {"@id": SITE + "/#jorge-ramirez"},
                "isPartOf": {"@id": SITE + "/#website"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": copy["crumbs"][0], "item": SITE + ("/es" if language == "es" else "/")},
                    {"@type": "ListItem", "position": 2, "name": copy["crumbs"][1], "item": SITE + county_hub_route},
                    {"@type": "ListItem", "position": 3, "name": copy["crumbs"][2], "item": SITE + own_route},
                ],
            },
        ],
    }

    return f'''<!DOCTYPE html>
<html lang="{copy["lang"]}">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(copy["title"])}</title>
  <meta name="description" content="{esc(copy["description"], quote=True)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="author" content="Jorge Ramirez">
  <meta name="llm-context" content="{esc(copy["llm"], quote=True)}">
  <link rel="canonical" href="{SITE}{own_route}">
  <link rel="alternate" hreflang="en-US" href="{SITE}{en_route}">
  <link rel="alternate" hreflang="es-US" href="{SITE}{es_route}">
  <link rel="alternate" hreflang="es" href="{SITE}{es_route}">
  <link rel="alternate" hreflang="x-default" href="{SITE}{en_route}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE}{own_route}">
  <meta property="og:title" content="{esc(copy["title"], quote=True)}">
  <meta property="og:description" content="{esc(copy["description"], quote=True)}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta property="og:locale" content="{copy["locale"]}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(copy["title"], quote=True)}">
  <meta name="twitter:description" content="{esc(copy["description"], quote=True)}">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <style>
    :root{{--charcoal:#1A1A1A;--red:#C41230;--deep-red:#8B0D22;--gold:#B8962E;--ivory:#FAFAF8;--paper:#FFFFFF;--ink:#2C2C2C;--muted:#69645C;--line:#E7E0D4;--display:'Playfair Display',Georgia,serif;--body:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
    *{{box-sizing:border-box}} html{{scroll-behavior:smooth}} body.county-research-page{{margin:0;background:var(--ivory);color:var(--ink);font-family:var(--body);line-height:1.7}}
    .skip-link{{position:fixed;left:1rem;top:-5rem;z-index:3000;background:var(--paper);color:var(--charcoal);padding:.75rem 1rem;border:2px solid var(--gold)}} .skip-link:focus{{top:1rem}}
    .county-nav{{position:fixed;inset:0 0 auto;z-index:1000;background:rgba(10,10,10,.97);border-bottom:1px solid rgba(184,150,46,.25);box-shadow:0 10px 30px rgba(0,0,0,.18)}}
    .county-nav__inner{{width:min(1400px,94vw);min-height:86px;margin:auto;display:flex;align-items:center;gap:1.35rem}}
    .county-logo{{display:flex;align-items:center;margin-right:auto}} .county-logo img{{display:block;width:205px;height:auto;max-height:58px;object-fit:contain;background:#FFFFFF;padding:6px 10px;border-radius:4px}}
    .county-nav__links{{display:flex;align-items:center;gap:1.15rem;list-style:none;margin:0;padding:0}} .county-nav__links a{{color:#FFFFFF;text-decoration:none;font-weight:600;font-size:.91rem;white-space:nowrap}}
    .county-nav__links a:hover,.county-nav__links a:focus-visible{{color:#D4AF5A}} .county-nav__language{{display:inline-flex;min-width:36px;justify-content:center;padding:.42rem .58rem;border:1px solid rgba(255,255,255,.55);border-radius:999px}}
    .county-nav__value{{padding:.68rem 1rem;border-radius:999px;background:linear-gradient(135deg,var(--red),var(--deep-red));box-shadow:0 7px 20px rgba(196,18,48,.28)}}
    .county-menu{{display:none;width:44px;height:44px;border:1px solid rgba(255,255,255,.3);border-radius:8px;background:transparent;color:#FFFFFF;font-size:1.35rem}}
    main{{display:block}} .county-hero{{position:relative;overflow:hidden;padding:164px 5vw 88px;background:linear-gradient(120deg,rgba(0,0,0,.96),rgba(26,26,26,.93) 60%,rgba(139,13,34,.82));color:#FFFFFF}}
    .county-hero::after{{content:'';position:absolute;right:-12vw;bottom:-24vw;width:52vw;height:52vw;border:1px solid rgba(184,150,46,.25);border-radius:50%;box-shadow:0 0 0 7vw rgba(184,150,46,.035),0 0 0 14vw rgba(184,150,46,.025)}}
    .county-wrap{{position:relative;z-index:1;width:min(1160px,90vw);margin:0 auto}} .county-research-page .breadcrumbs{{position:static;top:auto;z-index:auto;width:auto;padding:0;background:transparent;backdrop-filter:none;box-shadow:none;transition:none;display:flex;flex-wrap:wrap;gap:.45rem;color:rgba(255,255,255,.66);font-size:.82rem;margin-bottom:2.3rem}} .breadcrumbs a{{color:#D4AF5A;text-decoration:none}}
    .county-eyebrow{{margin:0 0 1rem;color:#D4AF5A;font-size:.76rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}}
    .county-hero h1{{max-width:980px;margin:0;font-family:var(--display);font-size:clamp(2.75rem,6.2vw,5.7rem);font-weight:600;line-height:.99;letter-spacing:-.025em;color:#FFFFFF}}
    .county-hero__intro{{max-width:800px;margin:1.5rem 0 0;font-size:clamp(1.05rem,1.6vw,1.28rem);color:rgba(255,255,255,.82)}} .county-badges{{display:flex;flex-wrap:wrap;gap:.65rem;margin-top:1.7rem}} .county-badges span{{padding:.55rem .8rem;border:1px solid rgba(212,175,90,.42);border-radius:999px;background:rgba(0,0,0,.25);font-size:.72rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}
    .hero-actions,.cta-actions{{display:flex;flex-wrap:wrap;gap:.85rem;margin-top:2rem}} .button{{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:.8rem 1.2rem;border-radius:999px;text-decoration:none;font-weight:700;transition:transform .2s ease,box-shadow .2s ease}}
    .button:hover{{transform:translateY(-2px)}} .button--primary{{background:linear-gradient(135deg,var(--red),var(--deep-red));color:#FFFFFF;box-shadow:0 10px 24px rgba(196,18,48,.28)}} .button--outline{{border:1px solid rgba(255,255,255,.5);color:#FFFFFF}}
    .county-section{{padding:82px 0}} .county-section--paper{{background:var(--paper)}} .county-section--dark{{background:var(--charcoal);color:#FFFFFF}} .section-heading{{max-width:850px;margin-bottom:2.5rem}} .section-heading span{{display:block;margin-bottom:.65rem;color:var(--red);font-size:.75rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}}
    .county-section--dark .section-heading span{{color:#D4AF5A}} .section-heading h2{{margin:0 0 .85rem;font-family:var(--display);font-size:clamp(2rem,4vw,3.35rem);line-height:1.1;color:inherit}} .section-heading p{{margin:0;color:var(--muted);font-size:1.04rem}} .county-section--dark .section-heading p{{color:rgba(255,255,255,.7)}}
    .scope-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}} .scope-card{{position:relative;padding:1.7rem;background:var(--paper);border:1px solid var(--line);border-radius:12px;box-shadow:0 12px 34px rgba(0,0,0,.05)}} .scope-card span{{display:block;margin-bottom:1.2rem;color:var(--gold);font:700 .75rem/1 var(--body);letter-spacing:.12em}} .scope-card h3,.research-card h3,.source-card h3{{margin:0 0 .65rem;font-family:var(--display);font-size:1.35rem;line-height:1.2;color:var(--charcoal)}} .scope-card p,.research-card p,.source-card p{{margin:0;color:var(--muted)}}
    .research-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:rgba(184,150,46,.28);border:1px solid rgba(184,150,46,.28);border-radius:12px;overflow:hidden}} .research-card{{min-height:240px;padding:1.45rem;background:var(--charcoal)}} .research-card h3{{color:#FFFFFF}} .research-card p{{color:rgba(255,255,255,.68);font-size:.93rem}}
    .town-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.75rem}} .town-link{{display:flex;align-items:center;justify-content:space-between;min-height:54px;padding:.75rem 1rem;background:var(--paper);border:1px solid var(--line);border-radius:9px;color:var(--charcoal);text-decoration:none;font-weight:700}} .town-link::after{{content:'→';color:var(--red)}} .town-link:hover{{border-color:var(--gold);box-shadow:0 10px 24px rgba(0,0,0,.06)}} .directory-link{{display:inline-flex;margin-top:1.25rem;color:var(--deep-red);font-weight:800;text-decoration-thickness:1px;text-underline-offset:4px}}
    .sequence-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem}} .sequence-card{{padding:2rem;background:var(--paper);border-top:4px solid var(--red);border-radius:10px;box-shadow:0 16px 40px rgba(0,0,0,.07)}} .sequence-card--gold{{border-color:var(--gold)}} .sequence-card h2{{margin:0 0 1.2rem;font-family:var(--display);font-size:2rem;color:var(--charcoal)}} .sequence-card ol{{margin:0;padding-left:1.3rem}} .sequence-card li{{padding:.35rem 0 .55rem .35rem}} .sequence-card .button{{margin-top:1.35rem}}
    .source-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem}} .source-card{{padding:1.45rem;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.12);border-radius:10px}} .source-card h3,.source-card h3 a{{color:#FFFFFF}} .source-card p{{color:rgba(255,255,255,.68);font-size:.92rem}} .source-card p+p{{margin-top:.65rem}} .source-publisher{{margin-bottom:.65rem!important;color:#D4AF5A!important;font-size:.7rem!important;font-weight:800;letter-spacing:.11em;text-transform:uppercase}} .source-review{{margin:1.25rem 0 0;color:rgba(255,255,255,.62);font-size:.86rem}}
    .county-cta{{padding:78px 0;background:linear-gradient(135deg,var(--deep-red),var(--red));color:#FFFFFF}} .county-cta__inner{{display:grid;grid-template-columns:1fr auto;align-items:center;gap:2rem}} .county-cta h2{{margin:.3rem 0 .75rem;font-family:var(--display);font-size:clamp(2rem,4vw,3.3rem);line-height:1.07;color:#FFFFFF}} .county-cta p{{max-width:760px;margin:0;color:rgba(255,255,255,.8)}} .county-cta .county-eyebrow{{color:#FFFFFF;opacity:.75}} .county-cta .button--primary{{background:#FFFFFF;color:var(--deep-red);box-shadow:none}} .county-cta .button--outline{{color:#FFFFFF}}
    .county-footer{{background:#090909;color:rgba(255,255,255,.72);padding:60px 0 28px}} .footer-grid{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:2rem}} .footer-brand img{{width:230px;height:auto;background:#FFFFFF;padding:10px;border-radius:4px}} .footer-brand p{{max-width:370px}} .county-footer h2{{margin:0 0 1rem;color:#FFFFFF;font:600 1.2rem/1.2 var(--display)}} .county-footer a{{display:block;margin:.45rem 0;color:rgba(255,255,255,.72);text-decoration:none}} .county-footer a:hover{{color:#D4AF5A}} .footer-bottom{{margin-top:2.5rem;padding-top:1.25rem;border-top:1px solid rgba(255,255,255,.12);font-size:.82rem}}
    @media(max-width:1100px){{.county-nav__links{{gap:.75rem}}.county-nav__links a{{font-size:.82rem}}.research-grid{{grid-template-columns:repeat(3,1fr)}}.footer-grid{{grid-template-columns:2fr 1fr 1fr}}}}
    @media(max-width:820px){{.county-nav__inner{{min-height:76px}}.county-logo img{{width:176px}}.county-menu{{display:inline-grid;place-items:center}}.county-nav__links{{display:none;position:absolute;top:76px;left:0;right:0;flex-direction:column;align-items:stretch;padding:1.25rem 5vw 1.5rem;background:#1A1A1A;border-top:1px solid rgba(184,150,46,.25)}}.county-nav__links.is-open{{display:flex}}.county-nav__links a{{display:flex;min-height:44px;align-items:center;font-size:.94rem}}.county-nav__language,.county-nav__value{{justify-content:center}}.county-hero{{padding-top:130px}}.scope-grid,.sequence-grid,.county-cta__inner{{grid-template-columns:1fr}}.research-grid{{grid-template-columns:repeat(2,1fr)}}.source-grid{{grid-template-columns:1fr}}.footer-grid{{grid-template-columns:1fr 1fr}}}}
    @media(max-width:540px){{.county-wrap{{width:min(92vw,1160px)}}.county-hero{{padding:118px 4vw 68px}}.county-section{{padding:62px 0}}.research-grid{{grid-template-columns:1fr}}.research-card{{min-height:0}}.footer-grid{{grid-template-columns:1fr}}.hero-actions .button,.cta-actions .button{{width:100%}}}}
    @media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}*,*::before,*::after{{transition:none!important}}}}
  </style>
  <script type="application/ld+json">{json.dumps(structured, ensure_ascii=False, separators=(",", ":"))}</script>
</head>
<body class="county-research-page" data-source-review="{REVIEWED_ON}">
  <a class="skip-link" href="#main">{esc(copy["skip"])}</a>
  <nav class="county-nav" aria-label="{esc(copy["nav_label"], quote=True)}">
    <div class="county-nav__inner">
      <a class="county-logo" href="{prefix or '/'}" aria-label="The Jorge Ramirez Group">
        <picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="250" height="100"></picture>
      </a>
      <button class="county-menu" type="button" aria-label="{esc(copy["nav"]["menu"], quote=True)}" aria-expanded="false" aria-controls="county-navigation">☰</button>
      <ul class="county-nav__links" id="county-navigation">
        <li><a href="{prefix or '/'}">{esc(copy["nav"]["home"])}</a></li>
        <li><a href="{prefix}/buy-a-home">{esc(copy["nav"]["buy"])}</a></li>
        <li><a href="{prefix}/sell-your-home">{esc(copy["nav"]["sell"])}</a></li>
        <li><a href="{prefix}/communities">{esc(copy["nav"]["communities"])}</a></li>
        <li><a href="{prefix}/blog">{esc(copy["nav"]["research"])}</a></li>
        <li><a class="county-nav__language" href="{alternate_route}" hreflang="{'en-US' if language == 'es' else 'es-US'}" aria-label="{esc(copy["nav"]["language"], quote=True)}">{alternate_label}</a></li>
        <li><a href="tel:+19082307844" aria-label="{esc(copy["nav"]["call"], quote=True)}">908-230-7844</a></li>
        <li><a class="county-nav__value" href="{prefix}/home-valuation">{esc(copy["nav"]["value"])}</a></li>
      </ul>
    </div>
  </nav>
  <main id="main" tabindex="-1">
    <header class="county-hero">
      <div class="county-wrap">
        <nav class="breadcrumbs" aria-label="{esc(copy["breadcrumb_label"], quote=True)}"><a href="{prefix or '/'}">{esc(copy["crumbs"][0])}</a><span aria-hidden="true">/</span><a href="{county_hub_route}">{esc(copy["crumbs"][1])}</a><span aria-hidden="true">/</span><span>{esc(copy["crumbs"][2])}</span></nav>
        <p class="county-eyebrow">{esc(copy["eyebrow"])}</p>
        <h1>{esc(copy["h1"])}</h1>
        <p class="county-hero__intro">{esc(copy["hero"])}</p>
        <div class="county-badges" aria-label="{esc(copy["credentials_label"], quote=True)}">{badges}</div>
        <div class="hero-actions">{hero_links}</div>
      </div>
    </header>

    <section class="county-section" aria-labelledby="scope-title">
      <div class="county-wrap">
        <div class="section-heading"><span>{esc(copy["county_name"])}</span><h2 id="scope-title">{esc(copy["scope_title"])}</h2><p>{esc(copy["scope_intro"])}</p></div>
        <div class="scope-grid">{scope_cards}</div>
      </div>
    </section>

    <section class="county-section county-section--dark" aria-labelledby="research-title">
      <div class="county-wrap">
        <div class="section-heading"><span>{esc(copy["footer_research"])}</span><h2 id="research-title">{esc(copy["research_title"])}</h2></div>
        <div class="research-grid">{research_cards}</div>
      </div>
    </section>

    <section class="county-section county-section--paper" aria-labelledby="towns-title">
      <div class="county-wrap">
        <div class="section-heading"><span>{esc(copy["county_name"])}</span><h2 id="towns-title">{esc(copy["towns_title"])}</h2><p>{esc(copy["towns_intro"])}</p></div>
        <div class="town-grid">{town_links}</div>
        <a class="directory-link" href="{esc(county["directoryUrl"], quote=True)}" rel="noopener">{esc(copy["directory"])} →</a>
        <a class="directory-link" href="{town_hub_route}">{esc(copy["all_towns"])} →</a>
      </div>
    </section>
{comparison_markup}

    <section class="county-section" aria-label="{esc(copy["research_sequences_label"], quote=True)}">
      <div class="county-wrap sequence-grid">
        <article class="sequence-card"><h2>{esc(copy["buyer_title"])}</h2><ol>{buyer_steps}</ol><a class="button button--primary" href="{prefix}/buy-a-home">{esc(copy["buyer_cta"])}</a></article>
        <article class="sequence-card sequence-card--gold"><h2>{esc(copy["seller_title"])}</h2><ol>{seller_steps}</ol><a class="button button--primary" href="{prefix}/home-valuation">{esc(copy["seller_cta"])}</a></article>
      </div>
    </section>

    <section class="county-section county-section--dark" aria-labelledby="sources-title">
      <div class="county-wrap">
        <div class="section-heading"><span>{esc(copy["footer_research"])}</span><h2 id="sources-title">{esc(copy["sources_title"])}</h2><p>{esc(copy["sources_intro"])}</p></div>
        <div class="source-grid">{source_cards(document, county, copy)}</div>
        <p class="source-review">{esc(copy["reviewed"])}</p>
      </div>
    </section>

    <section class="county-cta">
      <div class="county-wrap county-cta__inner">
        <div><p class="county-eyebrow">{esc(copy["contact_eyebrow"])}</p><h2>{esc(copy["contact_title"])}</h2><p>{esc(copy["contact_text"])}</p></div>
        <div class="cta-actions"><a class="button button--primary" href="mailto:jorge.ramirez@kw.com">{esc(copy["contact_primary"])}</a><a class="button button--outline" href="tel:+19082307844">{esc(copy["contact_secondary"])}</a></div>
      </div>
    </section>
  </main>

  <footer class="county-footer">
    <div class="county-wrap">
      <div class="footer-grid">
        <section class="footer-brand"><picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="250" height="100" loading="lazy"></picture><p>{esc(copy["footer_blurb"])}</p><p>488 Springfield Avenue<br>Summit, NJ 07901<br>{esc(copy["license_label"])} #1754604</p></section>
        <section><h2>{esc(copy["footer_research"])}</h2><a href="{prefix}/communities">{esc(copy["nav"]["communities"])}</a><a href="{prefix}/blog">{esc(copy["nav"]["research"])}</a><a href="{prefix}/nj-train-map">NJ TRANSIT</a></section>
        <section><h2>{esc(copy["footer_services"])}</h2><a href="{prefix}/buy-a-home">{esc(copy["nav"]["buy"])}</a><a href="{prefix}/sell-your-home">{esc(copy["nav"]["sell"])}</a><a href="{prefix}/home-valuation">{esc(copy["nav"]["value"])}</a></section>
        <section><h2>{esc(copy["footer_contact"])}</h2><a href="tel:+19082307844">908-230-7844</a><a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a><a href="{prefix}/privacy-policy">{esc(copy["privacy"])}</a></section>
      </div>
      <div class="footer-bottom">© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties · {esc(copy["rights"])}</div>
    </div>
  </footer>
  <script>
    (() => {{
      const button = document.querySelector('.county-menu');
      const menu = document.getElementById('county-navigation');
      if (!button || !menu) return;
      button.addEventListener('click', () => {{
        const open = menu.classList.toggle('is-open');
        button.setAttribute('aria-expanded', String(open));
      }});
      menu.addEventListener('click', event => {{
        if (event.target.closest('a')) {{ menu.classList.remove('is-open'); button.setAttribute('aria-expanded', 'false'); }}
      }});
    }})();
  </script>
  <script defer src="/js/site-cta.js"></script>
  <script defer src="/js/lead-attribution.js"></script>
</body>
</html>
'''


def targets(document: dict, facts: dict) -> dict[Path, str]:
    output: dict[Path, str] = {}
    for county in document["counties"]:
        for language in ("en", "es"):
            prefix = Path("es") if language == "es" else Path()
            path = ROOT / prefix / "counties" / f"{county['slug']}-county.html"
            output[path] = render(document, facts, county, language)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    document, facts = load_data()
    rendered = targets(document, facts)
    stale = [
        path
        for path, expected in rendered.items()
        if not path.exists() or path.read_text(encoding="utf-8") != expected
    ]
    if args.check:
        if stale:
            print("Stale county guides:")
            for path in stale:
                print(path.relative_to(ROOT))
            return 1
        print(f"{len(rendered)} county guides are current.")
        return 0
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered[path], encoding="utf-8")
    print(f"Updated {len(stale)} of {len(rendered)} county guides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
