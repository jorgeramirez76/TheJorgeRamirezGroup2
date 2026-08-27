#!/usr/bin/env python3
"""Retire the legacy daily-content cluster without creating broken URLs.

The retired routes remain as small, accessible ``noindex`` fallbacks pointing
people to stronger evergreen guides. They are removed from the sitemap and blog
index, and internal links are rewired to the corresponding destination.
"""

from __future__ import annotations

import html
import json
import posixpath
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
MANIFEST = ROOT / "data" / "retired-legacy-daily-posts.json"
SNIPPET_BACKLOG = ROOT / "data" / "english-snippet-backlog.json"
SKIP_DIRS = {".git", "crm", "node_modules", "property-leads-system"}
EXPECTED_LEGACY_PAGE_COUNT = 141


DESTINATION_LABELS = {
    "/buy-a-home": "Open the New Jersey buyer guide",
    "/sell-your-home": "Open the New Jersey seller guide",
    "/communities": "Explore New Jersey community guides",
    "/towns/roselle": "Open the current Roselle guide",
    "/blog/first-time-home-buyer-nj-guide": "Open the current New Jersey buyer guide",
    "/blog/nj-property-tax-guide": "Open the current New Jersey property-tax guide",
    "/blog/best-time-to-sell-home-nj": "Open the current New Jersey seller-planning guide",
}


def legacy_files(root: Path = ROOT) -> list[str]:
    commits = subprocess.run(
        [
            "git",
            "log",
            "--all",
            "--format=%H",
            "--grep=^Add daily blog posts -",
            "--grep=^blog: add daily SEO post ",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    paths: set[str] = set()
    for commit in commits:
        changed = subprocess.run(
            ["git", "show", "--name-only", "--format=", commit],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        paths.update(
            path
            for path in changed
            if path.startswith("blog/")
            and path.endswith(".html")
            and path != "blog/index.html"
            and (root / path).is_file()
        )
    return sorted(paths)


def destination_for(slug: str) -> str:
    if slug == "buying-home-roselle-nj-2026":
        return "/towns/roselle"
    if "property-tax" in slug:
        return "/blog/nj-property-tax-guide"
    if "walkable-neighborhood" in slug:
        return "/communities"
    if slug.startswith("buying-") or any(
        term in slug
        for term in (
            "buyer",
            "inspection",
            "home-safety",
            "fire-hazard",
            "mold",
            "pest",
            "water-damage",
            "house-sounds",
            "home-feels-cold",
            "homeowners-insurance",
            "house-with-pool",
        )
    ):
        return "/blog/first-time-home-buyer-nj-guide"
    if any(
        term in slug
        for term in (
            "real-estate-market",
            "housing-market",
            "home-prices",
            "pricing-your",
            "fall-listing",
            "sell-nj-home-fall",
            "selling-nj-home-summer",
        )
    ):
        return "/blog/best-time-to-sell-home-nj"
    return "/sell-your-home"


def fallback(destination: str) -> str:
    escaped_destination = html.escape(destination, quote=True)
    canonical = html.escape(f"{SITE}{destination}", quote=True)
    label = html.escape(DESTINATION_LABELS[destination])
    js_destination = json.dumps(destination)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#1A1A1A">
  <title>NJ Real Estate Guide Moved | Jorge Ramirez</title>
  <meta name="description" content="Continue to the current source-reviewed New Jersey real estate guide from The Jorge Ramirez Group.">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{canonical}">
  <meta http-equiv="refresh" content="0; url={escaped_destination}">
  <style>
    :root {{ --ink:#1A1A1A; --red:#C41230; --gold:#B8962E; --ivory:#FAFAF8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; padding:24px; background:var(--ink); color:var(--ivory); font-family:Inter,Arial,sans-serif; }}
    main {{ width:min(680px,100%); padding:clamp(28px,7vw,58px); background:#0A0A0A; border:1px solid var(--gold); border-top:5px solid var(--red); text-align:center; }}
    h1 {{ margin:0 0 16px; font-family:'Playfair Display',Georgia,serif; font-size:clamp(2rem,7vw,3.4rem); line-height:1.12; }}
    p {{ color:#D8D2C8; line-height:1.7; }}
    a {{ min-height:48px; display:inline-flex; align-items:center; justify-content:center; margin-top:12px; padding:12px 20px; background:var(--red); color:#fff; font-weight:700; text-decoration:none; border:2px solid transparent; }}
    a:focus-visible {{ outline:3px solid var(--gold); outline-offset:3px; }}
  </style>
  <script>window.location.replace({js_destination});</script>
</head>
<body>
  <main id="main">
    <h1>This guide has moved</h1>
    <p>Continue to a current, source-reviewed New Jersey real estate guide.</p>
    <a href="{escaped_destination}">{label}</a>
  </main>
</body>
</html>
'''


def route_from_href(value: str, *, source: Path) -> str | None:
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
    path = re.sub(r"\.html$", "", path.rstrip("/"))
    return path or "/"


def rewrite_internal_links(mapping: dict[str, str]) -> int:
    href_re = re.compile(r'(?P<prefix>\bhref\s*=\s*["\'])(?P<url>[^"\']+)(?P<suffix>["\'])', re.I)
    changed = 0
    retired_files = {f"blog/{route.rsplit('/', 1)[-1]}.html" for route in mapping}
    for path in ROOT.rglob("*.html"):
        relative = path.relative_to(ROOT)
        if relative.as_posix() in retired_files or any(part in SKIP_DIRS for part in relative.parts):
            continue
        source = path.read_text(encoding="utf-8", errors="replace")

        def replace(match: re.Match[str]) -> str:
            route = route_from_href(match.group("url"), source=path)
            destination = mapping.get(route or "")
            if not destination:
                return match.group(0)
            return f'{match.group("prefix")}{destination}{match.group("suffix")}'

        updated = href_re.sub(replace, source)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


def remove_sitemap_routes(mapping: dict[str, str]) -> int:
    path = ROOT / "sitemap.xml"
    source = path.read_text(encoding="utf-8")
    removed = 0
    for route in mapping:
        pattern = re.compile(
            r"\s*<url>\s*<loc>"
            + re.escape(f"{SITE}{route}")
            + r"(?:\.html)?/?</loc>.*?</url>",
            re.S,
        )
        source, count = pattern.subn("", source)
        removed += count
    source = "\n".join(line.rstrip() for line in source.splitlines())
    path.write_text(source.rstrip() + "\n", encoding="utf-8")
    return removed


def remove_blog_index_cards(mapping: dict[str, str]) -> int:
    path = ROOT / "blog" / "index.html"
    source = path.read_text(encoding="utf-8")
    article_re = re.compile(r"\s*<article\b[^>]*>.*?</article>", re.I | re.S)
    removed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal removed
        block = match.group(0)
        for route in mapping:
            slug = route.rsplit("/", 1)[-1]
            if route in block or f'{slug}.html' in block or f'href="{slug}"' in block:
                removed += 1
                return ""
        return block

    updated = article_re.sub(replace, source)
    updated = re.sub(r"\s*<!-- AUTO \d{4}-\d{2}-\d{2} -->", "", updated)
    path.write_text(updated, encoding="utf-8")
    return removed


def write_manifest(files: list[str], mapping: dict[str, str]) -> None:
    payload = {
        "workflow_id": "legacy-house-outlook-daily",
        "retired_on": "2026-08-26",
        "reason": (
            "Unreviewed scaled-content cluster with unsupported claims, weak topical fit, "
            "and negligible organic performance; retained only as noindex user fallbacks."
        ),
        "gsc_recent_3_months": {
            "exported_on": "2026-08-25",
            "clicks": 1,
            "impressions": 74,
            "matched_pages": 3,
        },
        "pages": [
            {
                "file": file,
                "path": f"/blog/{Path(file).stem}",
                "destination": mapping[f"/blog/{Path(file).stem}"],
            }
            for file in files
        ],
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def update_snippet_history(files: list[str]) -> None:
    payload = json.loads(SNIPPET_BACKLOG.read_text(encoding="utf-8"))
    pages = payload.get("pages", {})
    prior_retirements = set(payload.get("retired_pages", []))
    daily_retirements = {file for file in files if file in pages}
    payload["retired_pages"] = sorted(prior_retirements | daily_retirements)
    SNIPPET_BACKLOG.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    files = legacy_files()
    if len(files) != EXPECTED_LEGACY_PAGE_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_LEGACY_PAGE_COUNT} legacy HTML pages, found {len(files)}"
        )
    mapping = {f"/blog/{Path(file).stem}": destination_for(Path(file).stem) for file in files}
    sitemap_removed = remove_sitemap_routes(mapping)
    cards_removed = remove_blog_index_cards(mapping)
    links_rewritten = rewrite_internal_links(mapping)
    for file in files:
        route = f"/blog/{Path(file).stem}"
        (ROOT / file).write_text(fallback(mapping[route]), encoding="utf-8")
    write_manifest(files, mapping)
    update_snippet_history(files)
    print(
        f"retired {len(files)} legacy pages; removed {sitemap_removed} sitemap entries "
        f"and {cards_removed} blog cards; rewired links in {links_rewritten} files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
