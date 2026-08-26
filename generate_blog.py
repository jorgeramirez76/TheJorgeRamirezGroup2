#!/usr/bin/env python3
"""Retired entry point retained only to fail closed."""

import json
from pathlib import Path

from tools.market_report_publication_gate import quarantined_generator_main


# Preserve the integrated English fair-housing quarantine inventory as an
# explicit secondary guard. This entry point is fully retired below, but
# keeping the exact owned-output set here makes that protection auditable.
QUARANTINE_MANIFEST = Path(__file__).resolve().parent / "data" / "english-fair-housing-quarantine.json"
QUARANTINED_OUTPUTS = frozenset(
    Path(item["file"]).name
    for item in json.loads(QUARANTINE_MANIFEST.read_text(encoding="utf-8"))["pages"]
)


def is_quarantined_output(filename: str) -> bool:
    if filename in QUARANTINED_OUTPUTS:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(quarantined_generator_main('town report page'))
