#!/usr/bin/env python3
"""Build the bilingual, source-backed NYC commuter-town comparison pages."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEWED_ISO = "2026-08-26"
GTFS_DATE = "2026-08-19"

CANONICALS = {
    "en": "https://thejorgeramirezgroup.com/blog/best-nj-suburbs-nyc-commuters",
    "es": "https://thejorgeramirezgroup.com/es/blog/best-nj-suburbs-nyc-commuters",
}

OFFICIAL = {
    "system": "https://www.njtransit.com/accessibility/System-Map",
    "ny": "https://www.njtransit.com/getting-new-york-train",
    "rail": "https://www.njtransit.com/ride-rail",
    "planner": "https://www.njtransit.com/trip-planner-to",
    "stations": "https://www.njtransit.com/station-park-ride-to",
    "alerts": "https://www.njtransit.com/travel-alerts-to",
    "path": "https://www.panynj.gov/path/en/schedules-maps.html",
    "schools": "https://www.nj.gov/education/schoolperformance/",
    "crime": "https://www.nj.gov/njsp/ucr/uniform-crime-reports.shtml",
    "hud": "https://www.hud.gov/news/hud-no-26-028",
}

TOWNS = [
    {
        "name": "South Orange",
        "county": {"en": "Essex County", "es": "Condado de Essex"},
        "route": "Morris & Essex / Gladstone",
        "slug": "south-orange",
        "note": {
            "en": "Check the specific departure because New York Penn, Hoboken, and transfer patterns depend on the published itinerary.",
            "es": "Revise la salida específica porque New York Penn, Hoboken y los transbordos dependen del itinerario publicado.",
        },
    },
    {
        "name": "Maplewood",
        "county": {"en": "Essex County", "es": "Condado de Essex"},
        "route": "Morris & Essex / Gladstone",
        "slug": "maplewood",
        "note": {
            "en": "Compare the actual weekday, evening, and weekend itinerary rather than assuming one service pattern.",
            "es": "Compare el itinerario real de días laborables, noches y fines de semana en lugar de suponer un solo patrón.",
        },
    },
    {
        "name": "Millburn",
        "county": {"en": "Essex County", "es": "Condado de Essex"},
        "route": "Morris & Essex / Gladstone",
        "slug": "millburn",
        "note": {
            "en": "Test the route from the property to Millburn Station and confirm current parking rules with the listed operator.",
            "es": "Pruebe la ruta desde la propiedad hasta Millburn Station y confirme las reglas de estacionamiento con el operador indicado.",
        },
    },
    {
        "name": "Summit",
        "county": {"en": "Union County", "es": "Condado de Union"},
        "route": "Morris & Essex / Gladstone",
        "slug": "summit",
        "note": {
            "en": "Summit is a junction in the selected rail data; verify the train, platform, destination, and any transfer for the travel date.",
            "es": "Summit es una conexión en los datos ferroviarios seleccionados; verifique tren, andén, destino y transbordo para la fecha del viaje.",
        },
    },
    {
        "name": "Chatham Borough",
        "county": {"en": "Morris County", "es": "Condado de Morris"},
        "route": "Morris & Essex",
        "slug": "chatham-borough",
        "note": {
            "en": "Use the borough station as the transit starting point, then add the address-to-platform and destination-side legs.",
            "es": "Use la estación del borough como punto inicial y añada los tramos desde la dirección al andén y desde la terminal al destino.",
        },
    },
    {
        "name": "Madison",
        "county": {"en": "Morris County", "es": "Condado de Morris"},
        "route": "Morris & Essex",
        "slug": "madison",
        "note": {
            "en": "Check the itinerary needed for the actual work schedule and research station access separately for each property.",
            "es": "Revise el itinerario necesario para el horario real de trabajo e investigue por separado el acceso a la estación desde cada propiedad.",
        },
    },
    {
        "name": "Morristown",
        "county": {"en": "Morris County", "es": "Condado de Morris"},
        "route": "Morris & Essex",
        "slug": "morristown",
        "note": {
            "en": "Confirm whether the chosen departure serves New York Penn, Hoboken, or a transfer connection on that date.",
            "es": "Confirme si la salida elegida sirve New York Penn, Hoboken o una conexión con transbordo en esa fecha.",
        },
    },
    {
        "name": "Denville",
        "county": {"en": "Morris County", "es": "Condado de Morris"},
        "route": "Morris & Essex",
        "slug": "denville",
        "note": {
            "en": "A station name does not establish a one-seat trip; check the date-specific routing and any platform change.",
            "es": "El nombre de una estación no garantiza un viaje sin transbordo; revise la ruta de la fecha y cualquier cambio de andén.",
        },
    },
    {
        "name": "New Providence",
        "county": {"en": "Union County", "es": "Condado de Union"},
        "route": "Gladstone Branch",
        "slug": "new-providence",
        "note": {
            "en": "Compare New Providence and Murray Hill station access separately, including the current schedule and lot operator.",
            "es": "Compare por separado el acceso a New Providence y Murray Hill, incluido el horario vigente y el operador del estacionamiento.",
        },
    },
    {
        "name": "Berkeley Heights",
        "county": {"en": "Union County", "es": "Condado de Union"},
        "route": "Gladstone Branch",
        "slug": "berkeley-heights",
        "note": {
            "en": "Verify the selected train and station parking source; ownership and permit terms can differ by lot.",
            "es": "Verifique el tren y la fuente de estacionamiento; el propietario y los permisos pueden variar según el lote.",
        },
    },
    {
        "name": "Cranford",
        "county": {"en": "Union County", "es": "Condado de Union"},
        "route": "Raritan Valley Line",
        "slug": "cranford",
        "note": {
            "en": "New York routing varies by the published service pattern, so confirm whether the itinerary includes a Newark Penn transfer.",
            "es": "La ruta hacia Nueva York varía según el servicio publicado; confirme si el itinerario incluye transbordo en Newark Penn.",
        },
    },
    {
        "name": "Westfield",
        "county": {"en": "Union County", "es": "Condado de Union"},
        "route": "Raritan Valley Line",
        "slug": "westfield",
        "note": {
            "en": "Check the intended departure, its terminal, and station access instead of relying on a general town estimate.",
            "es": "Revise la salida prevista, su terminal y el acceso a la estación en lugar de depender de una estimación general del municipio.",
        },
    },
    {
        "name": "Fanwood",
        "county": {"en": "Union County", "es": "Condado de Union"},
        "route": "Raritan Valley Line",
        "slug": "fanwood",
        "note": {
            "en": "Identify the relevant parking lot and operator, then confirm the New York connection for the specific departure.",
            "es": "Identifique el estacionamiento y su operador, y confirme después la conexión a Nueva York para la salida específica.",
        },
    },
    {
        "name": "Somerville",
        "county": {"en": "Somerset County", "es": "Condado de Somerset"},
        "route": "Raritan Valley Line",
        "slug": "somerville",
        "note": {
            "en": "Use the official planner to test the full itinerary, including Newark routing and the final New York leg.",
            "es": "Use el planificador oficial para probar el itinerario completo, incluida la ruta por Newark y el tramo final en Nueva York.",
        },
    },
    {
        "name": "Rahway",
        "county": {"en": "Union County", "es": "Condado de Union"},
        "route": "Northeast Corridor comparison group",
        "slug": "rahway",
        "note": {
            "en": "Confirm the route serving the chosen departure and check current station, accessibility, and parking information.",
            "es": "Confirme la línea de la salida elegida y revise la información vigente de estación, accesibilidad y estacionamiento.",
        },
    },
    {
        "name": "Metropark / Woodbridge",
        "county": {"en": "Middlesex County", "es": "Condado de Middlesex"},
        "route": "Northeast Corridor",
        "slug": "woodbridge",
        "note": {
            "en": "Compare the address-to-Metropark trip, station facilities, and the selected train rather than using the municipality alone.",
            "es": "Compare el trayecto desde la dirección hasta Metropark, las instalaciones y el tren elegido, no solo el nombre del municipio.",
        },
    },
    {
        "name": "Metuchen",
        "county": {"en": "Middlesex County", "es": "Condado de Middlesex"},
        "route": "Northeast Corridor",
        "slug": "metuchen",
        "note": {
            "en": "Test the intended travel window and station access for the property, then recheck alerts before travel.",
            "es": "Pruebe la franja horaria prevista y el acceso desde la propiedad; revise las alertas antes de viajar.",
        },
    },
    {
        "name": "New Brunswick",
        "county": {"en": "Middlesex County", "es": "Condado de Middlesex"},
        "route": "Northeast Corridor",
        "slug": "new-brunswick",
        "note": {
            "en": "Check the exact train and local connection; the station-area trip is only one part of a door-to-destination comparison.",
            "es": "Revise el tren exacto y la conexión local; el tramo de la estación es solo una parte del viaje completo.",
        },
    },
    {
        "name": "Jersey City / Hoboken",
        "county": {"en": "Hudson County", "es": "Condado de Hudson"},
        "route": "PATH and connecting systems",
        "slug": "jersey-city",
        "note": {
            "en": "PATH is separate from NJ TRANSIT rail. Use the Port Authority schedule for the intended terminal, day, and time.",
            "es": "PATH es un sistema separado de NJ TRANSIT Rail. Use el horario de Port Authority para la terminal, el día y la hora previstos.",
        },
    },
]


COPY = {
    "en": {
        "lang": "en",
        "locale": "en-US",
        "title": "NJ Commuter Towns to NYC: Official Rail Comparison",
        "description": "Compare selected New Jersey commuter towns by official rail route, station access, transfer questions, and a practical door-to-destination checklist.",
        "og_locale": "en_US",
        "home": "Home",
        "blog": "Blog",
        "nav_communities": "Communities",
        "nav_map": "Train Map",
        "nav_search": "Search Homes",
        "nav_contact": "Contact",
        "eyebrow": "New Jersey commuter research · official-source guide",
        "h1": "How to Compare NJ Commuter Towns for NYC",
        "dek": "An unranked, source-backed way to compare route patterns, station access, transfers, and the complete trip from a specific property to a specific destination.",
        "reviewed": "Reviewed August 26, 2026",
        "snapshot": "Official NJ TRANSIT rail data snapshot: August 19, 2026",
        "hero_primary": "Open the Interactive Train Map",
        "hero_secondary": "Explore Community Guides",
        "quick_title": "Start with the trip you will actually make",
        "quick_intro": "A town name cannot answer a commute question. Define the departure window, Manhattan destination, station-access plan, and return trip before comparing properties.",
        "quick_items": [
            ("Exact itinerary", "Run the official planner for the days and times that matter. Service patterns, transfers, and terminals can differ."),
            ("Property to platform", "Include the walk, drive, drop-off, bicycle route, parking operator, accessibility needs, and realistic buffer."),
            ("Destination-side leg", "New York Penn, Hoboken, PATH terminals, and the final subway or walking leg create different trips."),
            ("Current conditions", "Recheck station notices, construction, service alerts, and parking rules before relying on earlier research."),
        ],
        "routes_title": "Route groups and the question each buyer should verify",
        "routes_intro": "This table is a planning framework, not a promise that every train follows the same pattern.",
        "caption": "Selected systems and date-specific questions to confirm with the official operator",
        "th_route": "Route or system",
        "th_examples": "Illustrative station areas",
        "th_question": "Question to verify",
        "th_source": "Official source",
        "route_rows": [
            ("Morris & Essex / Gladstone", "South Orange, Maplewood, Millburn, Summit, Chatham, Madison, Morristown", "Does this departure serve New York Penn, Hoboken, or require a connection?", "NJ TRANSIT New York guidance", "ny"),
            ("Raritan Valley Line", "Cranford, Westfield, Fanwood, Somerville", "Does the selected itinerary terminate at Newark Penn, continue to New York, or require a transfer?", "NJ TRANSIT trip planner", "planner"),
            ("Northeast Corridor", "Rahway, Metropark, Metuchen, New Brunswick", "Which train serves the required travel window, and what station access is available?", "NJ TRANSIT rail information", "rail"),
            ("PATH", "Jersey City and Hoboken station areas", "Which Manhattan terminal and service pattern apply on the selected day?", "Port Authority schedules and maps", "path"),
        ],
        "towns_title": "Selected town and station-area research cards",
        "towns_intro": "These examples cover the six counties in Jorge Ramirez's stated service area. They are illustrative and unranked; inclusion does not imply a recommendation, and omission does not imply a negative judgment.",
        "guide_link": "Open town research guide",
        "planner_link": "Check official trip planning",
        "path_link": "Check official PATH schedules",
        "method_title": "A repeatable door-to-destination comparison",
        "steps": [
            ("Write down the required arrival and departure windows", "Test normal workdays, late returns, and any weekend schedule that matters."),
            ("Map the exact property-to-station leg", "A municipality may have multiple stations, parking operators, local connections, or address-specific access constraints."),
            ("Record every transfer and terminal", "Compare the itinerary shown for the selected date instead of a marketing shorthand such as ‘direct.’"),
            ("Check fare, parking, and accessibility at the official source", "Use current operator tools. This guide intentionally does not repeat amounts or availability that can change."),
            ("Repeat the test before making a housing decision", "Schedules, work patterns, construction, and individual requirements change. Save the assumptions behind the comparison."),
        ],
        "fair_title": "Schools, crime data, and fair housing",
        "fair_copy": "This guide does not label or rank communities by schools, crime, demographics, or who should live there. If a reader independently wants those data, every reader receives the same links to NJDOE School Performance Reports and New Jersey State Police crime reports. Review the publication year, definitions, reporting coverage, and exact geography rather than relying on a slogan. HUD's current guidance emphasizes consistent, unbiased sharing without discriminatory intent.",
        "official_title": "Official sources and update method",
        "official_intro": "The route comparison was checked against NJ TRANSIT's official rail data and public rider tools. The selected station list is not the full system. Open the operator's current tools for a date-specific decision.",
        "source_labels": {
            "system": "NJ TRANSIT system map",
            "ny": "NJ TRANSIT: getting to New York by train",
            "rail": "NJ TRANSIT rail rider information",
            "planner": "NJ TRANSIT trip planner",
            "stations": "NJ TRANSIT station and parking research",
            "alerts": "NJ TRANSIT travel alerts",
            "path": "Port Authority PATH schedules and maps",
            "schools": "NJDOE School Performance Reports",
            "crime": "New Jersey State Police crime reports",
            "hud": "HUD guidance on consistent school and crime data sharing",
        },
        "faq_title": "NJ-to-NYC commute questions",
        "faqs": [
            ("Which NJ towns have rail access toward New York City?", "NJ TRANSIT's system map and official GTFS data identify many station areas. This guide shows an illustrative subset in Jorge Ramirez's six-county service area. Use the full official map and trip planner for other origins."),
            ("Does a station on a New York-serving line guarantee a one-seat ride?", "No. The terminal and transfer pattern can change by route, train, direction, day, and service condition. Confirm the exact itinerary in the official planner."),
            ("How should I compare a Raritan Valley Line trip?", "Enter the actual travel window and check whether the itinerary continues beyond Newark Penn or requires a transfer. Repeat the check for the return trip and for different service days."),
            ("How can I tell whether a commute fits my schedule?", "Start with the required arrival time, then include the property-to-station leg, waiting, transfers, the destination-side leg, and a realistic disruption buffer. Test more than one service window."),
            ("Where should I verify fares, parking, and accessibility?", "Use NJ TRANSIT's current trip, station, and rider-information tools or the applicable PATH source. Confirm the operator and terms for the specific lot or facility."),
            ("How does this guide choose the towns shown?", "The examples form an unranked cross-section across Union, Essex, Morris, Hudson, Middlesex, and Somerset counties. They illustrate route and due-diligence differences and are not a universal recommendation."),
        ],
        "cta_title": "Compare the route, then compare the property",
        "cta_copy": "Use current listings only after the transit assumptions are clear. Jorge can help organize property-specific questions without promising a travel time or outcome.",
        "cta_search": "Search Current Listings",
        "cta_contact": "Ask a Property Question",
        "cta_value": "Request a Home Valuation",
        "author": "Jorge Ramirez · NJ real estate salesperson license #1754604 · Keller Williams Premier Properties",
        "footer_equal": "Equal Housing Opportunity. Verify time-sensitive transit, property, legal, tax, and lending details with the responsible source or professional.",
        "skip": "Skip to main content",
    },
    "es": {
        "lang": "es",
        "locale": "es-US",
        "title": "Pueblos de NJ para Viajar a NYC: Comparación Oficial",
        "description": "Compare pueblos seleccionados de Nueva Jersey por ruta ferroviaria oficial, acceso a la estación, transbordos y el viaje completo desde una propiedad.",
        "og_locale": "es_US",
        "home": "Inicio",
        "blog": "Blog",
        "nav_communities": "Comunidades",
        "nav_map": "Mapa de Trenes",
        "nav_search": "Buscar Casas",
        "nav_contact": "Contacto",
        "eyebrow": "Investigación de transporte en Nueva Jersey · fuentes oficiales",
        "h1": "Cómo Comparar Pueblos de NJ para Viajar a NYC",
        "dek": "Una forma sin rankings y respaldada por fuentes para comparar rutas, acceso a estaciones, transbordos y el viaje completo desde una propiedad específica hasta un destino específico.",
        "reviewed": "Revisado el 26 de agosto de 2026",
        "snapshot": "Datos oficiales de NJ TRANSIT Rail: 19 de agosto de 2026",
        "hero_primary": "Abrir el Mapa Interactivo",
        "hero_secondary": "Explorar Guías de Comunidades",
        "quick_title": "Empiece con el viaje que realmente hará",
        "quick_intro": "El nombre de un municipio no responde una pregunta de transporte. Defina la hora de salida, el destino en Manhattan, el acceso a la estación y el regreso antes de comparar propiedades.",
        "quick_items": [
            ("Itinerario exacto", "Use el planificador oficial para los días y horarios importantes. Los transbordos, terminales y patrones pueden variar."),
            ("De la propiedad al andén", "Incluya caminata, manejo, llegada, bicicleta, operador de estacionamiento, accesibilidad y un margen realista."),
            ("Tramo desde la terminal", "New York Penn, Hoboken, terminales PATH y el tramo final en metro o a pie producen viajes distintos."),
            ("Condiciones vigentes", "Revise avisos de estaciones, obras, alertas y reglas de estacionamiento antes de usar una investigación anterior."),
        ],
        "routes_title": "Grupos de rutas y la pregunta que cada comprador debe verificar",
        "routes_intro": "Esta tabla es un marco de investigación, no una promesa de que todos los trenes sigan el mismo patrón.",
        "caption": "Sistemas seleccionados y preguntas que deben confirmarse con el operador oficial",
        "th_route": "Ruta o sistema",
        "th_examples": "Áreas de estación ilustrativas",
        "th_question": "Pregunta por verificar",
        "th_source": "Fuente oficial",
        "route_rows": [
            ("Morris & Essex / Gladstone", "South Orange, Maplewood, Millburn, Summit, Chatham, Madison, Morristown", "¿Esta salida sirve New York Penn, Hoboken o requiere una conexión?", "Guía de NJ TRANSIT para Nueva York", "ny"),
            ("Raritan Valley Line", "Cranford, Westfield, Fanwood, Somerville", "¿El itinerario termina en Newark Penn, continúa a Nueva York o requiere transbordo?", "Planificador de NJ TRANSIT", "planner"),
            ("Northeast Corridor", "Rahway, Metropark, Metuchen, New Brunswick", "¿Qué tren sirve el horario requerido y qué acceso tiene la estación?", "Información ferroviaria de NJ TRANSIT", "rail"),
            ("PATH", "Áreas de Jersey City y Hoboken", "¿Qué terminal en Manhattan y qué patrón aplican el día elegido?", "Horarios y mapas de Port Authority", "path"),
        ],
        "towns_title": "Tarjetas de investigación de pueblos y estaciones seleccionados",
        "towns_intro": "Estos ejemplos cubren los seis condados donde Jorge Ramirez indica que presta servicio. Son ilustrativos y no están clasificados; aparecer no implica recomendación y estar ausente no implica un juicio negativo.",
        "guide_link": "Abrir guía de investigación local",
        "planner_link": "Consultar planificación oficial",
        "path_link": "Consultar horarios oficiales de PATH",
        "method_title": "Una comparación repetible de puerta a destino",
        "steps": [
            ("Anote las horas necesarias de llegada y salida", "Pruebe días normales de trabajo, regresos tarde y cualquier horario de fin de semana que importe."),
            ("Trace el tramo exacto de la propiedad a la estación", "Un municipio puede tener varias estaciones, operadores, conexiones locales o restricciones de acceso según la dirección."),
            ("Registre cada transbordo y terminal", "Compare el itinerario para la fecha seleccionada en lugar de usar expresiones de mercadeo como ‘directo.’"),
            ("Revise tarifa, estacionamiento y accesibilidad en la fuente oficial", "Use herramientas vigentes del operador. Esta guía no repite cantidades ni disponibilidad que pueden cambiar."),
            ("Repita la prueba antes de una decisión de vivienda", "Los horarios, el trabajo, las obras y las necesidades individuales cambian. Guarde los supuestos de la comparación."),
        ],
        "fair_title": "Escuelas, datos de delitos y vivienda justa",
        "fair_copy": "Esta guía no etiqueta ni clasifica comunidades por escuelas, delitos, demografía o por quién debería vivir allí. Si un lector desea esos datos por decisión propia, todos reciben los mismos enlaces a los informes de NJDOE y de New Jersey State Police. Revise el año, las definiciones, la cobertura y la geografía exacta en lugar de depender de un eslogan. La guía vigente de HUD destaca compartir datos de forma consistente e imparcial y sin intención discriminatoria.",
        "official_title": "Fuentes oficiales y método de actualización",
        "official_intro": "La comparación se verificó con datos ferroviarios oficiales y herramientas públicas de NJ TRANSIT. La selección no representa todo el sistema. Abra las herramientas vigentes del operador para una decisión con fecha específica.",
        "source_labels": {
            "system": "Mapa del sistema de NJ TRANSIT",
            "ny": "NJ TRANSIT: cómo llegar a Nueva York en tren",
            "rail": "Información de NJ TRANSIT Rail",
            "planner": "Planificador de viajes de NJ TRANSIT",
            "stations": "Investigación de estaciones y estacionamiento",
            "alerts": "Alertas de viaje de NJ TRANSIT",
            "path": "Horarios y mapas de PATH",
            "schools": "Informes escolares de NJDOE",
            "crime": "Informes de delitos de New Jersey State Police",
            "hud": "Guía de HUD sobre compartir datos de forma consistente",
        },
        "faq_title": "Preguntas sobre viajes de NJ a NYC",
        "faqs": [
            ("¿Qué pueblos de NJ tienen acceso ferroviario hacia Nueva York?", "El mapa y los datos GTFS oficiales de NJ TRANSIT identifican muchas áreas. Esta guía muestra una selección ilustrativa dentro de los seis condados donde Jorge Ramirez presta servicio. Use el mapa y planificador oficiales para otros orígenes."),
            ("¿Una estación en una línea hacia Nueva York garantiza un viaje sin transbordo?", "No. La terminal y los transbordos pueden cambiar según ruta, tren, dirección, día y condición del servicio. Confirme el itinerario exacto en el planificador oficial."),
            ("¿Cómo debo comparar un viaje por Raritan Valley Line?", "Ingrese el horario real y revise si el itinerario continúa más allá de Newark Penn o requiere transbordo. Repita la revisión para el regreso y para distintos días de servicio."),
            ("¿Cómo sé si un viaje se ajusta a mi horario?", "Empiece con la hora necesaria de llegada e incluya el tramo a la estación, espera, transbordos, el tramo desde la terminal y un margen realista. Pruebe más de una franja."),
            ("¿Dónde verifico tarifas, estacionamiento y accesibilidad?", "Use las herramientas vigentes de viajes, estaciones e información al pasajero de NJ TRANSIT o la fuente PATH aplicable. Confirme el operador y las reglas de la instalación específica."),
            ("¿Cómo se eligieron los pueblos de esta guía?", "Los ejemplos forman una selección sin ranking de los condados de Union, Essex, Morris, Hudson, Middlesex y Somerset. Ilustran diferencias de ruta e investigación y no son una recomendación universal."),
        ],
        "cta_title": "Compare la ruta y después la propiedad",
        "cta_copy": "Use listados vigentes cuando los supuestos de transporte estén claros. Jorge puede ayudar a organizar preguntas específicas sin prometer tiempo de viaje ni resultado.",
        "cta_search": "Buscar Listados Vigentes",
        "cta_contact": "Hacer una Pregunta",
        "cta_value": "Solicitar Valoración",
        "author": "Jorge Ramirez · licencia de vendedor de bienes raíces de NJ #1754604 · Keller Williams Premier Properties",
        "footer_equal": "Igualdad de Oportunidades de Vivienda. Verifique datos variables de transporte, propiedad, impuestos, ley y financiamiento con la fuente o el profesional responsable.",
        "skip": "Saltar al contenido principal",
    },
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def town_cards(language: str, copy: dict) -> str:
    cards = []
    prefix = "" if language == "en" else "/es"
    for town in TOWNS:
        is_path = town["name"] == "Jersey City / Hoboken"
        official_url = OFFICIAL["path"] if is_path else OFFICIAL["planner"]
        official_label = copy["path_link"] if is_path else copy["planner_link"]
        external_class = "source-link button-link" if is_path else "source-link"
        cards.append(
            f'''<article class="town-card">
              <div class="town-card__head">
                <h3>{esc(town["name"])}</h3>
                <span>{esc(town["county"][language])}</span>
              </div>
              <p class="route-label">{esc(town["route"])}</p>
              <p>{esc(town["note"][language])}</p>
              <div class="card-links">
                <a href="{prefix}/towns/{esc(town['slug'])}">{esc(copy['guide_link'])}</a>
                <a class="{external_class}" href="{official_url}" target="_blank" rel="noopener noreferrer">{esc(official_label)}</a>
              </div>
            </article>'''
        )
    return "\n".join(cards)


def quick_cards(copy: dict) -> str:
    return "\n".join(
        f'''<article class="check-card"><h3>{esc(title)}</h3><p>{esc(body)}</p></article>'''
        for title, body in copy["quick_items"]
    )


def route_rows(copy: dict) -> str:
    rows = []
    for route, examples, question, source_label, source_key in copy["route_rows"]:
        extra_class = ' class="button-link"' if source_key == "path" else ""
        rows.append(
            f'''<tr>
              <th scope="row">{esc(route)}</th>
              <td>{esc(examples)}</td>
              <td>{esc(question)}</td>
              <td><a{extra_class} href="{OFFICIAL[source_key]}" target="_blank" rel="noopener noreferrer">{esc(source_label)}</a></td>
            </tr>'''
        )
    return "\n".join(rows)


def method_steps(copy: dict) -> str:
    return "\n".join(
        f'''<li><h3>{esc(title)}</h3><p>{esc(body)}</p></li>'''
        for title, body in copy["steps"]
    )


def faq_markup(copy: dict) -> str:
    return "\n".join(
        f'''<details><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>'''
        for question, answer in copy["faqs"]
    )


def sources_markup(copy: dict) -> str:
    links = []
    for key, label in copy["source_labels"].items():
        extra_class = ' class="button-link"' if key == "path" else ""
        links.append(
            f'<li><a{extra_class} href="{OFFICIAL[key]}" target="_blank" rel="noopener noreferrer">{esc(label)}</a></li>'
        )
    return "\n".join(links)


def schema_blocks(language: str, copy: dict) -> str:
    canonical = CANONICALS[language]
    prefix = "" if language == "en" else "/es"
    blog_posting = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "@id": canonical + "#article",
        "url": canonical,
        "headline": copy["title"],
        "description": copy["description"],
        "inLanguage": copy["locale"],
        "datePublished": "2026-03-17",
        "dateModified": REVIEWED_ISO,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "author": {
            "@type": "Person",
            "@id": "https://thejorgeramirezgroup.com/#agent",
            "name": "Jorge Ramirez",
            "url": "https://thejorgeramirezgroup.com/ai-authority",
        },
        "publisher": {
            "@type": "Organization",
            "name": "The Jorge Ramirez Group at Keller Williams Premier Properties",
            "url": "https://thejorgeramirezgroup.com/",
        },
        "image": "https://thejorgeramirezgroup.com/images/site/commute-map-teaser.jpg",
        "about": [
            {"@type": "Place", "name": "New Jersey"},
            {"@type": "Thing", "name": "NJ TRANSIT rail trip planning"},
        ],
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": copy["home"],
                "item": f"https://thejorgeramirezgroup.com{prefix}/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": copy["blog"],
                "item": f"https://thejorgeramirezgroup.com{prefix}/blog",
            },
            {"@type": "ListItem", "position": 3, "name": copy["title"], "item": canonical},
        ],
    }
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "inLanguage": copy["locale"],
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in copy["faqs"]
        ],
    }
    return "\n".join(
        f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False, separators=(",", ":"))}</script>'
        for block in (blog_posting, breadcrumb, faq)
    )


def render(language: str) -> str:
    copy = COPY[language]
    canonical = CANONICALS[language]
    prefix = "" if language == "en" else "/es"
    switch_href = CANONICALS["es"] if language == "en" else CANONICALS["en"]
    switch_label = "ES" if language == "en" else "EN"
    return f'''<!doctype html>
<html lang="{copy['lang']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(copy['title'])}</title>
  <meta name="description" content="{esc(copy['description'])}">
  <meta name="author" content="Jorge Ramirez, The Jorge Ramirez Group at Keller Williams Premier Properties">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="ai-content-declaration" content="Human-authored, official-source transit research reviewed {REVIEWED_ISO}; illustrative and unranked.">
  <meta name="llm-context" content="A bilingual, unranked comparison framework for selected New Jersey station areas. Route membership was checked against an official NJ TRANSIT GTFS snapshot dated {GTFS_DATE}; travelers are directed to live operator tools.">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="en-US" href="{CANONICALS['en']}">
  <link rel="alternate" hreflang="es-US" href="{CANONICALS['es']}">
  <link rel="alternate" hreflang="x-default" href="{CANONICALS['en']}">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="{copy['og_locale']}">
  <meta property="og:title" content="{esc(copy['title'])}">
  <meta property="og:description" content="{esc(copy['description'])}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="https://thejorgeramirezgroup.com/images/site/commute-map-teaser.jpg">
  <meta property="article:published_time" content="2026-03-17">
  <meta property="article:modified_time" content="{REVIEWED_ISO}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(copy['title'])}">
  <meta name="twitter:description" content="{esc(copy['description'])}">
  <meta name="twitter:image" content="https://thejorgeramirezgroup.com/images/site/commute-map-teaser.jpg">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700;800&display=swap" rel="stylesheet">
  {schema_blocks(language, copy)}
  <style>
    :root {{
      --ink: #1A1A1A;
      --night: #0A0A0A;
      --red: #C41230;
      --gold: #B8962E;
      --ivory: #FAFAF8;
      --paper: #FFFFFF;
      --muted: #5E5A54;
      --line: #DED8CD;
      --soft-gold: #F3EEDC;
      --shadow: 0 18px 50px rgba(10,10,10,.09);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; background: var(--ivory); color: var(--ink); font-family: 'Inter', sans-serif; line-height: 1.7; }}
    img {{ display: block; max-width: 100%; }}
    a {{ color: var(--red); text-underline-offset: .2em; }}
    a:hover {{ color: #8E0D22; }}
    :focus-visible {{ outline: 3px solid var(--gold); outline-offset: 3px; }}
    .skip-link {{ position: fixed; left: 16px; top: -90px; z-index: 2000; background: var(--paper); color: var(--ink); padding: 12px 18px; border: 2px solid var(--gold); border-radius: 4px; font-weight: 700; }}
    .skip-link:focus {{ top: 12px; }}
    .site-header {{ position: sticky; top: 0; z-index: 1000; background: var(--night); border-bottom: 2px solid var(--gold); }}
    .nav-wrap {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; min-height: 72px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }}
    .brand {{ color: var(--paper); font-family: 'Playfair Display', serif; font-size: 1.18rem; font-weight: 700; text-decoration: none; white-space: nowrap; }}
    .brand span {{ color: var(--gold); }}
    .nav-links {{ display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex-wrap: wrap; }}
    .nav-links a {{ min-height: 44px; display: inline-flex; align-items: center; padding: 8px 11px; color: #F2EFE8; text-decoration: none; font-size: .85rem; font-weight: 600; border-radius: 3px; }}
    .nav-links a:hover {{ color: var(--gold); background: rgba(255,255,255,.06); }}
    .nav-links .contact-link {{ background: var(--red); color: var(--paper); }}
    .nav-links .language-link {{ border: 1px solid rgba(184,150,46,.7); color: var(--gold); }}
    .breadcrumb {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 13px 0; font-size: .86rem; color: var(--muted); }}
    .breadcrumb span {{ padding: 0 7px; }}
    .hero {{ background: linear-gradient(115deg, rgba(10,10,10,.97), rgba(26,26,26,.91)), url('/images/site/commute-map-teaser.jpg') center/cover; color: var(--paper); border-top: 1px solid rgba(184,150,46,.25); }}
    .hero-inner {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: clamp(64px, 9vw, 112px) 0; }}
    .eyebrow {{ color: var(--gold); font-size: .78rem; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }}
    h1, h2, h3 {{ font-family: 'Playfair Display', serif; line-height: 1.16; }}
    h1 {{ max-width: 900px; margin: 12px 0 20px; color: var(--paper); font-size: clamp(2.35rem, 6vw, 5rem); letter-spacing: -.03em; }}
    .hero-dek {{ max-width: 780px; margin: 0 0 26px; color: #E7E2D8; font-size: clamp(1.06rem, 2vw, 1.25rem); }}
    .review-line {{ display: flex; flex-wrap: wrap; gap: 8px 20px; margin: 0 0 32px; color: #CFC8BA; font-size: .88rem; }}
    .hero-actions, .cta-actions {{ display: flex; flex-wrap: wrap; gap: 12px; }}
    .btn {{ min-height: 48px; display: inline-flex; align-items: center; justify-content: center; padding: 12px 20px; border: 2px solid transparent; border-radius: 4px; font-weight: 700; text-decoration: none; }}
    .btn-primary {{ background: var(--red); color: var(--paper); }}
    .btn-primary:hover {{ background: #970D25; color: var(--paper); }}
    .btn-secondary {{ border-color: var(--gold); color: var(--gold); }}
    .btn-secondary:hover {{ background: var(--gold); color: var(--night); }}
    .section {{ padding: clamp(58px, 8vw, 96px) 0; }}
    .section--paper {{ background: var(--paper); }}
    .section--dark {{ background: var(--ink); color: var(--paper); }}
    .container {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; }}
    .section-kicker {{ color: var(--red); font-size: .78rem; font-weight: 700; letter-spacing: .13em; text-transform: uppercase; }}
    .section--dark .section-kicker {{ color: var(--gold); }}
    h2 {{ margin: 8px 0 16px; font-size: clamp(2rem, 4vw, 3.25rem); letter-spacing: -.025em; }}
    .section-intro {{ max-width: 820px; margin: 0 0 34px; color: var(--muted); font-size: 1.05rem; }}
    .section--dark .section-intro {{ color: #D8D2C8; }}
    .check-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; }}
    .check-card {{ min-height: 100%; background: var(--paper); padding: 26px; border: 1px solid var(--line); border-top: 4px solid var(--gold); box-shadow: var(--shadow); }}
    .check-card h3 {{ margin: 0 0 10px; font-size: 1.24rem; }}
    .check-card p {{ margin: 0; color: var(--muted); }}
    .table-shell {{ overflow-x: auto; background: var(--paper); border: 1px solid var(--line); box-shadow: var(--shadow); }}
    table {{ width: 100%; min-width: 820px; border-collapse: collapse; }}
    caption {{ padding: 18px 20px; text-align: left; color: var(--muted); font-weight: 600; }}
    th, td {{ padding: 18px 20px; text-align: left; vertical-align: top; border-top: 1px solid var(--line); }}
    thead th {{ background: var(--night); color: var(--paper); border-top: 0; font-size: .84rem; letter-spacing: .05em; text-transform: uppercase; }}
    tbody th {{ color: var(--ink); font-family: 'Inter', sans-serif; font-size: .96rem; }}
    .town-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }}
    .town-card {{ min-height: 100%; display: flex; flex-direction: column; background: var(--paper); padding: 24px; border: 1px solid var(--line); border-left: 4px solid var(--red); box-shadow: var(--shadow); }}
    .town-card__head {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }}
    .town-card h3 {{ margin: 0; font-size: 1.3rem; }}
    .town-card__head span {{ color: var(--muted); font-size: .76rem; text-align: right; }}
    .route-label {{ margin: 10px 0; color: #765D10; font-size: .82rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }}
    .town-card > p:not(.route-label) {{ margin: 0; color: var(--muted); }}
    .card-links {{ display: flex; flex-wrap: wrap; gap: 10px 18px; margin-top: auto; padding-top: 18px; }}
    .card-links a {{ min-height: 44px; display: inline-flex; align-items: center; font-size: .86rem; font-weight: 700; }}
    .method-list {{ list-style: none; counter-reset: steps; margin: 30px 0 0; padding: 0; display: grid; gap: 16px; }}
    .method-list li {{ counter-increment: steps; position: relative; padding: 24px 24px 24px 78px; background: var(--paper); color: var(--ink); border: 1px solid rgba(184,150,46,.45); }}
    .method-list li::before {{ content: counter(steps); position: absolute; left: 22px; top: 22px; width: 38px; height: 38px; display: grid; place-items: center; background: var(--red); color: var(--paper); border-radius: 50%; font-weight: 800; }}
    .method-list h3 {{ margin: 0 0 5px; font-size: 1.18rem; }}
    .method-list p {{ margin: 0; color: #D8D2C8; }}
    .fair-note {{ margin-top: 28px; padding: 26px; background: var(--soft-gold); border-left: 5px solid var(--gold); }}
    .fair-note h2 {{ margin-top: 0; font-size: clamp(1.6rem, 3vw, 2.25rem); }}
    .fair-note p {{ margin-bottom: 0; }}
    .source-list {{ columns: 2; column-gap: 40px; margin: 24px 0 0; padding-left: 22px; }}
    .source-list li {{ break-inside: avoid; margin: 0 0 10px; }}
    .source-note {{ margin-top: 26px; padding: 18px 20px; border: 1px solid var(--gold); color: #E4DED2; }}
    .faq-list {{ display: grid; gap: 12px; max-width: 930px; }}
    details {{ background: var(--paper); border: 1px solid var(--line); }}
    summary {{ min-height: 52px; cursor: pointer; padding: 16px 52px 16px 20px; font-family: 'Playfair Display', serif; font-size: 1.12rem; font-weight: 700; }}
    details p {{ margin: 0; padding: 0 20px 20px; color: var(--muted); }}
    .cta-band {{ background: linear-gradient(110deg, var(--red), #8E0D22); color: var(--paper); padding: clamp(48px, 7vw, 78px) 0; }}
    .cta-band h2 {{ max-width: 760px; margin-top: 0; }}
    .cta-band p {{ max-width: 760px; color: #F7EDEF; }}
    .cta-band .btn {{ background: var(--paper); color: var(--ink); }}
    .cta-band .btn:hover {{ background: var(--gold); color: var(--night); }}
    .cta-band .btn-outline {{ background: transparent; border-color: var(--paper); color: var(--paper); }}
    .site-footer {{ background: var(--night); color: #CFC8BA; border-top: 2px solid var(--gold); padding: 42px 0; }}
    .footer-grid {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 30px; align-items: start; }}
    .site-footer strong {{ color: var(--paper); font-family: 'Playfair Display', serif; font-size: 1.15rem; }}
    .site-footer p {{ margin: 7px 0; font-size: .9rem; }}
    .site-footer a {{ color: var(--gold); }}
    @media (max-width: 960px) {{
      .nav-wrap {{ align-items: flex-start; flex-direction: column; padding: 13px 0; gap: 7px; }}
      .nav-links {{ width: 100%; justify-content: flex-start; }}
      .check-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .town-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 620px) {{
      .site-header {{ position: static; }}
      .nav-links a {{ padding: 7px 8px; font-size: .78rem; }}
      .hero-actions, .cta-actions {{ flex-direction: column; align-items: stretch; }}
      .check-grid, .town-grid, .footer-grid {{ grid-template-columns: 1fr; }}
      .source-list {{ columns: 1; }}
      .town-card__head {{ flex-direction: column; }}
      .town-card__head span {{ text-align: left; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
  </style>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');if(window.location.hostname==='www.thejorgeramirezgroup.com'){{window.location.replace(window.location.href.replace('//www.','//'))}}</script>
</head>
<body>
  <a class="skip-link" href="#main">{esc(copy['skip'])}</a>
  <header class="site-header">
    <nav class="nav-wrap" aria-label="Primary">
      <a class="brand" href="{prefix}/">Jorge Ramirez <span>Group</span></a>
      <div class="nav-links">
        <a href="{prefix}/communities">{esc(copy['nav_communities'])}</a>
        <a href="{prefix}/nj-train-map">{esc(copy['nav_map'])}</a>
        <a href="{prefix}/property-search">{esc(copy['nav_search'])}</a>
        <a class="contact-link" href="{prefix}/contact">{esc(copy['nav_contact'])}</a>
        <a class="language-link" href="{switch_href}" lang="{'es' if language == 'en' else 'en'}">{switch_label}</a>
      </div>
    </nav>
  </header>
  <div class="breadcrumb" aria-label="Breadcrumb">
    <a href="{prefix}/">{esc(copy['home'])}</a><span aria-hidden="true">/</span><a href="{prefix}/blog">{esc(copy['blog'])}</a><span aria-hidden="true">/</span><span>{esc(copy['nav_map'])}</span>
  </div>
  <main id="main">
    <section class="hero">
      <div class="hero-inner">
        <p class="eyebrow">{esc(copy['eyebrow'])}</p>
        <h1>{esc(copy['h1'])}</h1>
        <p class="hero-dek">{esc(copy['dek'])}</p>
        <p class="review-line"><span>{esc(copy['reviewed'])}</span><span>{esc(copy['snapshot'])}</span></p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{prefix}/nj-train-map">{esc(copy['hero_primary'])}</a>
          <a class="btn btn-secondary" href="{prefix}/communities">{esc(copy['hero_secondary'])}</a>
        </div>
      </div>
    </section>

    <section class="section section--paper">
      <div class="container">
        <p class="section-kicker">01 · Door to destination</p>
        <h2>{esc(copy['quick_title'])}</h2>
        <p class="section-intro">{esc(copy['quick_intro'])}</p>
        <div class="check-grid">{quick_cards(copy)}</div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <p class="section-kicker">02 · Route framework</p>
        <h2>{esc(copy['routes_title'])}</h2>
        <p class="section-intro">{esc(copy['routes_intro'])}</p>
        <div class="table-shell">
          <table>
            <caption>{esc(copy['caption'])}</caption>
            <thead><tr><th scope="col">{esc(copy['th_route'])}</th><th scope="col">{esc(copy['th_examples'])}</th><th scope="col">{esc(copy['th_question'])}</th><th scope="col">{esc(copy['th_source'])}</th></tr></thead>
            <tbody>{route_rows(copy)}</tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="section section--paper" data-selection="illustrative-not-ranked">
      <div class="container">
        <p class="section-kicker">03 · Six-county examples</p>
        <h2>{esc(copy['towns_title'])}</h2>
        <p class="section-intro">{esc(copy['towns_intro'])}</p>
        <div class="town-grid">{town_cards(language, copy)}</div>
      </div>
    </section>

    <section class="section section--dark">
      <div class="container">
        <p class="section-kicker">04 · Repeatable method</p>
        <h2>{esc(copy['method_title'])}</h2>
        <ol class="method-list">{method_steps(copy)}</ol>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="fair-note">
          <h2>{esc(copy['fair_title'])}</h2>
          <p>{esc(copy['fair_copy'])}</p>
        </div>
      </div>
    </section>

    <section class="section section--dark">
      <div class="container">
        <p class="section-kicker">05 · Source record</p>
        <h2>{esc(copy['official_title'])}</h2>
        <p class="section-intro">{esc(copy['official_intro'])}</p>
        <ul class="source-list">{sources_markup(copy)}</ul>
        <p class="source-note">{esc(copy['reviewed'])} · {esc(copy['snapshot'])} · {esc(copy['author'])}</p>
      </div>
    </section>

    <section class="section section--paper">
      <div class="container">
        <p class="section-kicker">06 · Common questions</p>
        <h2>{esc(copy['faq_title'])}</h2>
        <div class="faq-list">{faq_markup(copy)}</div>
      </div>
    </section>

    <section class="cta-band">
      <div class="container">
        <h2>{esc(copy['cta_title'])}</h2>
        <p>{esc(copy['cta_copy'])}</p>
        <div class="cta-actions">
          <a class="btn" href="{prefix}/property-search">{esc(copy['cta_search'])}</a>
          <a class="btn btn-outline" href="{prefix}/contact">{esc(copy['cta_contact'])}</a>
          <a class="btn btn-outline" href="{prefix}/home-valuation">{esc(copy['cta_value'])}</a>
        </div>
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <strong>The Jorge Ramirez Group</strong>
        <p>Keller Williams Premier Properties · 488 Springfield Ave, Summit, NJ 07901</p>
        <p><a href="tel:+19082307844">(908) 230-7844</a> · <a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a></p>
      </div>
      <div>
        <p>{esc(copy['author'])}</p>
        <p>{esc(copy['footer_equal'])}</p>
      </div>
    </div>
  </footer>
  <script defer src="/js/site-cta.js"></script>
</body>
</html>
'''


def redirect_stub(language: str) -> str:
    """Return a minimal fallback for a URL consolidated into the main guide."""
    destination = (
        "/blog/best-nj-suburbs-nyc-commuters"
        if language == "en"
        else "/es/blog/best-nj-suburbs-nyc-commuters"
    )
    canonical = f"https://thejorgeramirezgroup.com{destination}"
    if language == "en":
        title = "NJ Commuter Guide Moved | Jorge Ramirez"
        heading = "The NJ commuter guide has moved"
        body = "Continue to the source-backed comparison of selected New Jersey station areas and official transit planning tools."
        label = "Open the current commuter guide"
    else:
        title = "La Guía de Transporte se Trasladó | Jorge Ramirez"
        heading = "La guía de transporte de NJ se trasladó"
        body = "Continúe a la comparación respaldada por fuentes de estaciones seleccionadas y herramientas oficiales de transporte."
        label = "Abrir la guía vigente"
    return f'''<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(body)}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{canonical}">
  <meta http-equiv="refresh" content="0; url={destination}">
  <style>
    :root {{ --ink:#1A1A1A; --red:#C41230; --gold:#B8962E; --ivory:#FAFAF8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; padding:24px; background:var(--ink); color:var(--ivory); font-family:Inter,Arial,sans-serif; }}
    main {{ width:min(680px,100%); padding:clamp(28px,7vw,58px); background:#0A0A0A; border:1px solid var(--gold); border-top:5px solid var(--red); text-align:center; }}
    h1 {{ margin:0 0 16px; font-family:'Playfair Display',Georgia,serif; font-size:clamp(2rem,7vw,3.4rem); line-height:1.12; }}
    p {{ color:#D8D2C8; line-height:1.7; }}
    a {{ min-height:48px; display:inline-flex; align-items:center; justify-content:center; margin-top:12px; padding:12px 20px; background:var(--red); color:#fff; font-weight:700; text-decoration:none; border:2px solid transparent; }}
    a:focus-visible {{ outline:3px solid var(--gold); outline-offset:3px; }}
  </style>
  <script>window.location.replace('{destination}');</script>
</head>
<body>
  <main id="main">
    <h1>{esc(heading)}</h1>
    <p>{esc(body)}</p>
    <a href="{destination}">{esc(label)}</a>
  </main>
</body>
</html>
'''


def main() -> None:
    targets = {
        "en": ROOT / "blog" / "best-nj-suburbs-nyc-commuters.html",
        "es": ROOT / "es" / "blog" / "best-nj-suburbs-nyc-commuters.html",
    }
    for language, target in targets.items():
        target.write_text(render(language), encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)}")
    legacy_targets = {
        "en": ROOT / "blog" / "top-nyc-commuter-towns-nj-2026.html",
        "es": ROOT / "es" / "blog" / "top-nyc-commuter-towns-nj-2026.html",
    }
    for language, target in legacy_targets.items():
        target.write_text(redirect_stub(language), encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)} redirect fallback")


if __name__ == "__main__":
    main()
