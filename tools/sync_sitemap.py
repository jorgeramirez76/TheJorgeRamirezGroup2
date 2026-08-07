#!/usr/bin/env python3
"""Register indexable blog posts that other publishers dropped from sitemap.xml.

The cloud blog agent commits posts without touching sitemap.xml; this closes
the gap. Only adds /blog/<slug> pages that are self-canonical, not noindexed,
and not shadowed by a vercel.json redirect. Idempotent — safe to run daily.
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
SITE = "https://thejorgeramirezgroup.com"
SITEMAP = os.path.join(REPO, "sitemap.xml")


def missing_blog_entries():
    with open(SITEMAP, encoding="utf-8") as f:
        sm = f.read()
    with open(os.path.join(REPO, "vercel.json"), encoding="utf-8") as f:
        redirected = {r["source"] for r in json.load(f)["redirects"] if "has" not in r}
    out = []
    for name in sorted(os.listdir(os.path.join(REPO, "blog"))):
        if not name.endswith(".html") or name == "index.html":
            continue
        slug = name[:-5]
        url = f"/blog/{slug}"
        if f"<loc>{SITE}{url}</loc>" in sm or url in redirected:
            continue
        with open(os.path.join(REPO, "blog", name), encoding="utf-8") as f:
            head = f.read(6000)
        if re.search(r'name="robots"[^>]*noindex', head):
            continue
        m = re.search(r'<link rel="canonical" href="([^"]+)"', head)
        if not m or m.group(1).rstrip("/") != f"{SITE}{url}":
            continue
        mtime = os.path.getmtime(os.path.join(REPO, "blog", name))
        out.append((url, datetime.date.fromtimestamp(mtime).isoformat()))
    return out


def main():
    entries = missing_blog_entries()
    if not entries:
        print("sitemap in sync")
        return 0
    with open(SITEMAP, encoding="utf-8") as f:
        sm = f.read()
    block = "".join(
        f"  <url>\n    <loc>{SITE}{url}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n"
        for url, lastmod in entries
    )
    sm = sm.replace("</urlset>", block + "</urlset>", 1)
    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(sm)
    for url, _ in entries:
        print(f"added {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
