#!/usr/bin/env python3
"""Audit Spanish HTML pages for obvious mixed-language leftovers.

This is intentionally conservative: it flags known broken machine-translation
fragments and high-signal English real-estate terms, but allows proper nouns
such as NJ, NYC, Zillow, Keller Williams, and Jorge Ramirez.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ES_DIR = ROOT / "es"

# High-signal fragments observed during live/source inspection.
PATTERNS: dict[str, str] = {
    "bad_homepage_counts": r"\b(?:103\s+Comunidades|120\s+Pueblos|109\s+Pueblos)\b",
    "broken_titles": r"\b(?:Your\s+Listado|First-Time\s+Comprador|Free\s+NJ|What\s+Is\s+Mi\s+Casa|Sell\s+Mi\s+Casa\s+Fast|Buyer\s+Costs|Why\s+Choose\s+Jorge|Two\s+Small\s+Ciudad|Commuterss)\b",
    "english_cta": r"\b(?:Get\s+Home\s+Value|Know\s+My\s+Number|Start\s+the\s+Conversation|Find\s+a\s+Home|List\s+With\s+Jorge|Learn\s+More|Get\s+Started)\b",
    "english_real_estate": r"\b(?:Looking\s+to|Expert\s+guidance|Expert\s+bienes|buyer\s+and\s+seller|buyer\s+representation|seller\s+representation|Licensed\s+Agente|top[- ]rated|full[- ]time|since\s+2017)\b",
    "english_metrics": r"\b(?:Median\s+price|Average\s+price|Days\s+on\s+Market|Property\s+Tax|Closing\s+Costs|Down\s+Payment)\b",
    "english_context_words": r"\b(?:neighborhood|schools|commute|market\s+data|home\s+value|home\s+buyer|home\s+seller|homes\s+for\s+sale)\b",
    "mojibake": r"(?:Ã|Â|â€™|â€œ|â€|�)",
}

# Lines dominated by paths/URLs/scripts are noisy. Meta/title/schema text still matters.
SKIP_LINE = re.compile(r"(<script\b|</script>|href=|src=|canonical|@id|\"url\"|https?://)", re.I)
KEEP_EVEN_IF_SKIP = re.compile(r"(<title\b|<meta\b|\"description\"|\"jobTitle\"|\"knowsAbout\")", re.I)


def visibleish_text(raw: str) -> str:
    lines: list[str] = []
    for line in raw.splitlines():
        if SKIP_LINE.search(line) and not KEEP_EVEN_IF_SKIP.search(line):
            continue
        lines.append(line)
    return "\n".join(lines)


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
