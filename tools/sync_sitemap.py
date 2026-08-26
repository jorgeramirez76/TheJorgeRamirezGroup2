#!/usr/bin/env python3
"""Register missing, indexable English blog posts in ``sitemap.xml``.

Freshness is derived only from explicit page metadata. Filesystem timestamps
describe a deployment artifact, not necessarily a meaningful content update,
so an unknown or future page date is intentionally omitted from ``lastmod``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
ATTR_RE = re.compile(r"([:\w-]+)\s*=\s*([\"'])(.*?)\2", re.I | re.S)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def tag_attributes(tag: str) -> dict[str, str]:
    return {name.lower(): value.strip() for name, _, value in ATTR_RE.findall(tag)}


def meta_values(source: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for tag in re.findall(r"<meta\b[^>]*>", source, re.I | re.S):
        attrs = tag_attributes(tag)
        key = (attrs.get("property") or attrs.get("name") or "").lower()
        content = attrs.get("content", "").strip()
        if key and content:
            values.setdefault(key, []).append(content)
    return values


def valid_past_or_present_date(value: str, today: dt.date) -> str | None:
    candidate = value.strip()[:10]
    if not DATE_RE.fullmatch(candidate):
        return None
    try:
        parsed = dt.date.fromisoformat(candidate)
    except ValueError:
        return None
    return candidate if parsed <= today else None


def extract_lastmod(source: str, *, today: dt.date | None = None) -> str | None:
    """Return a truthful explicit content date, or ``None`` when unavailable."""
    today = today or dt.date.today()
    metas = meta_values(source)
    candidates = [
        *metas.get("article:modified_time", []),
        *re.findall(r'["\']dateModified["\']\s*:\s*["\']([^"\']+)', source, re.I),
        *metas.get("last-updated", []),
    ]
    for value in candidates:
        accepted = valid_past_or_present_date(value, today)
        if accepted:
            return accepted
    return None


def canonical_href(source: str) -> str | None:
    for tag in re.findall(r"<link\b[^>]*>", source, re.I | re.S):
        attrs = tag_attributes(tag)
        rel = attrs.get("rel", "").lower().split()
        if "canonical" in rel:
            return attrs.get("href", "").rstrip("/") or None
    return None


def is_noindex(source: str) -> bool:
    return any("noindex" in value.lower() for value in meta_values(source).get("robots", []))


def missing_blog_entries(
    *,
    root: Path = ROOT,
    today: dt.date | None = None,
) -> list[tuple[str, str | None]]:
    """Return deterministic ``(path, lastmod)`` records not yet submitted."""
    today = today or dt.date.today()
    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
    config = json.loads((root / "vercel.json").read_text(encoding="utf-8"))
    redirected = {
        item.get("source", "")
        for item in config.get("redirects", [])
        if not item.get("has")
    }

    entries: list[tuple[str, str | None]] = []
    for path in sorted((root / "blog").glob("*.html")):
        if path.name == "index.html":
            continue
        url = f"/blog/{path.stem}"
        if f"<loc>{SITE}{url}</loc>" in sitemap or url in redirected:
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        if is_noindex(source) or canonical_href(source) != f"{SITE}{url}":
            continue
        entries.append((url, extract_lastmod(source, today=today)))
    return entries


def render_entry(url: str, lastmod: str | None) -> str:
    loc = html.escape(f"{SITE}{url}", quote=True)
    lastmod_line = f"    <lastmod>{lastmod}</lastmod>\n" if lastmod else ""
    return (
        "  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"{lastmod_line}"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>0.7</priority>\n"
        "  </url>\n"
    )


def apply_entries(*, root: Path = ROOT, entries: list[tuple[str, str | None]]) -> int:
    """Append records atomically and return the number registered."""
    if not entries:
        return 0
    sitemap_path = root / "sitemap.xml"
    source = sitemap_path.read_text(encoding="utf-8")
    if source.count("</urlset>") != 1:
        raise RuntimeError("sitemap.xml must contain exactly one closing urlset tag")
    block = "".join(render_entry(url, lastmod) for url, lastmod in entries)
    updated = source.replace("</urlset>", block + "</urlset>", 1)
    temporary = sitemap_path.with_suffix(".xml.tmp")
    temporary.write_text(updated, encoding="utf-8")
    temporary.replace(sitemap_path)
    return len(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="report missing entries without changing sitemap.xml (default)",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="register reviewed entries; this is never selected by the daily job",
    )
    args = parser.parse_args(argv)
    entries = missing_blog_entries(root=ROOT)
    if not entries:
        print("sitemap in sync")
        return 0
    if not args.apply:
        for url, lastmod in entries:
            date_note = lastmod or "lastmod omitted (no valid explicit date)"
            print(f"missing {url} — {date_note}")
        return 1
    apply_entries(root=ROOT, entries=entries)
    for url, lastmod in entries:
        date_note = f" lastmod={lastmod}" if lastmod else " without lastmod"
        print(f"added {url}{date_note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
