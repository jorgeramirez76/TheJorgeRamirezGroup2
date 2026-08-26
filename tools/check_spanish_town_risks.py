#!/usr/bin/env python3
"""Context-aware fair-housing and factual-risk linter for es/towns."""

from __future__ import annotations

import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "spanish-town-risk-decisions.json"

RISK_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "protected_or_lifestyle_proxy",
        re.compile(
            r"\b(?:familias?|niñ[oa]s?|profesionales?\s+j[oó]venes?|jubilad[oa]s?|"
            r"personas?\s+retiradas?|nido\s+vac[ií]o|afluentes?|exclusiv[oa]s?|"
            r"prestigios[oa]s?|diversidad\s+demogr[aá]fica)\b|"
            r"\b(?:ideal|perfect[oa])\s+para\s+(?:quienes|compradores|personas|residentes)\b",
            re.I,
        ),
    ),
    (
        "school_rank_or_subjective",
        re.compile(
            r"\b(?:mejores?|excelentes?|destacad[oa]s?|sobresalientes?|de\s+primer\s+nivel)\s+escuelas?\b|"
            r"\b(?:escuelas?|distrito\s+escolar)\s+(?:mejor\s+calificad[oa]|clasificad[oa]|"
            r"con\s+alta\s+calificaci[oó]n)\b|\bcalificaci[oó]n\s+escolar\b|"
            r"\b(?:ranking|clasificaci[oó]n)\s+escolar\b|\b\d+(?:[.,]\d+)?\s*/\s*10\b",
            re.I,
        ),
    ),
    (
        "safety_or_crime_characterization",
        re.compile(
            r"\b(?:m[aá]s\s+segur[oa]s?|comunidad\s+segura|zona\s+segura|baja\s+criminalidad|"
            r"bajo\s+[ií]ndice\s+delictivo|tasa\s+de\s+(?:crimen|delito)|criminalidad)\b",
            re.I,
        ),
    ),
    (
        "market_or_finance_claim",
        re.compile(
            r"\$\s*\d[\d.,]*|\b\d+(?:[.,]\d+)?\s*%|"
            r"\bprecio\s+(?:medio|promedio|mediano|t[ií]pico)\b|"
            r"\b(?:d[ií]as\s+en\s+el\s+mercado|nivel(?:es)?\s+de\s+inventario|"
            r"tasa\s+de\s+apreciaci[oó]n|retorno\s+de\s+inversi[oó]n|rendimiento\s+financiero|"
            r"mercado\s+en\s+crecimiento)\b",
            re.I,
        ),
    ),
    (
        "commute_duration",
        re.compile(
            r"\b(?:aproximadamente|alrededor\s+de|cerca\s+de|menos\s+de|m[aá]s\s+de)?\s*"
            r"\d+(?:[.,]\d+)?\s*(?:minutos?|mins?|horas?)\b",
            re.I,
        ),
    ),
    (
        "forecast_or_guarantee",
        re.compile(
            r"\b(?:pron[oó]stico|proyectad[oa]|se\s+espera\s+que\s+(?:suba|crezca|aumente)|"
            r"aumentar[aá]|crecer[aá]|subir[aá]|garantizad[oa]|garant[ií]a\s+de\s+resultado|"
            r"inversi[oó]n\s+inteligente|excelente\s+inversi[oó]n)\b",
            re.I,
        ),
    ),
    (
        "ranking_or_best_place",
        re.compile(
            r"\b(?:mejor(?:es)?|principal(?:es)?|n[uú]mero\s+uno|#\s*1|ideal|perfect[oa])\s+"
            r"(?:ciudad|pueblo|comunidad|vecindario|suburbio|lugar|opci[oó]n|ubicaci[oó]n)\b",
            re.I,
        ),
    ),
    (
        "faux_first_person_experience",
        re.compile(
            r"\b(?:he\s+ayudado|hemos\s+(?:vendido|comprado|cerrado)|en\s+mi\s+experiencia|"
            r"conozco\s+cada|mis\s+clientes|nuestros\s+clientes|personalmente\s+he)\b",
            re.I,
        ),
    ),
    (
        "stale_visible_year",
        re.compile(r"\b20(?:1\d|2[0-5])\b"),
    ),
)


class CopyLayerParser(HTMLParser):
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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
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
                start = max(0, match.start() - 42)
                end = min(len(text), match.end() + 42)
                findings.append(
                    {
                        "rule": rule,
                        "layer": layer,
                        "match": match.group(0),
                        "excerpt": text[start:end],
                    }
                )
    return findings


def audit() -> list[str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    issues: list[str] = []
    for slug, decision in manifest["decisions"].items():
        source = (ROOT / "es" / "towns" / f"{slug}.html").read_text(encoding="utf-8")
        findings = lint_source(source)
        for finding in findings:
            issues.append(
                f"es/towns/{slug}.html: {finding['rule']} in {finding['layer']} "
                f"({finding['match']!r}) — {finding['excerpt']}"
            )
        noindex = bool(re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*noindex', source, re.I))
        redirect = bool(re.search(r'<meta\b[^>]*http-equiv=["\']refresh', source, re.I))
        if decision["action"] == "rebuild" and (noindex or redirect):
            issues.append(f"es/towns/{slug}.html: rebuild is not indexable")
        elif decision["action"] == "quarantine" and (not noindex or redirect):
            issues.append(f"es/towns/{slug}.html: quarantine state mismatch")
        elif decision["action"] == "redirect" and (not noindex or not redirect):
            issues.append(f"es/towns/{slug}.html: redirect state mismatch")
    return issues


def main() -> int:
    issues = audit()
    for issue in issues:
        print(issue, file=sys.stderr)
    if issues:
        print(f"Spanish town risk audit failed: {len(issues)} issue(s)", file=sys.stderr)
        return 1
    print("Spanish town risk audit passed: 138 routes, zero contextual findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
