#!/usr/bin/env python3
"""Fetch free, commercially-usable town photos from Wikimedia for blog imagery.

Sources Wikipedia article images per town, keeps only PD/CC0/CC BY/CC BY-SA
licenses (commercial use OK with attribution), converts to WebP at
images/towns/<slug>-N.webp, and writes images/towns/credits.json with
artist + license for caption attribution.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "TheJorgeRamirezGroupSite/1.0 (jorge.ramirez@kw.com) python-urllib"}
API = "https://en.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
OUT = "images/towns"
os.makedirs(OUT, exist_ok=True)

EXCLUDE = re.compile(r"seal|map|logo|flag|locator|montage|collage|census|coat[ _]of[ _]arms|\.svg|\.gif|\.tif|diagram|chart|graph|crest|aerial|air[ _]view|above|overhead|looking[ _]down|drone|interior|plaque|grave|cemetery|portrait|house[ _]at|residence", re.I)
# recognizable-landmark ranking: stations and welcome signs first
RANK = [re.compile(r"station|nj[ _]?transit|railroad|depot", re.I),
        re.compile(r"welcome|sign|gateway|entering", re.I),
        re.compile(r"downtown|main[ _]street|business[ _]district|center|centre|avenue", re.I),
        re.compile(r"hall|library|theat|park|school|church|clock|plaza|square|green|mill|landmark", re.I)]
LICENSE_OK = re.compile(r"^(cc0|cc[ -]by(?![ -]nc)(?![ -]nd)[ -0-9.sa]*|public domain|pd)", re.I)


def api(params, endpoint=None):
    params = dict(params, format="json")
    url = (endpoint or API) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def commons_search(town):
    """Search Commons File namespace for recognizable landmark shots."""
    name = town.replace("-", " ").title()
    q = f'{name} New Jersey (station OR downtown OR "welcome sign" OR "main street" OR depot)'
    r = api({"action": "query", "list": "search", "srsearch": q,
             "srnamespace": 6, "srlimit": 30}, endpoint=COMMONS)
    titles = [h["title"] for h in r["query"]["search"]
              if h["title"].lower().endswith((".jpg", ".jpeg", ".png"))
              and not EXCLUDE.search(h["title"])
              and name.split()[0].lower() in h["title"].lower()]
    return titles


def resolve_title(town):
    q = town.replace("-", " ") + " New Jersey"
    r = api({"action": "query", "list": "search", "srsearch": q, "srlimit": 1})
    hits = r["query"]["search"]
    return hits[0]["title"] if hits else None


def page_images(title):
    r = api({"action": "query", "titles": title, "prop": "images", "imlimit": 50})
    page = next(iter(r["query"]["pages"].values()))
    return [i["title"] for i in page.get("images", [])
            if i["title"].lower().endswith((".jpg", ".jpeg", ".png"))
            and not EXCLUDE.search(i["title"])]


def image_meta(file_titles):
    out = []
    for i in range(0, len(file_titles), 25):
        batch = file_titles[i:i+25]
        r = api({"action": "query", "titles": "|".join(batch),
                 "prop": "imageinfo", "iiprop": "url|size|extmetadata"}, endpoint=COMMONS)
        for page in r["query"]["pages"].values():
            ii = page.get("imageinfo", [{}])[0]
            if not ii.get("url"):
                continue
            md = ii.get("extmetadata", {})
            lic = md.get("LicenseShortName", {}).get("value", "")
            artist = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()
            out.append({
                "title": page["title"], "url": ii["url"],
                "width": ii.get("width", 0), "height": ii.get("height", 0),
                "license": lic, "artist": artist[:60],
            })
    return out


def rank_score(title):
    for i, pat in enumerate(RANK):
        if pat.search(title):
            return len(RANK) - i
    return 0


def pick(cands):
    ok = [c for c in cands
          if LICENSE_OK.match(c["license"].strip()) and c["width"] >= 900
          and c["width"] >= c["height"] * 0.85]         # landscape-ish only
    ok.sort(key=lambda c: (rank_score(c["title"]), c["width"]), reverse=True)
    # require a recognizable landmark for the lead photo
    ok = [c for c in ok if rank_score(c["title"]) > 0] or ok
    return ok[:2]


def download_webp(url, dest):
    tmp = dest + ".src"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        f.write(r.read())
    res = subprocess.run(["cwebp", "-quiet", "-q", "78", "-resize", "1280", "0", tmp, "-o", dest])
    os.remove(tmp)
    return res.returncode == 0 and os.path.exists(dest)


def main():
    towns = sys.argv[1:]
    credits = {}
    if os.path.exists(f"{OUT}/credits.json"):
        credits = json.load(open(f"{OUT}/credits.json"))
    for town in towns:
        if town in credits:
            print(f"{town}: cached", flush=True)
            continue
        try:
            title = resolve_title(town)
            if not title:
                print(f"{town}: NO WIKI PAGE", flush=True)
                continue
            files = commons_search(town)
            if len(files) < 2:                      # fallback: wiki article images
                files += [f for f in page_images(title) if f not in files]
            cands = image_meta(files)
            chosen = pick(cands)
            entry = []
            for n, c in enumerate(chosen, 1):
                dest = f"{OUT}/{town}-{n}.webp"
                if download_webp(c["url"], dest):
                    info = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", dest],
                                          capture_output=True, text=True).stdout
                    w = int(re.search(r"pixelWidth: (\d+)", info).group(1))
                    h = int(re.search(r"pixelHeight: (\d+)", info).group(1))
                    entry.append({"file": f"{town}-{n}.webp", "w": w, "h": h,
                                  "license": c["license"], "artist": c["artist"],
                                  "source": c["title"], "wiki": title})
            credits[town] = entry
            json.dump(credits, open(f"{OUT}/credits.json", "w"), indent=1)
            print(f"{town}: {len(entry)} photos ({title})", flush=True)
            time.sleep(4)
        except Exception as e:
            print(f"{town}: ERROR {str(e)[:80]}", flush=True)
            time.sleep(8)
    got = sum(1 for v in credits.values() if v)
    print(f"DONE: {got}/{len(credits)} towns with photos", flush=True)


if __name__ == "__main__":
    main()
