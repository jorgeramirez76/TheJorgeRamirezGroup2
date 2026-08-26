#!/usr/bin/env python3
"""Add deterministic county, service, and comparison links to priority towns."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from local_search_links import links_for_town


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- local-search-pathways:start -->"
END = "<!-- local-search-pathways:end -->"
STYLESHEET = '  <link rel="stylesheet" href="/css/local-search-pathways.css">\n'
TARGETS = {
    "berkeley-heights",
    "bloomfield",
    "chatham-borough",
    "chatham-township",
    "cranford",
    "denville",
    "east-brunswick",
    "east-hanover",
    "fanwood",
    "guttenberg",
    "morris-plains",
    "new-providence",
    "roselle-park",
    "south-brunswick",
    "springfield",
    "west-new-york",
}
BLOCK = re.compile(
    rf"\n?[ \t]*{re.escape(START)}.*?{re.escape(END)}\n?", re.S
)


def county_map() -> dict[str, str]:
    facts = json.loads((ROOT / "data/site-facts.json").read_text(encoding="utf-8"))
    return {
        slug: county
        for county, slugs in facts["canonicalTownInventory"]["byCounty"].items()
        for slug in slugs
    }


def display_name(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def pathway_block(slug: str, county: str) -> str:
    town = display_name(slug)
    links = [
        (f"/counties/{county.lower()}-county", f"{county} County real estate guide"),
        ("/buy-a-home", "Plan a New Jersey home search"),
        ("/sell-your-home", "Review the New Jersey selling process"),
        ("/home-valuation", "Request a property-specific home value review"),
    ]
    links.extend((item["route"], item["label"]) for item in links_for_town(slug))
    anchors = "".join(
        f'<a href="{html.escape(route, quote=True)}">{html.escape(label)}</a>'
        for route, label in links
    )
    return f'''  {START}
  <section class="local-search-pathways" data-local-search-pathways="v1" aria-labelledby="local-pathways-{slug}">
    <div class="local-search-pathways__inner">
      <p class="local-search-pathways__eyebrow">Continue local research</p>
      <h2 id="local-pathways-{slug}">Turn the {html.escape(town)} guide into a property decision</h2>
      <p class="local-search-pathways__intro">Move from public records to current property evidence, then choose the buyer, seller, or valuation path that matches the address and your next decision.</p>
      <nav class="local-search-pathways__links" aria-label="Related {html.escape(town)} real estate resources">{anchors}</nav>
    </div>
  </section>
  {END}
'''


def expected(source: str, slug: str, county: str) -> str:
    cleaned = BLOCK.sub("\n", source)
    cleaned = cleaned.replace(STYLESHEET, "")
    if "</head>" not in cleaned or "</main>" not in cleaned:
        raise RuntimeError(f"towns/{slug}.html is missing head or main")
    cleaned = cleaned.replace("</head>", STYLESHEET + "</head>", 1)
    closing = re.search(r"(?m)^[ \t]*</main>", cleaned)
    if not closing:
        raise RuntimeError(f"towns/{slug}.html has no standalone main closing tag")
    return (
        cleaned[: closing.start()]
        + pathway_block(slug, county)
        + closing.group(0)
        + cleaned[closing.end() :]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    counties = county_map()
    if not TARGETS <= set(counties):
        raise RuntimeError("priority pathway target is not in the canonical town inventory")
    stale: list[str] = []
    for slug in sorted(TARGETS):
        path = ROOT / "towns" / f"{slug}.html"
        source = path.read_text(encoding="utf-8")
        rendered = expected(source, slug, counties[slug])
        if rendered == source:
            continue
        if args.check:
            stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.write_text(rendered, encoding="utf-8")
    if stale:
        print("Stale priority town pathways:", ", ".join(stale))
        return 1
    print(
        "Priority town pathways are current."
        if args.check
        else f"Updated local pathways on {len(TARGETS)} priority town guides."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
