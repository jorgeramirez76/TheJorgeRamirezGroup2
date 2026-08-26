#!/usr/bin/env python3
"""Audit the owned Spanish public-page inventory for fair-housing risk.

The rules are contextual: ordinary transaction uses such as ``seguro de hogar``
or ``mejor oferta`` are allowed, while school/safety rankings, protected-audience
matching, and subjective descriptions of places are not.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_BASE = "91e46ee81037336421a0457cc307736f44d5d8a8"
INVENTORY_PATH = ROOT / "data" / "spanish-fair-housing-inventory.json"
QUARANTINE_PATH = ROOT / "data" / "spanish-fair-housing-quarantine.json"
REDIRECT_STUB = re.compile(r'<meta\b[^>]*http-equiv=["\']refresh["\']', re.I)
MARKET_REPORT = re.compile(r"(?:market-report|real-estate-market|county-market)", re.I)

REBUILT_EXCLUSIONS = {
    "es/blog/best-nj-suburbs-nyc-commuters.html",
    "es/blog/best-nj-towns-for-families.html",
    "es/blog/best-nj-towns-to-sell-home.html",
    "es/blog/best-time-to-sell-home-nj.html",
    "es/blog/first-time-home-buyer-nj-guide.html",
    "es/blog/midtown-direct-towns-nj.html",
    "es/blog/nj-property-tax-guide.html",
    "es/blog/top-nyc-commuter-towns-nj-2026.html",
    "es/nj-train-map.html",
    "es/nj-real-estate-questions-answers.html",
    "es/nj-realty-transfer-fee-calculator.html",
    "es/tools/mortgage-calculator.html",
}

SOURCE_EMITTERS = {
    "build_communities_page.py",
    "data/spanish-snippet-backlog.json",
    "fix_site_issues_v2.py",
    "fix_site_issues_v3.py",
    "fix_spanish_translations.py",
    "generate_blog.py",
    "generate_county_reports_and_comparisons.py",
    "generate_new_landing_pages.py",
    "js/communities-data.js",
    "scripts/apply_spanish_snippets.py",
    "scripts/fix_spanish_internal_links.py",
    "scripts/sync_communities_from_facts.py",
    "tools/fix_spanish_copy_quality.py",
    "tools/render_authority_tools.py",
    "translate_to_spanish.py",
}

GUARDED_EMITTERS = {
    "fix_spanish_translations.py": "Archived legacy token-level translator exits before writing.",
    "generate_blog.py": "Retired fail-closed entry point; it cannot emit public town-report pages.",
    "scripts/apply_spanish_snippets.py": "Skips every Spanish fair-housing quarantine output.",
    "tools/fix_spanish_copy_quality.py": "Skips every Spanish fair-housing quarantine output.",
    "tools/render_authority_tools.py": "Deterministic primary-source renderer owns the consolidated authority/tool Spanish outputs.",
    "translate_to_spanish.py": "Refuses every reviewed or quarantined Spanish output in the exact inventory.",
}

SCHOOL = r"(?:escuelas?|colegios?|distritos?\s+escolares?|sistemas?\s+escolares?)"
PLACE = r"(?:pueblos?|municipios?|ciudades?|comunidades?|vecindarios?|barrios?|suburbios?|zonas?|[aá]reas?|lugares?)"
AUDIENCE = (
    r"(?:familias?(?:\s+(?:j[oó]venes|con\s+(?:ni[nñ]os|hijos)|en\s+crecimiento))?|"
    r"padres?|ni[nñ]os|hijos|j[oó]venes\s+profesionales|profesionales\s+j[oó]venes|"
    r"jubilad[oa]s?|retirad[oa]s?|personas\s+mayores|adultos\s+mayores|"
    r"nidos?\s+vac[ií]os?|parejas?(?:\s+(?:j[oó]venes|sin\s+hijos))?|"
    r"solter[oa]s?|ejecutiv[oa]s?|profesionales)"
)

RISK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "clasificación escolar subjetiva",
        re.compile(
            rf"\b(?:(?:mejor(?:es)?|excelentes?|buen[oa]s?|destacad[oa]s?|sobresalientes?|"
            rf"prestigios[oa]s?|reconocid[oa]s?|s[oó]lid[oa]s?|fuertes?|de\s+primer\s+nivel|"
            rf"de\s+alto\s+rendimiento|altamente\s+calificad[oa]s?|mejor\s+calificad[oa]s?|"
            rf"mejor\s+valorad[oa]s?|ranke?ad[oa]s?|clasificad[oa]s?)\s+(?:\w+\s+){{0,3}}{SCHOOL}|"
            rf"{SCHOOL}[^.<\n]{{0,55}}\b(?:mejor(?:es)?|excelentes?|buen[oa]s?|destacad[oa]s?|"
            rf"sobresalientes?|prestigios[oa]s?|reconocid[oa]s?|s[oó]lid[oa]s?|fuertes?|"
            rf"primer\s+nivel|alto\s+rendimiento|altamente\s+calificad[oa]s?|"
            rf"mejor\s+calificad[oa]s?|mejor\s+valorad[oa]s?|ranke?ad[oa]s?|"
            rf"clasificad[oa]s?|clasificaciones?|rankings?|calificaciones?)\b|"
            rf"\b(?:ranking|rankings|clasificaci[oó]n|clasificaciones|calificaci[oó]n|"
            rf"calificaciones)\s+(?:de\s+)?{SCHOOL}\b|"
            rf"\b{SCHOOL}[^.<\n]{{0,45}}\b(?:A\+|Blue\s+Ribbon|top(?:[- ]tier)?|"
            rf"\d+(?:[.,]\d+)?\s*(?:/|de)\s*(?:5|10))\b|"
            rf"\b(?:A\+|Blue\s+Ribbon|top(?:[- ]tier)?|\d+(?:[.,]\d+)?\s*(?:/|de)\s*(?:5|10))"
            rf"[^.<\n]{{0,45}}\b{SCHOOL}\b|"
            rf"\b(?:GreatSchools|SchoolDigger|Niche\.com)\b)",
            re.I,
        ),
    ),
    (
        "afirmación categórica de seguridad o crimen",
        re.compile(
            rf"\b(?:m[aá]s\s+segur[oa]s?|muy\s+segur[oa]s?|segur[oa]s?\s+y\s+acogedor(?:a|as|es)?|"
            rf"baj[oa]s?\s+(?:(?:tasa|[ií]ndice|nivel)(?:s)?\s+de\s+)?(?:criminalidad|delincuencia|crimen)|"
            rf"bajo\s+(?:nivel\s+de\s+)?crimen|"
            rf"sin\s+crimen|libre\s+de\s+crimen|criminalidad\s+(?:muy\s+)?baja)\b|"
            rf"\b{PLACE}[^.<\n]{{0,35}}\b(?:segur[oa]s?|tranquil[oa]s?(?:\s+y\s+segur[oa]s?)?)\b|"
            rf"\b(?:segur[oa]s?|tranquil[oa]s?(?:\s+y\s+segur[oa]s?)?)[^.<\n]{{0,35}}\b{PLACE}\b|"
            rf"\b(?:seguridad|criminalidad|delincuencia)[^.<\n]{{0,25}}\b(?:excelente|alta|baja|mejor)\b",
            re.I,
        ),
    ),
    (
        "segmentación por clase protegida o perfil",
        re.compile(
            rf"\b(?:ideal(?:es)?|perfect[oa]s?|mejor(?:es)?|excelente(?:s)?|popular(?:es)?|"
            rf"atractiv[oa]s?|diseñad[oa]s?|pensad[oa]s?|refugio|im[aá]n|destino)\s+para\s+{AUDIENCE}\b|"
            rf"\b(?:atrae(?:n)?|atraer|atraen\s+a|pref(?:erid[oa]s?|iere(?:n)?)\s+por|"
            rf"popular(?:es)?\s+entre|muy\s+solicitad[oa]s?\s+por)[^.<\n]{{0,45}}\b{AUDIENCE}\b|"
            rf"\b{AUDIENCE}[^.<\n]{{0,55}}\b(?:buscan|prefieren|eligen|se\s+mudan|"
            rf"se\s+trasladan|quieren|necesitan)[^.<\n]{{0,65}}\b{PLACE}\b|"
            rf"\b(?:amigable|ideal|perfect[oa]|orientad[oa]|enfocad[oa])\s+para\s+familias\b|"
            rf"\b(?:ambiente|vida|estilo\s+de\s+vida|mercado|demanda|zona|vecindario|barrio)\s+familiar\b",
            re.I,
        ),
    ),
    (
        "audiencia protegida o perfil de comprador",
        re.compile(
            rf"\b(?:familias?\s+j[oó]venes|familias?\s+con\s+(?:ni[nñ]os|hijos)|"
            rf"compradores?\s+con\s+(?:ni[nñ]os|hijos)|(?:ni[nñ]os|hijos)\s+en\s+edad\s+escolar|"
            rf"profesionales\s+j[oó]venes|j[oó]venes\s+profesionales|jubilad[oa]s?|retirad[oa]s?|"
            rf"nidos?\s+vac[ií]os?|parejas?\s+sin\s+hijos|familias?\s+de\s+doble\s+ingreso|"
            rf"familias?\s+en\s+crecimiento|familias?\s+(?:compradoras|vendedoras|viajeras)|"
            rf"familias?\s+(?:que|con|buscando|buscan|priorizan|quieren|necesitan|eligen|"
            rf"se\s+mudan|se\s+trasladan|dejan|salen\s+de)[^.<\n]{{0,55}}"
            rf"(?:escuelas?|distritos?|pueblos?|municipios?|comunidades?|vecindarios?|barrios?|"
            rf"suburbios?|viaje|traslado|espacio|patio|vivienda)|"
            rf"(?:ni[nñ]os|hijos)[^.<\n]{{0,45}}(?:escuelas?|distritos?|pueblos?|municipios?|"
            rf"comunidades?|vecindarios?|barrios?|suburbios?|se\s+(?:mudan|muden|van|fueron)|"
            rf"universidad|edad\s+escolar|vivienda|espacio|patio)|"
            rf"compradores?\s+(?:que|buscando|buscan|priorizan|centrados?\s+en)[^.<\n]{{0,50}}"
            rf"(?:escuelas?|distritos?\s+escolares?)|"
            rf"familias?\s+(?:de\s+NYC|que\s+)?(?:valoran|necesitan|dan|pagan|atra[ií]das?|"
            rf"priorizan|quieren|buscan|eligen|prefieren)[^.<\n]{{0,65}}(?:escuelas?|"
            rf"zona\s+escolar|distritos?|pueblos?|municipios?|comunidades?|vecindarios?|"
            rf"barrios?|suburbios?|viaje|traslado|vivienda|casa|espacio|patio)|"
            rf"(?:demanda\s+de|m[aá]s)\s+familias?\b|"
            rf"\b(?:para|por|entre)\s+(?:las?\s+)?familias?\b|"
            rf"\b(?:criar|formar)\s+una\s+familia\b|"
            rf"\bfamilia\s+(?:minorista|y\s+tu\s+presupuesto)\b|"
            rf"(?:casa|vivienda|vida|estilo\s+de\s+vida|ambiente|aire|suburbio|pueblo|"
            rf"comunidad|vecindario|barrio|demanda|mercado)\s+familiar(?:es)?|"
            rf"(?:enfocad[oa]|orientad[oa]|amigable)\s+(?:en|para)\s+(?:la\s+)?familia)\b",
            re.I,
        ),
    ),
    (
        "ranking o recomendación subjetiva de comunidad",
        re.compile(
            rf"\b(?:mejor(?:es)?|perfect[oa]s?|ideal(?:es)?|m[aá]s\s+desead[oa]s?|"
            rf"m[aá]s\s+deseables?|exclusiv[oa]s?|prestigios[oa]s?|afluentes?|adinerad[oa]s?|"
            rf"de\s+[eé]lite|de\s+primer\s+nivel|premium|de\s+lujo|joya\s+escondida|"
            rf"joya|punto\s+ideal)\s+(?:de\s+|del\s+|para\s+)?(?:NJ|Nueva\s+Jersey\s+)?{PLACE}\b|"
            rf"\b{PLACE}[^.<\n]{{0,45}}\b(?:mejor(?:es)?|perfect[oa]s?|ideal(?:es)?|"
            rf"m[aá]s\s+desead[oa]s?|m[aá]s\s+deseables?|exclusiv[oa]s?|prestigios[oa]s?|"
            rf"afluentes?|adinerad[oa]s?|de\s+[eé]lite|de\s+primer\s+nivel|premium|"
            rf"joya\s+escondida|m[aá]s\s+codiciad[oa]s?|m[aá]s\s+destacad[oa]s?)\b|"
            rf"\b(?:uno|una)\s+de\s+los\s+{PLACE}[^.<\n]{{0,30}}\b(?:mejor(?:es)?|"
            rf"m[aá]s\s+deseables?|m[aá]s\s+segur[oa]s?|m[aá]s\s+prestigios[oa]s?|"
            rf"m[aá]s\s+codiciad[oa]s?|m[aá]s\s+destacad[oa]s?)\b|"
            rf"\b(?:uno|una)\s+de\s+(?:los|las)\s+(?:mejor(?:es)?|m[aá]s\s+deseables?|"
            rf"m[aá]s\s+codiciad[oa]s?|m[aá]s\s+destacad[oa]s?)[^.<\n]{{0,35}}\b{PLACE}\b",
            re.I,
        ),
    ),
    (
        "descripción subjetiva de comunidad",
        re.compile(
            rf"\b(?:extraordinari[oa]s?|excepcional(?:es)?|acogedor(?:a|as|es)?|"
            rf"unid[oa]s?|familiar(?:es)?|pintoresc[oa]s?)\s+{PLACE}\b|"
            rf"\b{PLACE}[^.<\n]{{0,45}}\b(?:extraordinari[oa]s?|excepcional(?:es)?|"
            rf"acogedor(?:a|as|es)?|unid[oa]s?|familiar(?:es)?|pintoresc[oa]s?)\b|"
            rf"\b(?:calidad\s+de\s+vida|encaja\s+con\s+tu\s+estilo\s+de\s+vida)"
            rf"[^.<\n]{{0,55}}\b{PLACE}\b|"
            rf"\b{PLACE}[^.<\n]{{0,55}}\b(?:calidad\s+de\s+vida|"
            rf"encaja\s+con\s+tu\s+estilo\s+de\s+vida)\b",
            re.I,
        ),
    ),
    (
        "diversidad o demografía como segmentación",
        re.compile(
            rf"\b(?:divers[oa]s?|inclusiv[oa]s?|multicultural(?:es)?|predominantemente\s+"
            rf"(?:blanc[oa]s?|negr[oa]s?|latin[oa]s?|hispan[oa]s?|asi[aá]tic[oa]s?))\s+{PLACE}\b|"
            rf"\b{PLACE}[^.<\n]{{0,35}}\b(?:divers[oa]s?|inclusiv[oa]s?|multicultural(?:es)?)\b|"
            rf"\b(?:perfil|composici[oó]n)\s+demogr[aá]fic[oa]\b|"
            rf"\bdiversidad\s+(?:racial|[eé]tnica|religiosa|demogr[aá]fica)[^.<\n]{{0,45}}"
            rf"\b(?:atrae|atractivo|demanda|compradores?|residentes?)\b",
            re.I,
        ),
    ),
    (
        "escuela como proxy de valor o demanda",
        re.compile(
            rf"\b{SCHOOL}[^.<\n]{{0,75}}\b(?:impulsa(?:n)?|protege(?:n)?|aumenta(?:n)?|"
            rf"eleva(?:n)?|sostiene(?:n)?|genera(?:n)?|prima)\s+(?:la\s+)?(?:demanda|"
            rf"valor(?:es)?|precios?|reventa)|"
            rf"\b(?:demanda|valor(?:es)?|precios?|reventa)[^.<\n]{{0,75}}\b(?:por|debido\s+a)"
            rf"[^.<\n]{{0,35}}\b{SCHOOL}\b",
            re.I,
        ),
    ),
    (
        "segmentación publicitaria por audiencia protegida",
        re.compile(
            r"\b(?:segmentaci[oó]n|perfilado|grupo\s+demogr[aá]fico|audiencia)"
            r"[^.<\n]{0,75}\b(?:familias?|ni[nñ]os|hijos|edad|jubilad[oa]s?|"
            r"retirad[oa]s?|adultos\s+mayores)\b|"
            r"\b(?:familias?|ni[nñ]os|hijos|jubilad[oa]s?|retirad[oa]s?)"
            r"[^.<\n]{0,75}\b(?:segmentaci[oó]n|perfilado|audiencia|anuncios?)\b",
            re.I,
        ),
    ),
    (
        "volumen de clientes no verificado",
        re.compile(
            r"\b(?:(?:muchas|decenas|docenas|cientos|miles)\s+de\s+familias?|"
            r"familias?\s+han\s+confiado\s+en\s+m[ií]|"
            r"(?:he|ha|han|hemos)\s+(?:ayudado|trabajado\s+con)\s+(?:a\s+)?"
            r"(?:muchas|decenas|docenas|cientos|miles)\s+(?:de\s+)?familias?)\b",
            re.I,
        ),
    ),
    (
        "Spanglish de alto impacto",
        re.compile(
            r"\b(?:best\s+(?:town|towns|school|schools|neighborhood|neighborhoods)|"
            r"top[- ]rated|family[- ]friendly|young\s+professionals?|retirees?|"
            r"empty[- ]nesters?|safe(?:st)?\s+(?:town|community|neighborhood)|"
            r"low[- ]crime|perfect\s+for\s+families|"
            r"(?:el|la|un|una|los|las|con|por|para|de)\s+downtown|"
            r"downtown\s+(?:caminable|vibrante|cl[aá]sico|cultural|art[ií]stico|boutique)|"
            r"escuelas?\s+top(?:[- ]tier)?|stock\s+de\s+vivienda|"
            r"(?:los?|para)\s+commuters?|commuters?\s+de\s+NYC|"
            r"tour\s+de\s+casas|premium\s+(?:ejecutivo|corporativo))\b",
            re.I,
        ),
    ),
    (
        "frase española defectuosa",
        re.compile(
            r"\b(?:Qué\s+Cómo|municipio\s+comparar|distintos\s+balance|"
            r"el\s+municipios|la\s+municipios?|los\s+municipio|las\s+municipio|"
            r"las\s+propietarios|los\s+propietarias|municipios?\s+para\s+comparar\s+de|"
            r"para\s+investigar\s+con\s+fuentes\s+oficiales\s+públicos|"
            r"con\s+licencia\s+en\s+Nueva\s+Jersey\s+de\s+NJ|"
            r"comunidades?\s+con\s+distintos\s+tipos\s+de\s+vivienda\s+de\s+Estados\s+Unidos|"
            r"de\s+las\s+mejor\s+calificadas|cuál\s+municipio\s+comparar)\b",
            re.I,
        ),
    ),
)


@dataclass(frozen=True)
class Issue:
    path: str
    category: str
    match: str


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8", errors="replace")


def quarantined_files() -> set[str]:
    if not QUARANTINE_PATH.exists():
        return set()
    payload = json.loads(QUARANTINE_PATH.read_text(encoding="utf-8"))
    return {item["file"] for item in payload["pages"]}


def server_redirect_files() -> set[str]:
    payload = json.loads(read("vercel.json"))
    files: set[str] = set()
    for item in payload.get("redirects", []):
        source = item.get("source", "")
        if not source.startswith("/es/") or not source.endswith(".html") or ":" in source:
            continue
        relative = source.lstrip("/")
        if (ROOT / relative).exists():
            files.add(relative)
    return files


def discover_inventory() -> dict[str, list[str]]:
    excluded = {"rebuilt": [], "market_reports": [], "redirects": [], "directories": []}
    owned: list[str] = []
    quarantined = quarantined_files()
    server_redirects = server_redirect_files()
    for path in sorted((ROOT / "es").rglob("*.html")):
        relative = path.relative_to(ROOT).as_posix()
        parts = path.relative_to(ROOT / "es").parts
        source = path.read_text(encoding="utf-8", errors="replace")
        if parts and parts[0] in {"towns", "realtor"}:
            excluded["directories"].append(relative)
        elif relative in REBUILT_EXCLUSIONS:
            excluded["rebuilt"].append(relative)
        elif MARKET_REPORT.search(path.name):
            excluded["market_reports"].append(relative)
        elif relative in quarantined:
            owned.append(relative)
        elif relative in server_redirects or REDIRECT_STUB.search(source):
            excluded["redirects"].append(relative)
        else:
            owned.append(relative)
    return {"owned": owned, **excluded}


def scan_text(source: str) -> str:
    source = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.I | re.S)
    source = re.sub(
        r"<script\b(?![^>]*application/ld\+json)[^>]*>.*?</script>",
        " ",
        source,
        flags=re.I | re.S,
    )
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    attributes: list[str] = []
    for tag in re.findall(r"<[^>]+>", source, flags=re.S):
        names = ("content",) if re.match(r"<meta\b", tag, re.I) else ("alt", "aria-label", "title")
        for name in names:
            match = re.search(rf'\b{name}\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
            if match:
                attributes.append(match.group(2))
    body = re.sub(
        r"</?(?:address|article|aside|blockquote|br|dd|div|dl|dt|fieldset|figcaption|"
        r"figure|footer|form|h[1-6]|header|hr|li|main|nav|ol|p|section|table|tbody|td|"
        r"tfoot|th|thead|tr|ul)\b[^>]*>",
        ". ",
        source,
        flags=re.I,
    )
    body = re.sub(r"<[^>]+>", " ", body)
    return html.unescape(". ".join([body, *attributes]))


def scan_file(relative: str) -> list[Issue]:
    candidate = scan_text(read(relative)) if relative.endswith(".html") else read(relative)
    issues: list[Issue] = []
    for category, pattern in RISK_PATTERNS:
        for match in pattern.finditer(candidate):
            normalized = " ".join(match.group(0).split()).casefold()
            if (
                relative == "translate_to_spanish.py"
                and category == "Spanglish de alto impacto"
                and normalized == "top rated"
                and "('Top Rated', 'Agente con Licencia en Nueva Jersey')" in candidate
            ):
                # The English input key is explicitly normalized to factual,
                # non-ranking Spanish before any page is written.
                continue
            if (
                relative == "es/first-time-buyer-nj-programs.html"
                and category == "audiencia protegida o perfil de comprador"
                and normalized in {"jubilado", "jubilados"}
            ):
                # Objective eligibility language for the named PFRS mortgage,
                # not housing-audience targeting.
                continue
            if category == "afirmación categórica de seguridad o crimen" and (
                "zonas de inundación y seguros" in normalized
                or "seguro contra inundaciones" in normalized
            ):
                continue
            issues.append(Issue(relative, category, " ".join(match.group(0).split())))
    return issues


def expected_payload() -> dict[str, object]:
    discovered = discover_inventory()
    quarantined = quarantined_files()
    return {
        "base": SOURCE_BASE,
        "reviewed": sorted(set(discovered["owned"]) - quarantined),
        "quarantined": sorted(quarantined),
        "emitters": sorted(SOURCE_EMITTERS),
        "guarded_emitters": GUARDED_EMITTERS,
        "excluded": {key: discovered[key] for key in ("rebuilt", "market_reports", "redirects", "directories")},
    }


def audit() -> list[Issue]:
    payload = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    targets = sorted(
        set(payload["reviewed"])
        | set(payload.get("quarantined", []))
        | set(payload.get("emitters", []))
    )
    issues: list[Issue] = []
    for relative in targets:
        issues.extend(scan_file(relative))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-inventory", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.write_inventory:
        INVENTORY_PATH.write_text(
            json.dumps(expected_payload(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    if not INVENTORY_PATH.exists():
        parser.error("inventory missing; run once with --write-inventory")
    issues = audit()
    if args.json:
        print(json.dumps([issue.__dict__ for issue in issues], indent=2, ensure_ascii=False))
    else:
        print(f"Auditoría de vivienda justa en español: {len(issues)} hallazgo(s)")
        for issue in issues[:300]:
            print(f" - {issue.path}: {issue.category}: {issue.match}")
        if len(issues) > 300:
            print(f" ... {len(issues) - 300} hallazgos adicionales")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
