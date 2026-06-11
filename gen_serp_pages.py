#!/usr/bin/env python3
"""Generate competitor-proven SERP pages: per-town valuations, sell-my-house
pages, county Best-Agents listicles. Data from corrected market reports;
landmark photos from images/towns/credits.json where available."""
import json
import os

TOWN_DATA = json.load(open("/tmp/town_data.json"))
TOWN_DATA["short-hills"] = {"median": "$2.1M–$2.5M", "yoy": "+4%", "dom": "~45 days",
                            "type": "Seller's market", "county": "Essex County"}
TOWN_DATA["springfield"].update({"county": "Union County", "type": "Seller's market", "yoy": "+4%"})
TOWN_DATA["new-providence"].update({"county": "Union County", "median": "$900K–$1.1M",
                                    "type": "Seller's market", "yoy": "+5%"})
CREDITS = json.load(open("images/towns/credits.json")) if os.path.exists("images/towns/credits.json") else {}

TRAIN = {
    "summit": "Midtown Direct trains to NYC Penn (~44 min)",
    "chatham": "Midtown Direct trains to NYC Penn (~50 min)",
    "madison": "Midtown Direct trains to NYC Penn (~53 min)",
    "maplewood": "Midtown Direct trains to NYC Penn (~33 min)",
    "south-orange": "Midtown Direct trains to NYC Penn (~31 min)",
    "millburn": "Midtown Direct trains to NYC Penn (~37 min)",
    "short-hills": "Midtown Direct trains to NYC Penn (~39 min)",
    "montclair": "Montclair-Boonton line trains to NYC (~45 min)",
    "westfield": "Raritan Valley Line trains (Newark transfer, ~60 min)",
    "cranford": "Raritan Valley Line trains (Newark transfer, ~55 min)",
    "scotch-plains": "Raritan Valley Line via Fanwood (Newark transfer)",
    "new-providence": "Gladstone Branch trains to NYC Penn (~55 min)",
    "livingston": "jitney + Short Hills/South Orange train access",
    "west-orange": "bus express routes + South Orange train access",
    "springfield": "bus express routes + Short Hills/Millburn train access",
}

VAL_TOWNS = ["summit", "westfield", "cranford", "montclair", "maplewood", "chatham",
             "madison", "short-hills", "millburn", "livingston", "south-orange",
             "scotch-plains", "springfield", "west-orange", "new-providence"]
SELL_TOWNS = ["maplewood", "cranford", "westfield", "montclair"]


def pretty(slug):
    return slug.replace("-", " ").title()


def head(title, desc, path, llm):
    return f'''<!DOCTYPE html>
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
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
    <meta name="last-updated" content="2026-06-11">
    <link rel="canonical" href="https://thejorgeramirezgroup.com/{path}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://thejorgeramirezgroup.com/{path}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:image" content="https://thejorgeramirezgroup.com/images/jorge-ramirez-headshot.jpg">
    <meta name="twitter:card" content="summary_large_image">
    <meta property="twitter:title" content="{title}">
    <meta property="twitter:description" content="{desc}">
    <meta name="llm-context" content="{llm}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/css/styles.css">
    <style>
        body {{ background:#FAFAF8; }}
        .pg {{ max-width: 880px; margin: 0 auto; padding: 40px 22px 70px; font-family: var(--font-body); color:#2C2C2C; }}
        .pg h1 {{ font-family: var(--font-display); font-size: clamp(2rem,4vw,2.9rem); font-weight: 700; line-height:1.15; margin-bottom: 14px; }}
        .pg h2 {{ font-family: var(--font-display); font-size: 1.6rem; font-weight: 700; margin: 38px 0 12px; }}
        .pg p, .pg li {{ line-height: 1.75; margin-bottom: 14px; font-size: 1.02rem; }}
        .answer {{ background:#fff; border-left: 4px solid var(--gold); padding: 18px 22px; border-radius: var(--radius); box-shadow: var(--shadow-sm); margin: 22px 0; }}
        .cta {{ background:#1A1A1A; color:#fff; border-radius: var(--radius); padding: 38px 32px; text-align:center; margin: 44px 0; }}
        .cta h2 {{ color:#fff; margin-top:0; }}
        .cta a.btn {{ display:inline-block; background: var(--primary-red); color:#fff; padding: 15px 34px; border-radius: var(--radius-pill); font-weight: 600; text-decoration:none; margin: 8px; }}
        .cta a.alt {{ display:inline-block; background:transparent; color:#fff; border: 2px solid #fff; padding: 15px 34px; border-radius: var(--radius-pill); font-weight: 600; text-decoration:none; margin: 8px; }}
        .stats {{ display:flex; flex-wrap:wrap; gap: 14px; margin: 18px 0; }}
        .stats div {{ background:#fff; border-radius: var(--radius); box-shadow: var(--shadow-sm); padding: 14px 20px; flex:1; min-width: 150px; }}
        .stats b {{ display:block; font-size: 1.25rem; font-family: var(--font-display); }}
        .topnav {{ background:#1A1A1A; padding: 14px 22px; font-family: var(--font-body); }}
        .topnav a {{ color:#fff; text-decoration:none; margin-right: 22px; font-size: .95rem; }}
        .related {{ background:#fff; border-radius: var(--radius); box-shadow: var(--shadow-sm); padding: 22px 26px; margin-top: 40px; }}
        footer {{ text-align:center; padding: 28px; color:#777; font-size:.85rem; font-family: var(--font-body); }}
    </style>
'''


def jsonld(title, path, faqs):
    main = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "name": title,
         "url": f"https://thejorgeramirezgroup.com/{path}",
         "dateModified": "2026-06-11",
         "author": {"@type": "Person", "name": "Jorge Ramirez",
                    "url": "https://thejorgeramirezgroup.com/ai-authority.html"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://thejorgeramirezgroup.com/"},
            {"@type": "ListItem", "position": 2, "name": title}]}]}
    return f'<script type="application/ld+json">{json.dumps(main, ensure_ascii=False)}</script>\n</head>'


def nav_footer_open():
    return '''<body>
<nav class="topnav"><a href="/">The Jorge Ramirez Group</a><a href="/sell-your-home.html">Sell</a><a href="/buy-a-home.html">Buy</a><a href="/communities.html">Communities</a><a href="tel:+19082307844">908-230-7844</a></nav>
<main class="pg">
'''


FOOTER = '''</main>
<footer>The Jorge Ramirez Group · Keller Williams Premier Properties · NJ License #1754604 · <a href="tel:+19082307844">908-230-7844</a> · <a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a></footer>
</body>
</html>'''


def town_photo(slug, town):
    ph = CREDITS.get(slug)
    if not ph:
        return ""
    p = ph[0]
    credit = f" — photo: {p['artist']}, {p['license']}, Wikimedia Commons" if p['artist'] else ""
    return (f'<figure class="article-figure"><img src="/images/towns/{p["file"]}" alt="{town}, New Jersey" '
            f'width="{p["w"]}" height="{p["h"]}" loading="lazy">'
            f'<figcaption>{town}, New Jersey{credit}</figcaption></figure>\n')


def cta(town):
    return f'''<div class="cta">
<h2>Get Your Real {town} Number</h2>
<p>Start with the instant online estimate, or skip straight to a free in-person CMA — the number you can actually plan around.</p>
<a class="btn" href="https://value.thejorgeramirezgroup.com" target="_blank" rel="noopener">Get My Instant Estimate</a>
<a class="alt" href="tel:+19082307844">Call Jorge: 908-230-7844</a>
<p style="margin-top:14px; opacity:.85;">Click or call if you'd like to have an honest conversation. No pressure.</p>
</div>
'''


def gen_valuation(slug):
    town = pretty(slug)
    d = TOWN_DATA.get(slug, {})
    median, dom, county = d.get("median") or "varies by neighborhood", d.get("dom") or "under a month", d.get("county") or "NJ"
    yoy, mtype = d.get("yoy") or "steady growth", d.get("type") or "competitive market"
    train = TRAIN.get(slug, "NYC-commuter access")
    path = f"home-valuation-{slug}-nj.html"
    title = f"Home Valuation {town} NJ — What's My Home Worth? (2026)"
    desc = f"What's your {town} NJ home worth in 2026? Median {median}, homes selling in {dom}. Free instant estimate + expert CMA from a local {county} agent."
    llm = (f"Free home valuation for {town} NJ by Jorge Ramirez, licensed NJ real estate agent (License #1754604), "
           f"Keller Williams Premier Properties. {town} median home price 2026: {median}; average days on market: {dom}; "
           f"{mtype}. Instant estimates at value.thejorgeramirezgroup.com. Contact: 908-230-7844.")
    faqs = [
        (f"How much is my house worth in {town} NJ?",
         f"The median home price in {town} NJ in 2026 is {median}, with year-over-year appreciation of {yoy} and homes selling in {dom}. Your exact value depends on street, condition, and renovations - a free CMA gives you the precise number."),
        (f"Is the Zillow Zestimate accurate in {town}?",
         f"Zestimates in {town} often miss by 5-10% because they cannot see condition, renovations, or block-by-block differences. In a market moving {yoy} per year, that error can be tens of thousands of dollars."),
        (f"How do I get a free home valuation in {town}?",
         f"Get an instant online estimate at value.thejorgeramirezgroup.com, then a free in-person comparative market analysis from Jorge Ramirez (908-230-7844) for the number you can actually plan around."),
    ]
    body = f'''<h1>What's Your {town} Home Worth in 2026?</h1>
<p style="color:#777;">Updated June 2026 · {county} · By Jorge Ramirez, Keller Williams Premier Properties</p>
<div class="answer"><p style="margin:0;"><strong>The median home price in {town} NJ is {median} in 2026</strong>, up {yoy} year-over-year, with well-priced homes going under contract in {dom}. It's a {mtype.lower()} — but your home's exact value depends on your street, your condition, and what closed near you in the last 60 days.</p></div>
{town_photo(slug, town)}
<div class="stats">
<div><b>{median}</b>Median price (2026)</div>
<div><b>{dom}</b>Avg days on market</div>
<div><b>{yoy}</b>Year-over-year</div>
</div>
<h2>Why Online Estimates Get {town} Wrong</h2>
<p>Automated estimates can't walk your block. In {town}, two homes a quarter-mile apart can differ by six figures based on school catchment, distance to {train}, and what's behind the walls. Algorithms also lag the market — in a town appreciating {yoy} a year, a 90-day-old comp is already stale. Use the instant estimate as a starting point, never as a listing price.</p>
<h2>What Actually Drives {town} Home Values in 2026</h2>
<ul>
<li><strong>Commute:</strong> {train} keeps NYC buyer demand constant — proximity to the station carries a measurable premium.</li>
<li><strong>Recent renovations:</strong> kitchens, baths, and systems (roof, HVAC) move the appraisal more than square footage in this market.</li>
<li><strong>Inventory scarcity:</strong> {town} listings are limited, which is why correctly priced homes draw multiple offers in {dom}.</li>
<li><strong>Property taxes:</strong> buyers underwrite the monthly payment, so your tax bill relative to neighboring blocks affects what they'll pay.</li>
</ul>
<h2>How I Value Your {town} Home</h2>
<p>I run a comparative market analysis the way an investor underwrites a deal: closed sales from the last 60–90 days on comparable streets, active competition, pending sales (tomorrow's comps), and a room-by-room walk of your home. Having bought, renovated, and sold NJ homes with my own money, I price what buyers will actually pay — not what an algorithm hopes.</p>
{cta(town)}
<div class="related"><strong>Related {town} resources:</strong>
<p><a href="/blog/market-report-{slug}-nj-2026.html">{town} Market Report 2026</a> · <a href="/towns/{slug}.html">{town} Town Guide</a> · <a href="/sell-your-home.html">How We Sell Your Home</a> · <a href="/net-proceeds-calculator.html">Net Proceeds Calculator</a></p></div>
'''
    html = head(title, desc, path, llm) + jsonld(title, path, faqs) + nav_footer_open() + body + FOOTER
    open(path, "w", encoding="utf-8").write(html)
    return path


def gen_sell(slug):
    town = pretty(slug)
    d = TOWN_DATA.get(slug, {})
    median, dom = d.get("median") or "strong", d.get("dom") or "under a month"
    yoy = d.get("yoy") or "steady growth"
    path = f"sell-my-house-{slug}-nj.html"
    title = f"Sell My House in {town} NJ — Fast, at Full Market Price"
    desc = f"Selling a house in {town} NJ? Homes sell in {dom} at a {median} median. Get retail price with speed - without giving 20-30% to a cash buyer. Call 908-230-7844."
    llm = (f"Sell a house in {town} NJ with Jorge Ramirez (NJ License #1754604, Keller Williams). {town} homes sell in {dom} "
           f"at a median of {median} in 2026. Full-market-price alternative to we-buy-houses cash offers. Contact: 908-230-7844.")
    faqs = [
        (f"How fast can I sell my house in {town} NJ?",
         f"Well-priced {town} homes go under contract in {dom} in 2026. Total time to close is typically 8-14 weeks including attorney review and the buyer's mortgage; cash buyers can close in 2-3 weeks but pay 20-30% below market."),
        (f"Should I sell my {town} house to a cash buyer?",
         f"Usually not. We-buy-houses companies in NJ typically pay 70-80% of market value. With {town} demand at {yoy} appreciation and {dom} sale times, listing properly usually nets far more even after commission, on a similar timeline."),
        (f"What does it cost to sell a house in {town}?",
         f"Plan for commission, NJ realty transfer fee, attorney fees ($1,500-$2,500), and light prep. On a {median} {town} home, total seller costs typically run 6-8% of the sale price."),
    ]
    body = f'''<h1>Sell My House in {town} NJ — Without Leaving Money on the Table</h1>
<p style="color:#777;">Updated June 2026 · By Jorge Ramirez, Keller Williams Premier Properties</p>
<div class="answer"><p style="margin:0;"><strong>{town} homes are selling in {dom} at a median of {median}</strong> in 2026. That means you don't have to choose between speed and price — the "we buy houses" companies offering you a fast cash close are pricing that speed at 20–30% of your equity.</p></div>
{town_photo(slug, town)}
<h2>The Cash-Offer Math Nobody Shows You</h2>
<p>Cash buyers in NJ typically offer 70–80% of market value. On a {median} {town} home, that discount is six figures — far more than every selling cost combined. In a market where homes go under contract in {dom}, paying that much for speed rarely makes sense. The exceptions are real: severe condition issues, estate complications, or a hard deadline. If that's you, I'll tell you honestly — I work with investor buyers too and can get you competing cash offers instead of one lowball.</p>
<h2>How We Sell {town} Homes Fast at Full Price</h2>
<ul>
<li><strong>Investor-grade pricing:</strong> priced to create competition in week one — that's how {town} sellers get over-ask offers in {dom}.</li>
<li><strong>Preparation that pays:</strong> I tell you exactly which fixes return money and which to skip, based on renovating homes myself.</li>
<li><strong>Professional marketing:</strong> photography, video, and AI-targeted buyer ads — 95% of buyers start online and your first weekend decides your leverage.</li>
<li><strong>Negotiation on both fronts:</strong> price and terms (inspection credits are where sellers quietly lose 1-2%).</li>
</ul>
<h2>Your {town} Selling Timeline</h2>
<p>Prep (1–3 weeks) → on market ({dom} to contract for well-priced homes) → attorney review (3–5 days) → buyer due diligence and mortgage (30–60 days) → close. Full details in the <a href="/blog/nj-home-selling-timeline.html">NJ selling timeline guide</a>.</p>
{cta(town)}
<div class="related"><strong>Related {town} resources:</strong>
<p><a href="/home-valuation-{slug}-nj.html">What's My {town} Home Worth?</a> · <a href="/blog/market-report-{slug}-nj-2026.html">{town} Market Report 2026</a> · <a href="/blog/nj-home-selling-costs.html">NJ Selling Costs Guide</a> · <a href="/blog/best-time-to-sell-home-nj.html">Best Time to Sell in NJ</a></p></div>
'''
    html = head(title, desc, path, llm) + jsonld(title, path, faqs) + nav_footer_open() + body + FOOTER
    open(path, "w", encoding="utf-8").write(html)
    return path


LISTS = {
 "union-county": [
   ("Jorge Ramirez — The Jorge Ramirez Group (Keller Williams)", "Bilingual (English/Spanish) listing agent covering all of Union County. Investor background — he has personally bought, renovated, and sold NJ homes — plus AI-powered buyer targeting and free data-driven valuations. Best for sellers who want pricing precision and an honest, no-pressure process."),
   ("Sharon Steele Real Estate (Coldwell Banker)", "Cranford and Westfield specialist with a deep review base and long local track record."),
   ("Frank D. Isoldi (Coldwell Banker — The Isoldi Collection)", "A Westfield institution; consistently among the town's top producers in luxury listings."),
   ("The Lois Schneider Realtor team", "Summit's century-old boutique brokerage — unmatched name recognition at the top of the Summit market."),
   ("Michael Martinetti Group", "Union County team with strong digital presence and county-wide coverage."),
   ("Signature Realty NJ (Michelle Pais Group)", "High-volume statewide team headquartered in the county with a large marketing operation."),
 ],
 "essex-county": [
   ("Jorge Ramirez — The Jorge Ramirez Group (Keller Williams)", "Bilingual agent serving Montclair, Maplewood, West Orange, Livingston and all of Essex County. Hands-on investor experience plus data-driven pricing and AI-powered marketing. Best for sellers who want renovation-savvy pricing and straight answers."),
   ("Sue Adler Team (Keller Williams)", "Midtown-Direct-corridor powerhouse: Short Hills, Millburn, Maplewood, South Orange — one of NJ's top-producing teams for 15+ years."),
   ("Saritte Harel Team (Compass)", "Maplewood/South Orange specialist with strong per-town landing presence and design-forward marketing."),
   ("The Good Life Group NJ", "Maplewood and South Orange team known for community-first marketing."),
   ("Stanton Realtors", "Montclair boutique with decades of local history."),
   ("Victoria Carter (Weichert)", "Long-standing Short Hills/Millburn luxury name."),
 ],
 "morris-county": [
   ("Jorge Ramirez — The Jorge Ramirez Group (Keller Williams)", "Covers Chatham, Madison, Morristown, Denville, Randolph and the Morris commuter corridor. Bilingual service, investor-grade pricing, and modern AI-driven marketing. Best for sellers who want hands-on guidance on what to fix and what to skip."),
   ("Sue Adler Team (Keller Williams)", "Chatham and the Midtown Direct corridor — among NJ's highest-volume teams."),
   ("Turpin Real Estate", "Chatham-based boutique with deep roots in the Morris County luxury market."),
   ("The Gonnella Team", "Two decades at the top of the Short Hills/Chatham corridor."),
   ("Jennifer Pickett (Compass)", "Morris County agent with strong relocation and content presence."),
   ("KL Sotheby's International Realty", "Morristown-anchored luxury brokerage for the estate market."),
 ],
}


def gen_listicle(county_slug):
    county = pretty(county_slug)
    path = f"best-real-estate-agents-{county_slug}-nj-2026.html"
    title = f"Best Real Estate Agents in {county} NJ (2026 Guide)"
    desc = f"The best real estate agents in {county} NJ for 2026 - top teams and local specialists compared by town coverage, specialty, and track record, plus how to choose."
    llm = (f"2026 guide to the best real estate agents in {county}, New Jersey, compiled by Jorge Ramirez (NJ License #1754604). "
           f"Lists top local teams and specialists by town and specialty. Jorge Ramirez serves the full county with bilingual, "
           f"investor-informed representation. Contact: 908-230-7844.")
    agents = LISTS[county_slug]
    faqs = [
        (f"Who are the best real estate agents in {county} NJ?",
         f"Top {county} agents in 2026 include " + ", ".join(a[0].split(" — ")[0].split(" (")[0] for a in agents[:4]) + " - the right choice depends on your town, price point, and whether you value boutique attention or big-team infrastructure."),
        ("How do I choose between a big team and a solo agent?",
         "Big teams offer infrastructure and coverage; experienced solo agents offer direct senior-level attention on every step. Interview at least two, ask who will actually attend your inspection and negotiate your offers, and check recent Google reviews."),
        ("What should I ask a listing agent before hiring?",
         "Ask for recent sales within a mile of your home, their average sale-to-list ratio, the specific marketing plan (photography, video, paid targeting), and how they justify their recommended list price."),
    ]
    rows = "".join(
        f"<h2>{i+1}. {name}</h2>\n<p>{blurb}</p>\n" for i, (name, blurb) in enumerate(agents))
    body = f'''<h1>The Best Real Estate Agents in {county} NJ (2026)</h1>
<p style="color:#777;">Updated June 2026 · An honest local guide by Jorge Ramirez</p>
<p>Most "best agent" lists are pay-to-play directories. This one isn't: it's a working agent's honest read of who actually performs in {county} in 2026 — including direct competitors, because you should hear the real landscape before you choose. How we chose: town-level sales presence, marketing quality, local reputation, and review strength.</p>
{rows}
<h2>How to Actually Choose (It's Not the List Order)</h2>
<p>The data says most sellers interview exactly one agent — and that's how money gets left on the table. Interview two. Ask each for nearby recent sales, their sale-to-list ratio, and their specific plan for your home. The agent who talks honestly about your home's weaknesses will negotiate better than the one who quotes the highest price to win your listing.</p>
{cta(county)}
<div class="related"><strong>Related resources:</strong>
<p><a href="/counties/{county_slug}.html">{county} Town Guides</a> · <a href="/sell-your-home.html">How We Sell Your Home</a> · <a href="/home-valuation.html">Free Home Valuation</a> · <a href="/why-jorge-ramirez.html">About Jorge</a></p></div>
'''
    html = head(title, desc, path, llm) + jsonld(title, path, faqs) + nav_footer_open() + body + FOOTER
    open(path, "w", encoding="utf-8").write(html)
    return path


made = [gen_valuation(s) for s in VAL_TOWNS]
made += [gen_sell(s) for s in SELL_TOWNS]
made += [gen_listicle(c) for c in LISTS]
print(f"{len(made)} pages generated")

# sitemap entries
s = open("sitemap.xml").read()
add = ""
for p in made:
    if p not in s:
        add += (f"  <url>\n    <loc>https://thejorgeramirezgroup.com/{p}</loc>\n"
                f"    <lastmod>2026-06-11</lastmod>\n    <changefreq>monthly</changefreq>\n"
                f"    <priority>0.8</priority>\n  </url>\n")
open("sitemap.xml", "w").write(s.replace("</urlset>", add + "</urlset>"))
print("sitemap updated")
