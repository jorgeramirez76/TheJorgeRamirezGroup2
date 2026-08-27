#!/usr/bin/env python3
"""Render the reviewed market-report redirects and research fallbacks."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / "data" / "market-report-containment.json"
SITE = "https://thejorgeramirezgroup.com"
SKIP_DIRS = {".git", "crm", "docs", "node_modules", "property-leads-system"}
QUARTERLY_LINK_REPLACEMENTS = {
    "/blog/essex-county-real-estate-market-q2-2026": (
        "/blog/essex-county-nj-real-estate-market-2026",
        "current Essex County report",
    ),
    "/es/blog/essex-county-real-estate-market-q2-2026": (
        "/es/blog/essex-county-nj-real-estate-market-2026",
        "informe vigente del condado de Essex",
    ),
    "/blog/morris-county-real-estate-market-q2-2026": (
        "/blog/morris-county-nj-real-estate-market-2026",
        "current Morris County report",
    ),
    "/es/blog/morris-county-real-estate-market-q2-2026": (
        "/es/blog/morris-county-nj-real-estate-market-2026",
        "informe vigente del condado de Morris",
    ),
}
QUARANTINED_GENERATORS = {
    "generate_blog.py": "town report page",
    "generate_county_reports_and_comparisons.py": "county report page",
}


def load_inventory(path: Path = DEFAULT_INVENTORY) -> dict[str, Any]:
    """Load and minimally validate the reviewed containment inventory."""

    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("containment inventory must be an object")
    required = ("version", "reviewedOn", "redirectPairs", "noindexTownReports")
    missing = [key for key in required if key not in document]
    if missing:
        raise ValueError(f"containment inventory is missing: {', '.join(missing)}")
    if document.get("siteOrigin") != SITE:
        raise ValueError("containment inventory siteOrigin is unexpected")
    return document


def _route_path(route: str, root: Path) -> Path:
    if not route.startswith("/") or route.endswith(".html"):
        raise ValueError(f"expected a clean site route, got {route!r}")
    return root / f"{route.lstrip('/')}.html"


def generated_page_paths(inventory: Mapping[str, Any], *, root: Path) -> list[Path]:
    """Return the exact set of public fallback files managed by this generator."""

    result: list[Path] = []
    for pair in inventory["redirectPairs"]:
        for language in ("en", "es"):
            result.append(_route_path(pair["source"][language], root))
    for item in inventory["noindexTownReports"]:
        slug = item["slug"]
        result.append(root / "blog" / f"market-report-{slug}-nj-2026.html")
        result.append(root / "es" / "blog" / f"market-report-{slug}-nj-2026.html")
    return result


def _shared_head(*, title: str, description: str, canonical: str) -> str:
    title_attr = html.escape(title, quote=True)
    description_attr = html.escape(description, quote=True)
    return f"""  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(title)}</title>
  <meta name=\"description\" content=\"{description_attr}\">
  <meta name=\"robots\" content=\"noindex, follow\">
  <meta name=\"theme-color\" content=\"#1A1A1A\">
  <link rel=\"canonical\" href=\"{html.escape(canonical, quote=True)}\">
  <meta property=\"og:title\" content=\"{title_attr}\">
  <meta property=\"og:description\" content=\"{description_attr}\">
  <meta property=\"og:url\" content=\"{html.escape(canonical, quote=True)}\">
  <meta property=\"og:type\" content=\"website\">
  <meta name=\"twitter:card\" content=\"summary\">
  <meta name=\"twitter:title\" content=\"{title_attr}\">
  <meta name=\"twitter:description\" content=\"{description_attr}\">
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&amp;family=Playfair+Display:wght@700&amp;display=swap\" rel=\"stylesheet\">
  <link rel=\"stylesheet\" href=\"/css/styles.css\">"""


def _shared_styles() -> str:
    return """  <style>
    :root{--ink:#1A1A1A;--red:#C41230;--gold:#B8962E;--ivory:#FAFAF8;--muted:#5d5d5d}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--ivory);color:var(--ink);font-family:Inter,Arial,sans-serif;line-height:1.65}
    .skip{position:absolute;left:12px;top:-80px;z-index:20;background:var(--gold);color:var(--ink);padding:10px 16px;font-weight:700}.skip:focus{top:12px}
    header{background:var(--ink);border-bottom:3px solid var(--gold)}.bar{max-width:1040px;margin:auto;min-height:72px;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;gap:20px}
    .brand{color:var(--ivory);font-family:'Playfair Display',Georgia,serif;font-size:clamp(1.05rem,3vw,1.35rem);text-decoration:none}.brand span{color:var(--gold)}
    .language{color:var(--ivory);text-decoration:none;border:1px solid var(--gold);border-radius:2px;padding:9px 14px;min-height:44px;display:inline-flex;align-items:center}
    main{min-height:calc(100vh - 150px);display:grid;place-items:center;padding:clamp(36px,7vw,88px) 20px;background:linear-gradient(135deg,rgba(26,26,26,.04),transparent 55%)}
    .card{width:min(760px,100%);background:#fff;border-top:6px solid var(--red);box-shadow:0 18px 48px rgba(26,26,26,.12);padding:clamp(28px,6vw,58px)}
    .eyebrow{color:var(--red);font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:.8rem}.rule{width:64px;border:0;border-top:3px solid var(--gold);margin:20px 0}
    h1{font-family:'Playfair Display',Georgia,serif;font-size:clamp(2rem,6vw,3.5rem);line-height:1.08;margin:.35rem 0;color:var(--ink)}p{max-width:65ch;color:var(--muted)}
    .actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}.button{min-height:44px;display:inline-flex;align-items:center;justify-content:center;padding:10px 18px;border:2px solid var(--red);background:var(--red);color:#fff;text-decoration:none;font-weight:700}.button.alt{background:transparent;color:var(--ink);border-color:var(--gold)}
    .sources{margin-top:30px;padding-top:22px;border-top:1px solid #ddd}.sources a{color:var(--red);text-underline-offset:3px;min-height:44px;display:inline-flex;align-items:center}
    a:focus-visible{outline:3px solid var(--gold);outline-offset:3px}footer{background:var(--ink);color:var(--ivory);text-align:center;padding:18px 20px;font-size:.85rem}
    @media(max-width:560px){.bar{min-height:64px}.card{padding:28px 22px}.actions{display:grid}.button{width:100%}}
    @media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
  </style>"""


def _analytics() -> str:
    return """  <script async src=\"https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0\"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>"""


def _shell(*, language: str, head: str, main: str, extra_head: str = "", script: str = "") -> str:
    home = "/" if language == "en" else "/es/"
    switch = "/es/" if language == "en" else "/"
    switch_label = "English" if language == "es" else "Español"
    footer = (
        "Independent real estate guidance for northern New Jersey."
        if language == "en"
        else "Orientación inmobiliaria independiente para el norte de Nueva Jersey."
    )
    return f"""<!doctype html>
<html lang=\"{language}\">
<head>
{head}
{extra_head}
{_shared_styles()}
{_analytics()}
</head>
<body>
  <a class=\"skip\" href=\"#main-content\">{('Skip to content' if language == 'en' else 'Saltar al contenido')}</a>
  <header><div class=\"bar\"><a class=\"brand\" href=\"{home}\">THE JORGE RAMIREZ <span>GROUP</span></a><a class=\"language\" href=\"{switch}\">{switch_label}</a></div></header>
{main}
  <footer>{footer}</footer>
{script}
</body>
</html>
"""


def render_redirect(source_route: str, destination: str, language: str) -> str:
    if "chatham" in source_route:
        topic = "Chatham"
    elif "westfield" in source_route:
        topic = "Westfield"
    elif "essex-county" in source_route:
        topic = "Essex County" if language == "en" else "condado de Essex"
    elif "morris-county" in source_route:
        topic = "Morris County" if language == "en" else "condado de Morris"
    else:
        topic = "Millburn / Short Hills"
    if language == "en":
        title = f"{topic} report moved | Jorge Ramirez"
        description = f"Continue to the current real estate research page for {topic}."
        eyebrow = "Research library update"
        heading = f"The {topic} report has moved"
        copy = "Use the current research page for the reviewed version of this topic."
        label = "Continue to the current report"
    else:
        title = f"Informe de {topic} trasladado | Jorge Ramirez"
        description = f"Continúe a la página vigente de investigación inmobiliaria de {topic}."
        eyebrow = "Actualización de la biblioteca"
        heading = f"El informe de {topic} cambió de ubicación"
        copy = "Use la página vigente para consultar la versión revisada de este tema."
        label = "Continuar al informe vigente"
    canonical = SITE + destination
    head = _shared_head(title=title, description=description, canonical=canonical)
    refresh = f'  <meta http-equiv="refresh" content="0; url={html.escape(destination, quote=True)}">'
    main = f"""  <main id=\"main-content\"><article class=\"card\">
    <div class=\"eyebrow\">{eyebrow}</div><h1>{heading}</h1><hr class=\"rule\"><p>{copy}</p>
    <div class=\"actions\"><a class=\"button\" href=\"{html.escape(destination, quote=True)}\">{label}</a></div>
  </article></main>"""
    script = f'  <script>window.location.replace({json.dumps(destination)});</script>'
    return _shell(
        language=language,
        head=head,
        extra_head=refresh,
        main=main,
        script=script,
    )


def render_research_fallback(item: Mapping[str, Any], language: str) -> str:
    slug = item["slug"]
    town_guide_slug = item.get("townGuideSlug", slug)
    prefix = "" if language == "en" else "/es"
    route = f"{prefix}/blog/market-report-{slug}-nj-2026"
    town_route = f"{prefix}/towns/{town_guide_slug}"
    valuation_route = "/home-valuation" if language == "en" else "/es/home-valuation"
    name = html.escape(item["name"][language])
    geography = html.escape(item["officialGeography"][language])
    county = html.escape(item["county"][language])
    if language == "en":
        title = f"{name} real estate research update | Jorge Ramirez"
        description = f"Source review notice and official research links for {name}, New Jersey."
        eyebrow = "Source review in progress"
        heading = f"{name} research update"
        body = (
            "This local report is temporarily withheld while each statement is matched "
            "to a reviewed public source. The public NJ Realtors portal provides state "
            "and county reports; municipality detail needs a separate documented review."
        )
        geography_label = "Official geography used for local public records"
        context = f"{geography}, within {county}."
        town_label = f"Explore the {name} community guide"
        value_label = "Request an address-specific valuation"
        sources_title = "Official research starting points"
        source_one = "NJ Realtors public reports"
        source_two = "New Jersey property-tax statistics"
    else:
        title = f"Investigación inmobiliaria de {name} | Jorge Ramirez"
        description = f"Aviso de revisión de fuentes y enlaces oficiales para {name}, Nueva Jersey."
        eyebrow = "Revisión de fuentes en curso"
        heading = f"Actualización de investigación de {name}"
        body = (
            "Este informe local está temporalmente retirado mientras cada afirmación se "
            "vincula con una fuente pública revisada. El portal público de NJ Realtors "
            "ofrece informes estatales y de condado; el detalle municipal necesita una "
            "revisión documentada por separado."
        )
        geography_label = "Geografía oficial usada para los registros públicos locales"
        context = f"{geography}, dentro del {county}."
        town_label = f"Ver la guía comunitaria de {name}"
        value_label = "Solicitar una valoración específica de la propiedad"
        sources_title = "Fuentes oficiales para iniciar la investigación"
        source_one = "Informes públicos de NJ Realtors"
        source_two = "Estadísticas de impuestos sobre la propiedad de Nueva Jersey"
    canonical = SITE + route
    head = _shared_head(title=title, description=description, canonical=canonical)
    main = f"""  <main id=\"main-content\"><article class=\"card\">
    <div class=\"eyebrow\">{eyebrow}</div><h1>{heading}</h1><hr class=\"rule\">
    <p>{body}</p><p><strong>{geography_label}:</strong> {context}</p>
    <div class=\"actions\"><a class=\"button\" href=\"{town_route}\">{town_label}</a><a class=\"button alt\" href=\"{valuation_route}\">{value_label}</a></div>
    <section class=\"sources\" aria-labelledby=\"source-heading\"><h2 id=\"source-heading\">{sources_title}</h2>
      <p><a href=\"https://www.njrealtor.com/research/10k/\">{source_one}</a><br><a href=\"https://www.nj.gov/treasury/taxation/lpt/statdata.shtml\">{source_two}</a></p>
    </section>
  </article></main>"""
    return _shell(language=language, head=head, main=main)


def rendered_pages(inventory: Mapping[str, Any], *, root: Path) -> dict[Path, str]:
    result: dict[Path, str] = {}
    for pair in inventory["redirectPairs"]:
        for language in ("en", "es"):
            source_route = pair["source"][language]
            result[_route_path(source_route, root)] = render_redirect(
                source_route, pair["destination"][language], language
            )
    for item in inventory["noindexTownReports"]:
        slug = item["slug"]
        result[root / "blog" / f"market-report-{slug}-nj-2026.html"] = (
            render_research_fallback(item, "en")
        )
        result[root / "es" / "blog" / f"market-report-{slug}-nj-2026.html"] = (
            render_research_fallback(item, "es")
        )
    return result


def contained_routes(inventory: Mapping[str, Any]) -> set[str]:
    """Return every route that must stay out of indexable discovery surfaces."""

    result = {
        pair["source"][language]
        for pair in inventory["redirectPairs"]
        for language in ("en", "es")
    }
    for item in inventory["noindexTownReports"]:
        slug = item["slug"]
        result.add(f"/blog/market-report-{slug}-nj-2026")
        result.add(f"/es/blog/market-report-{slug}-nj-2026")
    return result


def _anchor_pattern(route: str) -> re.Pattern[str]:
    route_pattern = re.escape(route)
    site_pattern = re.escape(SITE)
    return re.compile(
        rf"<a\b[^>]*\bhref=(?P<quote>['\"])(?:{site_pattern})?"
        rf"{route_pattern}(?:\.html)?(?:[?#][^'\"]*)?(?P=quote)[^>]*>"
        rf"(?:(?!</a>).)*?</a>",
        re.IGNORECASE | re.DOTALL,
    )


def _clean_indexable_html(source: str, routes: set[str]) -> str:
    """Remove contained report cards/links without reserializing surrounding HTML."""

    original = source
    route_tokens = tuple(f'href="{route}' for route in routes) + tuple(
        f"href='{route}" for route in routes
    )
    kept_lines: list[str] = []
    for line in source.splitlines(keepends=True):
        lowered = line.lower()
        if "<li" in lowered and any(token in line for token in route_tokens):
            continue
        if (
            "<p" in lowered
            and "market figures above are drawn" in lowered
            and any(token in line for token in route_tokens)
        ):
            continue
        stripped = line.strip()
        if (
            stripped.lower().startswith("<a ")
            and stripped.lower().endswith("</a>")
            and any(token in line for token in route_tokens)
        ):
            continue
        kept_lines.append(line)
    cleaned = "".join(kept_lines)

    # Quarterly source links on editorial pages can safely point to their current
    # annual consolidation target. Hub list items were already removed above to
    # avoid duplicate cards.
    for route, (destination, label) in QUARTERLY_LINK_REPLACEMENTS.items():
        pattern = _anchor_pattern(route)

        def replace_quarterly_link(match: re.Match[str]) -> str:
            anchor = match.group(0).replace(route, destination)
            return re.sub(
                r">(?:(?!</a>).)*?</a>$",
                f">{label}</a>",
                anchor,
                flags=re.IGNORECASE | re.DOTALL,
            )

        cleaned = pattern.sub(replace_quarterly_link, cleaned)

    for route in sorted(routes, key=len, reverse=True):
        anchor = _anchor_pattern(route)
        # Remove the adjacent list separator as well, preferring the separator
        # before an item so the first surviving link remains untouched.
        with_before = re.compile(
            rf"\s*(?:&middot;|&mdash;|·)\s*{anchor.pattern}",
            anchor.flags,
        )
        cleaned, count = with_before.subn("", cleaned)
        if count:
            continue
        with_after = re.compile(
            rf"{anchor.pattern}\s*(?:&middot;|&mdash;|·)\s*",
            anchor.flags,
        )
        cleaned, count = with_after.subn("", cleaned)
        if count:
            continue
        cleaned = anchor.sub("", cleaned)

    if cleaned == original:
        return original
    cleaned = re.sub(r"<p>\s*</p>", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _clean_sitemap(source: str, routes: set[str]) -> str:
    """Drop complete URL records whose loc is a contained clean route."""

    cleaned = source
    for route in sorted(routes, key=len, reverse=True):
        loc = re.escape(SITE + route)
        block = re.compile(
            rf"[ \t]*<url>\s*<loc>{loc}</loc>.*?</url>\s*",
            re.IGNORECASE | re.DOTALL,
        )
        cleaned = block.sub("", cleaned)
    return cleaned


def _required_redirects(inventory: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for pair in inventory["redirectPairs"]:
        for language in ("en", "es"):
            source = pair["source"][language]
            destination = pair["destination"][language]
            for alias in (source + ".html", source):
                result.append(
                    {
                        "source": alias,
                        "destination": destination,
                        "permanent": True,
                    }
                )
    return result


def _is_canonical_host_rule(rule: Mapping[str, Any]) -> bool:
    return (
        str(rule.get("source", "")) == "/(.*)"
        and str(rule.get("destination", "")) == SITE + "/$1"
        and any(
            condition.get("type") == "host"
            for condition in rule.get("has", [])
            if isinstance(condition, Mapping)
        )
    )


def _redirect_insertion_offset(source: str, marker: str, preamble_count: int) -> int:
    """Return the byte-safe text offset immediately after the host preamble."""

    cursor = source.index(marker) + len(marker)
    decoder = json.JSONDecoder()
    for _ in range(preamble_count):
        while cursor < len(source) and source[cursor] in " \t":
            cursor += 1
        _, cursor = decoder.raw_decode(source, cursor)
        if source.startswith(",\r\n", cursor):
            cursor += 3
        elif source.startswith(",\n", cursor):
            cursor += 2
        else:
            raise ValueError("vercel.json canonical host preamble format is unsupported")
    return cursor


def _ensure_vercel_redirects(
    source: str, inventory: Mapping[str, Any]
) -> str:
    """Insert only missing exact redirects while preserving config formatting."""

    document = json.loads(source)
    existing = {
        rule.get("source"): rule
        for rule in document.get("redirects", [])
        if isinstance(rule, dict) and rule.get("source")
    }
    missing: list[dict[str, Any]] = []
    for rule in _required_redirects(inventory):
        current = existing.get(rule["source"])
        if current is None:
            missing.append(rule)
            continue
        if (
            current.get("destination") != rule["destination"]
            or current.get("permanent") is not True
            or current.get("has")
        ):
            raise ValueError(f"conflicting redirect rule for {rule['source']}")
    if not missing:
        return source

    marker = '  "redirects": [\n'
    if marker not in source:
        raise ValueError("vercel.json redirects array format is unsupported")
    redirects = document.get("redirects", [])
    preamble_count = 0
    while preamble_count < len(redirects) and _is_canonical_host_rule(
        redirects[preamble_count]
    ):
        preamble_count += 1
    blocks = []
    for rule in missing:
        blocks.append(
            "    {\n"
            f"      \"source\": {json.dumps(rule['source'])},\n"
            f"      \"destination\": {json.dumps(rule['destination'])},\n"
            "      \"permanent\": true\n"
            "    },\n"
        )
    insertion = _redirect_insertion_offset(source, marker, preamble_count)
    return source[:insertion] + "".join(blocks) + source[insertion:]


def _is_indexable_html(source: str) -> bool:
    robots = re.search(
        r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\']([^"\']*)',
        source,
        flags=re.IGNORECASE,
    )
    if robots and "noindex" in robots.group(1).lower():
        return False
    return not bool(
        re.search(r'<meta\b[^>]*http-equiv=["\']refresh["\']', source, re.I)
    )


def _rebuild_page_paths(inventory: Mapping[str, Any], root: Path) -> set[Path]:
    return {
        root / prefix / "blog" / f"{stub}.html"
        for stub in inventory["rebuildPairs"]
        for prefix in (Path(), Path("es"))
    }


def _quarantined_wrapper(label: str) -> str:
    fair_housing_guard = ""
    if label == "town report page":
        fair_housing_guard = '''
# Preserve the integrated English fair-housing quarantine inventory as an
# explicit secondary guard. This entry point is fully retired below, but
# keeping the exact owned-output set here makes that protection auditable.
QUARANTINE_MANIFEST = Path(__file__).resolve().parent / "data" / "english-fair-housing-quarantine.json"
QUARANTINED_OUTPUTS = frozenset(
    Path(item["file"]).name
    for item in json.loads(QUARANTINE_MANIFEST.read_text(encoding="utf-8"))["pages"]
)


def is_quarantined_output(filename: str) -> bool:
    if filename in QUARANTINED_OUTPUTS:
        return True
    return False
'''
    return f'''#!/usr/bin/env python3
"""Retired entry point retained only to fail closed."""

import json
from pathlib import Path

from tools.market_report_publication_gate import quarantined_generator_main

{fair_housing_guard}

if __name__ == "__main__":
    raise SystemExit(quarantined_generator_main({label!r}))
'''


def synchronize(*, write: bool, root: Path = ROOT) -> tuple[int, list[str]]:
    inventory = load_inventory(root / "data" / "market-report-containment.json")
    pages = rendered_pages(inventory, root=root)
    drift: list[str] = []
    for path, expected in pages.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == expected:
            continue
        drift.append(path.relative_to(root).as_posix())
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    routes = contained_routes(inventory)
    managed = set(pages)
    rebuild_pages = _rebuild_page_paths(inventory, root)

    vercel_path = root / "vercel.json"
    current_vercel = vercel_path.read_text(encoding="utf-8")
    expected_vercel = _ensure_vercel_redirects(current_vercel, inventory)
    if current_vercel != expected_vercel:
        drift.append("vercel.json")
        if write:
            vercel_path.write_text(expected_vercel, encoding="utf-8")

    for relative, label in QUARANTINED_GENERATORS.items():
        path = root / relative
        current = path.read_text(encoding="utf-8") if path.exists() else None
        expected = _quarantined_wrapper(label)
        if current != expected:
            drift.append(relative)
            if write:
                path.write_text(expected, encoding="utf-8")

    for name in ("sitemap.xml", "sitemap-es.xml"):
        path = root / name
        current = path.read_text(encoding="utf-8")
        expected = _clean_sitemap(current, routes)
        if current != expected:
            drift.append(name)
            if write:
                path.write_text(expected, encoding="utf-8")

    for path in root.rglob("*.html"):
        if path in managed or any(part in SKIP_DIRS for part in path.parts):
            continue
        current = path.read_text(encoding="utf-8")
        if not _is_indexable_html(current):
            continue
        if not any(route in current for route in routes):
            continue
        expected = _clean_indexable_html(current, routes)
        if current == expected:
            continue
        relative = path.relative_to(root).as_posix()
        if path in rebuild_pages:
            raise RuntimeError(
                f"contained link found inside protected later-rebuild page: {relative}"
            )
        drift.append(relative)
        if write:
            path.write_text(expected, encoding="utf-8")
    return len(drift), drift


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    count, drift = synchronize(write=args.write)
    if args.check and count:
        print("Market-report containment drift:")
        for relative in drift:
            print(f"- {relative}")
        return 1
    if args.write:
        print(f"Updated {count} market-report containment artifacts.")
    else:
        print("44 market-report containment fallbacks are current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
