#!/usr/bin/env python3
"""Deep full-site checker — catches what audit_site.py can't.

Per page: document structure (head/body order, balanced tags — the class of
bug that made town pages render as 594px stubs), brand palette violations,
font-stack drift, SEO stack (title/desc/canonical/robots/og/twitter/h1/GA4),
AI-SEO stack (llm-context, JSON-LD validity), content regressions (flip-count
credential, merge-conflict markers), and local image existence.
"""
import json
import os
import re
import sys
from collections import defaultdict

BANNED_COLORS = re.compile(r'#(c9a84c|e8c97a|1a4b8c|0f3460|1a2a4a|f6a623|0f1117|1a1f2e|2d3347)\b', re.I)
BANNED_FONTS = re.compile(r'family=(Montserrat|Cormorant)|Cormorant Garamond', re.I)
FLIP = re.compile(r'(60\+|sixty[ -]plus|over 60) (house |home |personal )*(flip|homes|houses|properties)', re.I)
CONFLICT = re.compile(r'^(<<<<<<<|>>>>>>>|=======$)', re.M)

issues = defaultdict(list)


def add(kind, path, detail=""):
    issues[kind].append((path, detail))


def check(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    low = t.lower()
    is_stub = 'http-equiv="refresh"' in t
    noindex = re.search(r'<meta name="robots" content="noindex', t)

    # --- structure (every page, stubs included) ---
    for tag in ("<html", "<head>", "</head>", "<body", "</body>", "</html>"):
        if t.count(tag) != 1:
            add("structure-count", path, f"{tag} x{t.count(tag)}")
    h, b = t.find("</head>"), t.find("<body")
    if h == -1 or b == -1 or h > b:
        add("structure-order", path, f"</head>@{h} <body@{b}")
    for tag in ("style", "script"):
        o = len(re.findall(f"<{tag}[ >]", t))
        c = len(re.findall(f"</{tag}>", t))
        if o != c:
            add("unbalanced-tag", path, f"{tag} {o}/{c}")
    if t.count("<!--") != t.count("-->"):
        add("unbalanced-comment", path)
    if CONFLICT.search(t):
        add("conflict-markers", path)

    if is_stub:
        return  # redirect stubs need nothing else

    # --- SEO stack ---
    m = re.search(r"<title>([^<]*)</title>", t)
    if not m:
        add("no-title", path)
    elif not (10 <= len(m.group(1)) <= 68):
        add("title-length", path, f"{len(m.group(1))}ch")
    if not re.search(r'<meta name="description" content="[^"]{40,}"', t):
        add("weak-description", path)
    if '<link rel="canonical"' not in t:
        add("no-canonical", path)
    if '<meta name="robots"' not in t:
        add("no-robots", path)
    if 'property="og:title"' not in t:
        add("no-og", path)
    if 'twitter:card' not in t:
        add("no-twitter-card", path)
    h1s = len(re.findall(r"<h1[ >]", t))
    if h1s != 1 and not noindex and path != "404.html":
        add("h1-count", path, f"x{h1s}")
    if "G-KMS6H85LB0" not in t:
        add("no-ga4", path)
    if "styles.css" not in t:
        add("no-stylesheet", path)

    # --- AI SEO ---
    if 'name="llm-context"' not in t and not noindex:
        add("no-llm-context", path)
    lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
    if not lds and not noindex:
        add("no-jsonld", path)
    for ld in lds:
        try:
            json.loads(ld)
        except Exception as e:
            add("bad-jsonld", path, str(e)[:50])

    # --- brand consistency ---
    mcol = BANNED_COLORS.search(t)
    if mcol:
        add("off-brand-color", path, mcol.group(0))
    mfont = BANNED_FONTS.search(t)
    if mfont:
        add("off-brand-font", path, mfont.group(0)[:40])

    # --- content regressions ---
    body_txt = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    mflip = FLIP.search(body_txt)
    if mflip:
        add("flip-count", path, mflip.group(0)[:40])

    # --- local images exist ---
    for src in re.findall(r'<img[^>]+src="(/[^"]+|images/[^"]+|\.\./[^"]+)"', t):
        rel = src.lstrip("/") if src.startswith("/") else os.path.normpath(
            os.path.join(os.path.dirname(path), src))
        if not os.path.exists(rel):
            add("missing-image", path, src)


def main():
    n = 0
    for root, dirs, fs in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".design-screens",
                                                "node_modules", "lead-research",
                                                "property-leads-system", "docs", "_posts")]
        for fn in sorted(fs):
            if fn.endswith(".html"):
                check(os.path.join(root, fn).lstrip("./"))
                n += 1
    print(f"checked {n} pages\n")
    if not issues:
        print("ZERO ISSUES")
        return
    for kind in sorted(issues, key=lambda k: -len(issues[k])):
        lst = issues[kind]
        print(f"## {kind}: {len(lst)}")
        for p, d in lst[:6]:
            print(f"   {p}  {d}")
        if len(lst) > 6:
            print(f"   ... +{len(lst)-6} more")
    json.dump({k: v for k, v in issues.items()},
              open("/tmp/check_everything.json", "w"), indent=1)
    print("\nfull detail: /tmp/check_everything.json")


if __name__ == "__main__":
    main()
