#!/usr/bin/env python3
"""Render and guard the evidence-led English town remediation batch."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "indexable-town-risk-decisions.json"
SITE = "https://thejorgeramirezgroup.com"
SHARE_IMAGE = f"{SITE}/images/hero.jpg"
SHARE_ALT = "Residential property image from The Jorge Ramirez Group website"
ORGANIZATION_ID = f"{SITE}/#organization"
PERSON_ID = f"{SITE}/#jorge-ramirez"
PAGE_MODIFIED_ON = "2026-08-27"
HREFLANG_LINE = re.compile(
    r"^[ \t]*<link\b[^>]*\bhreflang=[\"'][^\"']+[\"'][^>]*>[ \t]*\n?",
    re.I | re.M,
)
URL_BLOCK = re.compile(r"(?ms)^[ \t]*<url>\n.*?^[ \t]*</url>\n?")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from town_data import COUNTY  # noqa: E402
from tools.local_search_links import comparison_links, links_for_town  # noqa: E402


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, object]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    decisions = manifest.get("decisions")
    if not isinstance(decisions, dict) or len(decisions) != 44:
        raise RuntimeError(f"{path}: expected 44 managed decisions")
    actions = {"rebuild": 0, "redirect": 0, "quarantine": 0}
    for slug, decision in decisions.items():
        action = decision.get("action")
        if action not in actions:
            raise RuntimeError(f"{path}: invalid action for {slug}: {action}")
        actions[action] += 1
    if actions != {"rebuild": 12, "redirect": 2, "quarantine": 30}:
        raise RuntimeError(f"{path}: unexpected action counts: {actions}")
    provenance = manifest.get("provenancePolicy")
    expected_provenance = {
        "publisher": "The Jorge Ramirez Group",
        "declaration": "ai-assisted, source-checked",
        "sourceCheckedDate": "2026-08-26",
        "responsibleContact": "Jorge Ramirez",
        "njRealEstateLicense": "1754604",
        "structuredDataRule": (
            "The WebPage publisher is the Organization; Jorge Ramirez is a Person "
            "who works for that Organization and is not represented as the page author or reviewer."
        ),
    }
    if provenance != expected_provenance:
        raise RuntimeError(f"{path}: provenance policy mismatch")
    return manifest


def managed_slugs(manifest: dict[str, object] | None = None) -> set[str]:
    selected = manifest or load_manifest()
    return set(selected["decisions"])


def action_slugs(
    action: str, manifest: dict[str, object] | None = None
) -> set[str]:
    selected = manifest or load_manifest()
    return {
        slug
        for slug, decision in selected["decisions"].items()
        if decision["action"] == action
    }


def display_name(slug: str) -> str:
    names = {
        "basking-ridge": "Basking Ridge",
        "bernards-township": "Bernards Township",
        "boonton-township": "Boonton Township",
        "florham-park": "Florham Park",
        "glen-ridge": "Glen Ridge",
        "jersey-city": "Jersey City",
        "long-hill": "Long Hill",
        "middlesex-borough": "Middlesex Borough",
        "morris-township": "Morris Township",
        "new-brunswick": "New Brunswick",
        "north-caldwell": "North Caldwell",
        "parsippany-troy-hills": "Parsippany-Troy Hills",
        "peapack-gladstone": "Peapack-Gladstone",
        "perth-amboy": "Perth Amboy",
        "scotch-plains": "Scotch Plains",
        "short-hills": "Short Hills",
        "south-orange": "South Orange",
        "washington-township-morris": "Washington Township (Morris)",
        "west-orange": "West Orange",
    }
    return names.get(slug, " ".join(part.capitalize() for part in slug.split("-")))


def analytics() -> str:
    return '''  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>'''


def shared_head(
    *, title: str, description: str, canonical: str, robots: str
) -> str:
    escaped_title = html.escape(title)
    escaped_description = html.escape(description, quote=True)
    escaped_canonical = html.escape(canonical, quote=True)
    return f'''  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0A0A0A">
  <title>{escaped_title}</title>
  <meta name="description" content="{escaped_description}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{escaped_canonical}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="The Jorge Ramirez Group">
  <meta property="og:url" content="{escaped_canonical}">
  <meta property="og:title" content="{escaped_title}">
  <meta property="og:description" content="{escaped_description}">
  <meta property="og:image" content="{SHARE_IMAGE}">
  <meta property="og:image:width" content="1400">
  <meta property="og:image:height" content="933">
  <meta property="og:image:alt" content="{SHARE_ALT}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="{escaped_canonical}">
  <meta name="twitter:title" content="{escaped_title}">
  <meta name="twitter:description" content="{escaped_description}">
  <meta name="twitter:image" content="{SHARE_IMAGE}">
  <meta name="twitter:image:alt" content="{SHARE_ALT}">
{analytics()}
  <link rel="icon" href="/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">'''


def navigation() -> str:
    return '''  <a class="skip-link" href="#main">Skip to main content</a>
  <nav class="town-guide__nav" aria-label="Primary navigation">
    <div class="town-guide__nav-inner">
      <a class="town-guide__brand" href="/" aria-label="The Jorge Ramirez Group home">
        <picture>
          <source srcset="/images/jorge-logo.webp" type="image/webp">
          <img src="/images/jorge-logo.jpg" width="250" height="100" alt="The Jorge Ramirez Group">
        </picture>
      </a>
      <ul class="town-guide__nav-links">
        <li><a href="/buy-a-home">Buy</a></li>
        <li><a href="/sell-your-home">Sell</a></li>
        <li><a href="/communities">Communities</a></li>
        <li><a href="/contact">Contact Jorge</a></li>
      </ul>
    </div>
  </nav>'''


def render_guide(
    slug: str,
    decision: dict[str, object],
    provenance: dict[str, object],
) -> str:
    town = str(decision["displayName"])
    county = str(decision["county"])
    place_type = str(decision["placeType"])
    identity = str(decision["identity"])
    canonical = f"{SITE}/towns/{slug}"
    title = f"{town} NJ Real Estate Guide | Buyers & Sellers"
    description = (
        f"Research {town}, NJ real estate with official property sources, "
        "buyer and seller checklists, county context, and an address-specific value review."
    )
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
                "dateModified": PAGE_MODIFIED_ON,
                "about": {"@type": "Place", "name": town},
                "publisher": {"@id": ORGANIZATION_ID},
                "isPartOf": {
                    "@type": "WebSite",
                    "name": "The Jorge Ramirez Group",
                    "url": SITE + "/",
                },
            },
            {
                "@type": "Organization",
                "@id": ORGANIZATION_ID,
                "name": str(provenance["publisher"]),
                "url": SITE + "/",
                "telephone": "+1-908-230-7844",
                "email": "jorge.ramirez@kw.com",
            },
            {
                "@type": "Person",
                "@id": PERSON_ID,
                "name": str(provenance["responsibleContact"]),
                "url": SITE + "/ai-authority",
                "jobTitle": "New Jersey real estate salesperson",
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "New Jersey real estate salesperson license",
                    "value": str(provenance["njRealEstateLicense"]),
                },
                "worksFor": {"@id": ORGANIZATION_ID},
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
                "parentOrganization": {"@id": ORGANIZATION_ID},
                "telephone": "+1-908-230-7844",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "488 Springfield Avenue",
                    "addressLocality": "Summit",
                    "addressRegion": "NJ",
                    "postalCode": "07901",
                    "addressCountry": "US",
                },
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": 40.7157,
                    "longitude": -74.3601,
                },
                "areaServed": {"@type": "Place", "name": town},
            },
        ],
    }
    focus = "\n".join(
        f"          <li>{html.escape(str(item))}</li>"
        for item in decision["researchFocus"]
    )
    sources = []
    for item in decision["sources"]:
        sources.append(
            f'''          <article class="town-guide__source-card">
            <p class="town-guide__source-type">{html.escape(str(item["category"]))}</p>
            <h3>{html.escape(str(item["publisher"]))}</h3>
            <p>{html.escape(str(item["fact_supported"]))}</p>
            <a href="{html.escape(str(item["url"]), quote=True)}" rel="noopener">Open official source</a>
          </article>'''
        )
    source_markup = "\n".join(sources)
    related = links_for_town(slug)
    related_markup = ""
    if related:
        related_items = "".join(
            f'<li><a href="{html.escape(item["route"], quote=True)}">{html.escape(item["label"])}</a></li>'
            for item in related
        )
        related_markup = f'''
        <section class="town-guide__section" aria-labelledby="related-heading">
          <p class="town-guide__eyebrow">Related local research</p>
          <h2 id="related-heading">Compare {html.escape(town)} with the same address-first method</h2>
          <p>These comparisons apply the same public-record checklist to both places. They do not rank communities or replace a property-specific review.</p>
          <ul class="town-guide__checklist">{related_items}</ul>
        </section>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{shared_head(title=title, description=description, canonical=canonical, robots="index, follow, max-image-preview:large")}
  <meta name="ai-content-declaration" content="{html.escape(str(provenance['declaration']), quote=True)}">
  <meta name="llm-context" content="Official-source {html.escape(town, quote=True)} property research guide. It identifies the correct municipality and links directly to public records without price, travel-duration, rating, or outcome claims.">
  <link rel="stylesheet" href="/css/town-evidence-guide.css">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body class="town-evidence-guide" data-town-evidence-guide="v1">
{navigation()}
  <main id="main" tabindex="-1">
    <section class="town-guide__hero" aria-labelledby="page-title">
      <div class="town-guide__hero-inner">
        <p class="town-guide__eyebrow">{html.escape(county)} County · Official-source planning</p>
        <h1 id="page-title">{html.escape(town)} real estate guide for buyers and sellers</h1>
        <p class="town-guide__lede">Research the municipality, parcel, land-use records, public data, current comparable properties, and transaction questions tied to one address before planning a purchase or sale.</p>
      </div>
    </section>

    <div class="town-guide__layout">
      <article class="town-guide__article">
        <section class="town-guide__section" aria-labelledby="identity-heading">
          <p class="town-guide__eyebrow">Identity first</p>
          <h2 id="identity-heading">Confirm the public-record geography</h2>
          <div class="town-guide__notice">
            <p><strong>Place type:</strong> {html.escape(place_type)}.</p>
            <p>{html.escape(identity)}</p>
          </div>
        </section>

        <section class="town-guide__section" aria-labelledby="checks-heading">
          <p class="town-guide__eyebrow">Address-level review</p>
          <h2 id="checks-heading">Checks to run before relying on a comparison</h2>
          <p>A town-wide summary cannot determine a parcel's condition, legal use, taxes, title, insurance terms, association obligations, transportation plan, or transaction result. Enter the exact address in the relevant official tools and confirm time-sensitive details with the responsible agency or qualified professional.</p>
          <ul class="town-guide__checklist">
{focus}
          </ul>
        </section>

        <section class="town-guide__section" aria-labelledby="sources-heading">
          <p class="town-guide__eyebrow">Sources accessed August 26, 2026</p>
          <h2 id="sources-heading">Open the primary public sources</h2>
          <p>These links go to government, Census, or public transportation sources. Their records and schedules can change, so confirm the applicable date, parcel, filing, and service before making a housing decision.</p>
          <div class="town-guide__sources">
{source_markup}
          </div>
        </section>

        <section class="town-guide__section" aria-labelledby="worksheet-heading">
          <p class="town-guide__eyebrow">Comparison worksheet</p>
          <h2 id="worksheet-heading">Keep the decision tied to your own criteria</h2>
          <p>For each address, record the municipality, block and lot, property type, current tax record, zoning district, permit history, disclosures, association documents when applicable, insurance questions, and the date-specific transportation plan you tested. Apply the same checklist to every property you compare.</p>
        </section>
{related_markup}
        <aside class="town-guide__notice" data-content-provenance="v1" aria-label="Content provenance">
          <p><strong>Published by {html.escape(str(provenance["publisher"]))}.</strong> AI-assisted, source-checked August 26, 2026. Jorge Ramirez is a New Jersey real estate salesperson (license #{html.escape(str(provenance["njRealEstateLicense"]))}). <a href="/contact">Contact Jorge or request a correction.</a></p>
        </aside>
      </article>

      <aside class="town-guide__aside" aria-labelledby="method-heading">
        <h2 id="method-heading">How this guide is framed</h2>
        <p>It does not rank places or predict a price, schedule, school result, neighborhood condition, investment return, or transaction outcome.</p>
        <p>Property and travel details are user-entered and date-specific. Confirm them independently.</p>
        <a href="/counties/{county.lower()}-county">View the {html.escape(county)} County guide</a>
        <a href="/towns">Browse all maintained town guides</a>
      </aside>
    </div>

    <section class="town-guide__cta" aria-labelledby="contact-heading">
      <div class="town-guide__cta-inner">
        <h2 id="contact-heading">Planning a {html.escape(town)} purchase or sale?</h2>
        <p>Start with the property address, then choose the research or transaction path that matches your next decision.</p>
        <div class="town-guide__actions"><a class="town-guide__button" href="/buy-a-home">Plan a home search</a><a class="town-guide__button" href="/sell-your-home">Review the selling process</a><a class="town-guide__button" href="/home-valuation">Request a home value review</a><a class="town-guide__button" href="/contact">Contact Jorge</a></div>
      </div>
    </section>
  </main>

  <footer class="town-guide__footer">
    <p>The Jorge Ramirez Group · Keller Williams Premier Properties</p>
    <p><a href="/">Home</a> · <a href="/privacy-policy">Privacy Policy</a></p>
  </footer>
</body>
</html>
'''


def render_fallback(slug: str) -> str:
    town = display_name(slug)
    county = COUNTY[slug]
    canonical = f"{SITE}/towns/{slug}"
    county_href = f"/counties/{county.lower()}-county"
    title = f"{town}, NJ Guide Review | Jorge Ramirez"
    description = (
        f"The earlier {town} page is under editorial review. Use the {county} "
        "County guide or contact Jorge Ramirez for property-specific information."
    )
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{shared_head(title=title, description=description, canonical=canonical, robots="noindex, follow")}
  <link rel="stylesheet" href="/css/town-fallback.css">
</head>
<body class="town-fallback" data-noindex-town-fallback="v1" data-indexable-risk-fallback="v1">
  <a href="#main" class="skip-link">Skip to main content</a>
  <nav class="town-fallback__nav" aria-label="Primary">
    <div class="town-fallback__nav-inner">
      <a class="town-fallback__brand" href="/" aria-label="The Jorge Ramirez Group home">
        <picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" width="250" height="100" alt="The Jorge Ramirez Group"></picture>
      </a>
      <ul class="town-fallback__nav-links"><li><a href="/communities">Communities</a></li><li><a href="/contact">Contact Jorge</a></li></ul>
    </div>
  </nav>
  <main id="main" tabindex="-1">
    <section class="town-fallback__hero" aria-labelledby="page-title">
      <div class="town-fallback__hero-inner">
        <p class="town-fallback__eyebrow">Guide status</p>
        <h1 id="page-title">A focused {html.escape(town)} guide is in review</h1>
        <p class="town-fallback__lede">The previous long-form page has been retired because its local details were not sufficiently verified. This URL remains available while a concise, source-backed replacement is reviewed.</p>
      </div>
    </section>
    <section class="town-fallback__content" aria-labelledby="next-step-title">
      <article class="town-fallback__card">
        <h2 id="next-step-title">Start with the regional guide</h2>
        <p>Use the {html.escape(county)} County guide for regional context currently available on this site. If your question concerns a particular home, sale, purchase, or move, contact Jorge with the address and the information you want checked. Property-specific guidance should be based on current records, current listing information when available, and the facts you provide.</p>
        <div class="town-fallback__actions">
          <a class="town-fallback__button town-fallback__button--primary" href="{county_href}">View the {html.escape(county)} County guide</a>
          <a class="town-fallback__button town-fallback__button--secondary" href="/contact">Contact Jorge</a>
        </div>
        <p class="town-fallback__note">This fallback is intentionally excluded from search sitemaps. It publishes no town-specific figures or outcome promises while the full guide is under review.</p>
      </article>
    </section>
  </main>
  <footer class="town-fallback__footer"><p>The Jorge Ramirez Group · Keller Williams Premier Properties</p><p><a href="/">Home</a> · <a href="/privacy-policy">Privacy Policy</a></p></footer>
</body>
</html>
'''


def render_redirect_stub(
    slug: str, destination: str, *, language: str = "en"
) -> str:
    town = display_name(slug)
    canonical = SITE + destination
    if language == "es":
        destination_slug = destination.rstrip("/").split("/")[-1]
        destination_name = {
            "basking-ridge": "Basking Ridge",
            "millburn": "Millburn Township",
        }.get(destination_slug, display_name(destination_slug))
        title = f"Página trasladada a {destination_name} | The Jorge Ramirez Group"
        description = (
            f"La ruta de {town} se consolidó en la guía de {destination_name}."
        )
        heading = "Esta página se trasladó"
        message = f"Continúa a la guía consolidada de {destination_name}."
        action = "Abrir la guía"
        lang = "es-US"
        marker = "data-spanish-town-redirect=\"v1\""
        skip_link = '  <a href="#main" class="skip-link">Saltar al contenido principal</a>\n'
        theme_meta = '  <meta name="theme-color" content="#0A0A0A">\n'
    else:
        title = "Page moved | The Jorge Ramirez Group"
        description = ""
        heading = "This page has moved"
        message = "Continue to the consolidated guide for this location."
        action = "Continue to the guide"
        lang = "en"
        marker = 'data-town-relationship-redirect="v1"'
        skip_link = ""
        theme_meta = ""
    description_meta = (
        f'  <meta name="description" content="{html.escape(description, quote=True)}">\n'
        if description
        else ""
    )
    action_anchor = (
        f'<a class="town-fallback__button town-fallback__button--primary" '
        f'href="{html.escape(destination, quote=True)}">{html.escape(action)}</a>'
    )
    action_markup = (
        f'<div class="town-fallback__actions">{action_anchor}</div>'
        if language == "es"
        else action_anchor
    )
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
{theme_meta}  <meta name="robots" content="noindex, follow">
  <meta http-equiv="refresh" content="0; url={html.escape(destination, quote=True)}">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <title>{html.escape(title)}</title>
{description_meta}  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/town-fallback.css">
  <script>window.location.replace({json.dumps(destination)});</script>
</head>
<body class="town-fallback" {marker}>
{skip_link}  <main id="main" tabindex="-1" class="town-fallback__content">
    <article class="town-fallback__card">
      <p class="town-fallback__eyebrow">{html.escape(town)}</p>
      <h1>{html.escape(heading)}</h1>
      <p>{html.escape(message)}</p>
      {action_markup}
    </article>
  </main>
</body>
</html>
'''


def expected_page(slug: str, manifest: dict[str, object]) -> str:
    decision = manifest["decisions"][slug]
    if decision["action"] == "rebuild":
        return render_guide(slug, decision, manifest["provenancePolicy"])
    if decision["action"] == "redirect":
        return render_redirect_stub(slug, str(decision["destination"]))
    return render_fallback(slug)


def render_pages(
    *, root: Path = ROOT, manifest_path: Path = MANIFEST_PATH
) -> list[Path]:
    manifest = load_manifest(manifest_path)
    changed: list[Path] = []
    for slug in sorted(managed_slugs(manifest)):
        path = root / "towns" / f"{slug}.html"
        expected = expected_page(slug, manifest)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == expected:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        changed.append(path)
    return changed


def check_pages(
    *, root: Path = ROOT, manifest_path: Path = MANIFEST_PATH
) -> list[Path]:
    manifest = load_manifest(manifest_path)
    mismatches: list[Path] = []
    for slug in sorted(managed_slugs(manifest)):
        path = root / "towns" / f"{slug}.html"
        if not path.exists() or path.read_text(encoding="utf-8") != expected_page(
            slug, manifest
        ):
            mismatches.append(path)
    return mismatches


def update_sitemap(path: Path, removed_urls: set[str]) -> bool:
    source = path.read_text(encoding="utf-8")

    def keep(match: re.Match[str]) -> str:
        block = match.group(0)
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        return "" if loc and loc.group(1) in removed_urls else block

    updated = URL_BLOCK.sub(keep, source)
    if updated == source:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def strip_sitemap_alternates(path: Path, locs: set[str]) -> bool:
    """Remove stale translation signals while preserving standalone URLs."""

    source = path.read_text(encoding="utf-8")

    def replace(block_match: re.Match[str]) -> str:
        block = block_match.group(0)
        loc_match = re.search(r"<loc>([^<]+)</loc>", block)
        if not loc_match or loc_match.group(1) not in locs:
            return block
        return re.sub(
            r'^[ \t]*<xhtml:link\b[^>]*?/?>[ \t]*\n?', "", block, flags=re.I | re.M
        )

    updated = URL_BLOCK.sub(replace, source)
    if updated == source:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def update_site_facts(manifest: dict[str, object]) -> bool:
    path = ROOT / "data" / "site-facts.json"
    facts = json.loads(path.read_text(encoding="utf-8"))
    before = json.dumps(facts, sort_keys=True)
    removed = action_slugs("quarantine", manifest) | action_slugs("redirect", manifest)
    inventory = facts["canonicalTownInventory"]
    for county, slugs in inventory["byCounty"].items():
        inventory["byCounty"][county] = [slug for slug in slugs if slug not in removed]
    inventory["total"] = sum(len(slugs) for slugs in inventory["byCounty"].values())
    inventory["definition"] = (
        "Unique indexable English /towns/ URLs included in sitemap.xml and the canonical communities hubs. Noindex fallbacks and relationship redirects are excluded."
    )
    entry = {
        "scope": "indexable-english-town-risk-remediation",
        "languages": ["en"],
        "manifest": "data/indexable-town-risk-decisions.json",
        "slugs": sorted(managed_slugs(manifest)),
        "reason": "Layer-aware audit found fair-housing or unsupported factual risk in the remaining legacy English town pages.",
        "searchHandling": "measured-demand routes rebuilt; duplicate geographies redirected; low-value routes use compact noindex, follow fallbacks",
        "reviewStatus": "managed-renderer-live",
        "renderer": "scripts/remediate_indexable_towns.py",
    }
    facts["editorialQuarantine"] = [
        item
        for item in facts["editorialQuarantine"]
        if item.get("scope") != entry["scope"]
    ] + [entry]
    after = json.dumps(facts, sort_keys=True)
    if after == before:
        return False
    path.write_text(
        json.dumps(facts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return True


def strip_spanish_hreflang(manifest: dict[str, object]) -> list[Path]:
    changed: list[Path] = []
    for slug, decision in manifest["decisions"].items():
        path = ROOT / "es" / "towns" / f"{slug}.html"
        if decision["action"] == "redirect":
            destination = "/es" + str(decision["destination"])
            updated = render_redirect_stub(slug, destination, language="es")
        else:
            source = path.read_text(encoding="utf-8")
            updated = HREFLANG_LINE.sub("", source)
        current = path.read_text(encoding="utf-8")
        if current == updated:
            continue
        path.write_text(updated, encoding="utf-8")
        changed.append(path)
    return changed


def alias_redirects(manifest: dict[str, object]) -> dict[str, str]:
    mappings: dict[str, str] = {}
    for slug in sorted(action_slugs("redirect", manifest)):
        destination = str(manifest["decisions"][slug]["destination"])
        target_slug = destination.removeprefix("/towns/")
        mappings.update(
            {
                f"/towns/{slug}": destination,
                f"/towns/{slug}.html": destination,
                f"/es/towns/{slug}": f"/es/towns/{target_slug}",
                f"/es/towns/{slug}.html": f"/es/towns/{target_slug}",
                f"/realtor/{slug}-nj": destination,
                f"/realtor/{slug}-nj.html": destination,
                f"/communities/{slug}": destination,
                f"/communities/{slug}.html": destination,
            }
        )
    return mappings


def update_vercel(manifest: dict[str, object]) -> bool:
    path = ROOT / "vercel.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    redirects = config["redirects"]
    mappings = alias_redirects(manifest)
    seen: set[str] = set()
    for item in redirects:
        source = str(item.get("source", ""))
        if source not in mappings:
            continue
        item["destination"] = mappings[source]
        item["permanent"] = True
        seen.add(source)
    additions = [
        {"source": source, "destination": destination, "permanent": True}
        for source, destination in mappings.items()
        if source not in seen
    ]
    # Keep every existing redirect in its original order. Exact alias rules need
    # only precede the path wildcards; inserting after the initial host redirect
    # preserves unrelated conditional routing maintained by other batches.
    insertion_index = 0
    while insertion_index < len(redirects) and redirects[insertion_index].get("has"):
        insertion_index += 1
    updated_redirects = (
        redirects[:insertion_index] + additions + redirects[insertion_index:]
    )
    for source in mappings:
        if sum(str(item.get("source")) == source for item in updated_redirects) != 1:
            raise RuntimeError(f"vercel alias redirect is not unique: {source}")
    for destination in mappings.values():
        if destination in mappings:
            raise RuntimeError(f"alias redirect would chain through {destination}")
    config["redirects"] = updated_redirects
    updated = json.dumps(config, indent=2) + "\n"
    current = path.read_text(encoding="utf-8")
    if current == updated:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def update_community_alias_stubs(manifest: dict[str, object]) -> list[Path]:
    changed: list[Path] = []
    for slug in sorted(action_slugs("redirect", manifest)):
        destination = str(manifest["decisions"][slug]["destination"])
        path = ROOT / "communities" / slug / "index.html"
        updated = render_redirect_stub(slug, destination)
        if path.read_text(encoding="utf-8") == updated:
            continue
        path.write_text(updated, encoding="utf-8")
        changed.append(path)
    return changed


def render_towns_index() -> str:
    facts = json.loads((ROOT / "data" / "site-facts.json").read_text(encoding="utf-8"))
    inventory = facts["canonicalTownInventory"]
    canonical = f"{SITE}/towns"
    title = "NJ Real Estate Town Guides & Comparisons | Jorge Ramirez"
    description = (
        f"Browse {inventory['total']} maintained NJ real estate town guides, six county hubs, "
        "and official-source comparisons for buyers and sellers planning a move."
    )
    cards: list[str] = []
    schema_items: list[dict[str, object]] = []
    position = 0
    for county, slugs in inventory["byCounty"].items():
        links = []
        for slug in slugs:
            position += 1
            name = display_name(slug)
            links.append(f'<li><a href="/towns/{slug}">{html.escape(name)}</a></li>')
            schema_items.append(
                {
                    "@type": "ListItem",
                    "position": position,
                    "name": name,
                    "url": f"{SITE}/towns/{slug}",
                }
            )
        cards.append(
            f'''        <section class="town-guide__source-card" aria-labelledby="{county.lower()}-heading">
          <h2 id="{county.lower()}-heading">{html.escape(county)} County</h2>
          <ul class="town-guide__checklist">{''.join(links)}</ul>
          <p><a href="/counties/{county.lower()}-county">Open the {html.escape(county)} County real estate guide</a></p>
        </section>'''
        )
    comparison_cards = "".join(
        f'''        <article class="town-guide__source-card"><h3>{html.escape(item["label"])}</h3><p>Compare municipal identity, public records, transit research, and address-level questions without ranking either place.</p><a href="{html.escape(item["route"], quote=True)}">Open the official-record comparison</a></article>'''
        for item in comparison_links()
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "url": canonical,
        "mainEntity": {"@type": "ItemList", "itemListElement": schema_items},
    }
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{shared_head(title=title, description=description, canonical=canonical, robots="index, follow, max-image-preview:large")}
  <meta name="llm-context" content="Maintained index of English New Jersey real estate guides and official-record town comparisons across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties. Only indexable canonical town routes are listed.">
  <link rel="stylesheet" href="/css/town-evidence-guide.css">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body class="town-evidence-guide">
{navigation()}
  <main id="main" tabindex="-1">
    <section class="town-guide__hero" aria-labelledby="page-title"><div class="town-guide__hero-inner"><p class="town-guide__eyebrow">Six-county real estate directory</p><h1 id="page-title">New Jersey real estate town guides and comparisons</h1><p class="town-guide__lede">Explore {inventory['total']} maintained town guides across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties. Each guide starts with official records and then connects buyers and sellers to an address-specific next step.</p></div></section>
    <div class="town-guide__layout"><article class="town-guide__article">
      <section class="town-guide__section" aria-labelledby="directory-method"><p class="town-guide__eyebrow">Choose the right research layer</p><h2 id="directory-method">Start broad, then narrow to the property</h2><p>Use a county guide to understand the responsible regional sources, a town guide to identify municipal record offices and local transportation resources, and a comparison guide to apply the same questions to two places. None of those layers can establish the condition, legal use, current value, insurance terms, or transaction result for one home.</p><p>For a purchase, compare the exact property type, parcel records, condition, current alternatives, and travel plan. For a sale, combine current comparable properties with the home's updates, constraints, presentation, access, and timing. Recheck every time-sensitive source before acting.</p></section>
      <div class="town-guide__sources">{''.join(cards)}</div>
      <section class="town-guide__section" aria-labelledby="comparison-directory"><p class="town-guide__eyebrow">Related town research</p><h2 id="comparison-directory">Official-record New Jersey town comparisons</h2><p>These guides answer common town-versus-town searches with municipal identity, public records, transit tools, and a repeatable address worksheet. They avoid community rankings, protected-characteristic targeting, school reputation, safety labels, and outcome promises.</p><div class="town-guide__sources">{comparison_cards}</div></section>
      <section class="town-guide__section" aria-labelledby="decision-path"><p class="town-guide__eyebrow">Your next step</p><h2 id="decision-path">Turn the guide into a property decision</h2><p>Open the <a href="/buy-a-home">buyer planning guide</a> when you are comparing active options. Review the <a href="/sell-your-home">seller process</a> when preparing a listing, or request a <a href="/home-valuation">property-specific home value review</a> based on current comparable evidence. Keep broad market research separate from advice about one address.</p></section>
    </article><aside class="town-guide__aside"><h2>Need a regional starting point?</h2><p>The county guides organize broader research without treating every property in a municipality as interchangeable.</p><a href="/counties">Browse all six county guides</a><a href="/communities">Open the communities directory</a></aside></div>
    <section class="town-guide__cta"><div class="town-guide__cta-inner"><h2>Have a particular address in mind?</h2><p>Choose a buyer, seller, or valuation path and keep every conclusion tied to current property evidence.</p><div class="town-guide__actions"><a class="town-guide__button" href="/buy-a-home">Plan a home search</a><a class="town-guide__button" href="/sell-your-home">Plan a sale</a><a class="town-guide__button" href="/home-valuation">Request a value review</a><a class="town-guide__button" href="/contact">Contact Jorge</a></div></div></section>
  </main>
  <footer class="town-guide__footer"><p>The Jorge Ramirez Group · Keller Williams Premier Properties</p><p><a href="/">Home</a> · <a href="/privacy-policy">Privacy Policy</a></p></footer>
</body>
</html>
'''


def write_if_changed(path: Path, expected: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == expected:
        return False
    path.write_text(expected, encoding="utf-8")
    return True


def apply_shared_inventory(manifest: dict[str, object]) -> list[Path]:
    changed: list[Path] = []
    nonindex = action_slugs("quarantine", manifest) | action_slugs("redirect", manifest)
    if update_sitemap(
        ROOT / "sitemap.xml", {f"{SITE}/towns/{slug}" for slug in nonindex}
    ):
        changed.append(ROOT / "sitemap.xml")
    if update_sitemap(
        ROOT / "sitemap-es.xml",
        {f"{SITE}/es/towns/{slug}" for slug in action_slugs("redirect", manifest)},
    ):
        changed.append(ROOT / "sitemap-es.xml")
    if strip_sitemap_alternates(
        ROOT / "sitemap.xml",
        {f"{SITE}/towns/{slug}" for slug in action_slugs("rebuild", manifest)},
    ):
        changed.append(ROOT / "sitemap.xml")
    if strip_sitemap_alternates(
        ROOT / "sitemap-es.xml",
        {f"{SITE}/es/towns/{slug}" for slug in managed_slugs(manifest)},
    ):
        changed.append(ROOT / "sitemap-es.xml")
    if update_site_facts(manifest):
        changed.append(ROOT / "data" / "site-facts.json")
    changed.extend(strip_spanish_hreflang(manifest))
    if update_vercel(manifest):
        changed.append(ROOT / "vercel.json")
    changed.extend(update_community_alias_stubs(manifest))
    hub_paths = (
        ROOT / "communities.html",
        ROOT / "communities" / "index.html",
        ROOT / "es" / "communities.html",
        ROOT / "es" / "communities" / "index.html",
    )
    hub_before = {path: path.read_bytes() for path in hub_paths}
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_communities_from_facts.py")],
        cwd=ROOT,
        check=True,
    )
    changed.extend(path for path in hub_paths if path.read_bytes() != hub_before[path])
    if write_if_changed(ROOT / "towns" / "index.html", render_towns_index()):
        changed.append(ROOT / "towns" / "index.html")
    return changed


def inventory_issues(manifest: dict[str, object]) -> list[str]:
    issues: list[str] = []
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_es = (ROOT / "sitemap-es.xml").read_text(encoding="utf-8")
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    redirects = {str(item.get("source")): str(item.get("destination")) for item in config["redirects"]}
    for slug, decision in manifest["decisions"].items():
        url = f"{SITE}/towns/{slug}"
        if decision["action"] == "rebuild" and f"<loc>{url}</loc>" not in sitemap:
            issues.append(f"sitemap missing rebuild: {slug}")
        if decision["action"] != "rebuild" and f"<loc>{url}</loc>" in sitemap:
            issues.append(f"sitemap retains noncanonical route: {slug}")
        spanish = (ROOT / "es" / "towns" / f"{slug}.html").read_text(encoding="utf-8")
        if re.search(r'<link\b[^>]*hreflang=', spanish, re.I):
            issues.append(f"Spanish route retains stale hreflang: {slug}")
        if decision["action"] == "redirect":
            es_url = f"{SITE}/es/towns/{slug}"
            if f"<loc>{es_url}</loc>" in sitemap_es:
                issues.append(f"Spanish redirect remains submitted: {slug}")
        if re.search(
            rf'<xhtml:link\b[^>]*href=["\']{re.escape(url)}["\']',
            sitemap + sitemap_es,
            re.I,
        ):
            issues.append(f"stale sitemap hreflang remains: {slug}")
    for source, destination in alias_redirects(manifest).items():
        if redirects.get(source) != destination:
            issues.append(f"redirect mismatch: {source}")
        if destination in redirects:
            issues.append(f"redirect chain: {source} -> {destination}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report renderer or inventory drift")
    args = parser.parse_args()
    manifest = load_manifest()
    if args.check:
        mismatches = check_pages()
        issues = inventory_issues(manifest)
        for path in mismatches:
            print(f"page drift: {path.relative_to(ROOT)}", file=sys.stderr)
        for issue in issues:
            print(issue, file=sys.stderr)
        if mismatches or issues:
            return 1
        print("town remediation check passed: 44 routes and shared inventory")
        return 0

    page_changes = render_pages()
    inventory_changes = apply_shared_inventory(manifest)
    print(
        f"rendered {len(page_changes)} managed page changes; "
        f"updated {len(set(inventory_changes))} inventory/language files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
