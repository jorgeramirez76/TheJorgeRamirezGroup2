#!/usr/bin/env python3
"""Safely maintain sitemap ``lastmod`` values for explicitly changed HTML files.

Dates are always supplied by the caller.  This module intentionally never
derives a publication date from a file timestamp.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urlsplit


ORIGIN = "https://thejorgeramirezgroup.com"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

URL_BLOCK_RE = re.compile(
    r"<(?:[A-Za-z_][\w.-]*:)?url\b[^>]*>.*?</(?:[A-Za-z_][\w.-]*:)?url\s*>",
    re.IGNORECASE | re.DOTALL,
)
LOC_RE = re.compile(
    r"<(?:[A-Za-z_][\w.-]*:)?loc\b[^>]*>(?P<value>.*?)"
    r"</(?:[A-Za-z_][\w.-]*:)?loc\s*>",
    re.IGNORECASE | re.DOTALL,
)
LASTMOD_RE = re.compile(
    r"<(?:[A-Za-z_][\w.-]*:)?lastmod\b[^>]*>(?P<value>.*?)"
    r"</(?:[A-Za-z_][\w.-]*:)?lastmod\s*>",
    re.IGNORECASE | re.DOTALL,
)


class InvalidInput(ValueError):
    """Raised before mutation when a date or changed path is unsafe."""


class MaintenanceError(RuntimeError):
    """Raised before mutation when repository metadata cannot be read safely."""


@dataclass(frozen=True)
class PageDecision:
    """How one changed HTML path was classified."""

    path: str
    status: str
    canonical_url: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class UrlDecision:
    """What happened to one eligible canonical URL in its language sitemap."""

    canonical_url: str
    sitemap: str
    status: str
    old_lastmod: str | None = None
    detail: str | None = None


@dataclass
class MaintenanceReport:
    """Complete, deterministic report for one maintenance run."""

    mode: str
    date: str
    pages: list[PageDecision] = field(default_factory=list)
    urls: list[UrlDecision] = field(default_factory=list)


class _SeoParser(HTMLParser):
    """Collect only the tags needed to decide whether a page is indexable."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.robot_directives: list[str] = []
        self.has_refresh = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "link":
            rel = {token.lower() for token in values.get("rel", "").split()}
            if "canonical" in rel:
                self.canonicals.append(values.get("href", "").strip())
        elif tag.lower() == "meta":
            name = values.get("name", "").lower()
            if name in {"robots", "googlebot", "bingbot"}:
                self.robot_directives.append(values.get("content", ""))
            if values.get("http-equiv", "").lower() == "refresh":
                self.has_refresh = True


def _validated_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InvalidInput(f"invalid date {value!r}; expected YYYY-MM-DD")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as error:
        raise InvalidInput(f"invalid calendar date {value!r}") from error
    if parsed.isoformat() != value:
        raise InvalidInput(f"invalid date {value!r}; expected YYYY-MM-DD")
    return value


def _validated_paths(
    repo_root: Path,
    changed_paths: Sequence[str | os.PathLike[str]],
) -> tuple[Path, list[tuple[Path, str]]]:
    try:
        root = repo_root.resolve(strict=True)
    except FileNotFoundError as error:
        raise InvalidInput(f"repository root does not exist: {repo_root}") from error
    if not root.is_dir():
        raise InvalidInput(f"repository root is not a directory: {root}")
    if not changed_paths:
        raise InvalidInput("at least one changed HTML path is required")

    validated: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for raw_path in changed_paths:
        supplied = Path(raw_path)
        candidate = supplied if supplied.is_absolute() else root / supplied
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError as error:
            raise InvalidInput(f"changed path does not exist: {raw_path}") from error
        try:
            relative = resolved.relative_to(root)
        except ValueError as error:
            raise InvalidInput(f"changed path is outside the repository: {raw_path}") from error
        if not resolved.is_file():
            raise InvalidInput(f"changed path is not a file: {raw_path}")
        if resolved.suffix.lower() != ".html":
            raise InvalidInput(f"changed path is not an HTML file: {raw_path}")
        if ".git" in relative.parts:
            raise InvalidInput(f"changed path is repository metadata: {raw_path}")
        if resolved in seen:
            continue
        seen.add(resolved)
        validated.append((resolved, relative.as_posix()))
    return root, validated


def _deployed_path(relative: str) -> str:
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[: -len("/index.html")]
    return "/" + relative[: -len(".html")]


def _normalized_route(path: str) -> str:
    normalized = path.rstrip("/")
    return normalized or "/"


def _canonical_url(raw: str) -> tuple[str | None, str | None]:
    parsed = urlsplit(raw)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "thejorgeramirezgroup.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.query
        or parsed.fragment
    ):
        return None, "invalid-canonical"
    route = _normalized_route(parsed.path or "/")
    if route.endswith(".html"):
        return None, "non-extensionless-canonical"
    if not route.startswith("/") or "//" in route:
        return None, "invalid-canonical"
    return ORIGIN + route, None


def _exact_redirect_sources(repo_root: Path) -> set[str]:
    config_path = repo_root / "vercel.json"
    if not config_path.exists():
        return set()
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MaintenanceError(f"cannot safely read {config_path.name}: {error}") from error
    if not isinstance(config, dict) or not isinstance(config.get("redirects", []), list):
        raise MaintenanceError(f"cannot safely read {config_path.name}: invalid redirects structure")

    sources: set[str] = set()
    for item in config.get("redirects", []):
        if not isinstance(item, dict) or item.get("has"):
            continue
        source = item.get("source")
        if not isinstance(source, str) or ":" in source or "*" in source:
            continue
        sources.add(_normalized_route(source))
    return sources


def _is_noindex(directives: Iterable[str]) -> bool:
    return any(
        re.search(r"(?:^|[\s,])noindex(?:$|[\s,])", directive, re.IGNORECASE)
        for directive in directives
    )


def _classify_page(
    path: Path,
    relative: str,
    redirect_sources: set[str],
) -> PageDecision:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise MaintenanceError(f"cannot safely read {relative}: {error}") from error

    parser = _SeoParser()
    parser.feed(source)
    if _is_noindex(parser.robot_directives):
        return PageDecision(relative, "skipped", reason="noindex")
    if parser.has_refresh:
        return PageDecision(relative, "skipped", reason="meta-refresh")
    if not parser.canonicals:
        return PageDecision(relative, "skipped", reason="missing-canonical")
    if len(parser.canonicals) != 1:
        return PageDecision(relative, "skipped", reason="multiple-canonicals")

    canonical, invalid_reason = _canonical_url(parser.canonicals[0])
    if invalid_reason:
        return PageDecision(relative, "skipped", reason=invalid_reason)
    assert canonical is not None
    canonical_route = _normalized_route(urlsplit(canonical).path)
    deployed_route = _normalized_route(_deployed_path(relative))
    if canonical_route != deployed_route:
        return PageDecision(relative, "skipped", reason="non-self-canonical")
    if deployed_route in redirect_sources:
        return PageDecision(relative, "skipped", reason="redirect-source")
    return PageDecision(relative, "eligible", canonical_url=canonical)


def _sitemap_for(canonical_url: str) -> str:
    route = _normalized_route(urlsplit(canonical_url).path)
    if route == "/es" or route.startswith("/es/"):
        return "sitemap-es.xml"
    return "sitemap.xml"


def _normalized_sitemap_loc(raw: str) -> str | None:
    parsed = urlsplit(html.unescape(raw.strip()))
    if (
        parsed.scheme != "https"
        or parsed.netloc != "thejorgeramirezgroup.com"
        or parsed.query
        or parsed.fragment
    ):
        return None
    return ORIGIN + _normalized_route(parsed.path or "/")


def _replace_lastmod_value(block: str, match: re.Match[str], value: str) -> str:
    old = match.group("value")
    if old.strip():
        leading = old[: len(old) - len(old.lstrip())]
        trailing = old[len(old.rstrip()) :]
        replacement = leading + value + trailing
    else:
        replacement = value
    return block[: match.start("value")] + replacement + block[match.end("value") :]


def _plan_sitemap(
    sitemap_name: str,
    content: str,
    target_urls: Sequence[str],
    date_value: str,
    *,
    apply: bool,
) -> tuple[str, list[UrlDecision]]:
    try:
        root = ET.fromstring(content.encode("utf-8"))
    except ET.ParseError as error:
        raise MaintenanceError(f"{sitemap_name} is not valid XML: {error}") from error
    if root.tag.rsplit("}", 1)[-1].lower() != "urlset":
        raise MaintenanceError(f"{sitemap_name} is not a URL-set sitemap")

    blocks = list(URL_BLOCK_RE.finditer(content))
    entries: dict[str, list[int]] = {}
    for index, block_match in enumerate(blocks):
        loc_matches = list(LOC_RE.finditer(block_match.group(0)))
        if len(loc_matches) != 1:
            continue
        canonical = _normalized_sitemap_loc(loc_matches[0].group("value"))
        if canonical:
            entries.setdefault(canonical, []).append(index)

    replacements: dict[int, str] = {}
    decisions: list[UrlDecision] = []
    for canonical_url in sorted(target_urls):
        matching_blocks = entries.get(canonical_url, [])
        if not matching_blocks:
            decisions.append(
                UrlDecision(
                    canonical_url,
                    sitemap_name,
                    "unmatched",
                    detail="no matching <loc> entry",
                )
            )
            continue
        if len(matching_blocks) != 1:
            decisions.append(
                UrlDecision(
                    canonical_url,
                    sitemap_name,
                    "ambiguous",
                    detail="multiple matching <loc> entries",
                )
            )
            continue

        index = matching_blocks[0]
        block = blocks[index].group(0)
        lastmods = list(LASTMOD_RE.finditer(block))
        if not lastmods:
            decisions.append(
                UrlDecision(
                    canonical_url,
                    sitemap_name,
                    "missing-lastmod",
                    detail="matching entry has no <lastmod>",
                )
            )
            continue
        if len(lastmods) != 1:
            decisions.append(
                UrlDecision(
                    canonical_url,
                    sitemap_name,
                    "ambiguous",
                    detail="matching entry has multiple <lastmod> elements",
                )
            )
            continue

        old_lastmod = lastmods[0].group("value").strip()
        if old_lastmod == date_value:
            decisions.append(
                UrlDecision(canonical_url, sitemap_name, "current", old_lastmod)
            )
            continue
        replacements[index] = _replace_lastmod_value(block, lastmods[0], date_value)
        decisions.append(
            UrlDecision(
                canonical_url,
                sitemap_name,
                "updated" if apply else "would-update",
                old_lastmod,
            )
        )

    if not replacements:
        return content, decisions
    pieces: list[str] = []
    cursor = 0
    for index, block_match in enumerate(blocks):
        pieces.append(content[cursor : block_match.start()])
        pieces.append(replacements.get(index, block_match.group(0)))
        cursor = block_match.end()
    pieces.append(content[cursor:])
    return "".join(pieces), decisions


def _atomic_write_all(updates: dict[Path, str]) -> None:
    """Stage every changed sitemap before replacing any original file."""

    staged: list[tuple[Path, Path]] = []
    try:
        for destination, content in updates.items():
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=destination.parent,
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(content.encode("utf-8"))
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(temporary, stat.S_IMODE(destination.stat().st_mode))
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
            staged.append((temporary, destination))
        for temporary, destination in staged:
            os.replace(temporary, destination)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def maintain_lastmods(
    repo_root: Path,
    changed_paths: Sequence[str | os.PathLike[str]],
    date_value: str,
    *,
    apply: bool = False,
) -> MaintenanceReport:
    """Plan or apply lastmod updates for canonical, indexable changed pages.

    All date and path validation, page classification, and sitemap parsing is
    completed before any file is written. Missing entries and missing
    ``lastmod`` elements are reported but are never added automatically.
    """

    valid_date = _validated_date(date_value)
    root, paths = _validated_paths(Path(repo_root), changed_paths)
    redirects = _exact_redirect_sources(root)
    pages = [_classify_page(path, relative, redirects) for path, relative in paths]
    report = MaintenanceReport("apply" if apply else "check", valid_date, pages=pages)

    targets: dict[str, set[str]] = {}
    for page in pages:
        if page.status != "eligible" or page.canonical_url is None:
            continue
        targets.setdefault(_sitemap_for(page.canonical_url), set()).add(page.canonical_url)

    planned_updates: dict[Path, str] = {}
    for sitemap_name in sorted(targets):
        sitemap_path = root / sitemap_name
        if not sitemap_path.is_file():
            report.urls.extend(
                UrlDecision(
                    url,
                    sitemap_name,
                    "unmatched",
                    detail="sitemap file does not exist",
                )
                for url in sorted(targets[sitemap_name])
            )
            continue
        try:
            content = sitemap_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise MaintenanceError(f"cannot safely read {sitemap_name}: {error}") from error
        updated, decisions = _plan_sitemap(
            sitemap_name,
            content,
            sorted(targets[sitemap_name]),
            valid_date,
            apply=apply,
        )
        report.urls.extend(decisions)
        if apply and updated != content:
            planned_updates[sitemap_path] = updated

    if apply and planned_updates:
        _atomic_write_all(planned_updates)
    return report


def _print_report(report: MaintenanceReport) -> None:
    for page in report.pages:
        if page.status == "eligible":
            print(f"eligible {page.path} -> {page.canonical_url}")
        else:
            print(f"skipped {page.path}: {page.reason}")
    for item in report.urls:
        old = f" (was {item.old_lastmod})" if item.old_lastmod is not None else ""
        detail = f"; {item.detail}" if item.detail else ""
        print(f"{item.status} {item.sitemap}: {item.canonical_url}{old}{detail}")
    counts: dict[str, int] = {}
    for item in report.urls:
        counts[item.status] = counts.get(item.status, 0) + 1
    count_text = ", ".join(f"{name}={counts[name]}" for name in sorted(counts)) or "no-eligible-urls"
    print(f"summary mode={report.mode} date={report.date}: {count_text}")


def _needs_attention(report: MaintenanceReport) -> bool:
    gap_statuses = {"unmatched", "missing-lastmod", "ambiguous"}
    if any(item.status in gap_statuses for item in report.urls):
        return True
    return report.mode == "check" and any(
        item.status == "would-update" for item in report.urls
    )


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Update existing sitemap lastmod values for explicitly changed, "
            "self-canonical indexable HTML files."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        dest="mode",
        action="store_const",
        const="check",
        help="report drift without writing (exits 1 when action is needed)",
    )
    mode.add_argument(
        "--dry-run",
        dest="mode",
        action="store_const",
        const="check",
        help="alias for --check",
    )
    mode.add_argument(
        "--apply",
        dest="mode",
        action="store_const",
        const="apply",
        help="apply only safe updates to existing lastmod elements",
    )
    parser.add_argument("--date", required=True, help="explicit YYYY-MM-DD lastmod date")
    parser.add_argument("paths", nargs="+", help="changed HTML paths inside the repository")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    repo_root: Path = REPOSITORY_ROOT,
) -> int:
    args = _argument_parser().parse_args(argv)
    try:
        report = maintain_lastmods(
            Path(repo_root),
            args.paths,
            args.date,
            apply=args.mode == "apply",
        )
    except (InvalidInput, MaintenanceError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    _print_report(report)
    return 1 if _needs_attention(report) else 0


if __name__ == "__main__":
    sys.exit(main())
