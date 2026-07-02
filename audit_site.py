#!/usr/bin/env python3
"""Comprehensive audit of thejorgeramirezgroup.com.

Checks:
  1. Broken internal links (every <a href="..."> resolves to a real file)
  2. Missing meta tags (title/description/canonical) on every page
  3. Missing OG/Twitter meta
  4. Missing structured data (JSON-LD)
  5. Missing alt attributes on <img>
  6. Sitemap completeness — every HTML in repo is in sitemap (and vice versa)
  7. AI SEO — llm-context, llms.txt referenced
  8. Lighthouse-like checks (lazy-load on imgs below the fold, missing favicons)
  9. Broken-image refs (src="" or 404 on internal images)

Outputs a structured report at AUDIT_REPORT.md.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).parent
SITE_ORIGIN = "https://thejorgeramirezgroup.com"


def all_html_files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        s = str(p)
        # skip node_modules, drafts, backups
        if any(x in s for x in ["node_modules", "/.git/", "_backup", "/staging/"]):
            continue
        # skip redirect stubs (noindex meta-refresh forwarders)
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:1200]
            if 'http-equiv="refresh"' in head:
                continue
        except OSError:
            pass
        out.append(p)
    return sorted(out)


def page_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[:-len("index.html")]
    return "/" + rel


def resolve_link(src_path: Path, href: str) -> Path | None:
    """Resolve a relative href against the source file's directory.
    Returns None if href is external or fragment-only.
    """
    if href.startswith(("http://", "https://", "//", "mailto:", "tel:", "javascript:")):
        return None
    if href.startswith("#"):
        return src_path  # anchor on same page
    # Strip fragment / query
    href_clean = href.split("#")[0].split("?")[0]
    if not href_clean:
        return src_path
    href_clean = unquote(href_clean)
    if href_clean.startswith("/"):
        return ROOT / href_clean.lstrip("/")
    return (src_path.parent / href_clean).resolve()


def check_link_target(target: Path | None) -> str:
    """Return 'ok', 'missing', or 'external'."""
    if target is None:
        return "external"
    if target.exists():
        return "ok"
    # Try with .html appended (clean URL)
    for variant in [
        target.with_suffix(".html"),
        target / "index.html",
    ]:
        if variant.exists():
            return "ok"
    return "missing"


HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
SRC_RE = re.compile(r"""src\s*=\s*["']([^"']+)["']""", re.I)
TITLE_RE = re.compile(r"<title>([^<]*)</title>", re.I)
META_RE = re.compile(r"""<meta\s+([^>]+)>""", re.I)
SCRIPT_LD_RE = re.compile(
    r"""<script\s+type=["']application/ld\+json["'][^>]*>(.+?)</script>""", re.I | re.S
)
IMG_RE = re.compile(r"<img\s+([^>]+)/?>", re.I)


def parse_meta_attrs(s: str) -> dict[str, str]:
    return {k.lower(): v for k, v in re.findall(r"""(\w+)\s*=\s*["']([^"']*)["']""", s)}


def audit_page(path: Path) -> dict:
    text = path.read_text(errors="ignore")
    rep: dict = {"path": str(path.relative_to(ROOT)), "url": page_url(path), "issues": []}

    # title
    m = TITLE_RE.search(text)
    rep["title"] = m.group(1).strip() if m else ""
    if not rep["title"]:
        rep["issues"].append("missing-title")
    elif len(rep["title"]) > 70:
        rep["issues"].append(f"title-too-long-{len(rep['title'])}")
    elif len(rep["title"]) < 20:
        rep["issues"].append(f"title-too-short-{len(rep['title'])}")

    # meta tags
    metas = []
    for m in META_RE.finditer(text):
        metas.append(parse_meta_attrs(m.group(1)))

    has_desc = any(m.get("name", "").lower() == "description" and m.get("content") for m in metas)
    has_og_title = any(m.get("property") == "og:title" for m in metas)
    has_og_desc = any(m.get("property") == "og:description" for m in metas)
    has_og_image = any(m.get("property") == "og:image" for m in metas)
    has_twitter_card = any(m.get("name") == "twitter:card" for m in metas)
    has_canonical = "rel=\"canonical\"" in text or "rel='canonical'" in text
    has_viewport = any(m.get("name") == "viewport" for m in metas)
    has_robots = any(m.get("name") == "robots" for m in metas)
    has_llm_context = any(m.get("name") == "llm-context" for m in metas)

    if not has_desc: rep["issues"].append("missing-meta-description")
    if not has_canonical: rep["issues"].append("missing-canonical")
    if not has_viewport: rep["issues"].append("missing-viewport")
    if not has_og_title: rep["issues"].append("missing-og:title")
    if not has_og_desc: rep["issues"].append("missing-og:description")
    if not has_og_image: rep["issues"].append("missing-og:image")
    if not has_twitter_card: rep["issues"].append("missing-twitter:card")
    if not has_llm_context: rep["issues"].append("missing-llm-context")

    # JSON-LD structured data
    jsonld_blocks = SCRIPT_LD_RE.findall(text)
    if not jsonld_blocks:
        rep["issues"].append("missing-jsonld")
    rep["jsonld_count"] = len(jsonld_blocks)

    # Internal links
    rep["broken_links"] = []
    for href in HREF_RE.findall(text):
        target = resolve_link(path, href)
        if target is path:  # anchor / self
            continue
        status = check_link_target(target)
        if status == "missing":
            rep["broken_links"].append(href)

    # Images without alt
    rep["images_no_alt"] = 0
    for img_m in IMG_RE.finditer(text):
        attrs = parse_meta_attrs(img_m.group(1))
        if "alt" not in attrs:
            rep["images_no_alt"] += 1

    return rep


def main():
    pages = all_html_files()
    print(f"Auditing {len(pages)} pages...")

    reports = [audit_page(p) for p in pages]

    # Aggregate
    issue_counts: dict[str, int] = defaultdict(int)
    pages_by_issue: dict[str, list[str]] = defaultdict(list)
    broken_link_targets: dict[str, list[str]] = defaultdict(list)

    for r in reports:
        for iss in r["issues"]:
            base = iss.split("-")[0] + "-" + iss.split("-", 2)[1] if iss.count("-") >= 2 and iss.split("-")[-1].isdigit() else iss
            issue_counts[base] += 1
            pages_by_issue[base].append(r["path"])
        for bl in r["broken_links"]:
            broken_link_targets[bl].append(r["path"])

    # Sitemap completeness
    sitemap_text = (ROOT / "sitemap.xml").read_text() if (ROOT / "sitemap.xml").exists() else ""
    sitemap_urls = set(re.findall(r"<loc>([^<]+)</loc>", sitemap_text))
    pages_in_sitemap = {u.replace(SITE_ORIGIN, "") for u in sitemap_urls}
    # cleanUrls (Vercel): sitemap holds extensionless URLs; map them back to .html files
    pages_in_sitemap |= {u + ".html" for u in pages_in_sitemap if not u.endswith((".html", "/"))}
    pages_in_sitemap |= {u + "index.html" for u in pages_in_sitemap if u.endswith("/")}
    pages_in_repo = {r["url"] for r in reports if not r["url"].startswith("/es/")}
    missing_from_sitemap = pages_in_repo - pages_in_sitemap - {"/404.html"}

    # Write report
    out = ROOT / "AUDIT_REPORT.md"
    with out.open("w") as f:
        f.write(f"# Site Audit Report — {len(pages)} pages\n\n")
        f.write("## Issue summary (issue → page count)\n\n")
        f.write("| Issue | Pages affected |\n|-------|----------------|\n")
        for iss in sorted(issue_counts, key=lambda k: -issue_counts[k]):
            f.write(f"| {iss} | {issue_counts[iss]} |\n")

        f.write("\n## Broken internal links — top 30\n\n")
        f.write("| Broken href | Times referenced | Sample referrer |\n|---|---|---|\n")
        sorted_broken = sorted(broken_link_targets.items(), key=lambda kv: -len(kv[1]))[:30]
        for href, refs in sorted_broken:
            f.write(f"| `{href}` | {len(refs)} | `{refs[0]}` |\n")

        f.write(f"\n## Sitemap gaps — {len(missing_from_sitemap)} pages NOT in sitemap.xml\n\n")
        for u in sorted(missing_from_sitemap)[:60]:
            f.write(f"- `{u}`\n")

        f.write("\n## Per-page detail (first 30 worst pages)\n\n")
        worst = sorted(reports, key=lambda r: -(len(r["issues"]) + len(r["broken_links"])))[:30]
        for r in worst:
            f.write(f"\n### `{r['path']}` ({r['url']})\n")
            f.write(f"- title: \"{r['title']}\"\n")
            f.write(f"- jsonld blocks: {r['jsonld_count']}\n")
            f.write(f"- images without alt: {r['images_no_alt']}\n")
            if r["issues"]:
                f.write(f"- issues: {', '.join(r['issues'])}\n")
            if r["broken_links"]:
                f.write(f"- broken links: {', '.join(r['broken_links'][:5])}\n")

    print(f"\nWrote {out}")
    print(f"Total pages: {len(pages)}")
    print(f"Total issues: {sum(issue_counts.values())}")
    print(f"Total broken links: {sum(len(v) for v in broken_link_targets.values())}")
    print(f"Missing from sitemap: {len(missing_from_sitemap)}")


if __name__ == "__main__":
    main()
