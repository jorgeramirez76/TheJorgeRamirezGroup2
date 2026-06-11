#!/usr/bin/env python3
"""Swap stock lead figures for real local town photos (Wikimedia, attributed).

Figure #1 on each town page becomes the town photo; if a second town photo
exists, the last figure becomes town photo #2. Middle staged-interior figure
stays (it carries the selling caption). EN + ES versions share imagery.
"""
import json
import os
import re

CREDITS = json.load(open("images/towns/credits.json"))

PATS = [
    re.compile(r"^market-report-(.+?)-nj-2026\.html$"),
    re.compile(r"^buying-home-(.+?)-nj-2026\.html$"),
    re.compile(r"^neighborhoods-(.+?)-nj\.html$"),
    re.compile(r"^selling-home-(.+?)-nj-2026\.html$"),
    re.compile(r"^(.+?-county)-nj-real-estate-market.*\.html$"),
]
FIG = re.compile(r'<figure class="article-figure">.*?</figure>', re.S)


def town_for(fn):
    for p in PATS:
        m = p.match(fn)
        if m and m.group(1) in CREDITS and CREDITS[m.group(1)]:
            return m.group(1)
    return None


def pretty(slug):
    return slug.replace("-", " ").title().replace(" Nj", " NJ")


def town_figure(slug, photo, spanish):
    name = pretty(slug)
    alt = (f"Vista de {name}, Nueva Jersey" if spanish else f"{name}, New Jersey")
    credit_bits = []
    if photo["artist"]:
        credit_bits.append(f"foto: {photo['artist']}" if spanish else f"photo: {photo['artist']}")
    if photo["license"] and not photo["license"].lower().startswith(("public", "pd", "cc0")):
        credit_bits.append(photo["license"])
    credit = (" — " + ", ".join(credit_bits) + ", Wikimedia Commons") if credit_bits else " — Wikimedia Commons"
    cap = (f"{name}, Nueva Jersey{credit}" if spanish else f"{name}, New Jersey{credit}")
    return (f'<figure class="article-figure"><img src="/images/towns/{photo["file"]}" '
            f'alt="{alt}" width="{photo["w"]}" height="{photo["h"]}" loading="lazy">'
            f'<figcaption>{cap}</figcaption></figure>')


def main():
    changed = 0
    for d in ("blog", "es/blog"):
        spanish = d.startswith("es")
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".html"):
                continue
            slug = town_for(fn)
            if not slug:
                continue
            path = f"{d}/{fn}"
            t = open(path, encoding="utf-8", errors="replace").read()
            figs = list(FIG.finditer(t))
            if not figs or "/images/towns/" in t:
                continue
            photos = CREDITS[slug]
            # replace last figure first (offsets), then first
            if len(photos) > 1 and len(figs) > 1:
                last = figs[-1]
                t = t[:last.start()] + town_figure(slug, photos[1], spanish) + t[last.end():]
            first = figs[0]
            t = t[:first.start()] + town_figure(slug, photos[0], spanish) + t[first.end():]
            open(path, "w", encoding="utf-8").write(t)
            changed += 1
    print(f"local photos applied to {changed} pages")




def apply_town_pages():
    """towns/*.html, es/towns/*.html, realtor/*-nj.html get landmark figures."""
    changed = 0
    jobs = []
    for d in ("towns", "es/towns"):
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".html") and fn != "index.html":
                jobs.append((f"{d}/{fn}", fn[:-5], d.startswith("es"),
                             "<h2>Neighborhoods", "<h2>Commute"))
    for fn in sorted(os.listdir("realtor")):
        if fn.endswith("-nj.html"):
            jobs.append((f"realtor/{fn}", fn[:-8], False, "<h2>", None))
    for path, slug, spanish, anchor1, anchor2 in jobs:
        photos = CREDITS.get(slug)
        if not photos:
            continue
        t = open(path, encoding="utf-8", errors="replace").read()
        if "/images/towns/" in t:
            continue
        if path.startswith("realtor"):
            # insert before the SECOND h2
            h2s = [m.start() for m in re.finditer(r"<h2[ >]", t)]
            if len(h2s) < 2:
                continue
            pos = h2s[1]
            t = t[:pos] + town_figure(slug, photos[0], spanish) + "\n        " + t[pos:]
        else:
            i1 = t.find(anchor1)
            if i1 < 0:
                continue
            if anchor2 and len(photos) > 1:
                i2 = t.find(anchor2)
                if i2 > i1:
                    t = t[:i2] + town_figure(slug, photos[1], spanish) + "\n        " + t[i2:]
            t = t[:i1] + town_figure(slug, photos[0], spanish) + "\n        " + t[i1:]
        open(path, "w", encoding="utf-8").write(t)
        changed += 1
    print(f"town/realtor pages updated: {changed}")


if __name__ == "__main__":
    main()
    apply_town_pages()
