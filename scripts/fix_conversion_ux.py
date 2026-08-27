#!/usr/bin/env python3
"""Apply the safe, mechanical portions of the conversion UX remediation.

This script is intentionally narrow and idempotent:

* point legacy valuation-host links at the first-party intake;
* replace old-host mentions in metadata and prose with the canonical first-party URL;
* promote generated town-page hero targets into real ``main`` landmarks.

Use ``--check`` in CI to fail when a future generated page reintroduces either issue.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD_HOST = "value.thejorgeramirezgroup.com"
OLD_ABSOLUTE = f"https://{OLD_HOST}"
NEW_PATH = "/home-valuation"
NEW_ABSOLUTE = "https://thejorgeramirezgroup.com/home-valuation"
NEW_VISIBLE = "thejorgeramirezgroup.com/home-valuation"

LEGACY_LINK = re.compile(
    rf"(<a\b[^>]*\bhref\s*=\s*['\"]){re.escape(OLD_ABSOLUTE)}(['\"])",
    re.IGNORECASE,
)
FIRST_PARTY_LINK = re.compile(
    r"(<a\b[^>]*\bhref\s*=\s*['\"])"
    + re.escape(NEW_ABSOLUTE)
    + r"(['\"])",
    re.IGNORECASE,
)
TOWN_HERO = '<section id="main" class="hero">'
TOWN_FOOTER = re.compile(r"^(\s*)<footer class=\"footer\">", re.MULTILINE)
ANCHOR_TAG = re.compile(r"<a\b[^>]*>", re.IGNORECASE)
VALUATION_ANCHOR = re.compile(
    r"(<a\b(?=[^>]*\bhref\s*=\s*['\"]/home-valuation['\"])[^>]*>)"
    r"(.*?)(</a>)",
    re.IGNORECASE | re.DOTALL,
)
INTERNAL_VALUATION_HREF = re.compile(
    r"\bhref\s*=\s*['\"]/home-valuation['\"]",
    re.IGNORECASE,
)
NEW_TAB_ATTRIBUTE = re.compile(r"\s+target\s*=\s*['\"]_blank['\"]", re.IGNORECASE)

VALUATION_PROMISE_REPLACEMENTS = (
    (
        "Start with the instant online estimate, or skip straight to a free in-person CMA — the number you can actually plan around.",
        "Request a free CMA — a reasoned range with its assumptions and limits.",
    ),
    (
        "Start with the instant online estimate, or go straight to a free in-person valuation — the number you can actually plan around.",
        "Request a free valuation — a reasoned range with its assumptions and limits.",
    ),
    ("Free instant estimate + expert CMA", "Free expert CMA"),
    ("Instant estimates at", "Free CMA requests at"),
    ("Get My Instant Estimate", "Request My Free Valuation"),
    ("Get Your Instant Estimate", "Request Your Free Valuation"),
    ("Instant Online Estimate", "Request a Free Valuation"),
    ("get an instant estimate on your", "request a free CMA for your"),
    ("for an instant estimate", "to request a free CMA"),
    ("instant automated estimate", "automated estimate"),
    ("instant online estimate", "free CMA request"),
    ("instant estimates", "automated estimates"),
    ("instant estimate", "automated estimate"),
    (
        "Use the automated estimate as a starting point, never as a listing price.",
        "That is why Jorge prepares a local CMA instead of relying on an automated estimate.",
    ),
    ("estimación instantánea", "estimación automatizada"),
    ("valoración instantánea", "valoración preparada por un agente local"),
    ("under 60 seconds", "after the property request is reviewed"),
    ("less than 60 seconds", "after the property request is reviewed"),
    ("in under a minute", "after the property request is reviewed"),
    ("03 · Free · 60 Seconds", "03 · Free · Property Review"),
    (
        "Takes 60 seconds. No spam. No obligation.",
        "Request takes a few minutes. No spam. No obligation.",
    ),
    (
        "Opens our home valuation tool. Takes within 24 to 48 hours. No spam, no pressure.",
        "Opens our home valuation request. Jorge confirms the scope and timing after reviewing it. No spam, no pressure.",
    ),
    ("free home valuation tool", "free home valuation page"),
    (
        "It's free, it takes 15 minutes, and there's zero obligation.",
        "It's free, Jorge confirms the scope and timing after review, and there's zero obligation.",
    ),
    ("Toma 60 segundos. Sin spam. Sin compromiso.", "La solicitud toma unos minutos. Sin spam. Sin compromiso."),
    ("herramienta gratuita de valoración de casa", "página gratuita de valoración de casa"),
    ("para un estimado instantáneo", "para solicitar un CMA gratuito"),
    (
        "Es gratis, toma 15 minutos y no hay ningún compromiso.",
        "Es gratis, Jorge confirma el alcance y el plazo después de revisar la solicitud y no hay ningún compromiso.",
    ),
    (
        "Jorge's free home valuation has two components: (1) an automated estimate at <a href=\"/home-valuation\">thejorgeramirezgroup.com/home-valuation</a>, and (2) a full Comparative Market Analysis (CMA) where Jorge personally reviews recent comparable sales in your neighborhood, current competition, and market trends to provide a precise value range.",
        "Jorge's free home valuation is a full Comparative Market Analysis (CMA). Submit your property details at <a href=\"/home-valuation\">thejorgeramirezgroup.com/home-valuation</a>, then Jorge reviews relevant comparable sales, current competition, property information, and market conditions to provide a reasoned range with its assumptions and limits.",
    ),
    (
        "La valoración de casa gratuita de Jorge tiene dos partes: (1) una estimación automatizada al instante en <a href=\"/home-valuation\">thejorgeramirezgroup.com/home-valuation</a>, y (2) un Análisis Comparativo de Mercado (CMA) completo en el que Jorge revisa personalmente las ventas comparables recientes en tu vecindario, la competencia actual y las tendencias del mercado para ofrecer un rango de valor preciso.",
        "La valoración de casa gratuita de Jorge es un Análisis Comparativo de Mercado (CMA). Envía los datos de tu propiedad en <a href=\"/home-valuation\">thejorgeramirezgroup.com/home-valuation</a> y Jorge revisará ventas comparables relevantes, la competencia actual, la información de la propiedad y las condiciones del mercado para ofrecer un rango razonado con sus supuestos y limitaciones.",
    ),
    (
        "Herramienta de valoración en línea: https://thejorgeramirezgroup.com/home-valuation.",
        "Solicitud de valoración: https://thejorgeramirezgroup.com/home-valuation.",
    ),
    ("Vea una estimación en línea del valor de su casa", "Solicite una valoración del valor de su casa"),
    (
        "La herramienta gratis le da una primera cifra del valor de mercado de su casa en New Jersey. Escriba su dirección y la ve en el momento.",
        "La solicitud gratis reúne los datos iniciales de la propiedad. Jorge confirma el alcance, la información adicional necesaria y el plazo después de revisarla.",
    ),
    (
        "Empiece con la herramienta en línea si quiere una cifra rápida, o responda unas preguntas por teléfono y Jorge le prepara el análisis completo con las ventas de su vecindario. En cualquiera de los dos casos no hay compromiso.",
        "Empiece con la solicitud en línea o responda unas preguntas por teléfono. Jorge confirma el alcance y el plazo después de revisar los datos. En cualquiera de los dos casos no hay compromiso.",
    ),
    (
        "La herramienta en línea en <a href=\"/home-valuation\" style=\"color: #2C2C2C;\" rel=\"noopener\">thejorgeramirezgroup.com/home-valuation</a> le da una primera cifra en el momento, con solo escribir su dirección. El análisis comparativo completo, con los comparables que sostienen el número, Jorge lo prepara después de conocer los detalles de su propiedad y se lo repasa con usted por teléfono o en persona.",
        "La solicitud en <a href=\"/home-valuation\" style=\"color: #2C2C2C;\" rel=\"noopener\">thejorgeramirezgroup.com/home-valuation</a> reúne los datos iniciales. Jorge confirma el alcance, la información adicional necesaria y el plazo después de revisarla.",
    ),
)

VALUATION_CTA_LABELS = {
    "Get My Home Value": "Request My Home Valuation",
    "Get My Free Home Value": "Request My Free Valuation",
    "Get My Free Home Value Estimate →": "Request My Free Home Valuation →",
    "Get My Valoración Gratis de Casa Estimate →": "Solicitar Mi Valoración Gratis →",
    "Get Your Home's Value": "Request Your Home Valuation",
    "Get Your Home Value →": "Request Your Home Valuation →",
    "Get Your Free Home Value": "Request Your Free Valuation",
    "What Is My Home Worth?": "Request My Free Valuation",
    "Find Out What My Home Is Worth": "Request My Free Valuation",
    "Get My Free Home Value Now": "Request My Free Valuation",
    "Ver el valor de mi casa": "Solicitar Mi Valoración Gratuita",
    "Ver cuánto vale mi casa": "Solicitar Mi Valoración Gratuita",
    "¿Cuánto Vale Mi Casa?": "Solicitar Mi Valoración Gratuita",
}


def public_html_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if ".git" not in path.parts and "node_modules" not in path.parts
    )


def update_valuation_destination(text: str) -> str:
    text = LEGACY_LINK.sub(rf"\g<1>{NEW_PATH}\g<2>", text)
    text = text.replace(OLD_ABSOLUTE, NEW_ABSOLUTE)
    text = text.replace(OLD_HOST, NEW_VISIBLE)
    return FIRST_PARTY_LINK.sub(rf"\g<1>{NEW_PATH}\g<2>", text)


def normalize_valuation_promises(path: Path, text: str) -> str:
    def keep_internal_link_in_tab(match: re.Match[str]) -> str:
        tag = match.group(0)
        if INTERNAL_VALUATION_HREF.search(tag):
            return NEW_TAB_ATTRIBUTE.sub("", tag)
        return tag

    # Normalize the anchor before matching sentence-level replacements so a
    # legacy target="_blank" attribute cannot prevent a truthful copy update.
    text = ANCHOR_TAG.sub(keep_internal_link_in_tab, text)

    # The /features catalog describes separate automation products whose speed
    # claims are unrelated to the consumer valuation intake. Preserve that
    # factual product copy while correcting the site's valuation journey.
    is_feature_page = "features" in path.relative_to(ROOT).parts
    if not is_feature_page:
        for old, new in VALUATION_PROMISE_REPLACEMENTS:
            text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)

    def make_cta_match_the_request(match: re.Match[str]) -> str:
        label = match.group(2).strip()
        replacement = VALUATION_CTA_LABELS.get(label)
        if not replacement:
            return match.group(0)
        return f"{match.group(1)}{replacement}{match.group(3)}"

    return VALUATION_ANCHOR.sub(make_cta_match_the_request, text)


def add_town_main_landmark(path: Path, text: str) -> str:
    if path.parent not in {ROOT / "towns", ROOT / "es" / "towns"}:
        return text
    if TOWN_HERO not in text:
        return text
    if "<main" in text.lower():
        raise ValueError(f"refusing to add a second main landmark to {path.relative_to(ROOT)}")

    text = text.replace(TOWN_HERO, '<main id="main">\n  <section class="hero">', 1)
    text, replacements = TOWN_FOOTER.subn(
        lambda match: f"{match.group(1)}</main>\n\n{match.group(1)}<footer class=\"footer\">",
        text,
        count=1,
    )
    if replacements != 1:
        raise ValueError(f"could not find the town footer in {path.relative_to(ROOT)}")
    return text


def transform(path: Path, text: str) -> str:
    text = update_valuation_destination(text)
    text = normalize_valuation_promises(path, text)
    return add_town_main_landmark(path, text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="report files that would change without writing them",
    )
    args = parser.parse_args()

    changed: list[Path] = []
    for path in public_html_files():
        before = path.read_text(encoding="utf-8")
        after = transform(path, before)
        if after == before:
            continue
        changed.append(path)
        if not args.check:
            path.write_text(after, encoding="utf-8")

    verb = "would update" if args.check else "updated"
    print(f"{verb} {len(changed)} HTML files")
    for path in changed:
        print(path.relative_to(ROOT))
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
