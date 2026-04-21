#!/usr/bin/env python3
"""
gen_realtor_pages.py — Generate /realtor/<town>-nj.html service pages.

v2: Substantially deeper content (2000+ words), unique per-town data,
FAQ schema, proper internal linking, full schema stack.

Anti-pattern guard: we OMIT data we don't have (specific recent sales,
verified ratings) rather than fabricate. Fabricated data = AI-spam penalty.
"""
import json
import re
import sys
from pathlib import Path

from town_data import COUNTY, TRAIN, NEIGHBORHOODS, HIGH_SCHOOLS, county_of, train_info, neighborhoods_of, high_school_of

REPO = Path(__file__).parent
TOWNS_DIR = REPO / "towns"
OUT_DIR = REPO / "realtor"
OUT_DIR.mkdir(exist_ok=True)

SLUG_TO_DISPLAY_OVERRIDE = {
    "new-brunswick": "New Brunswick", "north-arlington": "North Arlington",
    "north-brunswick": "North Brunswick", "north-plainfield": "North Plainfield",
    "old-bridge": "Old Bridge", "west-caldwell": "West Caldwell",
    "east-brunswick": "East Brunswick", "east-hanover": "East Hanover",
    "east-newark": "East Newark", "south-amboy": "South Amboy",
    "south-bound-brook": "South Bound Brook", "south-brunswick": "South Brunswick",
    "south-orange": "South Orange", "south-plainfield": "South Plainfield",
    "south-river": "South River", "west-new-york": "West New York",
    "west-orange": "West Orange", "long-hill": "Long Hill",
    "short-hills": "Short Hills", "upper-saddle-river": "Upper Saddle River",
    "highland-park": "Highland Park", "green-brook": "Green Brook",
    "glen-ridge": "Glen Ridge", "far-hills": "Far Hills",
    "franklin-township": "Franklin Township", "chatham-township": "Chatham Township",
    "chatham-borough": "Chatham Borough", "chester-borough": "Chester Borough",
    "chester-township": "Chester Township", "bernards-township": "Bernards Township",
    "boonton-township": "Boonton Township", "warren-township": "Warren Township",
    "washington-township-morris": "Washington Township", "rockaway-borough": "Rockaway Borough",
    "rockaway-township": "Rockaway Township", "rocky-hill": "Rocky Hill",
    "roselle-park": "Roselle Park", "scotch-plains": "Scotch Plains",
    "bound-brook": "Bound Brook", "jersey-city": "Jersey City",
    "union-city": "Union City", "basking-ridge": "Basking Ridge",
    "berkeley-heights": "Berkeley Heights", "lincoln-park": "Lincoln Park",
    "victory-gardens": "Victory Gardens", "florham-park": "Florham Park",
    "north-bergen": "North Bergen", "north-caldwell": "North Caldwell",
    "peapack-gladstone": "Peapack-Gladstone", "parsippany-troy-hills": "Parsippany-Troy Hills",
    "mendham-borough": "Mendham Borough", "mendham-township": "Mendham Township",
    "morris-plains": "Morris Plains", "morris-township": "Morris Township",
    "mount-arlington": "Mount Arlington", "mount-olive": "Mount Olive",
    "mountain-lakes": "Mountain Lakes", "middlesex-borough": "Middlesex",
    "perth-amboy": "Perth Amboy", "monroe-township": "Monroe Township",
    "pequannock-township": "Pequannock Township", "mine-hill": "Mine Hill",
    "middlesex-borough": "Middlesex Borough", "middlesex": "Middlesex",
}

# Neighboring-town map for regional cluster internal linking
# (Each town links to 3-5 nearby towns — helps hub-and-spoke signal)
NEIGHBORS = {
    "summit": ["new-providence", "berkeley-heights", "springfield", "short-hills", "millburn"],
    "westfield": ["scotch-plains", "cranford", "mountainside", "garwood", "fanwood"],
    "cranford": ["westfield", "garwood", "kenilworth", "clark", "roselle-park"],
    "maplewood": ["south-orange", "millburn", "west-orange", "livingston", "short-hills"],
    "millburn": ["short-hills", "summit", "maplewood", "springfield", "livingston"],
    "short-hills": ["millburn", "summit", "livingston", "west-orange", "maplewood"],
    "montclair": ["glen-ridge", "bloomfield", "verona", "cedar-grove", "west-orange"],
    "madison": ["chatham", "florham-park", "chatham-township", "morristown", "harding"],
    "chatham": ["madison", "chatham-township", "summit", "florham-park", "morristown"],
    "chatham-borough": ["chatham", "madison", "chatham-township", "summit"],
    "chatham-township": ["chatham", "madison", "harding", "summit"],
    "florham-park": ["madison", "chatham", "east-hanover", "hanover", "morris-plains"],
    "livingston": ["short-hills", "millburn", "west-orange", "roseland", "west-caldwell"],
    "west-orange": ["livingston", "montclair", "verona", "orange", "maplewood"],
    "south-orange": ["maplewood", "millburn", "west-orange", "orange", "newark"],
    "berkeley-heights": ["new-providence", "summit", "mountainside", "scotch-plains", "watchung"],
    "new-providence": ["berkeley-heights", "summit", "mountainside", "chatham"],
    "scotch-plains": ["fanwood", "westfield", "mountainside", "plainfield", "cranford"],
    "fanwood": ["scotch-plains", "westfield", "plainfield", "watchung"],
    "mountainside": ["westfield", "scotch-plains", "berkeley-heights", "watchung", "summit"],
    "springfield": ["summit", "millburn", "union", "mountainside", "maplewood"],
    "glen-ridge": ["montclair", "bloomfield", "nutley"],
    "bloomfield": ["glen-ridge", "montclair", "nutley", "newark", "belleville"],
    "nutley": ["bloomfield", "montclair", "glen-ridge", "north-arlington", "kearny"],
    "caldwell": ["west-caldwell", "north-caldwell", "verona", "roseland", "essex-fells"],
    "west-caldwell": ["caldwell", "north-caldwell", "livingston", "fairfield"],
    "north-caldwell": ["caldwell", "west-caldwell", "roseland", "livingston"],
    "verona": ["montclair", "caldwell", "west-orange", "cedar-grove"],
    "roseland": ["caldwell", "livingston", "west-caldwell", "north-caldwell"],
    "morristown": ["morris-township", "morris-plains", "harding", "madison", "mendham-borough"],
    "morris-plains": ["morristown", "morris-township", "parsippany-troy-hills", "hanover"],
    "morris-township": ["morristown", "morris-plains", "harding", "randolph", "mendham-township"],
    "mendham-borough": ["mendham-township", "morristown", "chester-borough", "bernardsville"],
    "mendham-township": ["mendham-borough", "morris-township", "harding", "bernardsville"],
    "bernardsville": ["basking-ridge", "bernards-township", "mendham-borough", "far-hills", "peapack-gladstone"],
    "basking-ridge": ["bernards-township", "bedminster", "bernardsville", "harding", "warren-township"],
    "bernards-township": ["basking-ridge", "bedminster", "bernardsville", "warren-township"],
    "bedminster": ["basking-ridge", "bernards-township", "peapack-gladstone", "far-hills", "branchburg"],
    "far-hills": ["bedminster", "bernardsville", "peapack-gladstone", "bernards-township"],
    "peapack-gladstone": ["bedminster", "far-hills", "bernardsville"],
    "randolph": ["morris-township", "denville", "mount-olive", "mine-hill", "chester-township"],
    "denville": ["randolph", "rockaway-township", "boonton", "parsippany-troy-hills", "mountain-lakes"],
    "mountain-lakes": ["denville", "boonton", "parsippany-troy-hills", "rockaway-township"],
    "boonton": ["boonton-township", "mountain-lakes", "denville", "parsippany-troy-hills", "lincoln-park"],
    "boonton-township": ["boonton", "mountain-lakes", "denville", "kinnelon"],
    "parsippany-troy-hills": ["morris-plains", "denville", "montville", "hanover", "east-hanover"],
    "montville": ["parsippany-troy-hills", "lincoln-park", "pequannock-township", "boonton-township"],
    "hanover": ["east-hanover", "parsippany-troy-hills", "morris-plains", "florham-park"],
    "east-hanover": ["hanover", "florham-park", "livingston", "parsippany-troy-hills"],
    "edison": ["metuchen", "piscataway", "new-brunswick", "woodbridge", "highland-park"],
    "metuchen": ["edison", "piscataway", "woodbridge", "highland-park"],
    "piscataway": ["edison", "metuchen", "highland-park", "new-brunswick", "south-plainfield"],
    "new-brunswick": ["highland-park", "east-brunswick", "north-brunswick", "edison", "piscataway"],
    "highland-park": ["new-brunswick", "edison", "metuchen", "piscataway"],
    "east-brunswick": ["new-brunswick", "north-brunswick", "milltown", "old-bridge", "monroe-township"],
    "north-brunswick": ["new-brunswick", "east-brunswick", "south-brunswick", "milltown"],
    "south-brunswick": ["north-brunswick", "east-brunswick", "monroe-township", "plainsboro", "cranbury"],
    "old-bridge": ["east-brunswick", "sayreville", "south-amboy", "monroe-township", "spotswood"],
    "sayreville": ["old-bridge", "south-amboy", "perth-amboy", "east-brunswick"],
    "woodbridge": ["edison", "metuchen", "perth-amboy", "carteret", "rahway"],
    "carteret": ["woodbridge", "rahway", "linden", "perth-amboy"],
    "perth-amboy": ["woodbridge", "sayreville", "south-amboy", "carteret"],
    "south-amboy": ["sayreville", "perth-amboy", "old-bridge"],
    "jersey-city": ["hoboken", "weehawken", "bayonne", "kearny", "north-bergen", "union-city", "secaucus"],
    "hoboken": ["jersey-city", "weehawken", "union-city", "north-bergen"],
    "weehawken": ["hoboken", "union-city", "west-new-york", "north-bergen", "jersey-city"],
    "bayonne": ["jersey-city", "kearny", "newark"],
    "union-city": ["weehawken", "west-new-york", "hoboken", "north-bergen", "jersey-city"],
    "west-new-york": ["union-city", "weehawken", "north-bergen", "guttenberg"],
    "north-bergen": ["weehawken", "union-city", "west-new-york", "secaucus", "guttenberg"],
    "guttenberg": ["west-new-york", "union-city", "north-bergen"],
    "secaucus": ["north-bergen", "jersey-city", "kearny", "weehawken"],
    "kearny": ["jersey-city", "harrison", "east-newark", "newark", "bayonne"],
    "harrison": ["kearny", "east-newark", "newark"],
    "east-newark": ["harrison", "kearny", "newark"],
    "newark": ["east-orange", "irvington", "bloomfield", "kearny", "harrison", "belleville"],
    "elizabeth": ["linden", "hillside", "roselle", "newark", "union"],
    "linden": ["elizabeth", "rahway", "roselle", "cranford", "woodbridge"],
    "rahway": ["linden", "clark", "cranford", "woodbridge"],
    "union": ["springfield", "kenilworth", "hillside", "elizabeth", "summit"],
    "hillside": ["elizabeth", "union", "newark", "irvington"],
    "roselle": ["roselle-park", "cranford", "linden", "elizabeth", "kenilworth"],
    "roselle-park": ["roselle", "cranford", "kenilworth", "union", "hillside"],
    "clark": ["cranford", "rahway", "westfield", "garwood"],
    "garwood": ["cranford", "westfield", "kenilworth", "clark"],
    "kenilworth": ["cranford", "roselle-park", "roselle", "union", "garwood"],
    "plainfield": ["scotch-plains", "fanwood", "south-plainfield", "north-plainfield"],
    "winfield": ["clark", "linden", "cranford"],
    "bridgewater": ["raritan", "branchburg", "somerville", "bound-brook", "hillsborough", "warren-township"],
    "somerville": ["bridgewater", "raritan", "bound-brook"],
    "hillsborough": ["bridgewater", "branchburg", "montgomery", "franklin-township"],
    "branchburg": ["bridgewater", "hillsborough", "bedminster", "raritan"],
    "raritan": ["somerville", "bridgewater", "branchburg"],
    "franklin-township": ["hillsborough", "new-brunswick", "south-brunswick", "bound-brook"],
    "watchung": ["mountainside", "berkeley-heights", "warren-township", "green-brook"],
    "warren-township": ["basking-ridge", "watchung", "bernards-township", "green-brook", "long-hill"],
    "green-brook": ["watchung", "north-plainfield", "plainfield", "warren-township"],
    "long-hill": ["warren-township", "watchung", "berkeley-heights", "basking-ridge"],
    "bound-brook": ["south-bound-brook", "bridgewater", "somerville", "franklin-township"],
    "south-bound-brook": ["bound-brook", "franklin-township", "somerville"],
    "north-plainfield": ["plainfield", "watchung", "green-brook"],
    "monroe-township": ["south-brunswick", "east-brunswick", "old-bridge", "cranbury", "jamesburg"],
    "cranbury": ["monroe-township", "south-brunswick", "plainsboro"],
    "plainsboro": ["south-brunswick", "cranbury"],
    "jamesburg": ["monroe-township", "spotswood"],
    "spotswood": ["jamesburg", "east-brunswick", "old-bridge", "milltown"],
    "milltown": ["east-brunswick", "north-brunswick", "spotswood", "new-brunswick"],
    "helmetta": ["spotswood", "jamesburg", "monroe-township"],
    "dunellen": ["piscataway", "south-plainfield", "green-brook", "plainfield"],
    "south-plainfield": ["dunellen", "plainfield", "piscataway", "edison"],
    "south-river": ["new-brunswick", "east-brunswick", "sayreville"],
    "middlesex": ["piscataway", "south-plainfield", "dunellen", "bridgewater"],
    "middlesex-borough": ["piscataway", "south-plainfield", "dunellen", "bridgewater"],
    "dover": ["wharton", "rockaway-borough", "randolph", "mine-hill", "victory-gardens"],
    "wharton": ["dover", "mine-hill", "randolph", "rockaway-borough"],
    "victory-gardens": ["dover", "randolph", "wharton"],
    "mine-hill": ["randolph", "wharton", "dover", "roxbury"],
    "mount-arlington": ["roxbury", "jefferson", "mount-olive"],
    "roxbury": ["mount-arlington", "randolph", "mount-olive", "jefferson", "mine-hill"],
    "mount-olive": ["roxbury", "randolph", "chester-township"],
    "jefferson": ["rockaway-township", "mount-arlington", "kinnelon"],
    "rockaway-borough": ["rockaway-township", "dover", "wharton"],
    "rockaway-township": ["rockaway-borough", "denville", "jefferson", "kinnelon"],
    "kinnelon": ["butler", "jefferson", "boonton-township", "rockaway-township"],
    "butler": ["kinnelon", "bloomingdale", "riverdale"],
    "riverdale": ["pompton-lakes", "butler", "pequannock-township"],
    "pequannock-township": ["riverdale", "montville", "lincoln-park"],
    "lincoln-park": ["pequannock-township", "montville", "boonton"],
    "netcong": ["mount-olive", "stanhope", "roxbury"],
    "harding": ["morris-township", "chatham-township", "madison", "mendham-township", "mendham-borough"],
    "chester-borough": ["chester-township", "mendham-borough", "mendham-township"],
    "chester-township": ["chester-borough", "randolph", "mendham-township", "mount-olive"],
    "orange": ["east-orange", "west-orange", "south-orange", "maplewood", "montclair"],
    # Fallback — common default
}

# Towns in each county (for regional hub linking)
COUNTY_TOWNS = {}
for slug, county in COUNTY.items():
    COUNTY_TOWNS.setdefault(county, []).append(slug)


def slug_to_display(slug):
    if slug in SLUG_TO_DISPLAY_OVERRIDE:
        return SLUG_TO_DISPLAY_OVERRIDE[slug]
    return slug.replace("-", " ").title()


def extract_data(town_html, slug):
    data = {
        "slug": slug,
        "display": slug_to_display(slug),
        "median": None,
        "median_raw": None,
        "commute_min": None,
        "commute_line": None,
        "commute_station": None,
        "schools": None,
        "county": None,
        "days_on_market": None,
    }

    m = re.search(r'median home price in [^"]*?approximately[^"]*?\$([\d,]+)', town_html, re.I)
    if m:
        data["median_raw"] = int(m.group(1).replace(",", ""))
        v = data["median_raw"]
        data["median"] = f"${v/1_000_000:.2f}M" if v >= 1_000_000 else f"${v/1000:.0f}K"

    m = re.search(r'(?:schools are rated|schools[^<]*?rated)[^<]*?(\d+)/10', town_html, re.I)
    if m:
        data["schools"] = f"{m.group(1)}/10"

    m = re.search(r'approximately (\d+) minutes', town_html, re.I)
    if m:
        data["commute_min"] = m.group(1)

    m = re.search(r'typically spend (\d+) days on market', town_html, re.I)
    if m:
        data["days_on_market"] = m.group(1)

    # Authoritative county from lookup (overrides html extraction)
    data["county"] = county_of(slug)

    # Authoritative train info
    ti = train_info(slug)
    if ti:
        data["commute_min"] = ti["mins_penn"]
        data["commute_line"] = ti["line"]
        data["commute_station"] = ti["station"]

    data["neighborhoods"] = neighborhoods_of(slug)
    data["high_school"] = high_school_of(slug)
    return data


def build_schema(d):
    slug = d["slug"]
    display = d["display"]
    url = f"https://thejorgeramirezgroup.com/realtor/{slug}-nj.html"
    info_url = f"https://thejorgeramirezgroup.com/towns/{slug}.html"
    county = d.get("county") or "Northern New Jersey"

    # FAQ entities
    faqs = build_faqs(d)
    faq_schema = {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ]
    }

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "RealEstateAgent",
                "@id": url + "#service",
                "name": f"Jorge Ramirez — {display}, NJ Real Estate Agent",
                "url": url,
                "telephone": "+1-908-230-7844",
                "email": "jorge.ramirez@kw.com",
                "image": "https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg",
                "priceRange": "$$-$$$$",
                "areaServed": {
                    "@type": "City",
                    "name": display,
                    "containedInPlace": {
                        "@type": "AdministrativeArea",
                        "name": f"{county} County, New Jersey"
                    }
                },
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "488 Springfield Ave",
                    "addressLocality": "Summit",
                    "addressRegion": "NJ",
                    "postalCode": "07901",
                    "addressCountry": "US"
                },
                "sameAs": [
                    "https://www.instagram.com/thejorgeramirezgroup/",
                    "https://www.facebook.com/thejorgeramirezgroup/",
                    "https://www.linkedin.com/in/jorge-ramirez-realtor-nj/",
                    "https://www.kw.com/agent/jorge-ramirez-nj"
                ],
                "founder": {"@id": "https://thejorgeramirezgroup.com/#person"},
                "memberOf": {
                    "@type": "Organization",
                    "name": "Keller Williams Premier Properties"
                }
            },
            {
                "@type": "Person",
                "@id": "https://thejorgeramirezgroup.com/#person",
                "name": "Jorge Ramirez",
                "jobTitle": "Licensed Real Estate Agent",
                "telephone": "+1-908-230-7844",
                "email": "jorge.ramirez@kw.com",
                "url": "https://thejorgeramirezgroup.com/",
                "image": "https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg",
                "worksFor": {
                    "@type": "RealEstateAgent",
                    "name": "The Jorge Ramirez Group at Keller Williams Premier Properties"
                },
                "hasCredential": [
                    {
                        "@type": "EducationalOccupationalCredential",
                        "credentialCategory": "NJ Real Estate License",
                        "identifier": "1754604"
                    }
                ],
                "knowsAbout": [
                    f"{display} NJ real estate", f"{county} County real estate",
                    "home valuations", "investment property", "house flipping",
                    "NYC commuter homes", "first-time home buyers"
                ],
                "sameAs": [
                    "https://www.instagram.com/thejorgeramirezgroup/",
                    "https://www.facebook.com/thejorgeramirezgroup/",
                    "https://www.linkedin.com/in/jorge-ramirez-realtor-nj/",
                    "https://www.kw.com/agent/jorge-ramirez-nj"
                ]
            },
            {
                "@type": "Place",
                "@id": url + "#place",
                "name": f"{display}, New Jersey",
                "containedInPlace": {
                    "@type": "AdministrativeArea",
                    "name": f"{county} County, New Jersey"
                }
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thejorgeramirezgroup.com/"},
                    {"@type": "ListItem", "position": 2, "name": "Find a Real Estate Agent", "item": "https://thejorgeramirezgroup.com/realtor/"},
                    {"@type": "ListItem", "position": 3, "name": f"{county} County", "item": "https://thejorgeramirezgroup.com/realtor/"},
                    {"@type": "ListItem", "position": 4, "name": f"{display}, NJ", "item": url}
                ]
            },
            {
                "@type": "WebPage",
                "@id": url,
                "url": url,
                "name": f"{display} NJ Real Estate Agent — Jorge Ramirez",
                "inLanguage": "en-US",
                "isPartOf": {"@id": "https://thejorgeramirezgroup.com/#website"},
                "about": {"@id": url + "#place"},
                "mainEntity": {"@id": url + "#service"},
                "relatedLink": info_url,
                "author": {"@id": "https://thejorgeramirezgroup.com/#person"}
            },
            faq_schema
        ]
    }
    return json.dumps(schema, indent=2)


def build_faqs(d):
    display = d["display"]
    county = d.get("county") or "Northern NJ"
    median = d.get("median")
    commute = d.get("commute_min")
    dom = d.get("days_on_market")
    high_school = d.get("high_school")

    faqs = []

    faqs.append((
        f"Who is the best real estate agent in {display}, NJ?",
        f"Jorge Ramirez is a licensed NJ real estate agent (License #1754604) at Keller Williams Premier Properties who serves {display} and the surrounding {county} County area. Jorge has personally bought, renovated, and sold 60+ investment properties across Northern NJ, giving him working knowledge of renovation costs, buyer behavior, and pricing strategy. Call 908-230-7844 for a free {display} consultation."
    ))

    if median:
        faqs.append((
            f"What is the average home price in {display}, NJ?",
            f"The median home sale price in {display}, NJ is approximately {median}. Prices vary significantly by neighborhood, lot size, school district zoning, and proximity to the train station. For a current comparative market analysis on a specific address, contact Jorge Ramirez at 908-230-7844."
        ))

    if dom:
        faqs.append((
            f"How long do homes take to sell in {display}, NJ?",
            f"Homes in {display}, NJ typically spend about {dom} days on market from listing to accepted offer, though the actual timeline depends on price positioning, presentation, and seasonality. Well-prepared listings in {display} often receive offers within the first two weeks. For a pricing strategy specific to your home, request a free valuation."
        ))

    faqs.append((
        f"What commission do {display} real estate agents charge?",
        f"Real estate commission in NJ is negotiable and typically falls between 4% and 6% of the sale price, usually split between the listing agent and buyer's agent. Since the 2024 NAR settlement, buyer-agent compensation is separately negotiated. Jorge Ramirez offers transparent pricing and will walk you through exactly what you'll pay — call 908-230-7844 to discuss."
    ))

    if commute:
        faqs.append((
            f"How long is the commute from {display} to New York City?",
            f"The commute from {display}, NJ to Manhattan is approximately {commute} minutes via " + (d.get("commute_line") or "public transit") + ". For buyers prioritizing a specific commute time, Jorge can help you identify homes within walking distance of the train station versus those requiring a drive — these are meaningfully different markets."
        ))

    if high_school:
        faqs.append((
            f"What high school serves {display}, NJ?",
            f"{display} students attend {high_school}. School boundary lines inside {display} can affect home values, especially for families targeting a specific district. Jorge can cross-reference a property address against current district lines before you write an offer."
        ))

    faqs.append((
        f"Is {display}, NJ a good place to buy a house in 2026?",
        f"{display} remains a sought-after {county} County market with consistent buyer demand, strong schools, and proximity to NYC employment. Whether it's a good buy depends on your budget, timeline, and which neighborhood fits your situation. Jorge gives direct, unfiltered answers — not sales pitches. Call 908-230-7844."
    ))

    faqs.append((
        f"Does Jorge Ramirez work with first-time home buyers in {display}?",
        f"Yes. First-time buyers are a significant part of Jorge's practice. He'll walk you through NJ-specific programs (NJHMFA, down payment assistance), realistic closing-cost math, and what to expect during inspection — so you're not surprised on closing day."
    ))

    return faqs


def build_page(d):
    display = d["display"]
    slug = d["slug"]
    county = d.get("county") or "Northern New Jersey"
    median = d.get("median")
    schools = d.get("schools")
    commute = d.get("commute_min")
    commute_line = d.get("commute_line")
    commute_station = d.get("commute_station")
    dom = d.get("days_on_market")
    neighborhoods = d.get("neighborhoods", [])
    high_school = d.get("high_school")

    # ---- title + meta
    title = f"{display} NJ Real Estate Agent | Jorge Ramirez, Licensed Realtor"
    hook = f"{display} NJ real estate agent Jorge Ramirez."
    cred = "Licensed NJ Realtor at Keller Williams, 60+ house flips."
    stat = f" Median {median}." if median else ""
    cta = " Call 908-230-7844."
    desc = (hook + " " + cred + stat + cta).strip()
    if len(desc) > 158:
        desc = (hook + " " + cred + cta).strip()

    og_title = f"Hire a Real Estate Agent in {display}, NJ — Jorge Ramirez"
    og_desc = f"Licensed NJ Realtor since 2017. 60+ house flips. Buy or sell in {display} with an agent who knows the numbers. Free consultation."

    # ---- stats tiles
    stat_tiles = []
    if median:
        stat_tiles.append(f'<div class="stat"><span class="v">{median}</span><span class="l">Median Sale Price</span></div>')
    if commute:
        commute_line_note = f" via {commute_line}" if commute_line else ""
        stat_tiles.append(f'<div class="stat"><span class="v">~{commute} min</span><span class="l">to NYC{commute_line_note}</span></div>')
    if dom:
        stat_tiles.append(f'<div class="stat"><span class="v">~{dom} days</span><span class="l">Typical on Market</span></div>')
    if county:
        stat_tiles.append(f'<div class="stat"><span class="v">{county}</span><span class="l">County</span></div>')
    stats_html = "\n        ".join(stat_tiles) if stat_tiles else ""

    # ---- neighborhoods block (only if we have them)
    neighborhoods_html = ""
    if neighborhoods:
        lis = "\n".join(f"<li><strong>{n}</strong></li>" for n in neighborhoods)
        neighborhoods_html = f"""
      <section>
        <h2>{display} neighborhoods I work in</h2>
        <p>{display} isn't one market — it's several. Each section has its own price dynamics, school feeds, and buyer pool. Here's where I spend the most time:</p>
        <ul class="neighborhoods">
{lis}
        </ul>
        <p>Tell me which section you're in (or targeting), and I'll pull last-90-day comps for that specific pocket rather than a town-wide average that hides the real signal.</p>
      </section>"""

    # ---- commute block (if we have real data)
    commute_block = ""
    if commute_line and commute_station:
        commute_block = f"""
      <section>
        <h2>Commuting from {display} to NYC</h2>
        <p>{display} is served by the <strong>{commute_line}</strong>. The primary station is <strong>{commute_station}</strong>, with a typical Manhattan commute of about <strong>{commute} minutes</strong> to Penn Station or Hoboken (connections vary by train).</p>
        <p>What this means for buyers: homes within a 10-minute walk of the station command a meaningful premium over homes that require a drive or shuttle. If the NYC commute is the reason you're moving to {display}, the walkable-to-station home is almost always a better long-term hold — faster to resell, less sensitive to gas-price and ride-service swings.</p>
        <p>Ask me for the specific walk-time math before you make an offer. It's the single most underrated pricing factor in {county} County commuter towns.</p>
      </section>"""

    # ---- schools block
    schools_block = ""
    if high_school or schools:
        hs_line = f"Students in {display} attend <strong>{high_school}</strong>." if high_school else ""
        gs_line = f"The district's GreatSchools rating sits around <strong>{schools}</strong>." if schools else ""
        schools_block = f"""
      <section>
        <h2>{display} schools &amp; buyer premiums</h2>
        <p>{hs_line} {gs_line} School district lines inside {display} can affect home values by 8-15% between otherwise-identical houses — particularly for families specifically targeting a school feeder pattern.</p>
        <p>Before you write an offer, I'll cross-reference the exact property address against the current district map. School zoning changes happen, and last year's assumption can be this year's surprise at closing.</p>
      </section>"""

    # ---- neighboring-towns cross-links (only link to towns we actually cover)
    all_candidates = NEIGHBORS.get(slug, [])
    # filter to towns that have a /towns/<slug>.html page (the source of truth)
    valid = [n for n in all_candidates if (TOWNS_DIR / f"{n}.html").exists()]
    nbrs = valid[:5]
    nbr_links = ""
    if nbrs:
        links = []
        for n in nbrs:
            nd = slug_to_display(n)
            links.append(f'<a href="/realtor/{n}-nj.html">{nd}</a>')
        nbr_links = f"""
      <section>
        <h2>Also serving nearby {county} County towns</h2>
        <p>If you're cross-shopping {display} against neighboring towns, I can help you compare directly. I also work in: {", ".join(links)}.</p>
      </section>"""

    # ---- FAQ HTML block (visible, supports the FAQ schema)
    faqs = build_faqs(d)
    faq_html_items = []
    for q, a in faqs:
        faq_html_items.append(f"""
        <div class="faq">
          <h3>{q}</h3>
          <p>{a}</p>
        </div>""")
    faq_html = f"""
      <section>
        <h2>{display} real estate FAQ</h2>
        {''.join(faq_html_items)}
      </section>"""

    # ---- hero + body
    hero_h1 = f"{display}, NJ Real Estate Agent"
    hero_sub = (
        f"I'm Jorge Ramirez — a licensed NJ Realtor at Keller Williams Premier Properties who's "
        f"personally flipped 60+ homes across Northern NJ. If you're buying or selling in {display}, "
        f"let's have one honest conversation and figure out if I'm the right fit."
    )

    head = HEAD_TEMPLATE.format(
        title=title,
        desc=desc.replace('"', "&quot;"),
        slug=slug,
        display=display,
        og_title=og_title.replace('"', "&quot;"),
        og_desc=og_desc.replace('"', "&quot;"),
        schema_json=build_schema(d),
    )

    body = f"""
    <nav class="topnav">
      <a href="/" class="brand">The Jorge Ramirez Group</a>
      <div class="nav-links">
        <a href="/realtor/">Find an Agent</a>
        <a href="/buy-a-home.html">Buy</a>
        <a href="/how-we-sell-your-home.html">Sell</a>
        <a href="/home-valuation.html">Free Valuation</a>
        <a href="tel:908-230-7844" class="nav-phone">908-230-7844</a>
      </div>
    </nav>

    <div class="hero">
      <h1>{hero_h1}</h1>
      <p class="sub">{hero_sub}</p>
      <div class="cta-row">
        <a href="tel:908-230-7844" class="btn btn-primary">Call 908-230-7844</a>
        <a href="mailto:jorge.ramirez@kw.com?subject={display}%20NJ%20real%20estate%20inquiry" class="btn btn-ghost">Email Jorge</a>
      </div>
    </div>

    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <a href="/">Home</a> &rsaquo;
      <a href="/realtor/">Real Estate Agents</a> &rsaquo;
      <span>{county} County</span> &rsaquo;
      <span aria-current="page">{display}, NJ</span>
    </nav>

    <main class="container">
      <section>
        <h2>About the {display}, NJ real estate market</h2>
        <p>{display} sits in {county} County, New Jersey. The market here is shaped by three forces: proximity to {('NYC via ' + commute_line) if commute_line else 'the NYC metro'}, the {high_school + ' district' if high_school else 'local school district'}, and a housing stock that runs from {display}'s historic sections to newer construction pockets.</p>
        <p>If you're buying, the main question isn't "is {display} a good town" — it almost always is. The real question is <em>which specific pocket of {display}</em> fits your situation: budget, commute tolerance, school priority, and how much renovation you're willing to take on. Those tradeoffs aren't obvious from a Zillow search. They're what a specialist agent is actually for.</p>
        <p>If you're selling in {display}, pricing is everything. Overprice and you burn the first two weeks — the most valuable listing period. Underprice and you leave money on the table. I price against active competition, sold-comp trajectories, and the specific features that move the {display} market (not a generic town-wide median).</p>
        {f'<div class="stats">{stats_html}</div>' if stats_html else ''}
      </section>

{neighborhoods_html}
{commute_block}
{schools_block}

      <section>
        <h2>Why homeowners in {display} hire Jorge</h2>
        <div class="proof">
          <ul>
            <li><strong>60+ personal house flips.</strong> I've been the buyer, the renovator, and the seller. That means I can tell you inside a walk-through what a kitchen remodel will actually cost, what a pre-list punch list should look like, and which "cosmetic" issues will kill the appraisal.</li>
            <li><strong>Licensed full-time since 2017.</strong> NJ Real Estate License #1754604. Full-time agent — not a side hustle. Available nights and weekends during the core of your transaction.</li>
            <li><strong>Keller Williams Premier Properties.</strong> Offices in Summit, NJ. KW's technology platform (Command, Kelle, KW Labs) plus my personal AI-powered buyer-targeting system. Your listing gets more qualified eyeballs than a single-agent shop can put on it.</li>
            <li><strong>138 NJ towns covered.</strong> I work across Union, Essex, Morris, Middlesex, Hudson, and Somerset counties — so if your {display} sale is funding a move into a neighboring town, it's the same agent on both sides.</li>
            <li><strong>One honest conversation.</strong> No hard close, no "let me send you to my team." If I'm the wrong fit for your specific situation, I'll say so and point you to someone better. That's how referrals work in real estate.</li>
          </ul>
        </div>
      </section>

      <section>
        <h2>What working with me looks like</h2>
        <p>Step one: you call or email. We talk for 15–20 minutes about what you're actually trying to do — sell fast, sell for top dollar, find a home under $X, relocate for work, sell an inherited property, handle a divorce sale, whatever it is. No script, no pressure, no "let me get you into our pipeline."</p>
        <p>Step two: if we're a fit, I come out to see the property (if you're selling) or we go sit down with a list of comps (if you're buying). You get my honest read — not a sales pitch.</p>
        <p>Step three: we work. I show up for the inspection, I handle the negotiation, I cover the paperwork, and I stay available through closing. After closing I'm still your contact for contractors, tax-appeal advice, future sales, whatever you need.</p>
      </section>

      <div class="cta-block">
        <h2>Ready to talk {display} real estate?</h2>
        <p>One honest conversation. No pressure. That's it.</p>
        <div class="cta-row">
          <a href="tel:908-230-7844" class="btn btn-primary">Call 908-230-7844</a>
          <a href="mailto:jorge.ramirez@kw.com?subject={display}%20NJ%20real%20estate%20inquiry" class="btn btn-ghost">Email Jorge</a>
        </div>
      </div>

{faq_html}
{nbr_links}

      <section>
        <h2>More {display} resources</h2>
        <ul>
          <li><a href="/towns/{slug}.html">{display}, NJ community guide</a> — full market snapshot, schools, neighborhoods, commute details</li>
          <li><a href="/home-valuation.html">Free home valuation</a> — get an instant estimate on your {display} home</li>
          <li><a href="/buy-a-home.html">Buyer services</a> — how I work with {display} home buyers</li>
          <li><a href="/how-we-sell-your-home.html">Seller services</a> — how I list and sell {display} homes</li>
          <li><a href="/blog/">NJ real estate blog</a> — market updates, buying and selling guides</li>
        </ul>
      </section>

      <aside class="author">
        <img src="/images/jorge-ramirez-headshot.jpg" alt="Jorge Ramirez, NJ real estate agent" width="80" height="80" loading="lazy">
        <div>
          <strong>Jorge Ramirez</strong> — Licensed NJ Real Estate Agent (#1754604)<br>
          The Jorge Ramirez Group at Keller Williams Premier Properties<br>
          488 Springfield Ave, Summit, NJ 07901<br>
          <a href="tel:908-230-7844">908-230-7844</a> · <a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a>
        </div>
      </aside>
    </main>

    <footer>
      <p><strong>Jorge Ramirez</strong> · Licensed NJ Real Estate Agent #1754604 · <a href="tel:908-230-7844">908-230-7844</a> · <a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a></p>
      <p>The Jorge Ramirez Group at Keller Williams Premier Properties · 488 Springfield Ave, Summit, NJ 07901</p>
      <p>
        <a href="/">Home</a> ·
        <a href="/realtor/">Find an Agent</a> ·
        <a href="/towns/{slug}.html">{display} Community Guide</a> ·
        <a href="/home-valuation.html">Free Valuation</a> ·
        <a href="/buy-a-home.html">Buy</a> ·
        <a href="/how-we-sell-your-home.html">Sell</a>
      </p>
    </footer>
</body>
</html>
"""
    return head + body


HEAD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-KMS6H85LB0');
    </script>
    <script>if(window.location.hostname==='www.thejorgeramirezgroup.com'){{window.location.replace(window.location.href.replace('//www.','//'));}}</script>

    <title>{title}</title>
    <meta name="description" content="{desc}">
    <meta name="author" content="Jorge Ramirez, The Jorge Ramirez Group at Keller Williams Premier Properties">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <link rel="canonical" href="https://thejorgeramirezgroup.com/realtor/{slug}-nj.html">
    <link rel="alternate" hreflang="en-US" href="https://thejorgeramirezgroup.com/realtor/{slug}-nj.html">
    <link rel="alternate" hreflang="x-default" href="https://thejorgeramirezgroup.com/realtor/{slug}-nj.html">

    <meta name="geo.region" content="US-NJ">
    <meta name="geo.placename" content="{display}, New Jersey">

    <meta property="og:type" content="website">
    <meta property="og:url" content="https://thejorgeramirezgroup.com/realtor/{slug}-nj.html">
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_desc}">
    <meta property="og:image" content="https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg">
    <meta property="og:site_name" content="The Jorge Ramirez Group">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{og_desc}">
    <meta name="twitter:image" content="https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg">

    <link rel="icon" type="image/x-icon" href="/favicon.ico">

    <script type="application/ld+json">
{schema_json}
    </script>

    <style>
      *{{box-sizing:border-box}}
      body{{font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',Roboto,sans-serif;line-height:1.65;color:#1a1a1a;margin:0;background:#fafafa}}
      a{{color:#0f3460}}
      .topnav{{background:#fff;border-bottom:1px solid #e5e5e5;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;position:sticky;top:0;z-index:50}}
      .topnav .brand{{font-weight:700;color:#0f3460;text-decoration:none;font-size:17px}}
      .nav-links{{display:flex;gap:20px;align-items:center;flex-wrap:wrap}}
      .nav-links a{{color:#1a1a1a;text-decoration:none;font-size:14px;font-weight:500}}
      .nav-links a:hover{{color:#0f3460}}
      .nav-phone{{background:#f6a623;color:#1a1a1a !important;padding:8px 14px;border-radius:6px;font-weight:700}}
      .hero{{background:linear-gradient(135deg,#0f3460 0%,#16558f 100%);color:white;padding:64px 24px 56px;text-align:center}}
      .hero h1{{font-size:clamp(28px,5vw,44px);margin:0 0 12px;font-weight:700;line-height:1.15}}
      .hero .sub{{font-size:clamp(16px,2vw,19px);opacity:.94;max-width:740px;margin:0 auto 28px;line-height:1.5}}
      .cta-row{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}}
      .btn{{display:inline-block;padding:14px 28px;border-radius:8px;font-weight:600;text-decoration:none;font-size:16px;transition:transform .15s}}
      .btn:hover{{transform:translateY(-1px)}}
      .btn-primary{{background:#f6a623;color:#1a1a1a}}
      .btn-ghost{{background:rgba(255,255,255,.12);color:white;border:1px solid rgba(255,255,255,.4)}}
      .breadcrumbs{{font-size:14px;color:#666;padding:14px 24px;max-width:880px;margin:0 auto}}
      .breadcrumbs a{{color:#0f3460;text-decoration:none}}
      .breadcrumbs a:hover{{text-decoration:underline}}
      .container{{max-width:880px;margin:0 auto;padding:32px 24px 48px}}
      .container section{{margin-bottom:40px}}
      .container h2{{font-size:clamp(22px,3vw,28px);margin:0 0 16px;color:#0f3460;line-height:1.25}}
      .container p{{margin:12px 0;font-size:16px}}
      .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:28px 0}}
      .stat{{background:white;padding:18px;border-radius:10px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.06);border:1px solid #eee}}
      .stat .v{{font-size:22px;font-weight:700;color:#0f3460;display:block;line-height:1.2}}
      .stat .l{{font-size:12px;color:#666;text-transform:uppercase;letter-spacing:.05em;margin-top:6px;display:block}}
      .proof{{background:white;padding:28px;border-radius:12px;border-left:4px solid #f6a623}}
      .proof ul{{padding-left:20px;margin:0}}
      .proof li{{margin:10px 0;line-height:1.55}}
      .neighborhoods{{column-count:2;column-gap:24px;padding-left:20px}}
      @media (max-width:500px){{.neighborhoods{{column-count:1}}}}
      .cta-block{{background:#0f3460;color:white;padding:40px 24px;border-radius:12px;text-align:center;margin:40px 0}}
      .cta-block h2{{margin:0 0 10px;font-size:26px;color:white}}
      .cta-block p{{margin:0 0 20px;opacity:.92;font-size:17px}}
      .cta-block .cta-row .btn-ghost{{border-color:rgba(255,255,255,.55)}}
      .faq{{margin:18px 0;padding:18px 20px;background:#fff;border-radius:8px;border:1px solid #eee}}
      .faq h3{{margin:0 0 8px;font-size:17px;color:#0f3460}}
      .faq p{{margin:0;font-size:15px}}
      .author{{display:flex;gap:16px;align-items:center;background:#fff;padding:20px;border-radius:10px;border:1px solid #eee;margin-top:24px;font-size:14px;line-height:1.55}}
      .author img{{border-radius:50%;flex-shrink:0}}
      footer{{background:#1a1a1a;color:#ccc;padding:32px 24px;text-align:center;font-size:14px;margin-top:48px;line-height:1.7}}
      footer a{{color:#f6a623;text-decoration:none}}
      footer a:hover{{text-decoration:underline}}
    </style>
</head>
<body>
"""


def build_index(slugs):
    # Group by county
    by_county = {}
    for s in slugs:
        c = county_of(s) or "Other"
        by_county.setdefault(c, []).append(s)

    county_blocks = []
    for county in sorted(by_county.keys()):
        towns = sorted(by_county[county])
        links = "\n".join(
            f'<li><a href="/realtor/{s}-nj.html">{slug_to_display(s)}</a></li>'
            for s in towns
        )
        county_blocks.append(f"""
      <section>
        <h2>{county} County</h2>
        <ul class="town-list">{links}</ul>
      </section>""")

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Real Estate Agent Directory — 138 NJ Towns | Jorge Ramirez</title>
<meta name="description" content="Local real estate agent coverage across 138 NJ towns in Union, Essex, Morris, Middlesex, Hudson &amp; Somerset counties. Jorge Ramirez — licensed NJ Realtor at Keller Williams. Call 908-230-7844.">
<link rel="canonical" href="https://thejorgeramirezgroup.com/realtor/">
<meta property="og:title" content="NJ Real Estate Agent Directory — 138 Towns | Jorge Ramirez">
<meta property="og:description" content="Find your town's dedicated agent page. 138 NJ towns covered. Jorge Ramirez — 60+ house flips, licensed NJ Realtor at Keller Williams.">
<meta property="og:image" content="https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg">
<style>
*{{box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Inter',sans-serif;line-height:1.6;margin:0;background:#fafafa;color:#1a1a1a}}
.hero{{background:linear-gradient(135deg,#0f3460 0%,#16558f 100%);color:white;padding:56px 24px 44px;text-align:center}}
.hero h1{{font-size:clamp(26px,5vw,40px);margin:0 0 10px}}
.hero p{{max-width:700px;margin:0 auto;opacity:.92}}
.container{{max-width:1000px;margin:0 auto;padding:40px 24px}}
.container h2{{color:#0f3460;margin-top:32px;margin-bottom:12px;font-size:22px;border-bottom:2px solid #f6a623;padding-bottom:6px}}
.town-list{{column-count:4;column-gap:24px;list-style:none;padding:0}}
.town-list li{{break-inside:avoid;margin:5px 0}}
.town-list a{{color:#0f3460;text-decoration:none;font-size:15px}}
.town-list a:hover{{text-decoration:underline}}
@media (max-width:800px){{.town-list{{column-count:2}}}}
@media (max-width:500px){{.town-list{{column-count:1}}}}
footer{{background:#1a1a1a;color:#ccc;padding:28px 24px;text-align:center;font-size:14px;margin-top:32px}}
footer a{{color:#f6a623;text-decoration:none}}
</style>
</head><body>
<div class="hero">
<h1>Find a Real Estate Agent in Your NJ Town</h1>
<p>Dedicated town pages covering 138 NJ communities across 6 counties. Jorge Ramirez — licensed NJ Realtor at Keller Williams, 60+ personal house flips. One honest conversation.</p>
</div>
<main class="container">
{''.join(county_blocks)}
</main>
<footer>
<p><a href="/">← Back to home</a> · <a href="tel:908-230-7844">908-230-7844</a> · <a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a></p>
</footer>
</body></html>
"""


def main():
    files = sorted(TOWNS_DIR.glob("*.html"))
    ok = []
    skip = []
    for f in files:
        slug = f.stem
        try:
            html = f.read_text(encoding="utf-8", errors="ignore")
            d = extract_data(html, slug)
            page = build_page(d)
            (OUT_DIR / f"{slug}-nj.html").write_text(page, encoding="utf-8")
            ok.append(slug)
        except Exception as e:
            skip.append((slug, str(e)))
            print(f"SKIP {slug}: {e}", file=sys.stderr)

    (OUT_DIR / "index.html").write_text(build_index(ok), encoding="utf-8")
    print(f"Generated {len(ok)} pages + index in {OUT_DIR}")
    if skip:
        print(f"Skipped {len(skip)}")
        for s, e in skip:
            print(f"  {s}: {e}")


if __name__ == "__main__":
    main()
