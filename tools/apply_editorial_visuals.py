#!/usr/bin/env python3
"""Add responsive, contextual editorial images to the densest indexable pages.

The mapping is intentionally explicit. It keeps imagery relevant, bilingual,
idempotent, and reviewable instead of decorating every template indiscriminately.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE_MODIFIED_ON = "2026-08-27"
START = "<!-- JRG editorial visual:start -->"
END = "<!-- JRG editorial visual:end -->"

ASSETS = {
    "buyer": ("/images/editorial/nj-first-time-buyer-planning-2026", 854),
    "tax": ("/images/editorial/nj-property-tax-research-2026", 854),
    "valuation": ("/images/editorial/nj-home-valuation-review-2026", 854),
    "comparison": ("/images/editorial/nj-housing-comparison-2026", 854),
    "rental": ("/images/editorial/nj-rental-property-transition-2026", 854),
    "offer": ("/images/editorial/nj-written-offer-comparison-2026", 854),
    "fsbo": ("/images/nj-fsbo-selling-plan-2026", 853),
    "relocation": ("/images/nyc-to-nj-relocation-plan-2026", 853),
}

ALT = {
    "buyer": {
        "en": "Blank home-buying planning sheet, document folders, calculator, house model, keys, and measuring tape arranged on a warm wood table",
        "es": "Hoja en blanco para planificar la compra de vivienda, carpetas, calculadora, modelo de casa, llaves y cinta de medir sobre una mesa de madera",
    },
    "tax": {
        "en": "House model, parcel research sheet, calculator, magnifying glass, key, and document folder arranged for a New Jersey property-tax review",
        "es": "Modelo de casa, plano de parcela, calculadora, lupa, llave y carpeta preparados para revisar impuestos de propiedad en New Jersey",
    },
    "valuation": {
        "en": "House model, blank valuation notes, measuring tape, calculator, keys, and room photos arranged for a property review",
        "es": "Modelo de casa, notas de valoración, cinta de medir, calculadora, llaves y fotos de habitaciones preparados para revisar una propiedad",
    },
    "comparison": {
        "en": "Two equal house models, key sets, route sheet, and blank comparison notebook arranged for a neutral housing decision",
        "es": "Dos modelos de casa iguales, juegos de llaves, hoja de rutas y cuaderno de comparación preparados para una decisión neutral de vivienda",
    },
    "rental": {
        "en": "Rental-property transition checklist, document folder, keys, calendar, measuring tape, and tool pouch on a wood table",
        "es": "Lista de transición de una propiedad de alquiler, carpeta, llaves, calendario, cinta de medir y bolsa de herramientas sobre una mesa",
    },
    "offer": {
        "en": "Two equal document folders, blank offer sheets, house model, key, calculator, and calendar arranged for a side-by-side review",
        "es": "Dos carpetas iguales, hojas de oferta en blanco, modelo de casa, llave, calculadora y calendario preparados para comparar opciones",
    },
    "fsbo": {
        "en": "Home-selling checklist, measuring tape, phone, keys, and blank sign arranged on a table near the front door",
        "es": "Lista para vender una casa, cinta de medir, teléfono, llaves y letrero en blanco sobre una mesa cerca de la entrada",
    },
    "relocation": {
        "en": "Moving boxes and keys inside an open front door with a moving truck waiting outside",
        "es": "Cajas de mudanza y llaves dentro de una entrada abierta con un camión de mudanza afuera",
    },
}

PAGE_VISUALS = {
    "blog/first-time-home-buyer-nj-guide.html": "buyer",
    "es/blog/first-time-home-buyer-nj-guide.html": "buyer",
    "home-valuation.html": "valuation",
    "es/home-valuation.html": "valuation",
    "blog/best-nj-suburbs-nyc-commuters.html": "comparison",
    "es/blog/best-nj-suburbs-nyc-commuters.html": "comparison",
    "blog/best-nj-towns-for-families-2026.html": "comparison",
    "es/blog/best-nj-towns-for-families.html": "comparison",
    "blog/nj-property-tax-guide.html": "tax",
    "es/blog/nj-property-tax-guide.html": "tax",
    "sell-rental-property-nj.html": "rental",
    "es/sell-rental-property-nj.html": "rental",
    "towns/south-brunswick.html": "comparison",
    "towns/east-brunswick.html": "comparison",
    "towns/bloomfield.html": "comparison",
    "towns/guttenberg.html": "comparison",
    "towns/west-new-york.html": "comparison",
    "blog/listing-agent-vs-selling-agent-nj.html": "offer",
    "sell-your-home.html": "valuation",
    "es/sell-your-home.html": "valuation",
    "divorce-home-sale-nj.html": "offer",
    "es/divorce-home-sale-nj.html": "offer",
    "blog/maplewood-vs-south-orange-nj.html": "comparison",
    "es/blog/maplewood-vs-south-orange-nj.html": "comparison",
    "blog/summit-vs-westfield-nj.html": "comparison",
    "es/blog/summit-vs-westfield-nj.html": "comparison",
    "how-we-sell-your-home.html": "valuation",
    "es/how-we-sell-your-home.html": "valuation",
    "cash-offer-nj.html": "offer",
    "es/cash-offer-nj.html": "offer",
    "expired-listing-help.html": "fsbo",
    "es/expired-listing-help.html": "fsbo",
    "fsbo-help.html": "fsbo",
    "es/fsbo-help.html": "fsbo",
    "blog/midtown-direct-towns-nj.html": "comparison",
    "es/blog/midtown-direct-towns-nj.html": "comparison",
    "relocating-from-nj.html": "relocation",
    "es/relocating-from-nj.html": "relocation",
}


def visual_markup(kind: str, language: str) -> str:
    base, height = ASSETS[kind]
    alt = html.escape(ALT[kind][language], quote=True)
    return f'''\n    {START}
    <figure class="jrg-editorial-figure" data-editorial-visual="{kind}">
      <picture>
        <source srcset="{base}-768.webp 768w, {base}-1280.webp 1280w" sizes="(max-width: 900px) calc(100vw - 32px), 960px" type="image/webp">
        <img src="{base}-1280.webp" width="1280" height="{height}" loading="lazy" decoding="async" alt="{alt}">
      </picture>
    </figure>
    {END}\n'''


def insert_after_opening_landmark(source: str, block: str, relative: str) -> str:
    main = re.search(r"<main\b[^>]*>", source, re.I)
    if main is None:
        raise ValueError(f"{relative}: missing main landmark")
    main_end = source.lower().find("</main>", main.end())
    if main_end == -1:
        raise ValueError(f"{relative}: missing closing main landmark")
    scope = source[main.end():main_end]

    candidates = []
    for tag in ("header", "section"):
        opening = re.search(rf"<{tag}\b", scope, re.I)
        if opening is None:
            continue
        closing = re.search(rf"</{tag}>", scope[opening.end():], re.I)
        if closing is not None:
            candidates.append((opening.start(), opening.end() + closing.end(), tag))
    if candidates:
        _, relative_end, _ = min(candidates)
        insertion = main.end() + relative_end
        return source[:insertion] + block + source[insertion:]

    h1 = re.search(r"<h1\b[^>]*>.*?</h1>", scope, re.I | re.S)
    if h1 is None:
        raise ValueError(f"{relative}: missing opening header/section and h1 fallback")
    paragraph = re.search(r"</p>", scope[h1.end():], re.I)
    relative_end = h1.end() + (paragraph.end() if paragraph else 0)
    insertion = main.end() + relative_end
    return source[:insertion] + block + source[insertion:]


def align_page_modified_signals(source: str, relative: str) -> str:
    """Align page-change signals without changing source-review evidence dates."""

    updated, schema_count = re.subn(
        r'(?P<prefix>"dateModified"\s*:\s*")\d{4}-\d{2}-\d{2}(?P<suffix>")',
        rf"\g<prefix>{PAGE_MODIFIED_ON}\g<suffix>",
        source,
    )
    if schema_count < 1:
        raise ValueError(f"{relative}: missing schema dateModified")
    updated = re.sub(
        r'(?P<prefix><meta\s+property="article:modified_time"\s+content=")'
        r'\d{4}-\d{2}-\d{2}(?P<suffix>")',
        rf"\g<prefix>{PAGE_MODIFIED_ON}\g<suffix>",
        updated,
        flags=re.I,
    )
    updated = re.sub(
        r'(?P<prefix><meta\s+name="last-updated"\s+content=")'
        r'\d{4}-\d{2}-\d{2}(?P<suffix>")',
        rf"\g<prefix>{PAGE_MODIFIED_ON}\g<suffix>",
        updated,
        flags=re.I,
    )
    return updated


def apply_visual(relative: str, kind: str) -> bool:
    path = ROOT / relative
    source = path.read_text(encoding="utf-8")
    updated = align_page_modified_signals(source, relative)
    language = "es" if relative.startswith("es/") else "en"
    block = visual_markup(kind, language)
    existing = re.search(
        rf"{re.escape(START)}.*?{re.escape(END)}",
        updated,
        flags=re.S,
    )
    if existing is not None:
        if existing.group(0).strip() != block.strip():
            updated = updated[: existing.start()] + block.strip() + updated[existing.end() :]
    else:
        updated = insert_after_opening_landmark(updated, block, relative)
    if updated == source:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    changed = 0
    for relative, kind in PAGE_VISUALS.items():
        changed += apply_visual(relative, kind)
    print(f"editorial visuals applied: pages={len(PAGE_VISUALS)} changed={changed}")


if __name__ == "__main__":
    main()
