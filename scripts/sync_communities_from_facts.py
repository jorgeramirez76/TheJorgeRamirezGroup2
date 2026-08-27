#!/usr/bin/env python3
"""Synchronize the communities hub with data/site-facts.json.

This updates content and structured data only. It deliberately preserves the
page's existing styles, scripts, canonical URL, and hreflang declarations.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / "data" / "site-facts.json").read_text(encoding="utf-8"))
# Vercel's clean-URL routing can resolve `/communities` from the root-level
# `communities.html` file while conventional static servers resolve the
# directory index. Generate both route candidates from one source so preview
# and production cannot publish different inventories.
OUT = ROOT / "communities" / "index.html"
ROUTE_ALIASES = (ROOT / "communities.html",)
SPANISH_OUT = ROOT / "es" / "communities" / "index.html"
SPANISH_ROUTE_ALIASES = (ROOT / "es" / "communities.html",)

SPECIAL_NAMES = {
    "boonton-township": "Boonton Township",
    "chatham-borough": "Chatham Borough",
    "chatham-township": "Chatham Township",
    "chester-borough": "Chester Borough",
    "chester-township": "Chester Township",
    "east-newark": "East Newark",
    "mendham-borough": "Mendham Borough",
    "mendham-township": "Mendham Township",
    "middlesex-borough": "Middlesex Borough",
    "morris-township": "Morris Township",
    "mount-olive": "Mount Olive",
    "north-brunswick": "North Brunswick",
    "parsippany-troy-hills": "Parsippany-Troy Hills",
    "peapack-gladstone": "Peapack-Gladstone",
    "pequannock-township": "Pequannock Township",
    "rockaway-borough": "Rockaway Borough",
    "rockaway-township": "Rockaway Township",
    "south-brunswick": "South Brunswick",
    "washington-township-morris": "Washington Township (Morris)",
}

COUNTY_BLURBS = {
    "Union": "Browse the supported Union County community guides, including local housing, transportation, and municipal resources.",
    "Essex": "Browse the supported Essex County community guides, including local housing, transportation, and municipal resources.",
    "Morris": "Browse the supported Morris County community guides, including local housing, transportation, and municipal resources.",
    "Hudson": "Browse the supported Hudson County community guides, including local housing, transportation, and municipal resources.",
    "Middlesex": "Browse the supported Middlesex County community guides, including local housing, transportation, and municipal resources.",
    "Somerset": "Browse the supported Somerset County community guides, including Basking Ridge within Bernards Township.",
}

SPANISH_COUNTY_BLURBS = {
    county: (
        f"Explora las guías disponibles del condado de {county}, con recursos "
        "sobre vivienda, transporte y servicios municipales."
    )
    for county in COUNTY_BLURBS
}


def display_name(slug: str) -> str:
    return SPECIAL_NAMES.get(slug, slug.replace("-", " ").title())


def normalize_main_landmark(source: str) -> str:
    """Keep the hero, filters, and directory inside the skip-link target."""
    preferred = '<main id="main" role="main" tabindex="-1">'
    hero = '<section class="communities-hero">'
    legacy = '<main id="main" role="main">'
    if preferred not in source:
        source, hero_replacements = re.subn(
            re.escape(hero), f"{preferred}\n{hero}", source, count=1
        )
        source, legacy_replacements = re.subn(
            rf"\n{re.escape(legacy)}\s*\n", "\n", source, count=1
        )
        if hero_replacements != 1 or legacy_replacements != 1:
            raise RuntimeError("communities hub main landmark could not be normalized")
    if source.count(preferred) != 1 or source.index(preferred) > source.index(hero):
        raise RuntimeError("communities hub hero is outside the main landmark")
    return source


inventory = FACTS["canonicalTownInventory"]
by_county = inventory["byCounty"]
total = inventory["total"]
counties = list(by_county)

items = []
for county in counties:
    for slug in by_county[county]:
        items.append(
            {
                "@type": "ListItem",
                "position": len(items) + 1,
                "url": f"https://thejorgeramirezgroup.com/towns/{slug}",
                "name": f"{display_name(slug)}, {county} County",
            }
        )

schema = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "New Jersey Community Guides | The Jorge Ramirez Group",
    "description": (
        f"Directory of {total} maintained New Jersey real estate community guides across "
        + ", ".join(counties[:-1])
        + f", and {counties[-1]} counties, with official-source town and county research."
    ),
    "url": "https://thejorgeramirezgroup.com/communities",
    "isPartOf": {
        "@type": "WebSite",
        "name": "The Jorge Ramirez Group",
        "url": "https://thejorgeramirezgroup.com",
    },
    "mainEntity": {
        "@type": "ItemList",
        "numberOfItems": total,
        "itemListElement": items,
    },
    "breadcrumb": {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": "https://thejorgeramirezgroup.com/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Communities",
                "item": "https://thejorgeramirezgroup.com/communities",
            },
        ],
    },
}


def section_html(county: str) -> str:
    cards = []
    for slug in by_county[county]:
        name = display_name(slug)
        cards.append(
            f'''        <a class="town-card" href="/towns/{slug}" data-name="{name.lower()}">
          <h3>{name}</h3>
          <p>Open the community guide for {name} in {county} County.</p>
          <span class="arrow">View {name} →</span>
        </a>'''
        )
    return f'''  <section class="county-section" data-county="{county}" id="{county.lower()}">
    <div class="container">
      <div class="county-header">
        <h2>{county} County</h2>
        <span class="count">{len(by_county[county])} towns</span>
      </div>
      <p class="county-blurb">{COUNTY_BLURBS[county]}</p>
      <div class="town-grid">
{chr(10).join(cards)}
      </div>
      <p><a href="/counties/{county.lower()}-county">Open the {county} County real estate guide →</a></p>
    </div>
  </section>'''


def spanish_section_html(county: str) -> str:
    cards = []
    for slug in by_county[county]:
        name = display_name(slug)
        cards.append(
            f'''        <a class="town-card" href="/es/towns/{slug}" data-name="{name.lower()}">
          <h3>{name}</h3>
          <p>Abre la guía de {name} en el condado de {county}.</p>
          <span class="arrow">Ver {name} →</span>
        </a>'''
        )
    return f'''  <section class="county-section" data-county="{county}" id="{county.lower()}">
    <div class="container">
      <div class="county-header">
        <h2>Condado de {county}</h2>
        <span class="count">{len(by_county[county])} pueblos</span>
      </div>
      <p class="county-blurb">{SPANISH_COUNTY_BLURBS[county]}</p>
      <div class="town-grid">
{chr(10).join(cards)}
      </div>
      <p><a href="/es/counties/{county.lower()}-county">Abrir la guía inmobiliaria del condado de {county} →</a></p>
    </div>
  </section>'''


source = normalize_main_landmark(OUT.read_text(encoding="utf-8"))
source = re.sub(
    r"<title>.*?</title>",
    f"<title>NJ Community Guides — {total} Towns | The Jorge Ramirez Group</title>",
    source,
    count=1,
    flags=re.S,
)
source = re.sub(
    r'<meta name="description" content="[^"]*">',
    f'<meta name="description" content="Explore {total} maintained NJ real estate community guides across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties with local research.">',
    source,
    count=1,
)
source = re.sub(
    r'<meta name="llm-context" content="[^"]*">',
    (
        f'<meta name="llm-context" content="Directory of {total} supported New Jersey community guides '
        f'across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties. Basking Ridge is listed '
        f'within Bernards Township in Somerset County. Contact Jorge Ramirez: 908-230-7844, '
        f'jorge.ramirez@kw.com.">'
    ),
    source,
    count=1,
)
source = re.sub(
    r'<meta property="og:title" content="[^"]*">',
    f'<meta property="og:title" content="NJ Community Guides — {total} Towns | The Jorge Ramirez Group">',
    source,
    count=1,
)
source = re.sub(
    r'<meta property="og:description" content="[^"]*">',
    f'<meta property="og:description" content="Explore {total} maintained NJ real estate community guides across six counties with town, county, buyer, and seller research.">',
    source,
    count=1,
)
source = re.sub(
    r'<meta name="twitter:title" content="[^"]*">',
    f'<meta name="twitter:title" content="NJ Communities — {total} Towns | Jorge Ramirez">',
    source,
    count=1,
)
source = re.sub(
    r'<meta name="twitter:description" content="[^"]*">',
    f'<meta name="twitter:description" content="Explore {total} maintained NJ real estate community guides across six counties with town and county research.">',
    source,
    count=1,
)
source = re.sub(
    r'  <script type="application/ld\+json">\s*\{.*?\}\s*</script>',
    '  <script type="application/ld+json">\n'
    + json.dumps(schema, indent=2, ensure_ascii=False)
    + "\n  </script>",
    source,
    count=1,
    flags=re.S,
)
source = re.sub(
    r"<h1>\d+ NJ (?:Communities We Serve|Community Guides)</h1>",
    f"<h1>{total} NJ Community Guides</h1>",
    source,
    count=1,
)
source, replacements = re.subn(
    r'(<section class="communities-hero">\s*<h1>.*?</h1>)\s*<p>.*?</p>',
    r"\1\n  <p>Explore maintained real estate guides across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties. Each guide connects public records and local research to a property-specific buyer or seller decision.</p>",
    source,
    count=1,
    flags=re.S,
)
if replacements != 1:
    raise RuntimeError("English communities hub is missing its hero introduction")
for county in counties:
    source = re.sub(
        rf'(<button class="county-filter" data-county="{county}">{county} \()\d+(\)</button>)',
        rf"\g<1>{len(by_county[county])}\g<2>",
        source,
        count=1,
    )
    source = re.sub(
        rf'  <section\b[^>]*data-county="{county}"[^>]*>.*?</section>',
        section_html(county),
        source,
        count=1,
        flags=re.S,
    )
source = source.replace(
    "<p>Jorge serves all of Northern and Central New Jersey. Call directly for any town — even ones not listed here.</p>",
    "<p>Looking for help in a town not listed here? Call Jorge to confirm current coverage.</p>",
)
source, replacements = re.subn(
    r'  <section class="cta-section">.*?</section>',
    '''  <section class="cta-section">
    <h2>Choose the right local real estate research path</h2>
    <p>Browse the complete maintained town directory, start with a six-county guide, or continue to the buyer and seller planning resources. Every property conclusion should remain tied to the address and current evidence.</p>
    <a href="/towns" class="btn">All Town Guides</a>
    <a href="/counties" class="btn">Six County Guides</a>
    <a href="/buy-a-home" class="btn">Buyer Planning</a>
    <a href="/sell-your-home" class="btn">Seller Planning</a>
  </section>''',
    source,
    count=1,
    flags=re.S,
)
if replacements != 1:
    raise RuntimeError("English communities hub is missing its closing pathway section")

OUT.write_text(source, encoding="utf-8")
for alias in ROUTE_ALIASES:
    alias.write_text(source, encoding="utf-8")

spanish_schema = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "Guías de comunidades de Nueva Jersey",
    "description": (
        f"Directorio de {total} guías inmobiliarias mantenidas de Nueva Jersey en los "
        "condados de Union, Essex, Morris, Hudson, Middlesex y Somerset, con fuentes oficiales."
    ),
    "url": "https://thejorgeramirezgroup.com/es/communities",
    "inLanguage": "es-US",
    "isPartOf": {
        "@type": "WebSite",
        "name": "The Jorge Ramirez Group",
        "url": "https://thejorgeramirezgroup.com/es",
    },
    "mainEntity": {
        "@type": "ItemList",
        "numberOfItems": total,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "url": f"https://thejorgeramirezgroup.com/es/towns/{slug}",
                "name": f"{display_name(slug)}, condado de {county}",
            }
            for index, (county, slug) in enumerate(
                (
                    (county, slug)
                    for county in counties
                    for slug in by_county[county]
                ),
                start=1,
            )
        ],
    },
    "breadcrumb": {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Inicio",
                "item": "https://thejorgeramirezgroup.com/es",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Comunidades",
                "item": "https://thejorgeramirezgroup.com/es/communities",
            },
        ],
    },
}

spanish = normalize_main_landmark(SPANISH_OUT.read_text(encoding="utf-8"))
spanish_replacements = (
    (
        r"<title>.*?</title>",
        f"<title>Comunidades de NJ — {total} guías | The Jorge Ramirez Group</title>",
    ),
    (
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="Explora {total} guías inmobiliarias de NJ en Union, Essex, Morris, Hudson, Middlesex y Somerset, con recursos locales para compradores y vendedores.">',
    ),
    (
        r'<meta name="llm-context" content="[^"]*">',
        (
            f'<meta name="llm-context" content="Directorio de {total} guías de comunidades '
            'de Nueva Jersey en los condados de Union, Essex, Morris, Hudson, Middlesex y '
            'Somerset. Contacto: 908-230-7844, jorge.ramirez@kw.com.">'
        ),
    ),
    (
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="Comunidades de NJ — {total} guías | The Jorge Ramirez Group">',
    ),
    (
        r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="Explora {total} guías inmobiliarias de NJ en seis condados con recursos de pueblos, condados, compra y venta.">',
    ),
    (
        r'<meta name="twitter:title" content="[^"]*">',
        f'<meta name="twitter:title" content="Comunidades de NJ — {total} guías | Jorge Ramirez">',
    ),
    (
        r'<meta name="twitter:description" content="[^"]*">',
        f'<meta name="twitter:description" content="Explora {total} guías inmobiliarias de NJ en seis condados con investigación local.">',
    ),
)
for pattern, replacement in spanish_replacements:
    spanish, replacements = re.subn(
        pattern, replacement, spanish, count=1, flags=re.S
    )
    if replacements != 1:
        raise RuntimeError(f"Spanish communities hub did not match: {pattern}")

spanish, replacements = re.subn(
    r'  <script type="application/ld\+json">\s*\{.*?\}\s*</script>',
    '  <script type="application/ld+json">\n'
    + json.dumps(spanish_schema, indent=2, ensure_ascii=False)
    + "\n  </script>",
    spanish,
    count=1,
    flags=re.S,
)
if replacements != 1:
    raise RuntimeError("Spanish communities hub is missing its JSON-LD block")

spanish, replacements = re.subn(
    r"<h1>(?:\d+ Comunidades de NJ que Atendemos|\d+ guías de comunidades de NJ)</h1>",
    f"<h1>{total} guías de comunidades de NJ</h1>",
    spanish,
    count=1,
)
if replacements != 1:
    raise RuntimeError("Spanish communities hub is missing its numeric heading")
spanish = re.sub(
    r'(<section class="communities-hero">\s*<h1>.*?</h1>)\s*<p>.*?</p>',
    r"\1\n  <p>Explora guías inmobiliarias mantenidas en los condados de Union, Essex, Morris, Hudson, Middlesex y Somerset. Cada guía conecta registros públicos e investigación local con una decisión específica de compra o venta.</p>",
    spanish,
    count=1,
    flags=re.S,
)
for county in counties:
    spanish = re.sub(
        rf'(<button class="county-filter" data-county="{county}">{county} \()\d+(\)</button>)',
        rf"\g<1>{len(by_county[county])}\g<2>",
        spanish,
        count=1,
    )
    spanish, replacements = re.subn(
        rf'  <section\b[^>]*data-county="{county}"[^>]*>.*?</section>',
        spanish_section_html(county),
        spanish,
        count=1,
        flags=re.S,
    )
    if replacements != 1:
        raise RuntimeError(f"Spanish communities hub is missing {county}")
spanish = spanish.replace(
    "<p>Jorge atiende todo el norte y centro de Nueva Jersey. Llámalo directamente para cualquier pueblo.</p>",
    "<p>¿Buscas ayuda en otro pueblo? Llama a Jorge para confirmar la cobertura actual.</p>",
)
spanish, replacements = re.subn(
    r'  <section class="cta-section">.*?</section>',
    '''  <section class="cta-section">
    <h2>Elige la ruta correcta de investigación inmobiliaria local</h2>
    <p>Consulta el directorio completo de pueblos, empieza con una guía de los seis condados o continúa con los recursos para compradores y vendedores. Cada conclusión debe mantenerse vinculada a la dirección y evidencia vigente.</p>
    <a href="/es/communities#union" class="btn">Explorar por Condado</a>
    <a href="/es/buy-a-home" class="btn">Plan para Comprar</a>
    <a href="/es/sell-your-home" class="btn">Plan para Vender</a>
  </section>''',
    spanish,
    count=1,
    flags=re.S,
)
if replacements != 1:
    raise RuntimeError("Spanish communities hub is missing its closing pathway section")

SPANISH_OUT.write_text(spanish, encoding="utf-8")
for alias in SPANISH_ROUTE_ALIASES:
    alias.write_text(spanish, encoding="utf-8")
print(
    f"Synchronized /communities route candidates: {total} towns across "
    f"{len(counties)} counties in English and Spanish"
)
