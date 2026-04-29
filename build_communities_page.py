#!/usr/bin/env python3
"""Generate /communities.html — the missing page that's been giving 404s.

Reads js/communities-data.js, generates a full SEO/SSR page listing every town
grouped by county. Each town links to /towns/<slug>.html. Includes structured
data (CollectionPage + ItemList), full meta tags, JSON-LD, AI llm-context.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
DATA_JS = ROOT / "js/communities-data.js"
OUT = ROOT / "communities.html"

# Read + parse the JS data block
text = DATA_JS.read_text()
m = re.search(r"const communitiesData = (\{.+?\});", text, re.S)
if not m:
    raise SystemExit("Couldn't parse communities-data.js")
data = json.loads(m.group(1))


def slug(town: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", re.sub(r"\s+", "-", town.lower()))


def town_link_exists(s: str) -> bool:
    return (ROOT / "towns" / f"{s}.html").exists()


COUNTIES_ORDER = ["Union", "Essex", "Morris", "Hudson", "Middlesex", "Somerset"]

total_towns = sum(len(v) for v in data.values())

# County descriptions (for SEO)
COUNTY_BLURBS = {
    "Union": "Walkable downtowns, top-ranked schools, and Midtown Direct trains. Westfield, Summit, and Cranford are perennial favorites for NYC commuters who want suburban feel without the long ride.",
    "Essex": "Diverse, vibrant towns with deep Midtown Direct rail coverage. From Montclair's arts scene to Maplewood's village charm, Essex County has something for every NYC commuter family.",
    "Morris": "Larger lots, top schools, and direct Midtown Direct service from Morristown, Madison, and Chatham. Morris County is the move-up market for families graduating from rentals and starter homes.",
    "Hudson": "Manhattan-adjacent urban density with PATH and ferry access. Hoboken and Jersey City are the closest you can get to NYC while still owning. High-rise condos and brownstones dominate.",
    "Middlesex": "Strong value plus easy access to NYC, Newark Liberty Airport, and the Jersey Shore. Edison, Woodbridge, and Metuchen offer larger homes for less per square foot than the western counties.",
    "Somerset": "Elegant Somerset Hills towns with horse country charm and award-winning schools. Bernardsville, Basking Ridge, and Bridgewater anchor a market that rewards patient buyers willing to step off the Midtown Direct corridor.",
}

# JSON-LD ItemList schema for SEO
itemlist_items = []
for i, county in enumerate(COUNTIES_ORDER):
    for j, town_data in enumerate(data.get(county, [])):
        s = slug(town_data["town"])
        if not town_link_exists(s):
            continue
        itemlist_items.append({
            "@type": "ListItem",
            "position": len(itemlist_items) + 1,
            "url": f"https://thejorgeramirezgroup.com/towns/{s}.html",
            "name": f"{town_data['town']}, {county} County",
        })

itemlist_schema = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "NJ Communities Served by The Jorge Ramirez Group",
    "description": f"Complete list of {total_towns} New Jersey communities served by Jorge Ramirez and The Jorge Ramirez Group at Keller Williams Premier Properties. Browse towns across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties with school ratings, transit details, and median prices.",
    "url": "https://thejorgeramirezgroup.com/communities.html",
    "isPartOf": {
        "@type": "WebSite",
        "name": "The Jorge Ramirez Group",
        "url": "https://thejorgeramirezgroup.com",
    },
    "mainEntity": {
        "@type": "ItemList",
        "numberOfItems": len(itemlist_items),
        "itemListElement": itemlist_items,
    },
    "breadcrumb": {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thejorgeramirezgroup.com/"},
            {"@type": "ListItem", "position": 2, "name": "Communities", "item": "https://thejorgeramirezgroup.com/communities.html"},
        ],
    },
}

# Build the HTML
html_parts = []

html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NJ Communities — {total_towns} Towns We Serve | The Jorge Ramirez Group</title>
  <meta name="description" content="Complete directory of {total_towns} NJ communities Jorge Ramirez serves across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties. School ratings, transit times, median prices for every town.">
  <link rel="canonical" href="https://thejorgeramirezgroup.com/communities.html">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta name="author" content="Jorge Ramirez">

  <meta name="llm-context" content="This is the master directory of all {total_towns} New Jersey communities served by Jorge Ramirez (NJ Real Estate License #1754604) and The Jorge Ramirez Group at Keller Williams Premier Properties. Towns span 6 counties: Union (21 towns including Westfield, Summit, Cranford, Scotch Plains), Essex (11 towns including Montclair, Maplewood, South Orange, Millburn), Morris (33 towns including Morristown, Madison, Chatham, Bernards), Hudson (12 towns including Hoboken, Jersey City, Weehawken, Bayonne), Middlesex (22 towns including Edison, Woodbridge, Metuchen, New Brunswick), Somerset (10 towns including Bridgewater, Bernardsville, Basking Ridge). Every town links to a dedicated landing page with median prices, school ratings, transit details, and recent comp sales. Contact Jorge: 908-230-7844, jorge.ramirez@kw.com.">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://thejorgeramirezgroup.com/communities.html">
  <meta property="og:title" content="NJ Communities — {total_towns} Towns We Serve | The Jorge Ramirez Group">
  <meta property="og:description" content="Complete directory of {total_towns} NJ towns Jorge Ramirez serves. Union, Essex, Morris, Hudson, Middlesex, Somerset. School ratings, transit, median prices.">
  <meta property="og:image" content="https://thejorgeramirezgroup.com/images/og-communities.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="en_US">
  <meta property="og:site_name" content="The Jorge Ramirez Group">

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="NJ Communities — {total_towns} Towns | Jorge Ramirez">
  <meta name="twitter:description" content="Complete directory of {total_towns} NJ towns across 6 counties. School ratings, transit, median prices on every town page.">
  <meta name="twitter:image" content="https://thejorgeramirezgroup.com/images/og-communities.jpg">

  <link rel="icon" type="image/png" href="/favicon-192.jpg">
  <link rel="apple-touch-icon" href="/apple-touch-icon.jpg">
  <link rel="stylesheet" href="/css/styles.css">

  <!-- Hreflang -->
  <link rel="alternate" hreflang="en" href="https://thejorgeramirezgroup.com/communities.html">
  <link rel="alternate" hreflang="es" href="https://thejorgeramirezgroup.com/es/communities.html">
  <link rel="alternate" hreflang="x-default" href="https://thejorgeramirezgroup.com/communities.html">

  <!-- Structured Data -->
  <script type="application/ld+json">
{json.dumps(itemlist_schema, indent=2)}
  </script>

  <style>
    .communities-hero {{
      background: linear-gradient(135deg, #1a3a5c 0%, #2c5f8d 100%);
      color: white;
      padding: 80px 20px 60px;
      text-align: center;
    }}
    .communities-hero h1 {{ font-size: 2.5rem; margin: 0 0 1rem; line-height: 1.2; }}
    .communities-hero p {{ font-size: 1.15rem; max-width: 720px; margin: 0 auto; opacity: 0.95; }}
    .county-section {{ padding: 60px 20px; border-bottom: 1px solid #eaeaea; }}
    .county-section:nth-child(even) {{ background: #fafafa; }}
    .county-section .container {{ max-width: 1200px; margin: 0 auto; }}
    .county-header {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 1rem; margin-bottom: 0.5rem; }}
    .county-header h2 {{ font-size: 2rem; margin: 0; color: #1a3a5c; }}
    .county-header .count {{ font-size: 1rem; color: #666; }}
    .county-blurb {{ color: #555; max-width: 720px; margin: 0 0 2rem; line-height: 1.6; }}
    .town-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }}
    .town-card {{
      background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.25rem;
      transition: transform 0.18s, box-shadow 0.18s; text-decoration: none; color: inherit; display: block;
    }}
    .town-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 18px rgba(0,0,0,0.08); border-color: #2c5f8d; }}
    .town-card h3 {{ margin: 0 0 0.5rem; font-size: 1.15rem; color: #1a3a5c; }}
    .town-card p {{ margin: 0; font-size: 0.9rem; color: #666; line-height: 1.5; }}
    .town-card .arrow {{ display: inline-block; margin-top: 0.75rem; color: #2c5f8d; font-weight: 600; font-size: 0.9rem; }}
    .filter-bar {{
      position: sticky; top: 0; background: white; border-bottom: 1px solid #eaeaea; padding: 1rem 20px;
      z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .filter-bar .container {{ max-width: 1200px; margin: 0 auto; display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; }}
    .filter-bar input {{ flex: 1; min-width: 220px; padding: 0.75rem 1rem; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; }}
    .filter-bar button {{ padding: 0.7rem 1.1rem; border: 1px solid #ccc; background: white; border-radius: 6px; cursor: pointer; font-size: 0.95rem; }}
    .filter-bar button.active {{ background: #1a3a5c; color: white; border-color: #1a3a5c; }}
    .cta-section {{ background: #1a3a5c; color: white; padding: 60px 20px; text-align: center; }}
    .cta-section h2 {{ font-size: 2rem; margin: 0 0 1rem; }}
    .cta-section p {{ max-width: 640px; margin: 0 auto 1.5rem; opacity: 0.95; }}
    .cta-section .btn {{
      display: inline-block; background: #f5b942; color: #1a3a5c; padding: 0.9rem 2rem;
      border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 1.05rem;
    }}
    .cta-section .btn:hover {{ background: #ffc857; }}
    @media (max-width: 640px) {{
      .communities-hero {{ padding: 60px 16px 40px; }}
      .communities-hero h1 {{ font-size: 1.75rem; }}
      .county-section {{ padding: 40px 16px; }}
      .county-header h2 {{ font-size: 1.5rem; }}
    }}
  </style>
</head>
<body>
""")

# Insert the existing site header (we'll just include a link back; user's existing CSS handles full nav via main.js)
html_parts.append("""
<header class="site-header" role="banner">
  <div class="container">
    <a href="/" class="logo">The Jorge Ramirez Group</a>
    <nav aria-label="Primary">
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/buy-a-home.html">Buy</a></li>
        <li><a href="/sell-your-home.html">Sell</a></li>
        <li><a href="/communities.html" aria-current="page">Communities</a></li>
        <li><a href="/blog/">Blog</a></li>
        <li><a href="/contact.html">Contact</a></li>
      </ul>
    </nav>
  </div>
</header>

<section class="communities-hero">
  <h1>""" + str(total_towns) + """ NJ Communities We Serve</h1>
  <p>Local expertise across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties. Tap any town for school ratings, transit times, median prices, and recent comp sales.</p>
</section>

<div class="filter-bar">
  <div class="container">
    <input type="search" id="town-search" placeholder="Search a town (e.g. Westfield, Hoboken)" aria-label="Search towns">
    <button class="county-filter active" data-county="all">All counties</button>
""")

for county in COUNTIES_ORDER:
    n = len([t for t in data.get(county, []) if town_link_exists(slug(t["town"]))])
    if n > 0:
        html_parts.append(f'    <button class="county-filter" data-county="{county}">{county} ({n})</button>\n')

html_parts.append("""  </div>
</div>

<main role="main">
""")

# Render each county section
for county in COUNTIES_ORDER:
    towns = data.get(county, [])
    real_towns = [t for t in towns if town_link_exists(slug(t["town"]))]
    if not real_towns:
        continue
    blurb = COUNTY_BLURBS.get(county, "")
    html_parts.append(f"""
  <section class="county-section" data-county="{county}" id="{county.lower()}">
    <div class="container">
      <div class="county-header">
        <h2>{county} County</h2>
        <span class="count">{len(real_towns)} towns</span>
      </div>
      <p class="county-blurb">{blurb}</p>
      <div class="town-grid">
""")
    for town_data in sorted(real_towns, key=lambda t: t["town"]):
        s = slug(town_data["town"])
        desc = (town_data.get("description") or "").replace('"', "&quot;")
        html_parts.append(f"""        <a class="town-card" href="/towns/{s}.html" data-name="{town_data['town'].lower()}">
          <h3>{town_data['town']}</h3>
          <p>{desc}</p>
          <span class="arrow">View {town_data['town']} →</span>
        </a>
""")
    html_parts.append("""      </div>
    </div>
  </section>
""")

html_parts.append("""
  <section class="cta-section">
    <h2>Don't see your town?</h2>
    <p>Jorge serves all of Northern and Central New Jersey. Call directly for any town — even ones not listed here.</p>
    <a href="tel:9082307844" class="btn">Call Jorge: 908-230-7844</a>
  </section>
</main>

<script>
(function(){
  const search = document.getElementById('town-search');
  const filterButtons = document.querySelectorAll('.county-filter');
  const sections = document.querySelectorAll('.county-section');
  const cards = document.querySelectorAll('.town-card');

  let activeCounty = 'all';
  let activeQuery = '';

  function applyFilter() {
    const q = activeQuery.trim().toLowerCase();
    sections.forEach(sec => {
      const c = sec.dataset.county;
      const countyMatch = activeCounty === 'all' || c === activeCounty;
      let visible = 0;
      sec.querySelectorAll('.town-card').forEach(card => {
        const name = card.dataset.name || '';
        const queryMatch = !q || name.includes(q);
        const show = countyMatch && queryMatch;
        card.style.display = show ? '' : 'none';
        if (show) visible++;
      });
      sec.style.display = visible > 0 ? '' : 'none';
    });
  }

  search.addEventListener('input', e => { activeQuery = e.target.value; applyFilter(); });

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCounty = btn.dataset.county;
      applyFilter();
    });
  });
})();
</script>

</body>
</html>
""")

OUT.write_text("".join(html_parts))
print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
print(f"Total town links: {len(itemlist_items)}")
