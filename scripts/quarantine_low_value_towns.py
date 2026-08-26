#!/usr/bin/env python3
"""Quarantine low-value strict town templates without deleting public pages.

The policy keeps a small, explicit rewrite queue indexable. Every other member
of the strict duplicate clusters is removed from search submission in English
and Spanish while remaining available to people who already have the URL.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
GSC_EXPORT = Path(
    "/Users/teddy/Documents/Codex/2026-08-25/t/work/gsc_compare/Pages.csv"
)
GSC_FIXTURE = ROOT / "tests" / "fixtures" / "gsc-town-quarantine-pages.csv"
GSC_MANIFEST = ROOT / "data" / "gsc-town-quarantine-impact.json"

PRIORITY_REWRITE_SLUGS = {
    "berkeley-heights",
    "bloomfield",
    "chatham-borough",
    "chatham-township",
    "cranford",
    "denville",
    "east-brunswick",
    "east-hanover",
    "fanwood",
    "guttenberg",
    "morris-plains",
    "new-providence",
    "roselle-park",
    "south-brunswick",
    "springfield",
    "west-new-york",
}

LOW_VALUE_STRICT_SLUGS = {
    "bayonne",
    "boonton",
    "butler",
    "carteret",
    "chester-borough",
    "chester-township",
    "clark",
    "dover",
    "east-newark",
    "garwood",
    "hanover",
    "harding",
    "harrison",
    "highland-park",
    "hillside",
    "jamesburg",
    "kearny",
    "kenilworth",
    "kinnelon",
    "lincoln-park",
    "linden",
    "mendham-borough",
    "mendham-township",
    "milltown",
    "mine-hill",
    "monroe-township",
    "mount-arlington",
    "mount-olive",
    "mountain-lakes",
    "netcong",
    "north-bergen",
    "north-brunswick",
    "old-bridge",
    "piscataway",
    "rahway",
    "randolph",
    "riverdale",
    "rockaway-borough",
    "rockaway-township",
    "roxbury",
    "sayreville",
    "secaucus",
    "south-amboy",
    "south-plainfield",
    "spotswood",
    "union-city",
    "verona",
    "victory-gardens",
}

ROBOTS_TAG = re.compile(
    r'<meta\b[^>]*\bname=["\']robots["\'][^>]*>', flags=re.IGNORECASE
)
HREFLANG_LINE = re.compile(
    r'^[ \t]*<link\b[^>]*\bhreflang=["\'][^"\']+["\'][^>]*>[ \t]*\n?',
    flags=re.IGNORECASE | re.MULTILINE,
)
URL_BLOCK = re.compile(r"(?ms)^  <url>\n.*?^  </url>\n?")


def quarantine_page(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    updated, replacements = ROBOTS_TAG.subn(
        '<meta name="robots" content="noindex, follow">', source, count=1
    )
    if replacements != 1:
        raise RuntimeError(f"{path}: expected exactly one robots meta tag")
    updated = HREFLANG_LINE.sub("", updated)
    if updated == source:
        raise RuntimeError(f"{path}: quarantine produced no change")
    path.write_text(updated, encoding="utf-8")


def remove_sitemap_urls(path: Path, target_urls: set[str]) -> None:
    source = path.read_text(encoding="utf-8")
    removed: set[str] = set()

    def keep_or_remove(match: re.Match[str]) -> str:
        block = match.group(0)
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        if loc and loc.group(1) in target_urls:
            removed.add(loc.group(1))
            return ""
        return block

    updated = URL_BLOCK.sub(keep_or_remove, source)
    missing = target_urls - removed
    if missing:
        raise RuntimeError(
            f"{path}: expected submitted URLs were absent: {', '.join(sorted(missing))}"
        )
    path.write_text(updated, encoding="utf-8")


def update_site_facts() -> int:
    path = ROOT / "data" / "site-facts.json"
    facts = json.loads(path.read_text(encoding="utf-8"))
    inventory = facts["canonicalTownInventory"]
    by_county = inventory["byCounty"]

    before = {slug for slugs in by_county.values() for slug in slugs}
    missing = LOW_VALUE_STRICT_SLUGS - before
    if missing:
        raise RuntimeError(
            "site-facts inventory is missing expected quarantine slugs: "
            + ", ".join(sorted(missing))
        )

    for county, slugs in by_county.items():
        by_county[county] = [
            slug for slug in slugs if slug not in LOW_VALUE_STRICT_SLUGS
        ]
    inventory["total"] = sum(len(slugs) for slugs in by_county.values())

    quarantine_entry = {
        "scope": "town-guide-strict-near-duplicate-cluster",
        "languages": ["en", "es"],
        "slugs": sorted(LOW_VALUE_STRICT_SLUGS),
        "reason": (
            "Near-exact generated town guides lack enough source-backed local value "
            "to justify search indexing in either language."
        ),
        "searchHandling": "noindex, follow; omitted from sitemaps and hreflang",
        "reviewStatus": "pending-local-fact-verification-and-editorial-rewrite",
        "evidence": {
            "qualityCheck": "tools/check_town_content_quality.py --strict",
            "gscSnapshot": "data/gsc-town-quarantine-impact.json",
        },
    }
    editorial = [
        entry
        for entry in facts["editorialQuarantine"]
        if entry.get("scope") != quarantine_entry["scope"]
    ]
    editorial.append(quarantine_entry)
    facts["editorialQuarantine"] = editorial

    path.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    return inventory["total"]


def town_slug_from_export_url(value: str) -> Optional[str]:
    path = urlsplit(value).path.rstrip("/")
    if path.endswith(".html"):
        path = path[:-5]
    match = re.fullmatch(r"/(?:es/)?towns/([^/]+)", path)
    return match.group(1) if match else None


def build_gsc_snapshot() -> dict[str, object]:
    if not GSC_EXPORT.exists():
        raise RuntimeError(f"required Search Console export is missing: {GSC_EXPORT}")

    sys.path.insert(0, str(ROOT))
    from tools.check_town_content_quality import fold_gsc_page_rows

    with GSC_EXPORT.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise RuntimeError(f"{GSC_EXPORT}: missing CSV header")
        rows = [
            row
            for row in reader
            if town_slug_from_export_url(row.get("Top pages") or "")
            in LOW_VALUE_STRICT_SLUGS
        ]

    GSC_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with GSC_FIXTURE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    folded = fold_gsc_page_rows(rows, LOW_VALUE_STRICT_SLUGS)
    totals = {
        "canonicalFamiliesWithRows": len(folded),
        "variantRows": sum(int(metrics["rows"]) for metrics in folded.values()),
        "clicks": sum(int(metrics["clicks"]) for metrics in folded.values()),
        "impressions": sum(int(metrics["impressions"]) for metrics in folded.values()),
    }
    modified = datetime.fromtimestamp(GSC_EXPORT.stat().st_mtime).astimezone()
    manifest: dict[str, object] = {
        "schemaVersion": 1,
        "calculatedOn": "2026-08-25",
        "sourceExport": str(GSC_EXPORT),
        "sourceExportModified": modified.isoformat(timespec="seconds"),
        "sourceExportSha256": hashlib.sha256(GSC_EXPORT.read_bytes()).hexdigest(),
        "metricColumns": {
            "clicks": "Last 3 months Clicks",
            "impressions": "Last 3 months Impressions",
            "position": "Last 3 months Position",
        },
        "snapshotCaveat": (
            "Historical snapshot calculated from the supplied Search Console export; "
            "metrics are not live or current beyond that export."
        ),
        "quarantinedSlugs": sorted(LOW_VALUE_STRICT_SLUGS),
        "potentialCanonicalFamilies": len(LOW_VALUE_STRICT_SLUGS) * 2,
        "canonicalFamiliesWithoutRows": len(LOW_VALUE_STRICT_SLUGS) * 2
        - len(folded),
        "totals": totals,
        "byCanonicalFamily": folded,
    }
    GSC_MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    if len(PRIORITY_REWRITE_SLUGS) != 16:
        raise RuntimeError("priority rewrite policy must contain exactly 16 slugs")
    if len(LOW_VALUE_STRICT_SLUGS) != 48:
        raise RuntimeError("low-value quarantine policy must contain exactly 48 slugs")
    if PRIORITY_REWRITE_SLUGS & LOW_VALUE_STRICT_SLUGS:
        raise RuntimeError("priority and quarantine policies overlap")

    for slug in sorted(LOW_VALUE_STRICT_SLUGS):
        quarantine_page(ROOT / "towns" / f"{slug}.html")
        quarantine_page(ROOT / "es" / "towns" / f"{slug}.html")

    remove_sitemap_urls(
        ROOT / "sitemap.xml",
        {f"{SITE}/towns/{slug}" for slug in LOW_VALUE_STRICT_SLUGS},
    )
    remove_sitemap_urls(
        ROOT / "sitemap-es.xml",
        {f"{SITE}/es/towns/{slug}" for slug in LOW_VALUE_STRICT_SLUGS},
    )
    total = update_site_facts()
    snapshot = build_gsc_snapshot()
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_communities_from_facts.py")],
        cwd=ROOT,
        check=True,
    )

    print(
        f"Quarantined {len(LOW_VALUE_STRICT_SLUGS)} English and "
        f"{len(LOW_VALUE_STRICT_SLUGS)} Spanish town pages"
    )
    print(f"Canonical English town inventory: {total}")
    print(
        "GSC export snapshot: "
        f"{snapshot['totals']['clicks']} clicks, "
        f"{snapshot['totals']['impressions']} impressions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
