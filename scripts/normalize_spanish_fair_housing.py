#!/usr/bin/env python3
"""Apply reviewed, fluent Spanish fair-housing copy corrections.

Only the exact Spanish inventory and its emitting sources are touched. Markup,
classes, IDs, styles, and layout are preserved.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data" / "spanish-fair-housing-inventory.json"


LITERAL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("Mejores Distritos Escolares", "Cómo Investigar los Distritos Escolares"),
    ("mejores distritos escolares", "distritos escolares para investigar con fuentes oficiales"),
    ("distritos escolares mejor clasificados", "distritos escolares y sus informes oficiales"),
    ("distritos escolares públicos mejor clasificados", "distritos escolares públicos con informes disponibles en NJDOE"),
    ("distritos escolares rankeados", "distritos escolares con informes disponibles en NJDOE"),
    ("escuelas rankeadas a nivel nacional", "escuelas públicas con informes disponibles en NJDOE"),
    ("escuelas de las mejor clasificadas", "escuelas públicas con información disponible en NJDOE"),
    ("Escuelas de las Mejor Clasificadas", "Información Oficial de las Escuelas"),
    ("escuelas públicas de las mejor clasificadas del estado", "escuelas públicas con información disponible en NJDOE"),
    ("escuelas públicas de primer nivel", "escuelas públicas locales; revise los informes vigentes de NJDOE"),
    ("escuelas públicas progresistas y fuertes", "escuelas públicas locales con información disponible en NJDOE"),
    ("distritos escolares reconocidos a nivel nacional que rivalizan con las mejores escuelas privadas", "distritos escolares públicos con informes vigentes disponibles en NJDOE"),
    ("sistemas escolares consistentemente fuertes", "sistemas escolares locales con informes disponibles en NJDOE"),
    ("sistemas escolares fuertes", "sistemas escolares locales"),
    ("sólidos sistemas escolares", "sistemas escolares locales"),
    ("distritos escolares excelentes", "distritos escolares locales"),
    ("escuelas de alto rendimiento", "escuelas con informes disponibles en NJDOE"),
    ("escuelas altamente calificadas", "escuelas públicas locales"),
    ("escuelas mejor calificadas", "escuelas públicas locales"),
    ("escuelas mejor valoradas", "escuelas públicas locales"),
    ("escuelas premiadas", "escuelas públicas locales"),
    ("escuela secundaria reconocida", "escuela secundaria local"),
    ("escuelas excelentes", "escuelas públicas locales"),
    ("excelentes escuelas", "escuelas públicas locales"),
    ("buenas escuelas", "información escolar oficial"),
    ("fuertes escuelas", "escuelas públicas locales"),
    ("Calificación de Escuelas", "Recursos Oficiales de Escuelas"),
    ("calidad de las escuelas", "información oficial de las escuelas"),
    ("rankings escolares", "informes oficiales de NJDOE"),
    ("ranking escolar", "información oficial de NJDOE"),
    ("GreatSchools", "NJDOE School Performance Reports"),
    ("Mejores Pueblos y Escuelas", "Municipios y Recursos Escolares Oficiales"),
    ("Mejores Pueblos", "Comparación de Municipios"),
    ("mejores pueblos", "municipios para comparar"),
    ("Mejor Pueblo", "Comparación de Municipios"),
    ("Mejores Ciudades", "Comparación de Ciudades"),
    ("mejores ciudades", "ciudades para comparar"),
    ("Mejores Suburbios", "Comparación de Municipios con Acceso a NYC"),
    ("mejores suburbios", "municipios con acceso a NYC"),
    ("Mejores Comunidades", "Comparación de Comunidades"),
    ("mejores comunidades", "comunidades para comparar"),
    ("Mejores Vecindarios", "Comparación de Vecindarios"),
    ("mejores vecindarios", "vecindarios para comparar"),
    ("Pueblo Es el Ideal", "Cómo Comparar los Municipios"),
    ("Pueblo Es Ideal", "Cómo Comparar los Municipios"),
    ("Pueblo Ideal", "Criterios para Comparar Municipios"),
    ("Pueblo Perfecto", "Cómo Elegir Según Criterios Propios"),
    ("pueblo ideal", "municipio que coincida con criterios verificables"),
    ("pueblo perfecto", "municipio que coincida con criterios verificables"),
    ("pueblos premium", "municipios de precios más altos"),
    ("pueblo premium", "municipio de precios más altos"),
    ("comunidades premium", "comunidades de precios más altos"),
    ("comunidades ejecutivas premium", "comunidades con viviendas de precios más altos"),
    ("pueblos ejecutivos premium", "municipios con viviendas de precios más altos"),
    ("suburbio premium", "municipio de precios más altos"),
    ("pueblo de pasajeros premium", "municipio de precios más altos con acceso ferroviario"),
    ("pueblos más prestigiosos", "municipios con distintos tipos y precios de vivienda"),
    ("pueblos más deseables", "municipios que conviene comparar por propiedad"),
    ("uno de los pueblos pequeños más deseables", "un municipio pequeño que los compradores suelen comparar"),
    ("zonas más prestigiosas", "zonas de precios más altos"),
    ("zonas más deseadas", "zonas que conviene comparar por propiedad"),
    ("comunidades de lujo con campos de golf y amenidades premium", "comunidades con campos de golf y amenidades de gama alta"),
    ("diversos vecindarios", "vecindarios con distintos tipos de vivienda"),
    ("vecindarios diversos", "vecindarios con distintos tipos de vivienda"),
    ("vecindario diverso", "vecindario con distintos tipos de vivienda"),
    ("comunidades más diversas", "comunidades con distintos tipos de vivienda"),
    ("comunidades diversas", "comunidades con distintos tipos de vivienda"),
    ("pueblos más diversos", "municipios con distintos tipos de vivienda"),
    ("perfil demográfico", "datos de vivienda y transporte"),
    ("ideal para familias", "con distintos tipos de vivienda"),
    ("ideales para familias", "con distintos tipos de vivienda"),
    ("ambiente familiar", "entorno residencial"),
    ("destino para familias jóvenes", "destino para compradores que comparan vivienda y transporte"),
    ("atraen a diferentes tipos de familias", "ofrecen distintos tipos de vivienda y transporte"),
    ("atraen a familias y profesionales", "ofrecen distintos tipos de vivienda y acceso a centros de empleo"),
    ("atrae tanto a jóvenes profesionales como a familias", "ofrece distintos tipos de vivienda y acceso a centros de empleo"),
    ("atrae a una mezcla diversa de compradores: profesionales", "ofrece distintos tipos de vivienda y acceso a centros de empleo para compradores"),
    ("Popular entre familias y profesionales", "Compare la vivienda disponible y el acceso a centros de empleo"),
    ("atraen a familias", "ofrecen distintos tipos de vivienda"),
    ("atrae a familias", "ofrece distintos tipos de vivienda"),
    ("atrae a profesionales", "ofrece acceso a centros de empleo"),
    ("Atrae a commuters de NYC y a familias", "Ofrece acceso a NYC y distintos tipos de vivienda"),
    ("Atraen a un perfil similar — profesionales jóvenes", "Ofrecen un perfil de vivienda y transporte similar"),
    ("Popular entre familias", "Compare los tipos de vivienda disponibles"),
    ("comunidades seguras", "comunidades cuyos datos públicos deben revisarse directamente"),
    ("ciudades más seguras", "ciudades con datos públicos disponibles para investigación"),
    ("baja criminalidad", "datos de seguridad pública que deben verificarse con fuentes oficiales"),
    ("pueblos correctos para que te sientas seguro", "municipios que puedes comparar mediante fuentes oficiales y visitas personales"),
    ("Seguro de Qué Pueblo", "Cómo Comparar Municipios"),
    ("seguro de qué pueblo", "decidido qué municipio comparar"),
    ("Qué Cómo Comparar los Municipios", "Cómo Comparar los Municipios"),
    ("qué municipio coincide mejor con criterios verificables", "cómo se comparan los municipios según criterios verificables"),
    ("Qué municipio coincide mejor con criterios verificables", "Cómo se comparan los municipios según criterios verificables"),
    ("municipio coincide mejor con criterios verificables", "municipio se ajusta a criterios verificables"),
    ("municipio comparar", "municipio para comparar"),
    ("distintos balance", "distintos equilibrios"),
    ("las propietarios", "los propietarios"),
    ("Las Propietarios", "Los Propietarios"),
    ("las Propietarios", "los Propietarios"),
    ("municipios para comparar de NJ", "municipios de NJ que conviene comparar"),
    ("municipios para comparar de Nueva Jersey", "municipios de Nueva Jersey que conviene comparar"),
    ("Municipios para Comparar de NJ", "Municipios de NJ para Comparar"),
    ("Comparación de Municipios de NJ para Familias", "Comparación de Municipios de NJ"),
    ("Comparación de Municipios para Familias", "Comparación de Municipios"),
    ("Comparación de Ciudades NJ para Familias 2026 | Escuelas y Valor", "Comparación de Municipios de NJ | Vivienda y Fuentes Oficiales"),
    ("stock de vivienda", "inventario de viviendas"),
    ("Stock de vivienda", "Inventario de viviendas"),
    ("Downtown", "Centro urbano"),
    ("downtown", "centro urbano"),
    ("tour de casas", "recorrido de propiedades"),
    ("escuelas top-tier", "información escolar oficial"),
    ("escuelas top 3", "informes escolares vigentes de NJDOE"),
    ("escuelas top-5 de NJ", "informes escolares vigentes de NJDOE"),
    ("escuelas top", "información escolar oficial"),
    ("escuelas A+", "escuelas públicas locales con informes disponibles en NJDOE"),
    ("Escuelas A+", "Escuelas públicas locales con informes disponibles en NJDOE"),
    ("personas con nido vacío", "propietarios que reducen su vivienda"),
    ("Personas con Nido Vacío", "Propietarios que Reducen su Vivienda"),
    ("Nido Vacío", "Reducción de Vivienda"),
    ("nido vacío", "reducción de vivienda"),
    ("jóvenes profesionales", "compradores que comparan acceso a centros de empleo"),
    ("Jóvenes Profesionales", "Compradores que Comparan Acceso a Centros de Empleo"),
    ("Top Rated", "Con Licencia en Nueva Jersey"),
    ("top-rated", "licensed New Jersey"),
)


REGEX_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(?:uno|una) de los (?:pueblos|suburbios) m[aá]s deseables\b", re.I), "un municipio que los compradores suelen comparar"),
    (re.compile(r"\bpueblos? (?:del Condado de [A-Za-zÁÉÍÓÚáéíóúñÑ]+ )?son mejores\b", re.I), "municipios ofrecen distintas opciones según la propiedad"),
    (re.compile(r"\bpueblo tiene mejor\b", re.I), "municipio ofrece distintas"),
    (re.compile(r"\bpueblo es mejor\b", re.I), "municipio coincide mejor con criterios verificables"),
    (re.compile(r"\bpueblos exigen precios(?: de casa)? premium\b", re.I), "municipios registran precios de vivienda más altos"),
    (re.compile(r"\bpueblos ofrecen un valor considerablemente mejor\b", re.I), "municipios ofrecen distintos precios y tipos de vivienda"),
    (re.compile(r"\bcomunidades ofrecen el mejor\b", re.I), "comunidades ofrecen distintos"),
    (re.compile(r"\bescuelas? (?:tienen|con) el mejor\b", re.I), "escuelas publican información oficial sobre"),
    (re.compile(r"\b(?:fuerte|demanda fuerte) impulsada por sus escuelas\b", re.I), "demanda que debe evaluarse con ventas recientes de propiedades comparables"),
)


FILE_REPLACEMENTS: dict[str, tuple[tuple[str, str], ...]] = {
    "es/55-plus-communities-nj.html": (
        (
            "El 20% restante puede incluir cónyuges menores de 55, hijos adultos (por lo general de 18 a 22 años en algunas comunidades) y cuidadores. En general se restringe la residencia de tiempo completo a menores de 18 años. Las reglas exactas varían según la comunidad; verifica siempre con la Asociación de Propietarios antes de comprar.",
            "Cada comunidad establece sus propias reglas de ocupación dentro del marco aplicable. Antes de comprar, solicita y revisa los documentos vigentes de la Asociación de Propietarios y consulta a un profesional jurídico si necesitas interpretar sus requisitos.",
        ),
        (
            "El 20% restante puede incluir cónyuges menores de 55, hijos adultos y cuidadores.",
            "Las reglas de ocupación adicionales dependen de los documentos vigentes de cada comunidad y deben verificarse directamente.",
        ),
        (
            "se permiten cónyuges menores de 55, hijos adultos (de 18 a 22 años en algunas comunidades) y cuidadores, siempre que el 80% de las unidades tenga al menos un residente de 55+. Los menores de 18 años suelen estar prohibidos.",
            "las reglas para otros ocupantes dependen de los documentos vigentes de cada comunidad. Solicita esos documentos y confirma los requisitos con la Asociación de Propietarios antes de comprar.",
        ),
        (
            "Para quienes recién quedan con el nido vacío o para compradores viudos, esto puede ser transformador.",
            "Quienes comparan este tipo de vivienda deben revisar el calendario, los costos y las reglas de participación de cada comunidad.",
        ),
    ),
    "es/blog/chatham-vs-madison-nj.html": (
        ("Escuelas: Ambas Excelentes", "Escuelas: Consulte los Informes Oficiales de NJDOE"),
        ("ideales para familias", "con distintos tipos de vivienda"),
        ("atraen a tipos de familias", "ofrecen distintos tipos de vivienda"),
        ("comunidades ideales", "comunidades para comparar por propiedad"),
        ("pueblos son direcciones premium", "municipios tienen viviendas de precios más altos"),
        ("sus escuelas locales (9-10 de 10)", "su oferta de vivienda y su inventario más limitado"),
        ("9-10/10 (distrito más pequeño)", "Distrito más pequeño; consulte NJDOE"),
        ("8-9/10 (distrito sólido)", "Distrito más grande; consulte NJDOE"),
        ("Escuelas calificadas 9-10/10", "Informes escolares disponibles en NJDOE"),
        ("Escuelas calificadas 8-9/10", "Informes escolares disponibles en NJDOE"),
        ("escuelas locales (9-10/10)", "informes escolares vigentes de NJDOE"),
        ("escuelas locales (9-10 de 10)", "informes escolares vigentes de NJDOE"),
        ("el suburbio tranquilo", "un municipio de carácter residencial"),
        ("Pueblo: Aldea Tranquila", "Centro: Escala Pequeña"),
        ("pueblo más tranquilo", "municipio con menos actividad nocturna"),
        ("suburbio más tranquilo", "municipio con menos actividad nocturna"),
        ("Suburbio Tranquilo", "Municipio Residencial"),
        ("Tranquilo, residencial, enfocado en la familia", "Residencial, con un centro de menor escala"),
        ("calmado y enfocado en la familia", "residencial y de menor escala"),
        ("enfocada en la familia", "de carácter residencial"),
        (
            "Las escuelas son un motivo principal para las familias que se mudan tanto a Chatham como a Madison. Ambos pueblos tienen distritos muy bien calificados, pero la estructura y el tamaño difieren.",
            "Chatham y Madison tienen distritos escolares públicos distintos. Compare su estructura, programas e informes de rendimiento vigentes directamente en NJDOE.",
        ),
        (
            "Chatham es el suburbio tranquilo por excelencia. Es residencial, calmado y enfocado en la familia en el sentido tradicional. Las familias se mudan aquí por las escuelas y por el ambiente seguro y vecinal. Los deportes juveniles, los eventos escolares y las organizaciones comunitarias son el motor de la vida social. El pueblo no tiene mucha vida nocturna ni entretenimiento — y ese es precisamente el punto. Quienes eligen Chatham buscan paz, espacio y una comunidad unida donde los niños andan en bicicleta y los vecinos se conocen. El viaje a NYC es lo bastante rápido como para trabajar allí a diario, y el pueblo en sí es un refugio de ese ritmo.",
            "Chatham tiene un patrón principalmente residencial y un centro comercial de menor escala. Para comparar con Madison, revise horarios actuales de NJ Transit, inventario de vivienda, impuestos y servicios municipales, además de los informes escolares vigentes de NJDOE. Visite ambos municipios a distintas horas para evaluar el tránsito, la actividad comercial y el acceso desde cada propiedad.",
        ),
        (
            "Si quieres un pueblo donde todo cierra a las 9 PM y el enfoque está por completo en la familia y las escuelas, Chatham es tu respuesta.",
            "Si prefieres un centro de menor escala y un patrón principalmente residencial, incluye Chatham en tu comparación.",
        ),
        ("El Veredicto: Suburbio Tranquilo vs Pueblo Activo", "Comparación: Escala Residencial y Actividad Comercial"),
        ("Tu máxima prioridad son las escuelas locales (9-10/10)", "Deseas comparar los informes escolares vigentes de NJDOE"),
        ("Prefieres una comunidad calmada y enfocada en la familia por encima de la vida nocturna", "Prefieres un centro de menor escala y menos actividad comercial nocturna"),
        (
            "Ambos son mercados de vendedores fuertes, pero Chatham tiene un inventario más ajustado, lo que da a los vendedores más ventaja. Las casas bien tasadas en Chatham reciben con frecuencia ofertas múltiples. Madison también vende bien, en particular las casas cerca del centro y de la estación de tren, pero un poco más de inventario significa un poco menos de urgencia entre los compradores.",
            "Las condiciones cambian por fecha, rango de precio y estado de la propiedad. Compare ventas cerradas y listados activos recientes en cada municipio antes de fijar una estrategia.",
        ),
        (
            "El Distrito Escolar de los Chathams atiende tanto a Chatham Borough como a Chatham Township. Es uno de los distritos mejor calificados del Condado de Morris y del estado, con escuelas calificadas de manera constante entre 9 y 10 de 10.",
            "El Distrito Escolar de los Chathams atiende tanto a Chatham Borough como a Chatham Township. Consulte sus programas e informes de rendimiento vigentes directamente en NJDOE.",
        ),
        (
            "Chatham es un municipio de carácter residencial por excelencia. Es residencial, residencial y de menor escala en el sentido tradicional. Las familias se mudan aquí por las escuelas y por el ambiente seguro y vecinal. Los deportes juveniles, los eventos escolares y las organizaciones comunitarias son el motor de la vida social. El pueblo no tiene mucha vida nocturna ni entretenimiento — y ese es precisamente el punto. Quienes eligen Chatham buscan paz, espacio y una comunidad unida donde los niños andan en bicicleta y los vecinos se conocen. El viaje a NYC es lo bastante rápido como para trabajar allí a diario, y el pueblo en sí es un refugio de ese ritmo.",
            "Chatham tiene un patrón principalmente residencial y un centro comercial de menor escala. Para compararlo con Madison, revise horarios actuales de NJ Transit, inventario de vivienda, impuestos y servicios municipales, además de los informes escolares vigentes de NJDOE. Visite ambos municipios a distintas horas para evaluar el tránsito, la actividad comercial y el acceso desde cada propiedad.",
        ),
        (
            "Chatham y Madison son ambos lugares excelentes para vivir y criar una familia. Comparten el acceso Midtown Direct, información escolar oficial y comunidades cuyos datos públicos deben revisarse directamente y acogedoras. La diferencia está en el volumen — Chatham lo tiene bajo, Madison lo tiene alto.",
            "Chatham y Madison tienen servicio Midtown Direct, distritos escolares locales y centros comerciales de distinta escala. Compare horarios, impuestos, vivienda, servicios municipales e informes escolares oficiales para cada propiedad.",
        ),
        (
            "Jorge ha ayudado a familias a tomar exactamente esta decisión docenas de veces. Una llamada de 15 minutos puede ayudarte a descubrir qué pueblo encaja con tu estilo de vida antes de pasar fines de semana en casas abiertas en el pueblo equivocado.",
            "Una consulta puede ayudarte a organizar una comparación basada en horarios de transporte, vivienda, impuestos y ventas recientes antes de visitar propiedades.",
        ),
        ("Encuentra Tu Criterios para Comparar Municipios en el Condado de Morris", "Compara Propiedades en el Condado de Morris"),
        ("Ya sea Chatham, Madison o alguna de las otras extraordinarias comunidades del Condado de Morris, Jorge te ayudará a encontrar la opción indicada para tu familia y tu presupuesto.", "Jorge puede ayudarte a comparar propiedades de Chatham, Madison y otros municipios del Condado de Morris según ubicación, estado, costos y presupuesto."),
    ),
    "es/blog/index.html": (
        (
            "Descubre los municipios para comparar de Nueva Jersey para quienes viajan a NYC en 2026. Compara tiempos de tren, costos y calidad de vida en Summit, Millburn, Montclair, Maplewood y más.",
            "Compara municipios de Nueva Jersey por horarios de tren, costos de vivienda, impuestos y servicios municipales. Verifica los horarios actuales directamente con NJ Transit.",
        ),
    ),
    "es/blog/downsizing-your-nj-home.html": (
        ("Mudarte a una Casa Más Pequeña en NJ: Guía para el Reducción de Vivienda", "Viviendas Más Pequeñas en NJ: Guía para Propietarios"),
        ("Mudarte a una Casa Más Pequeña en NJ: Guía para el Reducción de Vivienda y Propietarios | Jorge Ramirez", "Viviendas Más Pequeñas en NJ: Guía para Propietarios"),
        ("Mudarte a una Casa Más Pequeña en NJ | Jorge Ramirez", "Viviendas Más Pequeñas en NJ: Guía para Propietarios"),
        ("casa familiar", "vivienda de muchos años"),
        ("Casa Familiar", "Vivienda de Muchos Años"),
        ("jubilados", "propietarios de distintas edades"),
        ("Para muchas familias de NJ", "Para muchos propietarios de NJ"),
        ("Los detonantes más comunes incluyen que los hijos se muden, el aumento de los costos de mantenimiento, querer liberar la plusvalía para la jubilación, o simplemente darte cuenta de que estás pagando por calentar y mantener habitaciones que nadie usa.", "Las razones pueden incluir costos de mantenimiento, espacio que ya no se utiliza o el deseo de comparar una vivienda distinta y su efecto financiero."),
        ("Tus Hijos Ya Se Fueron de Casa", "Tienes Espacio que Ya No Utilizas"),
        ("Algunos propietarios hacen el cambio cuando los hijos se van a la universidad. Otros esperan hasta la jubilación.", "Algunos propietarios hacen el cambio cuando los costos o el espacio dejan de ajustarse a sus necesidades; otros esperan hasta que su calendario financiero lo permita."),
        ("Aquí criaste a tu familia. Aquí hiciste tu vida.", "Has vivido aquí durante años y acumulado recuerdos."),
        ("la casa que era perfecta para una familia de cinco", "una vivienda que antes se ajustaba a tus necesidades"),
        ("El patio donde jugaban los niños ahora cuesta $200 al mes en jardinería.", "El mantenimiento del patio también debe incluirse en el costo total."),
        ("financiando tu jubilación, eliminando deudas, ayudando a tus hijos con sus cuotas iniciales, o simplemente dándote libertad financiera", "financiando otros objetivos, reduciendo deudas o aumentando tu flexibilidad financiera"),
        ("Criaste a tu familia en esta casa. Tus hijos dieron sus primeros pasos aquí. Las marcas en el marco de la puerta donde medías su estatura siguen ahí.", "Una vivienda de muchos años reúne recuerdos y decisiones personales que no aparecen en una hoja de cálculo."),
        ("Involucra a Tu Familia", "Involucra a Quienes Participan en la Decisión"),
        ("Los hijos adultos suelen tener sentimientos encontrados cuando se vende la vivienda de muchos años. Incluirlos en la conversación desde el principio — explicando tus razones, mostrándoles los beneficios financieros — puede ayudar a que todos estén en la misma página. Muchos hijos adultos terminan aliviados de que sus padres estén reduciendo sus cargas y mejorando su calidad de vida.", "Si otras personas participan en la decisión o en la titularidad, inclúyelas desde el principio. Compartir el calendario, los costos estimados y las opciones de vivienda ayuda a mantener la conversación centrada en hechos verificables."),
    ),
    "es/blog/decluttering-items-home-value-nj.html": (
        (
            "Recorreré tu casa contigo y te diré exactamente qué conservar, qué guardar y qué arreglar — sin costo y sin compromiso. Muchas familias han confiado en mí para su inversión más grande. Déjame ayudarte con la tuya.",
            "Puedo recorrer la propiedad contigo y ayudarte a priorizar qué conservar, guardar o reparar antes de vender, sin costo ni compromiso. La recomendación se basa en el estado de la vivienda, el presupuesto y ventas comparables recientes.",
        ),
    ),
    "es/blog/maplewood-vs-south-orange-nj.html": (
        ("escuelas primarias, con un perfil similar — fuerte", "escuelas primarias; consulte los informes vigentes de NJDOE"),
        ("pueblos ofrecen un valor considerablemente mejor", "municipios ofrecen distintos precios y tipos de vivienda"),
        ("el pueblo se siente más acogedor y tranquilo", "el municipio tiene un centro de menor escala"),
        ("La experiencia educativa de tus hijos es la misma sin importar en cuál pueblo vivas.", "Ambos municipios pertenecen al mismo distrito escolar; revise sus programas e informes vigentes directamente en NJDOE."),
        ("familias que se mudan desde NYC, Brooklyn y Jersey City buscando espacio", "compradores que comparan vivienda y acceso ferroviario desde NYC, Brooklyn y Jersey City"),
        (
            "El distrito compartido significa que la experiencia de preparatoria de tus hijos es la misma sin importar en cuál pueblo vivas.",
            "El distrito compartido significa que ambos municipios remiten a los mismos informes de secundaria y preparatoria; consúltelos directamente en NJDOE.",
        ),
        (
            "El pueblo se siente más acogedor y tranquilo que Maplewood la mayoría de las noches.",
            "El centro tiene una escala y un nivel de actividad nocturna distintos a los de Maplewood.",
        ),
        ("Prefieres un centro más acogedor y tranquilo con encanto universitario", "Prefieres un centro de menor escala junto a servicios universitarios y culturales"),
        (
            "Esto significa que la experiencia de secundaria y preparatoria de tus hijos es la misma sin importar en cuál pueblo elijas vivir.",
            "Ambos municipios comparten las mismas escuelas de secundaria y preparatoria; consulte los informes vigentes de NJDOE.",
        ),
        (
            "Ya sea Maplewood, South Orange u otra de las excelentes comunidades del Condado de Essex, Jorge te ayudará a encontrar la opción correcta para tu familia y tu presupuesto.",
            "Jorge puede ayudarte a comparar propiedades en Maplewood, South Orange y otros municipios del Condado de Essex según ubicación, estado, costos y presupuesto.",
        ),
    ),
    "es/blog/moving-from-nyc-to-nj-guide.html": (
        ("Todo lo que los profesionales y las familias de NYC necesitan saber para mudarse a Nueva Jersey", "Información práctica para mudarse de NYC a Nueva Jersey"),
        (
            "Su trabajo es ayudarte a encontrar el pueblo que se ajuste a tu vida y luego negociar el mejor trato posible en la casa que elijas.",
            "Su trabajo es ayudarte a comparar información verificable de cada municipio y, cuando elijas una propiedad, preparar y negociar una oferta fundamentada.",
        ),
        (
            "Su trabajo es ayudarte a encontrar el municipio que coincida con tus criterios y luego negociar una oferta fundamentada trato posible en la casa que elijas.",
            "Su trabajo es ayudarte a comparar información verificable de cada municipio y, cuando elijas una propiedad, preparar y negociar una oferta fundamentada.",
        ),
        ("vecindarios diversos", "vecindarios con distintos tipos de vivienda"),
        ("familias viajeras", "personas que viajan a NYC"),
        ("tus hijos se acercan a la edad escolar (o ya están ahí), y te diste cuenta de que el mismo dinero podría comprarte una casa de cuatro habitaciones con jardín, garaje para dos autos y algunas de las mejores escuelas públicas del país", "estás comparando cuánto espacio, transporte e impuestos puede cubrir el mismo presupuesto en Nueva Jersey"),
        ("más espacio, mejores escuelas, un jardín y un garaje", "distintos tipos de vivienda, espacio exterior y estacionamiento"),
        ("los distritos escolares públicos mejor calificados reemplazan la matrícula de escuela privada", "cada distrito escolar público publica programas e informes de rendimiento que conviene revisar directamente en NJDOE"),
        ("Si tienes hijos o planeas tenerlos, las escuelas", "Al comparar una propiedad, la información oficial de las escuelas"),
        ("¿No Estás Seguro de Cómo Comparar los Municipios para Ti?", "¿Necesitas Ayuda para Comparar Municipios?"),
        ("New Providence</a> — 45 min, mediana $750K, tranquilo, con distintos tipos de vivienda, impuestos más bajos que sus vecinos", "New Providence</a> — consulte horarios de NJ Transit, ventas recientes, tipos de vivienda e impuestos por propiedad"),
        ("¿No Estás Seguro de Cómo Comparar los Municipios para Ti?", "¿Necesitas Ayuda para Comparar Municipios?"),
    ),
    "es/blog/selling-inherited-home-nj.html": (
        ("casa familiar", "vivienda heredada"),
        (
            "<strong>Jorge ha ayudado a decenas de familias de NJ a navegar exactamente esta situación.</strong> Al haber comprado, renovado y vendido casas personalmente por toda Nueva Jersey, entiende las propiedades heredadas desde todos los ángulos: problemas de condición, retos de precio y la dinámica emocional única que conllevan. <a href=\"tel:+19082307844\">Llama al 908-230-7844</a> para una conversación confidencial sobre tu situación.",
            "Jorge puede ayudarte a comparar el estado de una propiedad heredada, presupuestos de reparación, ventas recientes y opciones de calendario antes de decidir cómo vender. <a href=\"tel:+19082307844\">Llama al 908-230-7844</a> para conversar sobre la propiedad y los próximos pasos.",
        ),
    ),
    "es/blog/probate-real-estate-nj-guide.html": (
        (
            "He trabajado con docenas de familias durante procesos de sucesión inmobiliaria en NJ. Antes de ser agente licenciado, trabajé como inversionista renovando propiedades — incluidas ventas de patrimonios. Esta es la guía clara y directa que me hubiera gustado tener desde el primer día.",
            "Esta guía resume pasos habituales para preparar y vender una propiedad durante una sucesión en Nueva Jersey. Cada caso depende de la documentación, los plazos del tribunal y el asesoramiento jurídico y fiscal correspondiente.",
        ),
    ),
    "es/blog/summit-vs-westfield-nj.html": (
        ("¿Qué pueblo del Condado de Union es el ideal para ti?", "¿Cómo se comparan Summit y Westfield?"),
        ("¿Qué Cómo Comparar los Municipios para Ti?", "¿Cómo se Comparan Estos Municipios?"),
        ("Dos de los municipios para comparar del Condado de Union. Ambos tienen escuelas A+, centros encantadores y mercados de bienes raíces fuertes. Pero no son iguales — y las diferencias importan. Así es como se comparan.", "Dos municipios del Condado de Union con opciones distintas de vivienda, transporte y servicios municipales. Compare datos actuales y criterios específicos de cada propiedad."),
        ("Summit High School clasificada entre las mejores escuelas públicas de NJ", "Summit High School publica información de programas y rendimiento en NJDOE"),
        ("el pueblo en sí es tranquilo", "el municipio tiene un centro compacto"),
        ("un aire de suburbio familiar clásico", "un patrón residencial de mayor escala"),
        ("¿Qué pueblo del Condado de Union es el ideal", "¿Cómo se comparan estos municipios del Condado de Union"),
        (
            "Summit sigue siendo uno de los mercados de vendedores más fuertes de NJ. La combinación del acceso al Midtown Direct, las escuelas públicas locales con informes disponibles en NJDOE y el inventario limitado hace que las casas con buen precio reciban regularmente múltiples ofertas. Los días en el mercado para las casas con buen precio promedian de 14 a 30 días. El sobreprecio que los compradores están dispuestos a pagar por el trayecto del Midtown Direct mantiene los precios fuertes incluso cuando el mercado general se debilita.",
            "Las condiciones de venta en Summit cambian por fecha, rango de precio, ubicación y estado de la propiedad. Compare ventas cerradas y listados activos recientes; además, verifique horarios de NJ Transit y datos específicos de la propiedad antes de fijar una estrategia.",
        ),
        ("Summit y Westfield son ambos lugares excepcionales para vivir. Los dos están en el Condado de Union, los dos tienen escuelas públicas locales con informes disponibles en NJDOE, los dos tienen centros encantadores y los dos tienen mercados de bienes raíces fuertes.", "Summit y Westfield están en el Condado de Union y cuentan con distritos escolares locales, centros comerciales y servicio ferroviario con características distintas."),
        ("dos de los municipios para comparar del Condado de Union", "dos municipios del Condado de Union"),
        (
            "Westfield tiene un aire suburbano clásico más americano. Está orientado a la familia con un fuerte énfasis en los deportes juveniles, las actividades escolares y los eventos comunitarios. El centro es más concurrido y social — las noches de viernes se sienten animadas, las mañanas de fin de semana se llenan de familias en los restaurantes y cafeterías. Westfield tiene un inventario de viviendas y un rango de precios ligeramente más diversos, lo que crea una mezcla socioeconómica más amplia. La comunidad es cálida, acogedora y profundamente arraigada en la tradición.",
            "Westfield abarca un área residencial y un centro comercial de mayor escala que Summit. Compare la actividad comercial, los servicios municipales, los tipos de vivienda, los impuestos y el acceso ferroviario desde cada propiedad.",
        ),
        (
            "<strong>En resumen:</strong> Summit es más íntimo y acomodado. Westfield es más animado y familiar. Ambos son lugares excelentes para vivir y criar una familia.",
            "<strong>En resumen:</strong> Summit y Westfield ofrecen distintas escalas de centro, tipos de vivienda, costos y opciones de transporte que deben revisarse por propiedad.",
        ),
        ("Encuentra Tu Cómo Elegir Según Criterios Propios en el Condado de Union", "Compara Propiedades en el Condado de Union"),
        (
            "Ya sea Summit, Westfield o cualquiera de las otras comunidades sobresalientes del Condado de Union, Jorge te ayudará a encontrar la opción correcta para tu familia y tu presupuesto.",
            "Jorge puede ayudarte a comparar propiedades en Summit, Westfield y otros municipios del Condado de Union según ubicación, estado, costos y presupuesto.",
        ),
    ),
    "es/buy-a-home.html": (
        ("Quieres más espacio, mejores escuelas y un patio", "Quieres comparar más espacio, transporte y costos de propiedad"),
        ("desde pueblos con centros caminables hasta tranquilos suburbios arbolados", "desde municipios con centros peatonales hasta zonas residenciales con distintos tipos de vivienda"),
        ("desde pueblos con centros caminables hasta tranquilos vecindarios suburbanos con escuelas locales", "desde municipios con centros peatonales hasta zonas residenciales con distintos tipos de vivienda y distritos escolares locales"),
        ("distintos equilibrios de tiempo de viaje, impuestos a la propiedad, calidad escolar y estilo de vida para profesionales de NYC", "diferencias en horarios de transporte, impuestos por propiedad, tipos de vivienda e informes escolares oficiales"),
    ),
    "es/counties/hudson-county.html": (
        ("jóvenes profesionales", "compradores que comparan acceso a centros de empleo"),
        ("¿Qué municipios ofrecen distintas opciones según la propiedad para familias?", "¿Qué opciones de vivienda se pueden comparar en el Condado de Hudson?"),
        (
            "Aunque el Condado de Hudson es más conocido por los compradores que comparan acceso a centros de empleo y la vida urbana, varias comunidades funcionan bien para familias. Secaucus ofrece un ambiente suburbano con excelente acceso a NYC y precios más accesibles que Hoboken o Centro urbano Jersey City. Bayonne ofrece un sentido de comunidad unida con acceso al waterfront y una conexión de light rail. Partes de North Bergen y Kearny ofrecen casas unifamiliares con jardín a precios muy por debajo de los pueblos del waterfront. Muchas familias finalmente hacen la transición del Condado de Hudson a comunidades suburbanas en los condados de Union, Essex o Morris a medida que sus hijos llegan a la edad escolar.",
            "El Condado de Hudson ofrece condominios, townhouses y casas unifamiliares en distintos municipios. Compare el tipo y estado de cada propiedad, los impuestos, el precio, el acceso al transporte y los servicios municipales; verifique horarios con NJ Transit y fuentes locales vigentes.",
        ),
        (
            "Aunque el Condado de Hudson es más conocido por los compradores que comparan acceso a centros de empleo y la vida urbana, varias comunidades funcionan bien para familias. Secaucus ofrece el ambiente más suburbano del condado con casas unifamiliares, un carácter residencial tranquilo y excelente acceso a autopistas hacia NYC y parques corporativos. Bayonne ofrece una comunidad unida con parques del waterfront, una conexión de light rail y precios de vivienda que permiten a las familias comprar en lugar de rentar. Partes de North Bergen y Kearny ofrecen casas unifamiliares con jardín a precios muy por debajo de los pueblos del waterfront. Muchas familias finalmente hacen la transición del Condado de Hudson a comunidades suburbanas en los condados de Union, Essex o Morris cuando sus hijos llegan a la edad escolar — y Jorge ayuda con ambos lados de ese cambio.",
            "El Condado de Hudson ofrece condominios, townhouses y casas unifamiliares en distintos municipios. Compare el tipo y estado de cada propiedad, los impuestos, el precio, el acceso al transporte y los servicios municipales; verifique horarios con NJ Transit y fuentes locales vigentes.",
        ),
    ),
    "es/counties/middlesex-county.html": (
        ("familias con escuelas con informes disponibles en NJDOE, inventario de viviendas", "compradores que comparan informes escolares de NJDOE e inventario de viviendas"),
        ("El mejor pueblo depende de tus prioridades", "La comparación depende de tus criterios"),
        ("el mejor pueblo depende de tus prioridades", "la comparación depende de tus criterios"),
        ("imanes para familias con escuelas con informes disponibles en NJDOE, inventario de viviendas moderno", "municipios donde conviene comparar los informes escolares vigentes de NJDOE y el inventario de viviendas"),
        ("una de las comunidades con distintos tipos de vivienda de Estados Unidos", "un municipio con una amplia variedad de viviendas"),
        ("uno de los municipios con distintos tipos de vivienda de Estados Unidos", "un municipio con una amplia variedad de viviendas"),
    ),
    "es/counties/morris-county.html": (
        ("combina las mejores escuelas con uno de los viajes más cortos con Midtown Direct del Condado de Morris", "cuenta con un distrito escolar local y servicio Midtown Direct; verifique los informes de NJDOE y horarios actuales de NJ Transit"),
        ("familias con niños", "compradores que comparan tipos de vivienda"),
    ),
    "es/counties/somerset-county.html": (
        ("casa familiar", "casa unifamiliar"),
        ("casas familiares", "casas unifamiliares"),
        ("familias en crecimiento", "compradores que comparan más espacio"),
        ("vecindarios familiares de Bridgewater y Hillsborough", "zonas residenciales con distintos tipos de vivienda en Bridgewater y Hillsborough"),
    ),
    "es/counties/union-county.html": (
        ("su reconocido centro y sus escuelas con informes disponibles en NJDOE", "su centro comercial y su distrito escolar local, cuyos informes vigentes están disponibles en NJDOE"),
        ("casa familiar", "casa unifamiliar"),
        ("familias en crecimiento", "compradores que comparan más espacio"),
    ),
    "es/cranford-vs-westfield-nj.html": (
        ("Familias que buscan valor y quieren un pueblo", "Compradores que comparan precio, vivienda y transporte y quieren un municipio"),
        ("quieres un centro más completo y escuelas ligeramente mejores", "quieres comparar un centro comercial de mayor escala y los informes escolares vigentes de NJDOE"),
        ("Cranford es uno de los pueblos del Condado de Union con mejor relación calidad-precio ahora mismo", "Cranford ofrece una combinación distinta de precios, vivienda y transporte que debe compararse con ventas recientes"),
    ),
    "es/downsizing-nj.html": (
        ("casa familiar", "vivienda actual"),
        ("Casa Familiar", "Vivienda Actual"),
        ("familias jóvenes que dan el salto desde su primera casa son los compradores más probables para una vivienda actual de 4 recámaras. El sistema de inteligencia artificial de Jorge pone tu listado frente a ese grupo demográfico exacto en pueblos de personas que viajan al trabajo, a través de Facebook, YouTube e Instagram", "la estrategia publicitaria se configura por ubicación e intención de compra, sin seleccionar ni excluir audiencias por características protegidas. La campaña presenta la propiedad en portales y canales digitales y se ajusta según resultados verificables"),
        ("Perfilado del Comprador Ideal", "Distribución Publicitaria de la Propiedad"),
        ("pueblos más tranquilos del Condado de Morris", "municipios del Condado de Morris con distintos tipos de vivienda"),
        ("jubilados", "propietarios que evalúan una mudanza"),
        ("familias jóvenes", "compradores activos"),
        ("Los hijos se fueron. La casa grande es demasiado para mantener. Quieres algo más pequeño, más fácil, quizás más cerca de los nietos.", "La vivienda actual puede requerir más espacio, mantenimiento o costos de los que deseas asumir."),
        ("Jorge ha ayudado a muchas personas con reducción de vivienda en NJ a reducir de tamaño.", "Jorge asesora a propietarios de NJ que comparan la venta de su vivienda actual con la compra de una propiedad más pequeña."),
    ),
    "es/index.html": (
        ("Descubre qué pueblos de NJ te dan el mejor trayecto, escuelas y valor para tu presupuesto.", "Compara pueblos de NJ por horarios de transporte, vivienda, impuestos e información escolar oficial."),
        ("Las mejores escuelas, vecindarios seguros y gran valor. Encuentra el pueblo de NJ correcto para las prioridades de tu familia.", "Compara vivienda, transporte, impuestos, servicios municipales e informes escolares oficiales según tus propios criterios."),
    ),
    "es/inherited-home-nj.html": (
        (
            "Perder a un ser querido es difícil. Lidiar con su casa mientras estás de luto lo es aún más. Jorge Ramirez guía a los herederos y albaceas por todo el proceso: los tiempos de la sucesión, la base fiscal, la coordinación entre varios herederos y la decisión de vender tal como está o arreglarla primero. Sin presión, sin ventas forzadas. Solo orientación clara de alguien que ha ayudado a decenas de familias de NJ a manejar esto.",
            "Perder a un ser querido es difícil, y atender una propiedad heredada puede añadir decisiones complejas. Jorge Ramirez puede ayudar a herederos y albaceas a organizar el calendario de venta, el estado de la vivienda, la coordinación entre las personas autorizadas y las opciones para vender tal como está o después de reparaciones. Consulta a profesionales jurídicos y fiscales para el asesoramiento correspondiente.",
        ),
        (
            "Jorge ha ayudado a muchas familias de NJ a vender casas heredadas, desde propiedades impecables y bien mantenidas hasta casas que no se habían tocado en 40 años. La primera conversación nunca es sobre listar la casa. Es sobre entender el estado de la sucesión, la situación fiscal y lo que realmente quieren todos los herederos.",
            "Jorge asesora a herederos y albaceas que evalúan la venta de una propiedad en Nueva Jersey. La primera conversación se centra en el estado de la sucesión, el calendario, la documentación disponible y los objetivos de quienes tienen autoridad para decidir.",
        ),
        (
            "Antes de convertirse en agente inmobiliario de tiempo completo en 2017, Jorge trabajó personalmente renovando y revendiendo casas por todo NJ. Ha recorrido decenas de casas anticuadas de sucesiones y puede decirte en 10 minutos si vale la pena gastar $20,000 en pintura y pisos para ganar $60,000 más en la venta, o si es más inteligente venderla tal como está a uno de sus contactos inversionistas la próxima semana.",
            "Jorge puede revisar el estado de la propiedad y comparar escenarios de venta tal como está o después de reparaciones. Las recomendaciones deben apoyarse en presupuestos, plazos y ventas comparables recientes; los resultados y tiempos de venta no están garantizados.",
        ),
        (
            "Las casas heredadas a menudo necesitan actualizaciones, y promocionarlas al público equivocado le hace perder el tiempo a todos. La segmentación de compradores con inteligencia artificial de Jorge empareja cada casa heredada con el grupo de compradores más propenso a hacer una oferta real, ya sea una familia minorista que ama un proyecto de renovación o un inversionista que escribe ofertas en efectivo.",
            "Las propiedades heredadas pueden requerir reparaciones o una estrategia de venta tal como están. La publicidad se distribuye por ubicación, características de la propiedad e intención de búsqueda, sin seleccionar ni excluir audiencias por características protegidas.",
        ),
    ),
    "es/investment-property-nj.html": (
        ("Pueblos de Essex y el Condado de Union Ideales para Renovar", "Municipios de Essex y Union para Analizar Proyectos de Renovación"),
    ),
    "es/montclair-vs-maplewood-nj.html": (
        ("Familias que quieren escuelas diversas y progresistas en un entorno de pueblo", "Compradores que desean revisar información oficial de escuelas, vivienda y transporte"),
        ("Compradores que desean revisar información oficial de escuelas, vivienda y transporte", "Personas que comparan vivienda, transporte e informes escolares oficiales"),
    ),
    "es/nj-real-estate-questions-answers.html": (
        ("El mejor pueblo depende de tu tolerancia al traslado, tu presupuesto, tus prioridades escolares y tu estilo de vida.", "Compare los municipios según horarios actuales de transporte, presupuesto, impuestos, vivienda e informes escolares oficiales."),
        ("sus escuelas públicas Blue Ribbon", "su distrito escolar público y los informes vigentes de NJDOE"),
        ("El mercado atrae con fuerza a quienes viajan a NYC y a las familias que priorizan la información oficial de las escuelas.", "Quienes investigan Westfield deben verificar ventas recientes, horarios actuales de NJ Transit e informes escolares vigentes de NJDOE."),
        ("un ambiente más tranquilo y suburbano que los pueblos para viajeros del condado de Union", "un patrón residencial y de transporte distinto al de los municipios del condado de Union"),
        ("familias con ventas de propiedades heredadas", "propietarios con ventas de propiedades heredadas"),
        ("agente inmobiliario con licencia en Nueva Jersey de NJ", "agente inmobiliario con licencia en Nueva Jersey"),
        ("¿Cuáles son los distritos escolares para investigar con fuentes oficiales de NJ?", "¿Dónde puedo consultar información oficial sobre los distritos escolares de NJ?"),
        ("¿Cuáles son los distritos escolares para investigar con fuentes oficiales de NJ para las familias?", "¿Dónde puedo consultar información oficial sobre los distritos escolares de NJ?"),
        (
            "Nueva Jersey tiene de forma constante algunos de los distritos escolares para investigar con fuentes oficiales públicos de Estados Unidos. Entre los distritos escolares locales de NJ están: Chatham (condado de Morris, 5 % superior a nivel estatal), Summit (condado de Union, 9/10 en NJDOE School Performance Reports), Mountain Lakes (condado de Morris), Westfield (condado de Union, Blue Ribbon), Millburn (condado de Essex, siempre en los primeros lugares), Madison (condado de Morris) y Mendham (condado de Morris). Las escuelas se financian principalmente con impuestos a la propiedad, por lo que los distritos mejor calificados también tienden a tener los precios de casa más altos.",
            "NJDOE publica informes oficiales de cada distrito y escuela pública de Nueva Jersey. Revise directamente los programas, límites de asistencia y datos vigentes de NJDOE para las propiedades concretas que esté comparando; no use una clasificación privada como sustituto de esa investigación.",
        ),
        (
            "Nueva Jersey tiene de forma constante algunos de los distritos escolares para investigar con fuentes oficiales públicos de Estados Unidos. Entre los distritos escolares y sus informes oficiales de NJ están: Chatham (condado de Morris, 5 % superior a nivel estatal), Summit (condado de Union, 9/10 en NJDOE School Performance Reports), Mountain Lakes (condado de Morris), Westfield (condado de Union, Blue Ribbon), Millburn/Short Hills (condado de Essex, siempre en los primeros lugares), Madison (condado de Morris) y Mendham (condado de Morris). Las escuelas en NJ se financian principalmente con impuestos a la propiedad, por lo que los distritos mejor calificados también tienden a tener los precios de casa más altos.",
            "NJDOE publica informes oficiales de cada distrito y escuela pública de Nueva Jersey. Revise directamente los programas, límites de asistencia y datos vigentes de NJDOE para las propiedades concretas que esté comparando; no use una clasificación privada como sustituto de esa investigación.",
        ),
        (
            "Los municipios para comparar de Nueva Jersey para quienes viajan a NYC en la línea Midtown Direct de NJ Transit incluyen Summit (38 min, mediana de $1.1M), Millburn/Short Hills (39 min, mediana de $1.3M), Chatham (49 min, mediana de $1M), Madison (53 min, mediana de $875K), South Orange (43 min, mediana de $650K), Maplewood (45 min, mediana de $675K) y Westfield (57 min por la Raritan Valley, mediana de $875K). Entre las opciones más accesibles están Cranford (59 min, $625K), Fanwood (65 min, $550K) y Scotch Plains (65 min, $600K). El pueblo adecuado depende de tu tolerancia al traslado, tu presupuesto, tus prioridades escolares y tus preferencias de estilo de vida.",
            "Entre los municipios con servicio ferroviario hacia NYC están Summit, Millburn, Chatham, Madison, South Orange, Maplewood, Westfield, Cranford, Fanwood y Scotch Plains. Verifique los horarios actuales directamente con NJ Transit y compare ventas recientes, impuestos por propiedad, tipos de vivienda e informes escolares oficiales.",
        ),
    ),
    "es/nj-real-estate-agent.html": (
        (
            "Jorge Ramirez, de The Jorge Ramirez Group en Keller Williams Premier Properties en Summit, NJ, es un agente de bienes raíces con licencia en Nueva Jersey de NJ. Con más de 8 años de experiencia a tiempo completo y amplia experiencia personal renovando propiedades de inversión, Jorge entrega resultados excepcionales.",
            "Jorge Ramirez, de The Jorge Ramirez Group en Keller Williams Premier Properties en Summit, es un agente de bienes raíces con licencia en Nueva Jersey que representa a compradores y vendedores.",
        ),
    ),
    "es/relocating-from-nj.html": (
        ("Los niños ya instalados en su nueva escuela.", "La mudanza al nuevo estado ya está en marcha."),
        ("instalando a los niños en una nueva escuela", "coordinando la instalación en tu nueva vivienda"),
    ),
    "es/short-hills-vs-westfield-nj.html": (
        ("familias que quieren un suburbio", "compradores que comparan un municipio"),
        ("familias que quieren el estilo de vida de un pueblo", "compradores que comparan vivienda y servicios municipales"),
        ("un sector pequeño, adinerado", "un sector pequeño con viviendas de precios más altos"),
        ("El sistema de Millburn Public Schools se ubica de forma habitual en el top 3 de NJ.", "Millburn Public Schools publica información vigente de programas y rendimiento a través de NJDOE."),
        ("escuelas premium", "información escolar oficial"),
        ("ejecutivos y profesionales de finanzas de NYC que necesitan el viaje al trabajo más corto + escuelas top 3 y están dispuestos a pagar la prima", "compradores que comparan horarios de NJ Transit, informes escolares oficiales y viviendas en el rango indicado"),
        ("Westfield es más grande, menos corporativo y más enfocado en la familia que Short Hills.", "Westfield abarca un área y un centro comercial de mayor escala que Short Hills."),
        ("Las escuelas son excelentes", "El distrito escolar publica informes vigentes en NJDOE"),
        ("municipio premium", "municipio de precios más altos"),
        (
            "Short Hills y Westfield son los dos pueblos de pasajeros de lujo más prominentes de NJ, pero atraen perfiles de comprador distintos. Short Hills es la opción más cara, más corporativa y más reconocida a nivel nacional. Westfield es la opción más grande, un poco más accesible y con más familias. Ambos están en el Midtown Direct, pero con tiempos de viaje al trabajo notablemente distintos.",
            "Short Hills y Westfield ofrecen distintas escalas de centro, tipos de vivienda, rangos de precio e itinerarios ferroviarios. Compare horarios actuales de NJ Transit, ventas recientes, impuestos y características específicas de cada propiedad.",
        ),
    ),
    "es/summit-nj-homes-for-sale.html": (
        (
            "Summit NJ es uno de los suburbios más codiciados de Nueva Jersey por muchas razones: escuelas públicas de las mejor calificadas (el distrito escolar de Summit se clasifica consistentemente entre los mejores de NJ), un cómodo trayecto de 45 minutos en NJ Transit hasta Penn Station en NYC, un centro vibrante con restaurantes y tiendas, bajos índices de criminalidad y una fuerte cultura comunitaria. Summit atrae de forma constante a compradores que buscan lo mejor de la vida suburbana con acceso a NYC.",
            "Summit es un municipio del Condado de Union con servicio de NJ Transit, comercios en el centro, servicios municipales y un distrito escolar público local. Verifique de forma independiente los horarios actuales, las ventas y condiciones específicas de cada propiedad, los impuestos y los informes oficiales del distrito.",
        ),
        (
            "Summit, Nueva Jersey se clasifica constantemente como uno de los mejores lugares para vivir del estado, y con razón. Ubicada en el Condado de Union, Summit combina lo mejor de la vida suburbana con un acceso inmejorable a la ciudad de Nueva York. Ya sea que te estés mudando a la zona, buscando una casa familiar más grande o invirtiendo en uno de los mercados de bienes raíces más estables de NJ, las casas en venta en Summit NJ representan un valor excepcional a largo plazo.",
            "Summit es un municipio del Condado de Union con distintos tipos de vivienda, un centro comercial y servicio de NJ Transit. Si estás comparando una compra o venta, revisa datos recientes de propiedades comparables, impuestos, estado físico, horarios de transporte y fuentes municipales oficiales.",
        ),
        ("familias en crecimiento que priorizan las escuelas", "compradores que comparan más espacio e información escolar oficial"),
        ("casa familiar", "casa unifamiliar"),
        ("mejores lugares", "municipios consultados con frecuencia"),
    ),
    "es/tools/commute-scorer.html": (
        ("Encuentra el mejor pueblo de NJ para pasajeros al trabajo según tu estilo de vida.", "Compara municipios de NJ según horarios de transporte, tiempo estimado y presupuesto."),
        ("Ayuda a compradores a encontrar el mejor pueblo para pasajeros al trabajo.", "Ayuda a compradores a comparar municipios con acceso a centros de empleo."),
        ("¿No estás decidido qué municipio para comparar de NJ es el mejor para tu viaje al trabajo?", "¿Necesitas comparar municipios de NJ según tu viaje al trabajo?"),
        ("ha ayudado a cientos de profesionales de NYC a encontrar el pueblo correcto para su viaje al trabajo, presupuesto y estilo de vida", "puede ayudarte a revisar horarios, vivienda, impuestos y presupuesto para cada propiedad"),
        ("Mejor pueblo", "Municipio para comparar"),
        ("mejor pueblo", "municipio para comparar"),
        ("premium ejecutivo", "viviendas de precios más altos"),
        ("mejor valor comprador primerizo", "precios y tipos de vivienda para comparar"),
        ("¿No estás decidido qué municipio para comparar de NJ es el mejor para tu viaje al trabajo?", "¿Necesitas comparar municipios de NJ según tu viaje al trabajo?"),
    ),
    "es/tools/market-comparison-widget.html": (
        ("¿qué te da más metros cuadrados, qué te da mejor tiempo de viaje, qué pueblo tiene centro urbano caminable, cuál tiene mejor apreciación histórica?", "¿qué propiedades ofrecen más espacio, cómo cambian los horarios de transporte, qué centros son peatonales y qué muestran las ventas cerradas recientes?"),
        ("Los municipios para comparar por perfil de comprador", "Criterios para comparar municipios"),
        ("Después de trabajar con cientos de compradores en NJ, veo que la mayoría cae en uno de estos cuatro perfiles. Sé honesto sobre cuál eres tú — te ahorra meses de recorrido de propiedades equivocadas:", "Use criterios verificables —precio, tipo de vivienda, impuestos, transporte y estado de la propiedad— para crear una lista corta y luego revisar ventas comparables recientes:"),
        ("Familias que valoran el viaje directo a Penn Station y comunidades culturalmente ricas.", "Compare el viaje directo a Penn Station, los tipos de vivienda y los precios de cada propiedad."),
        ("Ejecutivos jóvenes que quieren centro urbano caminable, tren directo, información escolar oficial y aceptan pagar el premio.", "Compare centros peatonales, servicio ferroviario, informes escolares oficiales y precios por propiedad."),
        ("Compradores primerizos y familias que necesitan un transbordo pero ganan mucho por dólar.", "Compare opciones con transbordo, tipos de vivienda y costos totales por propiedad."),
        ("¿qué te da más metros cuadrados, qué te da mejor tiempo de viaje, qué pueblo tiene centro urbano caminable, cuál tiene mejor apreciación histórica?", "¿qué propiedades ofrecen más espacio, cómo cambian los horarios de transporte, qué centros son peatonales y qué muestran las ventas cerradas recientes?"),
    ),
    "es/westfield-nj-homes-for-sale.html": (
        ("uno de los mercados más destacados del Condado de Union", "un mercado del Condado de Union que debe compararse con datos recientes"),
        ("Los vecindarios más codiciados de Westfield incluyen", "Las zonas de Westfield que los compradores suelen comparar incluyen"),
        ("el vecindario de Mindowaskin Park para familias", "la zona de Mindowaskin Park cerca del parque"),
        ("la mejor opción para tu estilo de vida y presupuesto", "opciones según vivienda, ubicación y presupuesto"),
        (
            "Las casas en venta en Westfield NJ están entre las más codiciadas de Nueva Jersey. Como un pintoresco pueblo del Condado de Union con escuelas públicas locales, un centro encantador y un excelente acceso de NJ Transit a la ciudad de Nueva York, Westfield atrae a compradores de todo el estado y de la propia NYC. Si estás buscando casas en venta en Westfield NJ, estás mirando una de las comunidades más destacadas del Garden State.",
            "Westfield es un municipio del Condado de Union con un distrito escolar público local, un centro comercial y servicio de NJ Transit. Si estás buscando una propiedad, compara ventas recientes, impuestos, estado físico, horarios de transporte e información municipal y escolar oficial.",
        ),
        ("residencia familiar de muchos años", "residencia de muchos años"),
        ("uno de los pueblos más codiciados de Nueva Jersey", "un municipio del Condado de Union que los compradores suelen comparar"),
        (
            "<strong>Zona de Mindowaskin Park:</strong> Hermosas vistas del parque, calles con distintos tipos de vivienda y muy caminable. De forma constante, entre los submercados más deseables (y más competitivos) de Westfield.",
            "<strong>Zona de Mindowaskin Park:</strong> Propiedades próximas al parque y a distintos servicios; confirme la distancia y el acceso desde cada dirección.",
        ),
        (
            "<strong>South Westfield:</strong> Lotes más grandes, calles más tranquilas, más privacidad. Ideal para compradores que quieren espacio sin sacrificar las comodidades y el distrito escolar de Westfield.",
            "<strong>South Westfield:</strong> Compare tamaño de lote, tipo de vivienda, impuestos, servicios y límites escolares vigentes por dirección.",
        ),
        (
            "<strong>North Westfield:</strong> Mezcla de casas clásicas y renovadas, cercanía a parques y escuelas. Fuerte demanda de familias que priorizan la ubicación dentro de la zona escolar.",
            "<strong>North Westfield:</strong> Mezcla de casas antiguas y renovadas cerca de parques y escuelas; verifique límites escolares y ventas recientes por dirección.",
        ),
        (
            "Las zonas populares incluyen el área del centro/estación de tren para quienes viajan a diario, Mindowaskin Park para familias, South Westfield para lotes más grandes y North Westfield para el acceso a la zona escolar. Jorge puede ayudarte a encontrar la mejor opción.",
            "Las zonas que suelen compararse incluyen el área del centro y la estación, Mindowaskin Park, South Westfield y North Westfield. Revise vivienda, lote, impuestos, transporte, servicios y límites escolares vigentes para cada propiedad.",
        ),
    ),
}


def normalize(source: str, relative: str) -> str:
    # Generator/source emitters are guarded with targeted edits and tests. The
    # broad Spanish copy table must never rewrite their English data/templates.
    if not relative.endswith(".html"):
        return source
    for old, new in FILE_REPLACEMENTS.get(relative, ()):
        source = source.replace(old, new)
    for old, new in LITERAL_REPLACEMENTS:
        source = source.replace(old, new)
    for pattern, replacement in REGEX_REPLACEMENTS:
        source = pattern.sub(replacement, source)
    return source


def targets() -> list[str]:
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    return sorted(set(payload["reviewed"]) | set(payload.get("emitters", [])))


def main() -> int:
    changed: list[str] = []
    changed_positions = 0
    for relative in targets():
        path = ROOT / relative
        source = path.read_text(encoding="utf-8", errors="replace")
        updated = normalize(source, relative)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
            changed.append(relative)
            changed_positions += sum(a != b for a, b in zip(source, updated)) + abs(len(source) - len(updated))
    print(f"normalized_files={len(changed)} changed_character_positions={changed_positions}")
    for relative in changed:
        print(relative)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
