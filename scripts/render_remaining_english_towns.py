#!/usr/bin/env python3
"""Render four retained English town pages as neutral public-source guides."""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "remaining-english-town-guides.json"
SITE = "https://thejorgeramirezgroup.com"
BUSINESS_ID = f"{SITE}/#agent"
PERSON_ID = f"{SITE}/#jorge-ramirez"
ZILLOW_PROFILE = "https://www.zillow.com/profile/TheJorgeRamirezGroup"
PERSON_PROFILE_URLS = [
    ZILLOW_PROFILE,
    "https://www.linkedin.com/in/jorge-ramirez-37034025/",
    "https://thejorgeramirezgroup.kw.com/agent/Jorge-Ramirez/520237",
]
BUSINESS_PROFILE_URLS = [
    "https://www.facebook.com/thejorgeramirezgroup",
    "https://www.instagram.com/jorgesellsnjhomes",
    "https://www.google.com/maps?cid=4574397105419981752",
]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.local_search_links import links_for_town  # noqa: E402


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def source_card(category: str, label: str, url: str, purpose: str, limit: str) -> str:
    return f'''          <article class="town-guide__source-card">
            <p class="town-guide__source-type">{esc(category)}</p>
            <h3>{esc(label)}</h3>
            <p><strong>Use:</strong> {esc(purpose)}</p>
            <p><strong>Limit:</strong> {esc(limit)}</p>
            <a href="{esc(url)}" rel="noopener">Open official source</a>
          </article>'''


def render_legacy(slug: str, page: dict, shared: list[dict], reviewed: str) -> str:
    town = page["display_name"]
    county = page["county"]
    canonical = f"{SITE}/towns/{slug}"
    spanish = f"{SITE}/es/towns/{slug}"
    title = f"{town} NJ Real Estate Guide | Buyers & Sellers"
    description = f"Research {town}, NJ real estate with direct property sources, buyer and seller planning, county context, and an address-specific home value review."
    sources = [
        source_card(
            "Municipal government",
            page["municipal_label"],
            page["municipal_url"],
            "Locate the responsible municipal departments, current notices, and public-record request resources.",
            "A municipal directory identifies record keepers; it does not establish a property's condition, value, or legal use.",
        ),
        source_card(
            "Property records",
            page["record_label"],
            page["record_url"],
            "Start the address-level search for assessment, land-use, permit, code, or related public information available from the responsible office.",
            "Availability and scope vary by office. Confirm the exact parcel and request the current record directly.",
        ),
    ]
    sources.extend(source_card(item["category"], item["label"], item["url"], item["purpose"], item["limit"]) for item in shared)
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "inLanguage": "en-US",
                "dateModified": reviewed,
                "about": {"@type": "Place", "name": f"{town}, New Jersey"},
                "author": {"@id": f"{SITE}/#jorge-ramirez"},
                "isPartOf": {"@id": f"{SITE}/#website"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Communities", "item": SITE + "/communities"},
                    {"@type": "ListItem", "position": 3, "name": town, "item": canonical},
                ],
            },
        ],
    }
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    related = links_for_town(slug)
    related_markup = ""
    if related:
        related_items = "".join(
            f'<li><a href="{esc(item["route"])}">{esc(item["label"])}</a></li>'
            for item in related
        )
        related_markup = f'''      <section class="town-guide__section" aria-labelledby="related-heading"><p class="town-guide__eyebrow">Related local research</p><h2 id="related-heading">Compare {esc(town)} with the same address-first method</h2><p>Use the same municipal, property-record, transportation, and personal-criteria worksheet for both places. The comparison does not rank communities.</p><ul class="town-guide__checklist">{related_items}</ul></section>'''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="author" content="Jorge Ramirez">
  <meta name="llm-context" content="Official-source property research guide for {esc(town)}. It distinguishes municipal context from address-level records and makes no price, timing, school, safety, or transaction-outcome claim.">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="en-US" href="{canonical}">
  <link rel="alternate" hreflang="es-US" href="{spanish}">
  <link rel="alternate" hreflang="es" href="{spanish}">
  <link rel="alternate" hreflang="x-default" href="{canonical}">
  <meta property="og:type" content="website"><meta property="og:site_name" content="The Jorge Ramirez Group"><meta property="og:locale" content="en_US"><meta property="og:url" content="{canonical}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:image" content="{SITE}/images/hero.jpg"><meta property="og:image:alt" content="Residential property image from The Jorge Ramirez Group website">
  <meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
  <link rel="icon" href="/favicon.ico"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet"><link rel="stylesheet" href="/css/styles.css"><link rel="stylesheet" href="/css/town-evidence-guide.css">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body class="town-evidence-guide" data-town-evidence-guide="retained-v1" data-source-review="{reviewed}">
  <a class="skip-link" href="#main">Skip to main content</a>
  <nav class="town-guide__nav" aria-label="Primary navigation"><div class="town-guide__nav-inner"><a class="town-guide__brand" href="/" aria-label="The Jorge Ramirez Group home"><picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" width="250" height="100" alt="The Jorge Ramirez Group"></picture></a><ul class="town-guide__nav-links"><li><a href="/buy-a-home">Buy</a></li><li><a href="/sell-your-home">Sell</a></li><li><a href="/communities">Communities</a></li><li><a href="{spanish.replace(SITE, '')}" hreflang="es-US">Español</a></li><li><a href="/contact">Contact Jorge</a></li></ul></div></nav>
  <main id="main" tabindex="-1">
    <section class="town-guide__hero" aria-labelledby="page-title"><div class="town-guide__hero-inner"><p class="town-guide__eyebrow">{esc(county)} County · official-source property research</p><h1 id="page-title">{esc(town)} real estate guide for buyers and sellers</h1><p class="town-guide__lede">Confirm the municipality, parcel, land-use records, education sources, flood-disclosure resources, current comparable properties, and a date-specific transportation plan tied to one address.</p></div></section>
    <div class="town-guide__layout"><article class="town-guide__article">
      <section class="town-guide__section" aria-labelledby="identity-heading"><p class="town-guide__eyebrow">Public-record identity first</p><h2 id="identity-heading">Confirm which office maintains the parcel</h2><div class="town-guide__notice"><p>{esc(page["identity"])}</p></div><p>Postal names, municipal boundaries, school assignments, transit labels, and market-report geographies answer different questions. Record the exact address and parcel identifiers before comparing information from different systems.</p></section>
      <section class="town-guide__section" aria-labelledby="checks-heading"><p class="town-guide__eyebrow">Address-level review</p><h2 id="checks-heading">Run the same checks for every property</h2><p>A community page cannot determine a parcel's physical condition, legal use, current tax bill, title, permit history, insurance terms, association obligations, school assignment, travel time, or transaction result.</p><ul class="town-guide__checklist"><li>Confirm the legal municipality, address, block and lot, and property type.</li><li>Review the current assessment, tax record, land-use information, permits, and available public filings.</li><li>Check deed, survey, title, disclosures, and association documents when applicable with the responsible professional.</li><li>Search current state education reports, then confirm the address assignment directly with the district.</li><li>Test transportation using the real origin, destination, date, time, transfers, and current service notices.</li><li>Apply the same objective worksheet and questions to each property you consider.</li></ul></section>
      <section class="town-guide__section" aria-labelledby="sources-heading"><p class="town-guide__eyebrow">Sources reviewed August 26, 2026</p><h2 id="sources-heading">Open the primary public sources</h2><p>Use each source only for the job it actually performs. Records, assignments, schedules, and service conditions can change; reopen the original source for the address and date that matter.</p><div class="town-guide__sources">{"".join(sources)}</div></section>
      <section class="town-guide__section" aria-labelledby="method-heading"><p class="town-guide__eyebrow">Neutral method</p><h2 id="method-heading">Separate sourced facts from personal preferences</h2><p>For each address, record the source, access date, and result. Keep your personal criteria—such as property type, budget, accessibility, commute destinations, and proximity to specific services—in a separate column and apply them consistently.</p><p>This guide does not rank communities or predict price, travel duration, school results, neighborhood conditions, investment performance, or a transaction outcome. Request a current property analysis for any market figure.</p></section>
{related_markup}
    </article><aside class="town-guide__aside" aria-labelledby="aside-heading"><h2 id="aside-heading">Bring one address</h2><p>Have the full address, block and lot when available, property type, questions about records, and the date you need the information.</p><p>Keep every answer tied to that property and an identifiable source.</p><a href="/counties/{county.lower()}-county">View the {esc(county)} County guide</a></aside></div>
    <section class="town-guide__cta" aria-labelledby="contact-heading"><div class="town-guide__cta-inner"><h2 id="contact-heading">Planning a {esc(town)} purchase or sale?</h2><p>Start with the address, then choose the buyer, seller, or valuation path that matches your next decision.</p><div class="town-guide__actions"><a class="town-guide__button" href="/buy-a-home">Plan a home search</a><a class="town-guide__button" href="/sell-your-home">Review the selling process</a><a class="town-guide__button" href="/home-valuation">Request a home value review</a><a class="town-guide__button" href="/contact">Contact Jorge</a></div></div></section>
  </main>
  <footer class="town-guide__footer"><p>The Jorge Ramirez Group · Keller Williams Premier Properties · NJ License #1754604</p><p><a href="/">Home</a> · <a href="/privacy-policy">Privacy Policy</a></p></footer>
  <script defer src="/js/site-cta.js"></script><script defer src="/js/lead-attribution.js"></script>
</body></html>
'''


def reviewed_label(value: str) -> str:
    parsed = date.fromisoformat(value)
    return parsed.strftime("%B %d, %Y").replace(" 0", " ")


def render_quick_win(slug: str, page: dict, reviewed: str, modified: str) -> str:
    town = str(page["display_name"])
    county = str(page["county"])
    canonical = f"{SITE}/towns/{slug}"
    spanish = f"{SITE}/es/towns/{slug}"
    title = str(page["title"])
    description = str(page["description"])
    source_date = reviewed_label(reviewed)
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "inLanguage": "en-US",
                "dateModified": modified,
                "about": {"@type": "Place", "name": f"{town}, New Jersey"},
                "publisher": {"@id": BUSINESS_ID},
                "isPartOf": {"@id": f"{SITE}/#website"},
            },
            {
                "@type": "RealEstateAgent",
                "@id": BUSINESS_ID,
                "name": "The Jorge Ramirez Group",
                "url": SITE + "/",
                "telephone": "+1-908-230-7844",
                "email": "jorge.ramirez@kw.com",
                "image": SITE + "/images/jorge-ramirez-headshot.jpg",
                "sameAs": BUSINESS_PROFILE_URLS,
                "parentOrganization": {
                    "@type": "Organization",
                    "name": "Keller Williams Premier Properties",
                    "url": "https://www.kw.com",
                },
            },
            {
                "@type": "Person",
                "@id": PERSON_ID,
                "name": "Jorge Ramirez",
                "url": SITE + "/ai-authority",
                "jobTitle": "New Jersey real estate salesperson",
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "New Jersey real estate salesperson license",
                    "value": "1754604",
                },
                "worksFor": {"@id": BUSINESS_ID},
                "image": SITE + "/images/jorge-ramirez-headshot.jpg",
                "sameAs": PERSON_PROFILE_URLS,
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Communities", "item": SITE + "/communities"},
                    {"@type": "ListItem", "position": 3, "name": town, "item": canonical},
                ],
            },
            {
                "@type": "LocalBusiness",
                "@id": SITE + "/#summit-office",
                "name": "The Jorge Ramirez Group",
                "url": SITE + "/",
                "parentOrganization": {"@id": BUSINESS_ID},
                "telephone": "+1-908-230-7844",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "488 Springfield Avenue",
                    "addressLocality": "Summit",
                    "addressRegion": "NJ",
                    "postalCode": "07901",
                    "addressCountry": "US",
                },
                "areaServed": {"@type": "Place", "name": town},
            },
        ],
    }
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    identity_paragraphs = "".join(
        f"<p>{esc(paragraph)}</p>" for paragraph in page["identity_paragraphs"]
    )
    decision_cards = "".join(
        f'''          <article class="town-guide__source-card">
            <h3>{esc(card["title"])}</h3>
            <p>{esc(card["body"])}</p>
          </article>'''
        for card in page["decision_cards"]
    )
    seller_steps = "".join(
        f"<li>{esc(item)}</li>" for item in page["seller_steps"]
    )
    sources = "".join(
        source_card(
            item["category"],
            item["label"],
            item["url"],
            item["purpose"],
            item["limit"],
        )
        for item in page["sources"]
    )
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="ai-content-declaration" content="ai-assisted, source-checked">
  <meta name="llm-context" content="Official-source {esc(town)} property guide for buyer, seller, municipal-record, and address-specific valuation research without price, rating, commute-duration, or outcome claims.">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="en-US" href="{canonical}">
  <link rel="alternate" hreflang="es-US" href="{spanish}">
  <link rel="alternate" hreflang="es" href="{spanish}">
  <link rel="alternate" hreflang="x-default" href="{canonical}">
  <meta property="og:type" content="website"><meta property="og:site_name" content="The Jorge Ramirez Group"><meta property="og:locale" content="en_US"><meta property="og:url" content="{canonical}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:image" content="{SITE}/images/hero.jpg"><meta property="og:image:alt" content="Residential property image from The Jorge Ramirez Group website">
  <meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
  <link rel="icon" href="/favicon.ico"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet"><link rel="stylesheet" href="/css/styles.css"><link rel="stylesheet" href="/css/town-evidence-guide.css">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body class="town-evidence-guide" data-town-evidence-guide="quick-win-v2" data-source-review="{reviewed}">
  <a class="skip-link" href="#main">Skip to main content</a>
  <nav class="town-guide__nav" aria-label="Primary navigation"><div class="town-guide__nav-inner"><a class="town-guide__brand" href="/" aria-label="The Jorge Ramirez Group home"><picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" width="250" height="100" alt="The Jorge Ramirez Group"></picture></a><ul class="town-guide__nav-links"><li><a href="/buy-a-home">Buy</a></li><li><a href="/sell-your-home">Sell</a></li><li><a href="/communities">Communities</a></li><li><a href="{spanish.replace(SITE, '')}" hreflang="es-US">Español</a></li><li><a href="/contact">Contact Jorge</a></li></ul></div></nav>
  <main id="main" tabindex="-1">
    <section class="town-guide__hero" aria-labelledby="page-title"><div class="town-guide__hero-inner"><p class="town-guide__eyebrow">{esc(county)} County · official-source property research</p><h1 id="page-title">{esc(town)} NJ real estate guide for buyers and sellers</h1><p class="town-guide__lede">{esc(page["hero"])}</p></div></section>
    <div class="town-guide__layout"><article class="town-guide__article">
      <section class="town-guide__section" aria-labelledby="identity-heading"><p class="town-guide__eyebrow">Correct public-record geography</p><h2 id="identity-heading">{esc(page["identity_heading"])}</h2><div class="town-guide__notice">{identity_paragraphs}</div></section>
      <section class="town-guide__section" data-local-agent-trust="v1" aria-labelledby="local-agent-heading"><div class="town-guide__agent-card"><picture class="town-guide__agent-photo"><source srcset="/images/jorge-ramirez-headshot.webp" type="image/webp"><img src="/images/jorge-ramirez-headshot.jpg" width="955" height="1280" loading="lazy" alt="Jorge Ramirez, licensed New Jersey real estate agent"></picture><div class="town-guide__agent-copy"><p class="town-guide__eyebrow">Who stands behind this guide</p><h2 id="local-agent-heading">Work with Jorge on an address in {esc(town)}</h2><p><strong>Jorge Ramirez</strong> is a New Jersey real estate salesperson with Keller Williams Premier Properties and has worked full-time at Keller Williams since 2017. His office is at 488 Springfield Avenue in Summit, and his NJ license is #1754604.</p><p>Jorge can help organize the records to verify, review current listing and comparable-sale information when available, and clarify the next buyer or seller decision without promising a price or result.</p><ul class="town-guide__agent-proof" aria-label="Verified credentials"><li>Full-time at Keller Williams since 2017</li><li>NJ license #1754604</li><li>Buyer and seller service across six New Jersey counties</li></ul><div class="town-guide__agent-links"><a href="/ai-authority">Verify Jorge's credentials</a><a href="{ZILLOW_PROFILE}" target="_blank" rel="noopener">Open Jorge's Zillow profile</a></div></div></div></section>
      <section class="town-guide__section" aria-labelledby="decision-heading"><p class="town-guide__eyebrow">Town-specific property review</p><h2 id="decision-heading">{esc(page["decision_heading"])}</h2><p>{esc(page["decision_intro"])}</p><div class="town-guide__sources">{decision_cards}</div></section>
      <section class="town-guide__section" aria-labelledby="sources-heading"><p class="town-guide__eyebrow">Sources reviewed {source_date}</p><h2 id="sources-heading">Open the primary public sources</h2><p>Use each source only for the job it performs. Reopen the original record for the property and date that matter because offices, documents, assignments, schedules, and conditions can change.</p><div class="town-guide__sources">{sources}</div></section>
      <section class="town-guide__section" aria-labelledby="seller-heading"><p class="town-guide__eyebrow">Buyer and seller evidence</p><h2 id="seller-heading">{esc(page["seller_heading"])}</h2><p>{esc(page["seller_intro"])}</p><ul class="town-guide__checklist">{seller_steps}</ul></section>
      <aside class="town-guide__notice" data-content-provenance="v1" aria-label="Content provenance"><p><strong>Published by The Jorge Ramirez Group.</strong> AI-assisted, source-checked {source_date}. Jorge Ramirez is a New Jersey real estate salesperson (license #1754604). <a href="/contact">Contact Jorge or request a correction.</a></p></aside>
    </article><aside class="town-guide__aside" aria-labelledby="method-heading"><h2 id="method-heading">Keep every conclusion property-specific</h2><p>This guide does not rank communities or predict a price, school result, travel duration, neighborhood condition, investment return, or transaction outcome.</p><p>Confirm the parcel, effective date, and responsible source before relying on any record.</p><a href="/counties/{county.lower()}-county">View the {esc(county)} County guide</a><a href="/towns">Browse maintained town guides</a></aside></div>
    <section class="town-guide__cta" aria-labelledby="contact-heading"><div class="town-guide__cta-inner"><h2 id="contact-heading">{esc(page["cta_heading"])}</h2><p>{esc(page["cta_copy"])}</p><div class="town-guide__actions"><a class="town-guide__button" href="/buy-a-home">Plan a home search</a><a class="town-guide__button" href="/sell-your-home">Review the selling process</a><a class="town-guide__button" href="/home-valuation">Request a home value review</a><a class="town-guide__button" href="/contact">Contact Jorge</a></div></div></section>
  </main>
  <footer class="town-guide__footer"><p>The Jorge Ramirez Group · Keller Williams Premier Properties · NJ License #1754604</p><p><a href="/">Home</a> · <a href="/privacy-policy">Privacy Policy</a></p></footer>
  <script defer src="/js/site-cta.js"></script><script defer src="/js/lead-attribution.js"></script>
</body></html>
'''


def render(
    slug: str,
    page: dict,
    shared: list[dict],
    reviewed: str,
    modified: str,
) -> str:
    if page.get("content_version") == "quick-win-v2":
        return render_quick_win(slug, page, reviewed, modified)
    return render_legacy(slug, page, shared, reviewed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if set(data["pages"]) != {"middlesex", "woodbridge", "orange", "helmetta"}:
        raise RuntimeError("remaining town manifest must manage exactly four routes")
    stale = []
    for slug, page in data["pages"].items():
        target = ROOT / "towns" / f"{slug}.html"
        rendered = render(
            slug,
            page,
            data["shared_sources"],
            data["reviewed"],
            data["modified"],
        )
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != rendered:
                stale.append(target.relative_to(ROOT).as_posix())
        else:
            target.write_text(rendered, encoding="utf-8")
    if stale:
        print("Out-of-date retained town pages:", ", ".join(stale))
        return 1
    print("Retained English town pages are current." if args.check else "Rendered four retained English town pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
