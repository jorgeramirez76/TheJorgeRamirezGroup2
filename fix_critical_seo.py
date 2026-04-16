#!/usr/bin/env python3
"""
Fix ALL 8 Critical SEO Issues on thejorgeramirezgroup.com
=========================================================
C1: Add Twitter Card tags to pages missing them
C2: Add Open Graph tags to blog posts missing them
C3: Add Open Graph tags to town pages missing them
C4: Fix Spanish meta descriptions (English -> Spanish)
C5: Fix Spanish og:url (points to English homepage)
C6: Fix outdated year in home-valuation.html H1
C7: Fix duplicate hreflang entries
C8: Add AggregateRating + Review schema to index.html
"""

import os
import re
import json
import html
from pathlib import Path

BASE_DIR = Path("/Users/teddy/TheJorgeRamirezGroup2")
SITE_URL = "https://thejorgeramirezgroup.com"
DEFAULT_IMAGE = f"{SITE_URL}/images/hero.jpg"

# Counters
changes = {
    "C1_twitter_cards_added": [],
    "C2_og_blog_posts_fixed": [],
    "C3_og_town_pages_fixed": [],
    "C4_spanish_meta_desc_fixed": [],
    "C5_spanish_og_url_fixed": [],
    "C6_year_updated": [],
    "C7_duplicate_hreflang_fixed": [],
    "C8_review_schema_added": [],
}


def read_file(filepath):
    """Read file with utf-8, ignore errors."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_file(filepath, content):
    """Write file with utf-8."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def extract_title(content):
    """Extract text from <title> tag."""
    m = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if m:
        return html.unescape(m.group(1).strip())
    return ""


def extract_og_title(content):
    """Extract og:title value."""
    m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if m:
        return html.unescape(m.group(1).strip())
    return ""


def extract_meta_description(content):
    """Extract meta description value."""
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if m:
        return html.unescape(m.group(1).strip())
    return ""


def extract_og_description(content):
    """Extract og:description value."""
    m = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if m:
        return html.unescape(m.group(1).strip())
    return ""


def has_twitter_card(content):
    """Check if page already has twitter:card meta tag."""
    return bool(re.search(r'(name|property)=["\']twitter:card["\']', content, re.IGNORECASE))


def has_og_title(content):
    """Check if page already has og:title meta tag."""
    return bool(re.search(r'property=["\']og:title["\']', content, re.IGNORECASE))


def escape_attr(text):
    """Escape text for use in HTML attribute values."""
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def get_relative_url(filepath):
    """Get the URL path relative to the site root."""
    rel = filepath.relative_to(BASE_DIR)
    return str(rel).replace("\\", "/")


# ============================================================
# C1: Add Twitter Card tags to pages missing them
# ============================================================
def fix_c1_twitter_cards():
    """Add Twitter Card meta tags to all HTML pages missing them."""
    count = 0
    for html_file in sorted(BASE_DIR.rglob("*.html")):
        # Skip es/ directory (Spanish versions are handled separately if needed)
        # Actually, we should fix ALL pages including es/ per the instructions
        # Skip non-content directories
        rel = str(html_file.relative_to(BASE_DIR))
        if rel.startswith(("docs/", "features/", "lead-research/", "data/")):
            continue

        content = read_file(html_file)

        # Skip if already has twitter:card
        if has_twitter_card(content):
            continue

        # Skip if no <head> tag
        if "</head>" not in content.lower():
            continue

        # Get title for twitter:title
        title = extract_og_title(content) or extract_title(content)
        if not title:
            continue  # Can't add meaningful twitter tags without a title

        # Get description for twitter:description
        desc = extract_og_description(content) or extract_meta_description(content)
        if not desc:
            desc = title  # fallback

        # Escape for HTML attributes
        title_safe = escape_attr(title)
        desc_safe = escape_attr(desc)

        # Build Twitter Card tags
        twitter_tags = f"""
    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title_safe}">
    <meta name="twitter:description" content="{desc_safe}">
    <meta name="twitter:image" content="{DEFAULT_IMAGE}">"""

        # Insert after existing OG tags (find last og: meta tag)
        og_match = None
        for m in re.finditer(r'<meta\s+property=["\']og:[^"\']*["\']\s+content=["\'][^"\']*["\']\s*/?\s*>', content, re.IGNORECASE):
            og_match = m

        if og_match:
            # Insert after the last OG tag
            insert_pos = og_match.end()
            new_content = content[:insert_pos] + twitter_tags + content[insert_pos:]
        else:
            # No OG tags found, insert before </head>
            head_close = re.search(r'</head>', content, re.IGNORECASE)
            if head_close:
                insert_pos = head_close.start()
                new_content = content[:insert_pos] + twitter_tags + "\n" + content[insert_pos:]
            else:
                continue

        write_file(html_file, new_content)
        changes["C1_twitter_cards_added"].append(rel)
        count += 1

    return count


# ============================================================
# C2: Add Open Graph tags to blog posts missing them
# ============================================================
def fix_c2_og_blog_posts():
    """Add OG tags to blog posts that are missing og:title."""
    blog_dir = BASE_DIR / "blog"
    if not blog_dir.exists():
        return 0

    count = 0
    for html_file in sorted(blog_dir.glob("*.html")):
        content = read_file(html_file)

        # Skip if already has og:title
        if has_og_title(content):
            continue

        title = extract_title(content)
        desc = extract_meta_description(content)
        if not title:
            continue

        if not desc:
            desc = title

        rel_url = get_relative_url(html_file)
        title_safe = escape_attr(title)
        desc_safe = escape_attr(desc)

        og_tags = f"""
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title_safe}">
    <meta property="og:description" content="{desc_safe}">
    <meta property="og:url" content="{SITE_URL}/{rel_url}">
    <meta property="og:image" content="{DEFAULT_IMAGE}">"""

        # Insert before </head>
        head_close = re.search(r'</head>', content, re.IGNORECASE)
        if head_close:
            insert_pos = head_close.start()
            new_content = content[:insert_pos] + og_tags + "\n" + content[insert_pos:]
            write_file(html_file, new_content)
            changes["C2_og_blog_posts_fixed"].append(str(html_file.relative_to(BASE_DIR)))
            count += 1

    return count


# ============================================================
# C3: Add Open Graph tags to town pages missing them
# ============================================================
def fix_c3_og_town_pages():
    """Add OG tags to town pages that are missing og:title."""
    towns_dir = BASE_DIR / "towns"
    if not towns_dir.exists():
        return 0

    count = 0
    for html_file in sorted(towns_dir.glob("*.html")):
        content = read_file(html_file)

        # Skip if already has og:title
        if has_og_title(content):
            continue

        title = extract_title(content)
        desc = extract_meta_description(content)
        if not title:
            continue

        if not desc:
            desc = title

        rel_url = get_relative_url(html_file)
        title_safe = escape_attr(title)
        desc_safe = escape_attr(desc)

        og_tags = f"""
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="{title_safe}">
    <meta property="og:description" content="{desc_safe}">
    <meta property="og:url" content="{SITE_URL}/{rel_url}">
    <meta property="og:image" content="{DEFAULT_IMAGE}">"""

        # Check if there's an og:image already but no og:title
        # Some town pages have og:image and og:type but no og:title, og:description, og:url
        has_some_og = bool(re.search(r'property=["\']og:', content, re.IGNORECASE))

        if has_some_og:
            # Page has some OG tags but missing og:title — add missing ones
            # Add og:title
            if not has_og_title(content):
                # Find the last existing og: tag to insert after
                og_last = None
                for m in re.finditer(r'<meta\s+property=["\']og:[^"\']*["\']\s+content=["\'][^"\']*["\']\s*/?\s*>', content, re.IGNORECASE):
                    og_last = m
                if og_last:
                    # Insert og:title, og:description, og:url after last OG tag
                    extra_og = f"""
    <meta property="og:title" content="{title_safe}">
    <meta property="og:description" content="{desc_safe}">
    <meta property="og:url" content="{SITE_URL}/{rel_url}">"""
                    insert_pos = og_last.end()
                    content = content[:insert_pos] + extra_og + content[insert_pos:]
                    write_file(html_file, content)
                    changes["C3_og_town_pages_fixed"].append(str(html_file.relative_to(BASE_DIR)))
                    count += 1
        else:
            # No OG tags at all — insert full set before </head>
            head_close = re.search(r'</head>', content, re.IGNORECASE)
            if head_close:
                insert_pos = head_close.start()
                new_content = content[:insert_pos] + og_tags + "\n" + content[insert_pos:]
                write_file(html_file, new_content)
                changes["C3_og_town_pages_fixed"].append(str(html_file.relative_to(BASE_DIR)))
                count += 1

    return count


# ============================================================
# C4: Fix Spanish meta descriptions
# ============================================================
def fix_c4_spanish_meta_desc():
    """Fix the Spanish homepage meta description (currently in English)."""
    es_index = BASE_DIR / "es" / "index.html"
    if not es_index.exists():
        return 0

    content = read_file(es_index)
    count = 0

    # Fix the meta description - currently English, replace with Spanish
    old_english = 'Licensed NJ Realtor Jorge Ramirez helps homeowners in Summit, Westfield, Chatham + 100 NJ towns sell for top dollar. Free home valuation. Call 908-230-7844.'
    spanish_desc = 'Jorge Ramirez es un agente de bienes ra\u00edces en Nueva Jersey. Ayuda a propietarios en Summit, Westfield, Chatham y m\u00e1s de 100 comunidades a vender su casa al mejor precio. Valuaci\u00f3n gratis. Llame al 908-230-7844.'

    if old_english in content:
        content = content.replace(old_english, spanish_desc)
        count += 1
        changes["C4_spanish_meta_desc_fixed"].append("es/index.html (meta description)")

    write_file(es_index, content)
    return count


# ============================================================
# C5: Fix Spanish og:url
# ============================================================
def fix_c5_spanish_og_url():
    """Fix the Spanish homepage og:url to point to /es/ instead of /."""
    es_index = BASE_DIR / "es" / "index.html"
    if not es_index.exists():
        return 0

    content = read_file(es_index)
    count = 0

    # Fix og:url from / to /es/
    old_og_url = '<meta property="og:url" content="https://thejorgeramirezgroup.com/">'
    new_og_url = '<meta property="og:url" content="https://thejorgeramirezgroup.com/es/">'

    if old_og_url in content:
        content = content.replace(old_og_url, new_og_url, 1)
        count += 1
        changes["C5_spanish_og_url_fixed"].append("es/index.html")
        write_file(es_index, content)

    return count


# ============================================================
# C6: Fix outdated year in home-valuation.html
# ============================================================
def fix_c6_year():
    """Change '2025' to '2026' in the H1 tag of home-valuation.html."""
    filepath = BASE_DIR / "home-valuation.html"
    if not filepath.exists():
        return 0

    content = read_file(filepath)
    count = 0

    # Target specifically the H1 tag with the year
    old_h1 = "What's My Home Worth in 2025?"
    new_h1 = "What's My Home Worth in 2026?"

    if old_h1 in content:
        content = content.replace(old_h1, new_h1, 1)
        count += 1
        changes["C6_year_updated"].append("home-valuation.html (H1: 2025 -> 2026)")
        write_file(filepath, content)

    return count


# ============================================================
# C7: Fix duplicate hreflang entries
# ============================================================
def fix_c7_duplicate_hreflang():
    """Remove duplicate hreflang entries from pages that have them."""
    count = 0

    for html_file in sorted(BASE_DIR.rglob("*.html")):
        rel = str(html_file.relative_to(BASE_DIR))
        if rel.startswith(("docs/", "features/", "lead-research/", "data/")):
            continue

        content = read_file(html_file)

        # Find all hreflang entries
        hreflang_pattern = r'<link\s+rel=["\']alternate["\']\s+hreflang=["\']([^"\']+)["\']\s+href=["\']([^"\']+)["\']\s*/?\s*>'
        matches = list(re.finditer(hreflang_pattern, content, re.IGNORECASE))

        if not matches:
            continue

        # Group by hreflang value
        hreflang_map = {}
        for m in matches:
            lang = m.group(1)
            url = m.group(2)
            if lang not in hreflang_map:
                hreflang_map[lang] = []
            hreflang_map[lang].append((m.group(0), url, m.start(), m.end()))

        # Check for duplicates
        has_dups = False
        for lang, entries in hreflang_map.items():
            if len(entries) > 1:
                has_dups = True
                break

        if not has_dups:
            continue

        # Process duplicates - keep the cleaner URL (prefer / over /index.html, prefer no trailing /index.html)
        lines_to_remove = []
        for lang, entries in hreflang_map.items():
            if len(entries) <= 1:
                continue

            # Determine which to keep: prefer shorter/cleaner URL
            # For homepage: prefer "/" over "/index.html"
            # For other pages: prefer the one without /index.html suffix
            best_idx = 0
            for i, (tag, url, start, end) in enumerate(entries):
                # Prefer URL that does NOT end with /index.html
                if not url.endswith("/index.html"):
                    best_idx = i

            # Mark all others for removal
            for i, (tag, url, start, end) in enumerate(entries):
                if i != best_idx:
                    lines_to_remove.append(tag)

        if lines_to_remove:
            for tag_to_remove in lines_to_remove:
                # Remove the tag and any surrounding whitespace/newline
                # Match the tag with optional leading whitespace and trailing newline
                escaped_tag = re.escape(tag_to_remove)
                pattern = r'\s*' + escaped_tag + r'\s*\n?'
                content = re.sub(pattern, '\n', content, count=1)

            write_file(html_file, content)
            changes["C7_duplicate_hreflang_fixed"].append(rel)
            count += 1

    return count


# ============================================================
# C8: Add AggregateRating + Review schema to index.html
# ============================================================
def fix_c8_review_schema():
    """Add AggregateRating to existing RealEstateAgent schema and add individual Review schema."""
    filepath = BASE_DIR / "index.html"
    if not filepath.exists():
        return 0

    content = read_file(filepath)

    # The 6 reviews from the homepage testimonials
    reviews = [
        {
            "author": "Michael T.",
            "location": "Summit, NJ",
            "date": "2025",
            "text": "Jorge sold our Summit home in 9 days \u2014 $47,000 over asking. He priced it perfectly and the targeted marketing brought buyers we never would have reached through a traditional listing. He was straight with us from day one."
        },
        {
            "author": "Diane R.",
            "location": "Westfield, NJ",
            "date": "2025",
            "text": "We had an expired listing with another agent for 90 days. Jorge took over, changed the pricing strategy, and had a full-price offer in 3 weeks. Wish we had called him first."
        },
        {
            "author": "David K.",
            "location": "Chatham, NJ",
            "date": "2025",
            "text": "As first-time buyers relocating from NYC, we were completely lost. Jorge walked every property with us like he was the one buying it. His investor background meant he caught things the inspector even missed. Closed on our Chatham home in 6 weeks."
        },
        {
            "author": "Patricia M.",
            "location": "Cranford, NJ",
            "date": "2026",
            "text": "I inherited my mother\u2019s home and had no idea where to start. Jorge handled everything \u2014 estate coordination, light repairs, pricing, all of it. He never pushed me and got us $30K above what I thought was possible."
        },
        {
            "author": "Robert H.",
            "location": "Maplewood, NJ",
            "date": "2026",
            "text": "We tried to sell FSBO for 4 months. After we listed with Jorge, we had an accepted offer in 11 days. His buyer targeting system found people we never could have reached on our own. Should have called him first."
        },
        {
            "author": "Tom F.",
            "location": "Montclair, NJ",
            "date": "2025",
            "text": "Jorge told us the truth about our home\u2019s value even though it wasn\u2019t what we wanted to hear. We priced it his way, had 8 showings the first weekend, and closed for more than our original ask. His honesty saved us months."
        }
    ]

    # 1. Add aggregateRating to existing RealEstateAgent JSON-LD
    # Find the RealEstateAgent schema block and add aggregateRating before the closing brace
    # The schema has "knowsAbout": [...] ] } as its ending structure

    aggregate_rating_json = """,
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "5.0",
        "reviewCount": "6",
        "bestRating": "5",
        "worstRating": "1"
    }"""

    # Find the end of the knowsAbout array in the RealEstateAgent schema and add aggregateRating
    # Pattern: "knowsAbout": [...] }  (end of the RealEstateAgent object)
    # We need to insert the aggregateRating before the final closing brace of the RealEstateAgent schema

    # The RealEstateAgent schema ends with:
    #       "New Jersey Home Valuations"
    #       ]
    #     }
    # We insert aggregateRating after the knowsAbout closing bracket

    old_ending = """      "New Jersey Home Valuations"
      ]
    }"""
    new_ending = """      "New Jersey Home Valuations"
      ],
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "5.0",
        "reviewCount": "6",
        "bestRating": "5",
        "worstRating": "1"
    }
    }"""

    if old_ending in content:
        content = content.replace(old_ending, new_ending, 1)
        changes["C8_review_schema_added"].append("index.html (AggregateRating added to RealEstateAgent schema)")
    else:
        print("  WARNING: Could not find expected ending in RealEstateAgent schema. Trying alternate pattern...")
        # Try a regex approach
        pattern = r'("New Jersey Home Valuations"\s*\]\s*)\}'
        replacement = r'''\1,
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "5.0",
        "reviewCount": "6",
        "bestRating": "5",
        "worstRating": "1"
    }
    }'''
        new_content = re.sub(pattern, replacement, content, count=1)
        if new_content != content:
            content = new_content
            changes["C8_review_schema_added"].append("index.html (AggregateRating added via regex)")

    # 2. Add individual Review schema as a separate JSON-LD block
    review_items = []
    for r in reviews:
        review_items.append({
            "@type": "Review",
            "author": {
                "@type": "Person",
                "name": r["author"]
            },
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": "5",
                "bestRating": "5",
                "worstRating": "1"
            },
            "reviewBody": r["text"],
            "datePublished": r["date"]
        })

    review_schema = {
        "@context": "https://schema.org",
        "@type": "RealEstateAgent",
        "@id": "https://thejorgeramirezgroup.com/#agent",
        "name": "Jorge Ramirez - The Jorge Ramirez Group",
        "review": review_items
    }

    review_json = json.dumps(review_schema, indent=2, ensure_ascii=False)

    # Insert the new schema block before </head>
    review_block = f"""
    <!-- JSON-LD Structured Data: Client Reviews -->
    <script type="application/ld+json">
    {review_json}
    </script>
"""

    head_close = re.search(r'</head>', content, re.IGNORECASE)
    if head_close:
        insert_pos = head_close.start()
        content = content[:insert_pos] + review_block + content[insert_pos:]
        changes["C8_review_schema_added"].append("index.html (6 individual Review schemas added)")

    write_file(filepath, content)
    return 1


# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    print("=" * 70)
    print("  SEO Critical Issue Fixer - thejorgeramirezgroup.com")
    print("=" * 70)
    print()

    # Run C2 and C3 FIRST (they add OG tags that C1 needs to find)
    print("[C2] Adding Open Graph tags to blog posts missing them...")
    c2 = fix_c2_og_blog_posts()
    print(f"     -> Fixed {c2} blog posts\n")

    print("[C3] Adding Open Graph tags to town pages missing them...")
    c3 = fix_c3_og_town_pages()
    print(f"     -> Fixed {c3} town pages\n")

    # Now run C1 (Twitter cards) - this will also handle pages that just got OG tags
    print("[C1] Adding Twitter Card tags to pages missing them...")
    c1 = fix_c1_twitter_cards()
    print(f"     -> Added Twitter Cards to {c1} pages\n")

    print("[C4] Fixing Spanish meta descriptions...")
    c4 = fix_c4_spanish_meta_desc()
    print(f"     -> Fixed {c4} descriptions\n")

    print("[C5] Fixing Spanish og:url...")
    c5 = fix_c5_spanish_og_url()
    print(f"     -> Fixed {c5} URLs\n")

    print("[C6] Fixing outdated year in home-valuation.html...")
    c6 = fix_c6_year()
    print(f"     -> Fixed {c6} pages\n")

    print("[C7] Fixing duplicate hreflang entries...")
    c7 = fix_c7_duplicate_hreflang()
    print(f"     -> Fixed {c7} pages\n")

    print("[C8] Adding AggregateRating + Review schema to index.html...")
    c8 = fix_c8_review_schema()
    print(f"     -> Added to {c8} page(s)\n")

    # Print detailed summary
    print()
    print("=" * 70)
    print("  DETAILED CHANGE LOG")
    print("=" * 70)

    for fix_id, items in changes.items():
        print(f"\n{fix_id} ({len(items)} changes):")
        if items:
            for item in items:
                print(f"  - {item}")
        else:
            print("  (none)")

    # Grand totals
    total = sum(len(v) for v in changes.values())
    print(f"\n{'=' * 70}")
    print(f"  TOTAL CHANGES: {total}")
    print(f"{'=' * 70}")
    print(f"  C1 Twitter Cards added:       {len(changes['C1_twitter_cards_added'])}")
    print(f"  C2 Blog OG tags added:        {len(changes['C2_og_blog_posts_fixed'])}")
    print(f"  C3 Town OG tags added:        {len(changes['C3_og_town_pages_fixed'])}")
    print(f"  C4 Spanish meta desc fixed:   {len(changes['C4_spanish_meta_desc_fixed'])}")
    print(f"  C5 Spanish og:url fixed:      {len(changes['C5_spanish_og_url_fixed'])}")
    print(f"  C6 Year updated:              {len(changes['C6_year_updated'])}")
    print(f"  C7 Duplicate hreflang fixed:  {len(changes['C7_duplicate_hreflang_fixed'])}")
    print(f"  C8 Review schema added:       {len(changes['C8_review_schema_added'])}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
