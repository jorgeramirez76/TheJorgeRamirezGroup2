#!/usr/bin/env python3
"""Generate 17 missing Somerset County NJ town pages + Spanish versions.

Existing: basking-ridge, peapack-gladstone, warren-township, watchung.
Missing (from 21 Somerset municipalities): 17 towns.

Strategy:
  1. Read towns/basking-ridge.html as template (already Somerset-styled).
  2. Per-town: swap name/zip/county context + prepend a 180-200 word
     town-specific intro paragraph with median-price / commute / school data.
  3. Write towns/<slug>.html + /es/towns/<slug>.html Spanish stub.
"""
import re
import sys
from pathlib import Path

ROOT = Path('/Users/teddy/TheJorgeRamirezGroup2')
TEMPLATE = ROOT / 'towns' / 'basking-ridge.html'

SOMERSET = [
    {'slug':'bedminster', 'name':'Bedminster', 'zip':'07921',
     'median':'$950,000', 'commute':'60', 'schools':'9/10',
     'district':'Bedminster Township Public Schools',
     'intro':('Bedminster is one of Somerset County\'s most prestigious rural communities — horse farms, preserved open space, and estate homes on multi-acre lots, 60 minutes to Manhattan via NJ Transit\'s Gladstone Branch through Far Hills. Median sale prices hover around $950K with substantial upside on custom builds. The Trump National Golf Club Bedminster sits in town, and the river views along the North Branch Raritan define much of the luxury market here.'),
     'why':('Bedminster gives you the privacy and land of horse country with a direct-to-NYC commuter rail 5 minutes away — an unusual combination in New Jersey.')},
    {'slug':'bernards-township', 'name':'Bernards Township', 'zip':'07920',
     'median':'$1,050,000', 'commute':'55', 'schools':'10/10',
     'district':'Bernards Township Public Schools',
     'intro':('Bernards Township includes Basking Ridge, Lyons, and Liberty Corner — Somerset County\'s flagship commuter township with 10/10 schools, a picture-perfect colonial downtown in Basking Ridge, and 55-minute commute to NYC via the Gladstone Branch. Median sale prices around $1.05M reflect the combination of top schools and substantial lot sizes. The Somerset Hills region stretches across Bernards, Bernardsville, and Far Hills, giving buyers options from $800K cape cods to $3M estates within 10 miles.'),
     'why':('Bernards delivers the highest school ratings in Somerset County with commute times competitive with much closer Essex/Union towns.')},
    {'slug':'bernardsville', 'name':'Bernardsville', 'zip':'07924',
     'median':'$1,250,000', 'commute':'60', 'schools':'9/10',
     'district':'Somerset Hills Regional School District',
     'intro':('Bernardsville is the quintessential Somerset Hills town — historic estates, a walkable Olcott Avenue downtown with boutiques and restaurants, and 60-minute direct NJ Transit service to Hoboken/NYC. Median sale prices around $1.25M with many 1-3 acre lots. The Somerset Hills Regional district (shared with Bedminster, Peapack-Gladstone, and Far Hills) ranks among the top 10% statewide.'),
     'why':('Bernardsville combines Morris-County-level school quality with the land and estate character of horse country — rare at this commute distance.')},
    {'slug':'bound-brook', 'name':'Bound Brook', 'zip':'08805',
     'median':'$450,000', 'commute':'50', 'schools':'6/10',
     'district':'Bound Brook School District',
     'intro':('Bound Brook offers one of the sharpest value plays in Somerset County — a historic borough with a walkable Main Street, a NJ Transit Raritan Valley Line station that puts NYC within 50 minutes, and median prices around $450K. Buyers priced out of Cranford or Westfield often land here, getting similar housing stock for 35-40% less.'),
     'why':('Bound Brook is the Somerset County entry-level commuter market — full train service, walkable downtown, sub-$500K median.')},
    {'slug':'branchburg', 'name':'Branchburg', 'zip':'08876',
     'median':'$625,000', 'commute':'75', 'schools':'8/10',
     'district':'Branchburg Township Public Schools',
     'intro':('Branchburg is a residential Somerset Co township west of Bridgewater — wooded lots, solid 8/10 schools, and proximity to Raritan Valley Community College and Rutgers. Median sale prices around $625K. The commute to NYC is longer at 75+ minutes via Raritan Valley Line with transfer, so Branchburg buyers are usually trading commute for space and schools.'),
     'why':('Branchburg delivers substantial lot sizes and good schools for roughly half the price of comparable Morris County towns.')},
    {'slug':'bridgewater', 'name':'Bridgewater', 'zip':'08807',
     'median':'$675,000', 'commute':'55', 'schools':'8/10',
     'district':'Bridgewater-Raritan Regional School District',
     'intro':('Bridgewater is Somerset County\'s largest population center — a mix of retail (Bridgewater Commons mall), corporate offices, and residential neighborhoods, with NJ Transit\'s Raritan Valley Line providing 55-minute service to NYC. Median sale prices around $675K for a wide inventory range from 1950s ranches to 2000s-era colonials. The Bridgewater-Raritan Regional district serves both towns with strong 8/10 schools.'),
     'why':('Bridgewater offers the deepest inventory and most retail convenience in Somerset County — ideal for buyers who want suburban amenities without moving farther west.')},
    {'slug':'far-hills', 'name':'Far Hills', 'zip':'07931',
     'median':'$1,400,000', 'commute':'65', 'schools':'9/10',
     'district':'Somerset Hills Regional',
     'intro':('Far Hills is the smallest Somerset Hills town by population but arguably its most prestigious — the Far Hills Race Meeting draws 30,000 spectators annually, and the Ryland Inn and Essex Hunt Club anchor the town\'s horse-country identity. Median sale prices around $1.4M with many estate properties on 5+ acre lots. NJ Transit Gladstone Branch stop is a 65-minute ride to NYC.'),
     'why':('Far Hills is where Manhattan executives put down horse-country roots — and it still has direct NYC train service, which rural Hunterdon/Warren towns do not.')},
    {'slug':'franklin-township', 'name':'Franklin Township', 'zip':'08823',
     'median':'$475,000', 'commute':'80', 'schools':'7/10',
     'district':'Franklin Township Public Schools',
     'intro':('Franklin Township (Somerset Co, distinct from Warren Co Franklin Twp) includes the Somerset section, with diverse neighborhoods from Griggstown to East Franklin. Median sale prices around $475K make Franklin one of the most affordable Somerset communities. The commute is 80 minutes via Princeton Junction or New Brunswick with transfer — longer than other Somerset towns but the pricing reflects it.'),
     'why':('Franklin Twp offers Somerset County address at below-$500K pricing — rare in the region.')},
    {'slug':'green-brook', 'name':'Green Brook', 'zip':'08812',
     'median':'$575,000', 'commute':'55', 'schools':'8/10',
     'district':'Green Brook Township Public Schools',
     'intro':('Green Brook is a compact Somerset Co township on the Watchung Ridge — solid 8/10 schools, median prices around $575K, and 55-minute NJ Transit access via the Raritan Valley Line through Plainfield. Green Brook feels smaller and more residential than neighboring Bridgewater or Watchung.'),
     'why':('Green Brook provides solid schools and manageable commute at a price point 20% below neighboring Watchung.')},
    {'slug':'hillsborough', 'name':'Hillsborough', 'zip':'08844',
     'median':'$550,000', 'commute':'80', 'schools':'8/10',
     'district':'Hillsborough Township Public Schools',
     'intro':('Hillsborough is one of Somerset County\'s largest townships by area — a residential community with 8/10 schools, median sale prices around $550K, and substantial 2000s-era colonial housing stock. The commute to NYC is 80+ minutes via Raritan Valley Line transfer, so Hillsborough suits buyers prioritizing space and schools over commute speed.'),
     'why':('Hillsborough delivers more-recent housing stock (many homes built 1995-2015) than most Somerset County — attractive to buyers who want minimal renovation.')},
    {'slug':'manville', 'name':'Manville', 'zip':'08835',
     'median':'$395,000', 'commute':'70', 'schools':'6/10',
     'district':'Manville School District',
     'intro':('Manville is Somerset County\'s most affordable borough — median sale prices around $395K, compact 2.4-square-mile geography, and NJ Transit Raritan Valley Line access with 70-minute commute to NYC. The borough is working to rebuild after historic flooding along the Raritan River; buyers here are often first-time homeowners or investors.'),
     'why':('Manville is the entry-level Somerset Co price point — sub-$400K median is rare anywhere in the region.')},
    {'slug':'millstone', 'name':'Millstone', 'zip':'08844',
     'median':'$650,000', 'commute':'80', 'schools':'8/10',
     'district':'Hillsborough Township Public Schools (shared)',
     'intro':('Millstone is Somerset County\'s smallest municipality by population (under 500 residents) — a historic borough along the Millstone River with preserved colonial homes and a rural feel despite being minutes from Hillsborough. Median sale prices around $650K, with very limited inventory turnover.'),
     'why':('Millstone is as close to "historic village" as Somerset County gets — tiny, preserved, genuinely quiet.')},
    {'slug':'montgomery', 'name':'Montgomery', 'zip':'08558',
     'median':'$950,000', 'commute':'75', 'schools':'10/10',
     'district':'Montgomery Township School District',
     'intro':('Montgomery Township sits on Somerset County\'s southern edge, adjacent to Princeton — and it shows in the median sale prices around $950K and top-ranked 10/10 schools. Many residents commute to Princeton employers (university, biotech corridor) rather than NYC directly. The NJ Transit Princeton Junction station is a 15-minute drive.'),
     'why':('Montgomery gives you Princeton-area schools and access without Princeton-proper pricing — median $950K vs $1.3M+ in Princeton.')},
    {'slug':'north-plainfield', 'name':'North Plainfield', 'zip':'07060',
     'median':'$425,000', 'commute':'55', 'schools':'6/10',
     'district':'North Plainfield School District',
     'intro':('North Plainfield is a working-class Somerset borough on the Watchung slope — median sale prices around $425K, direct NJ Transit service on the Raritan Valley Line with 55-minute commute, and a diverse community. North Plainfield buyers typically want the commute convenience without Watchung/Green Brook pricing.'),
     'why':('North Plainfield offers Raritan Valley train service at the lowest price point on the line — typically $100K+ below neighboring Watchung.')},
    {'slug':'raritan', 'name':'Raritan', 'zip':'08869',
     'median':'$475,000', 'commute':'55', 'schools':'8/10',
     'district':'Bridgewater-Raritan Regional',
     'intro':('Raritan Borough is a compact Somerset Co town adjacent to Bridgewater, sharing the 8/10 Bridgewater-Raritan Regional schools. Median sale prices around $475K — meaningfully below Bridgewater proper. The Raritan NJ Transit station puts NYC at 55 minutes via the Raritan Valley Line.'),
     'why':('Raritan lets you buy into the Bridgewater-Raritan school district at 30% less than Bridgewater proper.')},
    {'slug':'rocky-hill', 'name':'Rocky Hill', 'zip':'08553',
     'median':'$850,000', 'commute':'75', 'schools':'9/10',
     'district':'Montgomery Township School District',
     'intro':('Rocky Hill is a tiny Somerset Co borough (under 800 residents) sharing Montgomery\'s schools — preserved historic homes, a walkable Main Street, and median sale prices around $850K. Rocky Hill appeals to buyers who want small-village character with access to Princeton\'s amenities 8 miles south.'),
     'why':('Rocky Hill is the smallest municipality in our Somerset coverage — if you want village life with a Princeton-area ZIP, this is it.')},
    {'slug':'somerville', 'name':'Somerville', 'zip':'08876',
     'median':'$485,000', 'commute':'55', 'schools':'7/10',
     'district':'Somerville Public Schools',
     'intro':('Somerville is the Somerset County seat — a walkable downtown along Main Street with restaurants, shops, the historic county courthouse, and a NJ Transit Raritan Valley Line station offering 55-minute commute to NYC. Median sale prices around $485K, with substantial 1920s-1940s housing stock in the walkable downtown radius.'),
     'why':('Somerville is Somerset County\'s walkable downtown — true main-street living with NJ Transit commuter service, rare at this price.')},
    {'slug':'south-bound-brook', 'name':'South Bound Brook', 'zip':'08880',
     'median':'$425,000', 'commute':'55', 'schools':'6/10',
     'district':'South Bound Brook School District',
     'intro':('South Bound Brook is a compact (0.5 sq mi) Somerset Co borough along the Raritan River — median sale prices around $425K, walking distance to Bound Brook\'s NJ Transit station. Buyers here typically want the walkable-downtown/commuter convenience of Bound Brook at a slightly lower price point.'),
     'why':('South Bound Brook offers sub-$450K housing within a 10-minute walk to a Raritan Valley Line train station.')},
]


def _replace(html: str, t: dict) -> str:
    """Substitute Basking Ridge data with the new town's."""
    name = t['name']; slug = t['slug']
    out = html
    out = out.replace('Basking Ridge, NJ', f'{name}, NJ')
    out = out.replace('Basking Ridge NJ', f'{name} NJ')
    out = out.replace('Basking Ridge', name)
    out = out.replace('basking-ridge', slug)
    out = re.sub(r'\b07920\b', t['zip'], out)
    return out


def _intro_block(t: dict) -> str:
    return (
        f'\n<section class="town-intro-unique" style="max-width:860px;'
        f'margin:2rem auto;padding:1.5rem 2rem;border-left:4px solid #BF9D5B;'
        f'background:#FAFAFA;">\n'
        f'<p style="font-size:1.05rem;line-height:1.6;color:#333;margin:0 0 1rem;">'
        f'{t["intro"]}</p>\n'
        f'<p style="font-size:0.95rem;line-height:1.6;color:#555;margin:0;">'
        f'{t["why"]}</p>\n'
        f'<p style="font-size:0.85rem;margin-top:1.2rem;color:#888;">'
        f'<strong>Quick facts:</strong> '
        f'Median sale price around {t["median"]} &nbsp;•&nbsp; '
        f'{t["commute"]} min to NYC &nbsp;•&nbsp; '
        f'Schools: {t["schools"]} ({t["district"]}) &nbsp;•&nbsp; '
        f'ZIP {t["zip"]} &nbsp;•&nbsp; Somerset County, NJ.</p>\n'
        f'</section>\n'
    )


def main():
    if not TEMPLATE.exists():
        print(f'ERROR: template missing: {TEMPLATE}', file=sys.stderr)
        return 1
    tmpl = TEMPLATE.read_text(encoding='utf-8')

    print(f'Template: {TEMPLATE.name}  ({len(tmpl)} chars)')
    created = 0
    for t in SOMERSET:
        p = ROOT / 'towns' / f'{t["slug"]}.html'
        if p.exists():
            print(f'  [skip] {t["slug"]} already exists')
            continue
        out = _replace(tmpl, t)
        m = re.search(r'</h1>', out)
        if m:
            out = out[:m.end()] + _intro_block(t) + out[m.end():]
        p.write_text(out, encoding='utf-8')
        print(f'  ✓ {t["slug"]:26s} {len(out)} chars')
        created += 1

    print(f'\nGenerated {created} new Somerset towns')

    # Spanish stubs
    sys.path.insert(0, str(ROOT))
    from translate_to_spanish import translate_page
    es_ok = 0
    for t in SOMERSET:
        src = ROOT / 'towns' / f'{t["slug"]}.html'
        if src.exists() and translate_page(src):
            es_ok += 1
    print(f'Spanish stubs: {es_ok} ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
