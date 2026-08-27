#!/usr/bin/env python3
"""Retire the unsupported seller and valuation doorway-page layer.

The JSON manifest is the source of truth. This utility fails closed unless the
manifest exactly matches the known 37 seller and 15 valuation files. It then
plans the complete change in memory before writing: small ``noindex`` fallback
pages, exact permanent redirects for clean and ``.html`` URLs, sitemap removal,
and two maintained-hub link-section replacements. ``--check`` never writes.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
MANIFEST_PATH = ROOT / "data" / "programmatic-doorway-retirement.json"
BASE_COMMIT = "5abf49e7ee2d35311504e740a2c1bc428736120c"
MANAGED_LINK_FILES = {"home-valuation.html", "sell-your-home.html"}
SKIP_INTERNAL_LINK_DIRS = {
    ".git",
    "crm",
    "docs",
    "node_modules",
    "property-leads-system",
}

KNOWN_SELL_SLUGS = {
    "basking-ridge",
    "bloomfield",
    "chatham",
    "clark",
    "cranford",
    "edison",
    "fanwood",
    "florham-park",
    "glen-ridge",
    "highland-park",
    "linden",
    "livingston",
    "madison",
    "maplewood",
    "metuchen",
    "millburn",
    "montclair",
    "morristown",
    "mountain-lakes",
    "mountainside",
    "new-providence",
    "north-caldwell",
    "nutley",
    "old-bridge",
    "parsippany",
    "rahway",
    "roseland",
    "scotch-plains",
    "short-hills",
    "south-orange",
    "springfield",
    "summit",
    "verona",
    "warren-township",
    "west-orange",
    "westfield",
    "woodbridge",
}
KNOWN_VALUATION_SLUGS = {
    "chatham",
    "cranford",
    "livingston",
    "madison",
    "maplewood",
    "millburn",
    "montclair",
    "new-providence",
    "scotch-plains",
    "short-hills",
    "south-orange",
    "springfield",
    "summit",
    "west-orange",
    "westfield",
}
KNOWN_FILES = {
    *(f"sell-my-house-{slug}-nj.html" for slug in KNOWN_SELL_SLUGS),
    *(f"home-valuation-{slug}-nj.html" for slug in KNOWN_VALUATION_SLUGS),
}
KNOWN_ROUTES = {"/" + filename.removesuffix(".html") for filename in KNOWN_FILES}
KNOWN_LINK_EXCEPTIONS = {
    "blog/market-report-livingston-nj-2026.html",
    "blog/market-report-maplewood-nj-2026.html",
    "blog/market-report-montclair-nj-2026.html",
    "blog/market-report-short-hills-nj-2026.html",
    "blog/market-report-south-orange-nj-2026.html",
    "blog/market-report-west-orange-nj-2026.html",
    "towns/woodbridge.html",
}

URL_BLOCK = re.compile(r"^[ \t]*<url>\s*\n.*?^[ \t]*</url>[ \t]*\n?", re.M | re.S)
SITE_URL = re.compile(r"https://(?:www\.)?thejorgeramirezgroup\.com[^<\"']*")
HREF = re.compile(r'(?P<prefix>\bhref\s*=\s*["\'])(?P<url>[^"\']+)(?P<suffix>["\'])', re.I)
SELLER_LEGACY_SECTION = re.compile(
    r'\n[ \t]*<h3 style="margin-top: 30px;">Seller Guides by Town</h3>\s*'
    r'<div class="link-grid">.*?</div>',
    re.S,
)
SELLER_MANAGED_SECTION = re.compile(
    r'\n[ \t]*<section\b[^>]*data-doorway-retirement-links="seller"[^>]*>.*?</section>',
    re.S,
)
VALUATION_LEGACY_SECTION = re.compile(
    r'\n[ \t]*<div\b[^>]*>\s*'
    r'<h3\b[^>]*>Town-by-Town Home Valuations</h3>\s*'
    r'<p\b[^>]*>.*?</p>\s*</div>',
    re.S,
)
VALUATION_MANAGED_SECTION = re.compile(
    r'\n[ \t]*<section\b[^>]*data-doorway-retirement-links="valuation"[^>]*>.*?</section>',
    re.S,
)
RISKY_VISIBLE_COPY = re.compile(
    r"\b2026\b|\bmedian\b|days?\s+on\s+market|\bDOM\b|\bcash\b|"
    r"\bdiscount\b|\b(?:outcome|guarantee|promise)\b|\bschools?\b|"
    r"\bfamil(?:y|ies)\b|\bsold\b|over\s+asking|\$\s*\d|\d+(?:\.\d+)?\s*%",
    re.I,
)
SCHEMA_COPY = re.compile(
    r"application/ld\+json|FAQPage|RealEstateAgent|LocalBusiness|"
    r"AggregateRating|Review|priceRange|\"@type\"",
    re.I,
)


class RetirementContractError(RuntimeError):
    """Raised before writes when inventory or output scope is unsafe."""


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RetirementContractError("manifest root must be an object")
    return payload


def manifest_pages(manifest: dict[str, object]) -> list[dict[str, str]]:
    pages = manifest.get("pages")
    if not isinstance(pages, list) or not all(isinstance(item, dict) for item in pages):
        raise RetirementContractError("manifest pages must be a list of objects")
    return pages  # type: ignore[return-value]


def managed_output_paths(manifest: dict[str, object]) -> set[str]:
    return {item["file"] for item in manifest_pages(manifest)} | {
        "home-valuation.html",
        "sell-your-home.html",
        "sitemap.xml",
        "vercel.json",
    }


def validate_manifest(manifest: dict[str, object], *, root: Path = ROOT) -> None:
    pages = manifest_pages(manifest)
    if manifest.get("workflow_id") != "unsupported-programmatic-doorway-retirement":
        raise RetirementContractError("unexpected workflow_id")
    if manifest.get("inventory_base_commit") != BASE_COMMIT:
        raise RetirementContractError("manifest inventory base commit changed")
    if len(pages) != 52:
        raise RetirementContractError(f"expected 52 manifest pages, found {len(pages)}")
    if pages != sorted(pages, key=lambda item: str(item.get("file", ""))):
        raise RetirementContractError("manifest pages must be sorted by file")

    files: set[str] = set()
    routes: set[str] = set()
    family_counts = {"sell_my_house": 0, "home_valuation": 0}
    for item in pages:
        if set(item) != {"family", "file", "path", "destination"}:
            raise RetirementContractError(f"unexpected page fields: {item}")
        family = str(item["family"])
        filename = str(item["file"])
        route = str(item["path"])
        destination = str(item["destination"])
        if "/" in filename or filename not in KNOWN_FILES:
            raise RetirementContractError(f"unknown or non-root doorway file: {filename}")
        if filename in files or route in routes:
            raise RetirementContractError(f"duplicate doorway inventory: {filename}")
        if route != "/" + filename.removesuffix(".html") or route not in KNOWN_ROUTES:
            raise RetirementContractError(f"route/file mismatch: {filename} -> {route}")
        expected_family = (
            "sell_my_house" if filename.startswith("sell-my-house-") else "home_valuation"
        )
        expected_destination = (
            "/sell-your-home" if expected_family == "sell_my_house" else "/home-valuation"
        )
        if family != expected_family or destination != expected_destination:
            raise RetirementContractError(f"unsafe destination contract: {filename}")
        files.add(filename)
        routes.add(route)
        family_counts[family] += 1

    if files != KNOWN_FILES or routes != KNOWN_ROUTES:
        raise RetirementContractError("manifest does not equal the hard-coded known inventory")
    if family_counts != {"sell_my_house": 37, "home_valuation": 15}:
        raise RetirementContractError(f"unexpected family counts: {family_counts}")

    current_files = {
        path.name
        for pattern in ("sell-my-house-*-nj.html", "home-valuation-*-nj.html")
        for path in root.glob(pattern)
    }
    if current_files != KNOWN_FILES:
        missing = sorted(KNOWN_FILES - current_files)
        unexpected = sorted(current_files - KNOWN_FILES)
        raise RetirementContractError(
            f"root inventory drift; missing={missing}, unexpected={unexpected}"
        )

    exceptions = manifest.get("internal_link_exceptions")
    if not isinstance(exceptions, list) or not all(isinstance(item, dict) for item in exceptions):
        raise RetirementContractError("internal_link_exceptions must be a list of objects")
    exception_files = {str(item.get("file", "")) for item in exceptions}
    if exception_files != KNOWN_LINK_EXCEPTIONS or len(exceptions) != len(exception_files):
        raise RetirementContractError("protected internal-link exception inventory changed")
    for item in exceptions:
        if set(item) != {"file", "reason"} or not str(item.get("reason", "")).strip():
            raise RetirementContractError(f"invalid internal-link exception: {item}")
        if not (root / str(item["file"])).is_file():
            raise RetirementContractError(f"missing protected internal-link source: {item['file']}")

    outputs = managed_output_paths(manifest)
    explicitly_protected = {
        "towns/helmetta.html",
        "towns/middlesex.html",
        "towns/orange.html",
        "towns/woodbridge.html",
    }
    if outputs & explicitly_protected:
        raise RetirementContractError("managed output includes an explicitly protected town file")
    if any(
        path.startswith("blog/market-report-")
        or "buyer-guide" in path
        or "buyer-nj-programs" in path
        for path in outputs
    ):
        raise RetirementContractError("managed output includes active market/buyer content")


def redirect_mappings(manifest: dict[str, object]) -> dict[str, str]:
    mappings: dict[str, str] = {}
    for item in manifest_pages(manifest):
        route = item["path"]
        destination = item["destination"]
        mappings[route] = destination
        mappings[route + ".html"] = destination
    if len(mappings) != 104:
        raise RetirementContractError(
            f"expected 104 redirect variants, found {len(mappings)}"
        )
    return dict(sorted(mappings.items()))


def validate_destinations(manifest: dict[str, object], *, root: Path = ROOT) -> None:
    for destination in sorted({item["destination"] for item in manifest_pages(manifest)}):
        path = root / f"{destination.removeprefix('/')}.html"
        if not path.is_file():
            raise RetirementContractError(f"missing redirect destination: {destination}")
        source = path.read_text(encoding="utf-8")
        if re.search(r'<meta\b[^>]*http-equiv=["\']refresh["\']', source, re.I):
            raise RetirementContractError(
                f"redirect destination is an HTML redirect: {destination}"
            )
        if re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*noindex', source, re.I):
            raise RetirementContractError(f"redirect destination is noindex: {destination}")
        canonical = f'<link rel="canonical" href="{SITE}{destination}">'
        if canonical not in source:
            raise RetirementContractError(
                f"redirect destination is not self-canonical: {destination}"
            )


def render_fallback(item: dict[str, str]) -> str:
    destination = item["destination"]
    safe_destination = html.escape(destination, quote=True)
    safe_canonical = html.escape(SITE + destination, quote=True)
    js_destination = json.dumps(destination)
    if item["family"] == "sell_my_house":
        title = "Seller Page Moved | The Jorge Ramirez Group"
        heading = "The seller page has moved"
        description = "Continue to the maintained New Jersey home-selling guide."
        copy = (
            "Continue to the maintained New Jersey home-selling guide for service "
            "details and ways to get in touch."
        )
        label = "Open the home-selling guide"
    else:
        title = "Home Valuation Page Moved | The Jorge Ramirez Group"
        heading = "The valuation page has moved"
        description = "Continue to the maintained New Jersey home valuation page."
        copy = (
            "Continue to the maintained home valuation page to learn about the "
            "request process and share property details."
        )
        label = "Open the home valuation page"
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#1A1A1A">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{safe_canonical}">
  <meta http-equiv="refresh" content="0; url={safe_destination}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&amp;family=Playfair+Display:wght@700&amp;display=swap" rel="stylesheet" media="print" onload="this.media='all'">
  <noscript><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&amp;family=Playfair+Display:wght@700&amp;display=swap" rel="stylesheet"></noscript>
  <style>
    :root {{ --black:#0A0A0A; --ink:#1A1A1A; --red:#C41230; --red-dark:#8B0D22; --gold:#B8962E; --gold-light:#D4AF5A; --ivory:#FAFAF8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; padding:24px; background:linear-gradient(145deg,var(--black),var(--ink)); color:var(--ivory); font-family:Inter,Arial,sans-serif; }}
    main {{ width:min(680px,calc(100vw - 48px)); padding:clamp(30px,7vw,58px); background:#0A0A0A; border:1px solid var(--gold); border-top:5px solid var(--red); border-radius:18px; box-shadow:0 24px 70px rgba(0,0,0,.4); text-align:center; }}
    .eyebrow {{ margin:0 0 12px; color:var(--gold-light); font-size:.78rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }}
    h1 {{ margin:0 0 16px; font-family:'Playfair Display',Georgia,serif; font-size:clamp(2rem,7vw,3.4rem); line-height:1.1; }}
    p {{ margin:0 auto 24px; max-width:520px; color:#FAFAF8; line-height:1.7; }}
    a {{ min-height:48px; display:inline-flex; align-items:center; justify-content:center; padding:12px 20px; background:var(--red); color:#FAFAF8; border:2px solid transparent; border-radius:999px; font-weight:700; text-decoration:none; }}
    a:hover {{ background:var(--red-dark); }}
    a:focus-visible {{ outline:3px solid var(--gold-light); outline-offset:4px; }}
  </style>
  <script>window.location.replace({js_destination})</script>
</head>
<body>
  <main id="main" data-programmatic-doorway-fallback="v1" aria-labelledby="page-title">
    <p class="eyebrow">Page moved</p>
    <h1 id="page-title">{html.escape(heading)}</h1>
    <p>{html.escape(copy)}</p>
    <a href="{safe_destination}">{html.escape(label)}</a>
  </main>
</body>
</html>
'''


def expected_vercel(source: str, mappings: dict[str, str]) -> str:
    config = json.loads(source)
    redirects = config.get("redirects")
    if not isinstance(redirects, list):
        raise RetirementContractError("vercel.json redirects must be a list")
    unmanaged: list[dict[str, object]] = []
    for item in redirects:
        if not isinstance(item, dict):
            raise RetirementContractError("vercel redirect entries must be objects")
        redirect_source = str(item.get("source", ""))
        if redirect_source in mappings:
            if item.get("has"):
                raise RetirementContractError(
                    f"refusing to replace conditional managed redirect: {redirect_source}"
                )
            continue
        unmanaged.append(item)

    # Preserve unrelated redirect entries byte-for-byte and in their current
    # order, including any legacy duplicates outside this managed inventory.
    # This batch may only enforce uniqueness for its own 104 exact sources.
    unmanaged_sources = [str(item.get("source", "")) for item in unmanaged]
    for destination in set(mappings.values()):
        if destination in unmanaged_sources:
            raise RetirementContractError(f"redirect destination would chain: {destination}")

    def is_canonical_host_rule(item: dict[str, object]) -> bool:
        return (
            str(item.get("source", "")) == "/(.*)"
            and str(item.get("destination", "")) == SITE + "/$1"
            and any(
                condition.get("type") == "host"
                for condition in item.get("has", [])
                if isinstance(condition, dict)
            )
        )

    canonical_preamble_end = 0
    while (
        canonical_preamble_end < len(unmanaged)
        and is_canonical_host_rule(unmanaged[canonical_preamble_end])
    ):
        canonical_preamble_end += 1

    # Host canonicalization is a fail-closed preamble. Managed path redirects
    # belong after it but before every other conditional or dynamic route.
    insertion_index = len(unmanaged)
    for index, item in enumerate(
        unmanaged[canonical_preamble_end:], start=canonical_preamble_end
    ):
        source_value = str(item.get("source", ""))
        if item.get("has") or ":" in source_value:
            insertion_index = index
            break
    additions = [
        {"source": source_value, "destination": destination, "permanent": True}
        for source_value, destination in mappings.items()
    ]
    config["redirects"] = (
        unmanaged[:insertion_index] + additions + unmanaged[insertion_index:]
    )
    return json.dumps(config, indent=2) + "\n"


def normalized_managed_route(value: str) -> str | None:
    parsed = urlsplit(html.unescape(value.strip()))
    if parsed.scheme and parsed.netloc:
        if parsed.netloc.lower() not in {
            "thejorgeramirezgroup.com",
            "www.thejorgeramirezgroup.com",
        }:
            return None
        route = parsed.path
    elif value.startswith("/"):
        route = parsed.path
    else:
        return None
    route = re.sub(r"\.html$", "", route.rstrip("/"))
    return route or "/"


def expected_sitemap(source: str) -> str:
    def remove_managed_block(match: re.Match[str]) -> str:
        block = match.group(0)
        loc_match = re.search(r"<loc>([^<]+)</loc>", block)
        primary = normalized_managed_route(loc_match.group(1)) if loc_match else None
        references = {
            route
            for value in SITE_URL.findall(block)
            if (route := normalized_managed_route(value)) in KNOWN_ROUTES
        }
        if primary in KNOWN_ROUTES:
            return ""
        if references:
            raise RetirementContractError(
                "managed doorway appears as an alternate on an unrelated sitemap URL: "
                + ", ".join(sorted(references))
            )
        return block

    updated = URL_BLOCK.sub(remove_managed_block, source)
    remaining = {
        route
        for value in SITE_URL.findall(updated)
        if (route := normalized_managed_route(value)) in KNOWN_ROUTES
    }
    if remaining:
        raise RetirementContractError(
            "managed doorway reference remains outside a removable sitemap block: "
            + ", ".join(sorted(remaining))
        )
    return updated


SELLER_REPLACEMENT = '''
            <section class="doorway-retirement-links" data-doorway-retirement-links="seller">
                <h3 style="margin-top: 30px;">Selling a Home in New Jersey</h3>
                <p>Use the maintained statewide seller guide for the process, service details, and address-specific next steps.</p>
                <div class="link-grid">
                    <a href="/sell-your-home">Open the New Jersey Home-Selling Guide</a>
                    <a href="/counties/union-county">Union County</a>
                    <a href="/counties/essex-county">Essex County</a>
                    <a href="/counties/morris-county">Morris County</a>
                </div>
            </section>'''

VALUATION_REPLACEMENT = '''
        <section data-doorway-retirement-links="valuation" style="max-width:880px;margin:30px auto;padding:22px 26px;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <h3 style="margin-bottom:10px;">Home Valuation Requests</h3>
            <p style="line-height:1.7;">Use the maintained valuation page for any New Jersey property and share the address details needed for an individual review. <a href="/home-valuation#valuation-request">Open the home valuation request</a>.</p>
        </section>'''


def replace_exact_section(
    source: str,
    *,
    legacy: re.Pattern[str],
    managed: re.Pattern[str],
    replacement: str,
    label: str,
) -> str:
    legacy_matches = list(legacy.finditer(source))
    managed_matches = list(managed.finditer(source))
    if len(legacy_matches) == 1 and not managed_matches:
        return legacy.sub(replacement, source, count=1)
    if len(managed_matches) == 1 and not legacy_matches:
        return managed.sub(replacement, source, count=1)
    raise RetirementContractError(
        f"{label} link section is missing, duplicated, or ambiguous "
        f"(legacy={len(legacy_matches)}, managed={len(managed_matches)})"
    )


def expected_hub(relative: str, source: str) -> str:
    if relative == "sell-your-home.html":
        return replace_exact_section(
            source,
            legacy=SELLER_LEGACY_SECTION,
            managed=SELLER_MANAGED_SECTION,
            replacement=SELLER_REPLACEMENT,
            label="seller hub",
        )
    if relative == "home-valuation.html":
        return replace_exact_section(
            source,
            legacy=VALUATION_LEGACY_SECTION,
            managed=VALUATION_MANAGED_SECTION,
            replacement=VALUATION_REPLACEMENT,
            label="valuation hub",
        )
    raise RetirementContractError(f"unmanaged internal-link source: {relative}")


def internal_link_offenders(
    manifest: dict[str, object], outputs: dict[str, str], *, root: Path = ROOT
) -> list[str]:
    retired_files = {item["file"] for item in manifest_pages(manifest)}
    exceptions = {
        str(item["file"])
        for item in manifest["internal_link_exceptions"]  # type: ignore[index]
    }
    offenders: list[str] = []
    for path in root.rglob("*.html"):
        relative = path.relative_to(root)
        relative_name = relative.as_posix()
        if (
            relative_name in retired_files
            or relative_name in exceptions
            or any(part in SKIP_INTERNAL_LINK_DIRS for part in relative.parts)
        ):
            continue
        source = outputs.get(
            relative_name, path.read_text(encoding="utf-8", errors="replace")
        )
        if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', source, re.I):
            continue
        for match in HREF.finditer(source):
            route = normalized_managed_route(match.group("url"))
            if route in KNOWN_ROUTES:
                offenders.append(f"{relative_name} -> {match.group('url')}")
    return offenders


def validate_fallback(relative: str, source: str, item: dict[str, str]) -> None:
    destination = item["destination"]
    required = (
        '<html lang="en">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="robots" content="noindex, follow">',
        f'<link rel="canonical" href="{SITE}{destination}">',
        f'<meta http-equiv="refresh" content="0; url={destination}">',
        'data-programmatic-doorway-fallback="v1"',
        f'href="{destination}"',
        f"window.location.replace({json.dumps(destination)})",
        "https://fonts.googleapis.com/css2?family=Inter",
        "'Playfair Display'",
        "Inter",
        "width:min(680px,calc(100vw - 48px))",
    )
    missing = [needle for needle in required if needle not in source]
    if missing:
        raise RetirementContractError(f"unsafe fallback {relative}; missing {missing}")
    if len(source.encode("utf-8")) >= 5000:
        raise RetirementContractError(f"fallback exceeds compact size limit: {relative}")
    for color in (
        "#0A0A0A",
        "#1A1A1A",
        "#C41230",
        "#8B0D22",
        "#B8962E",
        "#D4AF5A",
        "#FAFAF8",
    ):
        if color not in source:
            raise RetirementContractError(f"fallback palette drift in {relative}: {color}")
    if SCHEMA_COPY.search(source):
        raise RetirementContractError(f"schema or rich-result content in fallback: {relative}")
    visible = re.sub(
        r"<script\b.*?</script>|<style\b.*?</style>",
        " ",
        source,
        flags=re.I | re.S,
    )
    visible = html.unescape(re.sub(r"<[^>]+>", " ", visible))
    if RISKY_VISIBLE_COPY.search(visible):
        raise RetirementContractError(f"risky visible copy in fallback: {relative}")


def build_outputs(
    manifest: dict[str, object], *, root: Path = ROOT
) -> dict[str, str]:
    validate_manifest(manifest, root=root)
    validate_destinations(manifest, root=root)
    outputs: dict[str, str] = {}
    for item in manifest_pages(manifest):
        outputs[item["file"]] = render_fallback(item)
    mappings = redirect_mappings(manifest)
    outputs["vercel.json"] = expected_vercel(
        (root / "vercel.json").read_text(encoding="utf-8"), mappings
    )
    outputs["sitemap.xml"] = expected_sitemap(
        (root / "sitemap.xml").read_text(encoding="utf-8")
    )
    for relative in sorted(MANAGED_LINK_FILES):
        outputs[relative] = expected_hub(
            relative, (root / relative).read_text(encoding="utf-8")
        )

    if set(outputs) != managed_output_paths(manifest):
        raise RetirementContractError("planned output scope does not match managed contract")
    for item in manifest_pages(manifest):
        validate_fallback(item["file"], outputs[item["file"]], item)
    offenders = internal_link_offenders(manifest, outputs, root=root)
    if offenders:
        raise RetirementContractError(
            "indexable internal links still target retired routes:\n" + "\n".join(offenders)
        )
    return outputs


def drifted_outputs(outputs: dict[str, str], *, root: Path = ROOT) -> list[str]:
    drift: list[str] = []
    for relative, expected in sorted(outputs.items()):
        path = root / relative
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            drift.append(relative)
    return drift


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the manifest, fallbacks, redirects, sitemap, and links without writing",
    )
    args = parser.parse_args()
    try:
        manifest = load_manifest()
        outputs = build_outputs(manifest)
        drift = drifted_outputs(outputs)
        if args.check:
            if drift:
                for relative in drift:
                    print(f"doorway retirement drift: {relative}", file=sys.stderr)
                return 1
            print(
                "programmatic doorway retirement current: "
                "52 fallbacks, 104 redirects"
            )
            return 0

        for relative in drift:
            (ROOT / relative).write_text(outputs[relative], encoding="utf-8")
        verified = build_outputs(manifest)
        remaining = drifted_outputs(verified)
        if remaining:
            raise RetirementContractError(
                "post-write verification failed: " + ", ".join(remaining)
            )
        print(
            f"retired 52 programmatic doorways; updated {len(drift)} managed files; "
            "104 permanent redirect variants current"
        )
        return 0
    except (OSError, json.JSONDecodeError, RetirementContractError) as error:
        print(f"programmatic doorway retirement failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
