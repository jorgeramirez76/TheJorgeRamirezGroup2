#!/usr/bin/env python3
"""Retained entry point for the quarantined Somerset clone inventory.

The former implementation copied another municipality's page and inserted
unsupported local figures. Running this command now renders only the compact,
English noindex fallbacks declared in the versioned fallback policy. Spanish
pages are intentionally outside this remediation and are not modified.
"""

from __future__ import annotations

import argparse
import sys

from scripts.render_noindex_town_fallbacks import (
    ROOT,
    check_fallbacks,
    group_slugs,
    render_fallbacks,
)


MANAGED_GROUP_ID = "wrong-town-somerset-clones"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()
    slugs = group_slugs(MANAGED_GROUP_ID)

    if args.check:
        mismatches = check_fallbacks(slugs=slugs)
        if mismatches:
            for path in mismatches:
                print(f"fallback drift: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"Somerset fallback check passed: {len(slugs)} routes")
        return 0

    changed = render_fallbacks(slugs=slugs)
    print(f"rendered {len(changed)} changed Somerset fallback pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
