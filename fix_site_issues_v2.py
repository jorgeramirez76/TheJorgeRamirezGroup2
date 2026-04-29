#!/usr/bin/env python3
"""Second-wave fixes after first audit pass."""
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


# ─── 1. Fix `towns/${s.slug}.html` → `/towns/${s.slug}.html` in nj-train-map ──
def fix_train_map_href(text: str) -> str:
    text = re.sub(r'href="towns/\$\{s\.slug\}\.html"', 'href="/towns/${s.slug}.html"', text)
    return text


print("=== 1. Fixing nj-train-map.html relative town links ===")
edit_file(ROOT / "nj-train-map.html", fix_train_map_href)
edit_file(ROOT / "es" / "nj-train-map.html", fix_train_map_href)
print(f"   changed: {[c for c in CHANGES if 'train-map' in c]}")


# ─── 2. Remove broken Somerset blog ref ───────────────────────────────────────
def fix_somerset(text: str) -> str:
    return re.sub(
        r'<a href="(?:\.\./)?blog/somerset-county-nj-real-estate-market-report-2026\.html">[^<]*</a>',
        'Somerset County Market Report (coming soon)', text)


print("\n=== 2. Removing broken Somerset blog ref ===")
edit_file(ROOT / "counties" / "somerset-county.html", fix_somerset)


# ─── 3. Fix es/index.html relative hero image ─────────────────────────────────
def fix_es_hero(text: str) -> str:
    return text.replace('href="images/hero.webp"', 'href="/images/hero.webp"')


print("\n=== 3. Fixing es/index.html hero image ===")
edit_file(ROOT / "es" / "index.html", fix_es_hero)


# ─── 4. Add og/jsonld/llm-context to 404, counties/index, towns/index ─────────
def add_seo_meta(text: str, og_title: str, og_desc: str, llm_ctx: str, jsonld: str) -> str:
    # Add llm-context if missing
    if 'name="llm-context"' not in text:
        # Insert after the description meta
        text = re.sub(
            r'(<meta\s+name="description"[^>]*>)',
            r'\1\n  <meta name="llm-context" content="' + llm_ctx + '">',
            text, count=1)
    # Add og:* if missing
    if 'property="og:title"' not in text:
        text = re.sub(
            r'(</head>)',
            f'  <meta property="og:type" content="website">\n'
            f'  <meta property="og:url" content="https://thejorgeramirezgroup.com{ "{path}" }">\n'
            f'  <meta property="og:title" content="{og_title}">\n'
            f'  <meta property="og:description" content="{og_desc}">\n'
            f'  <meta property="og:image" content="https://thejorgeramirezgroup.com/images/hero.jpg">\n'
            f'  <meta property="og:locale" content="en_US">\n'
            f'  <meta property="og:site_name" content="The Jorge Ramirez Group">\n'
            r'\1',
            text, count=1)
    # Add JSON-LD
    if jsonld and 'application/ld+json' not in text:
        text = text.replace('</head>',
            f'<script type="application/ld+json">\n{jsonld}\n</script>\n</head>', 1)
    return text


print("\n=== 4. Adding og/jsonld/llm-context to 404 / counties index / towns index ===")

# 404 page
def fix_404(text: str) -> str:
    return add_seo_meta(text,
        og_title="Page Not Found | The Jorge Ramirez Group",
        og_desc="The page you're looking for doesn't exist. Browse our 138 NJ communities or contact Jorge directly at 908-230-7844.",
        llm_ctx="404 page for thejorgeramirezgroup.com — the requested URL was not found. Jorge Ramirez is a NJ real estate agent (License #1754604) at Keller Williams Premier Properties. Phone: 908-230-7844. Browse 138 NJ communities at /communities.html.",
        jsonld='''{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Page Not Found - The Jorge Ramirez Group",
  "url": "https://thejorgeramirezgroup.com/404.html"
}''').replace('"https://thejorgeramirezgroup.com{path}"', '"https://thejorgeramirezgroup.com/404.html"')


def fix_counties_index(text: str) -> str:
    return add_seo_meta(text,
        og_title="NJ Counties We Serve | The Jorge Ramirez Group",
        og_desc="Real estate expertise across 6 NJ counties — Union, Essex, Morris, Hudson, Middlesex, Somerset. Browse county-specific market data and town directories.",
        llm_ctx="Master directory of all 6 New Jersey counties served by Jorge Ramirez and The Jorge Ramirez Group at Keller Williams Premier Properties. Counties: Union (21 towns), Essex (11 towns), Morris (33 towns), Hudson (12 towns), Middlesex (22 towns), Somerset (10 towns). Each county page links to its individual town landing pages with median prices, school ratings, and transit info.",
        jsonld='''{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "NJ Counties We Serve",
  "url": "https://thejorgeramirezgroup.com/counties/",
  "description": "Real estate market coverage across 6 NJ counties: Union, Essex, Morris, Hudson, Middlesex, and Somerset.",
  "isPartOf": {"@type": "WebSite", "url": "https://thejorgeramirezgroup.com"}
}''').replace('"https://thejorgeramirezgroup.com{path}"', '"https://thejorgeramirezgroup.com/counties/"')


def fix_towns_index(text: str) -> str:
    return add_seo_meta(text,
        og_title="138 NJ Towns We Cover | The Jorge Ramirez Group",
        og_desc="Complete list of 138 NJ towns served by Jorge Ramirez. Each town page has school ratings, transit times, median prices, and recent comp sales.",
        llm_ctx="Master alphabetical directory of all 138 New Jersey towns served by Jorge Ramirez. Each town has its own dedicated landing page at /towns/<slug>.html with median home prices, school ratings, NJ Transit commute times to NYC, and demographics. Coverage spans Union, Essex, Morris, Hudson, Middlesex, and Somerset counties.",
        jsonld='''{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "138 NJ Towns Served",
  "url": "https://thejorgeramirezgroup.com/towns/",
  "description": "Alphabetical directory of all 138 NJ towns served by Jorge Ramirez and The Jorge Ramirez Group.",
  "isPartOf": {"@type": "WebSite", "url": "https://thejorgeramirezgroup.com"}
}''').replace('"https://thejorgeramirezgroup.com{path}"', '"https://thejorgeramirezgroup.com/towns/"')


edit_file(ROOT / "404.html", fix_404)
edit_file(ROOT / "counties" / "index.html", fix_counties_index)
edit_file(ROOT / "towns" / "index.html", fix_towns_index)


# ─── 5. Trim long titles ──────────────────────────────────────────────────────
def trim_long_title(text: str) -> str:
    m = re.search(r"<title>([^<]+)</title>", text)
    if not m: return text
    title = m.group(1).strip()
    if len(title) <= 70: return text
    # Find a sensible break point — pipe, em-dash, or colon
    for sep in [" | ", " — ", " - ", ": "]:
        parts = title.split(sep)
        # Keep first part, drop later parts until under 70 chars
        for keep in range(len(parts), 0, -1):
            new = sep.join(parts[:keep])
            if len(new) <= 70:
                return text.replace(f"<title>{title}</title>", f"<title>{new}</title>", 1)
    # Fallback — truncate at word boundary
    truncated = title[:67].rsplit(" ", 1)[0] + "…"
    return text.replace(f"<title>{title}</title>", f"<title>{truncated}</title>", 1)


print("\n=== 5. Trimming long titles ===")
trim_count_before = len(CHANGES)
for p in ROOT.rglob("*.html"):
    if "/.git/" in str(p):
        continue
    edit_file(p, trim_long_title)
print(f"   trimmed: {len(CHANGES) - trim_count_before}")


print(f"\n=== Done: {len(set(CHANGES))} files changed ===")
for c in sorted(set(CHANGES)):
    print(f"  {c}")
