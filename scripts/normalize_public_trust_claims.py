#!/usr/bin/env python3
"""Remove unsupported service-area totals and agent superlatives from public copy.

This is deliberately a text-only migration. It does not parse or reserialize HTML,
so page structure, classes, inline styles, and JSON-LD formatting remain intact.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TEXT_FILES = (
    "api/lead.js",
    "build_communities_page.py",
    "bulk_update_towns.py",
    "fix_site_issues_v2.py",
    "gen_serp_pages.py",
    "generate_blog.py",
    "generate_county_reports_and_comparisons.py",
    "generate_new_landing_pages.py",
    "generate_somerset_towns.py",
    "index.html.backup",
    "js/communities-data.js",
    "js/main.js",
    "llms.txt",
    "llms-full.txt",
    "llms-es.txt",
    "optimize_seo.py",
    "schema-realtor.json",
    "manifest.json",
    "site.webmanifest",
)


def retired_legacy_html() -> set[str]:
    """Return immutable fallback files from the retired scaled-content cluster."""
    manifest = ROOT / "data" / "retired-legacy-daily-posts.json"
    if not manifest.exists():
        return set()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    return {
        str(item["file"])
        for item in payload.get("pages", [])
        if isinstance(item, dict) and item.get("file")
    }


RETIRED_LEGACY_HTML = retired_legacy_html()


REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Avoid turning "all 138 communities" into the overbroad "all communities."
    (
        re.compile(
            r"(<(?:p|h[1-6]|li|dt|dd|th|td|label|legend|button)\b[^>]*>)"
            r"(\s*)all\s+(?:103|109|120|138)\s+"
            r"(?:(?:NJ|New Jersey)\s+)?communities\b",
            re.I,
        ),
        r"\1\2Communities across six New Jersey counties",
    ),
    (
        re.compile(r"\ball\s+(?:103|109|120|138)\s+(?:(?:NJ|New Jersey)\s+)?communities\b", re.I),
        "communities across six New Jersey counties",
    ),
    (
        re.compile(r"\ball\s+(?:103|109|120|138)\s+(?:(?:NJ|New Jersey)\s+)?towns\b", re.I),
        "towns across six New Jersey counties",
    ),
    (
        re.compile(
            r"(<(?:p|h[1-6]|li|dt|dd|th|td|label|legend|button)\b[^>]*>)"
            r"(\s*)todas?\s+las\s+(?:103|109|120|138)\s+comunidades\b",
            re.I,
        ),
        r"\1\2Comunidades en seis condados de Nueva Jersey",
    ),
    (
        re.compile(r"\btodas?\s+las\s+(?:103|109|120|138)\s+comunidades\b", re.I),
        "comunidades en seis condados de Nueva Jersey",
    ),
    # Service scope is intentionally nonnumeric. The separate 121-guide directory
    # count is verified inventory data and is not matched by these rules.
    # Removed numeric claims at sentence or form/control-label starts need an
    # initial capital. Inline links and generic styling wrappers retain prose
    # casing, so they intentionally fall through to the lowercase rule below.
    (
        re.compile(
            r"(<(?:p|h[1-6]|li|dt|dd|th|td|label|legend|button)\b[^>]*>)"
            r"(\s*)(?:103|109|120|138)\s+(?:NJ\s+|New Jersey\s+)?communities\b",
            re.I,
        ),
        r"\1\2Communities",
    ),
    (
        re.compile(r"\b(?:103|109|120|138)\s+(?:NJ\s+|New Jersey\s+)?communities\b", re.I),
        "communities",
    ),
    (
        re.compile(r"\b(?:103|109|120|138)\s+(?:NJ\s+|New Jersey\s+)?towns\b", re.I),
        "NJ towns",
    ),
    # Apply the same structural treatment to Spanish numeric claims.
    (
        re.compile(
            r"(<(?:p|h[1-6]|li|dt|dd|th|td|label|legend|button)\b[^>]*>)"
            r"(\s*)(?:103|109|120|138)\s+comunidades\b",
            re.I,
        ),
        r"\1\2Comunidades",
    ),
    (re.compile(r"\b(?:103|109|120|138)\s+comunidades\b", re.I), "comunidades"),
    (re.compile(r"\b(?:103|109|120|138)\s+pueblos\b", re.I), "municipios"),
    # Generated English agent and group descriptions.
    (
        re.compile(r"\btop[- ]rated\s+NJ\s+real estate agent\b", re.I),
        "licensed NJ real estate agent",
    ),
    (
        re.compile(r"\btop[- ]rated\s+real estate agent\b", re.I),
        "licensed NJ real estate agent",
    ),
    (
        re.compile(r"\btop[- ]rated\s+real estate agency\b", re.I),
        "real estate group led by licensed NJ real estate agent Jorge Ramirez",
    ),
    (
        re.compile(r"\bTop\s+([A-Z][A-Za-z -]+ County)\s+real estate agent Jorge Ramirez\b"),
        r"Licensed NJ real estate agent Jorge Ramirez serving \1",
    ),
    (
        re.compile(r"\bTop\s+([A-Z][A-Za-z -]+ County)\s+NJ\s+realtor\b"),
        r"Licensed NJ Realtor serving \1",
    ),
    (
        re.compile(
            r"Expert pricing strategy, market insights, and proven marketing from "
            r"(?:top local realtor|local NJ real estate agent) Jorge Ramirez\.",
            re.I,
        ),
        "Pricing guidance and local market insights from licensed NJ real estate agent Jorge Ramirez.",
    ),
    (
        re.compile(r"\bJorge Ramirez is a top\s+([A-Z][A-Za-z -]+ County)\s+NJ\s+realtor\b", re.I),
        r"Jorge Ramirez is a licensed NJ Realtor serving \1",
    ),
    (re.compile(r"\bTop NJ real estate agent\b"), "Licensed NJ real estate agent"),
    (
        re.compile(r"\btop\s+local\s+realtor\s+Jorge Ramirez\b", re.I),
        "local NJ real estate agent Jorge Ramirez",
    ),
    (
        re.compile(r"\btop\s+real estate agent\s+in\s+Chatham,?\s+NJ\b", re.I),
        "licensed NJ real estate agent serving Chatham",
    ),
    (
        re.compile(r"\btop\s+realtor\s+Chatham\s+NJ\b", re.I),
        "licensed realtor Chatham NJ",
    ),
    (
        re.compile(r"\bTop Realtor\s*\|\s*Jorge Ramirez\b"),
        "Licensed Realtor | Jorge Ramirez",
    ),
    # FAQ questions must not frame the named agent as the answer to an
    # unsupported "best agent" query. The replacement remains a useful,
    # factual service-area question in both visible copy and JSON-LD.
    (
        re.compile(
            r"\bWho is the best (?:real estate )?(?:agent|Realtor) in "
            r"([^?<\"\n]+)\?",
            re.I,
        ),
        r"Does Jorge Ramirez serve \1?",
    ),
    # Direct English self-ranking phrases in titles, social metadata, and alt text.
    (re.compile(r"\bThe Best NJ Real Estate Agent\b", re.I), "Licensed NJ Real Estate Agent"),
    (re.compile(r"\bBest NJ Real Estate Agent\b", re.I), "Licensed NJ Real Estate Agent"),
    (re.compile(r"\bBest Agent in NJ\b", re.I), "Licensed Agent in NJ"),
    (re.compile(r"\bBest Realtor in NJ for Sellers and Buyers\b"), "Licensed NJ Realtor for Sellers and Buyers"),
    (re.compile(r"\bBest Realtor in NJ\b"), "Licensed NJ Realtor"),
    (re.compile(r"\bTop NJ Realtor\b"), "Licensed NJ Realtor"),
    (re.compile(r"\bTop NJ Real Estate Agent and Investor\b"), "Licensed NJ Real Estate Agent and Investor"),
    (re.compile(r"\bbest realtor NJ\b", re.I), "licensed NJ realtor"),
    (re.compile(r"\bbest NJ real estate agent\b", re.I), "licensed NJ real estate agent"),
    (re.compile(r"\btop real estate agent New Jersey\b", re.I), "licensed NJ real estate agent"),
    (re.compile(r"\bbest listing agent NJ\b", re.I), "NJ listing agent"),
    (re.compile(r"\btop NJ realtor\b", re.I), "licensed NJ realtor"),
    (re.compile(r"\bbest real estate agent Essex County\b", re.I), "Essex County real estate agent"),
    (re.compile(r"\bbest realtor Union County\b", re.I), "Union County realtor"),
    (
        re.compile(r"I'm Not Going to Tell You I'm the Licensed Agent in NJ", re.I),
        "I'm Not Going to Ask You to Take My Word for It",
    ),
    # Spanish generated descriptions use both normal and inverted word order.
    (
        re.compile(r"\bagente\s+de\s+bienes\s+ra[ií]ces\s+mejor\s+calificad[oa]\b", re.I),
        "agente de bienes raíces con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bmejor\s+calificad[oa]\s+agente\s+de\s+bienes\s+ra[ií]ces\b", re.I),
        "agente de bienes raíces con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bagencia\s+de\s+bienes\s+ra[ií]ces\s+mejor\s+calificad[oa]\b", re.I),
        "grupo inmobiliario dirigido por Jorge Ramirez, agente con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bagente\s+inmobiliario\s+mejor\s+calificad[oa]\b", re.I),
        "agente inmobiliario con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bagente\s+de\s+bienes\s+ra[ií]ces\s+de\s+primer\s+nivel\b", re.I),
        "agente de bienes raíces con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bagencia\s+de\s+bienes\s+ra[ií]ces\s+de\s+primer\s+nivel\b", re.I),
        "grupo inmobiliario dirigido por Jorge Ramirez, agente con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bagente\s+de\s+bienes\s+ra[ií]ces\s+l[ií]der\b", re.I),
        "agente de bienes raíces con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bdestacad[oa]\s+agente\s+de\s+listado\b", re.I),
        "agente de listado con licencia en Nueva Jersey",
    ),
    (
        re.compile(
            r"Estrategia de precios experta, análisis del mercado y marketing comprobado del "
            r"(?:destacado agente|agente con licencia)\.",
            re.I,
        ),
        "Orientación de precios y análisis local de un agente con licencia en Nueva Jersey.",
    ),
    (
        re.compile(r"\bdestacad[oa]\s+agente\s+inmobiliario\s+local\b", re.I),
        "agente inmobiliario local con licencia",
    ),
    (
        re.compile(r"\bequipo\s+de\s+bienes\s+ra[ií]ces\s+l[ií]der\b", re.I),
        "grupo de bienes raíces",
    ),
    (
        re.compile(r"\bmejores\s+agentes\s+de\s+listados\b", re.I),
        "agentes de listados establecidos",
    ),
    (
        re.compile(r"\bred\s+de\s+mejores\s+agentes\b", re.I),
        "red de agentes",
    ),
    (
        re.compile(r"\bes\s+calificad[oa]\s+consistentemente\s+como\s+uno\s+de\s+los\s+mejores\s+agentes\s+de\s+bienes\s+ra[ií]ces\b", re.I),
        "es un agente de bienes raíces con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\buno\s+de\s+los\s+mejores\s+agentes\s+de\s+bienes\s+ra[ií]ces\b", re.I),
        "un agente de bienes raíces con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bmejor\s+agente\s+de\s+bienes\s+ra[ií]ces\b", re.I),
        "agente de bienes raíces con licencia",
    ),
    (
        re.compile(r"\bmejor\s+agente\s+inmobiliario\b", re.I),
        "agente inmobiliario con licencia",
    ),
    (re.compile(r"\bmejor\s+agente\b", re.I), "agente con licencia"),
    (re.compile(r"\bmejor\s+Realtor\b", re.I), "Realtor con licencia"),
    (
        re.compile(r"\bdestacad[oa]\s+agente\s+inmobiliari[oa]\b", re.I),
        "agente inmobiliario local con licencia",
    ),
    (re.compile(r"\bdestacad[oa]\s+agente\b", re.I), "agente con licencia"),
    (
        re.compile(r"\bagente\s+inmobiliari[oa]\s+de\s+primer\s+nivel\b", re.I),
        "agente inmobiliario con licencia en Nueva Jersey",
    ),
    (
        re.compile(r"\bagente\s+inmobiliari[oa]\s+destacad[oa]\b", re.I),
        "agente inmobiliario con licencia en Nueva Jersey",
    ),
    (re.compile(r"\buna\s+grupo\s+inmobiliario\b", re.I), "un grupo inmobiliario"),
    # The factual Spanish replacement is longer than the original superlative.
    # Keep generated town snippets within search-result limits without touching
    # descriptions that did not contain the unsupported claim.
    (
        re.compile(
            r'<meta name="description" content="¿(Buscas|Quieres) comprar o vender '
            r'(una )?casa en ([^\"?]+), NJ\? Jorge Ramirez\s*[—,]\s*(?:el\s+)?'
            r'agente de bienes raíces con licencia en Nueva Jersey\s+(?:del|en el)\s+'
            r'Condado de ([^\"]+?)\s+(?:en|con)\s+Keller Williams\.?">',
            re.I,
        ),
        r'<meta name="description" content="¿\1 comprar o vender \2casa en \3, NJ? '
        r'Jorge Ramirez es agente con licencia en NJ y atiende \3 y el Condado de \4.">',
    ),
    # Direct network/ranking assertions on the luxury and agent pages.
    (
        re.compile(r"Jorge's network includes top listing agents", re.I),
        "Jorge's network includes established listing agents",
    ),
    (re.compile(r"Jorge's top-agent network", re.I), "Jorge's agent network"),
    (
        re.compile(
            r"Jorge Ramirez of The Jorge Ramirez Group at Keller Williams Premier "
            r"Properties in Summit, NJ is consistently rated as one of NJ's top "
            r"real estate agents\."
        ),
        "Jorge Ramirez of The Jorge Ramirez Group at Keller Williams Premier "
        "Properties in Summit, NJ is a licensed NJ real estate agent.",
    ),
    # Nonnumeric and non-categorical service-area language.
    (
        re.compile(r"\bserves\s+(?:all\s+)?(?:the\s+)?\d+\s+(?:NJ\s+)?(?:towns|communities)\b", re.I),
        "serves communities",
    ),
    (
        re.compile(r"\bserves\s+all\s+\d+\s+([A-Z][A-Za-z -]+ County)\s+(?:towns|communities)\b", re.I),
        r"serves communities throughout \1",
    ),
    (
        re.compile(r"\bserving\s+(?:all\s+)?(?:the\s+)?\d+\s+(?:NJ\s+)?(?:towns|communities)\b", re.I),
        "serving communities",
    ),
    (
        re.compile(r"\b(serves|serving)\s+(?:all\s+)?\d+\s+([A-Z][A-Za-z -]+ County)\s+(?:towns|communities)\b", re.I),
        r"\1 communities throughout \2",
    ),
    (
        re.compile(r"\b(serves|serving)\s+(?:all\s+)?\d+\s+([A-Z][A-Za-z -]+ County)\s+NJ\s+(?:towns|communities)\b", re.I),
        r"\1 communities throughout \2",
    ),
    (
        re.compile(r"\b\d+\s+(?:NJ\s+)?(?:towns|communities)\s+served\b", re.I),
        "communities served",
    ),
    (
        re.compile(r"\b\d+\s+([A-Z][A-Za-z -]+ County)\s+(?:towns|communities)\s+served\b", re.I),
        r"\1 community guides",
    ),
    (
        re.compile(r"\bserves\s+all\s+of\s+Northern\s+and\s+Central\s+New Jersey\b", re.I),
        "works with buyers and sellers across six New Jersey counties",
    ),
    (re.compile(r"\bknows\s+every\s+block\b", re.I), "brings local market knowledge"),
    (
        re.compile(r"\bserves\s+every\s+community\s+in\s+([A-Z][A-Za-z -]+ County)\b", re.I),
        r"works with clients in communities throughout \1",
    ),
    (
        re.compile(r"\bserves\s+every\s+([A-Z][A-Za-z -]+ County)\s+community\b", re.I),
        r"works with clients in communities throughout \1",
    ),
    (
        re.compile(r"\bcovers\s+every\s+([A-Z][A-Za-z -]+ County)\s+town\b", re.I),
        r"works across \1",
    ),
    (
        re.compile(r"\bcovers\s+every\s+([A-Z][A-Za-z-]+)\s+town\b", re.I),
        r"works across \1 County",
    ),
    (
        re.compile(r"\batiende\s+(?:a\s+)?(?:(?:todos?|todas?)\s+)?(?:(?:los|las)\s+)?\d+\s+(?:pueblos|comunidades|municipios)\b", re.I),
        "atiende comunidades",
    ),
    (
        re.compile(r"\batendiendo\s+(?:a\s+)?(?:(?:todos?|todas?)\s+)?(?:(?:los|las)\s+)?\d+\s+(?:pueblos|comunidades|municipios)\b", re.I),
        "atendiendo comunidades",
    ),
    (
        re.compile(r"\b\d+\s+(?:pueblos|comunidades|municipios)\s+(?:atendidos?|atendidas?)\b", re.I),
        "comunidades atendidas",
    ),
    (
        re.compile(r"\b\d+\s+(?:pueblos|comunidades|municipios)\s+del\s+(Condado de [A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+)\s+(?:atendidos?|atendidas?)\b", re.I),
        r"Guías de comunidades del \1",
    ),
    (
        re.compile(r"\b\d+\s+(?:pueblos|comunidades|municipios)\s+de\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+) County\s+(?:atendidos?|atendidas?)\b", re.I),
        r"Guías de comunidades del Condado de \1",
    ),
    (
        re.compile(r"\batiende\s+(?:a\s+)?todas?\s+las\s+comunidades\b", re.I),
        "atiende comunidades",
    ),
    (re.compile(r"\batiende\s+los\s+pueblos\s+del\s+condado\b", re.I), "atiende comunidades del condado"),
    (
        re.compile(r"\bcubre\s+cada\s+pueblo\b", re.I),
        "trabaja en comunidades",
    ),
    (
        re.compile(r"\batiende\s+cada\s+comunidad\s+del\s+(Condado de [A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+)\b", re.I),
        r"trabaja con clientes en comunidades del \1",
    ),
    (re.compile(r"\bcovers every town I work in\b", re.I), "includes guides for towns where I work"),
    (re.compile(r"\bconoce\s+cada\s+cuadra\b", re.I), "aporta conocimiento del mercado local"),
    (re.compile(r"\bconozco\s+cada\s+calle\b", re.I), "conozco las tendencias locales"),
    (
        re.compile(r"\bwork exclusively in this market and know every street\b", re.I),
        "work actively in this market and track local market trends",
    ),
    (
        re.compile(r"\bI know every street\b", re.I),
        "I track local market trends",
    ),
    (
        re.compile(r"\bknows every street\b", re.I),
        "tracks local market trends",
    ),
    (
        re.compile(r"\bcommunities page covers every town I work in\b", re.I),
        "communities page includes guides for towns where I work",
    ),
    (
        re.compile(r"\bha\s+ayudado\s+a\s+compradores\s+y\s+vendedores\s+en\s+todos\s+los\s+pueblos\b", re.I),
        "ha ayudado a compradores y vendedores en comunidades",
    ),
    (
        re.compile(
            r"\bha estado en ambos lados de la mesa\s*[—-]\s*como inversionista, comprador, vendedor y agente\s*[—-]\s*cientos de veces\b",
            re.I,
        ),
        "ha trabajado desde distintos roles — como inversionista, comprador, vendedor y agente",
    ),
    # Unsupported client-volume, tenure, development, return, and inventory copy.
    (re.compile(r"\bI(?:'|’)?ve helped hundreds of families\b", re.I), "I've helped buyers and sellers"),
    (re.compile(r"\bI have helped hundreds of families\b", re.I), "I have helped buyers and sellers"),
    (re.compile(r"\bJorge has helped hundreds of families\b", re.I), "Jorge has helped buyers and sellers"),
    (re.compile(r"\bhelped hundreds of families\b", re.I), "helped buyers and sellers"),
    (re.compile(r"\byears?\s+(?:of\s+)?helping\s+families\b", re.I), "experience helping buyers and sellers"),
    (
        re.compile(r"\byears?\s+of\s+helping\s+(?:New Jersey|NJ)\s+families\b", re.I),
        "experience helping New Jersey buyers and sellers",
    ),
    (re.compile(r"\bhe ayudado a cientos de familias\b", re.I), "he ayudado a compradores y vendedores"),
    (re.compile(r"\bha ayudado a cientos de familias\b", re.I), "ha ayudado a compradores y vendedores"),
    (re.compile(r"\bhan ayudado a cientos de familias\b", re.I), "han ayudado a compradores y vendedores"),
    (
        re.compile(r"\bdespu[eé]s de m[aá]s de \d+ a[ñn]os ayudando a familias\b", re.I),
        "con experiencia ayudando a compradores y vendedores",
    ),
    (
        re.compile(r"\blleva a[ñn]os ayudando a familias\b", re.I),
        "tiene experiencia ayudando a compradores y vendedores",
    ),
    (re.compile(r"\ba[ñn]os ayudando a familias\b", re.I), "experiencia ayudando a compradores y vendedores"),
    (re.compile(r"\bactive development pipeline\b", re.I), "new-construction activity that should be verified with current local records"),
    (
        re.compile(r"\bcartera activa de desarrollo\b", re.I),
        "actividad de construcción nueva que debe verificarse con registros locales actuales",
    ),
    (
        re.compile(r"\bhistorical appreciation demonstrates reliable returns\b", re.I),
        "Past appreciation does not guarantee future returns",
    ),
    (
        re.compile(r"\bla apreciaci[oó]n hist[oó]rica demuestra rendimientos confiables\b", re.I),
        "La apreciación pasada no garantiza rendimientos futuros",
    ),
    (re.compile(r"\bmaintains healthy inventory levels\b", re.I), "has inventory that changes with market activity"),
    (re.compile(r"\bhealthy inventory levels?\b", re.I), "inventory levels that change with market activity"),
    (
        re.compile(r"\bmantiene niveles? de inventario saludables?\b", re.I),
        "tiene un inventario que cambia con la actividad del mercado",
    ),
    (
        re.compile(r"\bniveles? de inventario saludables?\b", re.I),
        "niveles de inventario que cambian con la actividad del mercado",
    ),
    # Neutral school language where no dated source supports a categorical rank.
    (
        re.compile(r"\b(?:strong|top(?:[- ]rated|[- ]tier)?)\s+school(?:-| )districts?\b", re.I),
        "local school districts",
    ),
    (re.compile(r"\b(?:strong|top(?:[- ]rated|[- ]tier)?)\s+public schools\b", re.I), "local public schools"),
    (re.compile(r"\b(?:strong|top(?:[- ]rated|[- ]tier)?)\s+school systems?\b", re.I), "local school systems"),
    (re.compile(r"\b(?:strong|top(?:[- ]rated|[- ]tier)?)\s+schools\b", re.I), "local schools"),
    (re.compile(r"\btop(?:[- ]tier)?\s+school towns?\b", re.I), "towns with local schools"),
    (
        re.compile(r"\bdistritos? escolares? (?:mejor(?:es)? calificados?|de primer nivel)\b", re.I),
        "distritos escolares locales",
    ),
    (
        re.compile(r"\bescuelas? (?:s[oó]lidas?|fuertes?|de primer nivel|mejor(?:es)? calificadas?)\b", re.I),
        "escuelas locales",
    ),
    (
        re.compile(r"\bdistritos? escolares? (?:s[oó]lidos?|fuertes?)\b", re.I),
        "distritos escolares locales",
    ),
    (
        re.compile(r"\bescuelas? p[uú]blicas? (?:s[oó]lidas?|fuertes?)\b", re.I),
        "escuelas públicas locales",
    ),
    # Repair sentence/title casing after safe phrase substitutions.
    (re.compile(r'content="licensed\b'), 'content="Licensed'),
    (re.compile(r'"description":\s*"licensed\b'), '"description": "Licensed'),
    (re.compile(r'content="agente\b'), 'content="Agente'),
    (re.compile(r"\.\s+serving communities\b"), ". Serving communities"),
    (re.compile(r"\.\s+communities served\b"), ". Communities served"),
    (re.compile(r"\.\s+atiende comunidades\b"), ". Atiende comunidades"),
    (re.compile(r"\bcommunities mastered\b", re.I), "experience across local markets"),
    (re.compile(r"\bcomunidades dominadas\b", re.I), "experiencia en mercados locales"),
    (
        re.compile(r"\bDeep Local Knowledge Across communities\b", re.I),
        "Deep Local Knowledge Across Six New Jersey Counties",
    ),
    (
        re.compile(r"\bProfundo Conocimiento Local en comunidades\b", re.I),
        "Profundo Conocimiento Local en Seis Condados de Nueva Jersey",
    ),
    (
        re.compile(r"\bHow many communities does Jorge Ramirez serve(?: in NJ)?\?", re.I),
        "Where does Jorge Ramirez serve clients in NJ?",
    ),
    (
        re.compile(r"¿A cu[aá]ntas comunidades atiende Jorge Ramirez\?", re.I),
        "¿Dónde atiende Jorge Ramirez a sus clientes en Nueva Jersey?",
    ),
    (
        re.compile(r"\bacross communities across six New Jersey counties he serves\b", re.I),
        "across the six New Jersey counties where he works",
    ),
    (re.compile(r"\bexpertise across communities\b", re.I), "experience across six NJ counties"),
    (
        re.compile(r"Why Jorge Ramirez Is New Jersey's licensed NJ real estate agent", re.I),
        "Why Clients Work with Licensed NJ Real Estate Agent Jorge Ramirez",
    ),
    (
        re.compile(r"\bReal Estate Agent Directory — NJ towns\b", re.I),
        "Real Estate Agent Directory — Six NJ Counties",
    ),
    (re.compile(r"\bNew Jersey has NJ towns worth considering\b", re.I), "New Jersey has communities worth considering"),
    (
        re.compile(r"Licensed NJ real estate agent Jorge Ramirez serving ([A-Z][A-Za-z -]+ County) serves communities", re.I),
        r"Licensed NJ real estate agent Jorge Ramirez serves communities in \1",
    ),
    (
        re.compile(r"Licensed NJ real estate agent Jorge Ramirez serves communities in ([A-Z][A-Za-z -]+ County) including", re.I),
        r"Licensed NJ real estate agent Jorge Ramirez serves communities in \1, including",
    ),
    (
        re.compile(r"\bJorge Ramirez serves \d+ ([A-Z][A-Za-z -]+ County) NJ towns including\b", re.I),
        r"Jorge Ramirez serves communities in \1, including",
    ),
    (
        re.compile(r"Licensed NJ Realtor serving ([A-Z][A-Za-z -]+ County) serving (?:communities )?including", re.I),
        r"Licensed NJ Realtor serving communities in \1, including",
    ),
    (
        re.compile(r"Jorge Ramirez, agente inmobiliario con licencia en Nueva Jersey del (Condado de [A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+), atiende comunidades", re.I),
        r"Jorge Ramirez, agente inmobiliario con licencia en Nueva Jersey, atiende comunidades del \1",
    ),
    (
        re.compile(r"Jorge Ramirez, agente inmobiliario con licencia en Nueva Jersey, atiende comunidades del", re.I),
        "Jorge Ramirez, agente con licencia en NJ, atiende comunidades del",
    ),
    (
        re.compile(r"atiende comunidades del (Condado de [A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+) NJ incluyendo", re.I),
        r"atiende comunidades del \1, incluyendo",
    ),
    (
        re.compile(r"atiende comunidades del (Condado de [A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+) incluyendo", re.I),
        r"atiende comunidades del \1, incluyendo",
    ),
    (
        re.compile(r"Agente inmobiliario con licencia en Nueva Jersey del (Condado de [A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]+) NJ atendiendo", re.I),
        r"Agente inmobiliario con licencia en Nueva Jersey que atiende comunidades del \1, incluyendo",
    ),
    (re.compile(r"\bincluyendo comunidades incluyendo\b", re.I), "incluyendo"),
    (re.compile(r"\by \d+ pueblos más\b", re.I), "y otras comunidades cercanas"),
    (re.compile(r"\band \d+ more towns\b", re.I), "and nearby communities"),
    (re.compile(r"\bBuying a home in New Jersey across NJ towns\b", re.I), "Buying a home across six New Jersey counties"),
    (re.compile(r"\blicensed NJ real estate agent He uses\b"), "licensed NJ real estate agent. He uses"),
    (
        re.compile(r"\bagente de bienes raíces con licencia en Nueva Jersey en NJ\b", re.I),
        "agente de bienes raíces con licencia en Nueva Jersey",
    ),
)


SPANISH_COMMUNITY_HUB_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"<title>.*?</title>", re.I | re.S),
        "<title>Guías de Comunidades en Seis Condados de NJ | Jorge Ramirez</title>",
    ),
    (
        re.compile(r'<meta name="description" content="[^"]*">', re.I),
        '<meta name="description" content="Explora guías de comunidades en los condados de Union, Essex, Morris, Hudson, Middlesex y Somerset, con vivienda, transporte y recursos locales.">',
    ),
    (
        re.compile(r'<meta name="llm-context" content="[^"]*">', re.I),
        '<meta name="llm-context" content="Directorio en español de guías de comunidades publicadas para seis condados de Nueva Jersey: Union, Essex, Morris, Hudson, Middlesex y Somerset. Cada entrada enlaza a una guía local con información sobre vivienda, transporte y escuelas que debe verificarse con fuentes actuales. Jorge Ramirez es agente inmobiliario con licencia de Nueva Jersey #1754604 en Keller Williams Premier Properties.">',
    ),
    (
        re.compile(r'<meta property="og:title" content="[^"]*">', re.I),
        '<meta property="og:title" content="Guías de Comunidades en Seis Condados de NJ | Jorge Ramirez">',
    ),
    (
        re.compile(r'<meta name="twitter:title" content="[^"]*">', re.I),
        '<meta name="twitter:title" content="Guías de Comunidades en Seis Condados de NJ | Jorge Ramirez">',
    ),
    (
        re.compile(r'"name": "NJ Communities Served by The Jorge Ramirez Group"'),
        '"name": "Guías de Comunidades de Nueva Jersey"',
    ),
    (
        re.compile(r'"description": "Complete list of communities served by Jorge Ramirez[^\n]*"'),
        '"description": "Directorio de guías de comunidades en los condados de Union, Essex, Morris, Hudson, Middlesex y Somerset, con información local para compradores y vendedores."',
    ),
    (
        re.compile(r"<h1>Comunidades de NJ que Atendemos</h1>", re.I),
        "<h1>Guías de Comunidades en Seis Condados de NJ</h1>",
    ),
)


FILE_REPLACEMENTS: dict[str, tuple[tuple[re.Pattern[str], str], ...]] = {
    "index.html.backup": (
        (
            re.compile(r"Jorge Ramirez \| Top Real Estate Agent in Northern & Central NJ", re.I),
            "Jorge Ramirez | Licensed Real Estate Agent in Northern & Central NJ",
        ),
        (
            re.compile(r"Jorge Ramirez is a top New Jersey real estate agent", re.I),
            "Jorge Ramirez is a licensed New Jersey real estate agent",
        ),
        (
            re.compile(r"Jorge Ramirez - Top Real Estate Agent in Union, Essex, Morris County NJ", re.I),
            "Jorge Ramirez - Licensed Real Estate Agent Serving Union, Essex, and Morris Counties",
        ),
    ),
    "why-jorge-ramirez.html": (
        (
            re.compile(r'<div class="number">103</div>\s*<div class="label">NJ Communities Served</div>'),
            '<div class="number">NJ</div>\n                <div class="label">Licensed Agent</div>',
        ),
        (re.compile(r"\b(?:11|12|21|22|37) communities including\b", re.I), "Communities including"),
        (re.compile(r"\b((?:Essex|Hudson|Morris|Middlesex|Union) County) \(\d+ towns\)"), r"\1"),
        (re.compile(r"AI-powered marketing, communities,"), "AI-powered marketing, experience across six NJ counties,"),
        (re.compile(r"AI-powered marketing\. communities\."), "AI-powered marketing. Experience across six NJ counties."),
    ),
    "es/why-jorge-ramirez.html": (
        (
            re.compile(r'<div class="number">103</div>\s*<div class="label">Comunidades de NJ Atendidas</div>'),
            '<div class="number">NJ</div>\n                <div class="label">Agente con Licencia</div>',
        ),
        (re.compile(r"\b(?:11|12|21|22|37) comunidades incluyendo\b", re.I), "Comunidades incluyendo"),
        (re.compile(r"\b(Condado de (?:Essex|Hudson|Morris|Middlesex|Union)) \(\d+ pueblos\)"), r"\1"),
        (re.compile(r"Marketing con IA, comunidades,"), "Marketing con IA, experiencia en seis condados de NJ,"),
        (re.compile(r"Marketing con IA\. comunidades(?: en NJ)?\."), "Marketing con IA. Experiencia en seis condados de NJ."),
        (
            re.compile(r"<title>Por Qué Elegir a Jorge Ramirez \| agente inmobiliario con licencia en NJ</title>", re.I),
            "<title>Por Qué Elegir a Jorge Ramirez | Agente con Licencia en NJ</title>",
        ),
        (
            re.compile(r'<meta name="description" content="Jorge Ramirez no es solo un agente — es un inversionista que ha renovado casas en NJ\. Marketing con IA, experiencia en seis condados de NJ, disponibilidad los 7 días de la semana\.">', re.I),
            '<meta name="description" content="Jorge Ramirez es un agente con licencia en NJ e inversionista con experiencia práctica en renovaciones y servicio en seis condados.">',
        ),
    ),
    "es/index.html": (
        # The Spanish homepage used to carry a second, hidden FAQ answer set and
        # several fixed outcome/cost claims. Keep this migration path-specific:
        # these expressions intentionally do not rewrite other public pages.
        (
            re.compile(
                r'\s*<script\b(?=[^>]*\btype=["\']application/ld\+json["\'])[^>]*>'
                r'(?:(?!</script>).)*?"@type"\s*:\s*"FAQPage"'
                r'(?:(?!</script>).)*?</script>\s*',
                re.I | re.S,
            ),
            "\n    <!-- Structured FAQ rich-result markup is intentionally omitted. -->\n",
        ),
        (
            re.compile(
                r'<meta name="llm-context" content="[^"]*\b(?:inversionista|inversi[oó]n|mejor precio)[^"]*">',
                re.I,
            ),
            '<meta name="llm-context" content="Jorge Ramirez es un agente inmobiliario con licencia en Nueva Jersey (Licencia #1754604) en Keller Williams Premier Properties, con sede en Summit. Trabaja con compradores y vendedores en los condados de Essex, Hudson, Morris, Middlesex, Union y Somerset. Su proceso usa información actual de la propiedad y ventas comparables, explica las alternativas y no garantiza un precio ni un resultado. Solicitud de valoración en español: https://thejorgeramirezgroup.com/es/home-valuation. Contacto: 908-230-7844.">',
        ),
        (
            re.compile(
                r'<p(?P<attrs>[^>]*)>(?:(?!</p>).)*?'
                r'(?:personalmente\s+he\s+comprado|\binversionista\b)'
                r'(?:(?!</p>).)*?</p>',
                re.I | re.S,
            ),
            '<p\g<attrs>>Jorge es un agente inmobiliario con licencia en Nueva Jersey en Keller Williams Premier Properties, con sede en Summit.</p>',
        ),
        (
            re.compile(
                r'<div class="credential-item">[^<]*(?:inversionista|inversi[oó]n|renovaci[oó]n|7\s+d[ií]as)[^<]*</div>',
                re.I,
            ),
            '<div class="credential-item">✓ Licencia de Bienes Raíces de NJ #1754604</div>',
        ),
        (
            re.compile(r'<p(?P<attrs>[^>]*)>[^<]*(?:trabajo|disponible)\s+los\s+7\s+d[ií]as[^<]*</p>', re.I),
            '<p\g<attrs>>Con sede en Summit, Nueva Jersey.</p>',
        ),
        (
            re.compile(r'<p(?P<attrs>[^>]*)>\s*Respuesta\s+r[aá]pida\s+garantizada\s*</p>', re.I),
            '<p\g<attrs>>Licencia de NJ #1754604</p>',
        ),
        (
            re.compile(
                r'<div class="stat-card">\s*<span class="stat-number"[^>]*>7</span>\s*'
                r'<span class="stat-label">D[ií]as a la Semana</span>\s*</div>',
                re.I,
            ),
            '<div class="stat-card">\n                <span class="stat-number">#1754604</span>\n                <span class="stat-label">Licencia de NJ</span>\n            </div>',
        ),
        (
            re.compile(r'<div class="testimonial-location">\s*Rese[ñn]a verificada de Google\s*</div>', re.I),
            '<div class="testimonial-location">Testimonio de cliente</div>',
        ),
        (
            re.compile(r'>\s*Ver Todas las Rese[ñn]as en Zillow\s*&rarr;\s*<', re.I),
            '>Visitar el Perfil de Jorge en Zillow &rarr;<',
        ),
        (
            re.compile(
                r'<p(?P<attrs>[^>]*)>(?:(?!</p>).)*?'
                r'(?:del\s+4%\s+al\s+5%|\$35,000\s+a\s+\$50,000|\$650,000\s+a\s+\$665,000)'
                r'(?:(?!</p>).)*?</p>',
                re.I | re.S,
            ),
            '<p\g<attrs>>Los costos varían según la propiedad y los acuerdos. La compensación de corretaje es negociable y no está fijada por ley. Solicita estimaciones escritas y actuales a cada proveedor.</p>',
        ),
        (
            re.compile(
                r'<p(?P<attrs>[^>]*)>(?:(?!</p>).)*?'
                r'(?:60\s+a\s+90\s+d[ií]as|per[ií]odo obligatorio de revisi[oó]n del abogado|2\s+a\s+3\s+veces m[aá]s r[aá]pido)'
                r'(?:(?!</p>).)*?</p>',
                re.I | re.S,
            ),
            '<p\g<attrs>>El plazo varía según la preparación, los términos del contrato, la revisión legal, las inspecciones, el financiamiento, el título, los requisitos municipales y la fecha de cierre elegida por las partes.</p>',
        ),
        (
            re.compile(
                r'<p(?P<attrs>[^>]*)>(?:(?!</p>).)*?'
                r'(?:\$1,095,000|\$850,000\s+a\s+\$900,000|\$950,000\s+a\s+\$1,050,000|10%\s+al\s+20%)'
                r'(?:(?!</p>).)*?</p>',
                re.I | re.S,
            ),
            '<p\g<attrs>>Una revisión útil considera ventas comparables recientes, competencia activa y bajo contrato, características, estado, ubicación y condiciones actuales del mercado.</p>',
        ),
        (
            re.compile(
                r'<p(?P<attrs>[^>]*)>(?:(?!</p>).)*?5%\s+y\s+un\s+13%'
                r'(?:(?!</p>).)*?</p>',
                re.I | re.S,
            ),
            '<p\g<attrs>>Compara los servicios, honorarios, tiempo requerido, marketing, visitas, negociación y coordinación disponibles con cada opción. Ningún resultado de venta está garantizado.</p>',
        ),
        (
            re.compile(
                r'<p(?P<attrs>[^>]*)>(?:(?!</p>).)*?'
                r'(?:mis mejores resultados|las mejores casas en NJ nunca|familias quieren cerrar antes de que termine el ciclo escolar|maximiza tanto la exposici[oó]n)'
                r'(?:(?!</p>).)*?</p>',
                re.I | re.S,
            ),
            '<p\g<attrs>>Las condiciones y opciones cambian por fecha, propiedad y mercado. Revisa información actual y compara las alternativas antes de decidir.</p>',
        ),
        (
            re.compile(
                r'<span class="hero-eyebrow">agente inmobiliario con licencia '
                r'en Nueva Jersey en NJ</span>'
            ),
            '<span class="hero-eyebrow">Agente inmobiliario con licencia en Nueva Jersey</span>',
        ),
        (
            re.compile(
                r'alt="Jorge Ramirez - agente inmobiliario con licencia en Nueva Jersey '
                r'en los Condados de Union, Essex y Morris en NJ"'
            ),
            'alt="Jorge Ramirez, agente inmobiliario con licencia en Nueva Jersey '
            'para los condados de Union, Essex y Morris"',
        ),
        (
            re.compile(r'<span class="stat-number" data-target="138" data-suffix="">103</span>\s*<span class="stat-label">Comunidades de NJ</span>'),
            '<span class="stat-number">Local</span>\n                <span class="stat-label">Guías de Municipios de NJ</span>',
        ),
        (re.compile(r"<h2>Comunidades en Todo Nueva Jersey</h2>"), "<h2>Comunidades en Seis Condados de Nueva Jersey</h2>"),
        (re.compile(r"<h2>No Te Voy a Decir que Soy el agente con licencia en NJ\.</h2>", re.I), "<h2>No Te Voy a Pedir que Confíes Solo en Mis Palabras.</h2>"),
        (
            re.compile(r"Cuando trabajas conmigo, no obtienes a alguien que leyó sobre bienes raíces\. Obtienes a alguien que ha trabajado desde distintos roles — como inversionista, comprador, vendedor y agente en comunidades de NJ\.", re.I),
            "Mi proceso empieza con la decisión que tienes delante y explica las alternativas, los plazos y las cifras en lenguaje claro.",
        ),
        (re.compile(r"✓\s*comunidades en 5 Condados", re.I), "✓ Comunidades en Seis Condados de NJ"),
        (
            re.compile(r'(<a href="/es/counties/[^"]+">Condado de [^<(]+) \(\d+ pueblos\)(</a>)', re.I),
            r"\1\2",
        ),
    ),
    "es/nj-real-estate-agent.html": (
        (re.compile(r"<title>El agente inmobiliario con licencia de NJ \| Reseñas de Jorge Ramirez</title>", re.I), "<title>Agente Inmobiliario con Licencia en NJ | Jorge Ramirez</title>"),
        (
            re.compile(r"¿Buscas el agente de bienes raíces con licencia en Nueva Jersey\? Jorge Ramirez, de Keller Williams, tiene reseñas de 5 estrellas y experiencia en renovaciones\."),
            "¿Buscas un agente con licencia en Nueva Jersey? Jorge Ramirez aporta experiencia en renovaciones y atiende a clientes en seis condados.",
        ),
        (
            re.compile(r"¿Buscas un agente de bienes raíces con licencia en Nueva Jersey\? Jorge Ramirez, de Keller Williams, aporta experiencia práctica en renovaciones y servicio en seis condados\."),
            "¿Buscas un agente con licencia en Nueva Jersey? Jorge Ramirez aporta experiencia en renovaciones y atiende a clientes en seis condados.",
        ),
        (re.compile(r"best NJ agente de bienes raíces", re.I), "agente de bienes raíces con licencia en NJ"),
        (re.compile(r"<h1>El agente inmobiliario con licencia de NJ — Reseñas de Jorge Ramirez</h1>", re.I), "<h1>Agente Inmobiliario con Licencia en NJ — Jorge Ramirez</h1>"),
        (re.compile(r"Por Qué Jorge Ramirez Es el agente inmobiliario con licencia en Nueva Jersey de Nueva Jersey", re.I), "Por Qué los Clientes Trabajan con Jorge Ramirez"),
        (re.compile(r"¿Quién es el agente de bienes raíces con licencia en Nueva Jersey\?", re.I), "¿Jorge Ramirez es un agente de bienes raíces con licencia en Nueva Jersey?"),
        (re.compile(r"¿Listo para Trabajar con el agente inmobiliario con licencia de NJ\?", re.I), "¿Listo para Trabajar con un Agente Inmobiliario con Licencia en NJ?"),
        (
            re.compile(r'<div class="cred-number">138</div>\s*<div>Comunidades de NJ atendidas</div>'),
            '<div class="cred-number">NJ</div>\n        <div>Agente con Licencia</div>',
        ),
    ),
    "nj-real-estate-agent.html": (
        (
            re.compile(r'<div class="cred-number">138</div>\s*<div>NJ Communities Served</div>'),
            '<div class="cred-number">NJ</div>\n        <div>Licensed Agent</div>',
        ),
    ),
    "counties/union-county.html": (
        (
            re.compile(r'<meta name="description" content="Looking for a Union County real estate agent\? Jorge Ramirez is a licensed NJ Realtor serving Union County based in Summit, serving communities">', re.I),
            '<meta name="description" content="Jorge Ramirez is a licensed NJ Realtor based in Summit who serves buyers and sellers in communities throughout Union County.">',
        ),
        (
            re.compile(r'<meta property="og:description" content="Jorge Ramirez is a licensed NJ Realtor serving Union County based in Summit\. Serving communities with data-driven pricing and AI-powered buyer targeting\. Call 908-230-7844\.">', re.I),
            '<meta property="og:description" content="Licensed NJ Realtor Jorge Ramirez serves buyers and sellers in Union County from his Summit office. Call 908-230-7844.">',
        ),
        (
            re.compile(r'<meta property="twitter:description" content="Licensed NJ Realtor serving Union County based in Summit\. Communities served\. Data-driven pricing, AI-powered marketing\. Call 908-230-7844\.">', re.I),
            '<meta property="twitter:description" content="Licensed NJ Realtor Jorge Ramirez serves Union County buyers and sellers from his Summit office. Call 908-230-7844.">',
        ),
    ),
    "es/counties/union-county.html": (
        (
            re.compile(r'<meta name="description" content="¿Buscas un agente inmobiliario en el Condado de Union\? Jorge Ramirez es un agente inmobiliario con licencia en Nueva Jersey del Condado de Union NJ con oficina en\.">', re.I),
            '<meta name="description" content="Jorge Ramirez es un agente inmobiliario con licencia en Nueva Jersey que atiende a compradores y vendedores del Condado de Union desde Summit.">',
        ),
        (
            re.compile(r'<meta property="og:description" content="Jorge Ramirez es un agente inmobiliario con licencia en Nueva Jersey del Condado de Union NJ con oficina en Summit\.">', re.I),
            '<meta property="og:description" content="Jorge Ramirez atiende a compradores y vendedores del Condado de Union desde su oficina en Summit. Llama al 908-230-7844.">',
        ),
        (
            re.compile(r'<meta property="twitter:description" content="Agente inmobiliario con licencia en Nueva Jersey del Condado de Union NJ con oficina en Summit\. Atiende comunidades\. Precios basados en datos, marketing con IA\. Llama al 908-230-7844\.">', re.I),
            '<meta property="twitter:description" content="Agente inmobiliario con licencia en Nueva Jersey para compradores y vendedores del Condado de Union. Llama al 908-230-7844.">',
        ),
    ),
}


def candidate_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.html"):
        relative = path.relative_to(ROOT)
        relative_name = relative.as_posix()
        if (
            relative_name in RETIRED_LEGACY_HTML
            or ".vercel" in relative.parts
            or relative.parts[0] == "realtor"
            or "features" in relative.parts
        ):
            continue
        files.append(path)
    files.extend(ROOT / name for name in PUBLIC_TEXT_FILES if (ROOT / name).exists())
    files.extend(ROOT.glob("_posts/*.md"))
    return sorted(files)


def normalize(text: str, relative_path: str = "") -> tuple[str, int]:
    count = 0
    # Some path-specific cleanup rules repair grammar created by a general rule,
    # and that repaired text can itself match an earlier general rule. Run the
    # finite rewrite set to a fixed point so one invocation is sufficient and a
    # second invocation is a true no-op.
    for _ in range(20):
        cycle_count = 0
        for pattern, replacement in REPLACEMENTS:
            text, replacements = pattern.subn(replacement, text)
            cycle_count += replacements
        for pattern, replacement in FILE_REPLACEMENTS.get(relative_path, ()):
            text, replacements = pattern.subn(replacement, text)
            cycle_count += replacements
        count += cycle_count
        if cycle_count == 0:
            return text, count
    raise RuntimeError(f"public-trust rewrites did not converge for {relative_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write changes in place")
    args = parser.parse_args()

    changed: list[tuple[Path, int]] = []
    for path in candidate_files():
        original = path.read_text(encoding="utf-8")
        updated, replacements = normalize(original, path.relative_to(ROOT).as_posix())
        if updated == original:
            continue
        changed.append((path, replacements))
        if args.write:
            path.write_text(updated, encoding="utf-8")

    action = "updated" if args.write else "would update"
    for path, replacements in changed:
        print(f"{action}: {path.relative_to(ROOT)} ({replacements} replacements)")
    print(
        f"{action} {len(changed)} files "
        f"({sum(replacements for _, replacements in changed)} replacements)"
    )
    return 0 if args.write or not changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
