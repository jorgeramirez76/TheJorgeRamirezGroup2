#!/usr/bin/env python3
"""Render the bilingual, source-backed commute comparison worksheet."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "commute-planner-sources.json"


COPY = {
    "en": {
        "lang": "en",
        "locale": "en_US",
        "path": "tools/commute-scorer.html",
        "url": "https://thejorgeramirezgroup.com/tools/commute-scorer",
        "other_url": "https://thejorgeramirezgroup.com/es/tools/commute-scorer",
        "other_label": "ES",
        "other_aria": "En Español",
        "title": "NJ Commute Comparison Calculator | Jorge Ramirez",
        "description": "Compare up to three New Jersey commute plans using your own door-to-door time and cost inputs, then verify live schedules and fares at the official transit source.",
        "llm": "A bilingual New Jersey commute comparison worksheet from licensed NJ real estate agent Jorge Ramirez. Results use only visitor-entered assumptions and are not a town ranking, travel guarantee, or live transit feed.",
        "skip": "Skip to main content",
        "nav": [
            ("Home", "/"), ("Buy", "/buy-a-home"), ("Sell", "/sell-your-home"),
            ("Communities", "/communities"), ("Research", "/blog")
        ],
        "menu": "Toggle navigation menu",
        "value": "Get Home Value",
        "crumb_home": "Home",
        "crumb_tools": "Tools",
        "crumb_current": "Commute comparison",
        "eyebrow": "NJ commute planning · visitor-entered comparison",
        "h1": "Compare the whole commute—not a town score",
        "intro": "Enter the same door-to-door components for up to three routes. The worksheet calculates your own time and cost assumptions; it does not rank communities or import live transit data.",
        "badges": ["No account required", "Nothing submitted", "Official-source links"],
        "hero_primary": "Build your comparison",
        "hero_secondary": "Open NJ TRANSIT trip planner",
        "tool_kicker": "Worksheet",
        "tool_h2": "Use one repeatable method for every route",
        "tool_intro": "Check each route for the actual origin, destination, date, and travel window. Then enter the same components below so the comparison stays consistent.",
        "days": "Commute days per week",
        "days_help": "Used only to calculate weekly round-trip time and cost.",
        "option": "Option",
        "label": "Route or property label",
        "label_placeholder": "Example: Property A to office",
        "first_leg": "Home to first stop",
        "wait_transfer": "Waiting and transfers",
        "scheduled_ride": "Scheduled transit or driving",
        "final_leg": "Final stop to destination",
        "buffer": "Personal buffer",
        "fare_tolls": "Daily round-trip fares or tolls",
        "parking_local": "Daily parking or local transit",
        "minutes": "minutes",
        "dollars": "US dollars",
        "calculate": "Compare my entries",
        "reset": "Clear worksheet",
        "privacy": "Your entries stay in this browser page and are not sent to Jorge or stored by this site.",
        "results_kicker": "Your entries",
        "results_h2": "Side-by-side calculation",
        "results_note": "These totals are arithmetic based on what you entered—not predicted travel times, future costs, or a recommendation.",
        "columns": ["Option", "One-way total", "Weekly round-trip time", "Weekly cost"],
        "empty": "Enter at least one time or cost for an option to compare it.",
        "print": "Print or save results",
        "method_kicker": "Before deciding",
        "method_h2": "Four checks the worksheet cannot do for you",
        "methods": [
            ("Check a dated itinerary", "Use the actual origin, destination, day, and departure window. Weekday, weekend, and special-service patterns may differ."),
            ("Count every leg", "Include the trip to the first stop, waiting, transfers, the scheduled ride, the final leg, and a buffer that reflects your needs."),
            ("Verify current costs", "Check current fares, tolls, parking terms, and connecting-service costs. Enter daily round-trip amounts on the same basis for every option."),
            ("Test the trip", "When practical, make the route during the travel window that matters to you and note what the published itinerary did not capture.")
        ],
        "fair_title": "Keep the comparison personal and property-specific",
        "fair_text": "Use your own work location, schedule, mobility needs, budget, and property criteria. The calculation uses only the trip components you enter; it does not assess people, schools, reported crime, or neighborhood character.",
        "sources_kicker": "Research",
        "sources_h2": "Official source notebook",
        "sources_intro": "Open the operating agency's current information before entering a figure. Each source has a specific job and a limit.",
        "use": "Use",
        "limit": "Limit",
        "reviewed": "Source links reviewed August 26, 2026. Recheck live information near the date of travel.",
        "cta_kicker": "Property-specific help",
        "cta_h2": "Compare the real-estate facts after you compare the routes",
        "cta_text": "Jorge can help organize property details, current comparable sales, taxes, and your timing priorities for the homes you are considering. Transit schedules and travel conditions must be verified with the operating agency.",
        "cta_primary": "Ask Jorge about a property",
        "cta_secondary": "Call 908-230-7844",
        "footer_about": "Full-time Realtor with Keller Williams Premier Properties since 2017.",
        "footer_research": "Research",
        "footer_services": "Services",
        "footer_contact": "Contact",
        "footer_links": [("Communities", "/communities"), ("Research", "/blog"), ("NJ TRANSIT", "/nj-train-map")],
        "service_links": [("Buy", "/buy-a-home"), ("Sell", "/sell-your-home"), ("Get Home Value", "/home-valuation")],
        "privacy_policy": "Privacy Policy",
    },
    "es": {
        "lang": "es",
        "locale": "es_US",
        "path": "es/tools/commute-scorer.html",
        "url": "https://thejorgeramirezgroup.com/es/tools/commute-scorer",
        "other_url": "https://thejorgeramirezgroup.com/tools/commute-scorer",
        "other_label": "EN",
        "other_aria": "In English",
        "title": "Calculadora para Comparar Traslados en NJ | Jorge Ramirez",
        "description": "Compare hasta tres planes de traslado en Nueva Jersey con sus propios tiempos y costos, y luego verifique horarios y tarifas en la fuente oficial.",
        "llm": "Hoja bilingüe para comparar traslados en Nueva Jersey de Jorge Ramirez, agente inmobiliario con licencia de NJ. Los resultados usan solo datos ingresados por el visitante; no son una clasificación de municipios, garantía de viaje ni fuente de tránsito en vivo.",
        "skip": "Saltar al contenido principal",
        "nav": [
            ("Inicio", "/es/"), ("Comprar", "/es/buy-a-home"), ("Vender", "/es/sell-your-home"),
            ("Comunidades", "/es/communities"), ("Investigación", "/es/blog")
        ],
        "menu": "Abrir o cerrar el menú de navegación",
        "value": "Valor de su casa",
        "crumb_home": "Inicio",
        "crumb_tools": "Herramientas",
        "crumb_current": "Comparación de traslados",
        "eyebrow": "Planificación de traslados en NJ · comparación con sus datos",
        "h1": "Compare el viaje completo, no un puntaje de municipio",
        "intro": "Ingrese los mismos componentes de puerta a puerta para hasta tres rutas. La hoja calcula sus propios tiempos y costos; no clasifica comunidades ni importa datos de tránsito en vivo.",
        "badges": ["Sin cuenta", "No se envían datos", "Enlaces a fuentes oficiales"],
        "hero_primary": "Crear mi comparación",
        "hero_secondary": "Abrir NJ TRANSIT",
        "tool_kicker": "Hoja de trabajo",
        "tool_h2": "Use el mismo método para cada ruta",
        "tool_intro": "Consulte cada ruta para el origen, destino, fecha y horario reales. Luego ingrese los mismos componentes para que la comparación sea consistente.",
        "days": "Días de traslado por semana",
        "days_help": "Se usa solamente para calcular el tiempo y el costo semanal de ida y vuelta.",
        "option": "Opción",
        "label": "Nombre de la ruta o propiedad",
        "label_placeholder": "Ejemplo: Propiedad A a la oficina",
        "first_leg": "Casa a la primera parada",
        "wait_transfer": "Espera y transbordos",
        "scheduled_ride": "Tránsito o conducción programada",
        "final_leg": "Última parada al destino",
        "buffer": "Margen personal",
        "fare_tolls": "Tarifas o peajes diarios de ida y vuelta",
        "parking_local": "Estacionamiento o tránsito local diario",
        "minutes": "minutos",
        "dollars": "dólares estadounidenses",
        "calculate": "Comparar mis datos",
        "reset": "Borrar la hoja",
        "privacy": "Sus datos permanecen en esta página del navegador y este sitio no los envía a Jorge ni los guarda.",
        "results_kicker": "Sus datos",
        "results_h2": "Cálculo lado a lado",
        "results_note": "Estos totales son operaciones aritméticas basadas en lo que ingresó; no predicen tiempos, costos futuros ni recomiendan una opción.",
        "columns": ["Opción", "Total de ida", "Tiempo semanal ida y vuelta", "Costo semanal"],
        "empty": "Ingrese al menos un tiempo o costo para una opción antes de compararla.",
        "print": "Imprimir o guardar resultados",
        "method_kicker": "Antes de decidir",
        "method_h2": "Cuatro verificaciones que la hoja no puede hacer",
        "methods": [
            ("Consulte un itinerario fechado", "Use el origen, destino, día y horario de salida reales. Los patrones de días laborables, fines de semana y servicios especiales pueden variar."),
            ("Cuente cada tramo", "Incluya el viaje a la primera parada, la espera, los transbordos, el recorrido programado, el tramo final y un margen acorde con sus necesidades."),
            ("Verifique los costos vigentes", "Consulte tarifas, peajes, condiciones de estacionamiento y costos de conexiones. Ingrese montos diarios de ida y vuelta con la misma base para cada opción."),
            ("Pruebe el viaje", "Cuando sea práctico, haga la ruta durante el horario que le importa y anote lo que el itinerario publicado no captó.")
        ],
        "fair_title": "Mantenga la comparación personal y específica a la propiedad",
        "fair_text": "Use su lugar de trabajo, horario, necesidades de movilidad, presupuesto y criterios de vivienda. El cálculo usa solamente los componentes de viaje que usted ingresa; no evalúa personas, escuelas, criminalidad reportada ni el carácter de una zona.",
        "sources_kicker": "Investigación",
        "sources_h2": "Cuaderno de fuentes oficiales",
        "sources_intro": "Abra la información vigente de la agencia operadora antes de ingresar una cifra. Cada fuente tiene una función y un límite.",
        "use": "Uso",
        "limit": "Límite",
        "reviewed": "Enlaces revisados el 26 de agosto de 2026. Vuelva a consultar la información vigente cerca de la fecha del viaje.",
        "cta_kicker": "Ayuda específica a la propiedad",
        "cta_h2": "Compare los datos inmobiliarios después de comparar las rutas",
        "cta_text": "Jorge puede ayudarle a organizar detalles de la propiedad, ventas comparables vigentes, impuestos y sus prioridades de tiempo para las viviendas que considera. Confirme horarios y condiciones de viaje con la agencia operadora.",
        "cta_primary": "Preguntar a Jorge por una propiedad",
        "cta_secondary": "Llamar al 908-230-7844",
        "footer_about": "Realtor de tiempo completo con Keller Williams Premier Properties desde 2017.",
        "footer_research": "Investigación",
        "footer_services": "Servicios",
        "footer_contact": "Contacto",
        "footer_links": [("Comunidades", "/es/communities"), ("Investigación", "/es/blog"), ("NJ TRANSIT", "/es/nj-train-map")],
        "service_links": [("Comprar", "/es/buy-a-home"), ("Vender", "/es/sell-your-home"), ("Valor de su casa", "/es/home-valuation")],
        "privacy_policy": "Política de privacidad",
    },
}


STYLE = """
    :root{--charcoal:#1A1A1A;--red:#C41230;--deep-red:#8B0D22;--gold:#B8962E;--ivory:#FAFAF8;--paper:#FFFFFF;--ink:#2C2C2C;--muted:#69645C;--line:#E7E0D4;--display:'Playfair Display',Georgia,serif;--body:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body.commute-page{margin:0;background:var(--ivory);color:var(--ink);font-family:var(--body);line-height:1.65}.skip-link{position:fixed;left:1rem;top:-5rem;z-index:3000;background:#fff;color:var(--charcoal);padding:.75rem 1rem;border:2px solid var(--gold)}.skip-link:focus{top:1rem}
    .site-nav{position:fixed;inset:0 0 auto;z-index:1000;background:rgba(10,10,10,.97);border-bottom:1px solid rgba(184,150,46,.25);box-shadow:0 10px 30px rgba(0,0,0,.18)}.nav-inner{width:min(1400px,94vw);min-height:86px;margin:auto;display:flex;align-items:center;gap:1.35rem}.logo{display:flex;align-items:center;margin-right:auto}.logo img{display:block;width:205px;max-height:58px;height:auto;object-fit:contain;background:#fff;padding:6px 10px;border-radius:4px}.nav-links{display:flex;align-items:center;gap:1.15rem;list-style:none;margin:0;padding:0}.nav-links a{color:#fff;text-decoration:none;font-weight:600;font-size:.91rem;white-space:nowrap}.nav-links a:hover,.nav-links a:focus-visible{color:#D4AF5A}.language{display:inline-flex;min-width:36px;justify-content:center;padding:.42rem .58rem;border:1px solid rgba(255,255,255,.55);border-radius:999px}.nav-value{padding:.68rem 1rem;border-radius:999px;background:linear-gradient(135deg,var(--red),var(--deep-red));box-shadow:0 7px 20px rgba(196,18,48,.28)}.menu{display:none;width:44px;height:44px;border:1px solid rgba(255,255,255,.3);border-radius:8px;background:transparent;color:#fff;font-size:1.35rem}
    .wrap{position:relative;z-index:1;width:min(1160px,90vw);margin:0 auto}.hero{position:relative;overflow:hidden;padding:164px 5vw 88px;background:linear-gradient(120deg,rgba(0,0,0,.96),rgba(26,26,26,.93) 60%,rgba(139,13,34,.82));color:#fff}.hero::after{content:'';position:absolute;right:-12vw;bottom:-24vw;width:52vw;height:52vw;border:1px solid rgba(184,150,46,.25);border-radius:50%;box-shadow:0 0 0 7vw rgba(184,150,46,.035),0 0 0 14vw rgba(184,150,46,.025)}.breadcrumbs{display:flex;flex-wrap:wrap;gap:.45rem;color:rgba(255,255,255,.66);font-size:.82rem;margin-bottom:2.3rem}.breadcrumbs a{color:#D4AF5A;text-decoration:none}.eyebrow{margin:0 0 1rem;color:#D4AF5A;font-size:.76rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}.hero h1{max-width:940px;margin:0;font-family:var(--display);font-size:clamp(2.65rem,6.1vw,5.55rem);font-weight:600;line-height:.99;letter-spacing:-.025em;color:#fff}.hero-intro{max-width:810px;margin:1.5rem 0 0;font-size:clamp(1.05rem,1.6vw,1.28rem);color:rgba(255,255,255,.82)}.badges,.hero-actions,.form-actions,.cta-actions{display:flex;flex-wrap:wrap;gap:.75rem}.badges{margin-top:1.7rem}.badges span{padding:.55rem .8rem;border:1px solid rgba(212,175,90,.42);border-radius:999px;background:rgba(0,0,0,.25);font-size:.72rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.hero-actions{margin-top:2rem}.button{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:.8rem 1.2rem;border:0;border-radius:999px;text-decoration:none;font:700 .95rem/1 var(--body);cursor:pointer;transition:transform .2s ease,box-shadow .2s ease}.button:hover{transform:translateY(-2px)}.button-primary{background:linear-gradient(135deg,var(--red),var(--deep-red));color:#fff;box-shadow:0 10px 24px rgba(196,18,48,.28)}.button-outline{border:1px solid rgba(255,255,255,.5);background:transparent;color:#fff}.button-light{background:#fff;color:var(--deep-red)}.button-quiet{background:#eee8de;color:var(--charcoal)}
    .section{padding:82px 0}.section-paper{background:#fff}.section-dark{background:var(--charcoal);color:#fff}.heading{max-width:850px;margin-bottom:2.25rem}.heading span{display:block;margin-bottom:.65rem;color:var(--red);font-size:.75rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.section-dark .heading span{color:#D4AF5A}.heading h2{margin:0 0 .85rem;font-family:var(--display);font-size:clamp(2rem,4vw,3.35rem);line-height:1.1;color:inherit}.heading p{margin:0;color:var(--muted);font-size:1.04rem}.section-dark .heading p{color:rgba(255,255,255,.7)}
    .commute-form{display:grid;gap:1.2rem}.days-card{max-width:440px;padding:1.25rem 1.35rem;background:#fff;border:1px solid var(--line);border-radius:12px}.days-card label,.field label{display:block;margin-bottom:.4rem;color:var(--charcoal);font-size:.84rem;font-weight:800}.field-help,.privacy-note{margin:.45rem 0 0;color:var(--muted);font-size:.82rem}.days-card input,.field input{width:100%;min-height:48px;padding:.7rem .8rem;border:1px solid #CFC6B8;border-radius:8px;background:#fff;color:var(--charcoal);font:inherit}.days-card input{max-width:130px}.days-card input:focus,.field input:focus{outline:3px solid rgba(184,150,46,.24);border-color:var(--gold)}.options-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.option-card{padding:1.35rem;background:#fff;border:1px solid var(--line);border-top:4px solid var(--red);border-radius:12px;box-shadow:0 12px 34px rgba(0,0,0,.05)}.option-card:nth-child(2){border-top-color:var(--gold)}.option-card:nth-child(3){border-top-color:var(--deep-red)}.option-card h3{margin:0 0 1.2rem;font:600 1.55rem/1.1 var(--display);color:var(--charcoal)}.fields{display:grid;gap:.9rem}.field-unit{position:relative}.field-unit input{padding-right:4.5rem}.field-unit span{position:absolute;right:.8rem;bottom:.76rem;color:var(--muted);font-size:.76rem}.form-actions{align-items:center;margin-top:.35rem}.privacy-note{max-width:720px}
    .results{margin-top:2.3rem;padding:1.5rem;background:var(--charcoal);color:#fff;border-radius:12px;outline:none}.results[hidden]{display:none}.results h2{margin:.2rem 0 .5rem;font:600 clamp(1.7rem,3vw,2.5rem)/1.1 var(--display)}.results p{color:rgba(255,255,255,.7)}.table-wrap{overflow-x:auto;margin:1.25rem 0}.results table{width:100%;min-width:680px;border-collapse:collapse}.results th,.results td{padding:.85rem;text-align:left;border-bottom:1px solid rgba(255,255,255,.14)}.results th{color:#D4AF5A;font-size:.75rem;letter-spacing:.06em;text-transform:uppercase}.results td:first-child{font-weight:800}.empty-result{padding:1rem;background:rgba(255,255,255,.06);border-radius:8px}
    .method-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem}.method-card,.fair-card{padding:1.6rem;background:#fff;border:1px solid var(--line);border-radius:12px}.method-card span{display:block;color:var(--gold);font-size:.74rem;font-weight:800;letter-spacing:.12em}.method-card h3,.fair-card h3,.source-card h3{margin:.65rem 0 .6rem;font:600 1.35rem/1.2 var(--display);color:var(--charcoal)}.method-card p,.fair-card p,.source-card p{margin:0;color:var(--muted)}.fair-card{margin-top:1rem;border-left:5px solid var(--gold)}
    .source-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem}.source-card{padding:1.45rem;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.12);border-radius:10px}.source-card h3,.source-card h3 a{color:#fff}.source-card p{color:rgba(255,255,255,.68);font-size:.92rem}.source-card p+p{margin-top:.65rem}.publisher{margin-bottom:.65rem!important;color:#D4AF5A!important;font-size:.7rem!important;font-weight:800;letter-spacing:.11em;text-transform:uppercase}.source-review{margin:1.25rem 0 0;color:rgba(255,255,255,.62);font-size:.86rem}
    .cta{padding:78px 0;background:linear-gradient(135deg,var(--deep-red),var(--red));color:#fff}.cta-inner{display:grid;grid-template-columns:1fr auto;align-items:center;gap:2rem}.cta h2{margin:.3rem 0 .75rem;font:600 clamp(2rem,4vw,3.3rem)/1.07 var(--display);color:#fff}.cta p{max-width:760px;margin:0;color:rgba(255,255,255,.82)}.cta .eyebrow{color:#fff;opacity:.75}.footer{background:#090909;color:rgba(255,255,255,.72);padding:60px 0 28px}.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:2rem}.footer-brand img{width:230px;height:auto;background:#fff;padding:10px;border-radius:4px}.footer-brand p{max-width:370px}.footer h2{margin:0 0 1rem;color:#fff;font:600 1.2rem/1.2 var(--display)}.footer a{display:block;margin:.45rem 0;color:rgba(255,255,255,.72);text-decoration:none}.footer a:hover{color:#D4AF5A}.footer-bottom{margin-top:2.5rem;padding-top:1.25rem;border-top:1px solid rgba(255,255,255,.12);font-size:.82rem}
    @media(max-width:1100px){.nav-links{gap:.75rem}.nav-links a{font-size:.82rem}.options-grid{grid-template-columns:1fr 1fr}.options-grid .option-card:last-child{grid-column:1/-1}.footer-grid{grid-template-columns:2fr 1fr 1fr}}@media(max-width:820px){.nav-inner{min-height:76px}.logo img{width:176px}.menu{display:inline-grid;place-items:center}.nav-links{display:none;position:absolute;top:76px;left:0;right:0;flex-direction:column;align-items:stretch;padding:1.25rem 5vw 1.5rem;background:var(--charcoal);border-top:1px solid rgba(184,150,46,.25)}.nav-links.is-open{display:flex}.nav-links a{display:flex;min-height:44px;align-items:center;font-size:.94rem}.language,.nav-value{justify-content:center}.hero{padding-top:130px}.options-grid,.method-grid,.cta-inner{grid-template-columns:1fr}.options-grid .option-card:last-child{grid-column:auto}.source-grid{grid-template-columns:1fr}.footer-grid{grid-template-columns:1fr 1fr}}@media(max-width:540px){.wrap{width:min(92vw,1160px)}.hero{padding:118px 4vw 68px}.section{padding:62px 0}.footer-grid{grid-template-columns:1fr}.hero-actions .button,.form-actions .button,.cta-actions .button{width:100%}}@media print{.site-nav,.hero-actions,.form-actions,.section-dark,.cta,.footer,.privacy-note{display:none!important}.site-nav{position:static}.hero{padding:24px;background:#fff;color:#000}.hero h1,.hero-intro{color:#000}.section{padding:24px 0}.option-card{box-shadow:none}.results{background:#fff;color:#000;border:1px solid #bbb}.results p,.results td{color:#000}.results th{color:#7a1020}.results th,.results td{border-color:#ccc}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{transition:none!important}}
"""


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def render(language: str, source_data: dict) -> str:
    c = COPY[language]
    is_es = language == "es"
    nav = "".join(f'<li><a href="{href}">{esc(label)}</a></li>' for label, href in c["nav"])
    badges = "".join(f"<span>{esc(label)}</span>" for label in c["badges"])
    cards = []
    for index in range(1, 4):
        fields = []
        field_specs = [
            ("first_leg", c["first_leg"], c["minutes"], "180", "1"),
            ("wait_transfer", c["wait_transfer"], c["minutes"], "180", "1"),
            ("scheduled_ride", c["scheduled_ride"], c["minutes"], "360", "1"),
            ("final_leg", c["final_leg"], c["minutes"], "180", "1"),
            ("buffer", c["buffer"], c["minutes"], "180", "1"),
            ("fare_tolls", c["fare_tolls"], c["dollars"], "500", "0.01"),
            ("parking_local", c["parking_local"], c["dollars"], "500", "0.01"),
        ]
        for name, label, unit, maximum, step in field_specs:
            field_id = f"option-{index}-{name}"
            fields.append(
                f'<div class="field field-unit"><label for="{field_id}">{esc(label)}</label>'
                f'<input id="{field_id}" name="option_{index}_{name}" type="number" min="0" max="{maximum}" step="{step}" inputmode="decimal" data-field="{name}">'
                f'<span aria-hidden="true">{esc(unit)}</span></div>'
            )
        cards.append(
            f'<fieldset class="option-card" data-commute-option><legend class="sr-only">{esc(c["option"])} {index}</legend>'
            f'<h3 aria-hidden="true">{esc(c["option"])} {index}</h3>'
            f'<div class="field"><label for="option-{index}-label">{esc(c["label"])}</label>'
            f'<input id="option-{index}-label" name="option_{index}_label" type="text" maxlength="80" placeholder="{esc(c["label_placeholder"])}" data-option-label></div>'
            f'<div class="fields">{"".join(fields)}</div></fieldset>'
        )

    method_cards = "".join(
        f'<article class="method-card"><span>0{index}</span><h3>{esc(title)}</h3><p>{esc(text)}</p></article>'
        for index, (title, text) in enumerate(c["methods"], 1)
    )
    source_cards = []
    for source in source_data["sources"]:
        source_cards.append(
            '<article class="source-card">'
            f'<p class="publisher">{esc(source[f"publisher_{language}"])}</p>'
            f'<h3><a href="{esc(source["url"])}" rel="noopener">{esc(source[f"title_{language}"])}</a></h3>'
            f'<p><strong>{esc(c["use"])}:</strong> {esc(source[f"use_{language}"])}</p>'
            f'<p><strong>{esc(c["limit"])}:</strong> {esc(source[f"limit_{language}"])}</p>'
            '</article>'
        )
    footer_links = "".join(f'<a href="{href}">{esc(label)}</a>' for label, href in c["footer_links"])
    service_links = "".join(f'<a href="{href}">{esc(label)}</a>' for label, href in c["service_links"])
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage", "@id": f'{c["url"]}#webpage', "url": c["url"],
                "name": c["title"], "description": c["description"],
                "inLanguage": "es-US" if is_es else "en-US", "dateModified": source_data["reviewed"],
                "author": {"@id": "https://thejorgeramirezgroup.com/#jorge-ramirez"},
                "isPartOf": {"@id": "https://thejorgeramirezgroup.com/#website"}
            },
            {
                "@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": c["crumb_home"], "item": "https://thejorgeramirezgroup.com/es/" if is_es else "https://thejorgeramirezgroup.com/"},
                    {"@type": "ListItem", "position": 2, "name": c["crumb_current"], "item": c["url"]}
                ]
            }
        ]
    }
    canonical_en = "https://thejorgeramirezgroup.com/tools/commute-scorer"
    canonical_es = "https://thejorgeramirezgroup.com/es/tools/commute-scorer"
    result_headers = "".join(f"<th scope=\"col\">{esc(header)}</th>" for header in c["columns"])
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    return f'''<!DOCTYPE html>
<html lang="{c["lang"]}">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="theme-color" content="#1A1A1A">
  <title>{esc(c["title"])}</title><meta name="description" content="{esc(c["description"])}"><meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"><meta name="author" content="Jorge Ramirez"><meta name="llm-context" content="{esc(c["llm"])}">
  <link rel="canonical" href="{c["url"]}"><link rel="alternate" hreflang="en-US" href="{canonical_en}"><link rel="alternate" hreflang="es-US" href="{canonical_es}"><link rel="alternate" hreflang="es" href="{canonical_es}"><link rel="alternate" hreflang="x-default" href="{canonical_en}">
  <meta property="og:type" content="website"><meta property="og:url" content="{c["url"]}"><meta property="og:title" content="{esc(c["title"])}"><meta property="og:description" content="{esc(c["description"])}"><meta property="og:image" content="https://thejorgeramirezgroup.com/images/hero.jpg"><meta property="og:locale" content="{c["locale"]}">
  <meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(c["title"])}"><meta name="twitter:description" content="{esc(c["description"])}"><meta name="twitter:image" content="https://thejorgeramirezgroup.com/images/hero.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="/css/styles.css">
  <style>.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}{STYLE}</style>
  <script type="application/ld+json">{schema_json}</script>
</head>
<body class="commute-page" data-source-review="{source_data["reviewed"]}">
  <a class="skip-link" href="#main">{esc(c["skip"])}</a>
  <nav class="site-nav" aria-label="Primary navigation"><div class="nav-inner"><a class="logo" href="{'/es/' if is_es else '/'}" aria-label="The Jorge Ramirez Group"><picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="250" height="100"></picture></a><button class="menu" type="button" aria-label="{esc(c["menu"])}" aria-expanded="false" aria-controls="primary-navigation">☰</button><ul class="nav-links" id="primary-navigation">{nav}<li><a class="language" href="{c["other_url"].replace('https://thejorgeramirezgroup.com', '')}" hreflang="{'en-US' if is_es else 'es-US'}" aria-label="{esc(c["other_aria"])}">{c["other_label"]}</a></li><li><a href="tel:+19082307844">908-230-7844</a></li><li><a class="nav-value" href="{'/es/home-valuation' if is_es else '/home-valuation'}">{esc(c["value"])}</a></li></ul></div></nav>
  <main id="main" tabindex="-1">
    <header class="hero"><div class="wrap"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="{'/es/' if is_es else '/'}">{esc(c["crumb_home"])}</a><span aria-hidden="true">/</span><span>{esc(c["crumb_tools"])}</span><span aria-hidden="true">/</span><span>{esc(c["crumb_current"])}</span></nav><p class="eyebrow">{esc(c["eyebrow"])}</p><h1>{esc(c["h1"])}</h1><p class="hero-intro">{esc(c["intro"])}</p><div class="badges">{badges}</div><div class="hero-actions"><a class="button button-primary" href="#worksheet">{esc(c["hero_primary"])}</a><a class="button button-outline" href="https://www.njtransit.com/trip-planner-service-near-to" rel="noopener">{esc(c["hero_secondary"])}</a></div></div></header>
    <section class="section" id="worksheet" aria-labelledby="worksheet-title"><div class="wrap"><div class="heading"><span>{esc(c["tool_kicker"])}</span><h2 id="worksheet-title">{esc(c["tool_h2"])}</h2><p>{esc(c["tool_intro"])}</p></div><form class="commute-form" data-commute-form><div class="days-card"><label for="days-per-week">{esc(c["days"])}</label><input id="days-per-week" name="days_per_week" type="number" min="0" max="7" step="1" value="5" inputmode="numeric"><p class="field-help">{esc(c["days_help"])}</p></div><div class="options-grid">{"".join(cards)}</div><div class="form-actions"><button class="button button-primary" type="submit">{esc(c["calculate"])}</button><button class="button button-quiet" type="reset">{esc(c["reset"])}</button></div><p class="privacy-note">{esc(c["privacy"])}</p></form><section class="results" data-results-panel tabindex="-1" hidden aria-live="polite"><p class="eyebrow">{esc(c["results_kicker"])}</p><h2>{esc(c["results_h2"])}</h2><p>{esc(c["results_note"])}</p><p class="empty-result" data-empty-result>{esc(c["empty"])}</p><div class="table-wrap"><table><thead><tr>{result_headers}</tr></thead><tbody data-commute-results></tbody></table></div><button class="button button-light" type="button" data-print-results>{esc(c["print"])}</button></section></div></section>
    <section class="section section-paper" aria-labelledby="method-title"><div class="wrap"><div class="heading"><span>{esc(c["method_kicker"])}</span><h2 id="method-title">{esc(c["method_h2"])}</h2></div><div class="method-grid">{method_cards}</div><aside class="fair-card"><h3>{esc(c["fair_title"])}</h3><p>{esc(c["fair_text"])}</p></aside></div></section>
    <section class="section section-dark" aria-labelledby="sources-title"><div class="wrap"><div class="heading"><span>{esc(c["sources_kicker"])}</span><h2 id="sources-title">{esc(c["sources_h2"])}</h2><p>{esc(c["sources_intro"])}</p></div><div class="source-grid">{"".join(source_cards)}</div><p class="source-review">{esc(c["reviewed"])}</p></div></section>
    <section class="cta"><div class="wrap cta-inner"><div><p class="eyebrow">{esc(c["cta_kicker"])}</p><h2>{esc(c["cta_h2"])}</h2><p>{esc(c["cta_text"])}</p></div><div class="cta-actions"><a class="button button-light" href="mailto:jorge.ramirez@kw.com">{esc(c["cta_primary"])}</a><a class="button button-outline" href="tel:+19082307844">{esc(c["cta_secondary"])}</a></div></div></section>
  </main>
  <footer class="footer"><div class="wrap"><div class="footer-grid"><section class="footer-brand"><picture><source srcset="/images/jorge-logo.webp" type="image/webp"><img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="250" height="100" loading="lazy"></picture><p>{esc(c["footer_about"])}</p><p>488 Springfield Avenue<br>Summit, NJ 07901<br>NJ License #1754604</p></section><section><h2>{esc(c["footer_research"])}</h2>{footer_links}</section><section><h2>{esc(c["footer_services"])}</h2>{service_links}</section><section><h2>{esc(c["footer_contact"])}</h2><a href="tel:+19082307844">908-230-7844</a><a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a><a href="{'/es/privacy-policy' if is_es else '/privacy-policy'}">{esc(c["privacy_policy"])}</a></section></div><div class="footer-bottom">© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties · All rights reserved.</div></div></footer>
  <script>(()=>{{const b=document.querySelector('.menu'),m=document.getElementById('primary-navigation');if(!b||!m)return;b.addEventListener('click',()=>{{const o=m.classList.toggle('is-open');b.setAttribute('aria-expanded',String(o))}});m.addEventListener('click',e=>{{if(e.target.closest('a')){{m.classList.remove('is-open');b.setAttribute('aria-expanded','false')}}}})}})();</script><script defer src="/js/commute-comparison.js"></script><script defer src="/js/site-cta.js"></script><script defer src="/js/lead-attribution.js"></script>
</body></html>
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if rendered files differ")
    args = parser.parse_args()
    source_data = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    mismatches = []
    for language in ("en", "es"):
        target = ROOT / COPY[language]["path"]
        rendered = render(language, source_data)
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != rendered:
                mismatches.append(str(target.relative_to(ROOT)))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered, encoding="utf-8")
    if mismatches:
        print("Out-of-date rendered files:", ", ".join(mismatches))
        return 1
    print("Commute comparison pages are current." if args.check else "Rendered bilingual commute comparison pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
