#!/usr/bin/env python3
"""Audit Spanish HTML pages for obvious mixed-language leftovers.

The audit reads DOM-visible copy, user-facing accessibility attributes, and
reviewed social/search metadata. It deliberately ignores code, CSS, URLs, and
official English organization names so proper nouns do not mask real UI leaks.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ES_DIR = ROOT / "es"

# High-signal fragments observed during live/source inspection.
PATTERNS: dict[str, str] = {
    "bad_homepage_counts": r"\b(?:10[0-9]|11[0-9]|12[0-9])\s+(?:Comunidades|Pueblos|comunidades|pueblos|Communities|Towns|communities|towns)\b",
    "broken_titles": r"\b(?:Your\s+Listado|First-Time\s+Comprador|Free\s+NJ|What\s+Is\s+Mi\s+Casa|Sell\s+Mi\s+Casa\s+Fast|Buyer\s+Costs|Why\s+Choose\s+Jorge|Two\s+Small\s+Ciudad|Commuterss)\b",
    "english_cta": r"\b(?:Get\s+Home\s+Value|Know\s+My\s+Number|Start\s+the\s+Conversation|Find\s+a\s+Home|List\s+With\s+Jorge|Learn\s+More|Get\s+Started)\b",
    "english_real_estate": r"\b(?:Looking\s+to|Expert\s+guidance|Expert\s+bienes|buyer\s+and\s+seller|buyer\s+representation|seller\s+representation|Licensed\s+Agente|top[- ]rated|full[- ]time|since\s+2017)\b",
    # "Property Tax Statistics" is an official source title and is allowed.
    "english_metrics": r"\b(?:Median\s+price|Average\s+price|Days\s+on\s+Market|Closing\s+Costs|Down\s+Payment)\b",
    "english_context_words": r"\b(?:neighborhood\s+names|commute\s+(?:promise|time)|market\s+data|home\s+value|home\s+buyer|home\s+seller|homes\s+for\s+sale|official[- ]source\s+research\s+guide|it\s+distinguishes\s+(?:county|municipality|property)|no\s+copied\s+market\s+tables|forward[- ]looking\s+claims|reviewed\s+municipality\s+research|published\s+values\s+are|town\s+listing\s+data|property\s+valuation)\b",
    "english_source_ui": r"\b(?:Buyer\s+and\s+seller\s+research\s+sequences|Open\s+the\s+primary\s+source|Official\s+municipal\s+website|Official\s+district\s+website)\b",
    "english_source_kinds": r"\b(?:federal\s+geographic\s+profile|primary\s+municipal\s+source|official\s+station\s+page|state\s+fair\s+housing\s+guidance|state\s+civil\s+rights\s+guidance|state\s+property-tax\s+data\s+library|state\s+education\s+data\s+portal|official\s+transit\s+planning\s+tool|public-school\s+district\s+primary\s+source)\b",
    "english_source_sentences": r"\b(?:Select\s+a\s+county|County\s+reports\s+do\s+not\s+establish|Review\s+the\s+state(?:'s|’s)|Averages,\s+assessments,\s+and\s+equalization\s+data|Search\s+current\s+state-published|Confirm\s+the\s+district\s+and\s+attendance\s+assignment|Confirm\s+whether\s+a\s+place\s+name|Check\s+the\s+current\s+route|Travel\s+time\s+varies|Postal\s+and\s+neighborhood\s+names|does\s+not\s+(?:establish|describe|promise|rank|predict))\b",
    "mojibake": r"(?:Ã|Â|â€™|â€œ|â€|�)",
}

IGNORED_ELEMENTS = {"script", "style", "template", "noscript", "svg"}
USER_FACING_ATTRIBUTES = {"alt", "aria-label", "placeholder", "title"}
META_FIELDS = {
    "description",
    "llm-context",
    "og:title",
    "og:description",
    "twitter:title",
    "twitter:description",
}


class SpanishCopyExtractor(HTMLParser):
    """Collect prose a visitor, assistive technology, or search preview sees."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        attributes = {name.casefold(): value or "" for name, value in attrs}
        if tag in IGNORED_ELEMENTS:
            self.ignored_depth += 1
            return
        if self.ignored_depth:
            return
        if tag == "meta":
            field = (attributes.get("name") or attributes.get("property") or "").casefold()
            if field in META_FIELDS:
                self._append(attributes.get("content", ""))
        for name in USER_FACING_ATTRIBUTES:
            self._append(attributes.get(name, ""))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.casefold() in IGNORED_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in IGNORED_ELEMENTS and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self._append(data)

    def _append(self, value: str) -> None:
        cleaned = " ".join(html.unescape(value).split())
        if cleaned:
            self.parts.append(cleaned)


def visibleish_text(raw: str) -> str:
    parser = SpanishCopyExtractor()
    parser.feed(raw)
    parser.close()
    return "\n".join(parser.parts)


def audit_file(path: Path) -> dict[str, object]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = visibleish_text(raw)
    categories: dict[str, int] = {}
    examples: dict[str, list[str]] = {}
    for name, pattern in PATTERNS.items():
        rx = re.compile(pattern, re.I)
        matches = list(rx.finditer(text))
        if matches:
            categories[name] = len(matches)
            vals: list[str] = []
            for m in matches[:5]:
                snippet = re.sub(r"\s+", " ", text[max(0, m.start() - 80): m.end() + 120]).strip()
                vals.append(snippet)
            examples[name] = vals
    return {
        "path": str(path.relative_to(ROOT)),
        "score": sum(categories.values()),
        "categories": categories,
        "examples": examples,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw_results = [audit_file(p) for p in sorted(ES_DIR.rglob("*.html"))]
    results = [r for r in raw_results if isinstance(r["score"], int) and r["score"] > 0]
    results.sort(key=lambda r: (-int(r["score"]), str(r["path"])))

    summary: dict[str, int] = {k: 0 for k in PATTERNS}
    for r in results:
        categories = r["categories"]
        if not isinstance(categories, dict):
            continue
        for k, n in categories.items():
            summary[str(k)] += int(n)

    payload = {"files_with_findings": len(results), "summary": summary, "top": results[: args.limit]}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Spanish files with findings: {payload['files_with_findings']}")
        print("Summary:")
        for k, v in summary.items():
            print(f"  {k:<24} {v}")
        print("\nTop files:")
        for r in results[: args.limit]:
            cats = ", ".join(f"{k}={v}" for k, v in dict(r["categories"]).items())
            print(f"  {int(r['score']):>4}  {r['path']}  {cats}")
    return 1 if results else 0


if __name__ == "__main__":
    raise SystemExit(main())
