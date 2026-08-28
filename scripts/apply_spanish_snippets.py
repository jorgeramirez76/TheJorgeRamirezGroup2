#!/usr/bin/env python3
"""Apply the reviewed Spanish snippet mapping and synchronize social metadata."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.remediate_spanish_towns import spanish_managed_slugs  # noqa: E402

MAPPING = ROOT / "data" / "spanish-snippet-backlog.json"
QUARANTINE = ROOT / "data" / "spanish-fair-housing-quarantine.json"
META_TAG = re.compile(r"<meta\b[^>]*>", re.IGNORECASE | re.DOTALL)
MANAGED_SPANISH_TOWN_PATHS = {
    f"es/towns/{slug}.html" for slug in spanish_managed_slugs()
}
MARKET_GENERATOR_MANIFESTS = (
    ROOT / "data" / "union-morris-town-market-sources-2026-08-26.json",
    ROOT / "data" / "town-market-research-essex-middlesex-somerset.json",
    ROOT / "data" / "county-market-report-sources-2026-08-26.json",
)


def generator_managed_market_paths() -> set[str]:
    """Return Spanish pages whose complete metadata is owned by market renderers."""

    managed: set[str] = set()
    for manifest_path in MARKET_GENERATOR_MANIFESTS:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        reports = manifest.get("reports")
        if not isinstance(reports, list) or not reports:
            raise ValueError(f"{manifest_path.name}: missing reports inventory")
        for report in reports:
            route = report.get("routes", {}).get("es")
            if not isinstance(route, str) or not route.startswith("/es/"):
                raise ValueError(
                    f"{manifest_path.name}: report lacks an absolute Spanish route"
                )
            relative = route.removeprefix("/")
            if not relative.endswith(".html"):
                relative += ".html"
            if relative in managed:
                raise ValueError(f"duplicate generator-owned route: {relative}")
            managed.add(relative)
    return managed


MANAGED_GENERATED_SPANISH_PATHS = (
    MANAGED_SPANISH_TOWN_PATHS | generator_managed_market_paths()
)


def attribute_value(tag: str, attribute: str) -> str | None:
    match = re.search(
        rf"\b{re.escape(attribute)}\s*=\s*([\"'])(.*?)\1",
        tag,
        re.IGNORECASE | re.DOTALL,
    )
    return html.unescape(match.group(2)) if match else None


def escaped_attribute(value: str) -> str:
    return html.escape(value, quote=False).replace('"', "&quot;")


def is_noindex(document: str) -> bool:
    """Return whether a document explicitly opts out of indexing.

    Consolidated archive fallbacks may remain in the snippet inventory for
    historical accountability.  The snippet updater must never turn those
    neutral fallbacks back into indexable-looking landing pages.
    """
    for match in META_TAG.finditer(document):
        tag = match.group(0)
        name = attribute_value(tag, "name")
        content = attribute_value(tag, "content")
        if not name or name.casefold() != "robots" or not content:
            continue
        directives = {
            directive.casefold()
            for directive in re.split(r"[\s,]+", content)
            if directive
        }
        if "noindex" in directives:
            return True
    return False


def replace_meta(
    document: str,
    selector_attribute: str,
    selector_value: str,
    content: str,
) -> tuple[str, int]:
    replacements = 0

    def update(match: re.Match[str]) -> str:
        nonlocal replacements
        tag = match.group(0)
        value = attribute_value(tag, selector_attribute)
        if value is None or value.lower() != selector_value.lower():
            return tag

        content_match = re.search(
            r"\bcontent\s*=\s*([\"'])(.*?)\1",
            tag,
            re.IGNORECASE | re.DOTALL,
        )
        if not content_match:
            raise ValueError(
                f"meta {selector_attribute}={selector_value} has no content attribute"
            )

        replacement = f'content="{escaped_attribute(content)}"'
        replacements += 1
        return tag[: content_match.start()] + replacement + tag[content_match.end() :]

    return META_TAG.sub(update, document), replacements


def replace_title(document: str, title: str) -> str:
    pattern = re.compile(r"(<title>)(.*?)(</title>)", re.IGNORECASE | re.DOTALL)
    updated, count = pattern.subn(
        lambda match: match.group(1) + html.escape(title, quote=False) + match.group(3),
        document,
    )
    if count != 1:
        raise ValueError(f"expected one title element, found {count}")
    return updated


def render(document: str, metadata: dict[str, str]) -> str:
    if "title" in metadata:
        document = replace_title(document, metadata["title"])
        for attribute, value in (
            ("name", "title"),
            ("name", "og:title"),
            ("property", "og:title"),
            ("name", "twitter:title"),
            ("property", "twitter:title"),
        ):
            document, _ = replace_meta(
                document,
                attribute,
                value,
                metadata["title"],
            )

    if "description" in metadata:
        document, count = replace_meta(
            document,
            "name",
            "description",
            metadata["description"],
        )
        if count != 1:
            raise ValueError(f"expected one meta description, found {count}")
        for attribute, value in (
            ("name", "og:description"),
            ("property", "og:description"),
            ("name", "twitter:description"),
            ("property", "twitter:description"),
        ):
            document, _ = replace_meta(
                document,
                attribute,
                value,
                metadata["description"],
            )

    return document


def load_pages() -> dict[str, dict[str, str]]:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    pages: dict[str, dict[str, str]] = mapping["pages"]
    protected = {
        item["file"]
        for item in json.loads(QUARANTINE.read_text(encoding="utf-8"))["pages"]
    }
    pages = {
        relative: metadata
        for relative, metadata in pages.items()
        if relative not in protected
        and relative not in MANAGED_GENERATED_SPANISH_PATHS
    }
    for relative, metadata in pages.items():
        if not relative.startswith("es/"):
            raise ValueError(f"Spanish mapping cannot modify non-es page: {relative}")
        unexpected = set(metadata) - {"title", "description"}
        if unexpected:
            raise ValueError(f"{relative}: unsupported fields {sorted(unexpected)}")
    return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="report mapped files that differ without writing them",
    )
    args = parser.parse_args()

    pages = load_pages()
    changed: list[str] = []

    for relative, metadata in pages.items():
        if relative in MANAGED_SPANISH_TOWN_PATHS:
            continue
        path = ROOT / relative
        before = path.read_text(encoding="utf-8")
        if is_noindex(before):
            continue
        try:
            after = render(before, metadata)
        except ValueError as error:
            raise ValueError(f"{relative}: {error}") from error
        if before == after:
            continue
        changed.append(relative)
        if not args.check:
            path.write_text(after, encoding="utf-8")

    if args.check and changed:
        print(f"{len(changed)} files do not match {MAPPING.relative_to(ROOT)}")
        for relative in changed:
            print(relative)
        return 1

    action = "updated" if changed else "verified"
    print(f"{action} {len(pages)} mapped pages; {len(changed)} files changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
