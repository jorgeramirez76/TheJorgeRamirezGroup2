#!/usr/bin/env python3
"""Batch-fix audit-identified site issues.

Order of operations:
  1. Fix Spanish CSS paths — change ../css/styles.css → /css/styles.css
  2. Fix blog→ai-authority.html (was relative, should be /ai-authority.html)
  3. Fix blog→blog/ (was relative, should be /blog/)
  4. Fix /es//fonts.* double-slash bug
  5. Add /communities.html to sitemap-index.xml and sitemap.xml
  6. Update homepage navigation to add /communities.html link
  7. Add twitter:card to pages missing it
  8. Remove broken Ridgewood references
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).parent
CHANGES = []

def edit_file(p: Path, transform) -> bool:
    """Apply `transform(text) -> text` to p; return True if file changed."""
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


# ─── 1. Spanish CSS paths ────────────────────────────────────────────────────
def fix_spanish_css(text: str) -> str:
    # Replace any relative css/styles.css reference inside /es/* with absolute /css/styles.css
    text = re.sub(r'href="\.\./css/styles\.css"', 'href="/css/styles.css"', text)
    text = re.sub(r"href='\.\./css/styles\.css'", "href='/css/styles.css'", text)
    text = re.sub(r'href="css/styles\.css"', 'href="/css/styles.css"', text)
    text = re.sub(r"href='css/styles\.css'", "href='/css/styles.css'", text)
    return text


print("=== 1. Fixing Spanish CSS paths ===")
for p in (ROOT / "es").rglob("*.html"):
    edit_file(p, fix_spanish_css)
print(f"   Spanish CSS fixed in {len([c for c in CHANGES if c.startswith('es/')])} files")


# ─── 2. Blog→ai-authority.html ────────────────────────────────────────────────
def fix_blog_relative_links(text: str) -> str:
    # In blog posts, ai-authority.html should be /ai-authority.html (absolute)
    text = re.sub(r'href="ai-authority\.html"', 'href="/ai-authority.html"', text)
    text = re.sub(r"href='ai-authority\.html'", "href='/ai-authority.html'", text)
    # Same for blog/ which from /blog/foo.html resolves wrong
    text = re.sub(r'href="blog/"(?!\w)', 'href="/blog/"', text)
    text = re.sub(r"href='blog/'(?!\w)", "href='/blog/'", text)
    return text


print("\n=== 2. Fixing relative ai-authority/blog links in /blog/ posts ===")
blog_count_before = len(CHANGES)
for p in (ROOT / "blog").rglob("*.html"):
    edit_file(p, fix_blog_relative_links)
print(f"   Fixed in {len(CHANGES) - blog_count_before} blog files")


# ─── 3. Spanish double-slash + bare hostnames ─────────────────────────────────
def fix_es_double_slash(text: str) -> str:
    # /es//fonts.googleapis.com → https://fonts.googleapis.com
    text = re.sub(r'href="/es/+(fonts\.googleapis\.com[^"]*)"',
                  r'href="https://\1"', text)
    text = re.sub(r'href="/es/+(fonts\.gstatic\.com[^"]*)"',
                  r'href="https://\1"', text)
    return text


print("\n=== 3. Fixing /es// double-slash bugs ===")
es_dbl_before = len(CHANGES)
for p in (ROOT / "es").rglob("*.html"):
    edit_file(p, fix_es_double_slash)
print(f"   Fixed in {len(CHANGES) - es_dbl_before} files")


# ─── 4. Remove broken Ridgewood references ────────────────────────────────────
def fix_ridgewood(text: str) -> str:
    # Ridgewood is Bergen County (not in our 6) — links 404. Remove the link, keep the name.
    text = re.sub(r'<a[^>]*href="(?:\.\./)?towns/ridgewood\.html"[^>]*>([^<]*)</a>',
                  r'\1', text)
    return text


print("\n=== 4. Removing broken Ridgewood links ===")
rw_before = len(CHANGES)
for p in ROOT.rglob("*.html"):
    if "/.git/" in str(p):
        continue
    edit_file(p, fix_ridgewood)
print(f"   Fixed in {len(CHANGES) - rw_before} files")


# ─── 5. Add twitter:card to pages missing it ──────────────────────────────────
TWITTER_CARD_BLOCK = """
  <meta name="twitter:card" content="summary_large_image">"""


def add_twitter_card(text: str) -> str:
    # Skip if already has twitter:card
    if re.search(r'name=["\']twitter:card["\']', text):
        return text
    # Insert right before </head>, after existing meta block
    if "</head>" in text:
        # If there's an og:image or og:title, append after the last og:* meta
        og_matches = list(re.finditer(r'<meta\s+property=["\']og:[^>]+>', text))
        if og_matches:
            last = og_matches[-1]
            insert_at = last.end()
            text = text[:insert_at] + TWITTER_CARD_BLOCK + text[insert_at:]
        else:
            # No og:* — insert before </head>
            text = text.replace("</head>", TWITTER_CARD_BLOCK + "\n</head>", 1)
    return text


print("\n=== 5. Adding twitter:card to pages missing it ===")
tw_before = len(CHANGES)
for p in ROOT.rglob("*.html"):
    s = str(p)
    if any(x in s for x in ["/.git/", "node_modules", "_backup"]):
        continue
    edit_file(p, add_twitter_card)
print(f"   Added twitter:card to {len(CHANGES) - tw_before} files")


# ─── 6. Add /communities.html to sitemaps ─────────────────────────────────────
def add_to_sitemap(text: str, url: str, lastmod: str = "2026-04-29") -> str:
    if url in text:
        return text
    entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
"""
    return text.replace("</urlset>", entry + "</urlset>", 1)


print("\n=== 6. Adding /communities.html to sitemap.xml ===")
sitemap_path = ROOT / "sitemap.xml"
edit_file(sitemap_path, lambda t: add_to_sitemap(t, "https://thejorgeramirezgroup.com/communities.html"))

# Also add the previously missing pages found by audit
missing_pages = [
    "https://thejorgeramirezgroup.com/blog/",
    "https://thejorgeramirezgroup.com/blog/best-nj-towns-for-families.html",
    "https://thejorgeramirezgroup.com/blog/essex-county-real-estate-market-q2-2026.html",
    "https://thejorgeramirezgroup.com/blog/first-time-home-buyer-guide-new-jersey.html",
    "https://thejorgeramirezgroup.com/blog/morris-county-real-estate-market-q2-2026.html",
    "https://thejorgeramirezgroup.com/blog/nj-property-tax-guide-homeowners.html",
    "https://thejorgeramirezgroup.com/blog/selling-your-home-summit-nj-guide.html",
    "https://thejorgeramirezgroup.com/chatham-vs-madison-nj.html",
    "https://thejorgeramirezgroup.com/property-search.html",
    "https://thejorgeramirezgroup.com/westfield-vs-summit-nj.html",
]
for url in missing_pages:
    pages_local = url.replace("https://thejorgeramirezgroup.com", "")
    if (ROOT / pages_local.lstrip("/")).exists() or pages_local.endswith("/"):
        edit_file(sitemap_path, lambda t, u=url: add_to_sitemap(t, u))

print(f"   sitemap.xml updates: {sitemap_path in [ROOT / c for c in CHANGES]}")


# ─── 7. Update homepage nav to include /communities.html ──────────────────────
def update_homepage_nav(text: str) -> str:
    # Where the homepage uses <li><a href="#communities">Communities</a></li> —
    # change to point to the real page (preserves UX + adds SEO target)
    text = text.replace(
        '<li><a href="#communities">Communities</a></li>',
        '<li><a href="/communities.html">Communities</a></li>',
        1,
    )
    # In schema BreadcrumbList, fix the #communities reference too
    text = text.replace(
        '"item": "https://thejorgeramirezgroup.com/#communities"',
        '"item": "https://thejorgeramirezgroup.com/communities.html"',
    )
    text = text.replace(
        '"target": "https://thejorgeramirezgroup.com/#communities?q={search_term_string}"',
        '"target": "https://thejorgeramirezgroup.com/communities.html?q={search_term_string}"',
    )
    # Also footer "Explore All N Communities" link
    text = re.sub(
        r'<a href="#communities"[^>]*>(\s*Explore[^<]+)</a>',
        r'<a href="/communities.html">\1</a>',
        text,
    )
    text = re.sub(
        r'<a href="#communities"\s+class="resource-link">',
        r'<a href="/communities.html" class="resource-link">',
        text,
    )
    return text


print("\n=== 7. Updating homepage nav to /communities.html ===")
edit_file(ROOT / "index.html", update_homepage_nav)


print("\n=== Done ===")
print(f"Total files changed: {len(set(CHANGES))}")
print("Sample (first 20):")
for c in sorted(set(CHANGES))[:20]:
    print(f"  {c}")
