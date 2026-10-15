"""Apply maintained seller-planning sections to the existing static renderers.

Only explicitly listed routes change. Fail if a template marker moves instead
of silently dropping reviewed content or injecting it at the wrong location.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def apply_seller_planning(route: str, source: str) -> str:
    pages = json.loads((ROOT / "data/seller-planning-additions.json").read_text(encoding="utf-8"))["pages"]
    addition = pages.get(route)
    if addition is None:
        return source
    marker = addition["before"]
    if source.count(marker) != 1:
        raise ValueError(f"{route}: expected one seller-planning insertion marker")
    fragment = addition["html"]
    if fragment not in source:
        source = source.replace(marker, fragment + marker, 1)
    for replacement in addition.get("preservedReplacements", []):
        old, new = replacement["old"], replacement["new"]
        if new in source:
            continue
        if source.count(old) != 1:
            raise ValueError(f"{route}: expected one preserved editorial link marker")
        source = source.replace(old, new, 1)
    date = addition["modifiedOn"]
    source = re.sub(r'("dateModified"\s*:\s*")[^"]+(")', lambda match: match[1] + date + match[2], source)
    source = re.sub(r'(<meta property="article:modified_time" content=")[^"]+', lambda match: match[1] + date, source)
    source = re.sub(r'(<meta name="last-updated" content=")[^"]+', lambda match: match[1] + date, source)
    source = re.sub(r'(educational page updated )\d{4}-\d{2}-\d{2}', lambda match: match[1] + date, source)
    return source
