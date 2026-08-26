#!/usr/bin/env python3
"""Deterministically render the authority, FAQ, market, and RTF remediation cluster."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
MANIFEST_PATH = ROOT / "data" / "authority-tools-sources.json"


SPANISH_SOURCE_NOTES = {
    "nj-rtf-current": (
        "Tabla vigente estándar y de exención parcial, clases de propiedad cubiertas, responsabilidad legal y bandas porcentuales graduadas.",
        "La página no determina la contraprestación, clasificación, exención, fecha de registro ni cantidad específica de una escritura.",
    ),
    "nj-rtf-graduated-notice": (
        "Confirma la fecha de vigencia del 10 de julio de 2025, la responsabilidad del vendedor, el porcentaje sobre toda la contraprestación y las cinco bandas vigentes.",
        "La disposición transitoria de reembolso descrita en el aviso es histórica y esta herramienta no la calcula.",
    ),
    "njdobi-bulletin-24-11": (
        "Guía estatal vigente sobre acuerdos escritos de servicios de corretaje, compensación negociable, posibles pagadores y divulgaciones de agencia.",
        "No sustituye el acuerdo firmado por el consumidor ni el asesoramiento legal específico de la transacción.",
    ),
    "njrec-faq": (
        "Respalda la diferencia entre la Declaración de Información al Consumidor y un acuerdo separado que establece una relación de agencia.",
        "La guía general del regulador no decide los términos del contrato del consumidor.",
    ),
    "njdobi-consumer-real-estate": (
        "Directorio estatal oficial de orientación al consumidor y materiales de la Comisión de Bienes Raíces.",
        "El directorio no determina resultados de contratos, inspecciones, títulos, préstamos ni cierres.",
    ),
    "njdobi-buying-home": (
        "Respalda la afirmación limitada de que muchos compradores de Nueva Jersey contratan abogados aunque no sea obligatorio, además de conceptos generales de contrato, inspección y título.",
        "La publicación contiene referencias históricas a formularios federales; las divulgaciones hipotecarias vigentes se citan por separado al CFPB.",
    ),
    "cfpb-loan-estimate": (
        "Orientación federal vigente para comparar términos estimados del préstamo y costos de cierre en transacciones hipotecarias cubiertas.",
        "Una Estimación del Préstamo no es aprobación final, informe de título ni promesa de cierre.",
    ),
    "cfpb-closing-disclosure": (
        "Orientación federal vigente para revisar los términos y costos finales de la Divulgación de Cierre en hipotecas cubiertas.",
        "La divulgación no establece un plazo universal de cierre en Nueva Jersey ni resuelve asuntos de contrato o título.",
    ),
    "nj-property-tax": (
        "Punto de partida oficial para recursos de tasación, facturación, juntas de condado e impuesto a la propiedad en Nueva Jersey.",
        "Una página estatal no puede indicar la tasación, tasa, factura, resultado de apelación ni elegibilidad de una parcela.",
    ),
    "nj-fair-housing": (
        "Información oficial de Nueva Jersey y recursos de denuncia sobre discriminación en la vivienda.",
        "La página ofrece información pública general y no decide si una conducta específica infringió la ley.",
    ),
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def sources_for(data: dict, cluster: str) -> list[dict]:
    return [source for source in data["sources"] if cluster in source["clusters"]]


def source_cards(records: list[dict], *, lang: str) -> str:
    cards = []
    for record in records:
        use, limit = (
            SPANISH_SOURCE_NOTES[record["id"]]
            if lang == "es"
            else (record["use"], record["limit"])
        )
        cards.append(
            '<article class="at-source-card">'
            f'<a href="{esc(record["url"])}" target="_blank" rel="noopener noreferrer">'
            f'{esc(record["publisher"])} — {esc(record["title"])} ↗</a>'
            f'<p>{esc(use)} {esc(limit)}</p>'
            "</article>"
        )
    heading = "Official sources reviewed" if lang == "en" else "Fuentes oficiales revisadas"
    note = (
        f"Reviewed {REVIEWED_ON}. Open the agency page before acting because rules, forms, data, and program details can change."
        if lang == "en"
        else f"Revisadas el {REVIEWED_ON}. Abra la página del organismo antes de actuar porque las reglas, formularios, datos y programas pueden cambiar."
    )
    return (
        '<section class="at-section" aria-labelledby="sources-heading">'
        f'<p class="at-eyebrow">{esc(heading)}</p>'
        f'<h2 id="sources-heading">{esc(heading)}</h2>'
        f'<p class="at-section-intro">{esc(note)}</p>'
        f'<div class="at-sources">{"".join(cards)}</div>'
        "</section>"
    )


def schemas(
    *,
    route: str,
    title: str,
    description: str,
    lang: str,
    breadcrumb_label: str,
    faqs: list[tuple[str, str]] | None = None,
) -> str:
    canonical = SITE + route
    graph: list[dict] = [
        {
            "@type": "Organization",
            "@id": SITE + "/#organization",
            "name": "The Jorge Ramirez Group",
            "url": SITE + "/",
            "logo": {"@type": "ImageObject", "url": SITE + "/images/jorge-logo.jpg"},
        },
        {
            "@type": "WebSite",
            "@id": SITE + "/#website",
            "name": "The Jorge Ramirez Group",
            "url": SITE + "/",
            "publisher": {"@id": SITE + "/#organization"},
        },
        {
            "@type": "Person",
            "@id": SITE + "/#jorge-ramirez",
            "name": "Jorge Ramirez",
            "jobTitle": "New Jersey Real Estate Agent",
            "url": SITE + "/ai-authority",
            "worksFor": {"@id": SITE + "/#organization"},
        },
        {
            "@type": "WebPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": title,
            "description": description,
            "inLanguage": "es-US" if lang == "es" else "en-US",
            "dateModified": REVIEWED_ON,
            "isPartOf": {"@id": SITE + "/#website"},
        },
        {
            "@type": "Article",
            "@id": canonical + "#article",
            "headline": title,
            "description": description,
            "dateModified": REVIEWED_ON,
            "inLanguage": "es-US" if lang == "es" else "en-US",
            "mainEntityOfPage": {"@id": canonical + "#webpage"},
            "author": {"@id": SITE + "/#jorge-ramirez"},
            "publisher": {"@id": SITE + "/#organization"},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Inicio" if lang == "es" else "Home",
                    "item": SITE + ("/es" if lang == "es" else "/"),
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": breadcrumb_label,
                    "item": canonical,
                },
            ],
        },
    ]
    if faqs:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": canonical + "#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                    for question, answer in faqs
                ],
            }
        )
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def head(
    *,
    title: str,
    description: str,
    llm_context: str,
    canonical_route: str,
    lang: str,
    robots: str,
    schema: str | None = None,
    pair: tuple[str, str] | None = None,
) -> str:
    canonical = SITE + canonical_route
    alternates = ""
    if pair:
        en_route, es_route = pair
        alternates = (
            f'  <link rel="alternate" hreflang="en-US" href="{SITE}{en_route}">\n'
            f'  <link rel="alternate" hreflang="es-US" href="{SITE}{es_route}">\n'
            + (f'  <link rel="alternate" hreflang="es" href="{SITE}{es_route}">\n' if lang == "es" else "")
            + f'  <link rel="alternate" hreflang="x-default" href="{SITE}{en_route}">\n'
        )
    schema_block = f'  <script type="application/ld+json">{schema}</script>\n' if schema else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <meta name="robots" content="{esc(robots)}">
  <meta name="author" content="Jorge Ramirez">
  <meta name="last-updated" content="{REVIEWED_ON}">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="llm-context" content="{esc(llm_context)}">
  <link rel="canonical" href="{canonical}">
{alternates}  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta property="article:modified_time" content="{REVIEWED_ON}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/authority-tools.css">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
{schema_block}</head>"""


def header(*, lang: str, language_route: str | None) -> str:
    if lang == "es":
        links = (
            ("Inicio", "/es"),
            ("Comprar", "/es/buy-a-home"),
            ("Vender", "/es/sell-your-home"),
            ("Municipios", "/es/communities"),
            ("Recursos", "/es/blog"),
        )
        contact_label, contact_route, language_label = "Contacto", "/es/#contact", "English"
    else:
        links = (
            ("Home", "/"),
            ("Buy", "/buy-a-home"),
            ("Sell", "/sell-your-home"),
            ("Towns", "/communities"),
            ("Resources", "/blog"),
        )
        contact_label, contact_route, language_label = "Contact", "/#contact", "Español"
    items = "".join(f'<li><a href="{route}">{esc(label)}</a></li>' for label, route in links)
    language = (
        f'<li><a class="at-language" href="{language_route}" lang="{"en" if lang == "es" else "es"}">{language_label}</a></li>'
        if language_route
        else ""
    )
    menu_label = "Abrir menú" if lang == "es" else "Open menu"
    nav_label = "Navegación principal" if lang == "es" else "Primary navigation"
    skip = "Saltar al contenido" if lang == "es" else "Skip to content"
    return f"""
<body class="at-page">
  <a class="at-skip-link" href="#main">{skip}</a>
  <header class="at-header">
    <nav class="at-nav" aria-label="{nav_label}">
      <a class="at-brand" href="/{'es' if lang == 'es' else ''}">The Jorge Ramirez <span>&nbsp;Group</span></a>
      <button class="at-menu-button" id="atMenuButton" type="button" aria-controls="atNavList" aria-expanded="false" aria-label="{menu_label}"><span></span><span></span><span></span></button>
      <ul class="at-nav-list" id="atNavList">{items}<li><a class="at-nav-cta" href="{contact_route}">{contact_label}</a></li>{language}</ul>
    </nav>
  </header>"""


def footer(*, lang: str) -> str:
    if lang == "es":
        about = "Servicios inmobiliarios con licencia en Nueva Jersey. La información de estas guías es educativa y no sustituye asesoría legal, tributaria, financiera, de seguros ni de crédito."
        explore = (("Guía para compradores", "/es/nj-home-buyer-guide"), ("Vender una vivienda", "/es/sell-your-home"), ("Municipios", "/es/communities"))
        verify = (("Perfil y licencia", "/es/ai-authority"), ("Política de privacidad", "/es/privacy-policy"), ("Contacto", "/es/#contact"))
        headings = ("Explorar", "Verificar")
    else:
        about = "Licensed New Jersey real-estate services. These guides are educational and do not replace legal, tax, financial, insurance, lending, or other licensed advice."
        explore = (("Buyer guide", "/nj-home-buyer-guide"), ("Seller guide", "/nj-home-seller-guide"), ("Town guides", "/communities"))
        verify = (("Profile and license", "/ai-authority"), ("Privacy policy", "/privacy-policy"), ("Contact", "/#contact"))
        headings = ("Explore", "Verify")
    explore_links = "".join(f'<li><a href="{route}">{esc(label)}</a></li>' for label, route in explore)
    verify_links = "".join(f'<li><a href="{route}">{esc(label)}</a></li>' for label, route in verify)
    return f"""
  <footer class="at-footer">
    <div class="at-footer-inner">
      <section class="at-footer-about"><h2>The Jorge Ramirez Group</h2><p>{esc(about)}</p><p>Keller Williams Premier Properties · NJ License #1754604</p><p>488 Springfield Avenue, Summit, NJ 07901 · <a href="tel:+19082307844">908-230-7844</a></p></section>
      <nav aria-label="{headings[0]}"><h3>{headings[0]}</h3><ul class="at-footer-links">{explore_links}</ul></nav>
      <nav aria-label="{headings[1]}"><h3>{headings[1]}</h3><ul class="at-footer-links">{verify_links}</ul></nav>
    </div>
    <div class="at-footer-bottom">© 2026 The Jorge Ramirez Group. Equal Housing Opportunity.</div>
  </footer>
  <script>(function(){{const b=document.getElementById('atMenuButton');const n=document.getElementById('atNavList');if(!b||!n)return;b.addEventListener('click',function(){{const open=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',String(!open));n.classList.toggle('is-open',!open);}});}}());</script>
</body>
</html>
"""


def breadcrumb(*, lang: str, label: str) -> str:
    home_route = "/es" if lang == "es" else "/"
    home_label = "Inicio" if lang == "es" else "Home"
    return f'<nav class="at-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="{home_route}">{home_label}</a></li><li aria-hidden="true">/</li><li aria-current="page">{esc(label)}</li></ol></nav>'


def full_page(
    *,
    lang: str,
    route: str,
    title: str,
    description: str,
    llm_context: str,
    eyebrow: str,
    h1: str,
    deck: str,
    meta: list[str],
    body: str,
    breadcrumb_label: str,
    pair: tuple[str, str] | None,
    language_route: str | None,
    faqs: list[tuple[str, str]] | None = None,
) -> str:
    schema = schemas(
        route=route,
        title=title,
        description=description,
        lang=lang,
        breadcrumb_label=breadcrumb_label,
        faqs=faqs,
    )
    hero_meta = "".join(f"<span>{esc(item)}</span>" for item in meta)
    return (
        head(
            title=title,
            description=description,
            llm_context=llm_context,
            canonical_route=route,
            lang=lang,
            robots="index, follow, max-image-preview:large, max-snippet:-1",
            schema=schema,
            pair=pair,
        )
        + header(lang=lang, language_route=language_route)
        + f'<main id="main" tabindex="-1"><section class="at-hero"><div class="at-hero-inner"><p class="at-eyebrow">{esc(eyebrow)}</p><h1>{esc(h1)}</h1><p class="at-hero-deck">{esc(deck)}</p><div class="at-hero-meta">{hero_meta}</div></div></section><div class="at-shell">'
        + breadcrumb(lang=lang, label=breadcrumb_label)
        + f'<article class="at-content">{body}</article></div></main>'
        + footer(lang=lang)
    )


def fallback_page(record: dict) -> str:
    lang = record["lang"]
    if lang == "es":
        title = "Este recurso ahora tiene una página principal"
        description = "Esta URL se ha consolidado en una guía mantenida para evitar contenido duplicado y desactualizado."
        h1 = "Este recurso se ha trasladado"
        copy = "Use la página principal enlazada abajo para consultar la versión mantenida y sus fuentes actuales."
        cta = "Abrir el recurso vigente"
        llm = "Página no indexable de transición que dirige a la versión canónica mantenida del recurso."
    else:
        title = "This resource now has one maintained home"
        description = "This URL has been consolidated into a maintained guide to avoid duplicate or outdated information."
        h1 = "This resource has moved"
        copy = "Use the primary page below for the maintained version and its current source record."
        cta = "Open the current resource"
        llm = "Non-indexable transition page pointing to the maintained canonical version of this resource."
    return (
        head(
            title=title + " | The Jorge Ramirez Group",
            description=description,
            llm_context=llm,
            canonical_route=record["destination"],
            lang=lang,
            robots="noindex, follow",
        )
        + header(lang=lang, language_route=None)
        + f'<main id="main" tabindex="-1" class="at-fallback"><section class="at-fallback-card"><p class="at-eyebrow">The Jorge Ramirez Group</p><h1>{esc(h1)}</h1><p>{esc(copy)}</p><div class="at-button-row"><a class="at-button primary" href="{esc(record["destination"])}">{esc(cta)} →</a></div></section></main>'
        + footer(lang=lang)
    )


RTF_FAQS_EN = [
    (
        "Who is responsible for New Jersey's Realty Transfer Fee?",
        "The New Jersey Division of Taxation says the seller is statutorily responsible for the Realty Transfer Fee and, when applicable, the Graduated Percent Fee. A transaction professional should verify the deed, consideration, property class, exemptions, and recording requirements.",
    ),
    (
        "Does the Graduated Percent Fee apply at exactly $1,000,000?",
        "The current state page says the supplemental fee applies when consideration is more than $1,000,000 and only to listed property classes, subject to exemptions. This calculator shows zero graduated fee at exactly $1,000,000.",
    ),
    (
        "Does this calculator determine a partial or full exemption?",
        "No. It estimates the standard schedule and separately shows the potential Graduated Percent Fee for a covered transfer. It does not decide senior, disability, low- or moderate-income housing, relationship, deed, or other exemptions.",
    ),
    (
        "Does the estimate include every seller closing cost?",
        "No. It excludes recording charges, legal and title work, brokerage compensation, mortgage or lien payoff, repairs, credits, income-tax matters, and other transaction-specific items.",
    ),
]


RTF_FAQS_ES = [
    (
        "¿Quién es responsable de la Realty Transfer Fee de Nueva Jersey?",
        "La División de Tributación de Nueva Jersey dice que el vendedor es legalmente responsable de la Realty Transfer Fee y, cuando corresponda, de la Graduated Percent Fee. Un profesional de la transacción debe verificar la escritura, contraprestación, clasificación, exenciones y requisitos de registro.",
    ),
    (
        "¿La Graduated Percent Fee aplica exactamente en $1,000,000?",
        "La página estatal vigente dice que la tarifa suplementaria aplica cuando la contraprestación supera $1,000,000 y solo a las clases de propiedad enumeradas, sujeta a exenciones. Esta calculadora muestra cero exactamente en $1,000,000.",
    ),
    (
        "¿Esta calculadora determina una exención total o parcial?",
        "No. Estima la tabla estándar y muestra por separado la posible Graduated Percent Fee para una transferencia cubierta. No decide exenciones por edad, discapacidad, vivienda de ingresos bajos o moderados, parentesco, tipo de escritura u otras.",
    ),
    (
        "¿La estimación incluye todos los costos de cierre del vendedor?",
        "No. Excluye cargos de registro, trabajo legal y de título, compensación de corretaje, pago de hipotecas o gravámenes, reparaciones, créditos, asuntos de impuesto sobre ingresos y otros costos específicos.",
    ),
]


def faq_markup(faqs: list[tuple[str, str]]) -> str:
    return '<div class="at-faq">' + "".join(
        f'<details><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>'
        for question, answer in faqs
    ) + "</div>"


def rtf_page(data: dict, *, lang: str) -> str:
    if lang == "es":
        route = "/es/nj-realty-transfer-fee-calculator"
        pair = ("/nj-realty-transfer-fee-calculator", route)
        title = "Calculadora de Realty Transfer Fee de NJ | Tabla vigente"
        description = "Estime la Realty Transfer Fee estándar de NJ y la posible Graduated Percent Fee con la tabla estatal vigente, sus límites y fuentes oficiales."
        llm = "Calculadora educativa bilingüe basada en la tabla vigente de la División de Tributación de Nueva Jersey. Calcula la tarifa estándar por bandas de $500 y muestra por separado la posible tarifa porcentual para transferencias cubiertas sobre $1 millón; no determina exenciones ni la cantidad legal adeudada."
        eyebrow = "Herramienta basada en la fuente estatal vigente"
        h1 = "Calculadora de Realty Transfer Fee de Nueva Jersey"
        deck = "Use la contraprestación de la escritura para una estimación de planificación de la tabla estándar y vea por separado la posible tarifa porcentual para ciertas transferencias sobre $1 millón."
        breadcrumb_label = "Calculadora RTF de NJ"
        language_route = "/nj-realty-transfer-fee-calculator"
        faqs = RTF_FAQS_ES
        calculator = """
        <section class="at-calculator" aria-labelledby="calculator-heading">
          <h2 id="calculator-heading">Estimar las tarifas estatales del vendedor</h2>
          <form id="rtfCalculator" data-lang="es" novalidate>
            <label for="consideration">Contraprestación indicada en la escritura</label>
            <div class="at-field-row"><div class="at-money-field"><span aria-hidden="true">$</span><input id="consideration" name="consideration" type="number" inputmode="decimal" min="0" step="0.01" autocomplete="off" aria-describedby="considerationHelp calculationError"></div><button class="at-calculate" type="submit">Calcular</button></div>
            <p class="at-help" id="considerationHelp">Esta herramienta supone una transacción estándar no exenta. En algunos casos el Estado usa otra base de cálculo.</p>
            <p class="at-error" id="calculationError" role="alert"></p>
          </form>
          <div class="at-results" id="rtfResults" aria-live="polite">
            <div class="at-result"><span>RTF estándar estimada</span><strong id="standardFee">—</strong></div>
            <div class="at-result"><span>Posible Graduated Percent Fee</span><strong id="graduatedFee">—</strong></div>
            <div class="at-result"><span>Total de planificación si ambas aplican</span><strong id="combinedFee">—</strong></div>
          </div>
          <p class="at-result-note" id="resultNote">Ingrese una cantidad para comenzar.</p>
        </section>"""
        lede = "El resultado no es una cotización de cierre ni una determinación legal o tributaria. Confirme el cálculo con el abogado, profesional de título o agente de cierre que revise la escritura y los formularios estatales."
        standard_intro = "La RTF estándar usa una tabla distinta según si la contraprestación total no supera $350,000 o la supera. La ley aplica cada tarifa por cada $500 o fracción dentro de la banda."
        scope_cards = (
            ("Lo que calcula", "La tabla estándar publicada y, si la cantidad supera $1 millón, la posible tarifa porcentual recta sobre la contraprestación total."),
            ("Lo que no decide", "Clasificación, exenciones, base alternativa, fecha de registro, formularios, reembolsos ni la obligación final de una escritura concreta."),
            ("Quién debe verificar", "El abogado, profesional de título o agente de cierre con la escritura, contrato, clasificación y formularios aplicables."),
        )
        section_labels = ("Cómo funciona la tabla", "Tabla estándar publicada", "Tarifa porcentual sobre $1 millón", "Límites importantes", "Preguntas frecuentes")
    else:
        route = "/nj-realty-transfer-fee-calculator"
        pair = (route, "/es/nj-realty-transfer-fee-calculator")
        title = "NJ Realty Transfer Fee Calculator | Current State Schedule"
        description = "Estimate standard NJ Realty Transfer Fee and the potential Graduated Percent Fee with the current state schedule, clear limits, and official sources."
        llm = "Bilingual educational calculator based on the current New Jersey Division of Taxation schedule. It calculates the standard fee in $500 bands and separately shows the potential graduated fee for covered transfers over $1 million; it does not determine exemptions or legal tax due."
        eyebrow = "Current state-source planning tool"
        h1 = "New Jersey Realty Transfer Fee Calculator"
        deck = "Enter the deed consideration for a planning estimate of the standard schedule, then see the potential graduated fee separately for certain covered transfers over $1 million."
        breadcrumb_label = "NJ RTF calculator"
        language_route = "/es/nj-realty-transfer-fee-calculator"
        faqs = RTF_FAQS_EN
        calculator = """
        <section class="at-calculator" aria-labelledby="calculator-heading">
          <h2 id="calculator-heading">Estimate the seller's state fees</h2>
          <form id="rtfCalculator" data-lang="en" novalidate>
            <label for="consideration">Consideration stated in the deed</label>
            <div class="at-field-row"><div class="at-money-field"><span aria-hidden="true">$</span><input id="consideration" name="consideration" type="number" inputmode="decimal" min="0" step="0.01" autocomplete="off" aria-describedby="considerationHelp calculationError"></div><button class="at-calculate" type="submit">Calculate</button></div>
            <p class="at-help" id="considerationHelp">This tool assumes a standard, non-exempt transaction. The State uses a different calculation basis in some circumstances.</p>
            <p class="at-error" id="calculationError" role="alert"></p>
          </form>
          <div class="at-results" id="rtfResults" aria-live="polite">
            <div class="at-result"><span>Estimated standard RTF</span><strong id="standardFee">—</strong></div>
            <div class="at-result"><span>Potential Graduated Percent Fee</span><strong id="graduatedFee">—</strong></div>
            <div class="at-result"><span>Planning total if both apply</span><strong id="combinedFee">—</strong></div>
          </div>
          <p class="at-result-note" id="resultNote">Enter an amount to begin.</p>
        </section>"""
        lede = "The result is not a closing quote or a legal or tax determination. Confirm it with the attorney, title professional, or settlement agent reviewing the deed and current state forms."
        standard_intro = "The standard RTF uses one schedule when total consideration is not over $350,000 and a different schedule when it is over $350,000. The statute applies each rate per $500 or fractional part within a band."
        scope_cards = (
            ("What it calculates", "The published standard schedule and, when consideration is over $1 million, the potential straight percentage applied to total consideration."),
            ("What it cannot decide", "Classification, exemptions, alternate basis, recording date, forms, refunds, or the final obligation for a particular deed."),
            ("Who should verify", "The attorney, title professional, or settlement agent with the deed, contract, property class, and applicable forms."),
        )
        section_labels = ("How the schedule works", "Published standard schedule", "Percentage fee over $1 million", "Important limits", "Frequently asked questions")

    cards = "".join(f'<article class="at-card"><h3>{esc(title_)}</h3><p>{esc(copy)}</p></article>' for title_, copy in scope_cards)
    if lang == "es":
        table_one = (("$0–$150,000", "$2.00"), ("Más de $150,000–$200,000", "$3.35"), ("Más de $200,000–$350,000", "$3.90"))
        table_two = (("$0–$150,000", "$2.90"), ("Más de $150,000–$200,000", "$4.25"), ("Más de $200,000–$550,000", "$4.80"), ("Más de $550,000–$850,000", "$5.30"), ("Más de $850,000–$1,000,000", "$5.80"), ("Más de $1,000,000", "$6.05"))
        graduated = (("Más de $1,000,000 y hasta $2,000,000", "1%"), ("Más de $2,000,000 y hasta $2,500,000", "2%"), ("Más de $2,500,000 y hasta $3,000,000", "2.5%"), ("Más de $3,000,000 y hasta $3,500,000", "3%"), ("Más de $3,500,000", "3.5%"))
        headers = ("Contraprestación total no mayor de $350,000", "Contraprestación total mayor de $350,000", "Banda", "Tarifa por cada $500 o fracción")
        graduated_copy = "Para escrituras presentadas para registro desde el 10 de julio de 2025, el Estado aplica una tarifa porcentual suplementaria a ciertas clases enumeradas cuando la contraprestación supera $1 millón. Es un porcentaje recto de la contraprestación total, no una tasa marginal."
        class_copy = "La página estatal enumera las clases 2 residencial; 3A agrícola solo cuando incluye una estructura residencial; 4A comercial, excepto industrial o apartamentos; y 4C cooperativas. Existen exenciones y formularios específicos."
    else:
        table_one = (("$0–$150,000", "$2.00"), ("Over $150,000–$200,000", "$3.35"), ("Over $200,000–$350,000", "$3.90"))
        table_two = (("$0–$150,000", "$2.90"), ("Over $150,000–$200,000", "$4.25"), ("Over $200,000–$550,000", "$4.80"), ("Over $550,000–$850,000", "$5.30"), ("Over $850,000–$1,000,000", "$5.80"), ("Over $1,000,000", "$6.05"))
        graduated = (("Over $1,000,000 through $2,000,000", "1%"), ("Over $2,000,000 through $2,500,000", "2%"), ("Over $2,500,000 through $3,000,000", "2.5%"), ("Over $3,000,000 through $3,500,000", "3%"), ("Over $3,500,000", "3.5%"))
        headers = ("Total consideration not over $350,000", "Total consideration over $350,000", "Band", "Rate per $500 or fraction")
        graduated_copy = "For deeds submitted for recording on or after July 10, 2025, the State applies a supplemental percentage fee to certain listed property classes when consideration is over $1 million. It is a straight percentage of total consideration, not a marginal rate."
        class_copy = "The state page lists Class 2 residential; Class 3A farm only when it includes a residential structure; Class 4A commercial other than industrial or apartments; and Class 4C cooperative units. Specific exemptions and forms exist."

    def schedule_table(caption: str, rows: tuple[tuple[str, str], ...]) -> str:
        rendered_rows = "".join(f"<tr><td>{esc(band)}</td><td>{esc(rate)}</td></tr>" for band, rate in rows)
        return f'<div class="at-table-wrap"><table class="at-table"><caption>{esc(caption)}</caption><thead><tr><th scope="col">{esc(headers[2])}</th><th scope="col">{esc(headers[3])}</th></tr></thead><tbody>{rendered_rows}</tbody></table></div>'

    graduated_rows = "".join(f"<tr><td>{esc(band)}</td><td>{esc(rate)}</td></tr>" for band, rate in graduated)
    home_cta_route = "/es/home-valuation" if lang == "es" else "/home-valuation"
    seller_cta_route = "/es/sell-your-home" if lang == "es" else "/nj-home-seller-guide"
    home_cta_label = "Valoración de vivienda" if lang == "es" else "Home valuation"
    seller_cta_label = "Guía del vendedor" if lang == "es" else "Seller guide"
    body = (
        f'<p class="at-lede">{esc(lede)}</p>{calculator}'
        f'<section class="at-section"><p class="at-eyebrow">{esc(section_labels[0])}</p><h2>{esc(section_labels[0])}</h2><p class="at-section-intro">{esc(standard_intro)}</p><div class="at-grid three">{cards}</div></section>'
        f'<section class="at-section"><p class="at-eyebrow">{esc(section_labels[1])}</p><h2>{esc(section_labels[1])}</h2><div class="at-grid">{schedule_table(headers[0], table_one)}{schedule_table(headers[1], table_two)}</div></section>'
        f'<section class="at-section"><p class="at-eyebrow">{esc(section_labels[2])}</p><h2>{esc(section_labels[2])}</h2><p class="at-section-intro">{esc(graduated_copy)}</p><div class="at-table-wrap"><table class="at-table"><caption>{esc(section_labels[2])}</caption><thead><tr><th scope="col">{esc(headers[2])}</th><th scope="col">%</th></tr></thead><tbody>{graduated_rows}</tbody></table></div><div class="at-notice"><strong>{esc(section_labels[3])}:</strong> {esc(class_copy)}</div></section>'
        f'<section class="at-section"><p class="at-eyebrow">FAQ</p><h2>{esc(section_labels[4])}</h2>{faq_markup(faqs)}</section>'
        + source_cards(sources_for(data, "rtf"), lang=lang)
        + f'<div class="at-button-row"><a class="at-button primary" href="{home_cta_route}">{home_cta_label}</a><a class="at-button secondary" href="{seller_cta_route}">{seller_cta_label}</a></div>'
        + '<script defer src="/js/nj-rtf-calculator.js"></script>'
    )
    return full_page(
        lang=lang,
        route=route,
        title=title,
        description=description,
        llm_context=llm,
        eyebrow=eyebrow,
        h1=h1,
        deck=deck,
        meta=[f"Reviewed {REVIEWED_ON}" if lang == "en" else f"Revisada el {REVIEWED_ON}", "NJ Division of Taxation", "Standard + graduated schedules" if lang == "en" else "Tablas estándar + porcentual"],
        body=body,
        breadcrumb_label=breadcrumb_label,
        pair=pair,
        language_route=language_route,
        faqs=faqs,
    )


FAQ_EN = [
    (
        "When does a New Jersey buyer need a written brokerage services agreement?",
        "New Jersey's 2024 law says a broker must enter a written brokerage services agreement before providing brokerage services or as soon as reasonably practical after beginning them. A separate MLS policy generally requires an agreement before an MLS participant tours a home with a buyer; an unrepresented consumer attending an open house is treated differently. Read the agreement before signing and ask a New Jersey attorney about legal terms.",
    ),
    (
        "Is buyer-agent compensation fixed by law?",
        "No. New Jersey's Bulletin 24-11 says the amount and rate are fully negotiable and not set by law. The agreement must state how compensation is calculated and can identify payment by a seller, buyer, third party, or compensation shared between brokerage firms.",
    ),
    (
        "Is a New Jersey buyer required to hire an attorney?",
        "State consumer guidance says many New Jersey buyers retain attorneys, but doing so is not required. Contract language and deadlines are transaction specific, so a licensed attorney—not a general webpage—should explain legal rights and obligations.",
    ),
    (
        "Is the Consumer Information Statement the same as a buyer-agency agreement?",
        "No. The New Jersey Real Estate Commission explains that the Consumer Information Statement is a disclosure and does not by itself create an agency relationship. The separate written agreement establishes the brokerage relationship and its terms.",
    ),
    (
        "How should a financed buyer compare mortgage costs?",
        "Compare written Loan Estimates for the same scenario and review rate, APR, points, credits, lender and third-party charges, projected payment, cash to close, and what can change. For a covered mortgage, compare the later Closing Disclosure against the Loan Estimate and ask the lender and settlement professionals about differences.",
    ),
    (
        "Are inspection, appraisal, title, and insurance the same thing?",
        "No. They serve different roles. Inspection examines condition within the contract process; appraisal supports a lender's collateral review; title work examines ownership and recorded interests; insurance addresses covered risks under its policy. The applicable contract, lender, attorney, title, inspection, and insurance documents control.",
    ),
    (
        "Who pays New Jersey's Realty Transfer Fee?",
        "The current New Jersey Division of Taxation page says the seller is statutorily responsible for the Realty Transfer Fee and the Graduated Percent Fee when it applies. Exemptions, consideration, property class, and deed facts still require transaction-specific review.",
    ),
    (
        "Can a statewide property-tax rate tell me a home's bill?",
        "No. Use the parcel assessment, the municipality's general tax rate, the official tax bill, and current local records. The effective rate is a statistical comparison measure, not the rate used to compute a specific bill. Assessment appeals challenge value, not the tax bill by itself.",
    ),
    (
        "How should buyers compare towns without fair-housing steering?",
        "Define neutral criteria such as budget, housing type, commute schedule, transit access, taxes, insurance, municipal services, and proximity to destinations. Review official school information directly rather than asking an agent to rank neighborhoods by protected-class composition or say which place is best for a particular kind of person.",
    ),
]


FAQ_ES = [
    (
        "¿Cuándo necesita un comprador de Nueva Jersey un acuerdo escrito de servicios de corretaje?",
        "La ley de Nueva Jersey de 2024 dice que el corredor debe celebrar un acuerdo escrito antes de prestar servicios de corretaje o tan pronto como sea razonablemente práctico después de iniciarlos. Una política separada del MLS generalmente exige un acuerdo antes de que un participante del MLS visite una vivienda con el comprador; una persona sin representación que asiste a una casa abierta recibe un trato distinto. Lea el acuerdo y consulte a un abogado de Nueva Jersey sobre sus términos legales.",
    ),
    (
        "¿La compensación del agente del comprador está fijada por ley?",
        "No. El Boletín 24-11 de Nueva Jersey dice que la cantidad y la tasa son totalmente negociables y no las fija la ley. El acuerdo debe explicar el cálculo y puede identificar pago por un vendedor, comprador, tercero o reparto entre firmas inmobiliarias.",
    ),
    (
        "¿Nueva Jersey exige que el comprador contrate a un abogado?",
        "La guía estatal dice que muchos compradores de Nueva Jersey contratan abogados, pero no es obligatorio. El contrato y sus plazos son específicos, por lo que un abogado con licencia—no una página general—debe explicar derechos y obligaciones legales.",
    ),
    (
        "¿La Declaración de Información al Consumidor equivale a un acuerdo de agencia del comprador?",
        "No. La Comisión de Bienes Raíces explica que esa declaración es una divulgación y por sí sola no crea una relación de agencia. El acuerdo escrito separado establece la relación de corretaje y sus términos.",
    ),
    (
        "¿Cómo debe comparar costos hipotecarios un comprador financiado?",
        "Compare Estimaciones del Préstamo escritas para el mismo escenario y revise tasa, APR, puntos, créditos, cargos, pago proyectado, efectivo para el cierre y qué puede cambiar. Para una hipoteca cubierta, compare después la Divulgación de Cierre y pregunte por las diferencias.",
    ),
    (
        "¿Inspección, tasación, título y seguro significan lo mismo?",
        "No. Cumplen funciones distintas. La inspección examina condición dentro del contrato; la tasación apoya la revisión de garantía del prestamista; el trabajo de título examina propiedad e intereses registrados; el seguro cubre riesgos según su póliza. Controlan los documentos aplicables y los profesionales responsables.",
    ),
    (
        "¿Quién paga la Realty Transfer Fee de Nueva Jersey?",
        "La página vigente de la División de Tributación dice que el vendedor es legalmente responsable de la Realty Transfer Fee y de la Graduated Percent Fee cuando aplica. Las exenciones, contraprestación, clase y escritura requieren revisión específica.",
    ),
    (
        "¿Una tasa estatal de impuesto a la propiedad indica la factura de una casa?",
        "No. Use la tasación de la parcela, la tasa general municipal, la factura oficial y los registros locales vigentes. La tasa efectiva es una medida estadística, no la tasa que calcula una factura específica. Una apelación cuestiona el valor tasado, no la factura por sí sola.",
    ),
    (
        "¿Cómo se comparan municipios sin incurrir en orientación discriminatoria?",
        "Defina criterios neutrales como presupuesto, tipo de vivienda, horario de viaje, transporte, impuestos, seguro, servicios municipales y proximidad a destinos. Consulte directamente la información escolar oficial en vez de pedir al agente que clasifique barrios por composición de clases protegidas o diga qué lugar es mejor para cierto tipo de persona.",
    ),
]


def faq_page(data: dict, *, lang: str) -> str:
    if lang == "es":
        route = "/es/nj-real-estate-questions-answers"
        pair = ("/nj-real-estate-questions-answers", route)
        title = "Preguntas de bienes raíces en NJ | Respuestas con fuentes"
        description = "Respuestas actuales sobre acuerdos del comprador, compensación, abogados, hipotecas, inspección, RTF, impuestos y vivienda justa en NJ."
        llm = "Preguntas frecuentes bilingües sobre transacciones inmobiliarias de Nueva Jersey, basadas en fuentes oficiales de NJDOBI, NJREC, NJ Taxation, CFPB y NJDCA, con límites claros y sin promesas de resultados."
        eyebrow = "Respuestas respaldadas por documentos oficiales"
        h1 = "Preguntas y respuestas sobre bienes raíces en Nueva Jersey"
        deck = "Empiece con la regla general, abra la fuente vigente y lleve las preguntas específicas al profesional autorizado que revisa su contrato, préstamo, título, impuestos o propiedad."
        lede = "Esta guía ofrece educación general. No es asesoramiento legal, tributario, financiero, de seguros, de crédito, inspección ni título y no puede determinar el resultado de una transacción."
        breadcrumb_label = "Preguntas inmobiliarias de NJ"
        language_route = "/nj-real-estate-questions-answers"
        faqs = FAQ_ES
        framework = (
            ("Regla", "Identifique qué dice la fuente estatal o federal y a qué situación se limita."),
            ("Documento", "Revise el acuerdo, divulgación, factura, informe o formulario que controla su caso."),
            ("Profesional", "Pida al abogado, prestamista, profesional de título, inspector, aseguradora o asesor tributario la conclusión dentro de su función."),
        )
        section_title = "Use cada respuesta como punto de verificación"
        faq_title = "Preguntas frecuentes"
    else:
        route = "/nj-real-estate-questions-answers"
        pair = (route, "/es/nj-real-estate-questions-answers")
        title = "NJ Real Estate Questions | Current Source-Backed Answers"
        description = "Current answers on NJ buyer agreements, compensation, attorneys, mortgages, inspection, RTF, property tax, and fair housing with official sources."
        llm = "Bilingual New Jersey real-estate FAQ grounded in current NJDOBI, NJREC, NJ Taxation, CFPB, and NJDCA sources, with explicit scope limits and no outcome claims."
        eyebrow = "Answers grounded in official documents"
        h1 = "New Jersey Real Estate Questions and Answers"
        deck = "Start with the general rule, open the current source, and take fact-specific questions to the licensed professional reviewing your contract, loan, title, taxes, or property."
        lede = "This guide is general education. It is not legal, tax, financial, insurance, lending, inspection, or title advice and cannot determine a transaction outcome."
        breadcrumb_label = "NJ real estate questions"
        language_route = "/es/nj-real-estate-questions-answers"
        faqs = FAQ_EN
        framework = (
            ("Rule", "Identify what the state or federal source says and the situation to which it is limited."),
            ("Document", "Review the signed agreement, disclosure, bill, report, or form controlling your facts."),
            ("Professional", "Ask the attorney, lender, title professional, inspector, insurer, or tax adviser for conclusions within that professional's role."),
        )
        section_title = "Use every answer as a verification checkpoint"
        faq_title = "Frequently asked questions"
    cards = "".join(f'<article class="at-card"><h3>{esc(name)}</h3><p>{esc(copy)}</p></article>' for name, copy in framework)
    body = (
        f'<p class="at-lede">{esc(lede)}</p>'
        f'<section class="at-section"><p class="at-eyebrow">Method</p><h2>{esc(section_title)}</h2><div class="at-grid three">{cards}</div></section>'
        f'<section class="at-section"><p class="at-eyebrow">FAQ</p><h2>{esc(faq_title)}</h2>{faq_markup(faqs)}</section>'
        + source_cards(sources_for(data, "faq"), lang=lang)
        + f'<div class="at-button-row"><a class="at-button primary" href="{"/es/#contact" if lang == "es" else "/#contact"}">{"Hablar sobre sus preguntas" if lang == "es" else "Discuss your questions"}</a><a class="at-button secondary" href="{"/es/nj-home-buyer-guide" if lang == "es" else "/nj-home-buyer-guide"}">{"Abrir la guía del comprador" if lang == "es" else "Open the buyer guide"}</a></div>'
    )
    return full_page(
        lang=lang,
        route=route,
        title=title,
        description=description,
        llm_context=llm,
        eyebrow=eyebrow,
        h1=h1,
        deck=deck,
        meta=[f"Reviewed {REVIEWED_ON}" if lang == "en" else f"Revisada el {REVIEWED_ON}", "NJDOBI · NJREC · NJ Taxation · CFPB", "English and Spanish" if lang == "en" else "Inglés y español"],
        body=body,
        breadcrumb_label=breadcrumb_label,
        pair=pair,
        language_route=language_route,
        faqs=faqs,
    )


MARKET_FAQS = [
    (
        "Does a statewide housing headline tell me whether to buy, sell, or wait?",
        "No. A useful decision needs the target county and property segment, current comparable properties, financing or sale terms, ownership costs, condition, and the person's timing and risk tolerance. Statewide data supplies context, not a transaction answer.",
    ),
    (
        "Which current New Jersey market data can the public verify?",
        "New Jersey Realtors publishes public state and county reports and says prior-month reports are generally uploaded by the eleventh of the current month. Its municipality reports require member access. New Jersey Taxation also publishes annual assessment, tax, and residential-sales files with year-specific limits.",
    ),
    (
        "What should a buyer test before acting?",
        "Compare the complete monthly and upfront budget, written lender scenarios, cash reserves, likely ownership horizon, property-specific taxes and insurance, repair capacity, target-area choices, and contract protections. A lender qualification amount is not the same as a personally sustainable budget.",
    ),
    (
        "What should a seller test before choosing timing?",
        "Review property condition, current comparable listings and closed sales, expected transaction costs, the next housing step, contract constraints, and the consequences of selling sooner or later. Replace a statewide prediction with a dated property-specific analysis.",
    ),
    (
        "Can this guide predict prices, rates, or the best month to transact?",
        "No. It does not forecast prices, interest rates, time on market, proceeds, or a closing date. Compare multiple scenarios and update them with current written documents before making a commitment.",
    ),
]


def market_page(data: dict) -> str:
    route = "/blog/nj-housing-market-2026-buy-sell-or-wait"
    title = "NJ Housing Market 2026 | A Buy, Sell, or Wait Framework"
    description = "Use current NJ state and county reports plus a property-specific budget, timing, condition, and risk review to decide whether to buy, sell, or wait."
    llm = "Source-backed New Jersey housing decision framework using current public state and county reports and CFPB consumer guidance. It does not predict prices, rates, timing, proceeds, or recommend a universal buy, sell, or wait answer."
    cards = (
        ("If you may buy", "Compare a personally sustainable total budget with current written loan scenarios, parcel taxes, insurance indications, repair capacity, target-area inventory, contract terms, and the length of time you may own the property."),
        ("If you may sell", "Build a dated property review from current competition, relevant closed sales, condition, preparation choices, written service terms, transaction costs, the next housing step, and timing constraints."),
        ("If you may wait", "Write down what waiting is expected to improve, what could worsen, how long you will reassess, and which evidence will trigger the next review. Do not treat a forecast as a promise."),
    )
    evidence = (
        ("State and county market reports", "Use the latest public New Jersey Realtors report for the relevant property type and county. Record the report period rather than calling any figure real time."),
        ("Property and municipal records", "Use official parcel, assessment, tax, permit, flood, zoning, and municipal sources for the actual property. A county trend cannot replace property due diligence."),
        ("Written transaction documents", "Replace planning assumptions with lender disclosures, contracts, professional reports, insurance quotes, title work, and settlement figures as they become available."),
    )
    cards_html = "".join(f'<article class="at-card"><h3>{esc(name)}</h3><p>{esc(copy)}</p></article>' for name, copy in cards)
    evidence_html = "".join(f'<article class="at-card"><h3>{esc(name)}</h3><p>{esc(copy)}</p></article>' for name, copy in evidence)
    body = (
        '<p class="at-lede">There is no responsible statewide answer to “buy, sell, or wait.” The useful question is which option fits the specific person, property, county segment, written terms, and time horizon after the current evidence is dated and checked.</p>'
        + '<section class="at-section"><p class="at-eyebrow">Three separate decisions</p><h2>Test the choice you actually face</h2><p class="at-section-intro">A market headline is only context. Use different evidence for a purchase, a sale, and a decision to postpone.</p><div class="at-grid three">' + cards_html + "</div></section>"
        + '<section class="at-section"><p class="at-eyebrow">Evidence hierarchy</p><h2>Move from broad context to the actual property</h2><div class="at-grid three">' + evidence_html + '</div><div class="at-notice"><strong>Data-date rule:</strong> The completed 2025 New Jersey Average Residential Statistics include sales columns. The published 2026 file was incomplete when reviewed and must not be treated as a complete current-sales source. Always read the year, column definitions, and report period.</div></section>'
        + '<section class="at-section"><p class="at-eyebrow">Decision record</p><h2>Write down assumptions before they become conclusions</h2><div class="at-grid"><article class="at-card"><h3>What is known now</h3><ul><li>Target county, towns, property type, and price range</li><li>Current income, savings, obligations, and housing costs</li><li>Property condition and likely professional investigations</li><li>Current written loan or sale scenarios</li></ul></article><article class="at-card"><h3>What still needs verification</h3><ul><li>Rate, insurance, tax, title, inspection, appraisal, and repair assumptions</li><li>Contract deadlines, representation terms, and transaction costs</li><li>Current comparable properties and county report period</li><li>The next review date and the evidence that could change the choice</li></ul></article></div></section>'
        + '<section class="at-section"><p class="at-eyebrow">FAQ</p><h2>Questions behind the headline</h2>' + faq_markup(MARKET_FAQS) + "</section>"
        + source_cards(sources_for(data, "market-decision"), lang="en")
        + '<div class="at-button-row"><a class="at-button primary" href="/#contact">Request a property-specific discussion</a><a class="at-button secondary" href="/blog/nj-property-tax-guide">Review NJ property-tax sources</a></div>'
    )
    return full_page(
        lang="en",
        route=route,
        title=title,
        description=description,
        llm_context=llm,
        eyebrow="A decision framework, not a forecast",
        h1="NJ Housing Market 2026: Buy, Sell, or Wait?",
        deck="Use current public reports for context, then decide from the property, written terms, complete budget, timing, and risks that apply to you.",
        meta=[f"Reviewed {REVIEWED_ON}", "Public state + county sources", "No price or rate forecast"],
        body=body,
        breadcrumb_label="NJ housing decision framework",
        pair=None,
        language_route=None,
        faqs=MARKET_FAQS,
    )


RTF_JS = r"""(function (root) {
  'use strict';

  const FIVE_HUNDRED_DOLLARS = 50000;
  const ONE_MILLION_DOLLARS = 100000000;

  function toCents(value) {
    if (typeof value === 'number') {
      return Number.isFinite(value) && value >= 0 ? Math.round(value * 100) : null;
    }
    const normalized = String(value || '').replace(/[$,\s]/g, '');
    if (!normalized || !/^\d+(?:\.\d{0,2})?$/.test(normalized)) return null;
    const amount = Number(normalized);
    return Number.isFinite(amount) && amount >= 0 ? Math.round(amount * 100) : null;
  }

  function feeForSchedule(considerationCents, schedule) {
    let feeCents = 0;
    let lower = 0;
    for (const tier of schedule) {
      const upper = tier.upperCents == null ? considerationCents : Math.min(considerationCents, tier.upperCents);
      const segment = Math.max(0, upper - lower);
      if (segment > 0) feeCents += Math.ceil(segment / FIVE_HUNDRED_DOLLARS) * tier.rateCents;
      if (tier.upperCents == null || considerationCents <= tier.upperCents) break;
      lower = tier.upperCents;
    }
    return feeCents;
  }

  function standardFeeCents(considerationCents) {
    if (!Number.isInteger(considerationCents) || considerationCents < 0) throw new TypeError('considerationCents must be a non-negative integer');
    if (considerationCents < 10000) return 0;
    const lowerSchedule = [
      { upperCents: 15000000, rateCents: 200 },
      { upperCents: 20000000, rateCents: 335 },
      { upperCents: 35000000, rateCents: 390 }
    ];
    const higherSchedule = [
      { upperCents: 15000000, rateCents: 290 },
      { upperCents: 20000000, rateCents: 425 },
      { upperCents: 55000000, rateCents: 480 },
      { upperCents: 85000000, rateCents: 530 },
      { upperCents: 100000000, rateCents: 580 },
      { upperCents: null, rateCents: 605 }
    ];
    return feeForSchedule(considerationCents, considerationCents <= 35000000 ? lowerSchedule : higherSchedule);
  }

  function graduatedPercentFeeCents(considerationCents) {
    if (!Number.isInteger(considerationCents) || considerationCents < 0) throw new TypeError('considerationCents must be a non-negative integer');
    if (considerationCents <= ONE_MILLION_DOLLARS) return 0;
    let basisPoints;
    if (considerationCents <= 200000000) basisPoints = 100;
    else if (considerationCents <= 250000000) basisPoints = 200;
    else if (considerationCents <= 300000000) basisPoints = 250;
    else if (considerationCents <= 350000000) basisPoints = 300;
    else basisPoints = 350;
    return Math.round((considerationCents * basisPoints) / 10000);
  }

  function calculate(value) {
    const considerationCents = toCents(value);
    if (considerationCents == null) return null;
    const standardCents = standardFeeCents(considerationCents);
    const graduatedCents = graduatedPercentFeeCents(considerationCents);
    return {
      considerationCents,
      standardCents,
      graduatedCents,
      combinedCents: standardCents + graduatedCents,
      graduatedAppliesByAmount: considerationCents > ONE_MILLION_DOLLARS
    };
  }

  const api = { toCents, standardFeeCents, graduatedPercentFeeCents, calculate };
  root.JRG_RTF_CALCULATOR = api;

  if (typeof document === 'undefined') return;
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('rtfCalculator');
    if (!form) return;
    const input = document.getElementById('consideration');
    const standard = document.getElementById('standardFee');
    const graduated = document.getElementById('graduatedFee');
    const combined = document.getElementById('combinedFee');
    const note = document.getElementById('resultNote');
    const error = document.getElementById('calculationError');
    const lang = form.getAttribute('data-lang') === 'es' ? 'es' : 'en';
    const money = new Intl.NumberFormat(lang === 'es' ? 'es-US' : 'en-US', { style: 'currency', currency: 'USD' });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      const result = calculate(input.value);
      if (!result) {
        error.textContent = lang === 'es' ? 'Ingrese una cantidad válida con hasta dos decimales.' : 'Enter a valid amount with no more than two decimal places.';
        standard.textContent = '—'; graduated.textContent = '—'; combined.textContent = '—';
        return;
      }
      error.textContent = '';
      standard.textContent = money.format(result.standardCents / 100);
      graduated.textContent = money.format(result.graduatedCents / 100);
      combined.textContent = money.format(result.combinedCents / 100);
      if (result.graduatedAppliesByAmount) {
        note.textContent = lang === 'es'
          ? 'La tarifa porcentual mostrada solo aplica si la propiedad está en una clase cubierta y no existe una exención. Confirme la escritura y los formularios vigentes.'
          : 'The graduated amount shown applies only when the property is in a covered class and no exemption applies. Confirm the deed and current forms.';
      } else {
        note.textContent = lang === 'es'
          ? 'La tarifa porcentual estatal comienza solo cuando la contraprestación supera $1,000,000; las exenciones y otras bases todavía requieren revisión.'
          : 'The state graduated fee begins only when consideration is over $1,000,000; exemptions and alternate bases still require review.';
      }
    });
  });
}(typeof globalThis !== 'undefined' ? globalThis : this));
"""


def outputs() -> dict[str, str]:
    data = manifest()
    rendered: dict[str, str] = {
        record["file"]: fallback_page(record)
        for record in data["consolidations"]
    }
    rendered.update(
        {
            "nj-realty-transfer-fee-calculator.html": rtf_page(data, lang="en"),
            "es/nj-realty-transfer-fee-calculator.html": rtf_page(data, lang="es"),
            "nj-real-estate-questions-answers.html": faq_page(data, lang="en"),
            "es/nj-real-estate-questions-answers.html": faq_page(data, lang="es"),
            "blog/nj-housing-market-2026-buy-sell-or-wait.html": market_page(data),
            "js/nj-rtf-calculator.js": RTF_JS,
        }
    )
    expected = set(data["managedFiles"])
    if expected != set(rendered):
        missing = sorted(expected - set(rendered))
        extra = sorted(set(rendered) - expected)
        raise RuntimeError(f"manifest/renderer mismatch: missing={missing}, extra={extra}")
    return rendered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if any managed output differs")
    args = parser.parse_args(argv)
    rendered = outputs()
    stale: list[str] = []
    for relative, expected in rendered.items():
        path = ROOT / relative
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != expected:
            stale.append(relative)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding="utf-8")
    if stale and args.check:
        print("stale managed files:")
        for relative in stale:
            print(f"- {relative}")
        return 1
    if stale:
        print(f"rendered {len(stale)} changed files; {len(rendered)} managed files are current")
    else:
        print(f"{len(rendered)} managed files are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
