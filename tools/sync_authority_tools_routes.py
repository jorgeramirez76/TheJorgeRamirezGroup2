#!/usr/bin/env python3
"""Synchronize redirects, sitemaps, and owned internal links for this cleanup wave."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
MANIFEST_PATH = ROOT / "data" / "authority-tools-sources.json"
TOWN_DECISIONS_PATH = ROOT / "data" / "indexable-town-risk-decisions.json"
REVIEWED_ON = "2026-08-26"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def redirected_routes(data: dict) -> set[str]:
    return {record["route"] for record in data["consolidations"]}


def town_alias_sources() -> set[str]:
    """Return exact alias routes owned by the town-remediation renderer."""
    decisions = json.loads(TOWN_DECISIONS_PATH.read_text(encoding="utf-8"))["decisions"]
    sources: set[str] = set()
    for slug, decision in decisions.items():
        if decision.get("action") != "redirect":
            continue
        sources.update(
            {
                f"/towns/{slug}",
                f"/towns/{slug}.html",
                f"/es/towns/{slug}",
                f"/es/towns/{slug}.html",
                f"/realtor/{slug}-nj",
                f"/realtor/{slug}-nj.html",
                f"/communities/{slug}",
                f"/communities/{slug}.html",
            }
        )
    return sources


def redirect_config(data: dict, current: str) -> str:
    config = json.loads(current)
    managed_sources = {
        candidate
        for record in data["consolidations"]
        for candidate in (record["route"], record["route"] + ".html")
    }
    preserved = [
        rule for rule in config.get("redirects", []) if rule.get("source") not in managed_sources
    ]
    desired = [
        {
            "source": candidate,
            "destination": record["destination"],
            "permanent": True,
        }
        for record in data["consolidations"]
        for candidate in (record["route"], record["route"] + ".html")
    ]
    def is_canonical_host_rule(rule: dict) -> bool:
        return (
            str(rule.get("source", "")) == "/(.*)"
            and str(rule.get("destination", "")) == SITE + "/$1"
            and any(
                condition.get("type") == "host"
                for condition in rule.get("has", [])
                if isinstance(condition, dict)
            )
        )

    canonical_preamble_end = 0
    while (
        canonical_preamble_end < len(preserved)
        and is_canonical_host_rule(preserved[canonical_preamble_end])
    ):
        canonical_preamble_end += 1
    # The town-remediation owner inserts newly materialized exact aliases after
    # the host preamble. Keep that contiguous block ahead of this cleanup's
    # rules so both deterministic owners converge regardless of run order.
    insertion_index = canonical_preamble_end
    town_sources = town_alias_sources()
    while (
        insertion_index < len(preserved)
        and preserved[insertion_index].get("source") in town_sources
    ):
        insertion_index += 1
    config["redirects"] = (
        preserved[:insertion_index]
        + desired
        + preserved[insertion_index:]
    )
    return json.dumps(config, ensure_ascii=False, indent=2) + "\n"


URL_BLOCK_RE = re.compile(r"^[ \t]*<url>\s*.*?</url>[ \t]*(?:\n|$)", re.MULTILINE | re.DOTALL)
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
ALTERNATE_RE = re.compile(
    r"^[ \t]*<xhtml:link\b[^>]*\bhref=\"([^\"]+)\"[^>]*/>[ \t]*(?:\n|$)",
    re.MULTILINE,
)


def sitemap_block(route: str, *, pair: tuple[str, str] | None, spanish: bool) -> str:
    lines = [
        "  <url>",
        f"    <loc>{SITE}{route}</loc>",
        f"    <lastmod>{REVIEWED_ON}</lastmod>",
        "    <changefreq>monthly</changefreq>",
        "    <priority>0.8</priority>",
    ]
    if pair:
        en_route, es_route = pair
        lines.extend(
            [
                f'    <xhtml:link rel="alternate" hreflang="en-US" href="{SITE}{en_route}"/>',
                f'    <xhtml:link rel="alternate" hreflang="es-US" href="{SITE}{es_route}"/>',
                f'    <xhtml:link rel="alternate" hreflang="es" href="{SITE}{es_route}"/>',
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{en_route}"/>',
            ]
        )
    else:
        lines.extend(
            [
                f'    <xhtml:link rel="alternate" hreflang="en-US" href="{SITE}{route}"/>',
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{route}"/>',
            ]
        )
    lines.append("  </url>")
    return "\n".join(lines)


def sitemap(data: dict, current: str, *, spanish: bool) -> str:
    retired = redirected_routes(data)
    pages = {
        record["route"]: record
        for record in data["indexablePages"].values()
        if (record["lang"] == "es") is spanish
    }
    replace_routes = retired | set(pages)

    def drop_managed_blocks(match: re.Match[str]) -> str:
        loc = LOC_RE.search(match.group(0))
        if not loc:
            return match.group(0)
        url = loc.group(1).removeprefix(SITE)
        return "" if url in replace_routes else match.group(0)

    updated = URL_BLOCK_RE.sub(drop_managed_blocks, current)

    def drop_retired_alternate(match: re.Match[str]) -> str:
        url = match.group(1)
        if not url.startswith(SITE):
            return match.group(0)
        route = url.removeprefix(SITE)
        if route.endswith(".html"):
            route = route[:-5]
        return "" if route in retired else match.group(0)

    updated = ALTERNATE_RE.sub(drop_retired_alternate, updated)
    blocks = []
    for route in pages:
        if route.endswith("nj-realty-transfer-fee-calculator"):
            pair = (
                "/nj-realty-transfer-fee-calculator",
                "/es/nj-realty-transfer-fee-calculator",
            )
        elif route.endswith("nj-real-estate-questions-answers"):
            pair = (
                "/nj-real-estate-questions-answers",
                "/es/nj-real-estate-questions-answers",
            )
        else:
            pair = None
        blocks.append(sitemap_block(route, pair=pair, spanish=spanish))
    insertion = "\n".join(blocks)
    body = updated.rstrip().removesuffix("</urlset>").rstrip()
    town_prefix = "/es/towns/" if spanish else "/towns/"
    first_town = re.search(
        rf"^[ \t]*<url>\s*<loc>{re.escape(SITE + town_prefix)}",
        body,
        re.MULTILINE,
    )
    if first_town:
        body = body[: first_town.start()].rstrip() + "\n" + insertion + "\n" + body[first_town.start() :]
    else:
        body = body + "\n" + insertion
    return body + "\n</urlset>\n"


HREF_RE = re.compile(r"(?P<before>\bhref\s*=\s*)(?P<quote>[\"'])(?P<url>[^\"']+)(?P=quote)", re.IGNORECASE)
LINK_TAG_RE = re.compile(r"^[ \t]*<link\b[^>]*>[ \t]*(?:\n|$)", re.IGNORECASE | re.MULTILINE)


def internal_links(data: dict, current: str, *, drop_hreflang: set[str]) -> str:
    destinations = {record["route"]: record["destination"] for record in data["consolidations"]}
    destinations.update(data.get("additionalLinkRewrites", {}))

    def drop_nonreciprocal_alternate(match: re.Match[str]) -> str:
        tag = match.group(0)
        if not re.search(r"\brel\s*=\s*[\"']alternate[\"']", tag, re.IGNORECASE):
            return tag
        href = HREF_RE.search(tag)
        if not href:
            return tag
        url = href.group("url")
        route = url.removeprefix(SITE)
        route = route[:-5] if route.endswith(".html") else route
        return "" if route in drop_hreflang else tag

    def replace_href(match: re.Match[str]) -> str:
        url = match.group("url")
        absolute = url.startswith(SITE)
        local = url.removeprefix(SITE) if absolute else url
        suffix_at = min(
            [position for mark in ("?", "#") if (position := local.find(mark)) >= 0]
            or [len(local)]
        )
        route, suffix = local[:suffix_at], local[suffix_at:]
        normalized = route[:-5] if route.endswith(".html") else route
        destination = destinations.get(normalized)
        if not destination:
            return match.group(0)
        rewritten = (SITE if absolute else "") + destination + suffix
        quote = match.group("quote")
        return f'{match.group("before")}{quote}{rewritten}{quote}'

    return HREF_RE.sub(replace_href, LINK_TAG_RE.sub(drop_nonreciprocal_alternate, current))


def planned_outputs(data: dict) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    vercel = ROOT / "vercel.json"
    outputs[vercel] = redirect_config(data, vercel.read_text(encoding="utf-8"))
    for name, spanish in (("sitemap.xml", False), ("sitemap-es.xml", True)):
        path = ROOT / name
        outputs[path] = sitemap(data, path.read_text(encoding="utf-8"), spanish=spanish)
    for relative in data["internalLinkFiles"]:
        path = ROOT / relative
        outputs[path] = internal_links(
            data,
            path.read_text(encoding="utf-8"),
            drop_hreflang=set(data.get("hreflangRemovals", {}).get(relative, [])),
        )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if synchronized files differ")
    args = parser.parse_args()
    data = load_manifest()
    outputs = planned_outputs(data)
    changed = [path for path, expected in outputs.items() if path.read_text(encoding="utf-8") != expected]
    if args.check:
        if changed:
            for path in changed:
                print(f"OUT OF SYNC: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"Authority/tool routes synchronized: {len(outputs)} files")
        return 0
    for path in changed:
        path.write_text(outputs[path], encoding="utf-8")
        print(f"WROTE {path.relative_to(ROOT)}")
    print(f"Authority/tool route sync complete: {len(changed)} changed, {len(outputs)} checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
