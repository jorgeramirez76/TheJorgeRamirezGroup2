#!/usr/bin/env python3
"""Retirement gate for an obsolete, unsafe site-mutation utility."""

from __future__ import annotations

import argparse
import json
import sys


STATUS = "retired"
MUTATION_ENABLED = False
REPLACEMENT_CHECKS = (
    "python3 tools/check_technical_seo.py",
    "python3 tools/sync_sitemap.py --check",
    "python3 tools/check_spanish_fair_housing.py",
)


def retirement_record() -> dict[str, object]:
    """Return the machine-readable, read-only retirement contract."""

    return {
        "status": STATUS,
        "mutationEnabled": MUTATION_ENABLED,
        "readOnly": True,
        "replacementChecks": list(REPLACEMENT_CHECKS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RETIRED: this legacy entry point does not modify files."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="print the read-only retirement record",
    )
    args = parser.parse_args(argv)
    if args.check:
        print(json.dumps(retirement_record(), sort_keys=True))
        return 0

    print(
        "RETIRED: fix_site_issues_v3.py does not modify files; run the read-only "
        "replacement checks listed by --check.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
