#!/usr/bin/env python3
"""Render the bilingual property-search and town-research worksheets."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / "data" / "site-facts.json").read_text(encoding="utf-8"))
OUTPUTS = (
    "property-search.html",
    "es/property-search.html",
    "tools/market-comparison-widget.html",
    "es/tools/market-comparison-widget.html",
)

PALETTE_CSS = """
:root{--ink:#1A1A1A;--black:#0A0A0A;--red:#C41230;--dark-red:#8B0D22;--gold:#B8962E;--gold-light:#D4AF5A;--paper:#FAFAF8;--soft:#F8F6F2;--white:#FFFFFF;--muted:#5A5A5A;--line:#DDD8CF}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:'Inter',sans-serif;line-height:1.65}a{color:var(--dark-red)}a:hover{text-decoration-thickness:2px}.skip{position:absolute;left:-9999px;top:0;background:var(--white);color:var(--ink);padding:12px 16px;z-index:100}.skip:focus{left:0}.site-nav{background:var(--black);color:var(--white);min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:10px max(20px,5vw)}.brand{display:flex;align-items:center;gap:12px;color:var(--white);text-decoration:none;font-family:'Playfair Display',serif;font-weight:700}.brand img{width:112px;height:47px;object-fit:contain;background:var(--white);border-radius:4px}.nav-links{display:flex;align-items:center;gap:18px;flex-wrap:wrap}.nav-links a{color:var(--white);text-decoration:none;font-weight:600}.nav-links .call{background:var(--red);border-radius:999px;padding:10px 18px}.hero{background:linear-gradient(135deg,rgba(10,10,10,.95),rgba(10,10,10,.8));color:var(--white);padding:clamp(54px,8vw,92px) max(20px,5vw)}.wrap{width:min(1120px,100%);margin:0 auto}.eyebrow{color:var(--gold-light);font-size:.76rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase}.hero h1,h2,h3{font-family:'Playfair Display',serif}.hero h1{font-size:clamp(2.15rem,6vw,4rem);line-height:1.06;max-width:880px;margin:12px 0 18px}.hero p{max-width:760px;color:rgba(255,255,255,.82);font-size:1.05rem}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}.button{display:inline-flex;min-height:48px;align-items:center;justify-content:center;border:2px solid var(--red);border-radius:999px;background:var(--red);color:var(--white);padding:10px 22px;text-decoration:none;font-weight:800;cursor:pointer;font:inherit}.button:hover{background:var(--dark-red);border-color:var(--dark-red)}.button.secondary{background:transparent;border-color:var(--gold-light);color:var(--white)}.section{padding:clamp(48px,7vw,78px) max(20px,5vw)}.section.alt{background:var(--soft)}.section h2{font-size:clamp(1.75rem,4vw,2.55rem);line-height:1.16;margin:0 0 12px}.lede{max-width:780px;color:var(--muted);margin:0 0 30px}.notice{background:var(--white);border-left:5px solid var(--gold);box-shadow:0 12px 35px rgba(10,10,10,.07);padding:20px 22px;margin:0 0 30px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.card{background:var(--white);border:1px solid var(--line);border-radius:12px;padding:22px}.card h3{font-size:1.25rem;margin:0 0 8px}.card p{color:var(--muted);margin:0 0 12px}.card a{font-weight:700}.town-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.town-card{background:var(--white);border:1px solid var(--line);border-radius:12px;padding:20px}.town-card h3{margin:0 0 10px}.town-links{display:flex;gap:8px 14px;flex-wrap:wrap}.town-links a{font-weight:650}.source-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.source{background:var(--white);border:1px solid var(--line);padding:18px;border-radius:10px}.source strong{display:block}.source span{display:block;color:var(--muted);font-size:.93rem}.cta{background:var(--black);color:var(--white);text-align:center}.cta .lede{color:rgba(255,255,255,.75);margin-left:auto;margin-right:auto}.footer{background:#050505;color:rgba(255,255,255,.65);padding:28px max(20px,5vw);text-align:center;font-size:.88rem}.footer a{color:var(--gold-light)}
.worksheet-head{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:28px 0}.field{display:grid;gap:7px}.field label{font-weight:800}.field input,.field textarea{width:100%;min-height:48px;border:1px solid #9B958C;border-radius:8px;background:var(--white);color:var(--ink);padding:12px;font:inherit}.field textarea{min-height:112px;resize:vertical}.field input:focus,.field textarea:focus,.button:focus,a:focus{outline:3px solid var(--gold-light);outline-offset:3px}.compare-table{display:grid;gap:18px}.compare-row{background:var(--white);border:1px solid var(--line);border-radius:12px;padding:20px}.compare-row h3{margin:0 0 5px}.compare-row>p{margin:0 0 16px;color:var(--muted)}.compare-inputs{display:grid;grid-template-columns:1fr 1fr;gap:16px}.print-note{font-size:.9rem;color:var(--muted)}
@media(max-width:800px){.site-nav{align-items:flex-start}.nav-links a:not(.call){display:none}.grid,.town-grid,.source-list{grid-template-columns:1fr}.worksheet-head,.compare-inputs{grid-template-columns:1fr}.hero{padding-top:52px}}@media(max-width:380px){.brand span{display:none}.brand img{width:102px}.nav-links .call{padding:9px 12px;font-size:.85rem}.section,.hero{padding-left:16px;padding-right:16px}}
@media print{.site-nav,.actions,.cta,.footer,.skip{display:none!important}.hero{background:none;color:#000;padding:20px 0}.hero p{color:#333}.section{padding:18px 0}.compare-row{break-inside:avoid}.field input,.field textarea{border-color:#777}.eyebrow{color:#333}}
"""

OFFICIAL_SOURCES = (
    ("NJ TRANSIT trip planner", "https://www.njtransit.com/trip-planner-to"),
    ("NJDOE School Performance Reports", "https://www.nj.gov/education/schoolperformance/"),
    ("NJ Division of Taxation statistics", "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml"),
    ("FEMA Flood Map Service Center", "https://msc.fema.gov/portal/home"),
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def schema(title: str, canonical: str, breadcrumb: str) -> str:
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical,
                "url": canonical,
                "name": title,
                "isPartOf": {
                    "@type": "WebSite",
                    "name": FACTS["business"]["name"],
                    "url": "https://thejorgeramirezgroup.com/",
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thejorgeramirezgroup.com/"},
                    {"@type": "ListItem", "position": 2, "name": breadcrumb, "item": canonical},
                ],
            },
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def shell(*, lang: str, title: str, description: str, canonical: str, en_url: str, es_url: str, breadcrumb: str, body: str) -> str:
    spanish = lang == "es"
    home = "/es" if spanish else "/"
    sell = "/es/sell-your-home" if spanish else "/sell-your-home"
    buy = "/es/buy-a-home" if spanish else "/buy-a-home"
    search = "/es/property-search" if spanish else "/property-search"
    skip = "Saltar al contenido principal" if spanish else "Skip to main content"
    nav = ("Inicio", "Vender", "Comprar", "Buscar", "Llamar") if spanish else ("Home", "Sell", "Buy", "Search", "Call")
    llm_limit = (
        "No se ofrece inventario en vivo, clasificación, puntuación, pronóstico ni garantía de resultados."
        if spanish
        else "No live inventory, ranking, score, forecast, or outcome guarantee is provided."
    )
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
  <meta name="last-updated" content="2026-08-27">
  <meta name="ai-content-declaration" content="ai-assisted, source-checked">
  <meta name="llm-context" content="{esc(description)} {esc(llm_limit)}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="alternate" hreflang="en-US" href="{esc(en_url)}">
  <link rel="alternate" hreflang="es-US" href="{esc(es_url)}">
  <link rel="alternate" hreflang="es" href="{esc(es_url)}">
  <link rel="alternate" hreflang="x-default" href="{esc(en_url)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:image" content="https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <style>{PALETTE_CSS}</style>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <script type="application/ld+json">{schema(title, canonical, breadcrumb)}</script>
</head>
<body>
<a class="skip" href="#main">{skip}</a>
<nav class="site-nav" aria-label="Primary">
  <a class="brand" href="{home}"><img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="200" height="84"><span>The Jorge Ramirez Group</span></a>
  <div class="nav-links"><a href="{home}">{nav[0]}</a><a href="{sell}">{nav[1]}</a><a href="{buy}">{nav[2]}</a><a href="{search}">{nav[3]}</a><a class="call" href="tel:+19082307844">{nav[4]} 908-230-7844</a></div>
</nav>
<main id="main">{body}</main>
<footer class="footer">The Jorge Ramirez Group · Keller Williams Premier Properties · NJ License #1754604 · <a href="tel:+19082307844">908-230-7844</a> · <a href="/privacy-policy">Privacy</a></footer>
<script defer src="/js/site-cta.js"></script>
</body>
</html>
'''


def display_name(slug: str) -> str:
    return slug.replace("-", " ").title()


def town_cards(spanish: bool) -> str:
    groups = FACTS["canonicalTownInventory"]["byCounty"]
    cards: list[str] = []
    prefix = "/es" if spanish else ""
    for county, slugs in groups.items():
        links = "".join(
            f'<a href="{prefix}/towns/{esc(slug)}">{esc(display_name(slug))}</a>'
            for slug in slugs
        )
        county_label = f"Condado de {county}" if spanish else f"{county} County"
        cards.append(f'<article class="town-card"><h3>{esc(county_label)}</h3><div class="town-links">{links}</div></article>')
    return "".join(cards)


def source_cards(spanish: bool) -> str:
    descriptions = (
        ("Horarios, transbordos, alertas y estaciones vigentes.", "Current schedules, transfers, alerts, and station records."),
        ("Informes oficiales por escuela y distrito; confirma la dirección con el distrito.", "Official school and district reports; confirm address assignment with the district."),
        ("Estadísticas publicadas, tasas y archivos; distingue promedios de datos de una propiedad.", "Published statistics, rates, and files; distinguish averages from parcel facts."),
        ("Punto de partida federal para mapas; confirma seguro y riesgo con profesionales calificados.", "Federal map starting point; confirm insurance and risk with qualified professionals."),
    )
    cards: list[str] = []
    for (name, url), pair in zip(OFFICIAL_SOURCES, descriptions):
        label = {
            "NJ TRANSIT trip planner": "Planificador de NJ TRANSIT",
            "NJDOE School Performance Reports": "Informes escolares de NJDOE",
            "NJ Division of Taxation statistics": "Estadísticas de Tributación de NJ",
            "FEMA Flood Map Service Center": "Centro de mapas de inundación de FEMA",
        }.get(name, name) if spanish else name
        description = pair[0] if spanish else pair[1]
        cards.append(f'<div class="source"><a href="{esc(url)}" target="_blank" rel="noopener noreferrer"><strong>{esc(label)}</strong></a><span>{esc(description)}</span></div>')
    return "".join(cards)


def property_page(spanish: bool) -> str:
    if spanish:
        title = "Buscar Propiedades en NJ | Listados y Verificación"
        description = "Abre la búsqueda externa de listados de Keller Williams y verifica tránsito, impuestos, distrito, inundación y datos municipales para cada dirección."
        canonical = "https://thejorgeramirezgroup.com/es/property-search"
        body = f'''
<section class="hero"><div class="wrap"><div class="eyebrow">Búsqueda de propiedades en NJ</div><h1>Busca listados. Verifica cada dirección.</h1><p>Los enlaces abren el sitio externo de búsqueda de Keller Williams. Esta página no aloja un MLS ni afirma que un listado siga disponible. Usa los pasos siguientes para investigar la propiedad específica antes de decidir.</p><div class="actions"><a class="button" href="https://thejorgeramirezgroup.kw.com/listings-search/" target="_blank" rel="noopener noreferrer">Abrir búsqueda de listados</a><a class="button secondary" href="/es/tools/market-comparison-widget">Abrir hoja comparativa</a></div></div></section>
<section class="section"><div class="wrap"><h2>Enlaces rápidos por municipio</h2><p class="lede">Cada enlace aplica un filtro de ciudad en el sitio externo. Confirma el municipio, la dirección, el estado del listado y los datos de la propiedad en la fuente original.</p><div class="grid">{listing_cards(True)}</div></div></section>
<section class="section alt"><div class="wrap"><h2>Un proceso de verificación, no un ranking</h2><div class="notice"><strong>Ningún municipio es universalmente adecuado para cada comprador.</strong> Compara la vivienda, el presupuesto completo, la ruta real, los registros oficiales y tus prioridades. Los datos municipales o distritales no sustituyen los hechos de una dirección.</div><div class="grid"><article class="card"><h3>1. Identidad y condición</h3><p>Guarda dirección, bloque/lote, municipio, tipo de vivienda, divulgaciones, permisos, inspecciones y documentos de asociación aplicables.</p></article><article class="card"><h3>2. Costo completo</h3><p>Usa precio, préstamo escrito, impuestos de la parcela, seguro cotizado, cuotas, servicios, mantenimiento y reservas; no un promedio estatal.</p></article><article class="card"><h3>3. Ruta y registros</h3><p>Prueba el trayecto a la hora necesaria. Revisa distrito, zonificación, inundación y registros municipales con las autoridades correspondientes.</p></article></div></div></section>
<section class="section"><div class="wrap"><h2>Guías por condado</h2><p class="lede">Estas guías organizan fuentes públicas y preguntas de investigación; no sustituyen listados activos ni una revisión específica.</p><div class="town-grid">{town_cards(True)}</div></div></section>
<section class="section alt"><div class="wrap"><h2>Fuentes oficiales para abrir junto al listado</h2><div class="source-list">{source_cards(True)}</div></div></section>
<section class="section cta"><div class="wrap"><h2>¿Quieres revisar una propiedad específica?</h2><p class="lede">Comparte el enlace y tus prioridades. Jorge puede ayudarte a organizar preguntas de corretaje; los temas legales, fiscales, técnicos y de seguro deben dirigirse al profesional correspondiente.</p><div class="actions" style="justify-content:center"><a class="button" href="/es#contact">Contactar a Jorge</a></div></div></section>'''
        return shell(lang="es", title=title, description=description, canonical=canonical, en_url="https://thejorgeramirezgroup.com/property-search", es_url=canonical, breadcrumb="Buscar propiedades", body=body)

    title = "Search NJ Properties | Listings and Address Research"
    description = "Open the external Keller Williams listing search, then verify transit, parcel taxes, district, flood, and municipal records for each address."
    canonical = "https://thejorgeramirezgroup.com/property-search"
    body = f'''
<section class="hero"><div class="wrap"><div class="eyebrow">New Jersey property search</div><h1>Search listings. Verify every address.</h1><p>The links open the external Keller Williams listing-search website. This page does not host an MLS or claim that a listing remains available. Use the steps below to investigate the specific property before making a decision.</p><div class="actions"><a class="button" href="https://thejorgeramirezgroup.kw.com/listings-search/" target="_blank" rel="noopener noreferrer">Open listing search</a><a class="button secondary" href="/tools/market-comparison-widget">Open comparison worksheet</a></div></div></section>
<section class="section"><div class="wrap"><h2>Quick links by municipality</h2><p class="lede">Each link applies a city filter on the external site. Confirm municipality, address, listing status, and property facts in the original source.</p><div class="grid">{listing_cards(False)}</div></div></section>
<section class="section alt"><div class="wrap"><h2>A verification process, not a town ranking</h2><div class="notice"><strong>No municipality is universally right for every buyer.</strong> Compare the property, complete budget, actual route, official records, and your priorities. Municipality or district data cannot establish the facts for an address.</div><div class="grid"><article class="card"><h3>1. Identity and condition</h3><p>Save the address, block/lot, municipality, housing type, disclosures, permits, inspections, and applicable association documents.</p></article><article class="card"><h3>2. Complete cost</h3><p>Use price, written loan terms, parcel tax bill, insurance quote, dues, utilities, maintenance, and reserves—not a statewide average.</p></article><article class="card"><h3>3. Route and records</h3><p>Test the trip at the needed time. Check district assignment, zoning, flood mapping, and municipal records with the responsible authority.</p></article></div></div></section>
<section class="section"><div class="wrap"><h2>Research guides by county</h2><p class="lede">These guides organize public sources and research questions; they do not replace active listings or property-specific review.</p><div class="town-grid">{town_cards(False)}</div></div></section>
<section class="section alt"><div class="wrap"><h2>Official sources to open beside a listing</h2><div class="source-list">{source_cards(False)}</div></div></section>
<section class="section cta"><div class="wrap"><h2>Want to review a specific property?</h2><p class="lede">Share the listing and your priorities. Jorge can help organize brokerage questions; route legal, tax, inspection, engineering, insurance, and lending questions to the appropriate professional.</p><div class="actions" style="justify-content:center"><a class="button" href="/contact">Contact Jorge</a></div></div></section>'''
    return shell(lang="en", title=title, description=description, canonical=canonical, en_url=canonical, es_url="https://thejorgeramirezgroup.com/es/property-search", breadcrumb="Property research", body=body)


def listing_cards(spanish: bool) -> str:
    towns = (
        ("Summit", "Union"), ("Westfield", "Union"), ("Cranford", "Union"),
        ("Chatham", "Morris"), ("Madison", "Morris"), ("Montclair", "Essex"),
        ("Millburn", "Essex"), ("Maplewood", "Essex"), ("Hoboken", "Hudson"),
        ("Jersey City", "Hudson"), ("Woodbridge", "Middlesex"), ("Basking Ridge", "Somerset"),
    )
    output: list[str] = []
    for town, county in towns:
        query = town.replace(" ", "+")
        county_label = f"Condado de {county}" if spanish else f"{county} County"
        action = "Abrir filtro externo" if spanish else "Open external filter"
        output.append(f'<article class="card"><h3>{esc(town)}</h3><p>{esc(county_label)}</p><a href="https://thejorgeramirezgroup.kw.com/listings-search/?city={esc(query)}" target="_blank" rel="noopener noreferrer">{esc(action)}</a></article>')
    return "".join(output)


WORKSHEET_ROWS = (
    ("Property sample and date", "Record the listings or closed sales reviewed, source, time period, property type, condition, and exclusions.", "Muestra de propiedades y fecha", "Anota listados o ventas cerradas, fuente, período, tipo de vivienda, condición y exclusiones."),
    ("Complete housing cost", "Use property-specific price, parcel tax, written financing, insurance indication, dues, utilities, maintenance, and reserves.", "Costo total de vivienda", "Usa precio, impuesto de parcela, financiamiento escrito, indicación de seguro, cuotas, servicios, mantenimiento y reservas."),
    ("Commute and transportation", "Test the actual origin, destination, day, time, transfers, parking, fares, alerts, and last return option.", "Traslado y transporte", "Prueba origen, destino, día, hora, transbordos, estacionamiento, tarifas, alertas y último regreso."),
    ("School and district records", "Confirm the assigned district and school with the responsible authority; review the current NJDOE report in context.", "Registros escolares y de distrito", "Confirma distrito y escuela asignada con la autoridad; revisa el informe vigente de NJDOE en contexto."),
    ("Parcel, zoning, flood, and insurance", "Record block/lot, zoning source, municipal contacts, flood map date, insurer feedback, and unanswered questions.", "Parcela, zonificación, inundación y seguro", "Anota bloque/lote, fuente de zonificación, contactos municipales, fecha del mapa, respuesta del asegurador y dudas."),
    ("Condition and transaction documents", "Compare disclosures, permits, inspections, association records, title questions, contract terms, and planned work.", "Condición y documentos", "Compara divulgaciones, permisos, inspecciones, asociación, título, contrato y trabajos previstos."),
    ("Daily-life requirements", "Write measurable needs such as route, housing features, accessibility, parking, services, and maintenance capacity.", "Necesidades cotidianas", "Escribe necesidades medibles como ruta, vivienda, accesibilidad, estacionamiento, servicios y capacidad de mantenimiento."),
    ("Open questions and next evidence", "List what remains unverified, who can answer, the source to request, and the decision deadline.", "Preguntas y próxima evidencia", "Enumera lo no verificado, quién responde, la fuente por pedir y la fecha de decisión."),
)


def worksheet_rows(spanish: bool) -> str:
    output: list[str] = []
    for index, row in enumerate(WORKSHEET_ROWS, start=1):
        title, help_text = (row[2], row[3]) if spanish else (row[0], row[1])
        left = "Municipio A" if spanish else "Town A"
        right = "Municipio B" if spanish else "Town B"
        output.append(f'''<section class="compare-row"><h3>{index}. {esc(title)}</h3><p>{esc(help_text)}</p><div class="compare-inputs"><div class="field"><label for="row-{index}-a">{left}</label><textarea id="row-{index}-a" name="row-{index}-a"></textarea></div><div class="field"><label for="row-{index}-b">{right}</label><textarea id="row-{index}-b" name="row-{index}-b"></textarea></div></div></section>''')
    return "".join(output)


def comparison_page(spanish: bool) -> str:
    if spanish:
        title = "Comparar Municipios de NJ | Hoja Basada en Fuentes"
        description = "Compara dos municipios con tus propios datos y fuentes oficiales. Sin puntaje, ganador automático, cifras precargadas ni pronóstico."
        canonical = "https://thejorgeramirezgroup.com/es/tools/market-comparison-widget"
        body = f'''
<section class="hero"><div class="wrap"><div class="eyebrow">Hoja de investigación</div><h1>Compara dos municipios sin un ganador automático.</h1><p>Introduce tus propias direcciones, documentos, cotizaciones y fuentes fechadas. La hoja no calcula un puntaje, no precarga cifras y no recomienda un municipio.</p><div class="actions"><button class="button" type="button" onclick="window.print()">Imprimir o guardar PDF</button><button class="button secondary" type="button" data-clear>Limpiar hoja</button></div></div></section>
<section class="section"><form class="wrap" id="comparison-form"><h2>Define la comparación</h2><div class="worksheet-head"><div class="field"><label for="town-a">Municipio o dirección A</label><input id="town-a" name="town-a" autocomplete="off"></div><div class="field"><label for="town-b">Municipio o dirección B</label><input id="town-b" name="town-b" autocomplete="off"></div><div class="field"><label for="as-of">Fecha de fuentes</label><input id="as-of" name="as-of" type="date"></div><div class="field"><label for="decision">Pregunta de decisión</label><input id="decision" name="decision" placeholder="Ej.: ¿Qué propiedad cabe en nuestro presupuesto completo?"></div></div><div class="notice"><strong>Regla de evidencia:</strong> anota la URL o el documento, su fecha y lo que todavía no se ha confirmado. Los promedios municipales no describen automáticamente una propiedad.</div><div class="compare-table">{worksheet_rows(True)}</div><p class="print-note">Las entradas permanecen en esta página y no se envían al sitio. Usa Imprimir para guardar una copia antes de salir.</p></form></section>
<section class="section alt"><div class="wrap"><h2>Fuentes oficiales</h2><p class="lede">Usa la misma fecha, definición y tipo de propiedad para ambos lados. Confirma los hechos de cada dirección con la autoridad correspondiente.</p><div class="source-list">{source_cards(True)}</div></div></section>
<section class="section cta"><div class="wrap"><h2>¿Quieres una segunda revisión?</h2><p class="lede">Jorge puede ayudarte a organizar la comparación de vivienda y corretaje. Las preguntas legales, fiscales, técnicas, de seguro o préstamo corresponden al profesional indicado.</p><div class="actions" style="justify-content:center"><a class="button" href="/es#contact">Contactar a Jorge</a><a class="button secondary" href="/es/property-search">Abrir búsqueda</a></div></div></section>
<script>document.querySelector('[data-clear]').addEventListener('click',function(){{if(window.confirm('¿Limpiar todos los campos de esta hoja?'))document.getElementById('comparison-form').reset();}});</script>'''
        return shell(lang="es", title=title, description=description, canonical=canonical, en_url="https://thejorgeramirezgroup.com/tools/market-comparison-widget", es_url=canonical, breadcrumb="Comparar municipios", body=body)

    title = "Compare New Jersey Towns | Source-Based Research Worksheet"
    description = "Compare two New Jersey towns with your own property facts and official sources—no score, automatic winner, prefilled market figures, or forecast."
    canonical = "https://thejorgeramirezgroup.com/tools/market-comparison-widget"
    body = f'''
<section class="hero"><div class="wrap"><div class="eyebrow">Town research worksheet</div><h1>Compare two towns without an automatic winner.</h1><p>Enter your own addresses, documents, quotes, and dated sources. The worksheet does not calculate a score, prefill market figures, or recommend a town.</p><div class="actions"><button class="button" type="button" onclick="window.print()">Print or save PDF</button><button class="button secondary" type="button" data-clear>Clear worksheet</button></div></div></section>
<section class="section"><form class="wrap" id="comparison-form"><h2>Define the comparison</h2><div class="worksheet-head"><div class="field"><label for="town-a">Town or address A</label><input id="town-a" name="town-a" autocomplete="off"></div><div class="field"><label for="town-b">Town or address B</label><input id="town-b" name="town-b" autocomplete="off"></div><div class="field"><label for="as-of">Source as-of date</label><input id="as-of" name="as-of" type="date"></div><div class="field"><label for="decision">Decision question</label><input id="decision" name="decision" placeholder="Example: Which property fits our complete budget?"></div></div><div class="notice"><strong>Evidence rule:</strong> record the URL or document, its date, and what remains unconfirmed. Municipality averages do not automatically describe a property.</div><div class="compare-table">{worksheet_rows(False)}</div><p class="print-note">Entries remain in this page and are not submitted to the site. Use Print to save a copy before leaving.</p></form></section>
<section class="section alt"><div class="wrap"><h2>Official research sources</h2><p class="lede">Use the same date, definition, and property type on both sides. Confirm address facts with the responsible authority.</p><div class="source-list">{source_cards(False)}</div></div></section>
<section class="section cta"><div class="wrap"><h2>Want a second review?</h2><p class="lede">Jorge can help organize the housing and brokerage comparison. Direct legal, tax, inspection, engineering, insurance, and lending questions to the appropriate professional.</p><div class="actions" style="justify-content:center"><a class="button" href="/contact">Contact Jorge</a><a class="button secondary" href="/property-search">Open property search</a></div></div></section>
<script>document.querySelector('[data-clear]').addEventListener('click',function(){{if(window.confirm('Clear every field in this worksheet?'))document.getElementById('comparison-form').reset();}});</script>'''
    return shell(lang="en", title=title, description=description, canonical=canonical, en_url=canonical, es_url="https://thejorgeramirezgroup.com/es/tools/market-comparison-widget", breadcrumb="Town comparison worksheet", body=body)


def render() -> dict[str, str]:
    return {
        "property-search.html": property_page(False),
        "es/property-search.html": property_page(True),
        "tools/market-comparison-widget.html": comparison_page(False),
        "es/tools/market-comparison-widget.html": comparison_page(True),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = render()
    drift = [relative for relative, expected in outputs.items() if not (ROOT / relative).is_file() or (ROOT / relative).read_text(encoding="utf-8") != expected]
    if args.check:
        if drift:
            print("property research page drift: " + ", ".join(drift))
            return 1
        print("property research pages current: 4")
        return 0
    for relative, content in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("rendered property research pages: 4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
