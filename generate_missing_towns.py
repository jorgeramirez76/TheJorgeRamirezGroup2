#!/usr/bin/env python3
"""Retired compatibility entry point for the former cloned-town generator.

The former command cloned one town into other municipalities and injected
unsupported prices, school scores, and travel times. It now delegates only to
the versioned evidence/noindex remediation renderer, which owns every affected
route and includes a deterministic drift check.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RENDERER = ROOT / "scripts" / "remediate_indexable_towns.py"


def main() -> int:
    return subprocess.run(
        [sys.executable, str(RENDERER), *sys.argv[1:]],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
