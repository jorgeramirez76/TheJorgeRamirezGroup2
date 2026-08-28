#!/usr/bin/env python3
"""Keep the public Jorge/person and business schema identifiers distinct.

The site historically used ``#agent`` for both the brokerage-facing business
entity and Jorge Ramirez as a person.  This synchronizer performs a surgical
JSON-LD migration: it preserves the original formatting, changes misassigned
identifiers, and gives named Jorge/person nodes the stable person identifier.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://thejorgeramirezgroup.com"
BUSINESS_ID = f"{ORIGIN}/#agent"
PERSON_ID = f"{ORIGIN}/#jorge-ramirez"

SKIP_DIRS = {".git", ".vercel", "node_modules", "crm", "docs", "property-leads-system", "staging"}
PERSON_REFERENCE_KEYS = {"author", "creator", "founder", "mainEntity"}
JSON_LD_RE = re.compile(
    r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script\s*>)',
    re.IGNORECASE | re.DOTALL,
)
BUSINESS_ID_FIELD_RE = re.compile(
    r'("@id"\s*:\s*")' + re.escape(BUSINESS_ID) + r'(")'
)


def entity_types(node: dict) -> set[str]:
    value = node.get("@type")
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    return set()


def represents_jorge(node: dict) -> bool:
    """Return whether a typed node represents Jorge rather than the business."""

    types = entity_types(node)
    name = node.get("name")
    return ("Person" in types and name == "Jorge Ramirez") or (
        "RealEstateAgent" in types and name == "Jorge Ramirez"
    )


def id_decisions(value: object, parent_key: str | None = None) -> list[bool]:
    """Map each textual ``#agent`` occurrence to whether it is person-scoped."""

    decisions: list[bool] = []
    if isinstance(value, dict):
        if value.get("@id") == BUSINESS_ID:
            reference_only = set(value) == {"@id"}
            decisions.append(
                represents_jorge(value)
                or (reference_only and parent_key in PERSON_REFERENCE_KEYS)
            )
        for key, child in value.items():
            id_key = key if isinstance(key, str) else None
            decisions.extend(id_decisions(child, id_key))
    elif isinstance(value, list):
        for child in value:
            decisions.extend(id_decisions(child, parent_key))
    return decisions


def json_object_spans(raw: str) -> list[tuple[int, int]]:
    """Return JSON object spans without being confused by braces in strings."""

    spans: list[tuple[int, int]] = []
    stack: list[int] = []
    in_string = False
    escaped = False
    for index, character in enumerate(raw):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            stack.append(index)
        elif character == "}" and stack:
            spans.append((stack.pop(), index + 1))
    if stack or in_string:
        raise ValueError("unterminated JSON object or string")
    return spans


def add_missing_person_ids(raw: str, source: Path) -> tuple[str, int]:
    """Insert ``#jorge-ramirez`` into named personal nodes that lack an ID."""

    insertions: list[tuple[int, str]] = []
    for start, end in json_object_spans(raw):
        snippet = raw[start:end]
        try:
            node = json.loads(snippet)
        except json.JSONDecodeError:
            continue
        if not isinstance(node, dict) or node.get("@id") or not represents_jorge(node):
            continue

        type_field = re.search(
            r'"@type"\s*:\s*"(?:Person|RealEstateAgent)"\s*,',
            snippet,
        )
        if type_field is None:
            raise ValueError(
                f"could not locate person @type in {source.relative_to(ROOT)}"
            )
        absolute_end = start + type_field.end()
        line_start = snippet.rfind("\n", 0, type_field.start()) + 1
        prefix = snippet[line_start : type_field.start()]
        if line_start == 0:
            insertion = f' "@id": "{PERSON_ID}",'
        else:
            insertion = f'\n{prefix}"@id": "{PERSON_ID}",'
        insertions.append((absolute_end, insertion))

    for position, insertion in sorted(insertions, reverse=True):
        raw = raw[:position] + insertion + raw[position:]
    return raw, len(insertions)


def migrate_block(raw: str, source: Path) -> tuple[str, int]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON-LD in {source.relative_to(ROOT)}: {exc}") from exc

    decisions = id_decisions(payload)
    matches = list(BUSINESS_ID_FIELD_RE.finditer(raw))
    if len(decisions) != len(matches):
        raise ValueError(
            f"identifier scan mismatch in {source.relative_to(ROOT)}: "
            f"{len(decisions)} parsed vs {len(matches)} textual"
        )

    decision_iter = iter(decisions)
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        if next(decision_iter):
            changed += 1
            return f"{match.group(1)}{PERSON_ID}{match.group(2)}"
        return match.group(0)

    migrated = BUSINESS_ID_FIELD_RE.sub(replace, raw)
    migrated, inserted = add_missing_person_ids(migrated, source)
    return migrated, changed + inserted


def migrate_source(source: str, path: Path) -> tuple[str, int]:
    total = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal total
        migrated, changed = migrate_block(match.group(2), path)
        total += changed
        return f"{match.group(1)}{migrated}{match.group(3)}"

    return JSON_LD_RE.sub(replace, source), total


def public_html_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if not (set(path.relative_to(ROOT).parts) & SKIP_DIRS)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated HTML has drift")
    args = parser.parse_args()

    changed_files: list[Path] = []
    migrated_ids = 0
    for path in public_html_files():
        source = path.read_text(encoding="utf-8")
        migrated, changed = migrate_source(source, path)
        if not changed:
            continue
        changed_files.append(path)
        migrated_ids += changed
        if not args.check:
            path.write_text(migrated, encoding="utf-8")

    mode = "drift" if args.check else "updated"
    print(f"schema entity IDs: {len(changed_files)} files, {migrated_ids} identifiers {mode}")
    if args.check and changed_files:
        for path in changed_files:
            print(path.relative_to(ROOT))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
