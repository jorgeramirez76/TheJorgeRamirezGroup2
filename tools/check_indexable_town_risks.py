#!/usr/bin/env python3
"""Layer-aware fair-housing and factual-risk check for managed town routes.

The checker intentionally separates visible copy, search metadata, and parsed
JSON-LD string values. CSS and executable JavaScript are not treated as copy.
The managed route inventory and decisions live in a versioned manifest so the
gate cannot silently expand to source-backed guides with different contracts.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "indexable-town-risk-decisions.json"

RISK_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "protected_or_proxy_targeting",
        re.compile(
            r"\b(?:famil(?:y|ies)|family[- ]friendly|children|kids?|"
            r"young professionals?|retirees?|empty nesters?|affluent|exclusive|"
            r"prestigious|diverse community|demographics?)\b|"
            r"\b(?:ideal|perfect|great)\s+for\s+(?:people|buyers|residents|those|anyone)\b",
            re.I,
        ),
    ),
    (
        "school_rank_or_subjective",
        re.compile(
            r"\b(?:top(?:[- ]rated)?|highly[- ]rated|award[- ]winning|best|excellent|"
            r"outstanding|strong)\s+(?:public\s+)?schools?\b|"
            r"\bschool(?:s| district)?\s+(?:rank(?:ed|ing|ings)?|rating|score)\b|"
            r"\b\d+(?:\.\d+)?\s*/\s*10\b",
            re.I,
        ),
    ),
    (
        "safety_or_crime",
        re.compile(
            r"\b(?:safest|safe\s+(?:town|community|neighbou?rhood)|"
            r"low[- ]crime|crime rate|secure community)\b",
            re.I,
        ),
    ),
    (
        "market_or_finance_claim",
        re.compile(
            r"\$\s*\d[\d,.]*|\b\d+(?:\.\d+)?\s*%|"
            r"\b(?:median|average)\s+(?:home|sale|list|listing)\s+price\b|"
            r"\b(?:inventory levels?|days on market|appreciation rate|"
            r"return on investment|reliable returns?|market forecast)\b",
            re.I,
        ),
    ),
    (
        "commute_duration",
        re.compile(
            r"\b(?:about|approximately|around|roughly|under|over|within)?\s*"
            r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)"
            r"\s*(?:minutes?|mins?|hours?)\b",
            re.I,
        ),
    ),
    (
        "forecast_or_guarantee",
        re.compile(
            r"\b(?:forecast|projected|expected to (?:rise|grow|increase)|"
            r"will (?:rise|grow|increase)|guarantee(?:d|s)?|"
            r"excellent investment|smart investment)\b",
            re.I,
        ),
    ),
    (
        "ranking_or_best_claim",
        re.compile(
            r"\b(?:best|top|ranked|ranking|number one|#\s*1|ideal|perfect)\s+"
            r"(?:town|place|community|neighbou?rhood|suburb|choice|location)\b",
            re.I,
        ),
    ),
)


class CopyLayerParser(HTMLParser):
    """Extract user/search-facing strings without regex-parsing HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._hidden_depth = 0
        self._head_depth = 0
        self._title_depth = 0
        self._json_depth = 0
        self._json_buffer: list[str] = []
        self.visible: list[str] = []
        self.metadata: list[str] = []
        self.json_blocks: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.casefold()
        values = {key.casefold(): value or "" for key, value in attrs}
        if tag == "head":
            self._head_depth += 1
        elif tag == "title":
            self._title_depth += 1
        elif tag == "script":
            if values.get("type", "").casefold() == "application/ld+json":
                self._json_depth += 1
            else:
                self._hidden_depth += 1
        elif tag in {"style", "template", "noscript"}:
            self._hidden_depth += 1
        if tag == "meta" and values.get("content"):
            self.metadata.append(values["content"])
        for attribute in ("alt", "aria-label", "title"):
            if values.get(attribute):
                self.visible.append(values[attribute])

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag == "head" and self._head_depth:
            self._head_depth -= 1
        elif tag == "title" and self._title_depth:
            self._title_depth -= 1
        elif tag == "script":
            if self._json_depth:
                self.json_blocks.append("".join(self._json_buffer))
                self._json_buffer.clear()
                self._json_depth -= 1
            elif self._hidden_depth:
                self._hidden_depth -= 1
        elif tag in {"style", "template", "noscript"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._json_depth:
            self._json_buffer.append(data)
        elif self._title_depth:
            self.metadata.append(data)
        elif not self._hidden_depth and not self._head_depth:
            self.visible.append(data)


def _json_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _json_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _json_strings(child)


def copy_layers(source: str) -> dict[str, str]:
    parser = CopyLayerParser()
    parser.feed(source)
    structured: list[str] = []
    for block in parser.json_blocks:
        try:
            structured.extend(_json_strings(json.loads(html.unescape(block))))
        except json.JSONDecodeError:
            structured.append(block)
    return {
        "visible": " ".join(" ".join(parser.visible).split()),
        "metadata": " ".join(" ".join(parser.metadata).split()),
        "jsonld": " ".join(" ".join(structured).split()),
    }


def lint_source(source: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for layer, text in copy_layers(source).items():
        for rule, pattern in RISK_RULES:
            for match in pattern.finditer(text):
                start = max(0, match.start() - 36)
                end = min(len(text), match.end() + 36)
                findings.append(
                    {
                        "rule": rule,
                        "layer": layer,
                        "match": match.group(0),
                        "excerpt": text[start:end],
                    }
                )
    return findings


def _number(row: Mapping[str, str], column: str) -> float:
    value = (row.get(column) or "0").replace(",", "").replace("%", "").strip()
    try:
        return float(value)
    except ValueError:
        return 0.0


def _canonical_town_path(value: str, target_slugs: set[str]) -> str | None:
    path = urlsplit(value).path.rstrip("/")
    if path.endswith(".html"):
        path = path[:-5]
    match = re.fullmatch(r"/towns/([^/]+)", path)
    if not match or match.group(1) not in target_slugs:
        return None
    return f"/towns/{match.group(1)}"


def fold_gsc_rows(
    rows: Iterable[Mapping[str, str]],
    target_slugs: set[str],
    periods: Mapping[str, Mapping[str, str]],
) -> dict[str, dict[str, dict[str, float | int]]]:
    """Fold clean, HTML, and slash URL variants for each declared period."""

    working: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "rows": 0.0,
                "clicks": 0.0,
                "impressions": 0.0,
                "positionWeight": 0.0,
            }
        )
    )
    for row in rows:
        canonical = _canonical_town_path(row.get("Top pages") or "", target_slugs)
        if not canonical:
            continue
        for period, columns in periods.items():
            metric = working[canonical][period]
            impressions = _number(row, columns["impressions"])
            metric["rows"] += 1
            metric["clicks"] += _number(row, columns["clicks"])
            metric["impressions"] += impressions
            metric["positionWeight"] += _number(row, columns["position"]) * impressions

    folded: dict[str, dict[str, dict[str, float | int]]] = {}
    for slug in sorted(target_slugs):
        canonical = f"/towns/{slug}"
        folded[canonical] = {}
        for period in periods:
            metric = working[canonical][period]
            impressions = int(metric["impressions"])
            folded[canonical][period] = {
                "rows": int(metric["rows"]),
                "clicks": int(metric["clicks"]),
                "impressions": impressions,
                "position": round(
                    metric["positionWeight"] / impressions if impressions else 0.0,
                    2,
                ),
            }
    return folded


def managed_issues(root: Path = ROOT, manifest_path: Path = MANIFEST) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    for slug, decision in manifest["decisions"].items():
        source = (root / "towns" / f"{slug}.html").read_text(
            encoding="utf-8", errors="replace"
        )
        is_noindex = bool(
            re.search(
                r'<meta\b[^>]*name=["\']robots["\'][^>]*\bnoindex\b',
                source,
                re.I,
            )
        )
        is_redirect = bool(
            re.search(r'<meta\b[^>]*http-equiv=["\']refresh["\']', source, re.I)
        )
        action = decision["action"]
        if action == "rebuild":
            if is_noindex or is_redirect:
                issues.append(f"towns/{slug}.html: rebuild is not indexable")
                continue
            for finding in lint_source(source):
                issues.append(
                    f"towns/{slug}.html: {finding['rule']} in {finding['layer']} "
                    f"({finding['match']!r})"
                )
        elif action == "quarantine" and not is_noindex:
            issues.append(f"towns/{slug}.html: quarantine is indexable")
        elif action == "redirect" and not is_redirect:
            issues.append(f"towns/{slug}.html: redirect fallback is missing")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    issues = managed_issues(args.root.resolve(), args.manifest.resolve())
    if issues:
        print(f"FAIL: {len(issues)} managed town risk issue(s)", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("PASS: managed indexable town pages contain no blocked risk patterns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
