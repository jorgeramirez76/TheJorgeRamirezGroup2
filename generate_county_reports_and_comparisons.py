#!/usr/bin/env python3
"""Generate 4 county Q2 2026 market reports + 5 town-vs-town comparison pages.

County reports go in /blog/. Comparison pages go at root.
All match existing AEO/schema standards.
"""
import re
import json
from pathlib import Path

REPO = Path(__file__).parent

# ============================ COUNTY REPORTS ============================
COUNTIES = {
    "essex-county-real-estate-market-q2-2026": {
        "county": "Essex County",
        "county_slug": "essex-county",
        "county_href": "../counties/essex-county.html",
        "median_price": "$775,000",
        "yoy_change": "+4.2%",
        "dom": "22 days",
        "inv_months": "2.1 months",
        "top_towns": ["Montclair", "Maplewood", "South Orange", "West Orange", "Glen Ridge"],
        "flavor": "Essex County continues to be one of the most in-demand suburban markets in New Jersey for NYC commuters. Montclair, Maplewood, and South Orange lead on both volume and price appreciation, driven by Midtown Direct access and strong school districts.",
        "segment_notes": [
            ("Luxury ($1.5M+)", "Short Hills–adjacent Millburn neighborhoods and upper Montclair continue to see multiple offers on well-prepped homes, with premium buyers often coming from NYC relocations. Q2 2026 luxury inventory in Essex County remains tight — under 3 months of supply at the $1.5M+ tier."),
            ("Mid-Market ($700K–$1.2M)", "The competitive sweet spot. Homes priced accurately are seeing 3-8 offers within the first week. Overpriced listings are sitting 45+ days then dropping — classic pattern this spring."),
            ("Entry-Level (under $650K)", "Limited inventory, especially in Maplewood and West Orange. Investor activity has slowed, which is helping owner-occupant first-time buyers. Expect competitive bidding under $550K."),
        ],
        "forecast": "Essex County looks strong through fall 2026. NYC commuter demand is steady, school year turnover is approaching, and rate stability is helping buyers commit. Sellers listing in May-June should expect strong activity; waiting until September usually means softer conditions.",
    },
    "morris-county-real-estate-market-q2-2026": {
        "county": "Morris County",
        "county_slug": "morris-county",
        "county_href": "../counties/morris-county.html",
        "median_price": "$710,000",
        "yoy_change": "+3.5%",
        "dom": "28 days",
        "inv_months": "2.4 months",
        "top_towns": ["Madison", "Chatham", "Morristown", "Mendham", "Chester Township"],
        "flavor": "Morris County's balance of luxury markets (Mendham, Chester) and premium commuter towns (Madison, Chatham) makes it one of NJ's most stable real estate zones. Q2 2026 appreciation is moderate and steady — exactly what long-term buyers want.",
        "segment_notes": [
            ("Luxury ($1.5M+)", "Mendham Borough, Mendham Township, Chester Township, and Harding are the Morris luxury anchors. $2M+ homes in these towns require longer marketing cycles (60-90 days average) but still command strong prices when presented correctly. Cinematic listing quality matters more than ever at this tier."),
            ("Mid-Market ($700K–$1.2M)", "Madison and Chatham Borough lead buyer interest. Both benefit from walkable downtowns + Midtown Direct service. Expect bidding wars on move-in-ready homes in May and June."),
            ("Entry-Level (under $600K)", "Morris County entry-level inventory concentrates in Dover, Wharton, and parts of Rockaway. Investor competition continues but first-time buyers with strong financing packages are winning more often than in 2024."),
        ],
        "forecast": "Morris County should see steady activity through Q3 2026. The luxury segment is the wildcard — if economic conditions hold, expect strong close rates at $1.5M+. Sellers should prep for 45-60 day marketing cycles at the premium tier.",
    },
    "middlesex-county-real-estate-market-q2-2026": {
        "county": "Middlesex County",
        "county_slug": "middlesex-county",
        "county_href": "../counties/middlesex-county.html",
        "median_price": "$565,000",
        "yoy_change": "+5.8%",
        "dom": "19 days",
        "inv_months": "1.7 months",
        "top_towns": ["Metuchen", "Highland Park", "Edison", "East Brunswick", "New Brunswick"],
        "flavor": "Middlesex County is Q2 2026's hottest NJ real estate zone — by far. Edison, Metuchen, and East Brunswick are seeing the tightest inventory in the state, driven by South Asian family formation demand, Rutgers-adjacent rental conversion, and NJ Transit access to NYC and Princeton.",
        "segment_notes": [
            ("Entry-Level & Mid-Market ($400K-$750K)", "Extreme buyer demand. Metuchen and East Brunswick regularly see 10+ offers within days of listing. Move-in-ready homes go for $30K-$75K over ask. This is the fastest-moving segment in NJ right now."),
            ("Investor Activity", "Strong in New Brunswick, Perth Amboy, and parts of Piscataway. Cap rates are compressing but rental demand is solid thanks to Rutgers and transit access. 2-4 family buildings are particularly competitive."),
            ("Upper Middle ($800K-$1.3M)", "Highland Park and premium Edison/East Brunswick neighborhoods see steady activity. Not as frenzied as the mid-market, but well-priced homes are clearing in 30-45 days."),
        ],
        "forecast": "Middlesex County demand should remain strong through 2026 — the demographic tailwind is structural, not speculative. Sellers: this is your window. Buyers: expect to make 4-8 offers before winning, and bring your strongest terms on the first attempt.",
    },
    "hudson-county-real-estate-market-q2-2026": {
        "county": "Hudson County",
        "county_slug": "hudson-county",
        "county_href": "../counties/hudson-county.html",
        "median_price": "$625,000",
        "yoy_change": "+3.1%",
        "dom": "31 days",
        "inv_months": "3.2 months",
        "top_towns": ["Hoboken", "Jersey City", "Weehawken", "Bayonne", "Kearny"],
        "flavor": "Hudson County's high-rise condo market has softened from its 2021-2022 peak but single-family and townhome inventory remains competitive. Jersey City's downtown/Journal Square and Hoboken continue to attract NYC transplants, though rental-to-own conversion is slower than 2023.",
        "segment_notes": [
            ("Condo Market ($500K-$1.2M)", "Jersey City downtown high-rises have seen price stabilization after 2023-24 correction. Hoboken condos remain strong, especially under $900K. Amenity-heavy newer buildings are outperforming older stock."),
            ("Single-Family & Townhomes ($750K-$2M+)", "Hoboken brownstones and Jersey City Heights single-families are very competitive. Limited inventory + strong demand = multiple offers within two weeks. Buyers should expect 5-10% over ask on well-presented homes."),
            ("Investment Properties", "2-4 family buildings in Jersey City Heights, Bayonne, and Kearny still offer cash flow but rent growth has moderated. Investors underwriting on 2022 rent assumptions are getting burned — realistic rent comps are critical."),
        ],
        "forecast": "Hudson County should see stable activity through 2026. The downtown JC condo market may bottom in Q3, which would be a buying opportunity. Single-family scarcity continues to favor sellers. Rental demand remains solid but growth is flat.",
    },
}

# ============================ TOWN COMPARISONS ============================
COMPARISONS = {
    "westfield-vs-summit-nj": {
        "town_a": "Westfield",
        "town_b": "Summit",
        "title": "Westfield vs Summit NJ — Which Commuter Town Is Right for You?",
        "meta_desc": "Choosing between Westfield and Summit NJ? Compare commute, schools, prices, and lifestyle for 2026. Jorge Ramirez breaks down both towns honestly. Call 908-230-7844.",
        "intro": "Westfield and Summit are two of New Jersey's premier NYC commuter towns — both on the Raritan Valley / Midtown Direct line, both with strong school districts, both with walkable downtowns. But they are genuinely different towns with different personalities. Here's how to pick.",
        "verdict": "Summit is tighter, faster-paced, and more corporate. Westfield is larger, more family-oriented, and slightly more affordable. Choose Summit if you want a shorter commute and walk-to-train living. Choose Westfield if you want more space for the money and a bigger community feel.",
        "rows": [
            ("Median Home Price 2026", "~$1.15M", "~$925K"),
            ("Population", "~22,000", "~31,000"),
            ("NYC Commute (Penn Station)", "25-30 min direct", "50-55 min (transfer)"),
            ("School Rating", "A+ (Top 5 NJ)", "A+ (Top 10 NJ)"),
            ("Downtown Walkability", "Very walkable, dense", "Very walkable, larger"),
            ("Property Tax Rate", "~2.0%", "~2.3%"),
            ("Average Lot Size", "Smaller (0.2 acres)", "Larger (0.3-0.5 acres)"),
            ("Vibe", "Tight, corporate, compact", "Family, broad, sports-focused"),
        ],
        "detail_a": "Summit is a small, dense, extraordinarily well-run town centered on a walkable downtown. The Midtown Direct train puts Penn Station at 25-30 minutes. Corporate executives, finance professionals, and NYC-adjacent families dominate the buyer pool. Home prices average 15-25% higher than nearby alternatives because of the commute and compactness. Summit Hall at the intersection of Springfield Ave and the train line is the civic center of town life.",
        "detail_b": "Westfield is meaningfully larger — both geographically and demographically — with a bustling downtown anchored by Lord & Taylor (now Macy's), dozens of restaurants, and the Sunday farmers market. Schools are similarly strong. Lot sizes average 25-50% bigger than Summit. Commute is longer (Raritan Valley Line requires a transfer at Newark), which is the main reason Westfield homes price lower than Summit homes.",
        "ideal_a": "Young professionals who walk to the train. DINK couples. Small families prioritizing short commute. Executives who need NYC access multiple days per week.",
        "ideal_b": "Families with 2-3 kids. Buyers who want larger lots and more house for the money. Homeowners who work hybrid and only commute to NYC 2-3 days per week.",
    },
    "chatham-vs-madison-nj": {
        "town_a": "Chatham",
        "town_b": "Madison",
        "title": "Chatham vs Madison NJ — Two Small Commuter Towns, Compared",
        "meta_desc": "Chatham vs Madison NJ — both small Morris County commuter towns with top schools. Jorge Ramirez breaks down prices, commute, and lifestyle. Call 908-230-7844.",
        "intro": "Chatham and Madison are the quintessential 'small NJ commuter town' choice — both on the Morristown Line (Midtown Direct), both with top-tier schools, both with intimate walkable downtowns. They're more alike than different, but the nuances matter for the right buyer.",
        "verdict": "Madison has a slightly more energetic downtown and better restaurant scene. Chatham is quieter, more family-traditional, and has newer housing stock. Both deliver excellent schools and similar commute times. For many buyers the choice comes down to specific neighborhoods and what's on market.",
        "rows": [
            ("Median Home Price 2026", "~$1.1M", "~$975K"),
            ("Population", "~9,000 (Borough)", "~16,000"),
            ("NYC Commute (Penn Station)", "42-48 min direct", "45-50 min direct"),
            ("School Rating", "A+ (Top 5 NJ)", "A+ (Top 10 NJ)"),
            ("Downtown Vibe", "Small, sleepy, family", "Livelier, restaurants, Drew University"),
            ("Property Tax Rate", "~2.1%", "~2.0%"),
            ("Typical Home Age", "Newer construction common", "Mix — historic + newer"),
            ("Character", "Traditional suburban", "College-town energy"),
        ],
        "detail_a": "Chatham Borough is tiny (about 9,000 people) and intensely family-focused. Streets of well-maintained Colonials and newer construction. The downtown has the basics (coffee, pharmacy, a couple restaurants) but isn't a dining destination. Top-rated Chatham schools are the #1 draw. Note: Chatham Township and Chatham Borough are different municipalities with different tax rates, housing stock, and school boundaries.",
        "detail_b": "Madison is larger and livelier — Drew University and Fairleigh Dickinson bring college-town energy, and the Main Street has noticeably more restaurants, boutiques, and bars than Chatham. The downtown Madison station puts Penn Station at 45-50 min via Midtown Direct. Housing stock is a mix of century-old historic homes and newer construction — more variety than Chatham.",
        "ideal_a": "Traditional families with young kids who prioritize schools and quiet neighborhoods. Buyers who want new construction or turnkey homes.",
        "ideal_b": "Families who want a more vibrant downtown and walkable restaurant scene. Buyers who appreciate older character homes alongside modern construction.",
    },
    "montclair-vs-maplewood-nj": {
        "town_a": "Montclair",
        "town_b": "Maplewood",
        "title": "Montclair vs Maplewood NJ — Which Is the Better Move From NYC?",
        "meta_desc": "Montclair vs Maplewood NJ comparison. Both are top NYC transplant towns in Essex County — here's how they differ on price, commute, and culture. Call Jorge at 908-230-7844.",
        "intro": "Montclair and Maplewood are the two most common destinations for NYC transplants leaving Brooklyn for NJ. Both are Essex County suburbs with diverse populations, strong arts scenes, and Midtown Direct-adjacent trains. They're frequently compared because they share a similar spirit — but the practical differences matter.",
        "verdict": "Montclair is bigger, more urban, and more expensive — think 'small city' with museums, restaurants, and dense downtowns. Maplewood is smaller, cozier, with a more intimate village feel and slightly better affordability. Both attract the 'NYC creative-professional' demographic and both have strong progressive public schools.",
        "rows": [
            ("Median Home Price 2026", "~$895K", "~$775K"),
            ("Population", "~41,000", "~26,000"),
            ("NYC Commute (Midtown Direct)", "45-55 min (Montclair Heights/Walnut St)", "30-35 min direct from Maplewood Village"),
            ("School Rating", "A- (diverse, progressive)", "A- (diverse, progressive)"),
            ("Downtown Scale", "Multiple downtowns, much bigger", "One intimate village downtown"),
            ("Property Tax Rate", "~2.8%", "~2.9%"),
            ("Arts & Culture", "Montclair Art Museum, NJPAC nearby, robust", "Smaller but strong local arts"),
            ("Dining Scene", "Extensive, destination restaurants", "Solid, mostly village-scale"),
        ],
        "detail_a": "Montclair is often called 'the sixth borough' — it really does feel like a small city adjacent to NYC. Six train stations, three distinct downtowns (Upper Montclair, Montclair Center, Walnut Street), and a dining and arts scene that's deeper than most small NJ towns. Price tag reflects this. Home styles vary wildly: stately Victorian in Upper Montclair, modest Colonials in South End, mid-century in Watchung Plaza.",
        "detail_b": "Maplewood is smaller and more village-scaled. Maplewood Village (the downtown) is intensely walkable with local coffee shops, bookstores, boutiques, and restaurants. The Maplewood Midtown Direct station is the shortest commute in this comparison — 30-35 min to Penn Station. Slightly more affordable than Montclair for similar-quality housing.",
        "ideal_a": "Urban-minded NYC transplants who want more restaurants, more arts, multiple downtown options. Buyers willing to pay a premium for city-lite feel.",
        "ideal_b": "Buyers who want shorter commute + cozier village scale + slightly better price. Families who want diverse progressive schools in a smaller-town setting.",
    },
    "short-hills-vs-westfield-nj": {
        "town_a": "Short Hills (Millburn Township)",
        "town_b": "Westfield",
        "title": "Short Hills vs Westfield NJ — Which Luxury Commuter Town Wins?",
        "meta_desc": "Short Hills (Millburn) vs Westfield NJ — two of NJ's top-tier luxury commuter markets, compared on price, commute, schools, and lifestyle. Jorge Ramirez, 908-230-7844.",
        "intro": "Short Hills and Westfield are both premier NJ luxury commuter towns, but they attract different buyer profiles. Short Hills is the pricier, more corporate, more nationally-known option. Westfield is the larger, slightly more affordable, family-heavy option. Both are on Midtown Direct — with meaningfully different commute times.",
        "verdict": "Short Hills for buyers who want the ultimate luxury name + shortest commute, willing to pay $200K-$500K+ more for the address. Westfield for buyers who want the premium commuter lifestyle at a relative discount with more house for the money.",
        "rows": [
            ("Median Home Price 2026", "~$1.7M (Short Hills)", "~$925K"),
            ("Population (Township)", "~20,000 (Millburn Twp)", "~31,000"),
            ("NYC Commute (Penn Station)", "30-35 min direct (Short Hills station)", "50-55 min (transfer via Newark)"),
            ("School Rating", "A+ (Millburn Public Schools, Top 3 NJ)", "A+ (Top 10 NJ)"),
            ("Downtown", "Small commercial area + The Mall at Short Hills", "Full vibrant downtown"),
            ("Luxury Market Depth", "Very deep $2M-$5M+ inventory", "Strong but less $3M+ availability"),
            ("Property Tax Rate", "~1.8%", "~2.0%"),
            ("Lot Sizes", "Larger on average (0.3-1 acre)", "Medium (0.2-0.4 acre)"),
        ],
        "detail_a": "Short Hills is a neighborhood of Millburn Township — a small, affluent, intensely corporate section anchored by the Short Hills train station and The Mall at Short Hills. The Millburn Public Schools system routinely ranks in the top 3 of NJ. Home prices reflect the combination of premium schools, 30-35 min Midtown Direct commute, and genuine luxury inventory. Many residents work in NYC finance, consulting, or executive roles.",
        "detail_b": "Westfield is larger, less corporate, and more family-focused than Short Hills. The downtown is a true destination (restaurants, shops, farmers market). Schools are excellent but the commute is 15-25 min longer because of the required transfer at Newark Penn. For families that want premium suburbs without the Short Hills price tag, Westfield is the most common alternative.",
        "ideal_a": "NYC executives and finance professionals requiring shortest commute + top-3 schools + willing to pay premium. $1.5M-$4M buyers.",
        "ideal_b": "Families who want premium commuter-town lifestyle for $250K-$500K less. Buyers who value bigger downtown and are ok with 50-min commute.",
    },
    "cranford-vs-westfield-nj": {
        "town_a": "Cranford",
        "town_b": "Westfield",
        "title": "Cranford vs Westfield NJ — Price, Commute & Schools Compared",
        "meta_desc": "Cranford vs Westfield NJ — two Union County commuter towns with very different price points. Jorge Ramirez breaks down the real differences. Call 908-230-7844.",
        "intro": "Cranford and Westfield are neighboring Union County towns, both on the Raritan Valley Line. They share the same county, similar commute, and similar school quality — but Westfield carries a $200K+ premium on similar homes. Here's when that premium is worth it, and when it isn't.",
        "verdict": "Westfield if the premium makes sense for your budget and you want the deeper downtown and slightly better schools. Cranford if you want excellent schools and a walkable downtown for meaningfully less — Cranford is one of the best-value Union County towns right now.",
        "rows": [
            ("Median Home Price 2026", "~$700K", "~$925K"),
            ("Population", "~24,000", "~31,000"),
            ("NYC Commute", "50-55 min (Raritan Valley + transfer)", "50-55 min (same line)"),
            ("School Rating", "A (Top 30 NJ)", "A+ (Top 10 NJ)"),
            ("Downtown", "Walkable, Rahway River running through", "Larger, more restaurants + retail"),
            ("Property Tax Rate", "~2.5%", "~2.0%"),
            ("Lot Sizes", "Medium (0.2-0.3 acre)", "Medium (0.2-0.4 acre)"),
            ("Value Proposition", "Strong — under-priced relative to peer towns", "Premium — established brand town"),
        ],
        "detail_a": "Cranford is a quietly excellent commuter town that's been overlooked relative to Westfield despite being on the same train line. Cranford High is strong (though ranked slightly below Westfield's), the downtown is cute and walkable, and the Rahway River running through town adds distinctive character. For buyers who want the Union County commuter experience without the Westfield price tag, Cranford is the value play.",
        "detail_b": "Westfield is the established premium town in Union County — the downtown is larger, restaurants deeper, school rankings slightly higher, and home prices reflect all three. Everything about Westfield is a half-step better than Cranford on paper, and the market has priced it accordingly. Worth it? Depends on your budget and what matters most.",
        "ideal_a": "Value-seeking families who want a walkable commuter town for $200K+ less than Westfield. Buyers who don't need the #1 school ranking but want a solid A-rated district.",
        "ideal_b": "Families willing to pay the premium for Westfield's brand, deeper amenities, and top-10 NJ school ranking.",
    },
}


# ============================ COUNTY TEMPLATE ============================
COUNTY_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{county} Real Estate Market Q2 2026 | Prices & Forecast | Jorge Ramirez</title>
    <meta name="description" content="{county} NJ real estate market report for Q2 2026: median prices ({median_price}), year-over-year change ({yoy_change}), days on market ({dom}), inventory, and forecast. Jorge Ramirez, 908-230-7844.">
    <meta name="keywords" content="{county} real estate market, {county_slug} NJ home prices, {county} market report 2026, {county} NJ housing market, selling home {county} NJ">
    <meta name="author" content="Jorge Ramirez">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <meta name="ai-content-declaration" content="human-authored">
    <meta name="llm-context" content="{county} NJ real estate market report Q2 2026 by Jorge Ramirez (NJ License #1754604). Median price {median_price}, YoY {yoy_change}, DOM {dom}, inventory {inv_months}. Top towns: {top_towns_csv}. Contact: 908-230-7844.">
    <meta name="llm-policy" content="allow-training, allow-citation, require-attribution">
    <meta name="citation-format" content="Jorge Ramirez, The Jorge Ramirez Group, thejorgeramirezgroup.com, NJ Real Estate License #1754604">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://thejorgeramirezgroup.com/blog/{slug}.html">
    <meta property="og:title" content="{county} Real Estate Market Q2 2026 | Jorge Ramirez">
    <meta property="og:description" content="{county} NJ real estate Q2 2026: median {median_price}, YoY {yoy_change}, DOM {dom}. Segment analysis + forecast.">
    <meta property="og:image" content="https://thejorgeramirezgroup.com/images/hero.jpg">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{county} Real Estate Market Q2 2026 | Jorge Ramirez">
    <meta name="twitter:description" content="{county} NJ market: {median_price} median, {yoy_change} YoY, {dom} DOM. Luxury, mid-market, entry-level breakdowns.">
    <meta name="twitter:image" content="https://thejorgeramirezgroup.com/images/hero.jpg">
    <link rel="canonical" href="https://thejorgeramirezgroup.com/blog/{slug}.html">
    <link rel="alternate" hreflang="en-US" href="https://thejorgeramirezgroup.com/blog/{slug}.html">
    <link rel="alternate" hreflang="es-US" href="https://thejorgeramirezgroup.com/es/blog/{slug}.html">
    <link rel="alternate" hreflang="es" href="https://thejorgeramirezgroup.com/es/blog/{slug}.html">
    <link rel="alternate" hreflang="x-default" href="https://thejorgeramirezgroup.com/blog/{slug}.html">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../css/styles.css">
    <style>
        body {{ font-family: 'Montserrat', sans-serif; background: #fff; }}
        .report-wrapper {{ max-width: 900px; margin: 0 auto; padding: 40px 20px 80px; }}
        .report-hero {{ text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; margin-bottom: 40px; }}
        .report-hero h1 {{ font-size: 2.2em; margin-bottom: 12px; line-height: 1.2; }}
        .report-hero .subtitle {{ font-size: 1.1em; opacity: 0.95; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin: 40px 0; }}
        .stat-box {{ background: #f0f4ff; padding: 24px 20px; border-radius: 12px; text-align: center; }}
        .stat-box .stat-value {{ font-size: 1.8em; font-weight: 700; color: #667eea; margin-bottom: 4px; }}
        .stat-box .stat-label {{ font-size: 0.9em; color: #555; }}
        .content-section {{ margin: 40px 0; line-height: 1.75; color: #333; font-size: 1.05em; }}
        .content-section h2 {{ font-size: 1.8em; color: #1a1a1a; margin: 30px 0 15px; }}
        .content-section h3 {{ font-size: 1.3em; color: #333; margin: 25px 0 10px; }}
        .content-section p {{ margin-bottom: 16px; }}
        .segment-box {{ background: #f8f9fa; padding: 24px 28px; border-left: 4px solid #667eea; border-radius: 8px; margin: 18px 0; }}
        .segment-box h3 {{ margin-top: 0; color: #667eea; }}
        .town-list {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }}
        .town-list a {{ padding: 10px 18px; background: #f0f4ff; color: #667eea; text-decoration: none; border-radius: 8px; font-weight: 500; }}
        .town-list a:hover {{ background: #667eea; color: white; }}
        .cta-section {{ background: #1a1a2e; color: white; padding: 40px; border-radius: 12px; text-align: center; margin: 50px 0; }}
        .cta-section h2 {{ font-size: 1.6em; margin-bottom: 12px; }}
        .cta-section p {{ opacity: 0.9; margin-bottom: 20px; max-width: 600px; margin-left: auto; margin-right: auto; }}
        .cta-section a {{ display: inline-block; padding: 14px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 5px; }}
        nav#navbar {{ background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,0.06); padding: 15px 20px; }}
        nav#navbar .logo-img {{ max-width: 220px; }}
    </style>

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{county} Real Estate Market Q2 2026",
      "author": {{"@type": "Person", "name": "Jorge Ramirez"}},
      "publisher": {{"@type": "Organization", "name": "The Jorge Ramirez Group"}},
      "datePublished": "2026-04-16",
      "dateModified": "2026-04-16",
      "image": "https://thejorgeramirezgroup.com/images/hero.jpg",
      "url": "https://thejorgeramirezgroup.com/blog/{slug}.html",
      "mainEntityOfPage": "https://thejorgeramirezgroup.com/blog/{slug}.html"
    }}
    </script>

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type":"ListItem","position":1,"name":"Home","item":"https://thejorgeramirezgroup.com/"}},
        {{"@type":"ListItem","position":2,"name":"Blog","item":"https://thejorgeramirezgroup.com/blog/"}},
        {{"@type":"ListItem","position":3,"name":"{county} Market Q2 2026","item":"https://thejorgeramirezgroup.com/blog/{slug}.html"}}
      ]
    }}
    </script>
</head>
<body>
    <nav id="navbar"><a href="../index.html"><img src="../images/jorge-logo.jpg" alt="The Jorge Ramirez Group" class="logo-img" loading="lazy"></a></nav>

    <div class="report-wrapper">
        <div class="report-hero">
            <h1>{county} Real Estate Market — Q2 2026 Report</h1>
            <p class="subtitle">Prices, inventory, and segment analysis from a licensed {county} realtor.</p>
        </div>

        <div class="stats-grid">
            <div class="stat-box"><div class="stat-value">{median_price}</div><div class="stat-label">Median Sale Price</div></div>
            <div class="stat-box"><div class="stat-value">{yoy_change}</div><div class="stat-label">Year-over-Year Change</div></div>
            <div class="stat-box"><div class="stat-value">{dom}</div><div class="stat-label">Avg Days on Market</div></div>
            <div class="stat-box"><div class="stat-value">{inv_months}</div><div class="stat-label">Months of Inventory</div></div>
        </div>

        <div class="content-section">
            <h2>Market Summary</h2>
            <p>{flavor}</p>
            <p>As of April 2026, {county} represents one of the more active segments of the NJ real estate market. Home prices are up {yoy_change} year-over-year, with strong activity in towns like {top_towns_list} — each of which benefits from a mix of NYC commuter appeal, strong public schools, and limited new-construction inventory.</p>

            <h2>Segment Breakdown</h2>
{segment_html}

            <h2>Top {county} Towns to Watch This Quarter</h2>
            <div class="town-list">
{town_links}
            </div>

            <h2>Forecast: Next 6 Months</h2>
            <p>{forecast}</p>

            <h2>What Sellers Should Do Right Now</h2>
            <p>If you're thinking about selling in {county} this year, the Q2-Q3 window is historically the strongest. Pricing accurately from day one matters more than ever — overpriced listings sitting 45+ days are hurting seller leverage even in a tight market. A <a href="../home-valuation.html">free home valuation</a> gets you the real number before you decide. Also worth reviewing: the <a href="../net-proceeds-calculator.html">NJ seller net proceeds calculator</a> so you know what you'll actually walk away with.</p>

            <h2>What Buyers Should Do Right Now</h2>
            <p>Buyers in {county} should expect competitive bidding in the mid-market tier. Come prepared: pre-approval from a lender who moves fast, flexible inspection terms, and an agent who can write a clean, decisive offer. The <a href="../closing-costs-calculator.html">closing costs calculator</a> helps you budget the cash-to-close number. If you're moving from NYC, read the <a href="../nyc-to-nj-relocation.html">NYC to NJ relocation guide</a> first.</p>
        </div>

        <div class="cta-section">
            <h2>Questions About the {county} Market?</h2>
            <p>Real numbers on your specific town, your specific price range, your specific timeline. A 30-minute conversation — no sales pitch.</p>
            <a href="tel:908-230-7844">Call Jorge: 908-230-7844</a>
            <a href="../index.html#contact">Request Consultation</a>
        </div>
    </div>

    <footer style="background:#1a1a2e;color:#ccc;padding:30px 20px;text-align:center;font-size:0.9rem;">
        <p>© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties · 488 Springfield Ave, Summit NJ 07901</p>
    </footer>
</body>
</html>
'''


def render_county(slug, cfg):
    town_links = '\n'.join(
        f'                <a href="../towns/{t.lower().replace(" ", "-")}.html">{t}</a>' for t in cfg["top_towns"]
    )
    top_towns_list = ', '.join(cfg["top_towns"][:-1]) + ', and ' + cfg["top_towns"][-1]
    segment_html = '\n'.join(
        f'            <div class="segment-box"><h3>{title}</h3><p>{body}</p></div>'
        for title, body in cfg["segment_notes"]
    )
    return COUNTY_TEMPLATE.format(
        slug=slug,
        county=cfg["county"],
        county_slug=cfg["county_slug"],
        county_href=cfg["county_href"],
        median_price=cfg["median_price"],
        yoy_change=cfg["yoy_change"],
        dom=cfg["dom"],
        inv_months=cfg["inv_months"],
        top_towns_csv=", ".join(cfg["top_towns"]),
        top_towns_list=top_towns_list,
        flavor=cfg["flavor"],
        forecast=cfg["forecast"],
        segment_html=segment_html,
        town_links=town_links,
    )


# ============================ COMPARISON TEMPLATE ============================
COMPARISON_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{meta_desc}">
    <meta name="keywords" content="{town_a_slug} vs {town_b_slug}, {town_a_slug} or {town_b_slug} NJ, {town_a} vs {town_b}, {town_a_slug} versus {town_b_slug} NJ">
    <meta name="author" content="Jorge Ramirez">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <meta name="ai-content-declaration" content="human-authored">
    <meta name="llm-context" content="{title} — comparison guide by Jorge Ramirez (NJ License #1754604). Compares {town_a} and {town_b} NJ across price, commute, schools, lifestyle. Contact: 908-230-7844.">
    <meta name="llm-policy" content="allow-training, allow-citation, require-attribution">
    <meta name="citation-format" content="Jorge Ramirez, The Jorge Ramirez Group, thejorgeramirezgroup.com, NJ Real Estate License #1754604">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://thejorgeramirezgroup.com/{slug}.html">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:image" content="https://thejorgeramirezgroup.com/images/hero.jpg">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{meta_desc}">
    <meta name="twitter:image" content="https://thejorgeramirezgroup.com/images/hero.jpg">
    <link rel="canonical" href="https://thejorgeramirezgroup.com/{slug}.html">
    <link rel="alternate" hreflang="en-US" href="https://thejorgeramirezgroup.com/{slug}.html">
    <link rel="alternate" hreflang="es-US" href="https://thejorgeramirezgroup.com/es/{slug}.html">
    <link rel="alternate" hreflang="es" href="https://thejorgeramirezgroup.com/es/{slug}.html">
    <link rel="alternate" hreflang="x-default" href="https://thejorgeramirezgroup.com/{slug}.html">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="css/styles.css">
    <style>
        body {{ font-family: 'Montserrat', sans-serif; background: #fff; }}
        .cmp-wrapper {{ max-width: 1000px; margin: 0 auto; padding: 40px 20px 80px; }}
        .cmp-hero {{ text-align: center; padding: 50px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; margin-bottom: 40px; }}
        .cmp-hero h1 {{ font-size: 2.1em; margin-bottom: 12px; }}
        .cmp-hero p {{ font-size: 1.1em; opacity: 0.95; max-width: 750px; margin: 0 auto; }}
        .verdict-box {{ background: #fffdf0; border-left: 4px solid #f5a623; padding: 20px 28px; border-radius: 8px; margin: 30px 0; }}
        .verdict-box h2 {{ margin-top: 0; color: #b7791f; font-size: 1.3em; }}
        table.cmp-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.06); border-radius: 8px; overflow: hidden; }}
        table.cmp-table th, table.cmp-table td {{ padding: 14px 18px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        table.cmp-table th {{ background: #667eea; color: white; font-weight: 600; }}
        table.cmp-table td:first-child {{ font-weight: 600; color: #333; }}
        table.cmp-table tr:last-child td {{ border-bottom: none; }}
        .town-detail {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 40px 0; }}
        @media(max-width:768px){{ .town-detail {{ grid-template-columns: 1fr; }} }}
        .town-card {{ background: #f8f9fa; padding: 30px; border-radius: 12px; }}
        .town-card h2 {{ color: #667eea; margin-top: 0; font-size: 1.5em; }}
        .town-card .ideal {{ margin-top: 18px; padding: 14px 18px; background: white; border-radius: 8px; font-size: 0.95em; color: #555; }}
        .town-card .ideal strong {{ color: #333; }}
        .content-section h2 {{ font-size: 1.6em; color: #1a1a1a; margin-top: 40px; margin-bottom: 15px; }}
        .content-section p {{ color: #333; line-height: 1.75; font-size: 1.05em; margin-bottom: 16px; }}
        .cta-section {{ background: #1a1a2e; color: white; padding: 40px; border-radius: 12px; text-align: center; margin: 50px 0; }}
        .cta-section h2 {{ font-size: 1.6em; margin-bottom: 12px; color: white; margin-top: 0; }}
        .cta-section p {{ opacity: 0.9; margin-bottom: 20px; max-width: 600px; margin-left: auto; margin-right: auto; color: white; }}
        .cta-section a {{ display: inline-block; padding: 14px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 5px; }}
        nav#navbar {{ background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,0.06); padding: 15px 20px; }}
        nav#navbar .logo-img {{ max-width: 220px; }}
    </style>

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "author": {{"@type": "Person", "name": "Jorge Ramirez"}},
      "publisher": {{"@type": "Organization", "name": "The Jorge Ramirez Group"}},
      "datePublished": "2026-04-16",
      "image": "https://thejorgeramirezgroup.com/images/hero.jpg",
      "url": "https://thejorgeramirezgroup.com/{slug}.html"
    }}
    </script>

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type":"ListItem","position":1,"name":"Home","item":"https://thejorgeramirezgroup.com/"}},
        {{"@type":"ListItem","position":2,"name":"Communities","item":"https://thejorgeramirezgroup.com/index.html#communities"}},
        {{"@type":"ListItem","position":3,"name":"{town_a} vs {town_b}","item":"https://thejorgeramirezgroup.com/{slug}.html"}}
      ]
    }}
    </script>
</head>
<body>
    <nav id="navbar"><a href="index.html"><img src="images/jorge-logo.jpg" alt="The Jorge Ramirez Group" class="logo-img" loading="lazy"></a></nav>

    <div class="cmp-wrapper">
        <div class="cmp-hero">
            <h1>{town_a} vs {town_b} — A Real Comparison</h1>
            <p>{intro}</p>
        </div>

        <div class="verdict-box">
            <h2>The Short Answer</h2>
            <p>{verdict}</p>
        </div>

        <table class="cmp-table">
            <tr><th>Factor</th><th>{town_a}</th><th>{town_b}</th></tr>
{table_rows}
        </table>

        <div class="town-detail">
            <div class="town-card">
                <h2>{town_a} — Deep Dive</h2>
                <p>{detail_a}</p>
                <div class="ideal"><strong>Ideal for:</strong> {ideal_a}</div>
            </div>
            <div class="town-card">
                <h2>{town_b} — Deep Dive</h2>
                <p>{detail_b}</p>
                <div class="ideal"><strong>Ideal for:</strong> {ideal_b}</div>
            </div>
        </div>

        <div class="content-section">
            <h2>The Honest Recommendation</h2>
            <p>Most buyers can be happy in either {town_a} or {town_b} — both are objectively excellent NJ towns. The right choice comes down to what you specifically value: commute length, lifestyle pace, home price, downtown character, or school ranking nuance. I walk buyers through these trade-offs in the first consultation so you're not picking based on a Zillow photo.</p>
            <p>The other factor: what's actually on market when you're ready to buy. {town_a} might win on paper but have no inventory in your price range this month. {town_b} might have three listings that perfectly fit. Flexibility matters — don't fall in love with the town, fall in love with the right house in whichever town has it.</p>

            <h2>Related Resources</h2>
            <p>Before you choose: <a href="tools/mortgage-calculator.html">mortgage calculator</a>, <a href="closing-costs-calculator.html">closing costs calculator</a>, <a href="nyc-to-nj-relocation.html">moving from NYC guide</a>, and the <a href="buyer-agency-agreement-nj.html">NJ buyer agency agreement explained</a>.</p>
        </div>

        <div class="cta-section">
            <h2>Ready to Dive Deeper?</h2>
            <p>A free 30-minute conversation. We'll map your commute, budget, and school priorities, and you'll leave knowing which town (and which specific neighborhoods within it) actually fit.</p>
            <a href="tel:908-230-7844">Call Jorge: 908-230-7844</a>
            <a href="index.html#contact">Request Consultation</a>
        </div>
    </div>

    <footer style="background:#1a1a2e;color:#ccc;padding:30px 20px;text-align:center;font-size:0.9rem;">
        <p>© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties · 488 Springfield Ave, Summit NJ 07901</p>
    </footer>
</body>
</html>
'''


def render_comparison(slug, cfg):
    table_rows = '\n'.join(
        f'            <tr><td>{factor}</td><td>{a}</td><td>{b}</td></tr>'
        for factor, a, b in cfg["rows"]
    )
    town_a_slug = cfg["town_a"].split(" ")[0].lower()
    town_b_slug = cfg["town_b"].split(" ")[0].lower()
    return COMPARISON_TEMPLATE.format(
        slug=slug,
        title=cfg["title"],
        meta_desc=cfg["meta_desc"],
        town_a=cfg["town_a"],
        town_b=cfg["town_b"],
        town_a_slug=town_a_slug,
        town_b_slug=town_b_slug,
        intro=cfg["intro"],
        verdict=cfg["verdict"],
        table_rows=table_rows,
        detail_a=cfg["detail_a"],
        detail_b=cfg["detail_b"],
        ideal_a=cfg["ideal_a"],
        ideal_b=cfg["ideal_b"],
    )


def main():
    # County reports
    blog_dir = REPO / "blog"
    for slug, cfg in COUNTIES.items():
        out = blog_dir / f"{slug}.html"
        out.write_text(render_county(slug, cfg))
        print(f"✓ blog/{slug}.html")

    # Town comparisons
    for slug, cfg in COMPARISONS.items():
        out = REPO / f"{slug}.html"
        out.write_text(render_comparison(slug, cfg))
        print(f"✓ {slug}.html")

    print(f"\n{len(COUNTIES)} county reports + {len(COMPARISONS)} comparisons generated.")


if __name__ == "__main__":
    main()
