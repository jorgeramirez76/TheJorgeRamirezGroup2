#!/usr/bin/env python3
"""Retire the English scaled town-blog cluster as neutral, noindex fallbacks.

The URLs remain usable, but the low-value pages leave the sitemap, hreflang,
blog index, and links on the owned English pages.  Running this script twice is
safe and produces the same files.
"""

from __future__ import annotations

import argparse
import csv
import html
import hashlib
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
MANIFEST = ROOT / "data" / "english-fair-housing-quarantine.json"
INVENTORY = ROOT / "data" / "english-fair-housing-inventory.json"
GSC_FIXTURE = ROOT / "tests" / "fixtures" / "gsc-english-fair-housing-quarantine-pages.csv"
GSC_EXPORT = Path("/Users/teddy/Documents/Codex/2026-08-25/t/work/gsc_compare/Pages.csv")
GSC_EXPORT_SHA256 = "5e66478db75f8693ea762cbeba2fd8d58d63eecbe3d50e71981fcd1f1c80c6f9"

SCHOOL_RANKING_PAGE = (
    "blog/best-school-districts-in-union-county-nj-for-families-buying-2026.html"
)
COMMUTER_RANKING_PAGE = "blog/nyc-to-nj-commute-guide-2026.html"
THREE_TOWN_RANKING_PAGE = "blog/summit-vs-chatham-vs-westfield-nj.html"
CHATHAM_MADISON_BLOG_PAGE = "blog/chatham-vs-madison-nj.html"
LIVINGSTON_WEST_ORANGE_PAGE = "livingston-vs-west-orange-nj.html"
PREEXISTING_REDIRECTS = {
    "blog/buying-home-roselle-nj-2026.html",
    "blog/selling-home-with-solar-panels-nj-2026.html",
}
RENDER_TEMPLATES = {"tools/blog-automation/template_source.html"}

DESTINATION_LABELS = {
    "/buy-a-home": "Open the New Jersey buyer guide",
    "/sell-your-home": "Open the New Jersey seller guide",
    "/communities": "Explore current New Jersey community guides",
    "/counties/essex-county": "Explore current Essex County resources",
    "/counties/hudson-county": "Explore current Hudson County resources",
    "/counties/morris-county": "Explore current Morris County resources",
    "/counties/somerset-county": "Explore current Somerset County resources",
    "/counties/union-county": "Explore current Union County resources",
    "/blog/best-nj-suburbs-nyc-commuters": "Open the source-reviewed New Jersey commuter guide",
    "/blog/best-nj-towns-for-families-2026": "Open the source-reviewed New Jersey town comparison",
}

TOWN_ROUTE_DESTINATIONS = {
    "/blog/neighborhoods-maplewood-nj": "/counties/essex-county",
    "/blog/neighborhoods-summit-nj": "/counties/union-county",
    "/blog/neighborhoods-basking-ridge-nj": "/counties/somerset-county",
    "/blog/neighborhoods-livingston-nj": "/counties/essex-county",
    "/blog/neighborhoods-madison-nj": "/counties/morris-county",
    "/blog/neighborhoods-montclair-nj": "/counties/essex-county",
    "/blog/neighborhoods-millburn-nj": "/counties/essex-county",
    "/blog/neighborhoods-scotch-plains-nj": "/counties/union-county",
    "/blog/buying-home-montclair-nj-2026": "/buy-a-home",
    "/blog/buying-home-randolph-nj-2026": "/buy-a-home",
    "/blog/buying-home-jersey-city-nj-2026": "/buy-a-home",
    "/blog/buying-home-rahway-nj-2026": "/buy-a-home",
    "/blog/selling-home-maplewood-nj-2026": "/sell-your-home",
    "/blog/nyc-to-nj-commute-guide-2026": "/blog/best-nj-suburbs-nyc-commuters",
    "/blog/summit-vs-chatham-vs-westfield-nj": "/blog/best-nj-towns-for-families-2026",
    "/blog/chatham-vs-madison-nj": "/chatham-vs-madison-nj",
}


def quarantine_mapping() -> dict[str, str]:
    buying = sorted(
        path
        for path in (ROOT / "blog").glob("buying-home-*-nj-2026.html")
        if path.relative_to(ROOT).as_posix() not in PREEXISTING_REDIRECTS
    )
    selling = sorted(
        path
        for path in (ROOT / "blog").glob("selling-home-*-nj-2026.html")
        if path.relative_to(ROOT).as_posix() not in PREEXISTING_REDIRECTS
    )
    neighborhoods = sorted((ROOT / "blog").glob("neighborhoods-*-nj.html"))
    if (len(buying), len(selling), len(neighborhoods)) != (47, 44, 11):
        raise RuntimeError(
            "expected 47 buying, 44 selling, and 11 neighborhood pages; "
            f"found {len(buying)}, {len(selling)}, and {len(neighborhoods)}"
        )

    mapping: dict[str, str] = {}
    for path in buying:
        mapping[path.relative_to(ROOT).as_posix()] = "/buy-a-home"
    for path in selling:
        mapping[path.relative_to(ROOT).as_posix()] = "/sell-your-home"
    for path in neighborhoods:
        mapping[path.relative_to(ROOT).as_posix()] = "/communities"
    mapping[SCHOOL_RANKING_PAGE] = "/counties/union-county"
    mapping[COMMUTER_RANKING_PAGE] = "/blog/best-nj-suburbs-nyc-commuters"
    mapping[THREE_TOWN_RANKING_PAGE] = "/blog/best-nj-towns-for-families-2026"
    mapping[CHATHAM_MADISON_BLOG_PAGE] = "/chatham-vs-madison-nj"
    mapping[LIVINGSTON_WEST_ORANGE_PAGE] = "/counties/essex-county"
    for relative in list(mapping):
        route = route_for(relative)
        if route in TOWN_ROUTE_DESTINATIONS:
            mapping[relative] = TOWN_ROUTE_DESTINATIONS[route]
    if len(mapping) != 107:
        raise RuntimeError(f"expected 107 quarantine pages, found {len(mapping)}")
    return dict(sorted(mapping.items()))


def route_for(relative: str) -> str:
    return "/" + relative.removesuffix(".html")


def fallback(destination: str, *, redirect: bool) -> str:
    escaped_destination = html.escape(destination, quote=True)
    canonical = html.escape(f"{SITE}{destination}", quote=True)
    label = html.escape(
        DESTINATION_LABELS.get(destination, "Continue to the current local guide")
    )
    redirect_markup = ""
    if redirect:
        redirect_markup = (
            f'\n  <meta http-equiv="refresh" content="0; url={escaped_destination}">'
            f'\n  <script>window.location.replace({json.dumps(destination)});</script>'
        )
    return f'''<!doctype html>
<html lang="en">
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
  <title>Archived New Jersey Real Estate Guide</title>
  <meta name="description" content="This older article is archived. Continue to a current, source-reviewed New Jersey real estate guide.">
  <meta name="robots" content="noindex, follow">
  <meta property="og:type" content="website">
  <meta property="og:title" content="Archived New Jersey Real Estate Guide">
  <meta property="og:description" content="This older article is archived. Continue to a current, source-reviewed New Jersey real estate guide.">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Archived New Jersey Real Estate Guide">
  <meta name="twitter:description" content="This older article is archived. Continue to a current, source-reviewed New Jersey real estate guide.">
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
  <a class="skip-link" href="#main">Skip to main content</a>
  <main id="main">
    <h1>This article has been archived</h1>
    <p>This older town article is no longer maintained. Continue to a current, source-reviewed New Jersey real estate guide.</p>
    <a class="archive-cta" href="{escaped_destination}">{label}</a>
  </main>
</body>
</html>
'''


def normalized_route(value: str, source: Path) -> str | None:
    parsed = urlsplit(value.strip())
    if parsed.scheme and parsed.netloc:
        if parsed.netloc.lower() not in {
            "thejorgeramirezgroup.com",
            "www.thejorgeramirezgroup.com",
        }:
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
    path = ROOT / "blog" / "index.html"
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


def rewrite_owned_links(mapping: dict[str, str], owned_files: set[str]) -> int:
    by_route = {route_for(relative): destination for relative, destination in mapping.items()}
    href_re = re.compile(r'(?P<prefix>\bhref\s*=\s*["\'])(?P<url>[^"\']+)(?P<suffix>["\'])', re.I)
    changed = 0
    for relative in sorted(owned_files - set(mapping) - RENDER_TEMPLATES):
        path = ROOT / relative
        source = path.read_text(encoding="utf-8", errors="replace")

        def replace(match: re.Match[str]) -> str:
            original = match.group("url")
            route = normalized_route(original, path)
            destination = by_route.get(route or "")
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


def remove_english_sitemap_entries(routes: set[str]) -> int:
    path = ROOT / "sitemap.xml"
    source = path.read_text(encoding="utf-8")
    removed = 0
    for route in sorted(routes):
        pattern = re.compile(
            r"\s*<url>\s*<loc>"
            + re.escape(f"{SITE}{route}")
            + r"(?:\.html)?/?</loc>.*?</url>",
            re.S,
        )
        source, count = pattern.subn("", source)
        removed += count
    path.write_text(source.rstrip() + "\n", encoding="utf-8")
    return removed


def remove_spanish_hreflang_references(routes: set[str]) -> int:
    absolute_routes = {f"{SITE}{route}" for route in routes}
    alternate = re.compile(
        r"\s*<link\b[^>]*rel=[\"']alternate[\"'][^>]*hreflang=[\"'](?:en-US|x-default)[\"'][^>]*>",
        re.I,
    )
    sitemap_alternate = re.compile(
        r"\s*<xhtml:link\b[^>]*hreflang=[\"'](?:en-US|x-default)[\"'][^>]*/>",
        re.I,
    )
    changed = 0
    for path in sorted((ROOT / "es").rglob("*.html")):
        source = path.read_text(encoding="utf-8", errors="replace")

        def replace(match: re.Match[str]) -> str:
            return "" if any(route in match.group(0) for route in absolute_routes) else match.group(0)

        updated = alternate.sub(replace, source)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    sitemap = ROOT / "sitemap-es.xml"
    source = sitemap.read_text(encoding="utf-8")

    def replace_sitemap(match: re.Match[str]) -> str:
        return "" if any(route in match.group(0) for route in absolute_routes) else match.group(0)

    updated = sitemap_alternate.sub(replace_sitemap, source)
    if updated != source:
        sitemap.write_text(updated.rstrip() + "\n", encoding="utf-8")
        changed += 1
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
        writer = csv.DictWriter(fixture, fieldnames=fieldnames)
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
            item["lastThreeMonthsImpressions"] += int(
                float(row["Last 3 months Impressions"] or 0)
            )
            item["previousThreeMonthsImpressions"] += int(
                float(row["Previous 3 months Impressions"] or 0)
            )

    redirect_routes = set(TOWN_ROUTE_DESTINATIONS)

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

    noindex_only = routes - redirect_routes
    aggregate = {
        "sourceExport": str(GSC_EXPORT),
        "sourceExportSha256": GSC_EXPORT_SHA256,
        "snapshotCaveat": (
            "Historical snapshot from the supplied Search Console Pages export; "
            "metrics are not live beyond that export."
        ),
        "trafficPreservedBySameIntentRedirect": totals(redirect_routes),
        "staticNoindexFallback": totals(noindex_only),
    }
    if aggregate["trafficPreservedBySameIntentRedirect"]["lastThreeMonthsClicks"] != 30:
        raise RuntimeError("expected 30 recent clicks on the same-intent redirect set")
    if aggregate["trafficPreservedBySameIntentRedirect"]["previousThreeMonthsClicks"] != 27:
        raise RuntimeError("expected 27 previous-period clicks on the same-intent redirect set")
    if aggregate["staticNoindexFallback"]["lastThreeMonthsClicks"]:
        raise RuntimeError("a recent-click URL was left as a static noindex fallback")
    if aggregate["staticNoindexFallback"]["previousThreeMonthsClicks"]:
        raise RuntimeError("a previous-period click URL was left as a static noindex fallback")
    return metrics, aggregate


def write_manifest(mapping: dict[str, str], metrics: dict[str, dict[str, int]], aggregate: dict[str, object]) -> None:
    pages = []
    for relative, destination in mapping.items():
        if relative == SCHOOL_RANKING_PAGE:
            cluster = "subjective-school-ranking"
        elif relative == COMMUTER_RANKING_PAGE:
            cluster = "legacy-commuter-ranking"
        elif relative == THREE_TOWN_RANKING_PAGE:
            cluster = "legacy-three-town-ranking"
        elif relative == CHATHAM_MADISON_BLOG_PAGE:
            cluster = "duplicate-town-comparison"
        elif relative == LIVINGSTON_WEST_ORANGE_PAGE:
            cluster = "unmaintained-school-ranking-comparison"
        elif relative.startswith("blog/buying-home-"):
            cluster = "scaled-town-buying"
        elif relative.startswith("blog/selling-home-"):
            cluster = "scaled-town-selling"
        else:
            cluster = "scaled-neighborhood-ranking"
        pages.append(
            {
                "file": relative,
                "path": route_for(relative),
                "destination": destination,
                "cluster": cluster,
                "disposition": (
                    "same-intent-redirect"
                    if route_for(relative) in TOWN_ROUTE_DESTINATIONS
                    else "static-noindex-fallback"
                ),
                "gsc": metrics[route_for(relative)],
            }
        )
    payload = {
        "base": "831c7918f9fcaad2496c4ea039ed1d8cc217038c",
        "quarantined_on": "2026-08-26",
        "reason": (
            "Scaled town pages depended on subjective school, safety, neighborhood, "
            "or protected-audience framing without maintained official local research."
        ),
        "signalReview": {
            "gsc": aggregate,
            "recordedLeads": {
                "status": "no-page-attribution-dataset-in-repository",
                "note": "The repository lead stores do not persist landing-page URLs for these routes.",
            },
            "externalBacklinks": {
                "status": "no-backlink-export-in-repository",
                "note": "No external backlink inventory was available in the supplied workspace.",
            },
            "internalLinks": {
                "status": "rewired-on-owned-english-inventory",
                "note": "Owned English links point to each route's documented stronger destination.",
            },
        },
        "pages": pages,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def update_inventory(mapping: dict[str, str]) -> set[str]:
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    owned_before = set(payload["reviewed"]) | set(payload.get("quarantined", []))
    quarantined = set(mapping)
    if not quarantined <= owned_before:
        missing = sorted(quarantined - owned_before)
        raise RuntimeError(f"quarantine paths are not in owned inventory: {missing}")
    payload["reviewed"] = sorted(owned_before - quarantined)
    payload["quarantined"] = sorted(quarantined)
    INVENTORY.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return owned_before


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-gsc-fixture",
        type=Path,
        metavar="PAGES_CSV",
        help="refresh the committed scoped fixture from the reviewed GSC Pages export",
    )
    args = parser.parse_args()
    mapping = quarantine_mapping()
    if args.refresh_gsc_fixture:
        refresh_gsc_fixture(mapping, args.refresh_gsc_fixture)
    metrics, aggregate = gsc_snapshot(mapping)
    routes = {route_for(relative) for relative in mapping}
    owned_before = update_inventory(mapping)
    write_manifest(mapping, metrics, aggregate)
    cards_removed = remove_blog_index_entries(routes)
    links_rewritten = rewrite_owned_links(mapping, owned_before)
    sitemap_removed = remove_english_sitemap_entries(routes)
    hreflang_files_changed = remove_spanish_hreflang_references(routes)
    for relative, destination in mapping.items():
        (ROOT / relative).write_text(
            fallback(destination, redirect=route_for(relative) in TOWN_ROUTE_DESTINATIONS),
            encoding="utf-8",
        )
    print(
        f"quarantined={len(mapping)} sitemap_removed={sitemap_removed} "
        f"blog_entries_removed={cards_removed} owned_link_files_rewritten={links_rewritten} "
        f"spanish_hreflang_files_changed={hreflang_files_changed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
