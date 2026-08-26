#!/usr/bin/env python3
"""Render the compact English fallbacks for quarantined town-guide routes.

The renderer is deliberately deterministic: town and county names come from
the repository's verified county lookup, the route inventory comes from one
versioned policy file, and no current market or demographic data is emitted.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Iterable, Optional


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "data" / "english-noindex-town-fallbacks.json"
SITE = "https://thejorgeramirezgroup.com"
SHARE_IMAGE = f"{SITE}/images/hero.jpg"
SHARE_IMAGE_ALT = "Residential property image from The Jorge Ramirez Group website"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from town_data import COUNTY  # noqa: E402


def load_policy(path: Path = POLICY_PATH) -> dict[str, object]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    groups = policy.get("groups")
    if not isinstance(groups, list):
        raise RuntimeError(f"{path}: groups must be a list")

    slugs = [
        slug
        for group in groups
        for slug in group.get("slugs", [])
        if isinstance(slug, str)
    ]
    if len(slugs) != 74 or len(set(slugs)) != 74:
        raise RuntimeError(f"{path}: expected 74 unique fallback slugs")

    protected = set(policy.get("protectedSourceBackedPrioritySlugs", []))
    if protected & set(slugs):
        raise RuntimeError(f"{path}: fallback and protected inventories overlap")

    county_guides = policy.get("countyGuides")
    if not isinstance(county_guides, dict):
        raise RuntimeError(f"{path}: countyGuides must be an object")
    missing_counties = {COUNTY.get(slug) for slug in slugs} - set(county_guides)
    if missing_counties:
        raise RuntimeError(
            f"{path}: missing county guide mappings: {sorted(missing_counties, key=str)}"
        )
    return policy


def group_slugs(group_id: str, policy: Optional[dict[str, object]] = None) -> set[str]:
    selected_policy = policy or load_policy()
    for group in selected_policy["groups"]:
        if group.get("id") == group_id:
            return set(group["slugs"])
    raise KeyError(f"unknown fallback group: {group_id}")


def all_fallback_slugs(policy: Optional[dict[str, object]] = None) -> set[str]:
    selected_policy = policy or load_policy()
    return {
        slug
        for group in selected_policy["groups"]
        for slug in group["slugs"]
    }


def display_name(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def render_page(slug: str, policy: Optional[dict[str, object]] = None) -> str:
    selected_policy = policy or load_policy()
    if slug not in all_fallback_slugs(selected_policy):
        raise KeyError(f"slug is not in the fallback policy: {slug}")

    town = display_name(slug)
    county = COUNTY[slug]
    county_guide = selected_policy["countyGuides"][county]
    canonical = f"{SITE}/towns/{slug}"
    title = f"{town}, NJ Guide Review | Jorge Ramirez"
    description = (
        f"The earlier {town} page is under editorial review. Use the "
        f"{county} County guide or contact Jorge Ramirez for current, "
        "property-specific information."
    )

    escaped = {
        "canonical": html.escape(canonical, quote=True),
        "county": html.escape(county),
        "county_href": html.escape(county_guide["href"], quote=True),
        "county_label": html.escape(county_guide["label"]),
        "description": html.escape(description, quote=True),
        "share_image": html.escape(SHARE_IMAGE, quote=True),
        "share_image_alt": html.escape(SHARE_IMAGE_ALT, quote=True),
        "title": html.escape(title),
        "town": html.escape(town),
    }

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0A0A0A">
  <title>{escaped["title"]}</title>
  <meta name="description" content="{escaped["description"]}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{escaped["canonical"]}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="The Jorge Ramirez Group">
  <meta property="og:url" content="{escaped["canonical"]}">
  <meta property="og:title" content="{escaped["title"]}">
  <meta property="og:description" content="{escaped["description"]}">
  <meta property="og:image" content="{escaped["share_image"]}">
  <meta property="og:image:width" content="1400">
  <meta property="og:image:height" content="933">
  <meta property="og:image:alt" content="{escaped["share_image_alt"]}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="{escaped["canonical"]}">
  <meta name="twitter:title" content="{escaped["title"]}">
  <meta name="twitter:description" content="{escaped["description"]}">
  <meta name="twitter:image" content="{escaped["share_image"]}">
  <meta name="twitter:image:alt" content="{escaped["share_image_alt"]}">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <link rel="icon" href="/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/town-fallback.css">
</head>
<body class="town-fallback" data-noindex-town-fallback="v1">
  <a href="#main" class="skip-link">Skip to main content</a>
  <nav class="town-fallback__nav" aria-label="Primary">
    <div class="town-fallback__nav-inner">
      <a class="town-fallback__brand" href="/" aria-label="The Jorge Ramirez Group home">
        <picture>
          <source srcset="/images/jorge-logo.webp" type="image/webp">
          <img src="/images/jorge-logo.jpg" width="250" height="100" alt="The Jorge Ramirez Group">
        </picture>
      </a>
      <ul class="town-fallback__nav-links">
        <li><a href="/communities">Communities</a></li>
        <li><a href="/contact" data-contact-link>Contact Jorge</a></li>
      </ul>
    </div>
  </nav>

  <main id="main" tabindex="-1">
    <section class="town-fallback__hero" aria-labelledby="page-title">
      <div class="town-fallback__hero-inner">
        <p class="town-fallback__eyebrow">Community guide status</p>
        <h1 id="page-title">A focused {escaped["town"]} guide is in review</h1>
        <p class="town-fallback__lede">The previous long-form page has been retired because its local details were not sufficiently verified. This URL remains available while a concise, source-backed replacement is reviewed.</p>
      </div>
    </section>

    <section class="town-fallback__content" aria-labelledby="next-step-title">
      <article class="town-fallback__card">
        <h2 id="next-step-title">Start with the regional guide</h2>
        <p>Use the {escaped["county"]} County guide for regional context currently available on this site. If your question concerns a particular home, sale, purchase, or move, contact Jorge with the address and the information you want checked. Property-specific guidance should be based on current records, current listing information when available, and the facts you provide.</p>
        <div class="town-fallback__actions">
          <a class="town-fallback__button town-fallback__button--primary" href="{escaped["county_href"]}">View the {escaped["county_label"]}</a>
          <a class="town-fallback__button town-fallback__button--secondary" href="/contact">Contact Jorge</a>
        </div>
        <p class="town-fallback__note">This fallback is intentionally excluded from search sitemaps. It publishes no town-specific figures or outcome promises while the full guide is under review.</p>
      </article>
    </section>
  </main>

  <footer class="town-fallback__footer">
    <p>The Jorge Ramirez Group · Keller Williams Premier Properties</p>
    <p><a href="/">Home</a> · <a href="/privacy-policy">Privacy Policy</a></p>
  </footer>
</body>
</html>
'''


def _selected_slugs(
    policy: dict[str, object], slugs: Optional[Iterable[str]]
) -> list[str]:
    inventory = all_fallback_slugs(policy)
    selected = inventory if slugs is None else set(slugs)
    unknown = selected - inventory
    if unknown:
        raise RuntimeError(f"requested slugs are outside the fallback policy: {sorted(unknown)}")
    return sorted(selected)


def render_fallbacks(
    *, root: Path = ROOT, slugs: Optional[Iterable[str]] = None
) -> list[Path]:
    policy = load_policy()
    changed: list[Path] = []
    for slug in _selected_slugs(policy, slugs):
        path = root / "towns" / f"{slug}.html"
        expected = render_page(slug, policy)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == expected:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        changed.append(path)
    return changed


def check_fallbacks(
    *, root: Path = ROOT, slugs: Optional[Iterable[str]] = None
) -> list[Path]:
    policy = load_policy()
    mismatches: list[Path] = []
    for slug in _selected_slugs(policy, slugs):
        path = root / "towns" / f"{slug}.html"
        if not path.exists() or path.read_text(encoding="utf-8") != render_page(slug, policy):
            mismatches.append(path)
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    parser.add_argument("--group", help="limit rendering to one policy group")
    args = parser.parse_args()

    selected = group_slugs(args.group) if args.group else None
    if args.check:
        mismatches = check_fallbacks(slugs=selected)
        if mismatches:
            for path in mismatches:
                print(f"fallback drift: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"fallback check passed: {len(selected or all_fallback_slugs())} routes")
        return 0

    changed = render_fallbacks(slugs=selected)
    print(f"rendered {len(changed)} changed fallback pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
