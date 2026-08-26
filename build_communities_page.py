#!/usr/bin/env python3
"""Retired compatibility entry point for the legacy communities generator.

The former generator republished subjective rankings and unsupported local
figures. The canonical hub is now synchronized only from the reviewed town
inventory in ``data/site-facts.json``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SYNC = ROOT / "scripts" / "sync_communities_from_facts.py"


def main() -> int:
    return subprocess.run(
        [sys.executable, str(SYNC)],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
