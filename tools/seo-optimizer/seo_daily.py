#!/usr/bin/env python3
"""Local SEO metadata auditor with a tightly gated, local-only apply mode."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path


MODE = "read-only"
NETWORK_ENABLED = False
PUSH_ENABLED = False
EMAIL_ENABLED = False
OWNER_APPROVAL = "I_APPROVE_THIS_LOCAL_SEO_METADATA_PLAN"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SKIP_DIRS = {".git", ".venv", ".vercel", "node_modules"}
ALLOWED_METADATA = {
    "description": ("name", "description"),
    "og:title": ("property", "og:title"),
    "og:description": ("property", "og:description"),
    "twitter:card": ("name", "twitter:card"),
    "twitter:title": ("name", "twitter:title"),
    "twitter:description": ("name", "twitter:description"),
}


def html_pages() -> list[Path]:
    """Return local HTML files without reading ignored dependency trees."""

    pages: list[Path] = []
    for path in REPO.rglob("*.html"):
        if any(part in SKIP_DIRS for part in path.relative_to(REPO).parts):
            continue
        pages.append(path)
    return sorted(pages)


def is_retired_page(source: str) -> bool:
    head = source.split("</head>", 1)[0].casefold()
    return bool(
        re.search(
            r'<meta\b(?=[^>]*\bname=["\']robots["\'])'
            r'(?=[^>]*\bcontent=["\'][^"\']*noindex)[^>]*>',
            head,
        )
        or "http-equiv=\"refresh\"" in head
        or "http-equiv='refresh'" in head
        or "window.location" in source.casefold()
    )


def has_meta(source: str, attr: str, value: str) -> bool:
    head = source.split("</head>", 1)[0]
    pattern = rf'<meta\b(?=[^>]*\b{re.escape(attr)}=["\']{re.escape(value)}["\'])[^>]*>'
    return bool(re.search(pattern, head, re.I))


def audit_repository() -> dict[str, object]:
    """Run a local, read-only metadata inventory and return JSON-safe counts."""

    pages = html_pages()
    indexable = 0
    retired = 0
    missing = {key: 0 for key in ALLOWED_METADATA}
    for path in pages:
        source = path.read_text(encoding="utf-8")
        if is_retired_page(source):
            retired += 1
            continue
        indexable += 1
        for key, (attr, value) in ALLOWED_METADATA.items():
            if not has_meta(source, attr, value):
                missing[key] += 1
    return {
        "mode": MODE,
        "networkEnabled": NETWORK_ENABLED,
        "mutationEnabled": False,
        "pushEnabled": PUSH_ENABLED,
        "emailEnabled": EMAIL_ENABLED,
        "htmlFiles": len(pages),
        "indexableFiles": indexable,
        "retiredFiles": retired,
        "missingMetadata": missing,
    }


def checked_target(relative_path: object) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("each change needs a non-empty relative path")
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.suffix != ".html":
        raise ValueError(f"unsafe plan path: {relative_path!r}")
    unresolved = REPO / candidate
    if unresolved.is_symlink():
        raise ValueError(f"symbolic-link targets are not eligible: {relative_path!r}")
    target = unresolved.resolve()
    try:
        target.relative_to(REPO)
    except ValueError as error:
        raise ValueError(f"plan path leaves repository: {relative_path!r}") from error
    if not target.is_file():
        raise ValueError(f"plan target is not a regular repository file: {relative_path!r}")
    if candidate.name in {"404.html", "index-fallback.html"}:
        raise ValueError(f"fallback pages are not eligible: {relative_path!r}")
    return target


def checked_metadata(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise ValueError("each change needs a non-empty metadata object")
    unknown = set(value) - set(ALLOWED_METADATA)
    if unknown:
        raise ValueError(f"metadata keys are not allowlisted: {sorted(unknown)}")
    checked: dict[str, str] = {}
    for key, raw in value.items():
        if not isinstance(raw, str) or not raw.strip() or raw != raw.strip():
            raise ValueError(f"{key} must be a trimmed, non-empty string")
        if "<" in raw or ">" in raw or len(raw) > 200:
            raise ValueError(f"{key} contains markup or exceeds 200 characters")
        if key == "twitter:card" and raw not in {"summary", "summary_large_image"}:
            raise ValueError("twitter:card must use a supported card type")
        checked[key] = raw
    return checked


def build_reviewed_updates(plan_path: Path) -> list[tuple[Path, str]]:
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read plan: {error}") from error
    if not isinstance(plan, dict) or plan.get("version") != 1:
        raise ValueError("plan must be a version 1 JSON object")
    changes = plan.get("changes")
    if not isinstance(changes, list) or not 1 <= len(changes) <= 10:
        raise ValueError("plan must contain between 1 and 10 explicit changes")

    updates: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError("each change must be an object")
        target = checked_target(change.get("path"))
        if target in seen:
            raise ValueError(f"duplicate plan target: {target.relative_to(REPO)}")
        seen.add(target)
        expected_hash = change.get("sha256")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise ValueError("each change needs an exact lowercase sha256")
        current_bytes = target.read_bytes()
        if hashlib.sha256(current_bytes).hexdigest() != expected_hash:
            raise ValueError(f"content hash changed: {target.relative_to(REPO)}")
        source = current_bytes.decode("utf-8")
        if is_retired_page(source):
            raise ValueError(f"retired/noindex pages are not eligible: {target.relative_to(REPO)}")
        if not re.search(r"</head>", source, re.I):
            raise ValueError(f"missing head boundary: {target.relative_to(REPO)}")
        metadata = checked_metadata(change.get("metadata"))
        tags: list[str] = []
        for key, raw in metadata.items():
            attr, value = ALLOWED_METADATA[key]
            if has_meta(source, attr, value):
                raise ValueError(f"{key} already exists in {target.relative_to(REPO)}")
            tags.append(f'  <meta {attr}="{value}" content="{html.escape(raw, quote=True)}">')
        block = "\n".join(tags) + "\n"
        updated = re.sub(r"</head>", block + "</head>", source, count=1, flags=re.I)
        updates.append((target, updated))
    return updates


def apply_reviewed_plan(plan_path: Path, owner_approval: str | None) -> dict[str, object]:
    """Apply only hash-pinned, allowlisted local metadata after exact approval."""

    if owner_approval != OWNER_APPROVAL:
        raise ValueError("exact owner approval phrase is required; no files changed")
    updates = build_reviewed_updates(plan_path)
    for target, updated in updates:
        target.write_text(updated, encoding="utf-8")
    return {
        "mode": "explicit-local-apply",
        "networkEnabled": NETWORK_ENABLED,
        "pushEnabled": PUSH_ENABLED,
        "emailEnabled": EMAIL_ENABLED,
        "changed": [str(path.relative_to(REPO)) for path, _ in updates],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only local SEO metadata inventory with an approval-gated apply plan."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="print the read-only local inventory (also the default)",
    )
    parser.add_argument(
        "--apply-plan",
        type=Path,
        help="apply one explicit, hash-pinned local metadata plan",
    )
    parser.add_argument(
        "--owner-approval",
        help="exact owner approval phrase required with --apply-plan",
    )
    args = parser.parse_args(argv)
    if not args.apply_plan:
        if args.owner_approval:
            parser.error("--owner-approval is valid only with --apply-plan")
        print(json.dumps(audit_repository(), sort_keys=True))
        return 0
    try:
        result = apply_reviewed_plan(args.apply_plan, args.owner_approval)
    except ValueError as error:
        print(f"DENIED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
