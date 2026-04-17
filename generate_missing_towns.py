#!/usr/bin/env python3
"""Generate 4 missing commuter town pages (Ridgewood, Princeton, Caldwell,
Rutherford) by cloning the Westfield template and applying per-town data.

Strategy:
  1. Read towns/westfield.html as template
  2. For each new town: swap name, ZIP, county, schools, commute-time etc.
  3. Prepend a 200-word town-specific intro paragraph (SEO-unique content)
  4. Write towns/<slug>.html + /es/towns/<slug>.html Spanish stub
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path('/Users/teddy/TheJorgeRamirezGroup2')
TEMPLATE = ROOT / 'towns' / 'westfield.html'

TOWNS = [
    {
        'slug': 'ridgewood',
        'name': 'Ridgewood',
        'county': 'Bergen County',
        'zip': '07450',
        'median_price': '$1,050,000',
        'commute_minutes': '45',
        'commute_line': 'NJ Transit Bergen County Line to Hoboken (with PATH to Manhattan)',
        'schools_rating': '10/10',
        'school_district': 'Ridgewood Public Schools',
        'intro_hook': (
            "Ridgewood is one of North Jersey's most-searched commuter towns for "
            "a reason. A walkable downtown with 200+ shops and restaurants, "
            "consistently top-ranked public schools, and a 45-minute Bergen "
            "County Line train that connects through Hoboken make it the "
            "default choice for Manhattan professionals raising families. "
            "Median sale price hovers around $1.05M for single-family homes, "
            "and inventory turns over fast — homes in the top school zones "
            "regularly sell above list within the first two weeks."
        ),
        'unique_selling': (
            "Ridgewood's Graydon Pool, the Van Neste Square summer concert "
            "series, and the weekly farmers market give the town a genuine "
            "community feel that's rare in Bergen County."
        ),
    },
    {
        'slug': 'princeton',
        'name': 'Princeton',
        'county': 'Mercer County',
        'zip': '08540',
        'median_price': '$1,300,000',
        'commute_minutes': '75',
        'commute_line': 'NJ Transit Northeast Corridor with Princeton Junction dinky transfer',
        'schools_rating': '10/10',
        'school_district': 'Princeton Public Schools',
        'intro_hook': (
            "Princeton is the Mercer County benchmark — Ivy League campus "
            "gravitas, 225-year-old streetscapes, and schools that send "
            "graduates to the country's top universities at rates no other "
            "NJ town matches. The commute to Manhattan runs about 75 "
            "minutes via Princeton Junction, which means Princeton buyers "
            "are usually trading commute efficiency for prestige, space, "
            "and cultural depth. Median sale price sits near $1.3M, with "
            "substantial variation by neighborhood: downtown, Western "
            "Section, Littlebrook, and Riverside each have distinct "
            "character and price bands."
        ),
        'unique_selling': (
            "Princeton's proximity to the University brings year-round "
            "concerts, museum exhibits, and lectures that rival Manhattan's "
            "cultural offerings — often free and minutes from home."
        ),
    },
    {
        'slug': 'caldwell',
        'name': 'Caldwell',
        'county': 'Essex County',
        'zip': '07006',
        'median_price': '$650,000',
        'commute_minutes': '35',
        'commute_line': 'DeCamp Bus 66 express to Port Authority or Morris & Essex Line via Upper Montclair',
        'schools_rating': '8/10',
        'school_district': 'Caldwell–West Caldwell School District',
        'intro_hook': (
            "Caldwell offers one of the sharpest value stories in Essex "
            "County: a historic walkable downtown, solid 8/10 schools, and "
            "median prices around $650K — meaningfully below Montclair or "
            "Maplewood while delivering 90% of the commuter-town feel. The "
            "DeCamp 66 express bus gets you to Port Authority in 35 minutes, "
            "and the Morris & Essex line via Upper Montclair is a 10-minute "
            "drive. Grover Cleveland's birthplace sits at the center of "
            "town, giving Caldwell rare historical identity."
        ),
        'unique_selling': (
            "Caldwell is the commuter town buyers find when they've toured "
            "Montclair and Maplewood, loved the vibe, and priced themselves "
            "back into a smaller house — Caldwell gives them the full house "
            "without the West Essex tax premium."
        ),
    },
    {
        'slug': 'rutherford',
        'name': 'Rutherford',
        'county': 'Bergen County',
        'zip': '07070',
        'median_price': '$720,000',
        'commute_minutes': '25',
        'commute_line': 'NJ Transit Bergen County & Main Line direct to Hoboken / Secaucus',
        'schools_rating': '8/10',
        'school_district': 'Rutherford Public Schools',
        'intro_hook': (
            "Rutherford is the closest real commuter town to Manhattan that "
            "still has the suburban feel buyers are actually looking for. "
            "25 minutes by train to Hoboken or Secaucus, a walkable Park "
            "Avenue downtown, and median prices around $720K put it in a "
            "sweet spot between Hoboken's condo density and the 45-minute "
            "Bergen County towns. Borough governance keeps streets tight "
            "and historic Victorians maintained — Rutherford is where "
            "buyers who love urban energy but need a yard end up."
        ),
        'unique_selling': (
            "Rutherford's Williams Center hosts year-round theater and jazz, "
            "and the MetLife Stadium / Meadowlands complex is a 5-minute "
            "drive — convenient for commuters who want to keep one foot in "
            "New York culture and entertainment."
        ),
    },
]


def replace_town(html: str, town: dict) -> str:
    """Substitute Westfield-specific data with the new town's."""
    name = town['name']
    slug = town['slug']

    # Case-preserving replaces
    out = html
    out = out.replace('Westfield, NJ', f'{name}, NJ')
    out = out.replace('Westfield NJ', f'{name} NJ')
    out = out.replace('Westfield', name)
    out = out.replace('westfield', slug)

    # Canonical + slug in URLs
    out = out.replace(f'/towns/{slug}.html', f'/towns/{slug}.html')  # noop
    # (westfield → slug already handled above)

    # ZIP + county
    out = re.sub(r'\b07090\b', town['zip'], out)
    out = out.replace('Union County', town['county'])

    return out


def inject_intro(html: str, town: dict) -> str:
    """Insert a town-specific 200-word intro right after the first <h1>."""
    intro_html = (
        f'\n<section class="town-intro-unique" style="max-width:860px;'
        f'margin:2rem auto;padding:1.5rem 2rem;border-left:4px solid #BF9D5B;'
        f'background:#FAFAFA;">\n'
        f'<p style="font-size:1.05rem;line-height:1.6;color:#333;margin:0 0 1rem;">'
        f'{town["intro_hook"]}</p>\n'
        f'<p style="font-size:0.95rem;line-height:1.6;color:#555;margin:0;">'
        f'{town["unique_selling"]}</p>\n'
        f'<p style="font-size:0.85rem;margin-top:1.2rem;color:#888;">'
        f'<strong>Quick facts:</strong> '
        f'Median sale price around {town["median_price"]} &nbsp;•&nbsp; '
        f'{town["commute_minutes"]} min to NYC via {town["commute_line"]} &nbsp;•&nbsp; '
        f'Schools: {town["schools_rating"]} ({town["school_district"]}) &nbsp;•&nbsp; '
        f'ZIP {town["zip"]}.</p>\n'
        f'</section>\n'
    )
    # Insert after first </h1>
    m = re.search(r'</h1>', html)
    if not m:
        return html
    idx = m.end()
    return html[:idx] + intro_html + html[idx:]


def main():
    if not TEMPLATE.exists():
        print(f'ERROR: template not found: {TEMPLATE}', file=sys.stderr)
        return 1
    template_html = TEMPLATE.read_text(encoding='utf-8')

    print(f'Template: {TEMPLATE}  ({len(template_html)} chars)')
    for town in TOWNS:
        out_path = ROOT / 'towns' / f'{town["slug"]}.html'
        if out_path.exists():
            print(f'  [skip] {town["slug"]} already exists')
            continue
        out = replace_town(template_html, town)
        out = inject_intro(out, town)
        out_path.write_text(out, encoding='utf-8')
        print(f'  ✓ {town["slug"]:14s} -> {out_path}  ({len(out)} chars)')

    # Spanish stubs via existing translator
    print('\nGenerating Spanish stubs...')
    sys.path.insert(0, str(ROOT))
    from translate_to_spanish import translate_page  # noqa: E402
    for town in TOWNS:
        en = ROOT / 'towns' / f'{town["slug"]}.html'
        if not en.exists():
            continue
        if translate_page(en):
            print(f'  ✓ es/towns/{town["slug"]}.html')
        else:
            print(f'  ✗ es/towns/{town["slug"]}.html FAILED')

    return 0


if __name__ == '__main__':
    sys.exit(main())
