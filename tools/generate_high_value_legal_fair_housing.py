#!/usr/bin/env python3
"""Render the reviewed high-value legal and fair-housing content cluster."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "high-value-legal-fair-housing-sources.json"
SITE_FACTS_PATH = ROOT / "data" / "site-facts.json"
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
RENDERER = "tools/generate_high_value_legal_fair_housing.py"
FALLBACK_PATH = "blog/selling-inherited-house-multiple-heirs-nj.html"
FALLBACK_DESTINATION = "/blog/selling-inherited-home-nj"

EXPECTED_FILES = {
    "buyer-agency-agreement-nj.html",
    "es/buyer-agency-agreement-nj.html",
    "blog/maplewood-vs-south-orange-nj.html",
    "es/blog/maplewood-vs-south-orange-nj.html",
    "blog/summit-vs-westfield-nj.html",
    "es/blog/summit-vs-westfield-nj.html",
    "blog/nj-home-selling-timeline.html",
    "es/blog/nj-home-selling-timeline.html",
    "blog/probate-real-estate-nj-guide.html",
    "es/blog/probate-real-estate-nj-guide.html",
    "blog/how-to-appeal-nj-property-taxes-2026.html",
    "westfield-vs-scotch-plains-nj.html",
    FALLBACK_PATH,
}

EXPECTED_CLUSTERS = {
    "buyer-agency": {
        "buyer-agency-agreement-nj.html",
        "es/buyer-agency-agreement-nj.html",
    },
    "maplewood-south-orange": {
        "blog/maplewood-vs-south-orange-nj.html",
        "es/blog/maplewood-vs-south-orange-nj.html",
    },
    "summit-westfield": {
        "blog/summit-vs-westfield-nj.html",
        "es/blog/summit-vs-westfield-nj.html",
    },
    "selling-timeline": {
        "blog/nj-home-selling-timeline.html",
        "es/blog/nj-home-selling-timeline.html",
    },
    "probate": {
        "blog/probate-real-estate-nj-guide.html",
        "es/blog/probate-real-estate-nj-guide.html",
    },
    "tax-appeal": {"blog/how-to-appeal-nj-property-taxes-2026.html"},
    "westfield-scotch-plains": {"westfield-vs-scotch-plains-nj.html"},
    "multiple-heirs-alias": {FALLBACK_PATH},
}
SPANISH_SOURCE_CLUSTERS = {
    "buyer-agency",
    "maplewood-south-orange",
    "summit-westfield",
    "selling-timeline",
    "probate",
}

SOURCE_FIELDS = {
    "id",
    "publisher",
    "title",
    "url",
    "kind",
    "use",
    "limit",
    "accessedOn",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_manifest(path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1:
        raise ValueError("source manifest schemaVersion must be 1")
    if document.get("reviewedOn") != REVIEWED_ON:
        raise ValueError("source manifest review date changed")
    if document.get("renderer") != RENDERER:
        raise ValueError("source manifest points to another renderer")
    if set(document.get("managedFiles", [])) != EXPECTED_FILES:
        raise ValueError("managed file inventory changed")
    if len(document.get("managedFiles", [])) != len(EXPECTED_FILES):
        raise ValueError("managed file inventory contains duplicates")

    clusters = document.get("clusters")
    if not isinstance(clusters, dict) or set(clusters) != set(EXPECTED_CLUSTERS):
        raise ValueError("source cluster inventory changed")
    for cluster, expected_files in EXPECTED_CLUSTERS.items():
        record = clusters[cluster]
        if set(record.get("files", [])) != expected_files:
            raise ValueError("cluster %s changed its managed files" % cluster)
        if not record.get("sourceIds"):
            raise ValueError("cluster %s has no reviewed sources" % cluster)
    if clusters["multiple-heirs-alias"].get("destination") != FALLBACK_DESTINATION:
        raise ValueError("multiple-heirs destination changed")

    sources = document.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources must be a non-empty list")
    source_ids: List[str] = []
    for source in sources:
        if set(source) != SOURCE_FIELDS:
            raise ValueError("source %r changed fields" % source.get("id"))
        if source.get("accessedOn") != REVIEWED_ON:
            raise ValueError("source %s lacks current review date" % source.get("id"))
        if not str(source.get("url", "")).startswith("https://"):
            raise ValueError("source %s must use HTTPS" % source.get("id"))
        for field in SOURCE_FIELDS - {"accessedOn"}:
            if not str(source.get(field, "")).strip():
                raise ValueError("source %s lacks %s" % (source.get("id"), field))
        source_ids.append(source["id"])
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source IDs must be unique")
    known = set(source_ids)
    for cluster, record in clusters.items():
        missing = set(record["sourceIds"]) - known
        if missing:
            raise ValueError("cluster %s refers to unknown sources: %s" % (cluster, sorted(missing)))
    spanish_source_copy = document.get("spanishSourceCopy")
    translated_source_ids = {
        source_id
        for cluster in SPANISH_SOURCE_CLUSTERS
        for source_id in clusters[cluster]["sourceIds"]
    }
    if not isinstance(spanish_source_copy, dict) or set(spanish_source_copy) != translated_source_ids:
        raise ValueError("Spanish source-copy inventory changed")
    for source_id, source_copy in spanish_source_copy.items():
        if not isinstance(source_copy, dict) or set(source_copy) != {"kind", "title", "use", "limit"}:
            raise ValueError("Spanish source copy for %s changed fields" % source_id)
        if not all(str(value).strip() for value in source_copy.values()):
            raise ValueError("Spanish source copy for %s is incomplete" % source_id)
    return document


def load_business() -> Dict[str, Any]:
    document = json.loads(SITE_FACTS_PATH.read_text(encoding="utf-8"))
    business = document.get("business", {})
    expected = {
        "name": "The Jorge Ramirez Group",
        "agentName": "Jorge Ramirez",
        "email": "jorge.ramirez@kw.com",
        "njRealEstateLicense": "1754604",
    }
    for key, value in expected.items():
        if business.get(key) != value:
            raise ValueError("verified site fact changed: business.%s" % key)
    if business.get("directPhone", {}).get("e164") != "+19082307844":
        raise ValueError("verified direct phone changed")
    if business.get("brokerage", {}).get("displayName") != "Keller Williams Premier Properties":
        raise ValueError("verified brokerage changed")
    return business


def card(title: str, body: str, items: Sequence[str] = ()) -> Dict[str, Any]:
    return {"title": title, "body": body, "items": list(items)}


def section(
    section_id: str,
    heading: str,
    intro: str,
    cards: Sequence[Mapping[str, Any]] = (),
    items: Sequence[str] = (),
    note: str = "",
    dark: bool = False,
) -> Dict[str, Any]:
    return {
        "id": section_id,
        "heading": heading,
        "intro": intro,
        "cards": list(cards),
        "items": list(items),
        "note": note,
        "dark": dark,
    }


def buyer_pages() -> List[Dict[str, Any]]:
    return [
        {
            "path": "buyer-agency-agreement-nj.html",
            "route": "/buyer-agency-agreement-nj",
            "otherRoute": "/es/buyer-agency-agreement-nj",
            "cluster": "buyer-agency",
            "lang": "en",
            "publishedOn": "2024-08-17",
            "title": "NJ Buyer Agency Agreement: Law, MLS Policy & Fees",
            "description": "Understand New Jersey buyer-agency agreements, negotiable compensation, the separate MLS touring policy, open-house exception, and questions to ask before signing.",
            "eyebrow": "New Jersey buyer representation · source reviewed",
            "h1": "NJ buyer agency agreements: law, MLS policy, and compensation",
            "dek": "A plain-language review of what New Jersey requires, what participating MLS rules require before touring, and which contract terms remain negotiable.",
            "sections": [
                section(
                    "law-versus-policy",
                    "New Jersey law and MLS policy are separate rules",
                    "They overlap in practice, but they come from different authorities. Keeping them separate prevents a national MLS rule from being described as a New Jersey or federal law.",
                    cards=(
                        card(
                            "New Jersey brokerage-services law",
                            "NJDOBI Bulletin 24-11 says a brokerage firm must obtain a signed brokerage services agreement before, or as soon as reasonably practical after, the firm starts providing residential brokerage services for a buyer. The agreement also establishes the business relationship and its terms.",
                        ),
                        card(
                            "MLS participant touring policy",
                            "NAR's policy guidance says an MLS Participant working with a buyer enters into a written agreement before an in-person or live virtual home tour. That is an MLS policy requirement, not a federal statute and not the source of New Jersey's brokerage-services rule.",
                        ),
                        card(
                            "Open-house exception",
                            "NAR's consumer guide says a person who visits an open house without your own agent, or only asks the host about services, does not need a written buyer agreement for that visit. The host is acting at the direction of the listing broker or seller.",
                        ),
                    ),
                ),
                section(
                    "agreement-terms",
                    "What the written agreement should make clear",
                    "Read the actual form before services begin. The signed document—not a website summary—controls the relationship.",
                    items=(
                        "The type of brokerage relationship and the separate Agency Disclosure paragraph or document.",
                        "The services the brokerage will provide and the term of the agreement.",
                        "Whether an agency relationship is exclusive or non-exclusive, when applicable.",
                        "The compensation amount or how it will be calculated, plus any permitted sharing or payment by more than one party.",
                        "Any consent to disclosed dual agency or designated agency and the conditions attached to that consent.",
                        "How the parties will proceed if another party offers no compensation or less than the amount in the buyer's agreement.",
                    ),
                    note="The New Jersey Real Estate Commission also warns that the Consumer Information Statement is not itself a buyer-agency contract.",
                ),
                section(
                    "compensation",
                    "Compensation is negotiable; the payor is not assumed",
                    "Bulletin 24-11 says brokerage compensation is fully negotiable and not set by law. It may be paid by the seller, buyer, third party, or compensation shared between brokerage firms. The agreement must state the amount or calculation method and address the buyer's instructions when another party offers limited or no payment.",
                    cards=(
                        card("Ask for the total", "Request the exact amount or calculation method, when it becomes due, and whether the brokerage may receive payment from another source."),
                        card("Ask about scope", "Match the agreement's duration, geographic or property scope, services, exclusivity, and termination language to what you understand."),
                        card("Ask before touring", "Resolve unclear payment, agency, conflict, and termination terms before a tour or offer rather than after a property is selected."),
                    ),
                    dark=True,
                ),
                section(
                    "signing-checklist",
                    "A buyer's pre-signing checklist",
                    "Use these questions as a conversation guide, then obtain legal advice for contract interpretation.",
                    items=(
                        "Which paragraph creates the agency or transaction-broker relationship?",
                        "What services start immediately, and what services are outside the scope?",
                        "How long does the agreement last, what property or area does it cover, and how can it end?",
                        "What amount could I owe, how is it calculated, and what other payment sources are permitted?",
                        "Could disclosed dual agency or designated agency arise, and what consent would be requested?",
                        "What happens if I attend an open house, contact a listing agent, or already have another exclusive agreement?",
                    ),
                ),
            ],
            "disclaimerHeading": "Scope and legal-information notice",
            "disclaimer": "This page summarizes public regulatory and policy sources reviewed on 2026-08-26. It is not legal advice, does not quote or modify any brokerage agreement, and does not state Jorge Ramirez's terms. Read the proposed agreement and consult a New Jersey attorney about legal rights or obligations.",
            "ctaHeading": "Review the actual terms before services begin",
            "ctaText": "Ask Jorge to explain the proposed services, agency relationship, duration, compensation method, and conflict provisions in writing. Legal questions belong with your attorney.",
            "ctaLabel": "Ask a buyer-agreement question",
        },
        {
            "path": "es/buyer-agency-agreement-nj.html",
            "route": "/es/buyer-agency-agreement-nj",
            "otherRoute": "/buyer-agency-agreement-nj",
            "cluster": "buyer-agency",
            "lang": "es",
            "publishedOn": "2024-08-17",
            "title": "Acuerdo del Comprador en NJ: Ley, MLS y Honorarios",
            "description": "Entienda el acuerdo del comprador en Nueva Jersey, la compensación negociable, la política separada del MLS, la excepción de casas abiertas y qué revisar.",
            "eyebrow": "Representación del comprador en NJ · fuentes revisadas",
            "h1": "Acuerdos del comprador en NJ: ley, política del MLS y compensación",
            "dek": "Una explicación clara de lo que exige Nueva Jersey, lo que las reglas de MLS participantes exigen antes de un recorrido y qué términos siguen siendo negociables.",
            "sections": [
                section(
                    "ley-y-politica",
                    "La ley de Nueva Jersey y la política del MLS son reglas distintas",
                    "Coinciden en parte durante el proceso, pero provienen de autoridades diferentes. Separarlas evita presentar una regla nacional del MLS como ley estatal o federal.",
                    cards=(
                        card(
                            "Ley estatal sobre servicios inmobiliarios",
                            "El Boletín 24-11 de NJDOBI dice que la firma inmobiliaria debe obtener un acuerdo de servicios firmado antes de comenzar los servicios o tan pronto como sea razonablemente práctico después de iniciarlos para un comprador residencial.",
                        ),
                        card(
                            "Política de recorridos para participantes del MLS",
                            "La guía de NAR indica que un participante del MLS que trabaja con un comprador celebra un acuerdo escrito antes de un recorrido presencial o virtual en vivo. Es una regla del MLS, no una ley federal ni la fuente de la regla estatal.",
                        ),
                        card(
                            "Excepción de casa abierta",
                            "La guía de NAR dice que una persona que visita una casa abierta sin su propio agente, o solo pregunta al anfitrión sobre sus servicios, no necesita un acuerdo escrito para esa visita. El anfitrión actúa por encargo del corredor del listado o del vendedor.",
                        ),
                    ),
                ),
                section(
                    "terminos-del-acuerdo",
                    "Lo que debe aclarar el acuerdo escrito",
                    "Lea el formulario real antes de que comiencen los servicios. El documento firmado, y no un resumen web, controla la relación.",
                    items=(
                        "El tipo de relación inmobiliaria y el párrafo o documento separado de divulgación de agencia.",
                        "Los servicios que prestará la firma y la duración del acuerdo.",
                        "Si la relación de agencia es exclusiva o no exclusiva, cuando corresponda.",
                        "La compensación o su método de cálculo, además de cualquier reparto o pago permitido por más de una parte.",
                        "Cualquier consentimiento para agencia dual divulgada o agencia designada y sus condiciones.",
                        "Cómo procederán las partes si otra parte no ofrece pago o ofrece menos que la cantidad pactada con el comprador.",
                    ),
                    note="La Comisión de Bienes Raíces de Nueva Jersey también advierte que la Declaración de Información al Consumidor no es por sí sola un contrato de agencia del comprador.",
                ),
                section(
                    "compensacion",
                    "La compensación se negocia; no se presume quién paga",
                    "El Boletín 24-11 dice que la compensación es totalmente negociable y no la fija la ley. Puede pagarla el vendedor, comprador, tercero o mediante reparto entre firmas inmobiliarias. El acuerdo debe indicar la cantidad o el método de cálculo y qué ocurrirá si otra parte ofrece un pago limitado o ninguno.",
                    cards=(
                        card("Pregunte por el total", "Solicite la cantidad exacta o el método de cálculo, cuándo se devenga y si la firma puede recibir pago de otra fuente."),
                        card("Pregunte por el alcance", "Compare la duración, el área o las propiedades cubiertas, los servicios, la exclusividad y la terminación con lo que usted entiende."),
                        card("Pregunte antes del recorrido", "Aclare pago, agencia, conflictos y terminación antes de visitar o presentar una oferta, no después de elegir una propiedad."),
                    ),
                    dark=True,
                ),
                section(
                    "lista-de-revision",
                    "Lista de revisión antes de firmar",
                    "Use estas preguntas para conversar y solicite asesoramiento jurídico para interpretar el contrato.",
                    items=(
                        "¿Qué párrafo crea la relación de agencia o de corredor de transacción?",
                        "¿Qué servicios empiezan de inmediato y cuáles quedan fuera?",
                        "¿Cuánto dura, qué propiedad o zona cubre y cómo puede terminar?",
                        "¿Qué cantidad podría adeudar, cómo se calcula y qué otras fuentes de pago se permiten?",
                        "¿Podría surgir agencia dual divulgada o agencia designada y qué consentimiento se pediría?",
                        "¿Qué ocurre si voy a una casa abierta, contacto al agente del listado o ya tengo otro acuerdo exclusivo?",
                    ),
                ),
            ],
            "disclaimerHeading": "Alcance y aviso de información jurídica",
            "disclaimer": "Esta página resume fuentes regulatorias y de política pública revisadas el 2026-08-26. No es asesoramiento legal, no cita ni modifica ningún acuerdo y no declara los términos de Jorge Ramirez. Lea el acuerdo propuesto y consulte a un abogado de Nueva Jersey sobre derechos u obligaciones legales.",
            "ctaHeading": "Revise los términos reales antes de iniciar servicios",
            "ctaText": "Pida a Jorge que explique por escrito los servicios propuestos, la relación de agencia, la duración, el método de compensación y los conflictos. Las preguntas jurídicas corresponden a su abogado.",
            "ctaLabel": "Hacer una pregunta sobre el acuerdo",
        },
    ]


def comparison_pages() -> List[Dict[str, Any]]:
    return [
        {
            "path": "blog/maplewood-vs-south-orange-nj.html",
            "route": "/blog/maplewood-vs-south-orange-nj",
            "otherRoute": "/es/blog/maplewood-vs-south-orange-nj",
            "cluster": "maplewood-south-orange",
            "lang": "en",
            "publishedOn": "2025-01-12",
            "modifiedOn": "2026-08-27",
            "title": "Maplewood vs South Orange, NJ: An Official-Source Comparison",
            "description": "Compare Maplewood and South Orange with official municipal, school-report, transit, tax, Census, and fair-housing sources—then verify the property address.",
            "eyebrow": "Essex County comparison · address-first research",
            "h1": "Maplewood vs South Orange: compare records, not labels",
            "dek": "A neutral research framework for two distinct Essex County municipalities that share a school district. It avoids lifestyle assumptions and sends address-specific questions to the responsible public source.",
            "sections": [
                section(
                    "municipal-records",
                    "Two municipalities, two sets of local records",
                    "Maplewood Township and South Orange Village are separate municipal entities. Start with the official municipal site for the exact property address rather than relying on a portal label or postal city.",
                    cards=(
                        card("Maplewood records", "Use Maplewood's official site for township departments, land-use material, public notices, and local contacts tied to a Maplewood address."),
                        card("South Orange records", "Use South Orange's official site for village departments, land-use material, public notices, and local contacts tied to a South Orange address."),
                        card("Census entity profiles", "The Census profiles describe each government entity using published datasets. They are context, not a prediction about a block, household, property, or future conditions."),
                    ),
                ),
                section(
                    "schools-and-address",
                    "Shared district does not remove address-level verification",
                    "Both municipalities are served by the South Orange-Maplewood School District. For 2024-25 public-school information, use the NJDOE School Performance Reports and the district's own assignment and enrollment resources.",
                    items=(
                        "Confirm the municipality and parcel record for the property address.",
                        "Ask the district to confirm the current assigned school for that address; do not infer an assignment from a listing or map pin.",
                        "Read the 2024-25 NJDOE report's definitions, comparison groups, data notes, and suppression rules before interpreting a measure.",
                        "Treat school information as objective public data, not a neighborhood recommendation or a statement about who should live there.",
                    ),
                    note="Attendance boundaries, programs, and enrollment procedures can change. The district is the source for a current address-level answer.",
                ),
                section(
                    "transit-and-tax",
                    "Check the actual trip and actual parcel",
                    "NJ TRANSIT maintains separate Maplewood and South Orange station pages. Use the current Trip Planner with your origin, destination, date, and time; this page does not promise a commute duration, frequency, transfer pattern, parking space, or service level.",
                    cards=(
                        card("Station resources", "Review the official station pages for current accessibility, parking, connecting service, notices, and facility information. Verify the route from the property address separately."),
                        card("Trip Planner", "Run the NJ TRANSIT Trip Planner for the trip you expect to make and check service alerts again near travel time."),
                        card("Property-tax records", "NJ Treasury publishes municipal statistical tables, but a municipal figure is not a parcel's tax bill. Verify the assessment, tax record, and current charges for the exact address."),
                    ),
                    dark=True,
                ),
                section(
                    "fair-housing-boundary",
                    "Fair housing boundary for a neutral comparison",
                    "Fair housing laws prohibit housing discrimination based on protected characteristics. This comparison does not rank communities, use information about residents as a buying signal, characterize safety, or steer a reader by school reputation.",
                    items=(
                        "Define property criteria such as housing type, condition, lot features, budget, and accessibility needs.",
                        "Verify taxes, land-use records, utilities, flood information, insurance, and title for each property under consideration.",
                        "Use the same official-source checklist for both municipalities so the comparison stays consistent.",
                        "Contact NJ DCA or the New Jersey Division on Civil Rights for current fair housing information or a discrimination concern.",
                    ),
                ),
            ],
            "disclaimerHeading": "Scope, change, and fair-housing notice",
            "disclaimer": "This page is a source map reviewed on 2026-08-26, not legal, tax, school-placement, transit, insurance, environmental, or housing advice. Public data and services change. Verify every material fact for the exact property address with the responsible agency and evaluate housing without protected-class preferences or proxies.",
            "ctaHeading": "Build an address-level comparison",
            "ctaText": "Share the properties and objective features you want to compare. Jorge can help organize listing and public-record questions; agencies and qualified professionals remain the sources for final answers.",
            "ctaLabel": "Request an objective comparison",
        },
        {
            "path": "es/blog/maplewood-vs-south-orange-nj.html",
            "route": "/es/blog/maplewood-vs-south-orange-nj",
            "otherRoute": "/blog/maplewood-vs-south-orange-nj",
            "cluster": "maplewood-south-orange",
            "lang": "es",
            "publishedOn": "2025-01-12",
            "modifiedOn": "2026-08-27",
            "title": "Maplewood vs South Orange, NJ: Comparación con Fuentes Oficiales",
            "description": "Compare Maplewood y South Orange con fuentes municipales, escolares, de transporte, impuestos, Censo y vivienda justa, verificando cada dirección.",
            "eyebrow": "Comparación de Essex County · investigación por dirección",
            "h1": "Maplewood vs South Orange: compare registros, no etiquetas",
            "dek": "Un marco neutral para investigar dos municipios distintos de Essex County que comparten distrito escolar, sin suposiciones sobre estilo de vida y con verificación para cada dirección.",
            "sections": [
                section(
                    "registros-municipales",
                    "Dos municipios y dos grupos de registros locales",
                    "Maplewood Township y South Orange Village son entidades municipales separadas. Empiece con el sitio oficial correspondiente a la dirección exacta, no con la etiqueta de un portal o la ciudad postal.",
                    cards=(
                        card("Registros de Maplewood", "Use el sitio oficial de Maplewood para departamentos, uso de suelo, avisos públicos y contactos vinculados con una dirección de Maplewood."),
                        card("Registros de South Orange", "Use el sitio oficial de South Orange para departamentos, uso de suelo, avisos públicos y contactos vinculados con una dirección de South Orange."),
                        card("Perfiles del Censo", "Los perfiles del Censo describen cada entidad gubernamental con datos publicados. No predicen condiciones de una cuadra, hogar, propiedad ni condiciones futuras."),
                    ),
                ),
                section(
                    "escuelas-y-direccion",
                    "Compartir distrito no elimina la verificación por dirección",
                    "Ambos municipios reciben servicios del South Orange-Maplewood School District. Para información pública de 2024-25, consulte los School Performance Reports de NJDOE y los recursos de asignación e inscripción del distrito.",
                    items=(
                        "Confirme el municipio y el registro de parcela para la dirección de la propiedad.",
                        "Pida al distrito que confirme la escuela asignada actualmente a esa dirección; no la deduzca de un anuncio o marcador de mapa.",
                        "Lea definiciones, grupos de comparación, notas de datos y reglas de supresión del informe 2024-25 de NJDOE.",
                        "Trate la información escolar como datos públicos objetivos, no como recomendación de un barrio ni señal de quién debe vivir allí.",
                    ),
                    note="Los límites de asistencia, programas y procesos de inscripción pueden cambiar. El distrito debe confirmar la respuesta actual para la dirección.",
                ),
                section(
                    "transporte-e-impuestos",
                    "Revise el viaje real y la parcela real",
                    "NJ TRANSIT mantiene páginas separadas para las estaciones de Maplewood y South Orange. Use el Planificador de viajes actual con origen, destino, fecha y hora; esta página no promete duración, frecuencia, transbordos, estacionamiento ni nivel de servicio.",
                    cards=(
                        card("Recursos de estaciones", "Consulte las páginas oficiales sobre accesibilidad, estacionamiento, conexiones, avisos e instalaciones. Verifique aparte la ruta desde la dirección."),
                        card("Planificador de viajes", "Ejecute el Planificador de viajes de NJ TRANSIT para el trayecto previsto y vuelva a revisar los avisos cerca de la salida."),
                        card("Registros de impuestos", "NJ Treasury publica tablas estadísticas municipales, pero un dato municipal no es la factura de una parcela. Verifique tasación, registro fiscal y cargos actuales de la dirección."),
                    ),
                    dark=True,
                ),
                section(
                    "vivienda-justa",
                    "Límite de vivienda justa para una comparación neutral",
                    "Las leyes de vivienda justa prohíben la discriminación por características protegidas. Esta comparación no clasifica comunidades, usa datos demográficos como señal de compra, caracteriza seguridad ni orienta por reputación escolar.",
                    items=(
                        "Defina criterios de la propiedad: tipo, condición, terreno, presupuesto y necesidades de accesibilidad.",
                        "Verifique impuestos, uso de suelo, servicios, inundación, seguro y título de cada propiedad.",
                        "Use la misma lista de fuentes oficiales para ambos municipios.",
                        "Contacte a NJ DCA o a la Division on Civil Rights de Nueva Jersey para información vigente sobre vivienda justa o una inquietud de discriminación.",
                    ),
                ),
            ],
            "disclaimerHeading": "Aviso de alcance, cambios y vivienda justa",
            "disclaimer": "Esta página es un mapa de fuentes revisado el 2026-08-26, no asesoramiento legal, fiscal, escolar, de transporte, seguro, ambiental ni de vivienda. Los datos y servicios cambian. Verifique cada hecho material para la dirección exacta y evalúe vivienda sin preferencias ni sustitutos de características protegidas.",
            "ctaHeading": "Prepare una comparación por dirección",
            "ctaText": "Comparta las propiedades y características objetivas que desea comparar. Jorge puede ayudar a organizar preguntas del anuncio y registros públicos; las agencias y profesionales cualificados dan las respuestas finales.",
            "ctaLabel": "Solicitar una comparación objetiva",
        },
        {
            "path": "blog/summit-vs-westfield-nj.html",
            "route": "/blog/summit-vs-westfield-nj",
            "otherRoute": "/es/blog/summit-vs-westfield-nj",
            "cluster": "summit-westfield",
            "lang": "en",
            "publishedOn": "2025-02-08",
            "modifiedOn": "2026-08-27",
            "title": "Summit vs Westfield, NJ: An Official-Source Comparison",
            "description": "Compare Summit and Westfield through official municipal, district, NJDOE, transit, tax, Census, and fair-housing resources, property by property.",
            "eyebrow": "Union County comparison · verify each address",
            "h1": "Summit vs Westfield: a property-by-property research guide",
            "dek": "A neutral way to compare two separate Union County municipalities using the same public-source checklist, without rankings, protected-class proxies, or commute promises.",
            "sections": [
                section(
                    "local-government",
                    "Separate municipal and school systems",
                    "Summit and Westfield are distinct municipalities with separate local departments and public-school districts. Confirm which entity is responsible for every question tied to a property address.",
                    cards=(
                        card("Municipal sources", "Use the City of Summit or Town of Westfield official site for local departments, notices, land-use records, and property-related contacts."),
                        card("District sources", "Use Summit Public Schools or Westfield Public Schools for current enrollment and address-assignment questions."),
                        card("Census context", "Census entity profiles provide published municipal context. They do not describe an individual property or establish a housing recommendation."),
                    ),
                ),
                section(
                    "school-research",
                    "Read school data with its definitions",
                    "The NJDOE 2024-25 School Performance Reports publish measures, explanatory notes, and comparison context. They should be read with district assignment information for the exact address, not converted into a neighborhood label.",
                    items=(
                        "Confirm the current district and assigned school directly with the district using the property address.",
                        "Review the 2024-25 report's methodology and data notes before comparing a measure.",
                        "Ask about programs or services through the district without making assumptions about a buyer or household.",
                        "Recheck assignment and enrollment procedures before relying on them in a housing decision.",
                    ),
                ),
                section(
                    "travel-and-taxes",
                    "Transit and tax questions require current inputs",
                    "NJ TRANSIT provides official Summit and Westfield station resources. Enter the expected origin, destination, date, and time in the Trip Planner and review alerts; no static page can promise a commute or future schedule.",
                    cards=(
                        card("Station details", "Review current accessibility, parking, facilities, connections, and service notices on the official station page, then verify access from the property address."),
                        card("Trip Planner", "Test the trip under the conditions that matter to you and repeat the check when schedules or travel needs change."),
                        card("Parcel-level tax review", "Use NJ Treasury statistics for municipal context only. Obtain the current assessment and tax record for each parcel and ask the responsible office about discrepancies."),
                    ),
                    dark=True,
                ),
                section(
                    "neutral-criteria",
                    "Use objective criteria within fair housing boundaries",
                    "Fair housing guidance from NJ DCA and the New Jersey Division on Civil Rights explains protected characteristics and discriminatory housing conduct. This page does not rate municipalities or infer resident preferences.",
                    items=(
                        "Compare property condition, layout, accessibility, lot features, budget, and verified land-use constraints.",
                        "Verify environmental, flood, insurance, title, utility, and inspection questions for each property.",
                        "Apply the same questions to Summit and Westfield and record the date and source of each answer.",
                        "Use public agencies for current fair housing information and reporting options.",
                    ),
                    note="A fair housing comparison focuses on properties, services, and verified public records—not protected characteristics or coded substitutes.",
                ),
            ],
            "disclaimerHeading": "Research and fair-housing scope",
            "disclaimer": "This source map was reviewed on 2026-08-26 and is not legal, tax, school-placement, transit, environmental, insurance, inspection, or housing advice. Conditions and public information change. Verify material facts for the property address with the responsible source.",
            "ctaHeading": "Compare specific Summit and Westfield properties",
            "ctaText": "Jorge can help organize objective listing and public-record questions around the properties you identify. Public agencies and qualified professionals should confirm the underlying facts.",
            "ctaLabel": "Request a property comparison",
        },
        {
            "path": "es/blog/summit-vs-westfield-nj.html",
            "route": "/es/blog/summit-vs-westfield-nj",
            "otherRoute": "/blog/summit-vs-westfield-nj",
            "cluster": "summit-westfield",
            "lang": "es",
            "publishedOn": "2025-02-08",
            "modifiedOn": "2026-08-27",
            "title": "Summit vs Westfield, NJ: Comparación con Fuentes Oficiales",
            "description": "Compare Summit y Westfield con recursos oficiales municipales, escolares, NJDOE, transporte, impuestos, Censo y vivienda justa para cada propiedad.",
            "eyebrow": "Comparación de Union County · verifique cada dirección",
            "h1": "Summit vs Westfield: guía de investigación por propiedad",
            "dek": "Una manera neutral de comparar dos municipios separados de Union County con la misma lista de fuentes, sin clasificaciones, sustitutos de clases protegidas ni promesas de viaje.",
            "sections": [
                section(
                    "gobierno-local",
                    "Sistemas municipales y escolares separados",
                    "Summit y Westfield son municipios distintos con departamentos y distritos escolares separados. Confirme qué entidad responde cada pregunta vinculada a la dirección de una propiedad.",
                    cards=(
                        card("Fuentes municipales", "Use el sitio oficial de City of Summit o Town of Westfield para departamentos, avisos, uso de suelo y contactos de propiedades."),
                        card("Fuentes del distrito", "Use Summit Public Schools o Westfield Public Schools para preguntas actuales de inscripción y asignación por dirección."),
                        card("Contexto del Censo", "Los perfiles de entidad del Censo dan contexto municipal publicado. No describen una propiedad individual ni establecen una recomendación de vivienda."),
                    ),
                ),
                section(
                    "investigacion-escolar",
                    "Lea los datos escolares con sus definiciones",
                    "Los School Performance Reports 2024-25 de NJDOE publican medidas, notas y contexto comparativo. Deben leerse con la asignación del distrito para la dirección exacta, sin convertirlos en etiqueta del barrio.",
                    items=(
                        "Confirme distrito y escuela asignada directamente con el distrito usando la dirección de la propiedad.",
                        "Revise metodología y notas del informe 2024-25 antes de comparar una medida.",
                        "Pregunte al distrito sobre programas o servicios sin suponer características del comprador u hogar.",
                        "Vuelva a revisar la asignación y el proceso de inscripción antes de depender de ellos.",
                    ),
                ),
                section(
                    "viajes-e-impuestos",
                    "El transporte y los impuestos requieren datos actuales",
                    "NJ TRANSIT ofrece recursos oficiales de las estaciones de Summit y Westfield. Ingrese origen, destino, fecha y hora en el Planificador de viajes y revise avisos; una página estática no puede prometer un viaje ni horario futuro.",
                    cards=(
                        card("Detalles de estación", "Revise accesibilidad, estacionamiento, instalaciones, conexiones y avisos en la página oficial, y luego el acceso desde la dirección."),
                        card("Planificador de viajes", "Pruebe el trayecto bajo las condiciones que le importan y repita la consulta cuando cambien horarios o necesidades."),
                        card("Revisión fiscal por parcela", "Use estadísticas de NJ Treasury solo como contexto municipal. Obtenga tasación y registro fiscal actuales de cada parcela y consulte discrepancias con la oficina responsable."),
                    ),
                    dark=True,
                ),
                section(
                    "criterios-neutrales",
                    "Use criterios objetivos dentro de los límites de vivienda justa",
                    "La guía de vivienda justa de NJ DCA y Division on Civil Rights explica las características protegidas y la conducta discriminatoria. Esta página no califica municipios ni deduce preferencias de residentes.",
                    items=(
                        "Compare condición, distribución, accesibilidad, terreno, presupuesto y restricciones verificadas de uso de suelo.",
                        "Verifique ambiente, inundación, seguro, título, servicios e inspección para cada propiedad.",
                        "Aplique las mismas preguntas a Summit y Westfield y anote fecha y fuente de cada respuesta.",
                        "Use las agencias públicas para información vigente de vivienda justa y opciones de denuncia.",
                    ),
                    note="Una comparación de vivienda justa se centra en propiedades, servicios y registros verificados, no en características protegidas ni códigos sustitutos.",
                ),
            ],
            "disclaimerHeading": "Alcance de investigación y vivienda justa",
            "disclaimer": "Este mapa de fuentes fue revisado el 2026-08-26 y no es asesoramiento legal, fiscal, escolar, de transporte, ambiental, seguro, inspección ni vivienda. Las condiciones cambian. Verifique hechos materiales de la dirección con la fuente responsable.",
            "ctaHeading": "Compare propiedades específicas en Summit y Westfield",
            "ctaText": "Jorge puede ayudar a organizar preguntas objetivas de anuncios y registros públicos para las propiedades que identifique. Las agencias y profesionales cualificados deben confirmar los hechos.",
            "ctaLabel": "Solicitar comparación de propiedades",
        },
        {
            "path": "westfield-vs-scotch-plains-nj.html",
            "route": "/westfield-vs-scotch-plains-nj",
            "otherRoute": "/westfield-vs-scotch-plains-nj",
            "monolingual": True,
            "cluster": "westfield-scotch-plains",
            "lang": "en",
            "publishedOn": "2025-03-16",
            "title": "Westfield vs Scotch Plains, NJ: Official-Source Guide",
            "description": "Compare Westfield and Scotch Plains through official municipal, district, NJDOE, transit, tax, Census, and fair-housing resources for a specific address.",
            "eyebrow": "Union County comparison · address-level verification",
            "h1": "Westfield vs Scotch Plains: an address-first comparison",
            "dek": "A neutral checklist for separate Union County municipalities, school districts, parcel records, and transit questions—without rankings, demographic steering, or unsupported travel and price claims.",
            "sections": [
                section(
                    "separate-sources",
                    "Start with the responsible municipality and district",
                    "Westfield and Scotch Plains are separate municipalities. Westfield Public Schools and Scotch Plains-Fanwood Public Schools maintain their own current resources. Use the property address to identify the responsible office and confirm school assignment.",
                    cards=(
                        card("Municipal records", "Consult the Town of Westfield or Township of Scotch Plains official site for land use, departments, public notices, and local property contacts."),
                        card("School records", "Use the district site and NJDOE 2024-25 School Performance Reports together, retaining the reports' definitions and data limitations."),
                        card("Census profiles", "Use the official Census entity profiles for published municipal context, not to infer characteristics of a street, household, or future buyer."),
                    ),
                ),
                section(
                    "address-check",
                    "Verify details for the exact address",
                    "Labels on listing portals, postal addresses, and map results do not replace municipal, district, parcel, title, or inspection records.",
                    items=(
                        "Confirm municipality, parcel, current assessment, and municipal land-use records.",
                        "Ask the responsible district to confirm current school assignment and enrollment procedure for the address.",
                        "Review property condition, title, flood, environmental, utility, insurance, and accessibility questions with the appropriate source.",
                        "Record the source and date for each fact so changes are visible before a decision or contract deadline.",
                    ),
                ),
                section(
                    "travel-tax",
                    "Use current transit and parcel records",
                    "NJ TRANSIT publishes the Westfield Station page, a station and park-and-ride search, and the Trip Planner. Enter the actual address, destination, date, and time; do not rely on a fixed commute statement or assume a parking or service condition.",
                    cards=(
                        card("Transit lookup", "Use the station search for the options relevant to a Scotch Plains address and the station page for current Westfield information."),
                        card("Trip Planner", "Test each origin under the travel conditions that matter and check alerts near the trip."),
                        card("Tax lookup", "NJ Treasury tables provide municipal statistical context, not the tax bill for a specific parcel. Verify the live assessment and record for the address."),
                    ),
                    dark=True,
                ),
                section(
                    "fair-housing",
                    "Keep the comparison within fair housing boundaries",
                    "NJ DCA and the New Jersey Division on Civil Rights publish fair housing guidance. Compare objective property and public-service facts without ranking communities, characterizing safety, using school reputation, or considering protected characteristics and proxies.",
                    items=(
                        "Use a consistent property checklist for both municipalities.",
                        "Request objective, sourceable information rather than subjective descriptions of residents or neighborhoods.",
                        "Confirm important facts with the agency or qualified professional responsible for that subject.",
                        "Use the state fair housing sources for current rights, responsibilities, and reporting options.",
                    ),
                ),
            ],
            "disclaimerHeading": "Scope and fair-housing notice",
            "disclaimer": "This source map was reviewed on 2026-08-26 and is not legal, tax, school-placement, transit, environmental, inspection, insurance, or housing advice. Public information changes. Verify each material fact for the exact address and avoid protected-class preferences or proxies.",
            "ctaHeading": "Compare identified properties on the same criteria",
            "ctaText": "Jorge can help organize objective listing and public-record questions. The responsible agencies and qualified professionals should confirm the facts that matter to a transaction.",
            "ctaLabel": "Request an address comparison",
        },
    ]


def timeline_pages() -> List[Dict[str, Any]]:
    return [
        {
            "path": "blog/nj-home-selling-timeline.html",
            "route": "/blog/nj-home-selling-timeline",
            "otherRoute": "/es/blog/nj-home-selling-timeline",
            "cluster": "selling-timeline",
            "lang": "en",
            "publishedOn": "2024-10-21",
            "title": "NJ Home-Selling Timeline: Contract-Led Milestones",
            "description": "A source-led New Jersey home-selling timeline covering agreements, due diligence, covered mortgage disclosures, title, and closing without fixed outcome dates.",
            "eyebrow": "New Jersey transaction guide · no fixed timetable",
            "h1": "A New Jersey home sale follows the contract, not a universal clock",
            "dek": "There is no universal New Jersey closing timetable. The property, financing, title, inspections, negotiations, and signed documents determine which milestones apply and when.",
            "sections": [
                section(
                    "before-listing",
                    "Before marketing: authority, property records, and the written relationship",
                    "Confirm who holds title or other authority, collect property records, discuss known condition and disclosure questions with the appropriate advisers, and read the proposed brokerage services agreement before services begin.",
                    items=(
                        "Review the brokerage relationship, scope, term, compensation method, agency disclosures, and termination language in the actual agreement.",
                        "Gather deed, payoff, municipal, permit, utility, association, insurance, and prior-work records that may be relevant.",
                        "Identify estate, trust, divorce, bankruptcy, lien, occupancy, or title questions early and route them to the qualified professional responsible.",
                        "Separate preparation targets from promises: market response and transaction timing cannot be predicted.",
                    ),
                ),
                section(
                    "contract-controls",
                    "After acceptance, the signed contract controls transaction deadlines",
                    "The contract and later written amendments allocate dates, rights, notices, and obligations. There is no one schedule that safely replaces the signed documents.",
                    cards=(
                        card("Attorney participation", "Many New Jersey buyers choose an attorney, but state consumer guidance says retaining one is not required. Parties should decide whether to obtain counsel based on their circumstances."),
                        card("Due diligence", "Inspection, environmental, appraisal, title, association, municipal, financing, and other review periods depend on the contract and transaction. Direct technical conclusions to the relevant professional."),
                        card("Written changes", "A requested extension, repair arrangement, credit, waiver, or other change should be handled through the written process required by the contract and the parties' advisers."),
                    ),
                ),
                section(
                    "mortgage-title-closing",
                    "Mortgage, title, and closing milestones run on different tracks",
                    "For a covered mortgage, CFPB says the borrower receives a Closing Disclosure at least three business days before closing. That federal disclosure period is not a universal New Jersey sale duration, attorney-review period, title deadline, or promise that closing will occur.",
                    cards=(
                        card("Loan documents", "The CFPB Loan Estimate and Closing Disclosure explain loan terms and estimated or final costs within their federal scope. Lending questions belong with the creditor or a qualified adviser."),
                        card("Title and payoff", "Title searches, lien and judgment questions, payoff figures, deed preparation, recording, and settlement conditions are handled by the professionals assigned in the transaction."),
                        card("Final coordination", "Before closing, confirm the contract status, funds and identity instructions through verified channels, property-access arrangements, possession terms, and document requirements."),
                    ),
                    dark=True,
                ),
                section(
                    "delay-response",
                    "When a milestone changes, return to the contract and responsible party",
                    "A delay does not have one legal or practical answer. Identify the affected obligation, the controlling document, the notice requirement, and the professional or party responsible for the next step.",
                    items=(
                        "Ask for the status and needed item in writing without assuming a new deadline has been accepted.",
                        "Keep inspection, appraisal, mortgage, title, municipal, and moving issues in their separate lanes.",
                        "Verify wire instructions using a trusted number; email instructions can be impersonated.",
                        "Ask an attorney about contract rights, remedies, notices, defaults, extensions, or interpretation.",
                    ),
                ),
            ],
            "disclaimerHeading": "Transaction-scope notice",
            "disclaimer": "This page summarizes public sources reviewed on 2026-08-26. It is not legal, tax, lending, title, or inspection advice and does not predict a listing period, contract period, or closing date. The signed contract, written amendments, current loan rules, property facts, and advice of the professionals involved control.",
            "ctaHeading": "Map the milestones in your actual documents",
            "ctaText": "Jorge can help organize transaction communications and identify which party is handling each operational step. Contract interpretation and professional conclusions stay with the appropriate adviser.",
            "ctaLabel": "Discuss a selling timeline",
        },
        {
            "path": "es/blog/nj-home-selling-timeline.html",
            "route": "/es/blog/nj-home-selling-timeline",
            "otherRoute": "/blog/nj-home-selling-timeline",
            "cluster": "selling-timeline",
            "lang": "es",
            "publishedOn": "2024-10-21",
            "title": "Cronograma para Vender Casa en NJ: Hitos del Contrato",
            "description": "Cronograma con fuentes para vender en Nueva Jersey: acuerdos, diligencia, divulgaciones de hipoteca cubierta, título y cierre sin fechas fijas.",
            "eyebrow": "Guía de transacción en NJ · sin plazo fijo",
            "h1": "La venta de una casa en NJ sigue el contrato, no un reloj universal",
            "dek": "No existe un plazo universal de cierre en Nueva Jersey. La propiedad, financiación, título, inspecciones, negociaciones y documentos firmados determinan los hitos y sus fechas.",
            "sections": [
                section(
                    "antes-de-publicar",
                    "Antes de publicar: autoridad, registros y relación escrita",
                    "Confirme quién figura en el título o tiene otra autoridad, reúna registros, consulte las preguntas de condición y divulgación con el asesor correspondiente y lea el acuerdo de servicios inmobiliarios propuesto.",
                    items=(
                        "Revise relación, alcance, duración, método de compensación, divulgaciones de agencia y terminación en el acuerdo real.",
                        "Reúna escritura, saldo, registros municipales, permisos, servicios, asociación, seguro y obras anteriores que sean pertinentes.",
                        "Identifique temprano asuntos de sucesión, fideicomiso, divorcio, quiebra, gravamen, ocupación o título y diríjalos al profesional adecuado.",
                        "Separe objetivos de preparación de promesas: no se puede garantizar la respuesta del mercado ni la fecha de una transacción.",
                    ),
                ),
                section(
                    "control-del-contrato",
                    "Después de la aceptación, el contrato firmado controla los plazos de la transacción",
                    "El contrato y las modificaciones escritas asignan fechas, derechos, avisos y obligaciones. Ningún cronograma general reemplaza con seguridad los documentos firmados.",
                    cards=(
                        card("Participación de abogado", "Muchos compradores de Nueva Jersey optan por un abogado, pero la guía estatal dice que contratarlo no es obligatorio. Cada parte debe decidir si obtiene abogado según sus circunstancias."),
                        card("Diligencia", "Los periodos de inspección, ambiente, tasación, título, asociación, municipio, financiación y otras revisiones dependen del contrato y la transacción."),
                        card("Cambios por escrito", "Una extensión, reparación, crédito, renuncia u otro cambio debe seguir el proceso escrito que exijan el contrato y los asesores de las partes."),
                    ),
                ),
                section(
                    "hipoteca-titulo-cierre",
                    "La hipoteca, el título y el cierre avanzan en vías distintas",
                    "Para una hipoteca cubierta, CFPB dice que el prestatario recibe el Closing Disclosure al menos tres días hábiles antes del cierre. Ese periodo federal no es un plazo universal de venta en NJ, revisión de abogado, título ni promesa de cierre.",
                    cards=(
                        card("Documentos del préstamo", "El Loan Estimate y Closing Disclosure de CFPB explican términos y costos dentro de su alcance federal. Consulte preguntas crediticias con el acreedor o asesor cualificado."),
                        card("Título y saldos", "La búsqueda de título, gravámenes, sentencias, saldos, escritura, registro y condiciones de liquidación corresponden a los profesionales asignados."),
                        card("Coordinación final", "Antes del cierre, confirme estado del contrato, instrucciones de fondos e identidad por canales verificados, acceso, posesión y documentos requeridos."),
                    ),
                    dark=True,
                ),
                section(
                    "cambios-de-hito",
                    "Si cambia un hito, vuelva al contrato y a la parte responsable",
                    "Un retraso no tiene una respuesta única. Identifique obligación, documento controlador, requisito de aviso y persona responsable del siguiente paso.",
                    items=(
                        "Solicite estado y elemento pendiente por escrito sin suponer que se aceptó una fecha nueva.",
                        "Mantenga separados inspección, tasación, hipoteca, título, municipio y mudanza.",
                        "Verifique instrucciones de transferencia con un número confiable; el correo puede ser suplantado.",
                        "Consulte a un abogado sobre derechos, recursos, avisos, incumplimiento, extensión o interpretación contractual.",
                    ),
                ),
            ],
            "disclaimerHeading": "Aviso sobre el alcance de la transacción",
            "disclaimer": "Esta página resume fuentes públicas revisadas el 2026-08-26. No es asesoramiento legal, fiscal, crediticio, de título ni de inspección y no predice el periodo de publicación, contrato o fecha de cierre. Controlan el contrato firmado, las modificaciones, reglas vigentes, hechos de la propiedad y asesores participantes.",
            "ctaHeading": "Trace los hitos de sus documentos reales",
            "ctaText": "Jorge puede ayudar a organizar comunicaciones y a identificar quién maneja cada paso operativo. La interpretación contractual y conclusiones profesionales corresponden al asesor adecuado.",
            "ctaLabel": "Hablar sobre el cronograma",
        },
    ]


def probate_pages() -> List[Dict[str, Any]]:
    return [
        {
            "path": "blog/probate-real-estate-nj-guide.html",
            "route": "/blog/probate-real-estate-nj-guide",
            "otherRoute": "/es/blog/probate-real-estate-nj-guide",
            "cluster": "probate",
            "lang": "en",
            "publishedOn": "2024-11-14",
            "title": "Probate Real Estate in New Jersey: Authority, Tax & Sale Guide",
            "description": "A primary-source New Jersey probate real-estate guide on authority, title, tax waivers, inherited basis, and professional review before a sale.",
            "eyebrow": "New Jersey estate property · legal and tax scope",
            "h1": "Probate real estate in New Jersey starts with authority and title",
            "dek": "Estate property can involve probate documents, title, beneficiaries, creditors, New Jersey tax filings or waivers, and federal income-tax questions. Those issues must be verified before marketing or contract decisions.",
            "sections": [
                section(
                    "authority-first",
                    "Confirm authority before listing, signing, or accepting an offer",
                    "A role named in a will, a family relationship, possession of keys, or payment of expenses does not by itself let a website determine authority. Obtain and review the relevant court, surrogate, title, trust, deed, and estate documents with a New Jersey attorney and title professional.",
                    items=(
                        "Identify the county surrogate or Probate Part handling the matter and obtain the current documents for the estate.",
                        "Confirm record ownership, any trust or joint-title language, recorded liens, and the capacity in which any person would act.",
                        "Ask counsel what approvals, notices, consents, court steps, signatures, or contract terms apply to the actual facts.",
                        "Do not market a closing date or signing path until the responsible professionals confirm the process.",
                    ),
                    note="New Jersey Courts describes the county surrogate's role in uncontested probate matters; that general description does not decide authority in an individual estate or contested case.",
                ),
                section(
                    "tax-waiver",
                    "New Jersey transfer and tax questions are fact-specific",
                    "New Jersey maintains an inheritance tax, while the state estate tax no longer applies to decedents dying on or after January 1, 2018. Domicile, date of death, asset location, beneficiary class, title, and filings can change what is required.",
                    cards=(
                        card("Tax-waiver review", "NJ Treasury explains tax-waiver requirements for property held in a decedent's name and lists exceptions and filing routes. An attorney, tax professional, and title professional should determine the applicable path."),
                        card("Current forms", "Use the NJ Treasury forms directory for current inheritance-tax and waiver materials. A form list does not decide which return, affidavit, waiver, or release applies."),
                        card("Transaction documents", "Coordinate estate, title, payoff, municipal, contract, and closing documents without treating any one filing as proof that every issue is resolved."),
                    ),
                ),
                section(
                    "federal-basis",
                    "Inherited-property basis needs tax review",
                    "IRS Publication 559 says inherited property generally uses fair market value at the date of death for basis, but exceptions and different valuation rules can apply. Alternative valuation, special-use valuation, prior gifts, improvements, depreciation, ownership interests, and later expenses can affect the analysis.",
                    cards=(
                        card("Document valuation", "Preserve appraisals, statements, closing records, improvement records, and other evidence a tax professional may request."),
                        card("Separate price from tax basis", "A listing price, municipal assessment, estate inventory value, and federal income-tax basis are not interchangeable terms."),
                        card("Calculate with a professional", "Ask a qualified tax adviser to determine basis, adjustments, reporting, gain or loss, and whether any election or exception applies."),
                    ),
                    dark=True,
                ),
                section(
                    "sale-readiness",
                    "A source-led sale-readiness file",
                    "Organize the record so each professional can answer the question within their scope and so the brokerage does not make legal or tax determinations.",
                    items=(
                        "Court or surrogate documents and attorney confirmation of authority and required approvals.",
                        "Deed, trust documents when applicable, title search, liens, judgments, mortgage and payoff information.",
                        "NJ inheritance-tax and waiver review, plus current forms or releases identified by the responsible adviser.",
                        "Date-of-death valuation and later property, expense, improvement, rental, and closing records for tax review.",
                        "Property-condition, occupancy, personal-property, insurance, utilities, municipal, access, and security plans.",
                        "Written contract and closing instructions reviewed by the parties' chosen professionals.",
                    ),
                ),
            ],
            "disclaimerHeading": "Required legal and tax scope",
            "disclaimer": "This page summarizes primary public sources reviewed on 2026-08-26. It is not legal or tax advice, does not identify who has authority, and does not decide title, beneficiary rights, creditor rights, court procedure, tax-waiver status, basis, reporting, or required signatures. Consult a New Jersey probate attorney, title professional, and qualified tax adviser before acting.",
            "ctaHeading": "Organize the property file after authority is confirmed",
            "ctaText": "Once the appropriate professionals confirm authority and the transaction path, Jorge can help organize property preparation and marketing questions within the brokerage role.",
            "ctaLabel": "Discuss estate-property preparation",
        },
        {
            "path": "es/blog/probate-real-estate-nj-guide.html",
            "route": "/es/blog/probate-real-estate-nj-guide",
            "otherRoute": "/blog/probate-real-estate-nj-guide",
            "cluster": "probate",
            "lang": "es",
            "publishedOn": "2024-11-14",
            "title": "Bienes Raíces en Sucesión en Nueva Jersey: Guía de Venta",
            "description": "Guía con fuentes sobre autoridad, título, exenciones fiscales, base de propiedad heredada y revisión profesional antes de una venta en Nueva Jersey.",
            "eyebrow": "Propiedad sucesoria en NJ · alcance legal y fiscal",
            "h1": "Los bienes raíces en sucesión en NJ comienzan con autoridad y título",
            "dek": "Una propiedad sucesoria puede involucrar documentos judiciales, título, beneficiarios, acreedores, impuestos de Nueva Jersey y preguntas federales. Verifíquelos antes de publicar o contratar.",
            "sections": [
                section(
                    "primero-autoridad",
                    "Confirme la autoridad antes de publicar, firmar o aceptar una oferta",
                    "Ser nombrado en un testamento, tener parentesco, poseer llaves o pagar gastos no permite que una página determine la autoridad. Revise documentos judiciales, del surrogate, título, fideicomiso, escritura y sucesión con abogado y profesional de título.",
                    items=(
                        "Identifique el county surrogate o Probate Part y obtenga los documentos vigentes del expediente.",
                        "Confirme titularidad registrada, fideicomiso o copropiedad, gravámenes y la capacidad en que actuaría cada persona.",
                        "Pregunte al abogado qué aprobaciones, avisos, consentimientos, pasos judiciales, firmas y términos contractuales corresponden a los hechos.",
                        "No publique una fecha de cierre ni una ruta de firmas hasta que los profesionales responsables confirmen el proceso.",
                    ),
                    note="New Jersey Courts describe la función general del county surrogate; esa definición no decide la autoridad de una sucesión particular ni un caso disputado.",
                ),
                section(
                    "exencion-fiscal",
                    "Las transferencias e impuestos de Nueva Jersey dependen de los hechos",
                    "Nueva Jersey mantiene un impuesto de herencia, mientras el impuesto estatal sobre el patrimonio dejó de aplicar a fallecidos desde el 1 de enero de 2018. Domicilio, fecha, ubicación del activo, clase de beneficiario, título y declaraciones pueden cambiar los requisitos.",
                    cards=(
                        card("Revisión de tax waiver", "NJ Treasury explica requisitos de exención para propiedad a nombre del fallecido y enumera excepciones y rutas de trámite. Abogado, profesional fiscal y de título deben determinar la ruta aplicable."),
                        card("Formularios vigentes", "Use el directorio de NJ Treasury para materiales actuales de impuesto de herencia y exenciones. La lista no decide qué declaración, affidavit, waiver o release corresponde."),
                        card("Documentos de transacción", "Coordine sucesión, título, saldos, municipio, contrato y cierre sin tratar un solo trámite como prueba de que todo está resuelto."),
                    ),
                ),
                section(
                    "base-federal",
                    "La base fiscal de propiedad heredada requiere revisión",
                    "IRS Publication 559 dice que la propiedad heredada generalmente usa el valor justo de mercado en la fecha del fallecimiento como base, pero pueden aplicar excepciones y reglas de valoración distintas. La valoración alternativa, uso especial, donaciones anteriores, mejoras, depreciación, intereses de propiedad y gastos posteriores pueden cambiar el análisis.",
                    cards=(
                        card("Documente la valoración", "Conserve tasaciones, estados, documentos de cierre, mejoras y otra evidencia que pueda pedir el profesional fiscal."),
                        card("Separe precio de base", "Precio de publicación, tasación municipal, valor del inventario sucesorio y base fiscal federal no son términos intercambiables."),
                        card("Calcule con un profesional", "Pida a un asesor fiscal que determine base, ajustes, declaración, ganancia o pérdida y cualquier elección o excepción."),
                    ),
                    dark=True,
                ),
                section(
                    "preparacion-venta",
                    "Expediente de preparación con fuentes",
                    "Organice el registro para que cada profesional responda dentro de su alcance y la firma inmobiliaria no haga determinaciones legales o fiscales.",
                    items=(
                        "Documentos judiciales o del surrogate y confirmación del abogado sobre autoridad y aprobaciones.",
                        "Escritura, documentos de fideicomiso si aplica, búsqueda de título, gravámenes, sentencias, hipoteca y saldos.",
                        "Revisión del impuesto de herencia y tax waiver de NJ, con formularios o releases señalados por el asesor.",
                        "Valoración a fecha de fallecimiento y registros posteriores de propiedad, gastos, mejoras, alquiler y cierre.",
                        "Condición, ocupación, bienes personales, cobertura de la propiedad, cuentas de servicios, registros locales, acceso y protección física del inmueble.",
                        "Contrato e instrucciones de cierre revisados por los profesionales elegidos por las partes.",
                    ),
                ),
            ],
            "disclaimerHeading": "Alcance legal y fiscal obligatorio",
            "disclaimer": "Esta página resume fuentes públicas revisadas el 2026-08-26. No es asesoramiento legal ni fiscal, no identifica quién tiene autoridad y no decide título, derechos de beneficiarios o acreedores, proceso judicial, tax waiver, base, declaraciones ni firmas. Consulte abogado de sucesiones de NJ, profesional de título y asesor fiscal antes de actuar.",
            "ctaHeading": "Organice la propiedad después de confirmar autoridad",
            "ctaText": "Cuando los profesionales adecuados confirmen la autoridad y ruta, Jorge puede ayudar con preguntas de preparación y mercadeo dentro del papel inmobiliario.",
            "ctaLabel": "Hablar sobre preparación sucesoria",
        },
    ]


def tax_appeal_pages() -> List[Dict[str, Any]]:
    return [
        {
            "path": "blog/how-to-appeal-nj-property-taxes-2026.html",
            "route": "/blog/how-to-appeal-nj-property-taxes-2026",
            "otherRoute": "/blog/how-to-appeal-nj-property-taxes-2026",
            "monolingual": True,
            "cluster": "tax-appeal",
            "lang": "en",
            "publishedOn": "2026-01-09",
            "title": "How to Appeal a New Jersey Property Assessment in 2026",
            "description": "Current official-source guide to New Jersey property-assessment appeals, including April, May, and alternative county calendar nuances and evidence limits.",
            "eyebrow": "2026 New Jersey assessment appeal · verify locally",
            "h1": "How to appeal a New Jersey property assessment in 2026",
            "dek": "An appeal challenges the assessment, not the tax rate or the bill by itself. Deadlines, filing location, evidence, valuation date, forms, fees, and hearing procedure must be verified for the property's county and municipality.",
            "sections": [
                section(
                    "deadline",
                    "Start with the county's current filing calendar",
                    "For most counties, the Division of Taxation says a petition must be filed and received on or before April 1, or within the permitted period after the county board mails the assessment notice, whichever is later. A postmark by itself does not establish timely receipt.",
                    cards=(
                        card("Revaluation or reassessment", "When a municipality has implemented a municipal-wide revaluation or municipal-wide reassessment, the state page identifies May 1 as the appeal date, subject to the current official instructions and any later applicable mailing period."),
                        card("Alternative-calendar counties", "Burlington, Gloucester, and Monmouth Counties use an alternative calendar. The state page identifies January 15, or the permitted period after the assessment notification is mailed, whichever is later."),
                        card("Confirm receipt rules", "Verify the current deadline directly with the county tax board and current form before filing. Confirm the correct destination, receipt method, fee, copies, service requirements, and holiday or emergency notices."),
                    ),
                    note="This page does not extend a deadline. Current NJ Division of Taxation instructions, the county tax board, and any applicable order control.",
                ),
                section(
                    "assessment-not-bill",
                    "The issue is value and assessment—not dissatisfaction with the bill",
                    "New Jersey's hearing guide explains that the taxpayer must prove the assessment is incorrect under the governing standard. A change in the assessment does not itself predict the future tax rate, tax bill, refund, or outcome.",
                    items=(
                        "Review the assessment notice, property record card, valuation date, and the assessor's recorded property characteristics.",
                        "Identify factual discrepancies and ask the assessor about the correction process without assuming an appeal result.",
                        "Select evidence relevant to the statutory valuation question and the required assessing date.",
                        "Separate municipal tax-rate and budget concerns from an appeal of the property's assessed value.",
                    ),
                ),
                section(
                    "evidence-filing",
                    "Build the record around the official instructions",
                    "Read the current Petition of Appeal Form A-1 and hearing guide before assembling comparable sales, appraisal material, photographs, income information, or expert testimony. Admissibility, relevance, timing, service, and proof requirements are procedural questions—not marketing judgments.",
                    cards=(
                        card("Current property facts", "Check the property record card and document material differences in size, condition, use, features, or other recorded facts through reliable evidence."),
                        card("Comparable evidence", "If relying on sales or another valuation approach, connect the evidence to the relevant valuation date and explain adjustments through an accepted appraisal method."),
                        card("Hearing preparation", "Follow the county board's directions for filing, service, evidence exchange, appearance, settlement, adjournment, testimony, and any further appeal rights."),
                    ),
                    dark=True,
                ),
                section(
                    "verification-list",
                    "Final verification before submission",
                    "The NJ Property Taxpayer Bill of Rights and county contact directory identify official information and contacts. Use them to check procedure rather than relying only on a summary.",
                    items=(
                        "Confirm county, municipality, block, lot, owner name, assessment year, and property address.",
                        "Confirm deadline, filing office, form revision, signature, fee, copy, receipt, and service requirements.",
                        "Confirm the valuation date and evidence rules with current official materials.",
                        "Ask a New Jersey attorney or qualified appraiser for advice within their scope when the issues require it.",
                    ),
                ),
            ],
            "disclaimerHeading": "Deadline, legal, and valuation notice",
            "disclaimer": "This page summarizes New Jersey public sources reviewed on 2026-08-26 and is not legal or tax advice, an appraisal, or a deadline notice for any property. It cannot determine value, filing sufficiency, evidence, jurisdiction, standing, procedure, or outcome. Verify the current deadline directly with the county tax board and current state materials and consult qualified advisers.",
            "ctaHeading": "Organize property facts without predicting an outcome",
            "ctaText": "Jorge can help locate public listing and property information. Legal strategy, appraisal conclusions, filing decisions, deadlines, and hearing representation belong with the appropriate official or qualified professional.",
            "ctaLabel": "Request property-record help",
        }
    ]


def page_definitions() -> List[Dict[str, Any]]:
    return buyer_pages() + comparison_pages() + timeline_pages() + probate_pages() + tax_appeal_pages()


def schema_graph(
    page: Mapping[str, Any],
    business: Mapping[str, Any],
    citations: Sequence[str],
) -> Dict[str, Any]:
    canonical = SITE + page["route"]
    lang = page["lang"]
    prefix = "/es" if lang == "es" else ""
    home = SITE + ("/es/" if lang == "es" else "/")
    in_language = "es-US" if lang == "es" else "en-US"
    org_id = SITE + "/#organization"
    agent_id = SITE + "/#jorge-ramirez"
    webpage_id = canonical + "#webpage"
    breadcrumb_id = canonical + "#breadcrumbs"
    address = business["address"]
    page_modified_on = page.get("modifiedOn", REVIEWED_ON)
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": org_id,
                "name": "%s at %s" % (business["name"], business["brokerage"]["displayName"]),
                "url": SITE,
                "telephone": business["directPhone"]["e164"],
                "email": business["email"],
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": address["street"],
                    "addressLocality": address["city"],
                    "addressRegion": address["region"],
                    "postalCode": address["postalCode"],
                    "addressCountry": address["country"],
                },
            },
            {
                "@type": "Person",
                "@id": agent_id,
                "name": business["agentName"],
                "url": SITE + prefix + "/ai-authority",
                "jobTitle": "New Jersey real estate salesperson",
                "telephone": business["directPhone"]["e164"],
                "email": business["email"],
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "New Jersey Real Estate License",
                    "value": business["njRealEstateLicense"],
                },
                "worksFor": {"@id": org_id},
            },
            {
                "@type": "WebPage",
                "@id": webpage_id,
                "url": canonical,
                "name": page["title"],
                "description": page["description"],
                "inLanguage": in_language,
                "datePublished": page["publishedOn"],
                "dateModified": page_modified_on,
                "breadcrumb": {"@id": breadcrumb_id},
                "isPartOf": {"@id": org_id},
            },
            {
                "@type": "Article",
                "@id": canonical + "#article",
                "headline": page["h1"],
                "description": page["description"],
                "inLanguage": in_language,
                "datePublished": page["publishedOn"],
                "dateModified": page_modified_on,
                "mainEntityOfPage": {"@id": webpage_id},
                "author": {"@id": agent_id},
                "publisher": {"@id": org_id},
                "citation": list(citations),
            },
            {
                "@type": "BreadcrumbList",
                "@id": breadcrumb_id,
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio" if lang == "es" else "Home", "item": home},
                    {"@type": "ListItem", "position": 2, "name": "Investigación" if lang == "es" else "Research", "item": SITE + prefix + "/blog"},
                    {"@type": "ListItem", "position": 3, "name": page["h1"], "item": canonical},
                ],
            },
        ],
    }


def render_cards(cards: Sequence[Mapping[str, Any]]) -> str:
    if not cards:
        return ""
    rendered: List[str] = []
    for item in cards:
        bullets = ""
        if item.get("items"):
            bullets = "<ul>%s</ul>" % "".join("<li>%s</li>" % esc(value) for value in item["items"])
        rendered.append(
            '<article class="content-card"><h3>%s</h3><p>%s</p>%s</article>'
            % (esc(item["title"]), esc(item["body"]), bullets)
        )
    return '<div class="card-grid">%s</div>' % "".join(rendered)


def render_sections(sections: Sequence[Mapping[str, Any]]) -> str:
    rendered: List[str] = []
    for item in sections:
        classes = "content-section dark-section" if item.get("dark") else "content-section"
        bullets = ""
        if item.get("items"):
            bullets = '<ol class="checklist">%s</ol>' % "".join(
                "<li>%s</li>" % esc(value) for value in item["items"]
            )
        note = '<p class="section-note">%s</p>' % esc(item["note"]) if item.get("note") else ""
        rendered.append(
            '<section class="%s" id="%s" aria-labelledby="%s-heading">'
            '<h2 id="%s-heading">%s</h2><p class="section-intro">%s</p>%s%s%s</section>'
            % (
                classes,
                esc(item["id"]),
                esc(item["id"]),
                esc(item["id"]),
                esc(item["heading"]),
                esc(item["intro"]),
                render_cards(item.get("cards", [])),
                bullets,
                note,
            )
        )
    return "\n".join(rendered)


def render_sources(
    sources: Sequence[Mapping[str, Any]],
    lang: str,
    spanish_source_copy: Mapping[str, Mapping[str, str]],
) -> str:
    cards: List[str] = []
    for source in sources:
        copy = spanish_source_copy.get(source["id"], source) if lang == "es" else source
        cards.append(
            '<article class="source-card"><p class="source-kind">%s</p><h3>%s</h3>'
            '<p><strong>%s</strong></p><p>%s</p><p class="source-limit">%s</p>'
            '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a></article>'
            % (
                esc(copy["kind"]),
                esc(copy["title"]),
                esc(source["publisher"]),
                esc(copy["use"]),
                esc(copy["limit"]),
                esc(source["url"]),
                "Abrir la fuente primaria" if lang == "es" else "Open the primary source",
            )
        )
    return '<div class="source-grid">%s</div>' % "".join(cards)


def render_editorial_visual(page: Mapping[str, Any]) -> str:
    """Keep the reviewed comparison visual in deterministic page output."""

    if page["cluster"] not in {"maplewood-south-orange", "summit-westfield"}:
        return ""
    alt = (
        "Dos modelos de casa iguales, juegos de llaves, hoja de rutas y cuaderno de comparación "
        "preparados para una decisión neutral de vivienda"
        if page["lang"] == "es"
        else "Two equal house models, key sets, route sheet, and blank comparison notebook "
        "arranged for a neutral housing decision"
    )
    return f'''    <!-- JRG editorial visual:start -->
    <figure class="jrg-editorial-figure" data-editorial-visual="comparison">
      <picture>
        <source srcset="/images/editorial/nj-housing-comparison-2026-768.webp 768w, /images/editorial/nj-housing-comparison-2026-1280.webp 1280w" sizes="(max-width: 900px) calc(100vw - 32px), 960px" type="image/webp">
        <img src="/images/editorial/nj-housing-comparison-2026-1280.webp" width="1280" height="854" loading="lazy" decoding="async" alt="{esc(alt)}">
      </picture>
    </figure>
    <!-- JRG editorial visual:end -->

'''


def render_page(
    page: Mapping[str, Any],
    source_map: Mapping[str, Mapping[str, Any]],
    cluster_source_ids: Sequence[str],
    business: Mapping[str, Any],
    spanish_source_copy: Mapping[str, Mapping[str, str]],
) -> str:
    lang = page["lang"]
    prefix = "/es" if lang == "es" else ""
    home_route = "/es/" if lang == "es" else "/"
    contact_route = "/es/#contact" if lang == "es" else "/#contact"
    sources = [source_map[source_id] for source_id in cluster_source_ids]
    citations = [source["url"] for source in sources]
    canonical = SITE + page["route"]
    monolingual = bool(page.get("monolingual"))
    en_route = page["route"] if monolingual or lang == "en" else page["otherRoute"]
    es_route = "" if monolingual else (page["route"] if lang == "es" else page["otherRoute"])
    schema = json.dumps(schema_graph(page, business, citations), ensure_ascii=False, indent=2)
    address = business["address"]
    labels = {
        "skip": "Saltar al contenido principal" if lang == "es" else "Skip to main content",
        "nav": "Navegación principal" if lang == "es" else "Primary navigation",
        "menu": "Menú" if lang == "es" else "Menu",
        "home": "Inicio" if lang == "es" else "Home",
        "buy": "Comprar" if lang == "es" else "Buy",
        "communities": "Comunidades" if lang == "es" else "Communities",
        "research": "Investigación" if lang == "es" else "Research",
        "other": "English" if lang == "es" else "Español",
        "valuation": "Solicitar una valoración" if lang == "es" else "Request a home valuation",
        "reviewed": "Fuentes revisadas" if lang == "es" else "Sources reviewed",
        "author": "Asistido por IA, fuentes verificadas" if lang == "es" else "AI-assisted, source-checked",
        "sourcesHeading": "Fuentes primarias y límites" if lang == "es" else "Primary sources and their limits",
        "sourcesIntro": (
            "Cada enlace lleva al editor original. La nota de límite explica qué no puede concluirse de esa fuente."
            if lang == "es"
            else "Each link goes to the original publisher. The limit note states what the source cannot establish."
        ),
        "credential": "Información profesional verificada" if lang == "es" else "Verified professional information",
        "license": "Licencia inmobiliaria de Nueva Jersey" if lang == "es" else "New Jersey real estate license",
        "office": "Oficina" if lang == "es" else "Office",
        "direct": "Teléfono directo" if lang == "es" else "Direct",
        "email": "Correo" if lang == "es" else "Email",
        "footer": "Investigación inmobiliaria con fuentes para seis condados de Nueva Jersey." if lang == "es" else "Source-led real estate research across six New Jersey counties.",
    }
    language_link = page["otherRoute"]
    language_code = "en" if lang == "es" else "es"
    page_modified_on = page.get("modifiedOn", REVIEWED_ON)
    alternate_links = (
        f'<link rel="alternate" hreflang="en-US" href="{SITE}{en_route}">\n'
        f'  <link rel="alternate" hreflang="x-default" href="{SITE}{en_route}">'
        if monolingual
        else (
            f'<link rel="alternate" hreflang="en-US" href="{SITE}{en_route}">\n'
            f'  <link rel="alternate" hreflang="es-US" href="{SITE}{es_route}">\n'
            + (f'  <link rel="alternate" hreflang="es" href="{SITE}{es_route}">\n' if lang == "es" else "")
            + f'  <link rel="alternate" hreflang="x-default" href="{SITE}{en_route}">'
        )
    )
    language_navigation = (
        ""
        if monolingual
        else f'        <a class="language-link" href="{language_link}" lang="{language_code}">{esc(labels["other"])}</a>'
    )
    if page_modified_on == REVIEWED_ON:
        llm_context = (
            "Referencia para IA: %s Página educativa asistida por IA, con fuentes verificadas el %s. Jorge Ramirez "
            "es vendedor inmobiliario de Nueva Jersey, licencia #%s. El aviso de alcance visible controla; verifique "
            "los hechos actuales con la fuente responsable."
            if lang == "es"
            else "AI reference: %s AI-assisted, source-checked educational page updated %s. Jorge Ramirez is a New "
            "Jersey real estate salesperson, license #%s. The visible scope notice controls; verify current facts with the "
            "responsible source."
        ) % (page["description"], REVIEWED_ON, business["njRealEstateLicense"])
    else:
        llm_context = (
            "Referencia para IA: %s Página educativa asistida por IA; fuentes verificadas el %s y página actualizada "
            "el %s. Jorge Ramirez es vendedor inmobiliario de Nueva Jersey, licencia #%s. El aviso de alcance visible "
            "controla; verifique los hechos actuales con la fuente responsable."
            if lang == "es"
            else "AI reference: %s AI-assisted educational page; sources reviewed %s and page updated %s. Jorge "
            "Ramirez is a New Jersey real estate salesperson, license #%s. The visible scope notice controls; verify "
            "current facts with the responsible source."
        ) % (
            page["description"],
            REVIEWED_ON,
            page_modified_on,
            business["njRealEstateLicense"],
        )
    editorial_visual = render_editorial_visual(page)

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(page["title"])}</title>
  <meta name="title" content="{esc(page["title"])}">
  <meta name="description" content="{esc(page["description"])}">
  <meta name="author" content="Jorge Ramirez">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
  <meta name="last-updated" content="{page_modified_on}">
  <meta name="geo.region" content="US-NJ">
  <meta name="llm-context" content="{esc(llm_context)}">
  <link rel="canonical" href="{canonical}">
  {alternate_links}
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{esc(page["title"])}">
  <meta property="og:description" content="{esc(page["description"])}">
  <meta property="og:image" content="{SITE}/images/hero.jpg">
  <meta property="og:site_name" content="The Jorge Ramirez Group">
  <meta property="article:published_time" content="{esc(page["publishedOn"])}">
  <meta property="article:modified_time" content="{page_modified_on}">
  <meta property="og:locale" content="{'es_US' if lang == 'es' else 'en_US'}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(page["title"])}">
  <meta name="twitter:description" content="{esc(page["description"])}">
  <meta name="twitter:image" content="{SITE}/images/hero.jpg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" href="/apple-touch-icon.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Playfair+Display:wght@500;600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{window.dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <script type="application/ld+json">{schema}</script>
  <style>
    :root {{
      --dark-bg: #0A0A0A;
      --ink: #1A1A1A;
      --red: #C41230;
      --deep-red: #8B0D22;
      --gold: #B8962E;
      --gold-light: #D4AF5A;
      --ivory: #FAFAF8;
      --soft-ivory: #F8F6F2;
      --white: #FFFFFF;
      --muted: #5D5851;
      --line: #E5DED2;
      --display: 'Playfair Display', Georgia, serif;
      --body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; background: #FAFAF8; color: #1A1A1A; font-family: var(--body); line-height: 1.7; overflow-x: hidden; }}
    a {{ color: #8B0D22; text-underline-offset: .2em; }}
    a:hover {{ color: #C41230; }}
    a:focus-visible, button:focus-visible {{ outline: 3px solid #B8962E; outline-offset: 3px; }}
    .skip-link {{ position: fixed; top: -7rem; left: 1rem; z-index: 1000; min-height: 44px; padding: .65rem 1rem; background: #FAFAF8; color: #1A1A1A; font-weight: 700; border-radius: 0 0 8px 8px; }}
    .skip-link:focus, .skip-link:focus-visible {{ top: 0; }}
    .site-nav {{ position: relative; z-index: 30; background: #0A0A0A; border-bottom: 1px solid rgba(184,150,46,.38); }}
    .nav-inner {{ width: min(1320px, calc(100% - 2rem)); min-height: 78px; margin: 0 auto; display: flex; align-items: center; gap: 1rem; }}
    .brand {{ flex: 0 0 auto; min-height: 44px; display: inline-flex; align-items: center; }}
    .brand img {{ width: auto; height: 54px; display: block; padding: 5px 10px; background: #FFFFFF; border-radius: 4px; }}
    .nav-links {{ margin-left: auto; display: flex; align-items: center; gap: .15rem; }}
    .nav-links a, .menu-button {{ min-height: 44px; display: inline-flex; align-items: center; justify-content: center; padding: .58rem .72rem; border-radius: 999px; color: #FFFFFF; font-size: .86rem; font-weight: 600; text-decoration: none; white-space: nowrap; }}
    .nav-links .nav-cta {{ padding-inline: 1rem; background: linear-gradient(135deg, #C41230, #8B0D22); }}
    .language-link {{ border: 1px solid rgba(255,255,255,.55); }}
    .menu-button {{ display: none; margin-left: auto; border: 1px solid rgba(255,255,255,.55); background: transparent; font: 600 .9rem var(--body); cursor: pointer; }}
    .page-hero {{ position: relative; isolation: isolate; overflow: hidden; background: #1A1A1A; color: #FFFFFF; }}
    .page-hero::before {{ content: ''; position: absolute; inset: 0; z-index: -2; background: url('/images/hero.jpg') center / cover no-repeat; opacity: .28; }}
    .page-hero::after {{ content: ''; position: absolute; inset: 0; z-index: -1; background: linear-gradient(105deg, rgba(10,10,10,.98) 0%, rgba(10,10,10,.9) 53%, rgba(139,13,34,.72) 100%), radial-gradient(circle at 82% 20%, rgba(212,175,90,.22), transparent 34%); }}
    .hero-inner {{ width: min(1080px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(4.8rem, 9vw, 8.2rem) 0 clamp(4.4rem, 8vw, 6.4rem); }}
    .eyebrow {{ margin: 0 0 1rem; color: #D4AF5A; font-size: .78rem; font-weight: 700; letter-spacing: .17em; text-transform: uppercase; }}
    h1, h2, h3 {{ font-family: var(--display); line-height: 1.15; }}
    h1 {{ max-width: 990px; margin: 0; font-size: clamp(2.55rem, 7vw, 5.55rem); letter-spacing: -.025em; }}
    .dek {{ max-width: 820px; margin: 1.45rem 0 0; color: rgba(255,255,255,.88); font-size: clamp(1.05rem, 2vw, 1.3rem); }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: .65rem; margin-top: 1.8rem; }}
    .hero-meta span {{ min-height: 44px; display: inline-flex; align-items: center; padding: .55rem .85rem; border: 1px solid rgba(212,175,90,.48); border-radius: 999px; background: rgba(10,10,10,.4); font-size: .82rem; }}
    main {{ display: block; }}
    .article-shell {{ width: min(1080px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(3.2rem, 7vw, 6rem) 0; }}
    .content-section {{ margin-bottom: clamp(3.8rem, 8vw, 6.8rem); scroll-margin-top: 1.5rem; }}
    .content-section > h2, .source-section > h2 {{ max-width: 880px; margin: 0 0 1rem; font-size: clamp(2rem, 5vw, 3.45rem); }}
    .section-intro, .source-intro {{ max-width: 850px; margin: 0; color: var(--muted); font-size: 1.08rem; }}
    .card-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin-top: 1.6rem; }}
    .content-card {{ min-width: 0; padding: 1.45rem; background: #FFFFFF; border: 1px solid var(--line); border-top: 4px solid #B8962E; border-radius: 12px; box-shadow: 0 14px 40px rgba(26,26,26,.05); }}
    .content-card h3 {{ margin: 0 0 .65rem; font-size: 1.42rem; }}
    .content-card p {{ margin: 0; color: var(--muted); }}
    .content-card ul {{ margin-bottom: 0; padding-left: 1.15rem; }}
    .checklist {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem 1rem; margin: 1.6rem 0 0; padding: 0; list-style: none; counter-reset: steps; }}
    .checklist li {{ min-height: 72px; position: relative; padding: 1rem 1rem 1rem 3.25rem; background: #F8F6F2; border: 1px solid var(--line); border-radius: 10px; }}
    .checklist li::before {{ counter-increment: steps; content: counter(steps); position: absolute; top: 1rem; left: 1rem; width: 1.7rem; height: 1.7rem; display: grid; place-items: center; border-radius: 50%; background: #8B0D22; color: #FFFFFF; font-size: .78rem; font-weight: 700; }}
    .section-note {{ margin: 1.3rem 0 0; padding: 1.05rem 1.15rem; background: #FFFFFF; border: 1px solid var(--line); border-left: 4px solid #B8962E; border-radius: 10px; }}
    .dark-section {{ padding: clamp(1.7rem, 4vw, 2.8rem); background: #0A0A0A; color: #FFFFFF; border-radius: 16px; box-shadow: inset 0 0 0 1px rgba(184,150,46,.3); }}
    .dark-section .section-intro, .dark-section .content-card p {{ color: rgba(255,255,255,.78); }}
    .dark-section .content-card {{ background: #1A1A1A; border-color: rgba(212,175,90,.32); }}
    .dark-section .content-card h3 {{ color: #FFFFFF; }}
    .notice {{ margin-bottom: clamp(3.8rem, 8vw, 6.8rem); padding: clamp(1.4rem, 4vw, 2.25rem); background: #FFFFFF; border: 1px solid var(--line); border-left: 5px solid #8B0D22; border-radius: 12px; }}
    .notice h2 {{ margin: 0 0 .7rem; font-size: clamp(1.65rem, 4vw, 2.35rem); }}
    .notice p {{ margin-bottom: 0; }}
    .source-section {{ margin-bottom: clamp(3.8rem, 8vw, 6.8rem); }}
    .source-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 1.6rem; }}
    .source-card {{ min-width: 0; display: flex; flex-direction: column; padding: 1.35rem; background: #F8F6F2; border: 1px solid var(--line); border-top: 4px solid #C41230; border-radius: 10px; }}
    .source-kind {{ margin: 0 0 .45rem; color: #8B0D22; font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }}
    .source-card h3 {{ margin: 0 0 .55rem; font-size: 1.28rem; }}
    .source-card p {{ margin: .35rem 0; color: var(--muted); }}
    .source-card .source-limit {{ padding-top: .7rem; border-top: 1px solid var(--line); font-size: .9rem; }}
    .source-card a {{ min-height: 44px; display: inline-flex; align-items: center; margin-top: auto; padding-top: .8rem; font-weight: 700; }}
    .cta-panel {{ margin-bottom: 1rem; padding: clamp(1.7rem, 5vw, 3rem); background: #1A1A1A; color: #FFFFFF; border-radius: 16px; box-shadow: inset 0 0 0 1px rgba(184,150,46,.34); }}
    .cta-panel h2 {{ margin: 0 0 .7rem; font-size: clamp(1.8rem, 4vw, 2.7rem); }}
    .cta-panel p {{ max-width: 800px; color: rgba(255,255,255,.82); }}
    .button-row {{ display: flex; flex-wrap: wrap; gap: .8rem; margin-top: 1.25rem; }}
    .button {{ min-height: 48px; display: inline-flex; align-items: center; justify-content: center; padding: .72rem 1.15rem; border: 2px solid #C41230; border-radius: 999px; color: #FFFFFF; font-weight: 700; text-decoration: none; }}
    .button.primary {{ border-color: #C41230; background: linear-gradient(135deg, #C41230, #8B0D22); }}
    .button.secondary {{ border-color: #D4AF5A; }}
    .credential {{ margin-top: 1rem; padding: 1.35rem; background: #F8F6F2; border: 1px solid var(--line); border-radius: 10px; }}
    .credential h2 {{ margin: 0 0 .8rem; font-size: 1.55rem; }}
    .credential-list {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem 1rem; margin: 0; }}
    .credential-list dt {{ color: #8B0D22; font-size: .76rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
    .credential-list dd {{ margin: .18rem 0 0; overflow-wrap: anywhere; }}
    .credential a {{ min-height: 44px; display: inline-flex; align-items: center; }}
    footer {{ background: #0A0A0A; color: rgba(255,255,255,.78); border-top: 1px solid rgba(184,150,46,.34); }}
    .footer-inner {{ width: min(1080px, calc(100% - 2rem)); margin: 0 auto; padding: 2.6rem 0; display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }}
    .footer-inner strong {{ color: #FFFFFF; font-family: var(--display); }}
    .footer-inner p {{ margin: .35rem 0 0; }}
    .footer-inner a {{ min-height: 44px; display: inline-flex; align-items: center; color: #FFFFFF; }}
    @media (max-width: 980px) {{ .card-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
    @media (max-width: 820px) {{
      .menu-button {{ display: inline-flex; }}
      .nav-links {{ display: none; position: absolute; top: 78px; left: 0; right: 0; margin: 0; padding: .8rem 1rem 1.1rem; flex-direction: column; align-items: stretch; background: #0A0A0A; border-top: 1px solid rgba(184,150,46,.35); }}
      .nav-links.open {{ display: flex; }}
      .nav-links a {{ width: 100%; }}
      .checklist {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 580px) {{
      .nav-inner {{ width: min(100% - 1rem, 1320px); }}
      .brand img {{ height: 46px; max-width: 240px; object-fit: contain; }}
      .hero-inner, .article-shell {{ width: min(100% - 1.25rem, 1080px); }}
      .card-grid, .source-grid, .credential-list {{ grid-template-columns: 1fr; }}
      .button-row {{ flex-direction: column; }}
      .button {{ width: 100%; text-align: center; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">{esc(labels["skip"])}</a>
  <nav class="site-nav" aria-label="{esc(labels["nav"])}">
    <div class="nav-inner">
      <a class="brand" href="{home_route}"><img src="/images/jorge-logo.jpg" width="250" height="100" alt="The Jorge Ramirez Group"></a>
      <button class="menu-button" type="button" aria-expanded="false" aria-controls="primary-links">{esc(labels["menu"])}</button>
      <div class="nav-links" id="primary-links">
        <a href="{home_route}">{esc(labels["home"])}</a>
        <a href="{prefix}/buy-a-home">{esc(labels["buy"])}</a>
        <a href="{prefix}/#communities">{esc(labels["communities"])}</a>
        <a href="{prefix}/blog">{esc(labels["research"])}</a>
{language_navigation}
        <a class="nav-cta" href="{prefix}/home-valuation">{esc(labels["valuation"])}</a>
      </div>
    </div>
  </nav>
  <main id="main" tabindex="-1">
    <article data-source-cluster="{esc(page["cluster"])}" data-reviewed-on="{REVIEWED_ON}">
      <header class="page-hero">
        <div class="hero-inner">
          <p class="eyebrow">{esc(page["eyebrow"])}</p>
          <h1>{esc(page["h1"])}</h1>
          <p class="dek">{esc(page["dek"])}</p>
          <div class="hero-meta">
            <span>{esc(labels["reviewed"])}:&nbsp;<time datetime="{REVIEWED_ON}">{REVIEWED_ON}</time></span>
            <span>{esc(labels["author"])}</span>
          </div>
        </div>
      </header>
{editorial_visual}      <div class="article-shell">
{render_sections(page["sections"])}
        <aside class="notice" aria-labelledby="scope-heading">
          <h2 id="scope-heading">{esc(page["disclaimerHeading"])}</h2>
          <p>{esc(page["disclaimer"])}</p>
        </aside>
        <section class="source-section" aria-labelledby="sources-heading">
          <h2 id="sources-heading">{esc(labels["sourcesHeading"])}</h2>
          <p class="source-intro">{esc(labels["sourcesIntro"])}</p>
          {render_sources(sources, lang, spanish_source_copy)}
        </section>
        <section class="cta-panel" aria-labelledby="next-heading">
          <h2 id="next-heading">{esc(page["ctaHeading"])}</h2>
          <p>{esc(page["ctaText"])}</p>
          <div class="button-row">
            <a class="button primary btn-primary" href="{contact_route}">{esc(page["ctaLabel"])}</a>
            <a class="button secondary cta-button" href="tel:{esc(business["directPhone"]["e164"])}">{esc(business["directPhone"]["display"])}</a>
          </div>
        </section>
        <aside class="credential" aria-labelledby="credential-heading">
          <h2 id="credential-heading">{esc(labels["credential"])}</h2>
          <dl class="credential-list">
            <div><dt>{esc(labels["license"])}</dt><dd>#{esc(business["njRealEstateLicense"])}</dd></div>
            <div><dt>{esc(labels["office"])}</dt><dd>{esc(business["brokerage"]["displayName"])}<br>{esc(address["street"])}, {esc(address["city"])}, {esc(address["region"])} {esc(address["postalCode"])}</dd></div>
            <div><dt>{esc(labels["direct"])}</dt><dd><a href="tel:{esc(business["directPhone"]["e164"])}">{esc(business["directPhone"]["display"])}</a></dd></div>
            <div><dt>{esc(labels["email"])}</dt><dd><a href="mailto:{esc(business["email"])}">{esc(business["email"])}</a></dd></div>
          </dl>
        </aside>
      </div>
    </article>
  </main>
  <footer>
    <div class="footer-inner">
      <div><strong>The Jorge Ramirez Group · {esc(business["brokerage"]["displayName"])}</strong><p>{esc(labels["footer"])}</p></div>
      <a href="{contact_route}">{esc(page["ctaLabel"])}</a>
    </div>
  </footer>
  <script>
    (() => {{
      const button = document.querySelector('.menu-button');
      const links = document.querySelector('#primary-links');
      if (!button || !links) return;
      const close = () => {{ links.classList.remove('open'); button.setAttribute('aria-expanded', 'false'); }};
      button.addEventListener('click', () => {{
        const open = links.classList.toggle('open');
        button.setAttribute('aria-expanded', String(open));
      }});
      links.addEventListener('click', (event) => {{ if (event.target.closest('a')) close(); }});
      document.addEventListener('keydown', (event) => {{ if (event.key === 'Escape') close(); }});
    }})();
  </script>
  <script src="/js/site-cta.js" defer></script>
</body>
</html>
'''


def render_fallback() -> str:
    destination = SITE + FALLBACK_DESTINATION
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <title>Inherited Home Guidance Has Moved | The Jorge Ramirez Group</title>
  <meta name="description" content="This inherited-home article has moved to the consolidated New Jersey guide with current source and professional-scope notes.">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{destination}">
  <meta http-equiv="refresh" content="0; url={FALLBACK_DESTINATION}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{destination}">
  <meta property="og:title" content="Inherited Home Guidance Has Moved">
  <meta property="og:description" content="Continue to the consolidated New Jersey inherited-home guide.">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="/css/styles.css">
  <style>
    :root {{ --dark-bg:#0A0A0A; --ink:#1A1A1A; --red:#C41230; --deep-red:#8B0D22; --gold:#B8962E; --gold-light:#D4AF5A; --ivory:#FAFAF8; --soft-ivory:#F8F6F2; --display:'Playfair Display',Georgia,serif; --body:'Inter',sans-serif; }}
    *{{box-sizing:border-box}} body{{margin:0;background:#FAFAF8;color:#1A1A1A;font-family:var(--body);line-height:1.7}} .skip-link{{position:absolute;left:-9999px}} .skip-link:focus{{left:1rem;top:0;background:#FAFAF8;padding:.7rem 1rem}} main{{min-height:100vh;display:grid;place-items:center;padding:1rem;background:linear-gradient(135deg,#0A0A0A,#1A1A1A)}} .card{{width:min(680px,100%);padding:clamp(1.6rem,5vw,3rem);background:#F8F6F2;border-top:5px solid #C41230;border-radius:12px}} h1{{font-family:var(--display);font-size:clamp(2rem,7vw,3.7rem);line-height:1.1}} a{{min-height:48px;display:inline-flex;align-items:center;padding:.75rem 1.1rem;border-radius:999px;background:linear-gradient(135deg,#C41230,#8B0D22);color:#fff;font-weight:700;text-decoration:none;box-shadow:0 0 0 1px #B8962E}}
  </style>
  <script>window.location.replace('{FALLBACK_DESTINATION}');</script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <main id="main">
    <section class="card">
      <p>Updated source-led guide</p>
      <h1>This inherited-home article has moved</h1>
      <p>The overlapping article is now consolidated into one New Jersey inherited-home guide with current source links and clear legal and tax boundaries.</p>
      <a href="{FALLBACK_DESTINATION}">Continue to the inherited-home guide</a>
    </section>
  </main>
</body>
</html>
'''


def targets(
    manifest: Mapping[str, Any], business: Mapping[str, Any]
) -> List[Tuple[Path, str]]:
    source_map = {item["id"]: item for item in manifest["sources"]}
    result: List[Tuple[Path, str]] = []
    seen: set = set()
    for page in page_definitions():
        relative = page["path"]
        if relative in seen or relative not in EXPECTED_FILES or relative == FALLBACK_PATH:
            raise ValueError("refusing duplicate or unexpected output path: %s" % relative)
        if page["cluster"] not in EXPECTED_CLUSTERS or relative not in EXPECTED_CLUSTERS[page["cluster"]]:
            raise ValueError("page %s has an unexpected source cluster" % relative)
        expected_route = "/" + relative[:-5]
        if page["route"] != expected_route:
            raise ValueError("page %s changed its clean canonical route" % relative)
        if page["lang"] not in {"en", "es"}:
            raise ValueError("page %s has an invalid language" % relative)
        source_ids = manifest["clusters"][page["cluster"]]["sourceIds"]
        result.append(
            (
                ROOT / relative,
                render_page(
                    page,
                    source_map,
                    source_ids,
                    business,
                    manifest["spanishSourceCopy"],
                ),
            )
        )
        seen.add(relative)
    expected_indexable = EXPECTED_FILES - {FALLBACK_PATH}
    if seen != expected_indexable:
        missing = sorted(expected_indexable - seen)
        unexpected = sorted(seen - expected_indexable)
        raise ValueError(
            "page definition inventory mismatch; missing=%s unexpected=%s"
            % (missing, unexpected)
        )
    result.append((ROOT / FALLBACK_PATH, render_fallback()))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail when a managed page is stale")
    mode.add_argument("--write", action="store_true", help="write stale managed pages")
    args = parser.parse_args()

    try:
        rendered = targets(load_manifest(), load_business())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print("High-value source manifest error: %s" % error, file=sys.stderr)
        return 2

    stale = [
        path for path, content in rendered
        if not path.exists() or path.read_text(encoding="utf-8") != content
    ]
    if args.check:
        if stale:
            print("Stale high-value legal/fair-housing pages:")
            for path in stale:
                print("- %s" % path.relative_to(ROOT))
            return 1
        print("%d managed pages are current." % len(rendered))
        return 0

    for path, content in rendered:
        if path in stale:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print("Updated %d of %d managed pages." % (len(stale), len(rendered)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
