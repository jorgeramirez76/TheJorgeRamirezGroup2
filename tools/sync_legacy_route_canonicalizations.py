#!/usr/bin/env python3
"""Synchronize evidence-backed legacy redirects and their static fallbacks."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "legacy-route-canonicalizations.json"
VERCEL_CONFIG = ROOT / "vercel.json"
SITE = "https://thejorgeramirezgroup.com"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def routes() -> list[dict[str, str]]:
    manifest = load_json(MANIFEST)
    values = manifest.get("routes", [])
    if manifest.get("schemaVersion") != 1 or not isinstance(values, list):
        raise RuntimeError("invalid legacy canonicalization manifest")
    sources = [str(item["source"]) for item in values]
    files = [str(item["fallbackFile"]) for item in values]
    if len(sources) != len(set(sources)) or len(files) != len(set(files)):
        raise RuntimeError("legacy canonicalization sources and fallback files must be unique")
    return [{key: str(value) for key, value in item.items()} for item in values]


def is_pattern(rule: dict) -> bool:
    source = str(rule.get("source", ""))
    return bool(rule.get("has") or any(mark in source for mark in (":", "*", "(")))


def render_config(config: dict, items: list[dict[str, str]]) -> str:
    redirects = config.get("redirects")
    if not isinstance(redirects, list):
        raise RuntimeError("vercel.json redirects must be a list")
    managed = {item["source"] for item in items}
    redundant_html = {source + ".html" for source in managed}
    retained = [
        rule
        for rule in redirects
        if str(rule.get("source", "")) not in managed | redundant_html
    ]
    # Keep the AI Pipeline and programmatic-doorway managed blocks after this
    # small exact-route block. Those independent generators remove and reinsert
    # their own routes in that order; this anchor keeps every tool idempotent.
    insertion = next(
        (
            index
            for index, rule in enumerate(retained)
            if re.fullmatch(
                r"/(?:es/)?features/[^/:*()]+",
                str(rule.get("source", "")),
            )
            or str(rule.get("source", "")).startswith(
                ("/home-valuation-", "/sell-my-house-")
            )
        ),
        next(
            (index for index, rule in enumerate(retained) if is_pattern(rule)),
            len(retained),
        ),
    )
    rendered = [
        {
            "source": item["source"],
            "destination": item["destination"],
            "permanent": True,
        }
        for item in sorted(items, key=lambda item: item["source"])
    ]
    config["redirects"] = retained[:insertion] + rendered + retained[insertion:]
    return json.dumps(config, indent=2) + "\n"


def render_fallback(item: dict[str, str]) -> str:
    destination = item["destination"]
    canonical = html.escape(f"{SITE}{destination}", quote=True)
    internal = html.escape(destination, quote=True)
    label = html.escape(item["buttonLabel"])
    spanish = item["language"] == "es"
    language = "es" if spanish else "en"
    title = "Guía inmobiliaria archivada de Nueva Jersey" if spanish else "Archived New Jersey Real Estate Guide"
    description = (
        "Esta dirección anterior se ha retirado. Continúa a la guía actual de bienes raíces de Nueva Jersey."
        if spanish
        else "This older address is retired. Continue to the current New Jersey real estate guide."
    )
    heading = "Esta guía se ha trasladado" if spanish else "This guide has moved"
    body = (
        "Conservamos esta dirección para llevarte directamente al recurso actual que coincide con el tema original."
        if spanish
        else "We keep this address available so it can lead directly to the current resource that matches the original topic."
    )
    skip = "Saltar al contenido principal" if spanish else "Skip to main content"
    return f'''<!doctype html>
<html lang="{language}">
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
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="robots" content="noindex, follow">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="canonical" href="{canonical}">
  <meta http-equiv="refresh" content="0; url={internal}">
  <script>window.location.replace({json.dumps(destination)});</script>
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
  <a class="skip-link" href="#main">{skip}</a>
  <main id="main">
    <h1>{heading}</h1>
    <p>{body}</p>
    <a class="archive-cta" href="{internal}">{label}</a>
  </main>
</body>
</html>
'''


def local_path(route: str) -> Path:
    relative = route.strip("/")
    html_path = ROOT / f"{relative}.html"
    if html_path.is_file():
        return html_path
    return ROOT / relative / "index.html"


def issues(items: list[dict[str, str]], expected_config: str) -> list[str]:
    problems: list[str] = []
    config = load_json(VERCEL_CONFIG)
    if config.get("cleanUrls") is not True or config.get("trailingSlash") is not False:
        problems.append("cleanUrls/trailingSlash contract changed")
    if VERCEL_CONFIG.read_text(encoding="utf-8") != expected_config:
        problems.append("vercel.json differs from legacy canonicalization render")
    redirects: dict[str, list[dict]] = {}
    for rule in config.get("redirects", []):
        redirects.setdefault(str(rule.get("source", "")), []).append(rule)
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sitemap += (ROOT / "sitemap-es.xml").read_text(encoding="utf-8")
    for item in items:
        source = item["source"]
        destination = item["destination"]
        rules = redirects.get(source, [])
        if len(rules) != 1 or rules[0].get("destination") != destination or rules[0].get("permanent") is not True:
            problems.append(f"{source}: clean permanent redirect mismatch")
        if source + ".html" in redirects:
            problems.append(f"{source}: redundant .html rule bypasses cleanUrls contract")
        if f"<loc>{SITE}{source}</loc>" in sitemap:
            problems.append(f"{source}: retired source remains submitted")
        if f"<loc>{SITE}{destination}</loc>" not in sitemap:
            problems.append(f"{source}: destination is not submitted")
        destination_path = local_path(destination)
        if not destination_path.is_file():
            problems.append(f"{source}: destination file missing")
        elif re.search(
            r'<meta\b[^>]*name=["\']robots["\'][^>]*noindex',
            destination_path.read_text(encoding="utf-8", errors="ignore"),
            re.I,
        ):
            problems.append(f"{source}: destination is noindex")
        fallback = ROOT / item["fallbackFile"]
        if not fallback.is_file() or fallback.read_text(encoding="utf-8") != render_fallback(item):
            problems.append(f"{source}: fallback drift")
    declared = sum(len(config.get(key, [])) for key in ("redirects", "rewrites", "headers"))
    if declared >= 2048:
        problems.append(f"declared Vercel route limit exceeded: {declared}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    items = routes()
    config = load_json(VERCEL_CONFIG)
    expected_config = render_config(config, items)
    if not args.check:
        if VERCEL_CONFIG.read_text(encoding="utf-8") != expected_config:
            VERCEL_CONFIG.write_text(expected_config, encoding="utf-8")
        for item in items:
            path = ROOT / item["fallbackFile"]
            rendered = render_fallback(item)
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
                path.write_text(rendered, encoding="utf-8")
        expected_config = render_config(load_json(VERCEL_CONFIG), items)
    found = issues(items, expected_config)
    for problem in found:
        print(problem, file=sys.stderr)
    if not found:
        print(f"legacy canonicalizations current: {len(items)} clean routes and fallbacks")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
