#!/usr/bin/env python3
"""Audit town guides for unsupported boilerplate and near-exact templates.

The default CI gate blocks unsupported claims at any length and near-exact
long-form templates, the highest-risk form of scaled content found in this
site audit. ``--strict`` also makes the shorter legacy template inventory a
failure so that it can be worked down deliberately without hiding the debt.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
BLOCKING_MINIMUM_WORDS = 3_000
BLOCKING_SIMILARITY = 0.90
REVIEW_MINIMUM_WORDS = 750
REVIEW_SIMILARITY = 0.98
SHINGLE_SIZE = 8
HIGH_RISK_SLUGS = {
    "cranbury",
    "montville",
    "pequannock-township",
    "roseland",
    "south-river",
    "warren-township",
    "watchung",
    "west-caldwell",
    "winfield",
}

UNSUPPORTED_CLAIMS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("helped hundreds", re.compile(r"helped\s+hundreds|he\s+ayudado\s+a\s+cientos", re.I)),
    (
        "healthy inventory",
        re.compile(
            r"healthy\s+inventory|inventario\s+saludable|"
            r"niveles\s+de\s+inventario\s+saludables",
            re.I,
        ),
    ),
    (
        "active development pipeline",
        re.compile(
            r"active\s+development\s+pipeline|"
            r"(?:proyectos?|canal)\s+de\s+desarrollo\s+activ",
            re.I,
        ),
    ),
    ("reliable returns", re.compile(r"reliable\s+returns|rendimientos\s+confiables", re.I)),
    (
        "best for families",
        re.compile(
            r"best\s+(?:neighborhood\s+)?for\s+families|"
            r"mejor\s+(?:vecindario\s+)?para\s+(?:las\s+)?familias",
            re.I,
        ),
    ),
)


def robots_noindex(source: str) -> bool:
    tags = re.findall(
        r'<meta\b[^>]*\bname=["\']robots["\'][^>]*>', source, flags=re.IGNORECASE
    )
    return any(re.search(r'\bcontent=["\'][^"\']*\bnoindex\b', tag, re.I) for tag in tags)


def redirect_stub(source: str) -> bool:
    return bool(
        re.search(r'<meta\b[^>]*\bhttp-equiv=["\']refresh["\']', source, re.IGNORECASE)
    )


def normalized_main_text(source: str, slug: str) -> str:
    """Return comparable visible main copy with page-specific tokens removed."""

    main = re.search(r"<main\b[^>]*>(.*?)</main>", source, flags=re.I | re.S)
    visible = main.group(1) if main else source
    visible = re.sub(
        r"<(?:script|style|template)\b[^>]*>.*?</(?:script|style|template)>",
        " ",
        visible,
        flags=re.I | re.S,
    )
    visible = re.sub(r"<!--.*?-->", " ", visible, flags=re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)
    visible = html.unescape(visible).lower()

    place_name = slug.replace("-", " ")
    place_variants = {
        place_name,
        place_name.removesuffix(" township"),
        place_name.removesuffix(" borough"),
    }
    for variant in sorted(place_variants, key=len, reverse=True):
        if len(variant) > 2:
            visible = re.sub(rf"\b{re.escape(variant)}\b", " townname ", visible)

    visible = unicodedata.normalize("NFKD", visible).encode("ascii", "ignore").decode()
    visible = re.sub(r"\b\d[\d,.]*\b", " number ", visible)
    tokens = re.findall(r"[a-z]+", visible)
    return " ".join(tokens)


@dataclass(frozen=True)
class TownPage:
    path: Path
    language: str
    slug: str
    source: str
    normalized_text: str
    word_count: int
    indexable: bool

    @classmethod
    def from_source(cls, path: Path, source: str) -> "TownPage":
        language = "es" if "es" in path.parts and "towns" in path.parts else "en"
        normalized = normalized_main_text(source, path.stem)
        return cls(
            path=path,
            language=language,
            slug=path.stem,
            source=source,
            normalized_text=normalized,
            word_count=len(normalized.split()),
            indexable=not robots_noindex(source) and not redirect_stub(source),
        )


def scan_town_pages(root: Path = ROOT) -> list[TownPage]:
    paths = [
        *sorted((root / "towns").glob("*.html")),
        *sorted((root / "es" / "towns").glob("*.html")),
    ]
    return [
        TownPage.from_source(path, path.read_text(encoding="utf-8", errors="replace"))
        for path in paths
    ]


def shingles(text: str, size: int = SHINGLE_SIZE) -> set[tuple[str, ...]]:
    words = text.split()
    return {tuple(words[index : index + size]) for index in range(len(words) - size + 1)}


def near_duplicate_groups(
    pages: list[TownPage],
    *,
    threshold: float,
    minimum_words: int,
) -> list[list[TownPage]]:
    """Group same-language indexable pages joined by near-exact similarity."""

    eligible = [page for page in pages if page.indexable and page.word_count >= minimum_words]
    fingerprints = {page.path: shingles(page.normalized_text) for page in eligible}
    adjacency: dict[Path, set[Path]] = defaultdict(set)
    by_path = {page.path: page for page in eligible}

    for left, right in combinations(eligible, 2):
        if left.language != right.language:
            continue
        left_set = fingerprints[left.path]
        right_set = fingerprints[right.path]
        union = left_set | right_set
        similarity = len(left_set & right_set) / len(union) if union else 0.0
        if similarity >= threshold:
            adjacency[left.path].add(right.path)
            adjacency[right.path].add(left.path)

    groups: list[list[TownPage]] = []
    seen: set[Path] = set()
    for start in sorted(adjacency, key=str):
        if start in seen:
            continue
        pending = [start]
        seen.add(start)
        component: list[Path] = []
        while pending:
            current = pending.pop()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    pending.append(neighbor)
        groups.append([by_path[path] for path in sorted(component, key=str)])
    return sorted(groups, key=lambda group: (-len(group), str(group[0].path)))


def unsupported_claim_issues(pages: list[TownPage]) -> list[str]:
    issues: list[str] = []
    for page in pages:
        if not page.indexable:
            continue
        matches = [label for label, pattern in UNSUPPORTED_CLAIMS if pattern.search(page.source)]
        if matches:
            issues.append(f"{page.path}: unsupported boilerplate ({', '.join(matches)})")
    return issues


def blocking_issues(pages: list[TownPage], *, strict: bool = False) -> list[str]:
    issues = unsupported_claim_issues(pages)
    if strict:
        minimum_words = REVIEW_MINIMUM_WORDS
        similarity = REVIEW_SIMILARITY
    else:
        minimum_words = BLOCKING_MINIMUM_WORDS
        similarity = BLOCKING_SIMILARITY
    groups = near_duplicate_groups(
        pages, threshold=similarity, minimum_words=minimum_words
    )
    for group in groups:
        members = ", ".join(str(page.path) for page in group)
        issues.append(
            f"near-exact indexable {group[0].language.upper()} template group "
            f"({len(group)} pages): {members}"
        )
    return issues


def numeric_metric(row: Mapping[str, str], key: str) -> float:
    value = (row.get(key) or "0").replace(",", "").strip()
    try:
        return float(value)
    except ValueError:
        return 0.0


def fold_gsc_page_rows(
    rows: Iterable[Mapping[str, str]], target_slugs: set[str]
) -> dict[str, dict[str, float | int]]:
    """Fold clean, ``.html``, and trailing-slash GSC rows by canonical path."""

    working: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {
            "rows": 0,
            "clicks": 0,
            "impressions": 0,
            "position_weight": 0.0,
        }
    )
    for row in rows:
        path = urlsplit(row.get("Top pages") or "").path.rstrip("/")
        if path.endswith(".html"):
            path = path[:-5]
        match = re.fullmatch(r"/(es/)?towns/([^/]+)", path)
        if not match or match.group(2) not in target_slugs:
            continue
        canonical = f"/{'es/' if match.group(1) else ''}towns/{match.group(2)}"
        clicks = int(numeric_metric(row, "Last 3 months Clicks"))
        impressions = int(numeric_metric(row, "Last 3 months Impressions"))
        position = numeric_metric(row, "Last 3 months Position")
        aggregate = working[canonical]
        aggregate["rows"] = int(aggregate["rows"]) + 1
        aggregate["clicks"] = int(aggregate["clicks"]) + clicks
        aggregate["impressions"] = int(aggregate["impressions"]) + impressions
        aggregate["position_weight"] = float(aggregate["position_weight"]) + (
            position * impressions
        )

    folded: dict[str, dict[str, float | int]] = {}
    for canonical, aggregate in sorted(working.items()):
        impressions = int(aggregate["impressions"])
        folded[canonical] = {
            "rows": int(aggregate["rows"]),
            "clicks": int(aggregate["clicks"]),
            "impressions": impressions,
            "position": (
                float(aggregate["position_weight"]) / impressions if impressions else 0.0
            ),
        }
    return folded


def relative_label(page: TownPage, root: Path) -> str:
    try:
        return str(page.path.relative_to(root))
    except ValueError:
        return str(page.path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Site repository root")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on shorter legacy near-exact groups as well as long-form groups",
    )
    parser.add_argument(
        "--show-review-groups",
        action="store_true",
        help="List shorter near-exact groups that remain review debt",
    )
    parser.add_argument("--max-groups", type=int, default=20)
    parser.add_argument(
        "--gsc-pages-csv",
        type=Path,
        help="Optional Search Console Pages.csv to fold URL variants for quarantine impact",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    pages = scan_town_pages(root)
    indexable = [page for page in pages if page.indexable]
    issues = blocking_issues(pages, strict=args.strict)
    review_groups = near_duplicate_groups(
        pages,
        threshold=REVIEW_SIMILARITY,
        minimum_words=REVIEW_MINIMUM_WORDS,
    )

    print(
        f"Town guides scanned: {len(pages)} "
        f"({len(indexable)} indexable, {len(pages) - len(indexable)} noindex/redirect)"
    )
    print(f"Unsupported indexable boilerplate: {len(unsupported_claim_issues(pages))}")
    print(f"Shorter near-exact groups for editorial review: {len(review_groups)}")

    if args.gsc_pages_csv:
        with args.gsc_pages_csv.open(encoding="utf-8-sig", newline="") as handle:
            gsc = fold_gsc_page_rows(csv.DictReader(handle), HIGH_RISK_SLUGS)
        clicks = sum(int(metrics["clicks"]) for metrics in gsc.values())
        impressions = sum(int(metrics["impressions"]) for metrics in gsc.values())
        rows = sum(int(metrics["rows"]) for metrics in gsc.values())
        print(
            f"GSC quarantine families: {len(gsc)} canonical URLs, {rows} variant rows, "
            f"{clicks} clicks, {impressions} impressions"
        )
        for canonical, metrics in sorted(
            gsc.items(), key=lambda item: (-int(item[1]["impressions"]), item[0])
        ):
            print(
                f"GSC {canonical}: {metrics['clicks']} clicks, "
                f"{metrics['impressions']} impressions, position {metrics['position']:.2f}"
            )

    if args.show_review_groups:
        for group in review_groups[: max(args.max_groups, 0)]:
            labels = ", ".join(relative_label(page, root) for page in group)
            print(f"REVIEW {group[0].language.upper()} ({len(group)}): {labels}")
        if len(review_groups) > args.max_groups:
            print(f"... {len(review_groups) - args.max_groups} additional review groups")

    if issues:
        print(f"FAIL: {len(issues)} blocking town-content issue(s)", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print("PASS: no blocking indexable town-content issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
