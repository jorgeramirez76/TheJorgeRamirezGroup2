#!/usr/bin/env python3
"""Third-wave fixes from deep audit."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).parent
CHANGES = []


def edit_file(p: Path, transform) -> bool:
    try:
        old = p.read_text()
    except Exception:
        return False
    new = transform(old)
    if new != old:
        p.write_text(new)
        CHANGES.append(str(p.relative_to(ROOT)))
        return True
    return False


# ─── 1. Fix Spanish image paths ───────────────────────────────────────────────
def fix_es_image_paths(text: str) -> str:
    text = re.sub(r'src="\.\./images/', 'src="/images/', text)
    text = re.sub(r"src='\.\./images/", "src='/images/", text)
    return text


print("=== 1. Fixing Spanish image paths ===")
n_before = len(CHANGES)
for p in (ROOT / "es").rglob("*.html"):
    edit_file(p, fix_es_image_paths)
print(f"   fixed: {len(CHANGES) - n_before} files")


# ─── 2. Add Google-Extended to robots.txt ─────────────────────────────────────
print("\n=== 2. Adding Google-Extended to robots.txt ===")
def add_google_extended(text: str) -> str:
    if "Google-Extended" in text:
        return text
    # Insert after the GPTBot block (last AI-bot block usually)
    addition = """
User-agent: Google-Extended
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot-User
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: cohere-ai
Allow: /

User-agent: Bytespider
Allow: /

User-agent: Diffbot
Allow: /
"""
    # Append at end
    return text.rstrip() + addition


edit_file(ROOT / "robots.txt", add_google_extended)


# ─── 3. Noindex the thin/redirect pages that have canonical pointing elsewhere ─
print("\n=== 3. Noindexing thin redirect pages with canonical-elsewhere ===")
THIN_REDIRECTS = [
    "blog/best-nj-towns-for-families.html",
    "blog/essex-county-real-estate-market-q2-2026.html",
    "blog/first-time-home-buyer-guide-new-jersey.html",
    "blog/morris-county-real-estate-market-q2-2026.html",
    "blog/nj-property-tax-guide-homeowners.html",
    "blog/selling-your-home-summit-nj-guide.html",
    "chatham-vs-madison-nj.html",
    "westfield-vs-summit-nj.html",
    "why-jorge-ramirez.html",
    "es/blog/first-time-home-buyer-guide-new-jersey.html",
    "es/why-jorge-ramirez.html",
]


def add_noindex(text: str) -> str:
    if 'name="robots"' in text:
        # Update existing robots meta
        return re.sub(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*["\']\s*/?>',
                      '<meta name="robots" content="noindex, follow">', text, count=1)
    # Insert new robots meta after canonical
    return re.sub(r'(<link\s+rel=["\']canonical["\'][^>]+>)',
                  r'\1\n  <meta name="robots" content="noindex, follow">', text, count=1)


for rel in THIN_REDIRECTS:
    p = ROOT / rel
    if p.exists():
        edit_file(p, add_noindex)
print(f"   noindexed: {len([c for c in CHANGES if c in THIN_REDIRECTS])}")


# ─── 4. Update communities/index.html canonical to match (it's a duplicate) ─
print("\n=== 4. Fixing communities/index.html canonical ===")


def fix_communities_index_canonical(text: str) -> str:
    # The /communities/index.html serves the same content but at /communities/ URL
    # Its canonical SHOULD point to /communities.html (the canonical) — that's already correct.
    # But we need to noindex this duplicate to avoid Google penalty
    if 'name="robots"' not in text:
        text = re.sub(r'(<link\s+rel=["\']canonical["\'][^>]+>)',
                      r'\1\n  <meta name="robots" content="noindex, follow">', text, count=1)
    return text


edit_file(ROOT / "communities" / "index.html", fix_communities_index_canonical)
edit_file(ROOT / "es" / "communities" / "index.html", fix_communities_index_canonical)


# ─── 5. Confirm the sitemap doesn't list the noindexed pages ──────────────────
print("\n=== 5. Removing noindexed pages from sitemap ===")
sitemap_p = ROOT / "sitemap.xml"
sitemap = sitemap_p.read_text()
removed = 0
for rel in THIN_REDIRECTS:
    if rel.startswith("es/"):
        continue  # ES pages are in sitemap-es.xml
    url = f"https://thejorgeramirezgroup.com/{rel}"
    pattern = re.compile(r'\s*<url>\s*<loc>' + re.escape(url) + r'</loc>.*?</url>\s*', re.S)
    new_sitemap = pattern.sub("\n", sitemap)
    if new_sitemap != sitemap:
        sitemap = new_sitemap
        removed += 1
# Also remove /communities/ duplicate if it's there
url = "https://thejorgeramirezgroup.com/communities/"
pattern = re.compile(r'\s*<url>\s*<loc>' + re.escape(url) + r'</loc>.*?</url>\s*', re.S)
new_sitemap = pattern.sub("\n", sitemap)
if new_sitemap != sitemap:
    sitemap = new_sitemap
    removed += 1
if removed > 0:
    sitemap_p.write_text(sitemap)
    CHANGES.append("sitemap.xml")
    print(f"   removed {removed} duplicate URLs from sitemap")


print(f"\n=== Done: {len(set(CHANGES))} files changed ===")
