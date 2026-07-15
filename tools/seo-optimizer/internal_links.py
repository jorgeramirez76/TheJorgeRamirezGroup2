#!/usr/bin/env python3
"""
Internal-linking pass — concentrate authority on the pillar pages.

Adds a contextual "Related New Jersey Guides" block to blog posts that have
fewer than MIN_LINKS links to the pillar pages. Anchors are keyword-rich (the
striking-distance signal) and VARIED by index so 54 posts don't share an
identical footprint. Redirect/noindex pages are skipped. Idempotent.

  python3 internal_links.py --dry-run   # report + write one sample, change nothing
  python3 internal_links.py             # apply to all under-linked posts
"""
import os, re, glob, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLOG = os.path.join(REPO, "blog")
MIN_LINKS = 2
MARKER = "related-guides-auto"

# Pillars with 2-3 anchor phrasings each (rotated to avoid a repeated footprint)
PILLARS = {
    "tax":  ("/blog/nj-property-tax-guide",
             ["the NJ property tax guide (rates by county & town)",
              "how New Jersey property taxes really work",
              "average NJ property taxes by county"]),
    "fthb": ("/blog/first-time-home-buyer-nj-guide",
             ["the first-time home buyer guide for New Jersey",
              "NJHMFA programs for first-time NJ buyers",
              "buying your first home in NJ (step by step)"]),
    "towns":("/blog/best-nj-towns-for-families-2026",
             ["the best NJ towns for families",
              "top New Jersey suburbs for families",
              "where families are buying in NJ"]),
    "val":  ("/home-valuation",
             ["what your NJ home is worth (free valuation)",
              "get your NJ home's current value",
              "a free New Jersey home valuation"]),
    "sell": ("/sell-your-home",
             ["how to sell your home in NJ",
              "selling your New Jersey home for more",
              "the NJ home-selling process"]),
    "when": ("/blog/best-time-to-sell-home-nj",
             ["the best time to sell a house in NJ",
              "when to list your NJ home",
              "timing your NJ home sale"]),
    "buy":  ("/buy-a-home",
             ["how to buy a home in New Jersey",
              "the NJ home-buying process",
              "buying a home in NJ"]),
}
SELL_SET = ["val", "sell", "when", "tax"]
BUY_SET = ["fthb", "buy", "towns", "tax"]
GEN_SET = ["tax", "fthb", "val", "towns"]


def intent(fn, title):
    s = (fn + " " + title).lower()
    if re.search(r"sell|seller|staging|valuation|listing|declutter|odor|pest|"
                 r"upgrade|renovat|curb|design|stage", s):
        return SELL_SET
    if re.search(r"buy|first-time|commut|moving|movers|rent|town|school|"
                 r"famil|relocat|neighborhood", s):
        return BUY_SET
    return GEN_SET


def pillar_link_count(t):
    return sum(t.count(u) for u, _ in PILLARS.values())


def build_block(keys, idx, self_url):
    items = []
    used = 0
    for k in keys:
        url, anchors = PILLARS[k]
        if url in self_url:            # never link a page to itself
            continue
        anchor = anchors[(idx + used) % len(anchors)]
        items.append(
            f'    <li style="margin-bottom:8px;"><a href="{url}" '
            f'style="color:#8A6D14;font-weight:600;text-decoration:none;">'
            f'{anchor}</a></li>')
        used += 1
        if used >= 3:
            break
    return (f'\n<section class="{MARKER}" style="margin:48px 0 8px;padding:26px 30px;'
            f'background:#FAFAF8;border:1px solid #E8E4DC;border-radius:10px;">\n'
            f'  <h2 style="margin:0 0 14px;font-size:1.25em;color:#1a1a1a;border:none;">'
            f'Related New Jersey Guides</h2>\n  <ul style="margin:0;padding-left:1.2em;'
            f'line-height:1.7;list-style:disc;">\n' + "\n".join(items)
            + '\n  </ul>\n</section>\n')


def process(path, idx, write=True):
    t = open(path, encoding="utf-8").read()
    if MARKER in t or "<title>Redirecting" in t or re.search(
            r'name=["\']robots["\'][^>]*noindex', t[:800]):
        return None
    if pillar_link_count(t) >= MIN_LINKS:
        return None
    title = (re.search(r"<title>(.*?)</title>", t, re.S) or [None, ""])[1]
    keys = intent(os.path.basename(path), title)
    block = build_block(keys, idx, "/blog/" + os.path.basename(path).replace(".html", ""))
    # insert before </main> (fallback: before footer, then before </body>)
    for anchor in ("</main>", '<footer', "</body>"):
        m = re.search(re.escape(anchor), t, re.I)
        if m:
            t2 = t[:m.start()] + block + t[m.start():]
            if write:
                open(path, "w", encoding="utf-8").write(t2)
            return block
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    posts = sorted(p for p in glob.glob(os.path.join(BLOG, "*.html"))
                   if not p.endswith("index.html"))
    under = []
    for p in posts:
        t = open(p, encoding="utf-8").read()
        if "<title>Redirecting" in t or re.search(r'noindex', t[:800]):
            continue
        if MARKER not in t and pillar_link_count(t) < MIN_LINKS:
            under.append(p)
    print(f"{len(under)} under-linked posts to enhance")
    if args.dry_run:
        sample = under[0] if under else None
        if sample:
            blk = process(sample, 0, write=False)
            print(f"\nSAMPLE for {os.path.basename(sample)}:\n{blk}")
        return
    done = 0
    for i, p in enumerate(under):
        if process(p, i, write=True):
            done += 1
    print(f"added Related-guides block to {done} posts")


if __name__ == "__main__":
    main()
