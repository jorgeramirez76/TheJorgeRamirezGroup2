#!/usr/bin/env python3
"""Conservative Spanish copy cleanup for known machine-translation leftovers.

Rules:
- Only edits files under /es.
- Skips URL-heavy lines unless they are title/meta/schema text values.
- Does not regenerate pages, so it preserves Claude Code's current town-page work.
- Idempotent: safe to run repeatedly.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ES_DIR = ROOT / "es"

LINE_SKIP = re.compile(r"(href=|src=|canonical|https?://|@id|\"url\"|<script\b|</script>)", re.I)
LINE_KEEP = re.compile(r"(<title\b|<meta\b|\"description\"|\"jobTitle\"|\"knowsAbout\")", re.I)
TAG_RE = re.compile(r"(<[^>]+>)")
CONTENT_ATTR_RE = re.compile(r'\b(content|title|alt)=("[^"]*"|\'[^\']*\')', re.I)

REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    # Homepage / communities consistency
    (re.compile(r"\b103\s+Comunidades\b"), "138 Comunidades"),
    (re.compile(r"\b120\s+Pueblos\b"), "138 Pueblos"),
    (re.compile(r"\b109\s+Pueblos\b"), "138 Pueblos"),

    # Broken top-level title/meta fragments observed in inspection
    (re.compile(r"\bYour Listado Expired\? Here's What Went Wrong — and How to Fix It\b"), "¿Tu Listado Venció? Qué Salió Mal y Cómo Solucionarlo"),
    (re.compile(r"\bFirst-Time Comprador de Casa Programs in NJ 2026\b"), "Programas para Compradores Primerizos en NJ 2026"),
    (re.compile(r"\bFree NJ Valoración de Casa \| What Is Mi Casa Worth\?\b"), "Valoración de Casa Gratis en NJ | ¿Cuánto Vale Mi Casa?"),
    (re.compile(r"\bSell Mi Casa Fast en NJ\b"), "Vender Mi Casa Rápido en NJ"),
    (re.compile(r"\bWhy Choose Jorge Ramirez \| Best Realtor en NJ\b"), "Por Qué Elegir a Jorge Ramirez | Realtor en NJ"),
    (re.compile(r"\bWhy Choose Jorge\b"), "Por Qué Elegir a Jorge"),
    (re.compile(r"\bTwo Small Ciudad para Commuterss, Compared\b"), "Dos Pueblos Pequeños para Viajeros, Comparados"),
    (re.compile(r"\bPrecio, Commute y Escuelas\b"), "Precio, Viaje y Escuelas"),
    (re.compile(r"\bNJ Costos de Cierre Calculator 2026 \| Buyer Costs\b"), "Calculadora de Costos de Cierre en NJ 2026 | Costos del Comprador"),
    (re.compile(r"\bNJ Ganancia Neta del Vendedor Calculator 2026\b"), "Calculadora de Ganancia Neta del Vendedor en NJ 2026"),
    (re.compile(r"\bImpuesto de Transferencia NJ Calculator 2026\b"), "Calculadora del Impuesto de Transferencia en NJ 2026"),
    (re.compile(r"\bNJ Calculadora Rentar vs Comprar 2026\b"), "Calculadora de Rentar vs Comprar en NJ 2026"),
    (re.compile(r"\bComprar una Casa en NJ \| Jorge Ramirez Agente del Comprador\b"), "Comprar una Casa en NJ | Jorge Ramirez, Agente del Comprador"),
    (re.compile(r"\bBest NJ Agente Inmobiliario \| Jorge Ramirez Reseñas\b"), "Agente Inmobiliario en NJ | Reseñas de Jorge Ramirez"),

    # SAFE multi-word phrases only — self-disambiguating.
    # Do NOT add single-word English->Spanish replacements: they corrupt
    # proper nouns (e.g. "Westfield Public Schools" -> "Westfield Public escuelas")
    # and inject Spanglish into paragraphs that are still mostly English.
    (re.compile(r"\bLooking to buy or sell a home in\b", re.I), "¿Buscas comprar o vender una casa en"),
    (re.compile(r"\bExpert bienes raíces guidance\b", re.I), "Orientación experta en bienes raíces"),
    (re.compile(r"\bExpert real estate guidance\b", re.I), "Orientación experta en bienes raíces"),
    (re.compile(r"\bLicensed Agente Inmobiliario\b"), "Agente Inmobiliario con Licencia"),
    (re.compile(r"\bbuyer and seller representation\b", re.I), "representación de compradores y vendedores"),
    (re.compile(r"\bbuyer representation\b", re.I), "representación de compradores"),
    (re.compile(r"\bseller representation\b", re.I), "representación de vendedores"),
    (re.compile(r"\bhomes for sale\b", re.I), "casas en venta"),
    (re.compile(r"\bmarket data\b", re.I), "datos del mercado"),
    (re.compile(r"\bMedian price\b"), "Precio medio"),
    (re.compile(r"\bAverage price\b"), "Precio promedio"),
    (re.compile(r"\bDays on Market\b"), "Días en el Mercado"),
    (re.compile(r"\bProperty Tax\b"), "Impuesto a la Propiedad"),
    (re.compile(r"\bClosing Costs\b"), "Costos de Cierre"),
    (re.compile(r"\bDown Payment\b"), "Pago Inicial"),
]


def should_edit_line(line: str) -> bool:
    if LINE_SKIP.search(line) and not LINE_KEEP.search(line):
        return False
    return True


def apply_replacements(text: str) -> str:
    for pattern, repl in REPLACEMENTS:
        text = pattern.sub(repl, text)
    return text


URL_VALUE = re.compile(r"^\s*(?:https?://|/|#|mailto:|tel:)", re.I)


def fix_tag(tag: str) -> str:
    """Only edit human-readable content/title/alt attributes inside a tag.

    Skips values that are URLs (og:url, twitter:url, canonical-ish content=)
    to avoid corrupting URL slugs (e.g. "real-estate-market-2025" -> "...-mercado-2025").
    """
    def repl(match: re.Match[str]) -> str:
        name, quoted = match.group(1), match.group(2)
        quote = quoted[0]
        value = quoted[1:-1]
        if URL_VALUE.match(value):
            return match.group(0)
        return f"{name}={quote}{apply_replacements(value)}{quote}"

    # Never edit structural attributes like class/id/href/src.
    return CONTENT_ATTR_RE.sub(repl, tag)


def fix_line(line: str, in_jsonld: bool) -> str:
    """Edit safe metadata attrs and JSON-LD strings, preserving HTML structure.

    Body prose text nodes are LEFT ALONE — token surgery on English-heavy
    paragraphs produces worse Spanglish than the source (e.g. injecting
    "viaje al trabajo" into an otherwise-English sentence). Body copy must
    be translated per-file with LLM context.
    """
    parts = TAG_RE.split(line)
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<") and part.endswith(">"):
            parts[i] = fix_tag(part)
        elif in_jsonld:
            parts[i] = apply_replacements(part)
        # else: body text node — skip
    return "".join(parts)


JSONLD_OPEN = re.compile(r'<script[^>]*type=(["\'])application/ld\+json\1', re.I)
JSONLD_CLOSE = re.compile(r"</script>", re.I)


def fix_text(text: str) -> str:
    out_lines: list[str] = []
    in_jsonld = False
    for line in text.splitlines():
        opened_this_line = bool(JSONLD_OPEN.search(line))
        if opened_this_line:
            in_jsonld = True
        if should_edit_line(line):
            line = fix_line(line, in_jsonld)
        if in_jsonld and JSONLD_CLOSE.search(line):
            in_jsonld = False
        out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    changed: list[str] = []
    for path in sorted(ES_DIR.rglob("*.html")):
        original = path.read_text(encoding="utf-8", errors="ignore")
        fixed = fix_text(original)
        if fixed != original:
            path.write_text(fixed, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))
    print(f"changed_files={len(changed)}")
    for rel in changed[:200]:
        print(rel)
    if len(changed) > 200:
        print(f"... {len(changed) - 200} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
