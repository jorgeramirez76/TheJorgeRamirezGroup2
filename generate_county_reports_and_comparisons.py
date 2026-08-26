#!/usr/bin/env python3
"""Retired entry point retained only to fail closed."""

import json
from pathlib import Path

from tools.market_report_publication_gate import quarantined_generator_main



if __name__ == "__main__":
    raise SystemExit(quarantined_generator_main('county report page'))
