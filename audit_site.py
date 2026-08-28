#!/usr/bin/env python3
"""Audit the public, indexable surface of thejorgeramirezgroup.com.

The repository intentionally contains redirect fallbacks, noindex pages, and
internal publishing templates. Those files still matter operationally, but they
must not be graded as indexable landing pages or treated as sitemap omissions.

Checks:
  1. Indexable-page title, description, canonical, social metadata and JSON-LD
  2. Internal links and image references on indexable pages
  3. Image alt attributes
  4. Exact EN/ES sitemap coverage for self-canonical indexable pages
  5. Redirect/noindex/canonicalized-file classification
  6. AI/GEO context metadata on indexable pages

The Markdown report is written to ``AUDIT_REPORT.md`` by default. Use
``--check`` to return a non-zero status when actionable defects remain.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).parent.resolve()
SITE_ORIGIN = "https://thejorgeramirezgroup.com"
LOCAL_HOSTS = {"thejorgeramirezgroup.com", "www.thejorgeramirezgroup.com"}

# These directories are excluded from the Vercel deployment or contain source
# material rather than public pages. Public redirect files under ``tools/`` are
# intentionally not excluded.
INTERNAL_SOURCE_PREFIXES = (
    ".vercel/",
    "tests/",
    "scripts/",
    "data/",
    "crm/",
    "docs/",
    "lead-research/",
    "property-leads-system/",
    "tools/blog-automation/",
    "tools/seo-optimizer/",
    "tmp/",
)

HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
TITLE_RE = re.compile(r"<title>([^<]*)</title>", re.I)
META_RE = re.compile(r"""<meta\s+([^>]+)>""", re.I)
LINK_RE = re.compile(r"""<link\s+([^>]+)>""", re.I)
SCRIPT_LD_RE = re.compile(
    r"""<script\s+type=["']application/ld\+json["'][^>]*>(.+?)</script>""",
    re.I | re.S,
)
IMG_RE = re.compile(r"<img\s+([^>]+)/?>", re.I)
ATTR_RE = re.compile(r"""([:\w-]+)\s*=\s*["']([^"']*)["']""", re.I)


def parse_meta_attrs(source: str) -> dict[str, str]:
    return {key.lower(): value for key, value in ATTR_RE.findall(source)}


def is_internal_source(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return rel.startswith(INTERNAL_SOURCE_PREFIXES) or any(
        token in rel for token in ("node_modules/", "/.git/", "_backup", "/staging/")
    )


def all_html_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*.html") if not is_internal_source(path))


def clean_route(path: Path) -> str:
    """Return the Vercel clean-URL route for a repository HTML file."""
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("/index.html")]
    if rel.endswith(".html"):
        rel = rel[:-5]
    return "/" + rel


def normalize_route(url_or_path: str) -> str:
    """Normalize a same-site URL or path to its clean route."""
    parsed = urlparse(url_or_path)
    path = parsed.path if parsed.scheme or parsed.netloc else url_or_path.split("#", 1)[0].split("?", 1)[0]
    path = unquote(path or "/")
    if not path.startswith("/"):
        path = "/" + path
    if path.endswith("/index.html"):
        path = path[: -len("/index.html")]
    elif path.endswith(".html"):
        path = path[:-5]
    if len(path) > 1:
        path = path.rstrip("/")
    return path or "/"


def load_redirect_sources() -> set[str]:
    config_path = ROOT / "vercel.json"
    if not config_path.exists():
        return set()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    routes: set[str] = set()
    for entry in config.get("redirects", []):
        source = entry.get("source", "")
        # Host-conditional canonicalization rules do not redirect the apex-host
        # page represented by a local HTML file.
        if entry.get("has") or entry.get("missing"):
            continue
        # Dynamic patterns cannot correspond to a single checked HTML file.
        if source and not any(char in source for char in (":", "*", "(", ")")):
            normalized = normalize_route(source)
            # A raw compatibility address such as ``/page.html`` or
            # ``/directory/index.html`` can redirect while its clean route is
            # still served. Only an exact clean-form source retires that clean
            # route from the indexable surface. Paired clean/.html migrations
            # remain redirects because their clean source is present too.
            if source == normalized:
                routes.add(normalized)
    return routes


def resolve_link(src_path: Path, href: str) -> Path | None:
    """Resolve a relative href; return None for external or script-only URLs."""
    if href.startswith(("mailto:", "tel:", "sms:", "javascript:", "data:")):
        return None
    if "${" in href or "{{" in href:
        return None
    parsed = urlparse(href if not href.startswith("//") else "https:" + href)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc.lower() not in LOCAL_HOSTS:
            return None
        clean = unquote(parsed.path or "/")
        return ROOT / clean.lstrip("/")
    if href.startswith("#"):
        return src_path
    clean = unquote(href.split("#", 1)[0].split("?", 1)[0])
    if not clean:
        return src_path
    if clean.startswith("/"):
        return ROOT / clean.lstrip("/")
    return (src_path.parent / clean).resolve()


def route_for_target(target: Path) -> str | None:
    try:
        rel = target.relative_to(ROOT).as_posix()
    except ValueError:
        return None
    if not rel:
        return "/"
    return normalize_route("/" + rel)


def check_link_target(target: Path | None, redirect_sources: set[str]) -> str:
    """Return ``ok``, ``missing`` or ``external`` for an internal target."""
    if target is None:
        return "external"
    try:
        target.relative_to(ROOT)
    except ValueError:
        return "missing"
    if target.exists():
        return "ok"
    variants = (target.with_suffix(".html"), target / "index.html")
    if any(variant.exists() for variant in variants):
        return "ok"
    route = route_for_target(target)
    if route and route in redirect_sources:
        return "ok"
    return "missing"


def target_html_file(target: Path) -> Path | None:
    """Return the repository HTML file represented by an internal clean URL."""
    candidates = (target, target.with_suffix(".html"), target / "index.html")
    for candidate in candidates:
        if candidate.is_file() and candidate.suffix.lower() == ".html":
            return candidate
    return None


def fragment_exists(target: Path, fragment: str) -> bool:
    """Check a same-page or cross-page HTML fragment against id/name attributes."""
    if not fragment:
        return True
    html_path = target_html_file(target)
    if html_path is None:
        return True
    text = html_path.read_text(encoding="utf-8", errors="replace")
    wanted = unquote(fragment)
    return bool(
        re.search(
            rf"(?:id|name)\s*=\s*([\"']){re.escape(wanted)}\1",
            text,
            flags=re.I,
        )
    )


def canonical_href(text: str) -> str:
    for match in LINK_RE.finditer(text):
        attrs = parse_meta_attrs(match.group(1))
        if "canonical" in attrs.get("rel", "").lower().split():
            return attrs.get("href", "")
    return ""


def meta_values(text: str) -> list[dict[str, str]]:
    return [parse_meta_attrs(match.group(1)) for match in META_RE.finditer(text)]


def has_noindex(metas: list[dict[str, str]]) -> bool:
    return any(
        meta.get("name", "").lower() in {"robots", "googlebot"}
        and "noindex" in meta.get("content", "").lower()
        for meta in metas
    )


def has_meta_refresh(metas: list[dict[str, str]]) -> bool:
    return any(meta.get("http-equiv", "").lower() == "refresh" for meta in metas)


def audit_page(path: Path, redirect_sources: set[str]) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    route = clean_route(path)
    metas = meta_values(text)
    canonical = canonical_href(text)
    canonical_route = normalize_route(canonical) if canonical else ""
    redirected = route in redirect_sources or has_meta_refresh(metas)
    noindex = has_noindex(metas)
    canonicalized = bool(canonical_route and canonical_route != route)
    indexable = not redirected and not noindex and not canonicalized and path.name != "404.html"

    if redirected:
        classification = "redirect"
    elif noindex or path.name == "404.html":
        classification = "noindex"
    elif canonicalized:
        classification = "canonicalized"
    else:
        classification = "indexable"

    report: dict = {
        "path": str(path.relative_to(ROOT)),
        "url": route,
        "canonical": canonical,
        "classification": classification,
        "indexable": indexable,
        "issues": [],
        "broken_links": [],
        "broken_images": [],
        "images_no_alt": 0,
    }

    title_match = TITLE_RE.search(text)
    report["title"] = title_match.group(1).strip() if title_match else ""
    jsonld_blocks = SCRIPT_LD_RE.findall(text)
    report["jsonld_count"] = len(jsonld_blocks)

    # Full SEO/GEO requirements apply only to pages intended for indexing.
    if indexable:
        if not report["title"]:
            report["issues"].append("missing-title")
        elif len(report["title"]) > 70:
            report["issues"].append(f"title-too-long-{len(report['title'])}")
        elif len(report["title"]) < 20:
            report["issues"].append(f"title-too-short-{len(report['title'])}")

        def has_meta(key: str, value: str) -> bool:
            return any(meta.get(key, "").lower() == value and meta.get("content") for meta in metas)

        if not has_meta("name", "description"):
            report["issues"].append("missing-meta-description")
        if not canonical:
            report["issues"].append("missing-canonical")
        elif canonical_route != route:
            report["issues"].append("non-self-canonical")
        if not has_meta("name", "viewport"):
            report["issues"].append("missing-viewport")
        if not has_meta("property", "og:title"):
            report["issues"].append("missing-og:title")
        if not has_meta("property", "og:description"):
            report["issues"].append("missing-og:description")
        if not has_meta("property", "og:image"):
            report["issues"].append("missing-og:image")
        if not has_meta("name", "twitter:card"):
            report["issues"].append("missing-twitter:card")
        if not has_meta("name", "llm-context"):
            report["issues"].append("missing-llm-context")
        if not jsonld_blocks:
            report["issues"].append("missing-jsonld")
        else:
            for block in jsonld_blocks:
                try:
                    json.loads(block)
                except json.JSONDecodeError:
                    report["issues"].append("invalid-jsonld")
                    break

        for href in HREF_RE.findall(text):
            target = resolve_link(path, href)
            status = check_link_target(target, redirect_sources)
            if status == "missing":
                report["broken_links"].append(href)
                continue
            fragment = urlparse(href if not href.startswith("//") else "https:" + href).fragment
            route = route_for_target(target) if target is not None else None
            if target is not None and route not in redirect_sources and not fragment_exists(target, fragment):
                report["broken_links"].append(f"{href} (missing fragment)")

        for image_match in IMG_RE.finditer(text):
            attrs = parse_meta_attrs(image_match.group(1))
            if "alt" not in attrs:
                report["images_no_alt"] += 1
            source = attrs.get("src", "")
            if source:
                target = resolve_link(path, source)
                if target is not None and not target.exists():
                    report["broken_images"].append(source)

    return report


def issue_key(issue: str) -> str:
    return re.sub(r"-(\d+)$", "", issue)


def read_sitemap(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [normalize_route(value) for value in re.findall(r"<loc>([^<]+)</loc>", path.read_text(encoding="utf-8"))]


def build_audit() -> dict:
    redirect_sources = load_redirect_sources()
    pages = all_html_files()
    reports = [audit_page(path, redirect_sources) for path in pages]

    # Vercel clean URLs and conventional static previews can intentionally use
    # two physical files for one route. Identical mirrors are counted once;
    # divergent files are a deployment ambiguity and therefore actionable.
    by_route: dict[str, list[dict]] = defaultdict(list)
    for report in reports:
        if report["indexable"]:
            by_route[report["url"]].append(report)
    route_aliases: dict[str, list[str]] = {}
    conflicting_route_files: dict[str, list[str]] = {}
    for route, group in by_route.items():
        if len(group) < 2:
            continue
        paths = [ROOT / report["path"] for report in group]
        digests = {hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        names = sorted(report["path"] for report in group)
        if len(digests) == 1:
            route_aliases[route] = names
            primary = min(group, key=lambda report: (report["path"].endswith("/index.html"), report["path"]))
            for report in group:
                if report is primary:
                    continue
                report["classification"] = "route-alias"
                report["indexable"] = False
                report["issues"] = []
                report["broken_links"] = []
                report["broken_images"] = []
        else:
            conflicting_route_files[route] = names

    issue_counts: dict[str, int] = defaultdict(int)
    broken_link_targets: dict[str, list[str]] = defaultdict(list)
    broken_image_targets: dict[str, list[str]] = defaultdict(list)
    for report in reports:
        for issue in report["issues"]:
            issue_counts[issue_key(issue)] += 1
        for href in report["broken_links"]:
            broken_link_targets[href].append(report["path"])
        for source in report["broken_images"]:
            broken_image_targets[source].append(report["path"])

    en_sitemap = read_sitemap(ROOT / "sitemap.xml")
    es_sitemap = read_sitemap(ROOT / "sitemap-es.xml")
    sitemap_routes = set(en_sitemap) | set(es_sitemap)
    expected_routes = {report["url"] for report in reports if report["indexable"]}
    missing_from_sitemap = expected_routes - sitemap_routes
    stale_in_sitemap = sitemap_routes - expected_routes
    duplicate_sitemap_routes = sorted(
        route for route in sitemap_routes if en_sitemap.count(route) + es_sitemap.count(route) > 1
    )
    wrong_locale_sitemap = sorted(
        {route for route in en_sitemap if route.startswith("/es/") or route == "/es"}
        | {route for route in es_sitemap if not (route.startswith("/es/") or route == "/es")}
    )

    classifications: dict[str, int] = defaultdict(int)
    for report in reports:
        classifications[report["classification"]] += 1

    actionable_count = (
        sum(issue_counts.values())
        + sum(len(refs) for refs in broken_link_targets.values())
        + sum(len(refs) for refs in broken_image_targets.values())
        + len(missing_from_sitemap)
        + len(stale_in_sitemap)
        + len(duplicate_sitemap_routes)
        + len(wrong_locale_sitemap)
        + len(conflicting_route_files)
    )
    return {
        "pages": pages,
        "reports": reports,
        "classifications": dict(classifications),
        "issue_counts": dict(issue_counts),
        "broken_link_targets": broken_link_targets,
        "broken_image_targets": broken_image_targets,
        "missing_from_sitemap": missing_from_sitemap,
        "stale_in_sitemap": stale_in_sitemap,
        "duplicate_sitemap_routes": duplicate_sitemap_routes,
        "wrong_locale_sitemap": wrong_locale_sitemap,
        "route_aliases": route_aliases,
        "conflicting_route_files": conflicting_route_files,
        "actionable_count": actionable_count,
    }


def write_report(audit: dict, output: Path) -> None:
    reports = audit["reports"]
    indexable_count = audit["classifications"].get("indexable", 0)
    with output.open("w", encoding="utf-8") as handle:
        handle.write(f"# Site Audit Report — {indexable_count} indexable pages\n\n")
        handle.write(f"Public HTML files classified: {len(audit['pages'])}.\n\n")
        handle.write("## Surface classification\n\n")
        handle.write("| Classification | Files |\n|---|---:|\n")
        for label in ("indexable", "route-alias", "redirect", "noindex", "canonicalized"):
            handle.write(f"| {label} | {audit['classifications'].get(label, 0)} |\n")

        handle.write("\n## Actionable issue summary\n\n")
        handle.write("| Issue | Pages affected |\n|---|---:|\n")
        if not audit["issue_counts"]:
            handle.write("| None | 0 |\n")
        else:
            for issue in sorted(audit["issue_counts"], key=lambda item: (-audit["issue_counts"][item], item)):
                handle.write(f"| {issue} | {audit['issue_counts'][issue]} |\n")

        handle.write("\n## Broken internal links\n\n")
        if not audit["broken_link_targets"]:
            handle.write("None.\n")
        else:
            handle.write("| Broken href | References | Sample referrer |\n|---|---:|---|\n")
            for href, refs in sorted(audit["broken_link_targets"].items(), key=lambda item: (-len(item[1]), item[0])):
                handle.write(f"| `{href}` | {len(refs)} | `{refs[0]}` |\n")

        handle.write("\n## Broken internal images\n\n")
        if not audit["broken_image_targets"]:
            handle.write("None.\n")
        else:
            handle.write("| Broken src | References | Sample referrer |\n|---|---:|---|\n")
            for source, refs in sorted(audit["broken_image_targets"].items(), key=lambda item: (-len(item[1]), item[0])):
                handle.write(f"| `{source}` | {len(refs)} | `{refs[0]}` |\n")

        for heading, key in (
            ("Missing from sitemap", "missing_from_sitemap"),
            ("Stale or non-indexable sitemap routes", "stale_in_sitemap"),
            ("Duplicate sitemap routes", "duplicate_sitemap_routes"),
            ("Routes in the wrong language sitemap", "wrong_locale_sitemap"),
            ("Conflicting physical files for one clean route", "conflicting_route_files"),
        ):
            values = sorted(audit[key])
            handle.write(f"\n## {heading} — {len(values)}\n\n")
            handle.write("None.\n" if not values else "".join(f"- `{value}`\n" for value in values))

        handle.write(f"\n## Verified identical route aliases — {len(audit['route_aliases'])}\n\n")
        if not audit["route_aliases"]:
            handle.write("None.\n")
        else:
            for route, paths in sorted(audit["route_aliases"].items()):
                handle.write(f"- `{route}`: " + ", ".join(f"`{path}`" for path in paths) + "\n")

        handle.write("\n## Per-page detail\n\n")
        worst = sorted(
            (report for report in reports if report["issues"] or report["broken_links"] or report["broken_images"]),
            key=lambda report: (-(len(report["issues"]) + len(report["broken_links"]) + len(report["broken_images"])), report["path"]),
        )
        if not worst:
            handle.write("No actionable page-level defects.\n")
        for report in worst:
            handle.write(f"\n### `{report['path']}` ({report['url']})\n")
            handle.write(f"- classification: {report['classification']}\n")
            handle.write(f"- title: \"{report['title']}\"\n")
            if report["issues"]:
                handle.write(f"- issues: {', '.join(report['issues'])}\n")
            if report["broken_links"]:
                handle.write(f"- broken links: {', '.join(report['broken_links'])}\n")
            if report["broken_images"]:
                handle.write(f"- broken images: {', '.join(report['broken_images'])}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 when actionable defects remain")
    parser.add_argument("--output", type=Path, default=ROOT / "AUDIT_REPORT.md")
    args = parser.parse_args()

    audit = build_audit()
    write_report(audit, args.output)
    print(f"Audited {len(audit['pages'])} public HTML files")
    print(f"Indexable pages: {audit['classifications'].get('indexable', 0)}")
    print(f"Actionable defects: {audit['actionable_count']}")
    print(f"Wrote {args.output}")
    return 1 if args.check and audit["actionable_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
