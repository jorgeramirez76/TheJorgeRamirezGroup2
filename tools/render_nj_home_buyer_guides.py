#!/usr/bin/env python3
"""Render the bilingual, source-backed legacy NJ home-buyer guides."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "nj-home-buyer-guide-sources.json"
OUTPUTS = {
    "nj-home-buyer-guide.html": "en",
    "es/nj-home-buyer-guide.html": "es",
}

CONSENT = (
    "I agree that Jorge Ramirez, licensed NJ real estate agent (The Jorge Ramirez "
    "Group at Keller Williams Premier Properties), may call and text me, including "
    "by automated technology, about my real estate request and to send related "
    "updates such as appointment and showing reminders, new-listing and price "
    "alerts, home-value follow-ups, and transaction updates. Consent is not a "
    "condition of getting the guide or of any purchase. Message frequency varies, "
    "typically a few per month. Message and data rates may apply. Reply STOP to opt "
    "out, HELP for help."
)

COUNTIES = [
    "Union County, New Jersey",
    "Essex County, New Jersey",
    "Morris County, New Jersey",
    "Hudson County, New Jersey",
    "Middlesex County, New Jersey",
    "Somerset County, New Jersey",
]

SOURCE_TRANSLATIONS = {
    "es": {
        "njdobi-real-estate-topics": (
            "NJDOBI identifica las relaciones de corretaje de Nueva Jersey, la Comisión "
            "de Bienes Raíces, los recursos de licencias y sus guías oficiales para consumidores."
        ),
        "njdobi-buying-guide": (
            "NJDOBI indica que muchos compradores eligen representación legal, pero no es "
            "obligatoria, y explica los contratos preparados por licenciatarios, la revisión "
            "por abogado, la inspección independiente, el título y la preparación del cierre."
        ),
        "njdobi-brokerage-bulletin": (
            "NJDOBI explica los acuerdos escritos de servicios de corretaje, sus términos "
            "obligatorios, las relaciones de agencia y que la compensación del corredor es "
            "negociable y no está fijada por ley."
        ),
        "njhmfa-roadmap": (
            "NJHMFA publica una ruta para comprar vivienda, el acceso a prestamistas "
            "participantes, recursos educativos, programas y asesoría de vivienda."
        ),
        "njhmfa-programs": (
            "NJHMFA publica descripciones vigentes de hipotecas y asistencia, recursos de "
            "elegibilidad, hojas informativas y el acceso a prestamistas participantes."
        ),
        "njhmfa-faq": (
            "NJHMFA aclara que sus preguntas frecuentes son información general, no los "
            "requisitos finales, y remite a los materiales vigentes y a prestamistas participantes."
        ),
        "cfpb-toolkit": (
            "El kit de la CFPB organiza la comparación de hipotecas, la revisión de costos "
            "de cierre y la preparación para ser propietario."
        ),
        "cfpb-loan-estimate": (
            "La CFPB explica cómo revisar y comparar el Loan Estimate, incluidos términos, "
            "pago proyectado, costos, créditos y efectivo estimado para el cierre."
        ),
        "cfpb-closing-disclosure": (
            "La CFPB explica cómo comparar el Closing Disclosure con el Loan Estimate más "
            "reciente y resolver términos o cargos inesperados antes del cierre."
        ),
        "cfpb-closing-roadmap": (
            "La CFPB publica una ruta de cierre que abarca los documentos finales, la "
            "preparación del efectivo, el recorrido final, la firma y los registros posteriores."
        ),
        "cfpb-model-forms": (
            "La CFPB publica modelos y ejemplos en inglés y español del Loan Estimate y "
            "del Closing Disclosure."
        ),
        "hud-fair-housing": (
            "HUD explica que la Ley de Vivienda Justa se aplica al comprar una vivienda, "
            "solicitar una hipoteca y participar en otras actividades de vivienda."
        ),
        "hud-housing-counseling": (
            "HUD mantiene la búsqueda y la línea telefónica para localizar agencias "
            "participantes de asesoría de vivienda."
        ),
    }
}


CONTENT = {
    "en": {
        "lang": "en-US",
        "canonical": "https://thejorgeramirezgroup.com/nj-home-buyer-guide",
        "title": "NJ Home Buyer Guide | Documents, Offers & Closing",
        "description": (
            "Use a source-backed New Jersey home buyer roadmap for budgeting, Loan "
            "Estimates, offers, inspections, NJHMFA programs, and closing documents."
        ),
        "llm_context": (
            "Primary-source New Jersey home buyer guide covering budgeting, Loan Estimates, "
            "NJHMFA programs, brokerage agreements, offers, inspections, Closing Disclosures, "
            "and fair housing. Reviewed 2026-08-26."
        ),
        "og_title": "A Document-First New Jersey Home Buyer Guide",
        "home_href": "/",
        "language_href": "/es/nj-home-buyer-guide",
        "language_label": "ES",
        "language_aria": "Leer esta guía en español",
        "skip": "Skip to main content",
        "nav": [
            ("Roadmap", "#roadmap", "guide-nav__desktop-only"),
            ("Programs", "/blog/first-time-home-buyer-nj-guide", "guide-nav__desktop-only"),
            ("Calculators", "#resources", "guide-nav__desktop-only"),
        ],
        "call": "Call 908-230-7844",
        "call_short": "Call",
        "hero_eyebrow": "New Jersey buyer roadmap",
        "h1": "A document-first guide to buying a home in New Jersey",
        "hero_lede": (
            "Build your plan around the documents that control the transaction: your "
            "budget, written loan terms, brokerage agreement, signed contract, property "
            "records, inspection, title work, insurance, and final closing disclosure."
        ),
        "proofs": [
            "State and federal primary sources",
            "Reviewed 2026-08-26",
            "English and Spanish",
        ],
        "read_roadmap": "Read the buyer roadmap",
        "get_pdf": "Get the portable guide",
        "review_label": "Source review",
        "review_copy": (
            "Official NJDOBI, NJHMFA, CFPB, and HUD pages checked on 2026-08-26. "
            "Program terms and eligibility can change."
        ),
        "review_link": "See every primary source",
        "overview_eyebrow": "How to use this guide",
        "overview_title": "Replace rules of thumb with written evidence",
        "overview_intro": (
            "A useful buyer plan does not depend on a generic percentage, a market slogan, "
            "or a town ranking. It records what applies to your finances, your contract, "
            "and the specific property."
        ),
        "overview_cards": [
            (
                "01 / Finance",
                "Price the complete obligation",
                "Use lender documents and property-specific estimates for payment, taxes, insurance, association obligations, maintenance, and cash needed to close.",
            ),
            (
                "02 / Rights",
                "Know who represents whom",
                "Read the Consumer Information Statement and brokerage service agreement before relying on advice or agreeing to compensation terms.",
            ),
            (
                "03 / Property",
                "Verify the address, not the sales pitch",
                "Connect every decision to the signed contract, current public records, independent inspections, title work, and provider documents.",
            ),
        ],
        "roadmap_eyebrow": "Transaction sequence",
        "roadmap_title": "Nine checkpoints from planning to keys",
        "roadmap_intro": (
            "The order can vary with the contract, loan, and property. Use these checkpoints "
            "to identify the document, professional, or agency that can answer each question."
        ),
        "steps": [
            {
                "id": "budget",
                "number": "01",
                "title": "Set a housing budget before choosing a price",
                "body": (
                    "Start with the payment and reserves you can carry without crowding out "
                    "other priorities. Account for principal and interest, taxes, homeowners "
                    "insurance, mortgage insurance when applicable, association obligations, "
                    "utilities, maintenance, moving, and immediate property work."
                ),
                "checkpoint": (
                    "Use the CFPB toolkit to define your ceiling, then use the site calculator "
                    "only as a planning estimate. A lender's written terms and property-specific "
                    "figures replace calculator assumptions."
                ),
                "links": [
                    ("Open the CFPB home-loan toolkit", "https://www.consumerfinance.gov/owning-a-home/explore/home-loan-toolkit/", True),
                    ("Use the NJ mortgage calculator", "/tools/mortgage-calculator", False),
                ],
            },
            {
                "id": "loan-estimate",
                "number": "02",
                "title": "Compare written loan offers line by line",
                "body": (
                    "Request Loan Estimates for comparable loan requests. Review the loan type, "
                    "term, rate and lock status, projected payment, mortgage insurance, origination "
                    "charges, services, lender credits, prepayment features, and estimated cash to close."
                ),
                "checkpoint": (
                    "Keep each Loan Estimate and ask the lender to explain every difference in "
                    "writing. Do not choose a loan from a rate headline alone."
                ),
                "links": [
                    ("Use the CFPB Loan Estimate explainer", "https://www.consumerfinance.gov/owning-a-home/loan-estimate/", True),
                    ("Open CFPB model forms and samples", "https://www.consumerfinance.gov/compliance/compliance-resources/mortgage-resources/tila-respa-integrated-disclosures/forms-samples/", True),
                ],
            },
            {
                "id": "programs",
                "number": "03",
                "title": "Check assistance at the official program source",
                "body": (
                    "NJHMFA publishes mortgage and assistance programs with program-specific "
                    "eligibility, property, occupancy, income, purchase-price, education, and "
                    "participating-lender rules. Those terms can change."
                ),
                "checkpoint": (
                    "Confirm current eligibility directly with NJHMFA and a participating lender. "
                    "Save the fact sheet and limit document used for your application instead of "
                    "relying on an amount quoted by an older article or downloadable file."
                ),
                "links": [
                    ("Open current NJHMFA program materials", "https://www.nj.gov/dca/hmfa/homebuyers-and-renters/homebuyers/", True),
                    ("Read the NJHMFA homebuyer FAQs", "https://www.nj.gov/dca/hmfa/homebuyers-and-renters/faqs/", True),
                    ("Use the site's NJ program guide", "/blog/first-time-home-buyer-nj-guide", False),
                ],
            },
            {
                "id": "representation",
                "number": "04",
                "title": "Put the brokerage relationship in writing",
                "body": (
                    "New Jersey recognizes several brokerage relationships. Read the Consumer "
                    "Information Statement and the written brokerage service agreement so the "
                    "services, relationship, term, compensation, and exit provisions are clear."
                ),
                "checkpoint": (
                    "Broker compensation is fully negotiable and not set by law. Ask who may pay "
                    "it, what the agreement requires if the seller offers less, and how any change "
                    "will be documented before you sign."
                ),
                "links": [
                    ("Read NJDOBI Bulletin 24-11", "https://www.nj.gov/dobi/bulletins/blt24_11.pdf", True),
                    ("Open NJDOBI real-estate consumer topics", "https://www.nj.gov/dobi/division_consumers/realestate/re_menu.htm", True),
                ],
            },
            {
                "id": "property-search",
                "number": "05",
                "title": "Research objective facts for each address",
                "body": (
                    "Compare the commute you would actually make, current tax records, zoning and "
                    "permitted use, municipal files, flood and environmental sources, property "
                    "condition, association documents, insurance availability, and accessibility needs."
                ),
                "checkpoint": (
                    "Jorge provides address-specific sources and does not rank places by protected "
                    "traits or demographic profiles. You choose the criteria; official records and "
                    "your own visits supply the evidence."
                ),
                "links": [
                    ("Explore the site's six county guides", "/counties", False),
                    ("Open the NJ commute map", "/nj-train-map", False),
                    ("Read HUD's Fair Housing Act overview", "https://www.hud.gov/helping-americans/fair-housing-act-overview", True),
                ],
            },
            {
                "id": "offer",
                "number": "06",
                "title": "Treat the signed contract as the rulebook",
                "body": (
                    "An offer can address price, deposits, included items, financing, appraisal, "
                    "inspection, title, closing, possession, and other negotiated terms. Once signed, "
                    "the contract controls the deadlines, notices, rights, and remedies."
                ),
                "checkpoint": (
                    "New Jersey does not require a home buyer to hire an attorney. NJDOBI says many "
                    "buyers choose legal representation. For a contract prepared by a real-estate "
                    "licensee, its guide describes an attorney-review clause with three business days "
                    "after delivery of fully signed contracts to consult an attorney. Do not calculate "
                    "a deadline from this page; obtain it from the signed contract and your attorney if retained."
                ),
                "links": [
                    ("Read NJDOBI's official buying guide", "https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf", True),
                ],
            },
            {
                "id": "inspection",
                "number": "07",
                "title": "Use independent due diligence on the property",
                "body": (
                    "A home inspection evaluates visible conditions within its scope; it does not "
                    "replace title work, appraisal, survey, insurance review, permit research, or "
                    "specialist evaluation. Read the inspection agreement and report, then track "
                    "contract notice dates and any negotiated response in writing."
                ),
                "checkpoint": (
                    "Match each concern to the professional qualified to evaluate it and to the "
                    "contract provision governing your options. Keep reports, invoices, permits, "
                    "disclosures, and written resolutions together."
                ),
                "links": [
                    ("Review the inspection section in NJDOBI's guide", "https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf", True),
                ],
            },
            {
                "id": "closing",
                "number": "08",
                "title": "Reconcile underwriting, title, insurance, and value",
                "body": (
                    "Keep the lender updated, review the appraisal as a value opinion rather than a "
                    "condition inspection, resolve title questions, obtain property-specific insurance "
                    "terms, and document any association or municipal requirements."
                ),
                "checkpoint": (
                    "Before closing, compare the final Closing Disclosure with the latest Loan Estimate. "
                    "Trace every change, confirm cash-to-close instructions through a trusted channel, "
                    "and resolve discrepancies before signing."
                ),
                "links": [
                    ("Use the CFPB Closing Disclosure explainer", "https://www.consumerfinance.gov/owning-a-home/closing-disclosure/", True),
                    ("Open CFPB model forms and samples", "https://www.consumerfinance.gov/compliance/compliance-resources/mortgage-resources/tila-respa-integrated-disclosures/forms-samples/", True),
                ],
            },
            {
                "id": "closing-day",
                "number": "09",
                "title": "Verify the property and documents before accepting keys",
                "body": (
                    "Use the final walk-through to compare the property's condition with the contract "
                    "and written repair agreements. Read every closing document, confirm the deed and "
                    "recording plan, retain the signed package, and know where future tax, insurance, "
                    "association, and loan notices will arrive."
                ),
                "checkpoint": (
                    "The final question is not whether a generic checklist is complete. It is whether "
                    "the signed contract, lender, title or closing professional, and property records "
                    "agree on what will happen next."
                ),
                "links": [
                    ("Use the full CFPB closing roadmap", "https://www.consumerfinance.gov/owning-a-home/close/", True),
                ],
            },
        ],
        "money_eyebrow": "Cash planning",
        "money_title": "Build the number from documents, not a universal percentage",
        "money_intro": (
            "The amount needed changes with the loan, property, contract, timing, providers, "
            "taxes, insurance, and credits. Request written figures for each category."
        ),
        "money_cards": [
            ("Before an offer", "Emergency reserve, moving, near-term property work, lender-requested funds, and the deposit structure you are prepared to place at risk under the contract."),
            ("On the Loan Estimate", "Loan amount, projected payment, estimated taxes and insurance, origination charges, services, credits, prepaid items, escrow, and estimated cash to close."),
            ("Property-specific work", "Inspection and specialist evaluations, survey or title work, insurance quote, association documents, permits, municipal requirements, and planned repairs."),
            ("Before signing", "Compare the latest Loan Estimate, Closing Disclosure, contract credits, deposit records, title or closing statement, and verified transfer instructions."),
        ],
        "resources_eyebrow": "First-party tools",
        "resources_title": "Continue with the current site resources",
        "resources_intro": (
            "These tools support planning. Your lender, signed contract, current agency materials, "
            "and property-specific documents remain controlling."
        ),
        "resources": [
            ("NJHMFA program guide", "Understand the questions to take to NJHMFA and a participating lender without relying on frozen assistance amounts.", "/blog/first-time-home-buyer-nj-guide", "Review programs"),
            ("Mortgage calculator", "Model payment components, then replace each assumption with the written loan and property figures you receive.", "/tools/mortgage-calculator", "Open calculator"),
            ("Closing-cost calculator", "Organize possible line items and compare the result with your Loan Estimate and Closing Disclosure.", "/closing-costs-calculator", "Plan closing items"),
            ("First-time buyer due-diligence guide", "Use the deeper document checklist for counseling, insurance, title, appraisal, inspection, and closing review.", "/blog/first-time-home-buyer-nj-guide", "Read the detailed guide"),
        ],
        "fair_title": "Equal access is part of the process",
        "fair_copy": (
            "The Fair Housing Act applies to buying, mortgage lending, and other housing-related "
            "activities. Housing choices should be supported with neutral, objective, and "
            "address-specific information rather than demographic assumptions or protected traits."
        ),
        "fair_link": "Read HUD's Fair Housing Act overview",
        "guide_eyebrow": "Portable planning copy",
        "guide_title": "Download the refreshed buyer workbook",
        "guide_intro": (
            "The PDF mirrors this evidence-first process and points back to current agency sources. "
            "Enter your email for immediate delivery; a phone number and text consent are optional."
        ),
        "form_title": "Send me the NJ buyer guide",
        "form_intro": "The download starts after the form is submitted, even if follow-up delivery is temporarily unavailable.",
        "name_label": "First name",
        "name_placeholder": "First name",
        "email_label": "Email address",
        "email_placeholder": "you@example.com",
        "phone_label": "Phone",
        "phone_optional": "optional",
        "phone_placeholder": "Phone for optional text updates",
        "sms_label": (
            "Text me too (optional). I agree that Jorge Ramirez, licensed New Jersey real "
            "estate agent with The Jorge Ramirez Group at Keller Williams Premier Properties, "
            "may call and text me about this request and related real-estate updates, including "
            "with automated technology. Consent is not a condition of receiving the guide or "
            "making a purchase. Message frequency varies; message and data rates may apply. "
            "Reply STOP to opt out or HELP for help."
        ),
        "privacy": "See the Privacy Policy and SMS Terms.",
        "privacy_link": "/privacy-policy",
        "sms_link": "/sms-terms",
        "submit": "Send my free guide",
        "form_note": "Email is required for follow-up. Phone and text consent are optional.",
        "error_name": "Enter your first name.",
        "error_email": "Enter a valid email address.",
        "sending": "Preparing your guide...",
        "noscript": "JavaScript is off. Download the buyer guide directly.",
        "success_title": "Your buyer guide is ready",
        "success_copy": "The download should begin automatically. Use the button if it does not.",
        "download": "Download the buyer guide PDF",
        "pdf_caveat": (
            "Program, loan, and property terms change. Confirm current details through the "
            "primary-source links on this page and the documents for your transaction."
        ),
        "sources_eyebrow": "Research record",
        "sources_title": "Primary sources used for this guide",
        "sources_intro": (
            "Each link goes directly to the responsible state or federal agency. Checked "
            "2026-08-26; always use the version available when you act."
        ),
        "source_checked": "Checked 2026-08-26",
        "source_open": "Open official source",
        "faq_eyebrow": "Direct answers",
        "faq_title": "New Jersey home-buyer questions",
        "faq_intro": "Short answers below are grounded in the visible primary sources on this page.",
        "faqs": [
            (
                "Does New Jersey require a home buyer to hire an attorney?",
                "New Jersey does not require a home buyer to hire an attorney. NJDOBI says many buyers choose legal representation because real-estate licensees cannot provide legal advice. A lawyer retained by the buyer represents that buyer's interests.",
            ),
            (
                "How much money do I need to buy a home in New Jersey?",
                "There is no universal percentage for every buyer. Build the amount from the chosen loan, deposit terms, property-specific taxes and insurance, provider charges, association obligations, planned work, credits, Loan Estimate, and final Closing Disclosure.",
            ),
            (
                "How should I verify an NJHMFA program?",
                "Confirm current eligibility directly with NJHMFA and a participating lender. Use the program page, current fact sheet, current limits, and the requirements documented for your application; do not rely on a frozen amount from an older guide.",
            ),
            (
                "What is the difference between a Loan Estimate and a Closing Disclosure?",
                "The Loan Estimate describes the requested mortgage's projected terms and costs. The Closing Disclosure presents final loan and transaction details. Compare them line by line and ask the lender or closing professional to explain changes before signing.",
            ),
            (
                "Is an appraisal the same as a home inspection?",
                "No. An appraisal supports a lender's value analysis; an independent home inspection evaluates property conditions within the inspector's scope. Neither replaces title, survey, insurance, permit, environmental, or specialist review when relevant.",
            ),
            (
                "What information should I compare between locations?",
                "Choose neutral criteria tied to your needs and the address: actual travel routes, taxes, zoning and permitted use, municipal records, flood and environmental sources, accessibility, condition, association documents, insurance, and your own visits.",
            ),
        ],
        "cta_eyebrow": "Local representation",
        "cta_title": "Bring the documents, not the guesswork",
        "cta_copy": (
            "Jorge Ramirez is a New Jersey real-estate agent, license #1754604, with Keller "
            "Williams Premier Properties. He serves buyers across Union, Essex, Morris, Hudson, "
            "Middlesex, and Somerset counties."
        ),
        "cta_primary": "Discuss a home search",
        "cta_secondary": "Browse properties",
        "contact_href": "/#contact",
        "search_href": "/property-search",
        "disclaimer": (
            "Educational information only; not legal, tax, financial, lending, insurance, "
            "inspection, title, or engineering advice. The signed contract and your licensed "
            "professionals control your transaction."
        ),
        "footer_about": "Full-time Realtor with Keller Williams Premier Properties since 2017.",
        "footer_counties": "Counties served",
        "footer_county_links": [
            ("Union", "/counties/union-county"),
            ("Essex", "/counties/essex-county"),
            ("Morris", "/counties/morris-county"),
            ("Hudson", "/counties/hudson-county"),
            ("Middlesex", "/counties/middlesex-county"),
            ("Somerset", "/counties/somerset-county"),
        ],
        "footer_buyer": "Buyer resources",
        "footer_buyer_links": [
            ("Buy a home", "/buy-a-home"),
            ("Property search", "/property-search"),
            ("NJHMFA programs", "/blog/first-time-home-buyer-nj-guide"),
            ("Mortgage calculator", "/tools/mortgage-calculator"),
            ("Closing planner", "/closing-costs-calculator"),
        ],
        "copyright": "© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties.",
        "license": "New Jersey real-estate license #1754604",
        "breadcrumb_home": "Home",
        "breadcrumb_page": "NJ Home Buyer Guide",
    },
    "es": {
        "lang": "es-US",
        "canonical": "https://thejorgeramirezgroup.com/es/nj-home-buyer-guide",
        "title": "Guía para Comprar Casa en NJ | Proceso y Documentos",
        "description": (
            "Usa una guía de Nueva Jersey con fuentes oficiales para presupuesto, Loan Estimate, "
            "ofertas, inspección, programas NJHMFA y documentos de cierre."
        ),
        "llm_context": (
            "Guía de compra de vivienda en Nueva Jersey basada en fuentes primarias sobre "
            "presupuesto, Loan Estimate, programas NJHMFA, corretaje, ofertas, inspecciones, "
            "Closing Disclosure y vivienda justa. Revisada el 2026-08-26."
        ),
        "og_title": "Guía Documental para Comprar Vivienda en Nueva Jersey",
        "home_href": "/es",
        "language_href": "/nj-home-buyer-guide",
        "language_label": "EN",
        "language_aria": "Read this guide in English",
        "skip": "Saltar al contenido principal",
        "nav": [
            ("Ruta", "#roadmap", "guide-nav__desktop-only"),
            ("Programas", "/es/blog/first-time-home-buyer-nj-guide", "guide-nav__desktop-only"),
            ("Calculadoras", "#resources", "guide-nav__desktop-only"),
        ],
        "call": "Llamar al 908-230-7844",
        "call_short": "Llamar",
        "hero_eyebrow": "Ruta del comprador en Nueva Jersey",
        "h1": "Guía documental para comprar vivienda en Nueva Jersey",
        "hero_lede": (
            "Organiza tu plan alrededor de los documentos que controlan la operación: presupuesto, "
            "términos escritos del préstamo, acuerdo de corretaje, contrato firmado, registros de la "
            "propiedad, inspección, título, seguro y divulgación final del cierre."
        ),
        "proofs": [
            "Fuentes primarias estatales y federales",
            "Revisada el 2026-08-26",
            "Inglés y español",
        ],
        "read_roadmap": "Leer la ruta de compra",
        "get_pdf": "Obtener la guía portátil",
        "review_label": "Revisión de fuentes",
        "review_copy": (
            "Páginas oficiales de NJDOBI, NJHMFA, CFPB y HUD verificadas el 2026-08-26. "
            "Los programas y requisitos pueden cambiar."
        ),
        "review_link": "Ver todas las fuentes primarias",
        "overview_eyebrow": "Cómo usar esta guía",
        "overview_title": "Sustituye las reglas generales por evidencia escrita",
        "overview_intro": (
            "Un plan útil no depende de un porcentaje genérico, un eslogan del mercado o una "
            "clasificación de municipios. Registra lo que corresponde a tus finanzas, tu contrato "
            "y la propiedad específica."
        ),
        "overview_cards": [
            ("01 / Finanzas", "Calcula la obligación completa", "Usa documentos del prestamista y estimados de la propiedad para pago, impuestos, seguro, asociación, mantenimiento y efectivo necesario para cerrar."),
            ("02 / Derechos", "Entiende quién representa a quién", "Lee la Declaración de Información al Consumidor y el acuerdo de servicios de corretaje antes de depender de recomendaciones o aceptar compensación."),
            ("03 / Propiedad", "Verifica la dirección, no el discurso", "Relaciona cada decisión con el contrato firmado, registros públicos vigentes, inspecciones independientes, título y documentos de proveedores."),
        ],
        "roadmap_eyebrow": "Secuencia de la operación",
        "roadmap_title": "Nueve puntos de control desde la planificación hasta las llaves",
        "roadmap_intro": (
            "El orden puede variar según el contrato, el préstamo y la propiedad. Usa estos puntos "
            "para identificar el documento, profesional o agencia que puede responder cada pregunta."
        ),
        "steps": [
            {
                "id": "budget", "number": "01", "title": "Define un presupuesto de vivienda antes del precio",
                "body": "Comienza con el pago y las reservas que puedes sostener sin desplazar otras prioridades. Incluye principal e intereses, impuestos, seguro de propietario, seguro hipotecario cuando corresponda, asociación, servicios, mantenimiento, mudanza y trabajo inmediato en la propiedad.",
                "checkpoint": "Usa el kit de la CFPB para fijar tu límite y la calculadora del sitio solo como estimado. Los términos escritos del prestamista y las cifras de la propiedad sustituyen los supuestos.",
                "links": [("Abrir el kit hipotecario de la CFPB", "https://www.consumerfinance.gov/owning-a-home/explore/home-loan-toolkit/", True), ("Usar la calculadora hipotecaria de NJ", "/es/tools/mortgage-calculator", False)],
            },
            {
                "id": "loan-estimate", "number": "02", "title": "Compara ofertas escritas línea por línea",
                "body": "Solicita un Loan Estimate para solicitudes comparables. Revisa tipo, plazo, tasa y bloqueo, pago proyectado, seguro hipotecario, cargos de originación, servicios, créditos del prestamista, penalidades y efectivo estimado para cerrar.",
                "checkpoint": "Conserva cada Loan Estimate y pide al prestamista que explique por escrito toda diferencia. No elijas un préstamo solo por un titular de tasa.",
                "links": [("Usar la explicación del Loan Estimate de la CFPB", "https://www.consumerfinance.gov/owning-a-home/loan-estimate/", True), ("Abrir modelos y ejemplos de la CFPB", "https://www.consumerfinance.gov/compliance/compliance-resources/mortgage-resources/tila-respa-integrated-disclosures/forms-samples/", True)],
            },
            {
                "id": "programs", "number": "03", "title": "Verifica la asistencia en la fuente oficial",
                "body": "NJHMFA publica programas hipotecarios y de asistencia con requisitos propios de elegibilidad, propiedad, ocupación, ingresos, precio, educación y prestamista participante. Esos términos pueden cambiar.",
                "checkpoint": "Confirma la elegibilidad vigente directamente con NJHMFA y un prestamista participante. Guarda la hoja informativa y el documento de límites usados en tu solicitud, en vez de depender de una cifra de un artículo o archivo anterior.",
                "links": [("Abrir materiales vigentes de NJHMFA", "https://www.nj.gov/dca/hmfa/homebuyers-and-renters/homebuyers/", True), ("Leer preguntas frecuentes de NJHMFA", "https://www.nj.gov/dca/hmfa/homebuyers-and-renters/faqs/", True), ("Usar la guía de programas del sitio", "/es/blog/first-time-home-buyer-nj-guide", False)],
            },
            {
                "id": "representation", "number": "04", "title": "Deja por escrito la relación de corretaje",
                "body": "Nueva Jersey reconoce varias relaciones de corretaje. Lee la Declaración de Información al Consumidor y el acuerdo escrito para entender servicios, relación, plazo, compensación y terminación.",
                "checkpoint": "La compensación del corredor es totalmente negociable y no está fijada por ley. Pregunta quién podría pagarla, qué exige el acuerdo si el vendedor ofrece menos y cómo se documentará cualquier cambio antes de firmar.",
                "links": [("Leer el Boletín 24-11 de NJDOBI", "https://www.nj.gov/dobi/bulletins/blt24_11.pdf", True), ("Abrir temas de consumo inmobiliario de NJDOBI", "https://www.nj.gov/dobi/division_consumers/realestate/re_menu.htm", True)],
            },
            {
                "id": "property-search", "number": "05", "title": "Investiga hechos objetivos para cada dirección",
                "body": "Compara el trayecto que realmente harías, registros tributarios vigentes, zonificación y uso permitido, archivos municipales, fuentes de inundación y ambiente, condición, documentos de asociación, disponibilidad de seguro y necesidades de accesibilidad.",
                "checkpoint": "Jorge proporciona fuentes ligadas a la dirección y no clasifica lugares por características protegidas o perfiles demográficos. Tú defines los criterios; los registros oficiales y tus propias visitas aportan la evidencia.",
                "links": [("Explorar las guías de municipios y condados", "/es/communities", False), ("Abrir el mapa de transporte de NJ", "/es/nj-train-map", False), ("Leer la explicación de HUD sobre Vivienda Justa", "https://www.hud.gov/helping-americans/fair-housing-act-overview", True)],
            },
            {
                "id": "offer", "number": "06", "title": "Trata el contrato firmado como el reglamento",
                "body": "Una oferta puede cubrir precio, depósitos, bienes incluidos, financiación, tasación, inspección, título, cierre, posesión y otros términos negociados. Una vez firmado, el contrato controla plazos, avisos, derechos y remedios.",
                "checkpoint": "Nueva Jersey no exige que el comprador contrate a un abogado. NJDOBI indica que muchos compradores eligen representación legal. Para un contrato preparado por un licenciatario inmobiliario, su guía describe una cláusula de revisión por abogado con tres días hábiles después de recibir los contratos totalmente firmados. No calcules un plazo desde esta página; obténlo del contrato y de tu abogado si contratas uno.",
                "links": [("Leer la guía oficial de compra de NJDOBI", "https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf", True)],
            },
            {
                "id": "inspection", "number": "07", "title": "Realiza diligencia independiente sobre la propiedad",
                "body": "Una inspección de vivienda evalúa condiciones visibles dentro de su alcance; no sustituye título, tasación, survey, seguro, permisos ni evaluaciones especializadas. Lee el acuerdo y el informe, y registra los avisos contractuales y respuestas negociadas por escrito.",
                "checkpoint": "Asigna cada inquietud al profesional cualificado para evaluarla y a la cláusula del contrato que gobierna tus opciones. Conserva informes, facturas, permisos, divulgaciones y resoluciones escritas.",
                "links": [("Revisar la sección de inspección de NJDOBI", "https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf", True)],
            },
            {
                "id": "closing", "number": "08", "title": "Concilia aprobación, título, seguro y valor",
                "body": "Mantén informado al prestamista, revisa la tasación como opinión de valor y no como inspección de condición, resuelve preguntas de título, obtén términos de seguro para la propiedad y documenta requisitos de asociación o municipio.",
                "checkpoint": "Antes del cierre, compara el Closing Disclosure final con el Loan Estimate más reciente. Rastrea cada cambio, confirma las instrucciones para transferir fondos por un canal confiable y resuelve diferencias antes de firmar.",
                "links": [("Usar la explicación del Closing Disclosure de la CFPB", "https://www.consumerfinance.gov/owning-a-home/closing-disclosure/", True), ("Abrir modelos y ejemplos de la CFPB", "https://www.consumerfinance.gov/compliance/compliance-resources/mortgage-resources/tila-respa-integrated-disclosures/forms-samples/", True)],
            },
            {
                "id": "closing-day", "number": "09", "title": "Verifica propiedad y documentos antes de recibir las llaves",
                "body": "Usa el recorrido final para comparar la condición con el contrato y las reparaciones escritas. Lee cada documento de cierre, confirma la escritura y su registro, guarda el paquete firmado y sabe dónde llegarán avisos futuros de impuestos, seguro, asociación y préstamo.",
                "checkpoint": "La pregunta final no es si completaste una lista genérica, sino si el contrato, el prestamista, el profesional de título o cierre y los registros coinciden en lo que ocurrirá después.",
                "links": [("Usar la ruta completa de cierre de la CFPB", "https://www.consumerfinance.gov/owning-a-home/close/", True)],
            },
        ],
        "money_eyebrow": "Plan de efectivo",
        "money_title": "Construye la cifra desde documentos, no desde un porcentaje universal",
        "money_intro": "La cantidad cambia con el préstamo, propiedad, contrato, calendario, proveedores, impuestos, seguro y créditos. Solicita cifras escritas para cada categoría.",
        "money_cards": [
            ("Antes de ofertar", "Reserva de emergencia, mudanza, trabajo próximo en la propiedad, fondos pedidos por el prestamista y depósitos que estás dispuesto a comprometer bajo el contrato."),
            ("En el Loan Estimate", "Monto del préstamo, pago proyectado, impuestos y seguro estimados, cargos de originación, servicios, créditos, prepagos, escrow y efectivo estimado para cerrar."),
            ("Trabajo de la propiedad", "Inspección y especialistas, survey o título, cotización de seguro, documentos de asociación, permisos, requisitos municipales y reparaciones previstas."),
            ("Antes de firmar", "Compara el Loan Estimate, Closing Disclosure, créditos del contrato, depósitos, estado de título o cierre e instrucciones de transferencia verificadas."),
        ],
        "resources_eyebrow": "Herramientas propias",
        "resources_title": "Continúa con los recursos vigentes del sitio",
        "resources_intro": "Estas herramientas apoyan la planificación. El prestamista, contrato, materiales oficiales y documentos de la propiedad siguen controlando.",
        "resources": [
            ("Guía de programas NJHMFA", "Prepara preguntas para NJHMFA y un prestamista participante sin depender de montos congelados.", "/es/blog/first-time-home-buyer-nj-guide", "Revisar programas"),
            ("Calculadora hipotecaria", "Modela componentes del pago y sustituye cada supuesto por cifras escritas del préstamo y la propiedad.", "/es/tools/mortgage-calculator", "Abrir calculadora"),
            ("Calculadora de cierre", "Organiza posibles partidas y compara el resultado con tu Loan Estimate y Closing Disclosure.", "/es/closing-costs-calculator", "Planificar partidas"),
            ("Guía de diligencia para primer comprador", "Usa la lista detallada para asesoría, seguro, título, tasación, inspección y cierre.", "/es/blog/first-time-home-buyer-nj-guide", "Leer la guía detallada"),
        ],
        "fair_title": "El acceso equitativo forma parte del proceso",
        "fair_copy": "La Ley de Vivienda Justa se aplica a la compra, el crédito hipotecario y otras actividades de vivienda. Las decisiones deben apoyarse en información neutral, objetiva y ligada a la dirección, no en supuestos demográficos o características protegidas.",
        "fair_link": "Leer la explicación de HUD sobre Vivienda Justa",
        "guide_eyebrow": "Copia portátil de planificación",
        "guide_title": "Descarga el cuaderno actualizado del comprador",
        "guide_intro": "El PDF refleja este proceso basado en evidencia y enlaza a fuentes oficiales vigentes. Ingresa tu correo para entrega inmediata; teléfono y consentimiento de texto son opcionales.",
        "form_title": "Envíame la guía del comprador de NJ",
        "form_intro": "La descarga comienza al enviar el formulario, aunque la entrega de seguimiento no esté disponible temporalmente.",
        "name_label": "Nombre",
        "name_placeholder": "Nombre",
        "email_label": "Correo electrónico",
        "email_placeholder": "tu@ejemplo.com",
        "phone_label": "Teléfono",
        "phone_optional": "opcional",
        "phone_placeholder": "Teléfono para textos opcionales",
        "sms_label": "Envíame textos también (opcional). Acepto que Jorge Ramirez, agente inmobiliario con licencia de Nueva Jersey de The Jorge Ramirez Group en Keller Williams Premier Properties, pueda llamarme y enviarme textos sobre esta solicitud y actualizaciones inmobiliarias relacionadas, incluso con tecnología automatizada. El consentimiento no es condición para recibir la guía ni comprar. La frecuencia varía; pueden aplicar tarifas de mensajes y datos. Responde STOP para cancelar o HELP para ayuda.",
        "privacy": "Consulta la Política de Privacidad y los Términos de SMS.",
        "privacy_link": "/es/privacy-policy",
        "sms_link": "/sms-terms",
        "submit": "Enviar mi guía gratis",
        "form_note": "El correo es obligatorio para seguimiento. Teléfono y textos son opcionales.",
        "error_name": "Ingresa tu nombre.",
        "error_email": "Ingresa un correo electrónico válido.",
        "sending": "Preparando tu guía...",
        "noscript": "JavaScript está desactivado. Descarga la guía directamente.",
        "success_title": "Tu guía del comprador está lista",
        "success_copy": "La descarga debe comenzar automáticamente. Usa el botón si no comienza.",
        "download": "Descargar la guía del comprador en PDF",
        "pdf_caveat": "Los programas, préstamos y condiciones de la propiedad cambian. Confirma los detalles con las fuentes primarias de esta página y los documentos de tu operación.",
        "sources_eyebrow": "Registro de investigación",
        "sources_title": "Fuentes primarias utilizadas en esta guía",
        "sources_intro": "Cada enlace lleva a la agencia estatal o federal responsable. Verificados el 2026-08-26; usa siempre la versión disponible cuando actúes.",
        "source_checked": "Verificada el 2026-08-26",
        "source_open": "Abrir fuente oficial",
        "faq_eyebrow": "Respuestas directas",
        "faq_title": "Preguntas del comprador de vivienda en Nueva Jersey",
        "faq_intro": "Las respuestas breves se apoyan en las fuentes primarias visibles de esta página.",
        "faqs": [
            ("¿Nueva Jersey exige que el comprador contrate a un abogado?", "Nueva Jersey no exige que el comprador contrate a un abogado. NJDOBI indica que muchos compradores eligen representación legal porque los licenciatarios inmobiliarios no pueden dar asesoría legal. Un abogado contratado por el comprador representa sus intereses."),
            ("¿Cuánto dinero necesito para comprar vivienda en Nueva Jersey?", "No existe un porcentaje universal para todos. Construye la cantidad desde el préstamo elegido, depósitos, impuestos y seguro de la propiedad, cargos de proveedores, asociación, trabajo previsto, créditos, Loan Estimate y Closing Disclosure final."),
            ("¿Cómo verifico un programa de NJHMFA?", "Confirma la elegibilidad vigente directamente con NJHMFA y un prestamista participante. Usa la página del programa, la hoja informativa, los límites vigentes y los requisitos documentados para tu solicitud; no dependas de una cifra de una guía anterior."),
            ("¿Qué diferencia hay entre Loan Estimate y Closing Disclosure?", "El Loan Estimate describe los términos y costos proyectados de la hipoteca solicitada. El Closing Disclosure presenta los detalles finales del préstamo y la operación. Compáralos línea por línea y pide explicación de cambios antes de firmar."),
            ("¿La tasación es lo mismo que la inspección?", "No. La tasación apoya el análisis de valor del prestamista; una inspección independiente evalúa condiciones dentro de su alcance. Ninguna sustituye título, survey, seguro, permisos, revisión ambiental o especialistas cuando correspondan."),
            ("¿Qué información conviene comparar entre ubicaciones?", "Elige criterios neutrales ligados a tus necesidades y la dirección: rutas reales, impuestos, zonificación y uso permitido, registros municipales, fuentes de inundación y ambiente, accesibilidad, condición, asociación, seguro y tus propias visitas."),
        ],
        "cta_eyebrow": "Representación local",
        "cta_title": "Trae los documentos, no las suposiciones",
        "cta_copy": "Jorge Ramirez es agente inmobiliario de Nueva Jersey, licencia #1754604, con Keller Williams Premier Properties. Atiende compradores en los condados de Union, Essex, Morris, Hudson, Middlesex y Somerset.",
        "cta_primary": "Hablar sobre mi búsqueda",
        "cta_secondary": "Buscar propiedades",
        "contact_href": "/es/#contact",
        "search_href": "/property-search",
        "disclaimer": "Información educativa solamente; no constituye asesoría legal, tributaria, financiera, hipotecaria, de seguros, inspección, título ni ingeniería. El contrato firmado y tus profesionales licenciados controlan la operación.",
        "footer_about": "Realtor de tiempo completo con Keller Williams Premier Properties desde 2017.",
        "footer_counties": "Condados atendidos",
        "footer_county_links": [("Union", "/es/counties/union-county"), ("Essex", "/es/counties/essex-county"), ("Morris", "/es/counties/morris-county"), ("Hudson", "/es/counties/hudson-county"), ("Middlesex", "/es/counties/middlesex-county"), ("Somerset", "/es/counties/somerset-county")],
        "footer_buyer": "Recursos del comprador",
        "footer_buyer_links": [("Comprar vivienda", "/es/buy-a-home"), ("Buscar propiedades", "/property-search"), ("Programas NJHMFA", "/es/blog/first-time-home-buyer-nj-guide"), ("Calculadora hipotecaria", "/es/tools/mortgage-calculator"), ("Planificador de cierre", "/es/closing-costs-calculator")],
        "copyright": "© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties.",
        "license": "Licencia inmobiliaria de Nueva Jersey #1754604",
        "breadcrumb_home": "Inicio",
        "breadcrumb_page": "Guía del Comprador de NJ",
    },
}


def esc(value: object, *, quote: bool = True) -> str:
    return html.escape(str(value), quote=quote)


def render_links(links: list[tuple[str, str, bool]]) -> str:
    rendered: list[str] = []
    for label, href, external in links:
        attrs = ' target="_blank" rel="noopener"' if external else ""
        rendered.append(
            f'<a class="source-link" href="{esc(href)}"{attrs}>{esc(label)} →</a>'
        )
    return "".join(rendered)


def render_steps(content: dict[str, object]) -> str:
    cards: list[str] = []
    for step in content["steps"]:
        cards.append(
            f'''<article class="roadmap-step" id="{esc(step["id"])}">
          <span class="roadmap-step__marker" aria-hidden="true">{esc(step["number"])}</span>
          <div><h3>{esc(step["title"])}</h3></div>
          <div>
            <p>{esc(step["body"])}</p>
            <div class="checkpoint"><strong>{"Verification checkpoint" if content["lang"] == "en-US" else "Punto de verificación"}</strong><p>{esc(step["checkpoint"])}</p>{render_links(step["links"])}</div>
          </div>
        </article>'''
        )
    return "\n".join(cards)


def source_summary(source: dict[str, object], language: str) -> str:
    if language == "es":
        return SOURCE_TRANSLATIONS["es"][source["id"]]
    return str(source["fact_supported"])


def render_sources(content: dict[str, object], manifest: dict[str, object], language: str) -> str:
    cards: list[str] = []
    for source in manifest["sources"]:
        cards.append(
            f'''<article class="source-card">
          <h3>{esc(source["publisher"])}</h3>
          <p>{esc(source_summary(source, language))}</p>
          <p class="source-card__date">{esc(content["source_checked"])}</p>
          <a class="source-link" href="{esc(source["url"])}" target="_blank" rel="noopener">{esc(content["source_open"])} →</a>
        </article>'''
        )
    return "\n".join(cards)


def json_ld(content: dict[str, object]) -> str:
    canonical = content["canonical"]
    faq_entities = [
        {
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {"@type": "Answer", "text": answer},
        }
        for question, answer in content["faqs"]
    ]
    areas = [{"@type": "AdministrativeArea", "name": county} for county in COUNTIES]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": content["title"],
                "description": content["description"],
                "inLanguage": content["lang"],
                "dateModified": "2026-08-26",
                "mainEntity": {"@id": f"{canonical}#article"},
            },
            {
                "@type": "Article",
                "@id": f"{canonical}#article",
                "url": canonical,
                "headline": content["h1"],
                "description": content["hero_lede"],
                "inLanguage": content["lang"],
                "dateModified": "2026-08-26",
                "image": "https://thejorgeramirezgroup.com/images/site/buyer-guide-cover.jpg",
                "author": {
                    "@type": "Person",
                    "@id": "https://thejorgeramirezgroup.com/#jorge-ramirez",
                    "name": "Jorge Ramirez",
                    "jobTitle": "New Jersey real-estate agent",
                    "identifier": {
                        "@type": "PropertyValue",
                        "propertyID": "New Jersey real-estate license",
                        "value": "1754604",
                    },
                    "worksFor": {
                        "@type": "Organization",
                        "name": "Keller Williams Premier Properties",
                    },
                    "areaServed": areas,
                },
                "publisher": {
                    "@type": "RealEstateAgent",
                    "@id": "https://thejorgeramirezgroup.com/#agent",
                    "name": "The Jorge Ramirez Group",
                    "url": "https://thejorgeramirezgroup.com/",
                    "telephone": "+19082307844",
                    "parentOrganization": {
                        "@type": "Organization",
                        "name": "Keller Williams Premier Properties",
                    },
                    "areaServed": areas,
                },
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{canonical}#breadcrumbs",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": content["breadcrumb_home"],
                        "item": "https://thejorgeramirezgroup.com/" if content["lang"] == "en-US" else "https://thejorgeramirezgroup.com/es",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": content["breadcrumb_page"],
                        "item": canonical,
                    },
                ],
            },
            {
                "@type": "FAQPage",
                "@id": f"{canonical}#faq-schema",
                "url": f"{canonical}#faq",
                "inLanguage": content["lang"],
                "mainEntity": faq_entities,
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def render_page(relative: str, language: str, manifest: dict[str, object]) -> str:
    c = CONTENT[language]
    alternate = "https://thejorgeramirezgroup.com/es/nj-home-buyer-guide" if language == "en" else "https://thejorgeramirezgroup.com/nj-home-buyer-guide"
    overview_cards = "\n".join(
        f'<article class="overview-card"><span class="overview-card__number">{esc(kicker)}</span><h3>{esc(title)}</h3><p>{esc(copy)}</p></article>'
        for kicker, title, copy in c["overview_cards"]
    )
    money_cards = "\n".join(
        f'<article class="money-card"><h3>{esc(title)}</h3><p>{esc(copy)}</p></article>'
        for title, copy in c["money_cards"]
    )
    resources = "\n".join(
        f'<article class="resource-card"><h3>{esc(title)}</h3><p>{esc(copy)}</p><a class="source-link" href="{esc(href)}">{esc(label)} →</a></article>'
        for title, copy, href, label in c["resources"]
    )
    faqs = "\n".join(
        f'<article class="faq-card"><h3>{esc(question)}</h3><p>{esc(answer)}</p></article>'
        for question, answer in c["faqs"]
    )
    nav_links = "\n".join(
        f'<li><a href="{esc(href)}" class="{esc(class_name)}">{esc(label)}</a></li>'
        for label, href, class_name in c["nav"]
    )
    county_links = "\n".join(
        f'<a href="{esc(href)}">{esc(label)}</a>' for label, href in c["footer_county_links"]
    )
    buyer_links = "\n".join(
        f'<a href="{esc(href)}">{esc(label)}</a>' for label, href in c["footer_buyer_links"]
    )
    field_suffix = "en" if language == "en" else "es"
    source_cards = render_sources(c, manifest, language)
    analytics = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-KMS6H85LB0');</script>"""
    return f'''<!DOCTYPE html>
<html lang="{esc(c["lang"])}">
<head>
  <!-- GENERATED: render_nj_home_buyer_guides.py. Edit the renderer and source manifest. -->
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0A0A0A">
  <title>{esc(c["title"])}</title>
  <meta name="description" content="{esc(c["description"])}">
  <meta name="llm-context" content="{esc(c["llm_context"])}">
  <meta name="author" content="Jorge Ramirez">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <link rel="canonical" href="{esc(c["canonical"])}">
  <link rel="alternate" hreflang="en-US" href="https://thejorgeramirezgroup.com/nj-home-buyer-guide">
  <link rel="alternate" hreflang="es-US" href="https://thejorgeramirezgroup.com/es/nj-home-buyer-guide">
  <link rel="alternate" hreflang="x-default" href="https://thejorgeramirezgroup.com/nj-home-buyer-guide">
  <meta name="geo.region" content="US-NJ">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{esc(c["canonical"])}">
  <meta property="og:title" content="{esc(c["og_title"])}">
  <meta property="og:description" content="{esc(c["description"])}">
  <meta property="og:image" content="https://thejorgeramirezgroup.com/images/site/buyer-guide-cover.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(c["og_title"])}">
  <meta name="twitter:description" content="{esc(c["description"])}">
  <meta name="twitter:image" content="https://thejorgeramirezgroup.com/images/site/buyer-guide-cover.jpg">
  <link rel="icon" href="/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;family=Playfair+Display:wght@600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css?v=20260826">
  <link rel="stylesheet" href="/css/nj-home-buyer-guide.css?v=20260826">
  <script type="application/ld+json">
{json_ld(c)}
  </script>
  {analytics}
  <script>if(window.location.hostname==='www.thejorgeramirezgroup.com'){{window.location.replace(window.location.href.replace('//www.','//'));}}</script>
</head>
<body>
  <a class="skip-link" href="#main">{esc(c["skip"])}</a>
  <nav class="guide-nav" aria-label="{'Primary navigation' if language == 'en' else 'Navegación principal'}">
    <div class="guide-nav__inner">
      <a class="guide-nav__brand" href="{esc(c["home_href"])}" aria-label="The Jorge Ramirez Group">
        <picture>
          <source srcset="/images/jorge-logo.webp" type="image/webp">
          <img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="250" height="100">
        </picture>
      </a>
      <ul class="guide-nav__links">
        {nav_links}
        <li><a class="guide-nav__language" href="{esc(c["language_href"])}" lang="{'es' if language == 'en' else 'en'}" aria-label="{esc(c["language_aria"])}">{esc(c["language_label"])}</a></li>
        <li><a class="guide-nav__phone" href="tel:+19082307844" aria-label="{esc(c["call"])}">{esc(c["call_short"])}</a></li>
      </ul>
    </div>
  </nav>

  <main id="main" tabindex="-1">
    <header class="guide-hero">
      <div class="guide-hero__inner">
        <p class="eyebrow">{esc(c["hero_eyebrow"])}</p>
        <h1>{esc(c["h1"])}</h1>
        <p class="guide-hero__lede">{esc(c["hero_lede"])}</p>
        <ul class="proof-row" aria-label="{'Guide facts' if language == 'en' else 'Datos de la guía'}">{''.join(f'<li>{esc(item)}</li>' for item in c["proofs"])}</ul>
        <div class="button-row">
          <a class="button button--primary" href="#roadmap">{esc(c["read_roadmap"])}</a>
          <a class="button button--ghost" href="#free-guide">{esc(c["get_pdf"])}</a>
        </div>
      </div>
    </header>

    <aside class="review-strip" aria-label="{esc(c["review_label"])}">
      <div class="review-strip__inner">
        <span><strong>{esc(c["review_label"])}:</strong> {esc(c["review_copy"])}</span>
        <a href="#sources">{esc(c["review_link"])} →</a>
      </div>
    </aside>

    <section class="section" id="overview" aria-labelledby="overview-heading">
      <div class="section__inner">
        <div class="section__intro">
          <div><p class="eyebrow">{esc(c["overview_eyebrow"])}</p><h2 id="overview-heading">{esc(c["overview_title"])}</h2></div>
          <p>{esc(c["overview_intro"])}</p>
        </div>
        <div class="overview-grid">{overview_cards}</div>
      </div>
    </section>

    <section class="section section--cream" id="roadmap" aria-labelledby="roadmap-heading">
      <div class="section__inner">
        <div class="section__intro">
          <div><p class="eyebrow">{esc(c["roadmap_eyebrow"])}</p><h2 id="roadmap-heading">{esc(c["roadmap_title"])}</h2></div>
          <p>{esc(c["roadmap_intro"])}</p>
        </div>
        <div class="roadmap">{render_steps(c)}</div>
      </div>
    </section>

    <section class="section" aria-labelledby="money-heading">
      <div class="section__inner">
        <div class="section__intro">
          <div><p class="eyebrow">{esc(c["money_eyebrow"])}</p><h2 id="money-heading">{esc(c["money_title"])}</h2></div>
          <p>{esc(c["money_intro"])}</p>
        </div>
        <div class="money-grid">{money_cards}</div>
      </div>
    </section>

    <section class="section section--cream" id="resources" aria-labelledby="resources-heading">
      <div class="section__inner">
        <div class="section__intro">
          <div><p class="eyebrow">{esc(c["resources_eyebrow"])}</p><h2 id="resources-heading">{esc(c["resources_title"])}</h2></div>
          <p>{esc(c["resources_intro"])}</p>
        </div>
        <div class="resource-grid">{resources}</div>
        <aside class="fair-housing-note">
          <h3>{esc(c["fair_title"])}</h3>
          <div><p>{esc(c["fair_copy"])}</p><a class="source-link" href="https://www.hud.gov/helping-americans/fair-housing-act-overview" target="_blank" rel="noopener">{esc(c["fair_link"])} →</a></div>
        </aside>
      </div>
    </section>

    <section class="section" id="free-guide" aria-labelledby="free-guide-heading">
      <div class="section__inner">
        <section class="lead-panel" id="lmCard" data-guide="buyer" data-pdf="/guides/nj-home-buyer-guide.pdf" data-source="{esc(c["form_source"] if "form_source" in c else ("nj-home-buyer-guide" if language == "en" else "es-nj-home-buyer-guide"))}" data-consent="{esc(CONSENT)}" data-error-name="{esc(c["error_name"])}" data-error-email="{esc(c["error_email"])}" data-sending="{esc(c["sending"])}">
          <div class="lead-panel__copy">
            <p class="eyebrow">{esc(c["guide_eyebrow"])}</p>
            <h2 id="free-guide-heading">{esc(c["guide_title"])}</h2>
            <p>{esc(c["guide_intro"])}</p>
            <form class="lead-form" id="lmForm" action="/api/lead" method="post" novalidate>
              <input type="hidden" name="guide" value="buyer">
              <input type="hidden" name="_source" value="{esc("nj-home-buyer-guide" if language == "en" else "es-nj-home-buyer-guide")}">
              <input type="hidden" name="intent" value="Buyer guide download">
              <input type="hidden" name="_next" value="/thank-you">
              <div class="honeypot" aria-hidden="true"><label for="buyer-guide-honey-{field_suffix}">Leave this field empty</label><input id="buyer-guide-honey-{field_suffix}" name="_honey" type="text" tabindex="-1" autocomplete="off"></div>
              <h3>{esc(c["form_title"])}</h3>
              <p>{esc(c["form_intro"])}</p>
              <label for="buyer-guide-name-{field_suffix}">{esc(c["name_label"])}</label>
              <input id="buyer-guide-name-{field_suffix}" name="name" type="text" autocomplete="given-name" required placeholder="{esc(c["name_placeholder"])}" aria-describedby="lmFormStatus">
              <label for="buyer-guide-email-{field_suffix}">{esc(c["email_label"])}</label>
              <input id="buyer-guide-email-{field_suffix}" name="email" type="email" autocomplete="email" required placeholder="{esc(c["email_placeholder"])}" aria-describedby="lmFormStatus">
              <label for="buyer-guide-phone-{field_suffix}">{esc(c["phone_label"])} <span class="lead-form__optional">({esc(c["phone_optional"])})</span></label>
              <input id="buyer-guide-phone-{field_suffix}" name="phone" type="tel" autocomplete="tel" placeholder="{esc(c["phone_placeholder"])}">
              <label class="lead-form__consent" for="buyer-guide-sms-{field_suffix}"><input id="buyer-guide-sms-{field_suffix}" name="smsConsent" type="checkbox" value="on"><span>{esc(c["sms_label"])}</span></label>
              <p class="lead-form__privacy">{esc(c["privacy"].split(" and ")[0] if language == "en" else "Consulta la")} <a href="{esc(c["privacy_link"])}">{'Privacy Policy' if language == 'en' else 'Política de Privacidad'}</a> {'and' if language == 'en' else 'y los'} <a href="{esc(c["sms_link"])}">{'SMS Terms' if language == 'en' else 'Términos de SMS'}</a>.</p>
              <p class="lead-form__status" id="lmFormStatus" role="alert" aria-live="assertive"></p>
              <button type="submit">{esc(c["submit"])}</button>
              <p class="lead-form__note">{esc(c["form_note"])}</p>
              <noscript><p>{esc(c["noscript"])} <a href="/guides/nj-home-buyer-guide.pdf" download>{esc(c["download"])}</a></p></noscript>
            </form>
          </div>
          <div class="lead-panel__visual">
            <img src="/images/site/buyer-guide-cover.jpg" alt="{'Cover of the NJ home buyer guide' if language == 'en' else 'Portada de la guía para compradores de vivienda en NJ'}" width="280" height="400" loading="lazy">
          </div>
        </section>
        <section class="lead-success" id="lmSuccess" tabindex="-1" hidden aria-labelledby="success-heading">
          <h2 id="success-heading">{esc(c["success_title"])}</h2>
          <p>{esc(c["success_copy"])}</p>
          <a class="button button--primary" id="lmDownload" href="/guides/nj-home-buyer-guide.pdf" download>{esc(c["download"])}</a>
          <p class="pdf-caveat">{esc(c["pdf_caveat"])}</p>
        </section>
      </div>
    </section>

    <section class="section section--dark" id="sources" aria-labelledby="sources-heading">
      <div class="section__inner">
        <div class="section__intro">
          <div><p class="eyebrow">{esc(c["sources_eyebrow"])}</p><h2 id="sources-heading">{esc(c["sources_title"])}</h2></div>
          <p>{esc(c["sources_intro"])}</p>
        </div>
        <div class="source-grid">{source_cards}</div>
      </div>
    </section>

    <section class="section" id="faq" aria-labelledby="faq-heading">
      <div class="section__inner">
        <div class="section__intro">
          <div><p class="eyebrow">{esc(c["faq_eyebrow"])}</p><h2 id="faq-heading">{esc(c["faq_title"])}</h2></div>
          <p>{esc(c["faq_intro"])}</p>
        </div>
        <div class="faq-grid">{faqs}</div>
      </div>
    </section>

    <section class="section section--cream" aria-labelledby="cta-heading">
      <div class="section__inner">
        <div class="cta-band">
          <p class="eyebrow">{esc(c["cta_eyebrow"])}</p>
          <h2 id="cta-heading">{esc(c["cta_title"])}</h2>
          <p>{esc(c["cta_copy"])}</p>
          <div class="button-row">
            <a class="button button--primary" href="{esc(c["contact_href"])}">{esc(c["cta_primary"])}</a>
            <a class="button button--ghost" href="{esc(c["search_href"])}">{esc(c["cta_secondary"])}</a>
          </div>
          <p class="pdf-caveat">{esc(c["disclaimer"])}</p>
        </div>
      </div>
    </section>
  </main>

  <footer class="guide-footer">
    <div class="guide-footer__inner">
      <section class="guide-footer__brand" aria-labelledby="footer-brand-heading">
        <img src="/images/jorge-logo.jpg" alt="The Jorge Ramirez Group" width="250" height="100" loading="lazy">
        <h2 id="footer-brand-heading">Jorge Ramirez</h2>
        <p>{esc(c["footer_about"])}</p>
        <p>488 Springfield Avenue<br>Summit, NJ 07901<br><a href="tel:+19082307844">908-230-7844</a><br><a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a></p>
      </section>
      <section class="guide-footer__links" aria-labelledby="footer-counties-heading"><h3 id="footer-counties-heading">{esc(c["footer_counties"])}</h3>{county_links}</section>
      <section class="guide-footer__links" aria-labelledby="footer-buyers-heading"><h3 id="footer-buyers-heading">{esc(c["footer_buyer"])}</h3>{buyer_links}</section>
    </div>
    <div class="guide-footer__bottom">
      <p>{esc(c["copyright"])}</p>
      <p>{esc(c["license"])} · {esc(c["disclaimer"])}</p>
    </div>
  </footer>

  <script defer src="/js/lead-magnet.js"></script>
  <script defer src="/js/lead-attribution.js"></script>
</body>
</html>
'''


def expected_outputs() -> dict[str, str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        relative: render_page(relative, language, manifest)
        for relative, language in OUTPUTS.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if rendered pages are stale")
    args = parser.parse_args()
    outputs = expected_outputs()
    stale: list[str] = []
    for relative, rendered in outputs.items():
        path = ROOT / relative
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != rendered:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
            print(f"rendered {relative}")
    if stale:
        print("stale buyer-guide output(s): " + ", ".join(stale), file=sys.stderr)
        return 1
    if args.check:
        print("buyer-guide outputs are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
