#!/usr/bin/env python3
"""Retired unsafe programmatic SERP-page generator.

The former generator depended on an untracked ``/tmp`` dataset and emitted
undated market figures, commute promises, school language, fixed costs,
personal-investor claims, and outcome comparisons. Its routes are now governed
by ``scripts/retire_programmatic_doorways.py`` and the checked-in retirement
manifest. This entry point intentionally refuses to generate or edit files.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "gen_serp_pages.py is retired and cannot write public pages. "
        "Run `python3 scripts/retire_programmatic_doorways.py --check` "
        "to verify the replacement redirects and fallbacks.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
