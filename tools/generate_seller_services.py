#!/usr/bin/env python3
"""Render the reviewed bilingual New Jersey seller-service cluster."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "seller-service-sources.json"
COPY = ROOT / "data" / "seller-service-copy.json"
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
EXPECTED_SLUGS = {
    "sell-your-home",
    "how-we-sell-your-home",
    "expired-listing-help",
    "fsbo-help",
    "cash-offer-nj",
    "relocating-from-nj",
    "divorce-home-sale-nj",
    "sell-rental-property-nj",
}
EXPECTED_SOURCE_IDS = {
    "nj-dobi-24-11",
    "nj-treasury-rtf",
    "nj-property-condition-disclosure",
    "njdep-flood-disclosure",
    "epa-lead-disclosure",
    "nj-dca-landlord-tenant",
    "irs-like-kind-exchanges",
    "irs-publication-544",
    "njcourts-divorce",
}


def esc(value: object, *, quote: bool = False) -> str:
    return html.escape(str(value), quote=quote)


def validate_manifest(document: dict) -> None:
    if document.get("schemaVersion") != 1:
        raise ValueError("seller-service source schemaVersion must be 1")
    if document.get("reviewedOn") != REVIEWED_ON:
        raise ValueError(f"seller-service sources must be reviewed on {REVIEWED_ON}")
    if document.get("renderer") != "tools/generate_seller_services.py":
        raise ValueError("seller-service manifest points to another renderer")
    routes = document.get("routes")
    sources = document.get("sources")
    if not isinstance(routes, list) or {item.get("slug") for item in routes} != EXPECTED_SLUGS:
        raise ValueError("seller-service route inventory is incomplete")
    if not isinstance(sources, list) or {item.get("id") for item in sources} != EXPECTED_SOURCE_IDS:
        raise ValueError("seller-service source inventory is incomplete")
    source_ids = {item["id"] for item in sources}
    for source in sources:
        if not all(
            source.get(field)
            for field in ("publisher", "title", "url", "use", "limit", "useEs", "limitEs")
        ):
            raise ValueError(f"source {source.get('id')} is incomplete")
        if not source["url"].startswith("https://"):
            raise ValueError(f"source {source['id']} is not HTTPS")
    for route in routes:
        if not route.get("intent") or len(route.get("sourceIds", [])) < 3:
            raise ValueError(f"route {route.get('slug')} lacks intent or sources")
        if not set(route["sourceIds"]) <= source_ids:
            raise ValueError(f"route {route['slug']} references an unknown source")


def load_data() -> tuple[dict, dict]:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    copy = json.loads(COPY.read_text(encoding="utf-8"))
    validate_manifest(document)
    if copy.get("schemaVersion") != 1 or copy.get("reviewedOn") != REVIEWED_ON:
        raise ValueError("seller-service copy is not the reviewed schema")
    pages = copy.get("pages")
    if not isinstance(pages, dict) or set(pages) != EXPECTED_SLUGS:
        raise ValueError("seller-service copy route inventory is incomplete")
    required = {
        "title",
        "description",
        "llm",
        "eyebrow",
        "h1",
        "intro",
        "focusTitle",
        "focusIntro",
        "focusCards",
        "processTitle",
        "processIntro",
        "processSteps",
        "checklistTitle",
        "checklistIntro",
        "checklist",
        "optionsTitle",
        "optionsIntro",
        "options",
        "guidance",
        "faq",
        "ctaTitle",
        "ctaText",
        "serviceName",
    }
    for slug, translations in pages.items():
        if set(translations) != {"en", "es"}:
            raise ValueError(f"{slug} lacks one reviewed language")
        for language, values in translations.items():
            missing = required - set(values)
            if missing:
                raise ValueError(f"{slug}/{language} is missing {sorted(missing)}")
            if len(values["focusCards"]) != 3 or len(values["processSteps"]) != 4:
                raise ValueError(f"{slug}/{language} has an invalid card or step count")
            if len(values["checklist"]) != 6 or len(values["options"]) != 2 or len(values["faq"]) != 3:
                raise ValueError(f"{slug}/{language} has an invalid content count")
    return document, copy


COMMON = {
    "en": {
        "lang": "en",
        "locale": "en_US",
        "skip": "Skip to main content",
        "home": "Home",
        "buy": "Buy",
        "sell": "Sell",
        "communities": "Communities",
        "research": "Research",
        "language": "En Español",
        "languageShort": "ES",
        "value": "Get Home Value",
        "menu": "Toggle navigation menu",
        "call": "Call Jorge at 908-230-7844",
        "sellerServices": "Seller services",
        "badges": (
            "Sources reviewed August 26, 2026",
            "NJ license #1754604",
            "Full-time Realtor since 2017",
        ),
        "primary": "Request a property-specific review",
        "secondary": "Call 908-230-7844",
        "focusLabel": "Start with the property",
        "processLabel": "Working plan",
        "checklistLabel": "Prepare the evidence",
        "optionsLabel": "Compare the paths",
        "sourceLabel": "Official-source notebook",
        "sourceTitle": "What the public sources say—and what they do not",
        "sourceIntro": "Each source below answers a defined question. Open the original, check its current date and coverage, and keep legal or tax decisions with the appropriate professional.",
        "use": "Use",
        "limit": "Limit",
        "sourceReview": "Source links reviewed August 26, 2026. Recheck live forms, rules, and transaction facts before acting.",
        "faqLabel": "Common questions",
        "relatedLabel": "Related seller paths",
        "relatedTitle": "Continue with the question that matches the property",
        "relatedIntro": "These maintained pages separate different seller decisions instead of treating every sale the same.",
        "ctaLabel": "Property-specific next step",
        "disclaimer": "This page is general education, not legal or tax advice. A New Jersey real-estate attorney, tax professional, lender, title professional, or other qualified adviser can address matters outside a real-estate licensee's scope.",
        "footerBlurb": "Full-time Realtor with Keller Williams Premier Properties since 2017.",
        "footerResearch": "Research",
        "footerServices": "Services",
        "footerContact": "Contact",
        "privacy": "Privacy Policy",
        "rights": "All rights reserved.",
    },
    "es": {
        "lang": "es",
        "locale": "es_US",
        "skip": "Saltar al contenido principal",
        "home": "Inicio",
        "buy": "Comprar",
        "sell": "Vender",
        "communities": "Comunidades",
        "research": "Recursos",
        "language": "English",
        "languageShort": "EN",
        "value": "Valor de Mi Casa",
        "menu": "Abrir o cerrar el menú",
        "call": "Llamar a Jorge al 908-230-7844",
        "sellerServices": "Servicios para vendedores",
        "badges": (
            "Fuentes revisadas el 26 de agosto de 2026",
            "Licencia de NJ #1754604",
            "Realtor a tiempo completo desde 2017",
        ),
        "primary": "Solicitar una revisión de la propiedad",
        "secondary": "Llamar al 908-230-7844",
        "focusLabel": "Empezar con la propiedad",
        "processLabel": "Plan de trabajo",
        "checklistLabel": "Preparar la evidencia",
        "optionsLabel": "Comparar los caminos",
        "sourceLabel": "Cuaderno de fuentes oficiales",
        "sourceTitle": "Lo que dicen las fuentes públicas y lo que no dicen",
        "sourceIntro": "Cada fuente responde una pregunta definida. Abra el original, verifique su fecha y alcance, y lleve las decisiones legales o fiscales al profesional correspondiente.",
        "use": "Uso",
        "limit": "Límite",
        "sourceReview": "Enlaces revisados el 26 de agosto de 2026. Confirme formularios, reglas y datos vivos de la operación antes de actuar.",
        "faqLabel": "Preguntas comunes",
        "relatedLabel": "Caminos relacionados para vendedores",
        "relatedTitle": "Continúe con la pregunta que corresponde a la propiedad",
        "relatedIntro": "Estas páginas mantenidas separan decisiones distintas en vez de tratar todas las ventas de la misma manera.",
        "ctaLabel": "Próximo paso para la propiedad",
        "disclaimer": "Esta página ofrece educación general, no asesoría legal ni fiscal. Un abogado de bienes raíces de New Jersey, un profesional fiscal, un prestamista, un profesional de títulos u otro asesor calificado puede atender asuntos fuera del alcance de una licencia inmobiliaria.",
        "footerBlurb": "Realtor a tiempo completo con Keller Williams Premier Properties desde 2017.",
        "footerResearch": "Investigación",
        "footerServices": "Servicios",
        "footerContact": "Contacto",
        "privacy": "Política de Privacidad",
        "rights": "Todos los derechos reservados.",
    },
}


RELATED = {
    "sell-your-home": ["how-we-sell-your-home", "expired-listing-help", "cash-offer-nj", "relocating-from-nj"],
    "how-we-sell-your-home": ["sell-your-home", "expired-listing-help", "fsbo-help", "cash-offer-nj"],
    "expired-listing-help": ["sell-your-home", "how-we-sell-your-home", "fsbo-help", "cash-offer-nj"],
    "fsbo-help": ["sell-your-home", "how-we-sell-your-home", "expired-listing-help", "cash-offer-nj"],
    "cash-offer-nj": ["sell-your-home", "how-we-sell-your-home", "relocating-from-nj", "sell-rental-property-nj"],
    "relocating-from-nj": ["sell-your-home", "how-we-sell-your-home", "cash-offer-nj", "sell-rental-property-nj"],
    "divorce-home-sale-nj": ["sell-your-home", "how-we-sell-your-home", "cash-offer-nj", "relocating-from-nj"],
    "sell-rental-property-nj": ["sell-your-home", "cash-offer-nj", "relocating-from-nj", "how-we-sell-your-home"],
}


def route(slug: str, language: str) -> str:
    return f"/{'es/' if language == 'es' else ''}{slug}"


def source_cards(document: dict, route_data: dict, common: dict, language: str) -> str:
    by_id = {item["id"]: item for item in document["sources"]}
    cards = []
    for source_id in route_data["sourceIds"]:
        item = by_id[source_id]
        use = item["useEs"] if language == "es" else item["use"]
        limit = item["limitEs"] if language == "es" else item["limit"]
        cards.append(
            f'''<article class="seller-source">
              <p class="seller-source__publisher">{esc(item["publisher"])}</p>
              <h3><a href="{esc(item["url"], quote=True)}" rel="noopener">{esc(item["title"])}</a></h3>
              <p><strong>{esc(common["use"])}:</strong> {esc(use)}</p>
              <p><strong>{esc(common["limit"])}:</strong> {esc(limit)}</p>
            </article>'''
        )
    return "\n".join(cards)


def related_cards(copy: dict, slug: str, language: str) -> str:
    cards = []
    for related_slug in RELATED[slug]:
        related = copy["pages"][related_slug][language]
        cards.append(
            f'''<article class="seller-related">
              <h3><a href="{route(related_slug, language)}">{esc(related["serviceName"])}</a></h3>
              <p>{esc(related["description"])}</p>
            </article>'''
        )
    return "\n".join(cards)


def doorway_retirement_links(slug: str, language: str) -> str:
    """Preserve the fail-closed town-doorway retirement contract on its seller hub."""
    if slug != "sell-your-home" or language != "en":
        return ""
    return '''
            <section class="doorway-retirement-links" data-doorway-retirement-links="seller">
                <h3 style="margin-top: 30px;">Selling a Home in New Jersey</h3>
                <p>Use the maintained statewide seller guide for the process, service details, and address-specific next steps.</p>
                <div class="link-grid">
                    <a href="/sell-your-home">Open the New Jersey Home-Selling Guide</a>
                    <a href="/counties/union-county">Union County</a>
                    <a href="/counties/essex-county">Essex County</a>
                    <a href="/counties/morris-county">Morris County</a>
                </div>
            </section>'''


def render(document: dict, copy: dict, route_data: dict, language: str) -> str:
    slug = route_data["slug"]
    page = copy["pages"][slug][language]
    common = COMMON[language]
    prefix = "/es" if language == "es" else ""
    own_route = route(slug, language)
    en_route = route(slug, "en")
    es_route = route(slug, "es")
    alternate = en_route if language == "es" else es_route
    breadcrumbs = (common["home"], common["sellerServices"], page["serviceName"])
    badges = "\n".join(f"<span>{esc(item)}</span>" for item in common["badges"])
    focus_cards = "\n".join(
        f'<article class="seller-card"><span class="seller-card__number">{index:02d}</span><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></article>'
        for index, item in enumerate(page["focusCards"], start=1)
    )
    process_steps = "\n".join(
        f'<article class="seller-step"><span>{index:02d}</span><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></article>'
        for index, item in enumerate(page["processSteps"], start=1)
    )
    checklist = "\n".join(f"<li>{esc(item)}</li>" for item in page["checklist"])
    options = "\n".join(
        f'<article class="seller-option{" seller-option--gold" if index else ""}"><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></article>'
        for index, item in enumerate(page["options"])
    )
    faqs = "\n".join(
        f'<article class="seller-faq"><h3>{esc(item["question"])}</h3><p>{esc(item["answer"])}</p></article>'
        for item in page["faq"]
    )
    doorway_links = doorway_retirement_links(slug, language)
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": SITE + own_route + "#webpage",
                "url": SITE + own_route,
                "name": page["title"],
                "description": page["description"],
                "inLanguage": "es-US" if language == "es" else "en-US",
                "dateModified": REVIEWED_ON,
                "isPartOf": {"@id": SITE + "/#website"},
                "about": {"@id": SITE + own_route + "#service"},
            },
            {
                "@type": "Service",
                "@id": SITE + own_route + "#service",
                "url": SITE + own_route,
                "name": page["serviceName"],
                "description": page["description"],
                "serviceType": page["serviceName"],
                "inLanguage": "es-US" if language == "es" else "en-US",
                "provider": {"@id": SITE + "/#agent"},
                "areaServed": [
                    {"@type": "AdministrativeArea", "name": f"{county} County, New Jersey"}
                    for county in ("Union", "Essex", "Morris", "Hudson", "Middlesex", "Somerset")
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": breadcrumbs[0], "item": SITE + ("/es" if language == "es" else "/")},
                    {"@type": "ListItem", "position": 2, "name": breadcrumbs[1], "item": SITE + route("sell-your-home", language)},
                    {"@type": "ListItem", "position": 3, "name": breadcrumbs[2], "item": SITE + own_route},
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                    }
                    for item in page["faq"]
                ],
            },
        ],
    }
    return f'''<!DOCTYPE html>
<html lang="{common["lang"]}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(page["title"])}</title>
  <meta name="description" content="{esc(page["description"], quote=True)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="author" content="Jorge Ramirez">
  <meta name="theme-color" content="#1A1A1A">
  <meta name="llm-context" content="{esc(page["llm"], quote=True)}">
  <link rel="canonical" href="{SITE}{own_route}">
  <link rel="alternate" hreflang="en-US" href="{SITE}{en_route}">
  <link rel="alternate" hreflang="es-US" href="{SITE}{es_route}">
  <link rel="alternate" hreflang="es" href="{SITE}{es_route}">
  <link rel="alternate" hreflang="x-default" href="{SITE}{en_route}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE}{own_route}">
  <meta property="og:title" content="{esc(page["title"], quote=True)}">
  <meta property="og:description" content="{esc(page["description"], quote=True)}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta property="og:locale" content="{common["locale"]}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(page["title"], quote=True)}">
  <meta name="twitter:description" content="{esc(page["description"], quote=True)}">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/seller-services.css">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
  <script type="application/ld+json">{json.dumps(structured, ensure_ascii=False, separators=(",", ":"))}</script>
</head>
<body class="seller-service-page" data-source-review="{REVIEWED_ON}">
  <a class="seller-skip" href="#main">{esc(common["skip"])}</a>
  <nav class="seller-nav" aria-label="Primary navigation">
    <div class="seller-nav__inner">
      <a class="seller-logo" href="{prefix or '/'}" aria-label="The Jorge Ramirez Group">
        <picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="250" height="100"></picture>
      </a>
      <button class="seller-menu" type="button" aria-label="{esc(common["menu"], quote=True)}" aria-expanded="false" aria-controls="seller-navigation">☰</button>
      <ul class="seller-nav__links" id="seller-navigation">
        <li><a href="{prefix or '/'}">{esc(common["home"])}</a></li>
        <li><a href="{prefix}/buy-a-home">{esc(common["buy"])}</a></li>
        <li><a href="{prefix}/sell-your-home">{esc(common["sell"])}</a></li>
        <li><a href="{prefix}/communities">{esc(common["communities"])}</a></li>
        <li><a href="{prefix}/blog">{esc(common["research"])}</a></li>
        <li><a class="seller-nav__language" href="{alternate}" hreflang="{'en-US' if language == 'es' else 'es-US'}" aria-label="{esc(common["language"], quote=True)}">{esc(common["languageShort"])}</a></li>
        <li><a href="tel:+19082307844" aria-label="{esc(common["call"], quote=True)}">908-230-7844</a></li>
        <li><a class="seller-nav__value" href="{prefix}/home-valuation">{esc(common["value"])}</a></li>
      </ul>
    </div>
  </nav>

  <main id="main" tabindex="-1">
    <header class="seller-hero">
      <div class="seller-wrap">
        <nav class="seller-breadcrumbs" aria-label="Breadcrumb"><a href="{prefix or '/'}">{esc(breadcrumbs[0])}</a><span aria-hidden="true">/</span><a href="{prefix}/sell-your-home">{esc(breadcrumbs[1])}</a><span aria-hidden="true">/</span><span>{esc(breadcrumbs[2])}</span></nav>
        <p class="seller-eyebrow">{esc(page["eyebrow"])}</p>
        <h1>{esc(page["h1"])}</h1>
        <p class="seller-hero__intro">{esc(page["intro"])}</p>
        <div class="seller-badges" aria-label="Page credentials">{badges}</div>
        <div class="seller-actions"><a class="seller-button seller-button--primary" href="{prefix}/home-valuation">{esc(common["primary"])}</a><a class="seller-button seller-button--outline" href="tel:+19082307844">{esc(common["secondary"])}</a></div>
      </div>
    </header>

    <section class="seller-section" aria-labelledby="focus-title">
      <div class="seller-wrap">
        <div class="seller-heading"><p class="seller-section-label">{esc(common["focusLabel"])}</p><h2 id="focus-title">{esc(page["focusTitle"])}</h2><p>{esc(page["focusIntro"])}</p></div>
        <div class="seller-grid--three">{focus_cards}</div>
      </div>
    </section>

    <section class="seller-section seller-section--dark seller-section--red-rule" aria-labelledby="process-title">
      <div class="seller-wrap">
        <div class="seller-heading"><p class="seller-eyebrow">{esc(common["processLabel"])}</p><h2 id="process-title">{esc(page["processTitle"])}</h2><p>{esc(page["processIntro"])}</p></div>
        <div class="seller-steps">{process_steps}</div>
      </div>
    </section>

    <section class="seller-section seller-section--paper" aria-labelledby="checklist-title">
      <div class="seller-wrap">
        <div class="seller-heading"><p class="seller-section-label">{esc(common["checklistLabel"])}</p><h2 id="checklist-title">{esc(page["checklistTitle"])}</h2><p>{esc(page["checklistIntro"])}</p></div>
        <ul class="seller-checklist">{checklist}</ul>
      </div>
    </section>

    <section class="seller-section" aria-labelledby="options-title">
      <div class="seller-wrap">
        <div class="seller-heading"><p class="seller-section-label">{esc(common["optionsLabel"])}</p><h2 id="options-title">{esc(page["optionsTitle"])}</h2><p>{esc(page["optionsIntro"])}</p></div>
        <div class="seller-grid--two seller-options">{options}</div>
        <aside class="seller-guidance"><p>{esc(page["guidance"])}</p></aside>
      </div>
    </section>

    <section class="seller-section seller-section--dark" aria-labelledby="sources-title">
      <div class="seller-wrap">
        <div class="seller-heading"><p class="seller-eyebrow">{esc(common["sourceLabel"])}</p><h2 id="sources-title">{esc(common["sourceTitle"])}</h2><p>{esc(common["sourceIntro"])}</p></div>
        <div class="seller-source-grid">{source_cards(document, route_data, common, language)}</div>
        <p class="seller-source-review">{esc(common["sourceReview"])}</p>
      </div>
    </section>

    <section class="seller-section seller-section--paper" aria-labelledby="faq-title">
      <div class="seller-wrap">
        <div class="seller-heading"><p class="seller-section-label">{esc(common["faqLabel"])}</p><h2 id="faq-title">{esc(page["serviceName"])}</h2></div>
        <div class="seller-faq-list">{faqs}</div>
        <aside class="seller-guidance"><p>{esc(common["disclaimer"])}</p></aside>
      </div>
    </section>

    <section class="seller-section" aria-labelledby="related-title">
      <div class="seller-wrap">
        <div class="seller-heading"><p class="seller-section-label">{esc(common["relatedLabel"])}</p><h2 id="related-title">{esc(common["relatedTitle"])}</h2><p>{esc(common["relatedIntro"])}</p></div>
        <div class="seller-related-grid">{related_cards(copy, slug, language)}</div>
      </div>
    </section>
{doorway_links}

    <section class="seller-cta">
      <div class="seller-wrap seller-cta__inner">
        <div><p class="seller-eyebrow">{esc(common["ctaLabel"])}</p><h2>{esc(page["ctaTitle"])}</h2><p>{esc(page["ctaText"])}</p></div>
        <div class="seller-actions"><a class="seller-button seller-button--light" href="{prefix}/home-valuation">{esc(common["primary"])}</a><a class="seller-button seller-button--outline" href="tel:+19082307844">{esc(common["secondary"])}</a></div>
      </div>
    </section>
  </main>

  <footer class="seller-footer">
    <div class="seller-wrap">
      <div class="seller-footer__grid">
        <section class="seller-footer__brand"><picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="250" height="100" loading="lazy"></picture><p>{esc(common["footerBlurb"])}</p><p>488 Springfield Avenue<br>Summit, NJ 07901<br>NJ License #1754604</p></section>
        <section><h2>{esc(common["footerResearch"])}</h2><a href="{prefix}/communities">{esc(common["communities"])}</a><a href="{prefix}/blog">{esc(common["research"])}</a><a href="{prefix}/nj-train-map">NJ TRANSIT</a></section>
        <section><h2>{esc(common["footerServices"])}</h2><a href="{prefix}/buy-a-home">{esc(common["buy"])}</a><a href="{prefix}/sell-your-home">{esc(common["sell"])}</a><a href="{prefix}/home-valuation">{esc(common["value"])}</a></section>
        <section><h2>{esc(common["footerContact"])}</h2><a href="tel:+19082307844">908-230-7844</a><a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a><a href="{prefix}/privacy-policy">{esc(common["privacy"])}</a></section>
      </div>
      <div class="seller-footer__bottom">© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties · {esc(common["rights"])}</div>
    </div>
  </footer>
  <script>
    (() => {{
      const button = document.querySelector('.seller-menu');
      const menu = document.getElementById('seller-navigation');
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


def redirect_fallback(language: str) -> str:
    prefix = "/es" if language == "es" else ""
    destination = f"{prefix}/sell-your-home"
    title = "Ruta consolidada | The Jorge Ramirez Group" if language == "es" else "Consolidated route | The Jorge Ramirez Group"
    message = "Esta guía ahora forma parte del servicio principal para vendedores." if language == "es" else "This guide is now part of the primary seller service."
    link = "Abrir el servicio para vendedores" if language == "es" else "Open the seller service"
    return f'''<!DOCTYPE html>
<html lang="{language}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{message}">
  <meta name="robots" content="noindex, follow">
  <meta http-equiv="refresh" content="0; url={destination}">
  <link rel="canonical" href="{SITE}{destination}">
</head>
<body>
  <main><h1>{message}</h1><p><a href="{destination}">{link}</a></p></main>
</body>
</html>
'''


def targets(document: dict, copy: dict) -> dict[Path, str]:
    output: dict[Path, str] = {}
    route_by_slug = {item["slug"]: item for item in document["routes"]}
    for slug in sorted(EXPECTED_SLUGS):
        for language in ("en", "es"):
            prefix = Path("es") if language == "es" else Path()
            output[ROOT / prefix / f"{slug}.html"] = render(document, copy, route_by_slug[slug], language)
    output[ROOT / "sell-home-fast-nj.html"] = redirect_fallback("en")
    output[ROOT / "es" / "sell-home-fast-nj.html"] = redirect_fallback("es")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    document, copy = load_data()
    rendered = targets(document, copy)
    stale = [
        path
        for path, expected in rendered.items()
        if not path.exists() or path.read_text(encoding="utf-8") != expected
    ]
    if args.check:
        if stale:
            print("Stale seller-service pages:")
            for path in stale:
                print(path.relative_to(ROOT))
            return 1
        print(f"{len(rendered)} seller-service pages are current.")
        return 0
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered[path], encoding="utf-8")
    print(f"Updated {len(stale)} of {len(rendered)} seller-service pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
