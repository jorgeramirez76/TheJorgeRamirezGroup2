#!/usr/bin/env python3
"""
gen_realtor_pages.py — Generate /realtor/<town>-nj.html service pages for all 138 towns.

These are deliberately short, transactional, lead-gen-focused pages targeting
"[town] nj real estate agent" / "best realtor [town] nj" / "[town] realtor"
commercial queries where the existing /towns/<town>.html info pages are
showing impressions but earning zero clicks.

Different from /towns/<town>.html:
  - /towns/<town>.html    = informational (long, 900+ lines, schools, commute, market)
  - /realtor/<town>-nj.html = transactional (short, hero + proof + CTA)

Data per-town is extracted from the existing town info page JSON-LD so we
don't duplicate content literally — we repackage verified facts with a
different voice and structure.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).parent
TOWNS_DIR = REPO / "towns"
OUT_DIR = REPO / "realtor"
OUT_DIR.mkdir(exist_ok=True)

SLUG_TO_DISPLAY_OVERRIDE = {
    # slug -> display name (for slugs that need special casing)
    "new-brunswick": "New Brunswick",
    "north-arlington": "North Arlington",
    "north-brunswick": "North Brunswick",
    "north-plainfield": "North Plainfield",
    "old-bridge": "Old Bridge",
    "west-caldwell": "West Caldwell",
    "east-brunswick": "East Brunswick",
    "east-hanover": "East Hanover",
    "east-newark": "East Newark",
    "south-amboy": "South Amboy",
    "south-bound-brook": "South Bound Brook",
    "south-brunswick": "South Brunswick",
    "south-orange": "South Orange",
    "south-plainfield": "South Plainfield",
    "south-river": "South River",
    "west-new-york": "West New York",
    "west-orange": "West Orange",
    "long-hill": "Long Hill",
    "short-hills": "Short Hills",
    "upper-saddle-river": "Upper Saddle River",
    "jamesburg": "Jamesburg",
    "highland-park": "Highland Park",
    "green-brook": "Green Brook",
    "glen-ridge": "Glen Ridge",
    "far-hills": "Far Hills",
    "franklin-township": "Franklin Township",
    "chatham-township": "Chatham Township",
    "chatham-borough": "Chatham Borough",
    "chester-borough": "Chester Borough",
    "chester-township": "Chester Township",
    "bernards-township": "Bernards Township",
    "boonton-township": "Boonton Township",
    "warren-township": "Warren Township",
    "washington-township-morris": "Washington Township",
    "rockaway-borough": "Rockaway Borough",
    "rockaway-township": "Rockaway Township",
    "rocky-hill": "Rocky Hill",
    "roselle-park": "Roselle Park",
    "scotch-plains": "Scotch Plains",
    "bound-brook": "Bound Brook",
    "jersey-city": "Jersey City",
    "union-city": "Union City",
    "basking-ridge": "Basking Ridge",
    "berkeley-heights": "Berkeley Heights",
    "lincoln-park": "Lincoln Park",
    "victory-gardens": "Victory Gardens",
    "florham-park": "Florham Park",
    "spotswood": "Spotswood",
    "helmetta": "Helmetta",
    "kenilworth": "Kenilworth",
    "kinnelon": "Kinnelon",
}


def slug_to_display(slug: str) -> str:
    if slug in SLUG_TO_DISPLAY_OVERRIDE:
        return SLUG_TO_DISPLAY_OVERRIDE[slug]
    return slug.replace("-", " ").title()


def extract_data(town_html: str, slug: str):
    """Pull median price, commute, schools, county from the existing info page."""
    data = {
        "slug": slug,
        "display": slug_to_display(slug),
        "median": None,
        "median_raw": None,
        "commute_min": None,
        "commute_line": None,
        "schools": None,
        "county": None,
        "county_slug": None,
        "days_on_market": None,
    }

    # median home price
    m = re.search(r'median home price in [^"]*?approximately[^"]*?\$([\d,]+)', town_html, re.I)
    if m:
        data["median_raw"] = int(m.group(1).replace(",", ""))
        v = data["median_raw"]
        data["median"] = f"${v/1_000_000:.2f}M" if v >= 1_000_000 else f"${v/1000:.0f}K"

    # school rating
    m = re.search(r'(?:schools are rated|schools[^<]*?rated)[^<]*?(\d+)/10', town_html, re.I)
    if m:
        data["schools"] = f"{m.group(1)}/10"

    # commute
    m = re.search(r'commute from [^"]+? to (?:Manhattan|NYC|New York)[^"]*?approximately (\d+) minutes[^"]*?(via ([A-Za-z &]+(?:Direct|Corridor|PATH|Transit|Line)))?', town_html, re.I)
    if m:
        data["commute_min"] = m.group(1)
        if m.group(3):
            data["commute_line"] = m.group(3).strip()

    # county
    m = re.search(r'"name":\s*"([A-Za-z ]+County), New Jersey"', town_html)
    if m:
        data["county"] = m.group(1)
        data["county_slug"] = m.group(1).lower().replace(" ", "-")

    # days on market
    m = re.search(r'typically spend (\d+) days on market', town_html, re.I)
    if m:
        data["days_on_market"] = m.group(1)

    return data


HEAD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-KMS6H85LB0');
    </script>
    <script>if(window.location.hostname==='www.thejorgeramirezgroup.com'){{window.location.replace(window.location.href.replace('//www.','//'));}}</script>

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>{title}</title>
    <meta name="description" content="{desc}">
    <meta name="author" content="Jorge Ramirez, The Jorge Ramirez Group at Keller Williams Premier Properties">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <link rel="canonical" href="https://thejorgeramirezgroup.com/realtor/{slug}-nj.html">

    <meta name="geo.region" content="US-NJ">
    <meta name="geo.placename" content="{display}, New Jersey">

    <meta property="og:type" content="website">
    <meta property="og:url" content="https://thejorgeramirezgroup.com/realtor/{slug}-nj.html">
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_desc}">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{og_desc}">

    <link rel="icon" type="image/x-icon" href="/favicon.ico">

    <!-- Service + Person + LocalBusiness schema -->
    <script type="application/ld+json">
{schema_json}
    </script>

    <link rel="stylesheet" href="/css/main.css">
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1a1a1a; margin: 0; background: #fafafa; }}
      .hero {{ background: linear-gradient(135deg, #0f3460 0%, #16558f 100%); color: white; padding: 64px 24px 48px; text-align: center; }}
      .hero h1 {{ font-size: clamp(28px, 5vw, 44px); margin: 0 0 12px; font-weight: 700; line-height: 1.2; }}
      .hero .sub {{ font-size: clamp(16px, 2vw, 20px); opacity: 0.92; max-width: 680px; margin: 0 auto 28px; }}
      .cta-row {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }}
      .btn {{ display: inline-block; padding: 14px 28px; border-radius: 8px; font-weight: 600; text-decoration: none; font-size: 16px; transition: transform 0.15s; }}
      .btn:hover {{ transform: translateY(-1px); }}
      .btn-primary {{ background: #f6a623; color: #1a1a1a; }}
      .btn-ghost {{ background: rgba(255,255,255,0.12); color: white; border: 1px solid rgba(255,255,255,0.35); }}
      .container {{ max-width: 840px; margin: 0 auto; padding: 48px 24px; }}
      .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin: 32px 0; }}
      .stat {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
      .stat .v {{ font-size: 24px; font-weight: 700; color: #0f3460; display: block; }}
      .stat .l {{ font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }}
      .proof {{ background: white; padding: 32px; border-radius: 12px; margin: 32px 0; border-left: 4px solid #f6a623; }}
      .proof h2 {{ margin-top: 0; font-size: 22px; }}
      .proof ul {{ padding-left: 20px; }}
      .proof li {{ margin: 8px 0; }}
      .cta-block {{ background: #0f3460; color: white; padding: 40px 24px; border-radius: 12px; text-align: center; margin: 32px 0; }}
      .cta-block h2 {{ margin: 0 0 12px; font-size: 24px; }}
      .cta-block p {{ margin: 0 0 20px; opacity: 0.92; }}
      .breadcrumbs {{ font-size: 14px; color: #666; padding: 12px 24px; max-width: 840px; margin: 0 auto; }}
      .breadcrumbs a {{ color: #0f3460; text-decoration: none; }}
      .breadcrumbs a:hover {{ text-decoration: underline; }}
      footer {{ background: #1a1a1a; color: #ccc; padding: 32px 24px; text-align: center; font-size: 14px; margin-top: 48px; }}
      footer a {{ color: #f6a623; text-decoration: none; }}
    </style>
</head>
<body>
"""


def build_schema(d):
    display = d["display"]
    url = f"https://thejorgeramirezgroup.com/realtor/{d['slug']}-nj.html"
    info_url = f"https://thejorgeramirezgroup.com/towns/{d['slug']}.html"
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Service",
                "@id": url + "#service",
                "name": f"Real Estate Agent Services in {display}, NJ",
                "serviceType": "Real Estate Agent",
                "areaServed": {
                    "@type": "City",
                    "name": display,
                    "containedInPlace": {"@type": "State", "name": "New Jersey"}
                },
                "provider": {"@id": "https://thejorgeramirezgroup.com/#person"},
                "url": url,
                "audience": {"@type": "Audience", "audienceType": f"Home buyers and sellers in {display}, NJ"}
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
                    "name": "The Jorge Ramirez Group at Keller Williams Premier Properties",
                    "address": {
                        "@type": "PostalAddress",
                        "streetAddress": "488 Springfield Ave",
                        "addressLocality": "Summit",
                        "addressRegion": "NJ",
                        "postalCode": "07901",
                        "addressCountry": "US"
                    }
                },
                "hasCredential": {
                    "@type": "EducationalOccupationalCredential",
                    "credentialCategory": "NJ Real Estate License",
                    "identifier": "1754604"
                },
                "sameAs": [
                    "https://www.instagram.com/thejorgeramirezgroup/",
                    "https://www.facebook.com/thejorgeramirezgroup/",
                    "https://www.linkedin.com/in/jorge-ramirez-realtor-nj/",
                    "https://www.kw.com/agent/jorge-ramirez-nj"
                ]
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thejorgeramirezgroup.com/"},
                    {"@type": "ListItem", "position": 2, "name": "Real Estate Agent Services", "item": "https://thejorgeramirezgroup.com/realtor/"},
                    {"@type": "ListItem", "position": 3, "name": f"{display}, NJ", "item": url}
                ]
            },
            {
                "@type": "WebPage",
                "@id": url,
                "url": url,
                "name": f"{display} NJ Real Estate Agent — Jorge Ramirez",
                "isPartOf": {"@id": "https://thejorgeramirezgroup.com/#website"},
                "about": {"@type": "City", "name": f"{display}, New Jersey"},
                "mainEntity": {"@id": url + "#service"},
                "relatedLink": info_url
            }
        ]
    }
    return json.dumps(schema, indent=2)


def build_page(d):
    display = d["display"]
    slug = d["slug"]
    county = d.get("county") or "Northern NJ"
    median = d.get("median") or "competitive"
    schools = d.get("schools")
    commute = d.get("commute_min")
    commute_line = d.get("commute_line")
    dom = d.get("days_on_market")

    # --- title + meta: lead with transactional intent
    title = f"{display} NJ Real Estate Agent | Jorge Ramirez, Licensed Realtor"
    # Build a description that fits cleanly in ~155 chars. Priority: hook, credential, stat, CTA.
    # We won't hard-truncate mid-word; build short first, add detail only if budget allows.
    hook = f"{display} NJ real estate agent Jorge Ramirez."
    cred = "Licensed NJ Realtor at Keller Williams, 60+ house flips."
    stat = f" Median {median}." if (median and median != "competitive") else ""
    cta = " Call 908-230-7844."
    desc = (hook + " " + cred + stat + cta).strip()
    # safety: if somehow over 158, drop the stat
    if len(desc) > 158:
        desc = (hook + " " + cred + cta).strip()

    og_title = f"Hire a Real Estate Agent in {display}, NJ — Jorge Ramirez"
    og_desc = f"Licensed NJ Realtor since 2017. 60+ personal house flips. Buy or sell in {display} with an agent who knows the numbers. Free consultation."

    # --- stat tiles
    stat_tiles = []
    if median and median != "competitive":
        stat_tiles.append(f'<div class="stat"><span class="v">{median}</span><span class="l">Median Price</span></div>')
    if schools:
        stat_tiles.append(f'<div class="stat"><span class="v">{schools}</span><span class="l">Schools</span></div>')
    if commute:
        line_note = f" via {commute_line}" if commute_line else ""
        stat_tiles.append(f'<div class="stat"><span class="v">{commute} min</span><span class="l">to NYC{line_note}</span></div>')
    if dom:
        stat_tiles.append(f'<div class="stat"><span class="v">{dom} days</span><span class="l">on Market</span></div>')
    stats_html = "\n        ".join(stat_tiles) if stat_tiles else ""

    # --- body — written to be substantively unique vs the info page
    hero_h1 = f"Real Estate Agent in {display}, NJ"
    hero_sub = f"I'm Jorge Ramirez — licensed NJ Realtor at Keller Williams Premier Properties. Whether you're buying or selling in {display}, you deserve an agent who's walked the numbers."

    body = f"""
    <div class="hero">
      <h1>{hero_h1}</h1>
      <p class="sub">{hero_sub}</p>
      <div class="cta-row">
        <a href="tel:908-230-7844" class="btn btn-primary">Call 908-230-7844</a>
        <a href="/contact.html?town={slug}" class="btn btn-ghost">Send a Message</a>
      </div>
    </div>

    <div class="breadcrumbs">
      <a href="/">Home</a> &rsaquo; <a href="/realtor/">Real Estate Agents</a> &rsaquo; {display}, NJ
    </div>

    <div class="container">
      <section>
        <h2>Why hire Jorge for {display}?</h2>
        <p>Most agents who list in {display} have closed a handful of homes here at most. I've personally bought, renovated, and sold <strong>60+ investment properties</strong> across {county} and neighboring towns. That means I can tell you — inside of a conversation — what a kitchen remodel actually costs, what a pre-list punch list should look like, and which features move the market in {display} vs. neighboring towns.</p>
        <p>If you're <strong>selling in {display}</strong>: I'll price you against the numbers that actually matter — days on market, active-vs-sold comps, and the negotiation leverage your specific block has right now. No "let's try high and see."</p>
        <p>If you're <strong>buying in {display}</strong>: I'll show you what the house will cost you over the next three years — not just the sticker price. Renovation estimates, realistic offer strategy, and an honest "is this a good deal" answer.</p>
        {f'<div class="stats">{stats_html}</div>' if stats_html else ''}
      </section>

      <section class="proof">
        <h2>Credentials</h2>
        <ul>
          <li>Licensed NJ Real Estate Agent since 2017 (License #1754604)</li>
          <li>60+ personal house flips across Northern NJ</li>
          <li>The Jorge Ramirez Group at <strong>Keller Williams Premier Properties</strong> — Summit, NJ office</li>
          <li>Serving 138 NJ towns across Union, Essex, Morris, Middlesex, Hudson & Somerset counties</li>
          <li>Full-time agent — not a side hustle. Available nights and weekends.</li>
        </ul>
      </section>

      <section>
        <h2>What does working with me look like?</h2>
        <p>Pick up the phone or send a message. I'll answer. We'll talk for 15 minutes about what you're actually trying to do — sell fast, sell for top dollar, find a home under $X, relocate for work, whatever it is. No script, no pressure, no "let me send you over to my team."</p>
        <p>If I'm the right fit, we keep going. If I'm not — maybe the town is outside my range, maybe the timeline doesn't work — I'll tell you, and I'll point you to someone who is.</p>
      </section>

      <div class="cta-block">
        <h2>Ready to talk {display} real estate?</h2>
        <p>One honest conversation. No pressure. That's it.</p>
        <a href="tel:908-230-7844" class="btn btn-primary">Call 908-230-7844</a>
      </div>

      <section>
        <h2>More about {display}</h2>
        <p>For the full market snapshot — schools, neighborhoods, commute details, recent sales — see my <a href="/towns/{slug}.html">{display}, NJ community guide</a>. For a specific property valuation, use the <a href="/home-valuation.html">free home value tool</a>.</p>
      </section>
    </div>

    <footer>
      <p><strong>Jorge Ramirez</strong> &middot; Licensed NJ Real Estate Agent &middot; <a href="tel:908-230-7844">908-230-7844</a> &middot; <a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a></p>
      <p>The Jorge Ramirez Group at Keller Williams Premier Properties &middot; 488 Springfield Ave, Summit, NJ 07901</p>
      <p><a href="/">Home</a> &middot; <a href="/towns/{slug}.html">{display} Community Guide</a> &middot; <a href="/home-valuation.html">Free Home Valuation</a></p>
    </footer>
</body>
</html>
"""

    head = HEAD_TEMPLATE.format(
        title=title,
        desc=desc.replace('"', "&quot;"),
        slug=slug,
        display=display,
        og_title=og_title.replace('"', "&quot;"),
        og_desc=og_desc.replace('"', "&quot;"),
        schema_json=build_schema(d),
    )
    return head + body


def main():
    town_files = sorted(TOWNS_DIR.glob("*.html"))
    generated = []
    skipped = []
    for f in town_files:
        slug = f.stem
        try:
            html = f.read_text(encoding="utf-8", errors="ignore")
            data = extract_data(html, slug)
            page = build_page(data)
            out = OUT_DIR / f"{slug}-nj.html"
            out.write_text(page, encoding="utf-8")
            generated.append(slug)
        except Exception as e:
            skipped.append((slug, str(e)))
            print(f"  SKIP {slug}: {e}", file=sys.stderr)

    # index page for /realtor/
    idx_html = build_index(generated)
    (OUT_DIR / "index.html").write_text(idx_html, encoding="utf-8")

    print(f"Generated {len(generated)} pages in {OUT_DIR}")
    if skipped:
        print(f"Skipped {len(skipped)}:")
        for s, e in skipped:
            print(f"  {s}: {e}")


def build_index(slugs):
    links = "\n".join(
        f'<li><a href="/realtor/{s}-nj.html">{slug_to_display(s)}, NJ Real Estate Agent</a></li>'
        for s in sorted(slugs)
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Real Estate Agent Directory | 138 NJ Towns | Jorge Ramirez</title>
<meta name="description" content="Dedicated real estate agent pages for 138 NJ towns. Jorge Ramirez — licensed NJ Realtor at Keller Williams. Find your town, see the market, hire local.">
<link rel="canonical" href="https://thejorgeramirezgroup.com/realtor/">
<link rel="stylesheet" href="/css/main.css">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; line-height: 1.6; margin: 0; background: #fafafa; }}
  .hero {{ background: linear-gradient(135deg, #0f3460 0%, #16558f 100%); color: white; padding: 64px 24px 48px; text-align: center; }}
  .hero h1 {{ font-size: clamp(28px, 5vw, 40px); margin: 0 0 12px; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 40px 24px; }}
  ul.towns {{ column-count: 3; column-gap: 24px; list-style: none; padding: 0; }}
  ul.towns li {{ break-inside: avoid; margin: 6px 0; }}
  ul.towns a {{ color: #0f3460; text-decoration: none; font-size: 15px; }}
  ul.towns a:hover {{ text-decoration: underline; }}
  @media (max-width: 720px) {{ ul.towns {{ column-count: 2; }} }}
  @media (max-width: 480px) {{ ul.towns {{ column-count: 1; }} }}
</style>
</head><body>
<div class="hero"><h1>Real Estate Agents Across 138 NJ Towns</h1><p>Find Jorge's dedicated local agent page for your town — median prices, credentials, free consultation.</p></div>
<div class="container">
<ul class="towns">
{links}
</ul>
</div>
</body></html>
"""


if __name__ == "__main__":
    main()
