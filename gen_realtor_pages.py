#!/usr/bin/env python3
"""Maintain redirect-only compatibility fallbacks for retired realtor URLs.

The public redirect source of truth is ``vercel.json``. This utility does not
create landing pages, schema, sales copy, or market content. It only mirrors
the permanent realtor redirects as small ``noindex, follow`` HTML fallbacks
for hosts or local previews where Vercel redirect handling is unavailable.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "realtor"
VERCEL_PATH = ROOT / "vercel.json"
SITE_ORIGIN = "https://thejorgeramirezgroup.com"
TOWN_RULE = re.compile(r"^/realtor/([a-z0-9-]+)-nj$")
EXPECTED_TOWN_COUNT = 138


class RedirectContractError(RuntimeError):
    """Raised when the redirect inventory is unsafe or inconsistent."""


def load_redirect_inventory() -> dict[str, str]:
    config = json.loads(VERCEL_PATH.read_text(encoding="utf-8"))
    redirects = config.get("redirects", [])

    wildcard = [
        item
        for item in redirects
        if item.get("source") == "/realtor/:slug-nj.html"
    ]
    expected_wildcard = [
        {
            "source": "/realtor/:slug-nj.html",
            "destination": "/towns/:slug",
            "permanent": True,
        }
    ]
    if wildcard != expected_wildcard:
        raise RedirectContractError(
            "vercel.json must retain the permanent realtor .html wildcard"
        )

    hub = [item for item in redirects if item.get("source") == "/realtor"]
    expected_hub = [
        {"source": "/realtor", "destination": "/communities", "permanent": True}
    ]
    if hub != expected_hub:
        raise RedirectContractError(
            "vercel.json must redirect /realtor directly to /communities"
        )
    if not (ROOT / "communities.html").exists():
        raise RedirectContractError("missing /communities destination page")

    inventory: dict[str, str] = {"index.html": "/communities"}
    for item in redirects:
        source = str(item.get("source", ""))
        match = TOWN_RULE.fullmatch(source)
        if not match:
            continue
        slug = match.group(1)
        destination = f"/towns/{slug}"
        if item.get("destination") != destination or item.get("permanent") is not True:
            raise RedirectContractError(
                f"{source} must redirect permanently and directly to {destination}"
            )
        if not (ROOT / "towns" / f"{slug}.html").exists():
            raise RedirectContractError(f"missing destination page: {destination}")
        filename = f"{slug}-nj.html"
        if filename in inventory:
            raise RedirectContractError(f"duplicate realtor redirect: {source}")
        inventory[filename] = destination

    town_count = len(inventory) - 1
    if town_count != EXPECTED_TOWN_COUNT:
        raise RedirectContractError(
            f"expected {EXPECTED_TOWN_COUNT} town redirects, found {town_count}"
        )
    return dict(sorted(inventory.items()))


def destination_label(filename: str) -> str:
    if filename == "index.html":
        return "communities guide"
    slug = filename.removesuffix("-nj.html")
    return f"{slug.replace('-', ' ').title()} town guide"


def render_fallback(filename: str, destination: str) -> str:
    label = destination_label(filename)
    safe_destination = html.escape(destination, quote=True)
    safe_canonical = html.escape(SITE_ORIGIN + destination, quote=True)
    safe_label = html.escape(label)
    javascript_destination = json.dumps(destination)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, follow">
  <meta http-equiv="refresh" content="0;url={safe_destination}">
  <link rel="canonical" href="{safe_canonical}">
  <title>Page moved | The Jorge Ramirez Group</title>
  <style>
    :root{{--ink:#0a0a0a;--red:#8b0d22;--gold:#b8962e;--ivory:#fafaf8}}
    *{{box-sizing:border-box}}
    body{{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:var(--ink);color:var(--ivory);font:16px/1.6 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
    main{{width:min(100%,640px);padding:clamp(28px,7vw,56px);border:1px solid rgba(184,150,46,.55);border-radius:18px;background:linear-gradient(145deg,#111,#080808);box-shadow:0 24px 70px rgba(0,0,0,.35)}}
    .eyebrow{{margin:0 0 12px;color:var(--gold);font-size:.78rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}}
    h1{{margin:0 0 14px;font:600 clamp(2rem,8vw,3.5rem)/1.05 Georgia,"Times New Roman",serif}}
    p{{margin:0 0 24px;color:#d8d5cf}}
    a{{display:inline-block;padding:12px 18px;border-radius:999px;background:var(--red);color:#fff;font-weight:700;text-decoration:none}}
    a:hover{{background:#c41230}}
    a:focus-visible{{outline:3px solid var(--gold);outline-offset:4px}}
  </style>
  <script>window.location.replace({javascript_destination})</script>
</head>
<body>
  <main id="main">
    <p class="eyebrow">Page moved</p>
    <h1>This page has moved</h1>
    <p>The requested location now points to the {safe_label}.</p>
    <a href="{safe_destination}">Continue to the {safe_label}</a>
  </main>
</body>
</html>
"""


def current_files() -> set[str]:
    return {path.name for path in OUT_DIR.glob("*.html")}


def check_fallbacks(inventory: dict[str, str]) -> list[str]:
    failures: list[str] = []
    expected_files = set(inventory)
    actual_files = current_files()
    for filename in sorted(expected_files - actual_files):
        failures.append(f"missing fallback: realtor/{filename}")
    for filename in sorted(actual_files - expected_files):
        failures.append(f"unexpected fallback: realtor/{filename}")
    for filename, destination in inventory.items():
        path = OUT_DIR / filename
        if path.exists() and path.read_text(encoding="utf-8") != render_fallback(
            filename, destination
        ):
            failures.append(f"stale fallback: realtor/{filename}")
    return failures


def write_fallbacks(inventory: dict[str, str]) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    unexpected = current_files() - set(inventory)
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise RedirectContractError(
            f"refusing to overwrite an unexpected realtor inventory: {names}"
        )
    for filename, destination in inventory.items():
        (OUT_DIR / filename).write_text(
            render_fallback(filename, destination), encoding="utf-8"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the redirect fallbacks without changing files",
    )
    args = parser.parse_args()

    try:
        inventory = load_redirect_inventory()
        if args.check:
            failures = check_fallbacks(inventory)
            if failures:
                print("\n".join(failures), file=sys.stderr)
                return 1
            print(f"{len(inventory)} redirect fallbacks are current")
            return 0
        write_fallbacks(inventory)
        print(f"Updated {len(inventory)} redirect-only fallbacks in {OUT_DIR}")
        return 0
    except (OSError, json.JSONDecodeError, RedirectContractError) as error:
        print(f"realtor fallback generation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
