#!/usr/bin/env python3
"""Retire unsafe scaled Spanish town articles as deterministic fallbacks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
INVENTORY = ROOT / "data" / "spanish-fair-housing-inventory.json"
MANIFEST = ROOT / "data" / "spanish-fair-housing-quarantine.json"
GSC_FIXTURE = ROOT / "tests" / "fixtures" / "gsc-spanish-fair-housing-quarantine-pages.csv"
GSC_EXPORT = Path("/Users/teddy/Documents/Codex/2026-08-25/t/work/gsc_compare/Pages.csv")
GSC_EXPORT_SHA256 = "5e66478db75f8693ea762cbeba2fd8d58d63eecbe3d50e71981fcd1f1c80c6f9"

SCHOOL_RANKING_PAGE = (
    "es/blog/best-school-districts-in-union-county-nj-for-families-buying-2026.html"
)
UNSAFE_INHERITED_SELLER_PAGES = {
    "es/blog/selling-inherited-home-nj.html",
}
CLICKED_REDIRECTS = {
    "/es/blog/selling-home-woodbridge-nj-2026": "/es/sell-your-home",
}
DESTINATION_LABELS = {
    "/es/buy-a-home": "Abrir la guía actual para compradores en Nueva Jersey",
    "/es/sell-your-home": "Abrir la guía actual para vendedores en Nueva Jersey",
    "/es/communities": "Explorar las guías actuales de comunidades",
    "/es/counties/union-county": "Explorar los recursos actuales del Condado de Union",
}


def route_for(relative: str) -> str:
    return "/" + relative.removesuffix(".html")


def quarantine_mapping() -> dict[str, str]:
    buying = sorted((ROOT / "es" / "blog").glob("buying-home-*-nj-2026.html"))
    selling = sorted((ROOT / "es" / "blog").glob("selling-home-*-nj-2026.html"))
    neighborhoods = sorted((ROOT / "es" / "blog").glob("neighborhoods-*-nj.html"))
    if (len(buying), len(selling), len(neighborhoods)) != (47, 44, 11):
        raise RuntimeError(
            "expected 47 buying, 44 selling, and 11 neighborhood pages; "
            f"found {len(buying)}, {len(selling)}, and {len(neighborhoods)}"
        )
    mapping: dict[str, str] = {}
    for path in buying:
        mapping[path.relative_to(ROOT).as_posix()] = "/es/buy-a-home"
    for path in selling:
        mapping[path.relative_to(ROOT).as_posix()] = "/es/sell-your-home"
    for path in neighborhoods:
        mapping[path.relative_to(ROOT).as_posix()] = "/es/communities"
    mapping[SCHOOL_RANKING_PAGE] = "/es/counties/union-county"
    for relative in UNSAFE_INHERITED_SELLER_PAGES:
        mapping[relative] = "/es/sell-your-home"
    if len(mapping) != 104:
        raise RuntimeError(f"expected 104 Spanish quarantine pages, found {len(mapping)}")
    return dict(sorted(mapping.items()))


def fallback(destination: str, *, redirect: bool) -> str:
    escaped_destination = html.escape(destination, quote=True)
    canonical = html.escape(f"{SITE}{destination}", quote=True)
    label = html.escape(DESTINATION_LABELS[destination])
    redirect_markup = ""
    if redirect:
        redirect_markup = (
            f'\n  <meta http-equiv="refresh" content="0; url={escaped_destination}">'
            f'\n  <script>window.location.replace({json.dumps(destination)});</script>'
        )
    return f'''<!doctype html>
<html lang="es">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#1A1A1A">
  <title>Guía inmobiliaria archivada de Nueva Jersey</title>
  <meta name="description" content="Este artículo anterior está archivado. Continúa con una guía inmobiliaria actual de Nueva Jersey, revisada con fuentes.">
  <meta name="robots" content="noindex, follow">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="es_US">
  <meta property="og:title" content="Guía inmobiliaria archivada de Nueva Jersey">
  <meta property="og:description" content="Este artículo anterior está archivado. Continúa con una guía inmobiliaria actual de Nueva Jersey, revisada con fuentes.">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Guía inmobiliaria archivada de Nueva Jersey">
  <meta name="twitter:description" content="Este artículo anterior está archivado. Continúa con una guía inmobiliaria actual de Nueva Jersey, revisada con fuentes.">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="canonical" href="{canonical}">{redirect_markup}
  <link rel="stylesheet" href="/css/styles.css">
  <style>
    :root {{ --archive-ink:#1A1A1A; --archive-panel:#0A0A0A; --archive-red:#C41230; --archive-gold:#B8962E; --archive-ivory:#FAFAF8; }}
    * {{ box-sizing:border-box; }}
    body.archive-page {{ margin:0; min-height:100vh; display:grid; place-items:center; padding:24px; background:var(--archive-ink); color:var(--archive-ivory); }}
    .archive-page main {{ width:min(680px,100%); padding:clamp(28px,7vw,58px); background:var(--archive-panel); border:1px solid var(--archive-gold); border-top:5px solid var(--archive-red); text-align:center; }}
    .archive-page h1 {{ margin:0 0 16px; color:var(--archive-ivory); font-size:clamp(2rem,7vw,3.4rem); line-height:1.12; }}
    .archive-page p {{ color:#D8D2C8; line-height:1.7; }}
    .archive-page .archive-cta {{ min-height:48px; display:inline-flex; align-items:center; justify-content:center; margin-top:12px; padding:12px 20px; background:var(--archive-red); color:#fff; font-weight:700; text-decoration:none; border:2px solid transparent; }}
    .archive-page .archive-cta:focus-visible {{ outline:3px solid var(--archive-gold); outline-offset:3px; }}
  </style>
</head>
<body class="archive-page">
  <a class="skip-link" href="#main">Saltar al contenido principal</a>
  <main id="main">
    <h1>Este artículo ha sido archivado</h1>
    <p>Este artículo local anterior ya no se mantiene. Continúa con una guía inmobiliaria actual de Nueva Jersey, revisada con fuentes.</p>
    <a class="archive-cta" href="{escaped_destination}">{label}</a>
  </main>
</body>
</html>
'''


def normalized_route(value: str, source: Path) -> str | None:
    parsed = urlsplit(value.strip())
    if parsed.scheme and parsed.netloc:
        if parsed.netloc.lower() not in {"thejorgeramirezgroup.com", "www.thejorgeramirezgroup.com"}:
            return None
        path = parsed.path
    elif value.startswith("/"):
        path = parsed.path
    elif parsed.scheme or value.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    else:
        relative = source.relative_to(ROOT)
        base = "/" + relative.parent.as_posix().strip("/") + "/"
        path = posixpath.normpath(posixpath.join(base, parsed.path))
        if not path.startswith("/"):
            path = "/" + path
    return re.sub(r"\.html$", "", path.rstrip("/")) or "/"


def remove_blog_index_entries(routes: set[str]) -> int:
    path = ROOT / "es" / "blog" / "index.html"
    source = path.read_text(encoding="utf-8")
    removed = 0
    for element in ("article", "li"):
        pattern = re.compile(rf"\s*<{element}\b[^>]*>.*?</{element}>", re.I | re.S)

        def replace(match: re.Match[str]) -> str:
            nonlocal removed
            block = match.group(0)
            if any(route in block or f"{route}.html" in block for route in routes):
                removed += 1
                return ""
            return block

        source = pattern.sub(replace, source)
    source = re.sub(r"\s*<!-- AUTO \d{4}-\d{2}-\d{2} -->", "", source)
    path.write_text(source, encoding="utf-8")
    return removed


def rewrite_spanish_links(mapping: dict[str, str], owned_files: set[str]) -> int:
    by_route = {route_for(relative): destination for relative, destination in mapping.items()}
    href_re = re.compile(r'(?P<prefix>\bhref\s*=\s*["\'])(?P<url>[^"\']+)(?P<suffix>["\'])', re.I)
    changed = 0
    for relative in sorted(owned_files - set(mapping)):
        if not relative.endswith(".html"):
            continue
        path = ROOT / relative
        source = path.read_text(encoding="utf-8", errors="replace")

        def replace(match: re.Match[str]) -> str:
            original = match.group("url")
            destination = by_route.get(normalized_route(original, path) or "")
            if not destination:
                return match.group(0)
            parsed = urlsplit(original)
            replacement = f"{SITE}{destination}" if parsed.scheme and parsed.netloc else destination
            return f'{match.group("prefix")}{replacement}{match.group("suffix")}'

        updated = href_re.sub(replace, source)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


def remove_spanish_sitemap_entries(routes: set[str]) -> int:
    path = ROOT / "sitemap-es.xml"
    source = path.read_text(encoding="utf-8")
    removed = 0
    for route in sorted(routes):
        pattern = re.compile(
            r"\s*<url>\s*<loc>" + re.escape(f"{SITE}{route}") + r"(?:\.html)?/?</loc>.*?</url>",
            re.S,
        )
        source, count = pattern.subn("", source)
        removed += count
    path.write_text(source.rstrip() + "\n", encoding="utf-8")
    return removed


def remove_english_reciprocal_hreflang(routes: set[str]) -> int:
    absolute_routes = {f"{SITE}{route}" for route in routes}
    html_alternate = re.compile(
        r"\s*<link\b[^>]*rel=[\"']alternate[\"'][^>]*hreflang=[\"'](?:es-US|es)[\"'][^>]*>",
        re.I,
    )
    sitemap_alternate = re.compile(
        r"\s*<xhtml:link\b[^>]*hreflang=[\"'](?:es-US|es)[\"'][^>]*/>",
        re.I,
    )
    changed = 0
    for path in sorted(ROOT.rglob("*.html")):
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] in {".vercel", "es", "towns", "realtor", "crm", "node_modules", "property-leads-system"}:
            continue
        source = path.read_text(encoding="utf-8", errors="replace")

        def replace(match: re.Match[str]) -> str:
            return "" if any(route in match.group(0) for route in absolute_routes) else match.group(0)

        updated = html_alternate.sub(replace, source)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    sitemap = ROOT / "sitemap.xml"
    source = sitemap.read_text(encoding="utf-8")

    def replace_sitemap(match: re.Match[str]) -> str:
        return "" if any(route in match.group(0) for route in absolute_routes) else match.group(0)

    updated = sitemap_alternate.sub(replace_sitemap, source)
    if updated != source:
        sitemap.write_text(updated.rstrip() + "\n", encoding="utf-8")
        changed += 1
    return changed


def rewrite_managed_redirect_destinations(mapping: dict[str, str]) -> int:
    """Keep existing redirect sources one-hop when their target is quarantined."""
    path = ROOT / "vercel.json"
    source = path.read_text(encoding="utf-8")
    by_route = {route_for(relative): destination for relative, destination in mapping.items()}
    destination_re = re.compile(r'(?P<prefix>"destination"\s*:\s*")(?P<route>/es/[^"?]+)(?P<suffix>[^"]*")')
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        route = match.group("route").removesuffix(".html")
        destination = by_route.get(route)
        if not destination:
            return match.group(0)
        changed += 1
        return f'{match.group("prefix")}{destination}{match.group("suffix")}'

    updated = destination_re.sub(replace, source)
    if updated != source:
        path.write_text(updated, encoding="utf-8")
    return changed


def canonical_gsc_route(url: str) -> str:
    path = urlsplit(url).path.rstrip("/")
    return path.removesuffix(".html") or "/"


def refresh_gsc_fixture(mapping: dict[str, str], source_export: Path) -> None:
    if hashlib.sha256(source_export.read_bytes()).hexdigest() != GSC_EXPORT_SHA256:
        raise RuntimeError("GSC source export checksum does not match the reviewed snapshot")
    routes = {route_for(relative) for relative in mapping}
    with source_export.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = [row for row in reader if canonical_gsc_route(row["Top pages"]) in routes]
        fieldnames = reader.fieldnames
    if not fieldnames:
        raise RuntimeError("GSC source export has no header")
    GSC_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with GSC_FIXTURE.open("w", encoding="utf-8", newline="") as fixture:
        writer = csv.DictWriter(fixture, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def gsc_snapshot(mapping: dict[str, str]) -> tuple[dict[str, dict[str, int]], dict[str, object]]:
    routes = {route_for(relative) for relative in mapping}
    metrics = {
        route: {
            "variantRows": 0,
            "lastThreeMonthsClicks": 0,
            "previousThreeMonthsClicks": 0,
            "lastThreeMonthsImpressions": 0,
            "previousThreeMonthsImpressions": 0,
        }
        for route in routes
    }
    with GSC_FIXTURE.open(encoding="utf-8-sig", newline="") as fixture:
        for row in csv.DictReader(fixture):
            route = canonical_gsc_route(row["Top pages"])
            if route not in metrics:
                raise RuntimeError(f"fixture contains out-of-scope GSC row: {route}")
            item = metrics[route]
            item["variantRows"] += 1
            item["lastThreeMonthsClicks"] += int(float(row["Last 3 months Clicks"] or 0))
            item["previousThreeMonthsClicks"] += int(float(row["Previous 3 months Clicks"] or 0))
            item["lastThreeMonthsImpressions"] += int(float(row["Last 3 months Impressions"] or 0))
            item["previousThreeMonthsImpressions"] += int(float(row["Previous 3 months Impressions"] or 0))
    redirect_routes = set(CLICKED_REDIRECTS)
    noindex_routes = routes - redirect_routes

    def totals(selected: set[str]) -> dict[str, int]:
        keys = (
            "lastThreeMonthsClicks",
            "previousThreeMonthsClicks",
            "lastThreeMonthsImpressions",
            "previousThreeMonthsImpressions",
        )
        return {
            "routes": len(selected),
            "routesWithRows": sum(bool(metrics[route]["variantRows"]) for route in selected),
            **{key: sum(metrics[route][key] for route in selected) for key in keys},
        }

    aggregate = {
        "sourceExport": str(GSC_EXPORT),
        "sourceExportSha256": GSC_EXPORT_SHA256,
        "snapshotCaveat": "Historical snapshot from the supplied Search Console Pages export; metrics are not live beyond that export.",
        "trafficPreservedBySameIntentRedirect": totals(redirect_routes),
        "staticNoindexFallback": totals(noindex_routes),
    }
    redirected = aggregate["trafficPreservedBySameIntentRedirect"]
    static = aggregate["staticNoindexFallback"]
    if redirected["lastThreeMonthsClicks"] != 1 or redirected["previousThreeMonthsClicks"] != 0:
        raise RuntimeError("the exact clicked Spanish route is not preserved by redirect")
    if static["lastThreeMonthsClicks"] or static["previousThreeMonthsClicks"]:
        raise RuntimeError("a clicked Spanish route was left as a static noindex fallback")
    return metrics, aggregate


def write_manifest(mapping: dict[str, str], metrics: dict[str, dict[str, int]], aggregate: dict[str, object]) -> None:
    pages = []
    for relative, destination in mapping.items():
        if relative == SCHOOL_RANKING_PAGE:
            cluster = "subjective-school-ranking"
        elif relative in UNSAFE_INHERITED_SELLER_PAGES:
            cluster = "unsafe-inherited-seller"
        elif "/buying-home-" in relative:
            cluster = "scaled-town-buying"
        elif "/selling-home-" in relative:
            cluster = "scaled-town-selling"
        else:
            cluster = "scaled-neighborhood-profile"
        route = route_for(relative)
        pages.append(
            {
                "file": relative,
                "path": route,
                "destination": destination,
                "cluster": cluster,
                "disposition": "same-intent-redirect" if route in CLICKED_REDIRECTS else "static-noindex-fallback",
                "gsc": metrics[route],
            }
        )
    payload = {
        "base": "91e46ee81037336421a0457cc307736f44d5d8a8",
        "quarantined_on": "2026-08-26",
        "reason": "Scaled Spanish town pages relied on subjective school, safety, neighborhood, or protected-audience framing without maintained official local research.",
        "signalReview": {
            "gsc": aggregate,
            "recordedLeads": {
                "status": "no-page-attribution-dataset-in-repository",
                "note": "Repository lead stores do not persist landing-page URLs for these routes.",
            },
            "externalBacklinks": {
                "status": "no-backlink-export-in-repository",
                "note": "No external backlink inventory was available in the supplied workspace.",
            },
            "internalLinks": {
                "status": "rewired-on-owned-spanish-inventory",
                "note": "Owned Spanish links point to each route's documented stronger destination.",
            },
        },
        "pages": pages,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_inventory(mapping: dict[str, str]) -> set[str]:
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    owned_before = set(payload["reviewed"]) | set(payload.get("quarantined", []))
    quarantined = set(mapping)
    if not quarantined <= owned_before:
        raise RuntimeError(f"quarantine paths are not in owned inventory: {sorted(quarantined - owned_before)}")
    payload["reviewed"] = sorted(owned_before - quarantined)
    payload["quarantined"] = sorted(quarantined)
    INVENTORY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return owned_before


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-gsc-fixture", type=Path, metavar="PAGES_CSV")
    args = parser.parse_args()
    mapping = quarantine_mapping()
    if args.refresh_gsc_fixture:
        refresh_gsc_fixture(mapping, args.refresh_gsc_fixture)
    metrics, aggregate = gsc_snapshot(mapping)
    routes = {route_for(relative) for relative in mapping}
    owned_before = update_inventory(mapping)
    write_manifest(mapping, metrics, aggregate)
    cards_removed = remove_blog_index_entries(routes)
    links_rewritten = rewrite_spanish_links(mapping, owned_before)
    sitemap_removed = remove_spanish_sitemap_entries(routes)
    reciprocal_changed = remove_english_reciprocal_hreflang(routes)
    redirects_rewritten = rewrite_managed_redirect_destinations(mapping)
    for relative, destination in mapping.items():
        route = route_for(relative)
        (ROOT / relative).write_text(
            fallback(destination, redirect=route in CLICKED_REDIRECTS),
            encoding="utf-8",
        )
    print(
        f"quarantined={len(mapping)} sitemap_removed={sitemap_removed} "
        f"blog_entries_removed={cards_removed} spanish_link_files_rewritten={links_rewritten} "
        f"english_reciprocal_files_changed={reciprocal_changed} "
        f"managed_redirects_rewritten={redirects_rewritten}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
