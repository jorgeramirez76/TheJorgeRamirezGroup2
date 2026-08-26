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
OUT = ROOT / "communities.html"

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


def display_name(slug: str) -> str:
    return SPECIAL_NAMES.get(slug, slug.replace("-", " ").title())


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
    "name": "NJ Communities Served by The Jorge Ramirez Group",
    "description": (
        f"Directory of {total} supported New Jersey community guides across "
        + ", ".join(counties[:-1])
        + f", and {counties[-1]} counties."
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
    </div>
  </section>'''


source = OUT.read_text(encoding="utf-8")
source = re.sub(
    r"<title>.*?</title>",
    f"<title>NJ Communities — {total} Towns We Serve | The Jorge Ramirez Group</title>",
    source,
    count=1,
    flags=re.S,
)
source = re.sub(
    r'<meta name="description" content="[^"]*">',
    f'<meta name="description" content="Directory of {total} supported NJ community guides across six counties.">',
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
    f'<meta property="og:title" content="NJ Communities — {total} Towns We Serve | The Jorge Ramirez Group">',
    source,
    count=1,
)
source = re.sub(
    r'<meta property="og:description" content="[^"]*">',
    f'<meta property="og:description" content="Directory of {total} supported NJ community guides across six counties.">',
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
    f'<meta name="twitter:description" content="Directory of {total} supported NJ community guides across six counties.">',
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
    r"<h1>\d+ NJ Communities We Serve</h1>",
    f"<h1>{total} NJ Communities We Serve</h1>",
    source,
    count=1,
)
source = re.sub(
    r"<p>Local expertise across .*?</p>",
    "<p>Community guides across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties.</p>",
    source,
    count=1,
    flags=re.S,
)
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

OUT.write_text(source, encoding="utf-8")
print(f"Synchronized {OUT.name}: {total} towns across {len(counties)} counties")
