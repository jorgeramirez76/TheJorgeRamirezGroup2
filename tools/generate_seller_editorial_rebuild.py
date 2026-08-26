#!/usr/bin/env python3
"""Render the source-led bilingual seller-editorial pages and archive fallbacks."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "seller-editorial-rebuild.json"
FACTS_PATH = ROOT / "data" / "site-facts.json"
SITE = "https://thejorgeramirezgroup.com"
REVIEWED_ON = "2026-08-26"
RENDERER = "tools/generate_seller_editorial_rebuild.py"


Card = Tuple[str, str]


CONTENT: Dict[str, Dict[str, Dict[str, Any]]] = {
    "expired-listing": {
        "en": {
            "eyebrow": "Expired listing review · New Jersey",
            "lede": "Start with the record the first listing created: property condition, pricing evidence, access history, buyer feedback, disclosure status, media, distribution, competing homes and the written service scope.",
            "note_heading": "Do not reduce the result to one slogan",
            "note": "An expired term does not prove that the home was overpriced, poorly marketed, inaccessible or defective. It shows that the listing period ended without the planned transaction. Review the evidence before assigning a cause or changing the plan.",
            "sections": [
                {
                    "label": "Listing audit",
                    "heading": "Separate observed facts from assumptions",
                    "intro": "Create one dated file. Preserve the original listing, price changes, photographs, showing instructions, feedback, offers, inspection information and seller decisions. Then compare those records with the market evidence available during the same periods.",
                    "cards": [
                        ("Property record", "Confirm the legal municipality, property type, room and system facts, permits, association materials, known condition items and improvements. Correct factual errors before a new listing is published."),
                        ("Price evidence", "Rebuild the comparable-sale set with stated selection rules. Keep closed sales separate from pending activity and current competing listings. Note condition, location, terms and publication lag."),
                        ("Access record", "Review notice rules, unavailable dates, showing windows, occupancy constraints and instructions. Access can affect opportunity, but the record should show what actually occurred."),
                        ("Exposure record", "Retain the published description, media, distribution dates and material revisions. Check whether property facts were consistent across channels rather than measuring success by an unsupported impression count."),
                    ],
                },
                {
                    "label": "Relisting decision",
                    "heading": "Write the next scope before changing the public story",
                    "intro": "A revised plan should identify the work, responsible party, supporting evidence and decision date. Broker compensation remains negotiable and is not set by law; document the agreed services and compensation in the written brokerage services agreement.",
                    "cards": [
                        ("Condition and disclosures", "Update the property-condition file and use the NJDEP address tool for flood questions. Review any applicable federal lead information and municipal certificate path with the responsible professionals and agencies."),
                        ("Launch choices", "Record proposed price scenarios, preparation items, access rules, media, distribution, offer-review procedure and occupancy constraints. Avoid a launch date or price promise that the evidence cannot support."),
                        ("Representation scope", "Compare written services, communication method, seller responsibilities, termination terms and compensation. Confirm license and brokerage information through the current state resources."),
                        ("Decision checkpoint", "Set a date to review current competition, visits, written feedback and property-specific evidence. A checkpoint changes the plan only when the observed record supports the change."),
                    ],
                },
            ],
            "questions_heading": "Questions to take into a relisting meeting",
            "questions": [
                ("What changed during the first term?", "Build a dated list of price, condition, access, media, competition and offer changes. Separate seller decisions from external events and unverifiable opinions."),
                ("What needs to be verified now?", "Recheck active competition, recent comparable transactions, the property-condition statement, flood information, permits and municipal procedures that relate to the address."),
                ("What belongs in writing?", "Put the service scope, compensation, seller duties, communication, media use, access, offer handling and termination terms into the applicable agreements and instructions."),
            ],
            "cta_heading": "Review the record before choosing the next listing plan",
            "cta_text": "Bring the prior listing, condition notes, access history, offers and current questions. Jorge can organize a property-specific market review while legal and tax professionals address their respective subjects.",
        },
        "es": {
            "eyebrow": "Revisión de publicación vencida · Nueva Jersey",
            "lede": "Comience con el registro que dejó la primera publicación: condición, evidencia de precio, historial de acceso, comentarios, divulgaciones, imágenes, distribución, competencia y alcance escrito del servicio.",
            "note_heading": "No reduzca el resultado a una sola explicación",
            "note": "El vencimiento no demuestra por sí solo que el precio, mercadeo, acceso o condición causó el resultado. Demuestra que terminó el plazo sin la transacción planeada. Revise la evidencia antes de cambiar el plan.",
            "sections": [
                {
                    "label": "Auditoría de la publicación",
                    "heading": "Separe hechos observados de suposiciones",
                    "intro": "Prepare un archivo fechado. Conserve publicación, cambios de precio, fotografías, instrucciones de visitas, comentarios, ofertas, información de inspección y decisiones. Compare esos registros con evidencia del mismo período.",
                    "cards": [
                        ("Registro de la propiedad", "Confirme municipio legal, tipo de propiedad, espacios, sistemas, permisos, documentos de asociación, condición conocida y mejoras. Corrija hechos antes de publicar nuevamente."),
                        ("Evidencia de precio", "Actualice las ventas comparables con reglas de selección escritas. Separe cierres, actividad pendiente y competencia actual. Anote condición, ubicación, términos y rezago de publicación."),
                        ("Registro de acceso", "Revise avisos, fechas no disponibles, horarios, ocupación e instrucciones. El acceso puede afectar oportunidades, pero el registro debe mostrar lo que ocurrió."),
                        ("Registro de exposición", "Conserve descripción, imágenes, fechas de distribución y cambios materiales. Revise coherencia de los hechos en cada canal sin depender de conteos no verificables."),
                    ],
                },
                {
                    "label": "Decisión para relistar",
                    "heading": "Escriba el nuevo alcance antes de cambiar el mensaje",
                    "intro": "El plan revisado debe indicar trabajo, responsable, evidencia y fecha de decisión. La compensación del corredor es negociable y no la fija la ley; documente los servicios y términos acordados en el contrato correspondiente.",
                    "cards": [
                        ("Condición y divulgaciones", "Actualice el archivo de condición y use la herramienta de NJDEP para preguntas de inundación. Revise información federal sobre plomo y trámites municipales con las autoridades correspondientes."),
                        ("Opciones de lanzamiento", "Anote escenarios de precio, preparación, acceso, imágenes, distribución, revisión de ofertas y ocupación. Evite prometer una fecha o un resultado que la evidencia no respalda."),
                        ("Alcance de representación", "Compare servicios escritos, comunicación, responsabilidades, terminación y compensación. Confirme licencia y corretaje mediante recursos estatales actuales."),
                        ("Punto de revisión", "Fije una fecha para revisar competencia, visitas, comentarios escritos y evidencia de la propiedad. Cambie el plan cuando el registro observado lo respalde."),
                    ],
                },
            ],
            "questions_heading": "Preguntas para una reunión de relistado",
            "questions": [
                ("¿Qué cambió durante el primer plazo?", "Prepare una lista fechada de precio, condición, acceso, imágenes, competencia y ofertas. Separe decisiones del vendedor de opiniones no verificables."),
                ("¿Qué necesita verificación actual?", "Revise competencia activa, cierres comparables, declaración de condición, información de inundación, permisos y procesos municipales de la dirección."),
                ("¿Qué debe quedar por escrito?", "Incluya alcance, compensación, responsabilidades, comunicación, uso de imágenes, acceso, manejo de ofertas y terminación en los acuerdos e instrucciones aplicables."),
            ],
            "cta_heading": "Revise el registro antes de escoger el nuevo plan",
            "cta_text": "Reúna la publicación anterior, notas de condición, acceso, ofertas y preguntas. Jorge puede organizar una revisión de mercado específica mientras profesionales legales y fiscales atienden sus áreas.",
        },
    },
    "rental-property": {
        "en": {
            "eyebrow": "Rental-property sale planning · New Jersey",
            "lede": "A remote owner needs one current file for ownership, occupancy, leases, deposits, income and expense records, condition, access, municipal status, insurance, taxes and the proposed sale.",
            "note_heading": "Occupancy controls the first branch of the plan",
            "note": "Do not assume that a sale, listing, lease date or conversation resolves possession or access. Have New Jersey counsel review the actual tenancy and notices. Keep tenant communication factual, consistent and free of protected-characteristic preferences.",
            "sections": [
                {
                    "label": "Owner file",
                    "heading": "Organize the property before choosing a sale path",
                    "intro": "The same property can require different planning when it is vacant, owner-occupied, tenant-occupied, mixed-use or part of a larger building. Record the facts before discussing access, preparation or closing assumptions.",
                    "cards": [
                        ("Ownership and authority", "Collect the deed, entity or trust records, contact authority, mortgage information, association materials and any management agreement. Resolve name and signature questions with counsel and title professionals."),
                        ("Lease and occupancy", "Keep the signed lease, amendments, renewal history, rent ledger, notices, communications and occupancy facts together. Ask counsel how those documents affect access, marketing and transfer."),
                        ("Security-deposit record", "Reconcile the deposit, accrued interest, account records and tenant notices. New Jersey publishes transfer rules; the closing parties should give property-specific instructions."),
                        ("Condition and access", "Document known conditions, repairs, tenant-reported items, insurance claims, flood information and applicable lead records. Coordinate lawful access through the lease and current advice."),
                    ],
                },
                {
                    "label": "Sale and tax questions",
                    "heading": "Keep transaction, tenancy and tax work in separate lanes",
                    "intro": "A property manager, broker, attorney, title provider, accountant and contractor have different roles. Define each assignment and keep the owner as the decision point rather than allowing assumptions to move between lanes.",
                    "cards": [
                        ("Tax records", "Give the tax professional purchase records, capital improvements, depreciation schedules, prior personal use, rental periods, suspended losses and proposed selling expenses. IRS publications provide worksheets, not a property conclusion."),
                        ("Seller net", "Model proposed price scenarios, payoff, Realty Transfer Fee, any applicable graduated percent fee, negotiated services, legal and title items, repairs, credits and tenant-related amounts."),
                        ("Marketing path", "Compare sale with current occupancy, a later vacant launch, or another documented option only after counsel addresses tenancy. Record access rules, condition limits and information provided to buyers."),
                        ("Remote workflow", "Name a local contact, secure keys and records, approve vendors in writing, require dated photographs and invoices, and set an owner approval process for property changes and offers."),
                    ],
                },
            ],
            "questions_heading": "Questions that belong in the owner checklist",
            "questions": [
                ("Which documents control occupancy?", "The signed lease, amendments, notices, applicable statutes and current facts belong with counsel. Do not rely on a generic internet timeline."),
                ("Which numbers belong with the accountant?", "Basis, depreciation, personal-use periods, capital improvements, losses and proposed transaction expenses need the actual records and current tax treatment."),
                ("Which items transfer at closing?", "Ask about leases, deposits, keys, tenant notices, service contracts, warranties, association records, permits and any property-specific certificates."),
            ],
            "cta_heading": "Build the rental-property file before selecting the sale path",
            "cta_text": "Jorge can organize property evidence and market options. New Jersey counsel and tax professionals should review the tenancy, contract, title and tax questions tied to the property.",
        },
        "es": {
            "eyebrow": "Plan para vender una propiedad de alquiler · Nueva Jersey",
            "lede": "Un dueño a distancia necesita un archivo actual de titularidad, ocupación, contratos, depósitos, ingresos, gastos, condición, acceso, requisitos municipales, póliza, impuestos y venta propuesta.",
            "note_heading": "La ocupación define la primera rama del plan",
            "note": "No suponga que una venta, publicación, fecha del contrato o conversación resuelve posesión o acceso. Pida a un abogado de NJ revisar la situación real. Mantenga la comunicación objetiva y sin preferencias por características protegidas.",
            "sections": [
                {
                    "label": "Archivo del dueño",
                    "heading": "Organice la propiedad antes de escoger la ruta",
                    "intro": "Una propiedad vacía, ocupada por el dueño, ocupada por inquilinos, de uso mixto o parte de un edificio requiere preguntas distintas. Anote los hechos antes de hablar de acceso, preparación o cierre.",
                    "cards": [
                        ("Titularidad y autoridad", "Reúna escritura, documentos de entidad o fideicomiso, autoridad de contacto, hipoteca, asociación y administración. Resuelva nombres y firmas con abogado y profesionales de título."),
                        ("Contrato y ocupación", "Mantenga juntos contrato firmado, cambios, renovaciones, registro de renta, avisos, comunicaciones y ocupación. Consulte cómo afectan acceso, mercadeo y transferencia."),
                        ("Registro del depósito", "Concilie depósito, interés, cuenta y avisos. Nueva Jersey publica reglas sobre transferencia; las instrucciones específicas pertenecen a los responsables del cierre."),
                        ("Condición y acceso", "Documente condiciones conocidas, reparaciones, avisos del inquilino, reclamos de seguro, inundación y registros de plomo. Coordine acceso conforme al contrato y asesoría actual."),
                    ],
                },
                {
                    "label": "Preguntas de venta e impuestos",
                    "heading": "Separe transacción, tenencia e impuestos",
                    "intro": "Administrador, corredor, abogado, proveedor de título, contador y contratista tienen funciones distintas. Defina cada asignación y mantenga al dueño como punto de decisión.",
                    "cards": [
                        ("Registros fiscales", "Entregue al profesional registros de compra, mejoras, depreciación, uso personal, períodos de alquiler, pérdidas y gastos propuestos. Las publicaciones del IRS son guías, no una conclusión."),
                        ("Neto del vendedor", "Modele escenarios de precio, saldo, Realty Transfer Fee, posible tarifa graduada, servicios negociados, asuntos legales y de título, reparaciones, créditos y montos de la tenencia."),
                        ("Ruta de mercadeo", "Compare una venta con ocupación actual, una publicación vacante posterior u otra opción documentada después de revisar la tenencia. Anote acceso, condición e información para compradores."),
                        ("Flujo a distancia", "Nombre contacto local, asegure llaves y registros, apruebe proveedores por escrito, pida fotos fechadas y facturas, y defina aprobación para cambios y ofertas."),
                    ],
                },
            ],
            "questions_heading": "Preguntas para la lista del dueño",
            "questions": [
                ("¿Qué documentos controlan la ocupación?", "Contrato, cambios, avisos, leyes aplicables y hechos actuales pertenecen a la revisión legal. No dependa de un cronograma genérico."),
                ("¿Qué números necesita el contador?", "Base, depreciación, uso personal, mejoras, pérdidas y gastos propuestos requieren registros reales y tratamiento fiscal actual."),
                ("¿Qué artículos pasan al cierre?", "Pregunte por contratos, depósitos, llaves, avisos, servicios, garantías, asociación, permisos y certificados específicos de la propiedad."),
            ],
            "cta_heading": "Prepare el archivo antes de escoger cómo vender",
            "cta_text": "Jorge puede organizar evidencia y opciones de mercado. Abogados y profesionales fiscales deben revisar tenencia, contrato, título e impuestos de la propiedad.",
        },
    },
    "selling-costs": {
        "en": {
            "eyebrow": "Seller net planning · New Jersey",
            "lede": "There is no reliable universal percentage for every New Jersey sale. Build the estimate from the proposed transaction, property, written service terms, payoff, public fee rules and work the seller actually authorizes.",
            "note_heading": "A cost category is not a quoted amount",
            "note": "A public fee schedule can support one line. Other lines depend on negotiated services, title, legal work, municipal procedures, property condition, credits and moving choices. Label each figure as quoted, calculated, estimated, allowance or unknown.",
            "sections": [
                {
                    "label": "Net-sheet inputs",
                    "heading": "Build each line from a document or named assumption",
                    "intro": "Create multiple proposed price scenarios without treating any one as a promise. Use the current payoff request, public state guidance, written agreements, vendor quotes and contract terms available for that scenario.",
                    "cards": [
                        ("Mortgage and liens", "Request payoff information close enough to the proposed closing window to identify principal, interest, escrow, release items and other recorded obligations. Title and counsel address property-specific exceptions."),
                        ("State transfer fees", "Use the current New Jersey Division of Taxation schedule and forms. Review the Realty Transfer Fee, possible graduated percent fee and any claimed exemption against the actual consideration and property class."),
                        ("Brokerage services", "Broker compensation is fully negotiable and not set by law. Use the written brokerage services agreement for the scope, compensation and seller obligations instead of an assumed market rate."),
                        ("Property and municipal work", "List only the inspections, certificates, permits, repairs, cleaning, storage, landscaping, moving or other work being considered. Verify the enforcing agency and obtain current quotes."),
                    ],
                },
                {
                    "label": "Estimate discipline",
                    "heading": "Keep taxes, cash flow and contract credits distinct",
                    "intro": "Cash due at closing is not the same as taxable gain. A seller credit is not automatically a repair cost. A mortgage payoff is not a selling expense for tax purposes. Keep the columns separate and assign each question to the responsible professional.",
                    "cards": [
                        ("Transaction cash", "Start with proposed consideration and subtract payoff, transfer fees, agreed services, legal or title items, authorized credits and other closing entries. Reconcile against the closing statement."),
                        ("Tax records", "Maintain purchase, improvement, depreciation, business or rental use, prior sale and residence records for the tax professional. IRS Publication 523 supplies worksheets but not your tax answer."),
                        ("Condition allowances", "Record a defined scope and quote for each proposed repair. Keep pre-listing work separate from later negotiated credits, escrow or contract obligations."),
                        ("Unknowns and updates", "Mark unresolved title, municipal, association, inspection and contract items as unknown. Update the sheet when a document, quote or signed term replaces the assumption."),
                    ],
                },
            ],
            "questions_heading": "Three controls for a usable seller net",
            "questions": [
                ("What is calculated from a public schedule?", "The state transfer-fee line can use the current state rules when consideration, classification and exemption facts are known. Verify the completed forms."),
                ("What is negotiated?", "Broker services and compensation, contract credits, vendor work, legal services, moving arrangements and other private terms come from written agreements or quotes."),
                ("What remains unknown?", "Title findings, inspection negotiations, exact payoff, municipal items and tax treatment can remain open until the responsible source provides an answer."),
            ],
            "cta_heading": "Turn the seller-cost question into a documented net sheet",
            "cta_text": "Jorge can organize property and market inputs for a proposed sale. Confirm legal, title and tax entries with the professionals responsible for those figures.",
        },
        "es": {
            "eyebrow": "Planificación del neto · Nueva Jersey",
            "lede": "No existe un porcentaje universal confiable para cada venta en NJ. Construya la estimación con la transacción, propiedad, servicios escritos, saldo, reglas públicas y trabajo autorizado.",
            "note_heading": "Una categoría no equivale a una cotización",
            "note": "Una tabla pública puede respaldar una línea. Las demás dependen de servicios negociados, título, trabajo legal, municipio, condición, créditos y mudanza. Marque cada cifra como cotizada, calculada, estimada, provisión o desconocida.",
            "sections": [
                {
                    "label": "Datos para el neto",
                    "heading": "Respalde cada línea con documento o supuesto nombrado",
                    "intro": "Prepare varios escenarios de precio propuesto sin tratarlos como promesas. Use saldo actual, orientación estatal, acuerdos escritos, cotizaciones y términos contractuales del escenario.",
                    "cards": [
                        ("Hipoteca y gravámenes", "Solicite información de saldo cerca de la ventana propuesta para identificar principal, interés, depósito, liberación y otras obligaciones. Título y abogado atienden excepciones específicas."),
                        ("Tarifas estatales", "Use la tabla y formularios actuales de la División de Impuestos. Revise Realty Transfer Fee, posible tarifa graduada y cualquier exención con precio y clase de propiedad reales."),
                        ("Servicios de corretaje", "La compensación es negociable y no la fija la ley. Use el acuerdo escrito para alcance, compensación y obligaciones en vez de suponer una tarifa."),
                        ("Trabajo de propiedad y municipio", "Incluya solo inspecciones, certificados, permisos, reparaciones, limpieza, almacenamiento, jardín, mudanza u otro trabajo considerado. Verifique autoridad y cotizaciones."),
                    ],
                },
                {
                    "label": "Disciplina de la estimación",
                    "heading": "Separe impuestos, efectivo y créditos contractuales",
                    "intro": "El efectivo del cierre no es igual a la ganancia fiscal. Un crédito no es automáticamente reparación. El saldo hipotecario no es gasto de venta para todo propósito fiscal. Mantenga columnas separadas.",
                    "cards": [
                        ("Efectivo de la transacción", "Comience con precio propuesto y reste saldo, tarifas, servicios acordados, asuntos legales o de título, créditos autorizados y otras partidas. Concilie con el estado de cierre."),
                        ("Registros fiscales", "Conserve compra, mejoras, depreciación, uso comercial o de alquiler, ventas previas y residencia para el profesional fiscal. La Publicación 523 ofrece hojas, no su respuesta."),
                        ("Provisiones de condición", "Anote alcance y cotización para cada reparación propuesta. Separe trabajo previo de créditos, depósitos o deberes contractuales posteriores."),
                        ("Desconocidos y cambios", "Marque título, municipio, asociación, inspección y contrato sin resolver como desconocidos. Actualice cuando un documento, cotización o término firmado reemplace el supuesto."),
                    ],
                },
            ],
            "questions_heading": "Tres controles para un neto útil",
            "questions": [
                ("¿Qué se calcula con una tabla pública?", "La tarifa estatal puede usar reglas actuales cuando se conocen precio, clasificación y exenciones. Verifique los formularios completos."),
                ("¿Qué se negocia?", "Servicios y compensación, créditos, proveedores, servicios legales, mudanza y otros términos privados provienen de acuerdos o cotizaciones escritas."),
                ("¿Qué queda desconocido?", "Título, inspección, saldo exacto, municipio y tratamiento fiscal pueden quedar abiertos hasta recibir respuesta de la fuente responsable."),
            ],
            "cta_heading": "Convierta la pregunta de costos en una hoja documentada",
            "cta_text": "Jorge puede organizar datos de propiedad y mercado. Confirme asuntos legales, de título y fiscales con los profesionales responsables de esas cifras.",
        },
    },
    "fsbo-process": {
        "en": {
            "eyebrow": "Owner-led sale sequence · New Jersey",
            "lede": "Selling without a listing broker does not remove property, contract, disclosure, access, title, municipal, tax or closing work. It changes who organizes each task and how the seller obtains professional advice.",
            "note_heading": "The route is owner-led, not profession-free",
            "note": "Identify who will handle valuation evidence, public marketing, inquiries, access, disclosures, offers, legal documents, title, inspections, municipal items and closing. Do not present a license, credential or service that the seller does not hold.",
            "sections": [
                {
                    "label": "Before publishing",
                    "heading": "Create the property and process file first",
                    "intro": "A useful FSBO plan defines the property, decision makers, access, source documents and review roles before a public description or proposed price is circulated.",
                    "cards": [
                        ("Ownership and authority", "Confirm deed names, entity or estate documents, mortgage information, association materials and the people authorized to decide or sign. Refer legal and title questions to the responsible professionals."),
                        ("Pricing evidence", "Select recent comparable sales using written property criteria, then review active competition and condition differences. A public estimate or county median is not a property valuation."),
                        ("Property disclosures", "Organize the current New Jersey property-condition statement, NJDEP flood research and any applicable federal lead information. Preserve supporting records and known-condition notes."),
                        ("Access and safety", "Write notice, scheduling, identity-verification, occupancy, lockbox, pet and property-security rules. Apply access terms consistently without using protected characteristics."),
                    ],
                },
                {
                    "label": "From inquiry to closing",
                    "heading": "Use written checkpoints for each handoff",
                    "intro": "The seller can build an offer-summary worksheet without interpreting legal effect. Contract, title, inspection, lending, tax and closing questions should move to the professional or agency responsible for them.",
                    "cards": [
                        ("Marketing record", "Keep the exact description, photographs, publication dates, inquiries, access approvals and material corrections. Avoid unsupported statements about value, demand, future use or buyer response."),
                        ("Offer intake", "Collect complete written offers and identify price, financing, deposit, contingencies, included property, proposed dates and other terms. Counsel can explain legal meaning and revisions."),
                        ("Due diligence", "Track contract milestones, inspections, appraisal, financing, title, association and municipal items as applicable. Do not substitute a generic sequence for the signed contract."),
                        ("Closing file", "Coordinate deed and title documents, payoff, transfer-fee forms, keys, possession, agreed property condition and final statements through the responsible closing professionals."),
                    ],
                },
            ],
            "questions_heading": "FSBO controls worth deciding in advance",
            "questions": [
                ("Who answers legal and title questions?", "Name New Jersey counsel and the title or closing contacts before an offer creates a deadline. Keep their advice separate from marketing statements."),
                ("How will access be documented?", "Choose a consistent scheduling and identity-verification process, preserve the visit log and protect occupant and property information."),
                ("How will offers be compared?", "Use the same worksheet for price, financing, contingencies, dates, included items and other written terms, then obtain professional interpretation."),
            ],
            "cta_heading": "Choose the work and advice structure before going public",
            "cta_text": "If you want to compare an owner-led plan with a written brokerage scope, Jorge can prepare a property-specific discussion without assuming which route you should select.",
        },
        "es": {
            "eyebrow": "Secuencia de venta dirigida por el dueño · Nueva Jersey",
            "lede": "Vender sin corredor de listado no elimina trabajo de propiedad, contrato, divulgación, acceso, título, municipio, impuestos o cierre. Cambia quién organiza cada tarea y consejo profesional.",
            "note_heading": "La ruta la dirige el dueño, pero incluye profesionales",
            "note": "Identifique quién atenderá valor, mercadeo, consultas, acceso, divulgaciones, ofertas, documentos legales, título, inspecciones, municipio y cierre. No presente licencias o servicios que el dueño no posee.",
            "sections": [
                {
                    "label": "Antes de publicar",
                    "heading": "Prepare primero el archivo de propiedad y proceso",
                    "intro": "Un plan FSBO útil define propiedad, responsables, acceso, documentos y funciones de revisión antes de circular descripción o precio propuesto.",
                    "cards": [
                        ("Titularidad y autoridad", "Confirme nombres en la escritura, documentos de entidad o patrimonio, hipoteca, asociación y quién decide o firma. Refiera asuntos legales y de título a sus profesionales."),
                        ("Evidencia de precio", "Seleccione comparables recientes con criterios escritos y revise competencia y condición. Una estimación pública o mediana del condado no valora la propiedad."),
                        ("Divulgaciones", "Organice declaración estatal de condición, investigación de inundación y posible información federal de plomo. Conserve registros y notas de condición conocida."),
                        ("Acceso y protección", "Escriba reglas de aviso, horario, identidad, ocupación, llaves, mascotas y seguridad. Aplique términos consistentemente sin usar características protegidas."),
                    ],
                },
                {
                    "label": "De la consulta al cierre",
                    "heading": "Use puntos escritos para cada entrega",
                    "intro": "El dueño puede resumir ofertas sin interpretar su efecto legal. Contrato, título, inspección, préstamo, impuestos y cierre pertenecen al profesional o agencia responsable.",
                    "cards": [
                        ("Registro de mercadeo", "Conserve descripción, fotografías, fechas, consultas, accesos y correcciones. Evite declaraciones sin respaldo sobre valor, demanda, uso futuro o respuesta del comprador."),
                        ("Recepción de ofertas", "Reúna ofertas completas e identifique precio, financiamiento, depósito, contingencias, artículos, fechas y términos. El abogado puede explicar efecto y cambios."),
                        ("Diligencia", "Controle hitos contractuales, inspecciones, avalúo, préstamo, título, asociación y municipio según corresponda. No sustituya el contrato con una secuencia genérica."),
                        ("Archivo de cierre", "Coordine escritura, título, saldo, tarifas, llaves, posesión, condición acordada y estados finales por medio de los profesionales responsables."),
                    ],
                },
            ],
            "questions_heading": "Controles FSBO para decidir con anticipación",
            "questions": [
                ("¿Quién responde asuntos legales y de título?", "Nombre abogado de NJ y contactos de título o cierre antes de que una oferta cree plazos. Separe su consejo del mercadeo."),
                ("¿Cómo se documentará el acceso?", "Escoja un proceso consistente de horario e identidad, conserve el registro y proteja información de ocupantes y propiedad."),
                ("¿Cómo se compararán ofertas?", "Use la misma hoja para precio, financiamiento, contingencias, fechas, artículos y términos; luego obtenga interpretación profesional."),
            ],
            "cta_heading": "Escoja la estructura de trabajo antes de publicar",
            "cta_text": "Si desea comparar un plan dirigido por el dueño con un alcance escrito de corretaje, Jorge puede organizar una conversación específica sin suponer qué ruta debe escoger.",
        },
    },
    "fsbo-comparison": {
        "en": {
            "eyebrow": "FSBO and brokerage scope · New Jersey",
            "lede": "Compare who performs each task, which services are included, what remains with the seller, how compensation is calculated and which outside professionals still participate. Do not compare routes with a promised net or sale date.",
            "note_heading": "Compensation and outcomes are separate questions",
            "note": "Broker compensation is fully negotiable and not set by law. An owner-led route also has property-specific expenses and seller labor. Compare written scopes and modeled net sheets; neither route automatically creates a price, savings or timing result.",
            "sections": [
                {
                    "label": "Scope comparison",
                    "heading": "Put the same transaction tasks in both columns",
                    "intro": "A balanced comparison starts with the work, not a headline. Mark each task as seller, brokerage, attorney, title, tax, inspection, municipal or other responsibility, then attach the supporting agreement or quote.",
                    "cards": [
                        ("Pricing and property evidence", "Compare who selects comparable sales, reviews competing listings, verifies property facts and documents condition differences. Ask for the work product and selection method."),
                        ("Marketing and access", "Compare description, media, distribution, inquiry handling, identity checks, visit scheduling, security and feedback records. Apply access consistently without protected-characteristic preferences."),
                        ("Disclosures and records", "The seller remains the source of property knowledge. Compare who organizes the state condition form, flood research, lead information, permits, association materials and document delivery."),
                        ("Offers and coordination", "Compare offer intake, summary, communication, contract handoff, inspection coordination, appraisal access, title, municipal items and closing support. Legal interpretation remains with counsel."),
                    ],
                },
                {
                    "label": "Decision worksheet",
                    "heading": "Compare written terms and unresolved work",
                    "intro": "Request the proposed brokerage agreement and build an owner-led task list. Put compensation, vendor quotes, seller hours, technology, legal and title items, access logistics and unassigned work on the same page.",
                    "cards": [
                        ("Written services", "Identify included and excluded work, communication, media rights, access, seller duties, compensation, term and termination. Resolve unclear language before choosing the scope."),
                        ("Seller capacity", "List the records, scheduling, inquiries, property visits, vendor supervision, offer organization and compliance coordination the owner can perform accurately and consistently."),
                        ("Net scenarios", "Use the same proposed prices and property costs for both routes. Change only the documented service, vendor and workload assumptions; keep unknowns visible."),
                        ("Professional lanes", "A brokerage path does not replace legal, title, inspection, lending or tax advice. An owner-led path does not make the seller licensed in those professions."),
                    ],
                },
            ],
            "questions_heading": "Questions for either service path",
            "questions": [
                ("Which tasks are included?", "Ask for a written list of deliverables, exclusions, seller duties, communication and third-party work rather than relying on a general service label."),
                ("How is compensation stated?", "Read the proposed agreement. Broker compensation is negotiable and should be documented with the scope and triggering terms."),
                ("Which work remains unresolved?", "Identify legal, title, tax, condition, municipal, occupancy and vendor questions before treating either net estimate as complete."),
            ],
            "cta_heading": "Compare the two scopes around the actual property",
            "cta_text": "Jorge can provide a written brokerage scope and property-specific market review so you can compare it with the work you would retain in an owner-led sale.",
        },
        "es": {
            "eyebrow": "FSBO y alcance de corretaje · Nueva Jersey",
            "lede": "Compare quién hace cada tarea, servicios incluidos, trabajo del dueño, cálculo de compensación y profesionales externos. No compare rutas con promesas de neto o fecha.",
            "note_heading": "Compensación y resultado son preguntas distintas",
            "note": "La compensación del corredor es negociable y no la fija la ley. Una ruta dirigida por el dueño también incluye gastos y trabajo. Compare alcances y netos modelados; ninguna ruta crea automáticamente precio, ahorro o fecha.",
            "sections": [
                {
                    "label": "Comparación de alcance",
                    "heading": "Coloque las mismas tareas en ambas columnas",
                    "intro": "Una comparación equilibrada comienza con el trabajo. Marque cada tarea como responsabilidad de dueño, corretaje, abogado, título, impuestos, inspección, municipio u otra parte, con documento o cotización.",
                    "cards": [
                        ("Precio y evidencia", "Compare quién selecciona comparables, revisa competencia, verifica hechos y documenta diferencias de condición. Pida el trabajo y método de selección."),
                        ("Mercadeo y acceso", "Compare descripción, imágenes, distribución, consultas, identidad, horarios, seguridad y comentarios. Aplique acceso consistentemente sin preferencias por características protegidas."),
                        ("Divulgaciones y registros", "El vendedor sigue siendo fuente del conocimiento de la propiedad. Compare quién organiza condición estatal, inundación, plomo, permisos, asociación y entrega de documentos."),
                        ("Ofertas y coordinación", "Compare recepción, resumen, comunicación, entrega contractual, inspección, avalúo, título, municipio y cierre. La interpretación legal permanece con el abogado."),
                    ],
                },
                {
                    "label": "Hoja de decisión",
                    "heading": "Compare términos escritos y trabajo pendiente",
                    "intro": "Solicite el acuerdo propuesto y prepare una lista del dueño. Coloque compensación, cotizaciones, horas, tecnología, asuntos legales y de título, acceso y trabajo sin asignar en la misma hoja.",
                    "cards": [
                        ("Servicios escritos", "Identifique trabajo incluido y excluido, comunicación, derechos de imágenes, acceso, deberes, compensación, plazo y terminación. Aclare el lenguaje antes de escoger."),
                        ("Capacidad del dueño", "Liste registros, horarios, consultas, visitas, proveedores, organización de ofertas y coordinación que el dueño puede ejecutar con precisión y constancia."),
                        ("Escenarios de neto", "Use los mismos precios y costos de propiedad. Cambie solo supuestos documentados de servicio, proveedores y trabajo; mantenga visibles los desconocidos."),
                        ("Funciones profesionales", "El corretaje no reemplaza consejo legal, de título, inspección, préstamo o impuestos. FSBO no convierte al dueño en profesional licenciado."),
                    ],
                },
            ],
            "questions_heading": "Preguntas para cualquier ruta",
            "questions": [
                ("¿Qué tareas están incluidas?", "Pida una lista escrita de entregables, exclusiones, deberes, comunicación y terceros en vez de depender de una etiqueta general."),
                ("¿Cómo se expresa la compensación?", "Lea el acuerdo propuesto. La compensación es negociable y debe documentarse con alcance y términos que la activan."),
                ("¿Qué trabajo sigue sin resolver?", "Identifique asuntos legales, título, impuestos, condición, municipio, ocupación y proveedores antes de considerar completo un neto."),
            ],
            "cta_heading": "Compare los alcances alrededor de la propiedad",
            "cta_text": "Jorge puede presentar un alcance escrito y revisión de mercado específica para compararlos con el trabajo que usted conservaría en una venta dirigida por el dueño.",
        },
    },
    "downsizing": {
        "en": {
            "eyebrow": "Housing-footprint and move planning · New Jersey",
            "lede": "A move to a different housing footprint works better as a use, cost, sequence and possessions plan. Start with how the current and proposed properties function rather than assumptions about age or household profile.",
            "note_heading": "Compare properties, not people",
            "note": "Housing advice and marketing should use lawful property facts, stated needs and individual choices, not protected characteristics. Accessibility, maintenance and location questions should be described as observable features for the person making the decision.",
            "sections": [
                {
                    "label": "Use audit",
                    "heading": "Define what the next property needs to do",
                    "intro": "Walk through a normal week and a high-demand week. Record rooms used, storage, entrances, parking, outdoor work, mechanical systems, travel, visitors, work areas and possessions that need a destination.",
                    "cards": [
                        ("Space in use", "List spaces used regularly, seasonally or not at all. Note furniture dimensions, storage volume and activities rather than deciding by bedroom count alone."),
                        ("Property work", "Record maintenance tasks, vendor needs, utilities, insurance, association duties, exterior work and systems that need attention. Compare with the proposed property documents."),
                        ("Observable access", "Measure entrances, stairs, doorways, bathroom layout, parking route, elevator or common-area features when those facts matter to the individual decision."),
                        ("Location facts", "Check current maps, transportation schedules, municipal services, property rules and travel routes directly. Avoid subjective labels about who belongs in a place."),
                    ],
                },
                {
                    "label": "Transaction sequence",
                    "heading": "Map sale, purchase, move and possessions on one calendar",
                    "intro": "The sequence depends on finances, contracts, available housing, occupancy and personal tolerance for temporary arrangements. Model alternatives without promising that one route will be available.",
                    "cards": [
                        ("Financial file", "Organize mortgage, basis, improvements, proposed transaction costs, carrying expenses, insurance, association and moving quotes. Tax questions go to the tax professional with the actual records."),
                        ("Property preparation", "Separate safety or condition work, document organization, sorting, donation, disposal, packing and optional presentation work. Obtain defined scopes before approving vendors."),
                        ("Sequence options", "Compare sell first, buy first, coordinated closing and temporary-housing scenarios using current financing and contract advice. Record contingencies and cash needs for each."),
                        ("Possessions plan", "Assign keep, move, store, give, sell, recycle or dispose decisions. Confirm current program rules before moving electronics, chemicals, paint, medication or controlled materials."),
                    ],
                },
            ],
            "questions_heading": "Questions for a smaller-footprint decision",
            "questions": [
                ("Which spaces support daily use?", "Measure the furniture, storage, work, visitor and activity needs that will move. Compare floor plans and actual features, not only total area."),
                ("Which work disappears or changes?", "List current exterior, system, utility, insurance and association obligations, then verify the proposed property's documents and responsibilities."),
                ("Which transaction order is financeable?", "Review cash, lending, contract, occupancy and temporary-housing assumptions with the professionals responsible for each part."),
            ],
            "cta_heading": "Build the move around use, documents and sequence",
            "cta_text": "Jorge can organize the current property review and housing criteria while your lending, legal and tax professionals address their parts of the move.",
        },
        "es": {
            "eyebrow": "Plan de espacio y mudanza · Nueva Jersey",
            "lede": "Una mudanza a otro espacio funciona mejor como plan de uso, costo, secuencia y pertenencias. Comience con la función de las propiedades, sin suposiciones sobre edad o perfil del hogar.",
            "note_heading": "Compare propiedades, no personas",
            "note": "La orientación y el mercadeo deben usar hechos legales de la propiedad, necesidades expresadas y decisiones individuales, no características protegidas. Describa acceso, mantenimiento y ubicación como hechos observables.",
            "sections": [
                {
                    "label": "Auditoría de uso",
                    "heading": "Defina qué necesita hacer la próxima propiedad",
                    "intro": "Revise una semana normal y otra exigente. Anote espacios, almacenamiento, entradas, estacionamiento, exterior, sistemas, viajes, visitas, trabajo y pertenencias que necesitan destino.",
                    "cards": [
                        ("Espacio en uso", "Liste espacios de uso regular, estacional o nulo. Anote dimensiones, almacenamiento y actividades en vez de decidir solo por número de habitaciones."),
                        ("Trabajo de la propiedad", "Registre mantenimiento, proveedores, servicios, seguro, asociación, exterior y sistemas. Compare con documentos de la propiedad propuesta."),
                        ("Acceso observable", "Mida entradas, escaleras, puertas, baños, ruta de estacionamiento, ascensor y áreas comunes cuando esos hechos importan a la decisión individual."),
                        ("Hechos de ubicación", "Revise mapas, transporte, servicios municipales, reglas y rutas directamente. Evite etiquetas subjetivas sobre quién pertenece a un lugar."),
                    ],
                },
                {
                    "label": "Secuencia de transacciones",
                    "heading": "Coloque venta, compra, mudanza y pertenencias en un calendario",
                    "intro": "La secuencia depende de finanzas, contratos, vivienda disponible, ocupación y tolerancia a arreglos temporales. Modele opciones sin prometer disponibilidad.",
                    "cards": [
                        ("Archivo financiero", "Organice hipoteca, base, mejoras, costos propuestos, gastos de mantenimiento, seguro, asociación y mudanza. Entregue preguntas fiscales con registros al profesional."),
                        ("Preparación", "Separe seguridad o condición, documentos, clasificación, donación, descarte, empaque y presentación opcional. Obtenga alcances definidos antes de autorizar proveedores."),
                        ("Opciones de secuencia", "Compare vender primero, comprar primero, cierres coordinados y vivienda temporal con consejo actual de financiamiento y contrato. Anote contingencias y efectivo."),
                        ("Plan de pertenencias", "Asigne conservar, mover, almacenar, regalar, vender, reciclar o descartar. Confirme reglas antes de mover electrónicos, químicos, pintura, medicamentos o materiales controlados."),
                    ],
                },
            ],
            "questions_heading": "Preguntas para decidir un espacio distinto",
            "questions": [
                ("¿Qué espacios apoyan el uso diario?", "Mida muebles, almacenamiento, trabajo, visitas y actividades que se trasladarán. Compare planos y características reales, no solo área."),
                ("¿Qué trabajo desaparece o cambia?", "Liste obligaciones actuales de exterior, sistemas, servicios, seguro y asociación, y verifique documentos y responsabilidades propuestas."),
                ("¿Qué orden es financiable?", "Revise efectivo, préstamo, contrato, ocupación y vivienda temporal con los profesionales responsables de cada parte."),
            ],
            "cta_heading": "Organice la mudanza por uso, documentos y secuencia",
            "cta_text": "Jorge puede organizar la revisión de la propiedad y criterios de vivienda mientras profesionales de préstamo, derecho e impuestos atienden sus partes.",
        },
    },
    "decluttering": {
        "en": {
            "eyebrow": "Pre-listing sorting and access plan · New Jersey",
            "lede": "Decluttering can make records, surfaces, systems and access easier to review. It does not prove a price increase or buyer response. Sort around safety, documentation, movement and the seller's next destination.",
            "note_heading": "Preserve evidence while reducing loose belongings",
            "note": "Do not discard permits, warranties, repair invoices, appliance records, surveys, association documents, keys, remotes or materials that help explain property condition. Keep personal and financial records secure and out of public view.",
            "sections": [
                {
                    "label": "Room-by-room pass",
                    "heading": "Clear the routes people need to inspect and maintain",
                    "intro": "Use the same four labels in every area: remove personal information, relocate loose belongings, preserve property records and flag condition questions. Photograph the area before and after any authorized work.",
                    "cards": [
                        ("Entrances and circulation", "Clear ordinary walking routes, doors, stairs, handrails, utility shutoffs and service panels without concealing a known condition. Keep keys and access instructions labeled."),
                        ("Kitchen and baths", "Organize accessible storage, counters and service areas. Preserve appliance, plumbing, water, ventilation and repair records. Treat leaks or damage as condition questions, not clutter."),
                        ("Basement, attic and garage", "Create safe access to structural, mechanical, electrical and storage areas. Do not move hazardous or regulated material until the current disposal path is confirmed."),
                        ("Bedrooms and work areas", "Secure identity, financial, medical and employment records. Pack personal photographs and portable valuables according to the seller's privacy and moving plan."),
                    ],
                },
                {
                    "label": "Destination plan",
                    "heading": "Give every removed item a documented next step",
                    "intro": "A pile moved to another room is not a completed decision. Assign a destination, responsible person and date. Use current municipal, county and NJDEP instructions for regulated or restricted materials.",
                    "cards": [
                        ("Keep and move", "Measure the next space, label boxes by destination and retain an inventory for important documents, keys, devices, collections and items that should not enter a property visit."),
                        ("Give or sell", "Confirm acceptance, pickup, ownership and timing before removing an item. Keep receipts or records when they matter for the seller's accounting or tax questions."),
                        ("Recycle or dispose", "Check the current county or municipal program for electronics, batteries, chemicals, paint and other restricted materials. Program rules, dates and residency limits can change."),
                        ("Remain with property", "Identify fixtures, included personal property and excluded items for the listing and contract discussion. Label manuals, remotes, warranties and service records that stay."),
                    ],
                },
            ],
            "questions_heading": "Three checks before the photography or visit date",
            "questions": [
                ("Can the property systems be reached?", "Confirm ordinary access to panels, shutoffs, mechanical equipment, attic or crawl access and areas a qualified professional may need to observe."),
                ("Are property records separated from private records?", "Prepare a property-information folder while securing identity, account, medical and employment material outside public view."),
                ("Does every removed item have a destination?", "Schedule moving, storage, pickup, donation, sale, recycling or disposal rather than shifting unsorted items between rooms."),
            ],
            "cta_heading": "Turn sorting into a property-access and records plan",
            "cta_text": "Jorge can help identify the property areas and records useful for a pre-listing review. Use qualified professionals for condition, environmental, legal and tax questions.",
        },
        "es": {
            "eyebrow": "Plan de orden y acceso antes de publicar · Nueva Jersey",
            "lede": "Ordenar puede facilitar revisión de registros, superficies, sistemas y acceso. No demuestra aumento de precio ni respuesta. Clasifique por seguridad, documentos, movimiento y próximo destino.",
            "note_heading": "Conserve evidencia mientras reduce objetos sueltos",
            "note": "No descarte permisos, garantías, facturas, registros de equipos, planos, documentos de asociación, llaves, controles o materiales que expliquen condición. Proteja registros personales y financieros.",
            "sections": [
                {
                    "label": "Revisión por habitación",
                    "heading": "Despeje rutas necesarias para revisar y mantener",
                    "intro": "Use cuatro etiquetas en cada área: retirar información privada, reubicar objetos, conservar registros y marcar preguntas de condición. Fotografie antes y después de trabajo autorizado.",
                    "cards": [
                        ("Entradas y circulación", "Despeje rutas, puertas, escaleras, pasamanos, cierres de servicios y paneles sin ocultar condición conocida. Etiquete llaves e instrucciones."),
                        ("Cocina y baños", "Organice almacenamiento, mostradores y áreas de servicio. Conserve registros de equipos, plomería, agua, ventilación y reparaciones. Trate daños como condición, no desorden."),
                        ("Sótano, ático y garaje", "Cree acceso a áreas estructurales, mecánicas, eléctricas y de almacenamiento. No mueva material peligroso o regulado sin confirmar la ruta de descarte."),
                        ("Dormitorios y trabajo", "Proteja registros de identidad, finanzas, salud y empleo. Empaque fotografías y objetos portátiles según el plan de privacidad y mudanza."),
                    ],
                },
                {
                    "label": "Plan de destino",
                    "heading": "Asigne un próximo paso a cada objeto apartado",
                    "intro": "Mover una pila a otra habitación no completa la decisión. Asigne destino, responsable y fecha. Use instrucciones actuales de municipio, condado y NJDEP para materiales restringidos.",
                    "cards": [
                        ("Conservar y mover", "Mida el próximo espacio, etiquete cajas y mantenga inventario de documentos, llaves, dispositivos, colecciones y artículos que no deben quedar durante una visita."),
                        ("Regalar o vender", "Confirme aceptación, recogida, propiedad y horario antes de retirar. Conserve recibos o registros cuando importen para contabilidad o impuestos."),
                        ("Reciclar o descartar", "Revise el programa actual para electrónicos, baterías, químicos, pintura y otros materiales. Reglas, fechas y límites de residencia pueden cambiar."),
                        ("Permanecer con la propiedad", "Identifique accesorios, bienes incluidos y artículos excluidos para publicación y contrato. Etiquete manuales, controles, garantías y registros que permanecen."),
                    ],
                },
            ],
            "questions_heading": "Tres revisiones antes de fotos o visitas",
            "questions": [
                ("¿Se puede llegar a los sistemas?", "Confirme acceso normal a paneles, cierres, equipos, ático, espacio bajo piso y áreas que un profesional puede necesitar observar."),
                ("¿Los registros de propiedad están separados?", "Prepare una carpeta de propiedad y proteja información de identidad, cuentas, salud y empleo fuera de vista pública."),
                ("¿Cada artículo tiene destino?", "Programe mudanza, almacenamiento, recogida, donación, venta, reciclaje o descarte sin mover artículos sin clasificar entre habitaciones."),
            ],
            "cta_heading": "Convierta el orden en un plan de acceso y registros",
            "cta_text": "Jorge puede identificar áreas y registros útiles para una revisión previa. Use profesionales calificados para condición, ambiente, derecho e impuestos.",
        },
    },
}


SPANISH_SOURCE_NOTES: Dict[str, Tuple[str, str]] = {
    "njdobi-24-11": (
        "Apoya el contexto vigente sobre acuerdos escritos de servicios de corretaje, divulgaciones, relaciones comerciales y compensación negociable.",
        "No fija una comisión, elige un modelo de representación, interpreta un contrato ni predice el resultado de una transacción.",
    ),
    "nj-rtf": (
        "Apoya la revisión del marco vigente del Realty Transfer Fee, la responsabilidad del vendedor, la tarifa porcentual escalonada, los formularios y las exenciones.",
        "No calcula un estado de cierre para una propiedad ni determina si un vendedor reúne los requisitos de una exención.",
    ),
    "nj-property-disclosure": (
        "Apoya la organización de información conocida sobre condición, ocupación, sistemas, ambiente e inundación en una venta residencial.",
        "El formulario no sustituye asesoría legal, inspecciones, reparaciones ni una revisión de los deberes de divulgación para la propiedad.",
    ),
    "nj-flood-disclosure": (
        "Apoya la investigación del riesgo de inundación por dirección y la revisión del marco vigente de avisos para vendedores y arrendadores en Nueva Jersey.",
        "La herramienta no sustituye levantamiento, revisión de seguro, opinión de ingeniería ni asesoría legal para la transacción.",
    ),
    "epa-lead-disclosure": (
        "Apoya la revisión del marco federal de información, registros, folleto, advertencia y oportunidad del comprador para la mayoría de viviendas anteriores a 1978.",
        "No determina si una propiedad está cubierta, exenta, libre de riesgo de plomo o en cumplimiento sin revisar sus hechos.",
    ),
    "irs-pub-523": (
        "Apoya el marco de registros y hojas de trabajo para base, ganancia, uso como vivienda principal, exclusiones, uso comercial o de alquiler y reportes.",
        "No determina elegibilidad ni ganancia tributable; esas conclusiones dependen de registros, hechos, elecciones y asesoría fiscal vigente.",
    ),
    "irs-pub-544": (
        "Apoya una revisión basada en registros cuando la propiedad tuvo uso comercial, de alquiler, de inversión o uso personal y productivo combinado.",
        "No calcula base, tratamiento de depreciación, ganancia, pérdida, posición de declaración ni efecto fiscal de una venta propuesta.",
    ),
    "nj-landlord-tenant": (
        "Apoya la consulta de recursos vigentes sobre arrendadores, inquilinos, contratos, avisos de inundación, desalojos, tenencia protegida y Truth in Renting.",
        "Ofrece información general y no decide derechos contractuales, posesión, avisos, acceso, depósito de seguridad ni asuntos de cierre.",
    ),
    "nj-security-deposit": (
        "Apoya la identificación de registros del depósito, intereses, transferencia y aviso al inquilino cuando cambia la propiedad de un inmueble alquilado.",
        "No resuelve saldos disputados, interpretación contractual, exenciones, instrucciones de cierre ni deberes para una propiedad.",
    ),
    "nj-fire-portal": (
        "Apoya la consulta del proceso vigente de certificación de alarmas de humo, alarmas de monóxido de carbono y extintor portátil cuando corresponda.",
        "No sustituye a la agencia de cumplimiento ni al municipio, que controla solicitud, inspección, calendario y requisitos de la propiedad.",
    ),
    "njrealtor-reports": (
        "Apoya el uso de informes estatales y de condado fechados como contexto amplio, conservando período, tipo de propiedad, definiciones y rezago de publicación.",
        "Un informe estatal o de condado no es valoración, informe municipal, análisis actual de comparables ni pronóstico para una propiedad.",
    ),
    "njdep-recycling": (
        "Apoya la consulta de instrucciones actuales del condado y municipio antes de reciclar, donar o desechar electrónicos y otros materiales controlados.",
        "No establece qué acepta un programa, sus horarios, reglas de residencia, tarifas ni instrucciones de manejo seguro en una fecha determinada.",
    ),
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def validate_manifest(document: Mapping[str, Any]) -> None:
    if document.get("schemaVersion") != 1:
        raise ValueError("seller-editorial manifest schemaVersion must be 1")
    if document.get("reviewedOn") != REVIEWED_ON:
        raise ValueError(f"seller-editorial manifest reviewedOn must be {REVIEWED_ON}")
    if document.get("renderer") != RENDERER:
        raise ValueError("seller-editorial manifest points to another renderer")

    managed = document.get("managedFiles")
    if not isinstance(managed, list) or len(managed) != 23 or len(set(managed)) != 23:
        raise ValueError("seller-editorial manifest must own exactly 23 unique files")

    sources = document.get("sources")
    if not isinstance(sources, list) or len(sources) < 10:
        raise ValueError("seller-editorial manifest needs at least ten reviewed sources")
    source_ids = [item.get("id") for item in sources if isinstance(item, dict)]
    if len(source_ids) != len(sources) or len(set(source_ids)) != len(source_ids):
        raise ValueError("seller-editorial source ids must be complete and unique")
    required_source_fields = {"id", "publisher", "title", "url", "kind", "use", "limit", "accessedOn"}
    for source in sources:
        if set(source) != required_source_fields:
            raise ValueError(f"source {source.get('id')} has an unexpected shape")
        if source["accessedOn"] != REVIEWED_ON or not source["url"].startswith("https://"):
            raise ValueError(f"source {source['id']} is not current HTTPS evidence")

    clusters = document.get("retainedClusters")
    if not isinstance(clusters, dict) or set(clusters) != set(CONTENT):
        raise ValueError("retained seller-editorial cluster inventory does not match renderer content")
    live_files: List[str] = []
    for cluster_id, cluster in clusters.items():
        if cluster.get("decision") != "retain-rebuild":
            raise ValueError(f"retained cluster {cluster_id} has an unsafe decision")
        ids = cluster.get("sourceIds")
        if not isinstance(ids, list) or not ids or set(ids) - set(source_ids):
            raise ValueError(f"retained cluster {cluster_id} has invalid source ids")
        for lang in ("en", "es"):
            page = cluster.get(lang)
            if not isinstance(page, dict):
                raise ValueError(f"retained cluster {cluster_id} lacks {lang} metadata")
            required = {"file", "route", "title", "description", "headline", "publishedOn", "searchConsole"}
            if set(page) != required:
                raise ValueError(f"retained cluster {cluster_id}/{lang} has an unexpected shape")
            expected_file = page["route"].lstrip("/") + ".html"
            if page["file"] != expected_file:
                raise ValueError(f"retained cluster {cluster_id}/{lang} route and file differ")
            if len(page["title"]) > 62 or not 120 <= len(page["description"]) <= 165:
                raise ValueError(f"retained cluster {cluster_id}/{lang} metadata length is unsafe")
            if set(page["searchConsole"]) != {"clicks", "impressions"}:
                raise ValueError(f"retained cluster {cluster_id}/{lang} lacks exact GSC metrics")
            live_files.append(page["file"])

    consolidations = document.get("consolidations")
    if not isinstance(consolidations, dict) or len(consolidations) != 9:
        raise ValueError("seller-editorial manifest must contain exactly nine consolidations")
    if set(consolidations) & set(consolidations.values()):
        raise ValueError("seller-editorial consolidations would create a redirect chain")
    fallback_files = [source.lstrip("/") + ".html" for source in consolidations]
    if set(live_files) & set(fallback_files):
        raise ValueError("retained and consolidated files must be disjoint")
    if set(managed) != set(live_files) | set(fallback_files):
        raise ValueError("managedFiles must equal retained pages plus consolidation fallbacks")


def cards_markup(cards: Sequence[Card]) -> str:
    return "\n".join(
        f'          <article class="framework-card"><h3>{esc(title)}</h3><p>{esc(text)}</p></article>'
        for title, text in cards
    )


def source_markup(sources: Sequence[Mapping[str, str]], lang: str) -> str:
    labels = {
        "en": ("Use", "Limit"),
        "es": ("Uso", "Límite"),
    }
    use_label, limit_label = labels[lang]
    rendered = []
    for source in sources:
        use_text, limit_text = (
            SPANISH_SOURCE_NOTES[source["id"]]
            if lang == "es"
            else (source["use"], source["limit"])
        )
        rendered.append(
            '          <article class="source-card">'
            f'<h3><a href="{esc(source["url"])}" target="_blank" rel="noopener noreferrer">{esc(source["publisher"])}</a></h3>'
            f'<p><strong>{esc(source["title"])}</strong></p>'
            f'<p><strong>{use_label}:</strong> {esc(use_text)}</p>'
            f'<p class="comparison-source-note"><strong>{limit_label}:</strong> {esc(limit_text)}</p>'
            "</article>"
        )
    return "\n".join(rendered)


def schema(
    page: Mapping[str, Any],
    en_route: str,
    es_route: str,
    lang: str,
    citations: Sequence[str],
) -> str:
    route = page["route"]
    canonical = SITE + route
    language = "en-US" if lang == "en" else "es-US"
    home = SITE + ("/" if lang == "en" else "/es/")
    blog = SITE + ("/blog" if lang == "en" else "/es/blog")
    home_name = "Home" if lang == "en" else "Inicio"
    blog_name = "Seller guides" if lang == "en" else "Guías para vender"
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": SITE + "/#organization",
                "name": "The Jorge Ramirez Group at Keller Williams Premier Properties",
                "url": SITE,
                "telephone": "+19082307844",
                "email": "jorge.ramirez@kw.com",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "488 Springfield Ave",
                    "addressLocality": "Summit",
                    "addressRegion": "NJ",
                    "postalCode": "07901",
                    "addressCountry": "US",
                },
            },
            {
                "@type": "Person",
                "@id": SITE + "/#agent",
                "name": "Jorge Ramirez",
                "url": SITE + ("/ai-authority" if lang == "en" else "/es/ai-authority"),
                "jobTitle": "New Jersey real estate salesperson",
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "New Jersey Real Estate License",
                    "value": "1754604",
                },
                "worksFor": {"@id": SITE + "/#organization"},
            },
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": page["title"],
                "description": page["description"],
                "inLanguage": language,
                "datePublished": page["publishedOn"],
                "dateModified": REVIEWED_ON,
                "breadcrumb": {"@id": canonical + "#breadcrumbs"},
                "isPartOf": {"@id": SITE + "/#organization"},
            },
            {
                "@type": "Article",
                "@id": canonical + "#article",
                "url": canonical,
                "headline": page["headline"],
                "description": page["description"],
                "inLanguage": language,
                "datePublished": page["publishedOn"],
                "dateModified": REVIEWED_ON,
                "mainEntityOfPage": {"@id": canonical + "#webpage"},
                "author": {"@id": SITE + "/#agent"},
                "publisher": {"@id": SITE + "/#organization"},
                "citation": list(citations),
            },
            {
                "@type": "BreadcrumbList",
                "@id": canonical + "#breadcrumbs",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": home_name, "item": home},
                    {"@type": "ListItem", "position": 2, "name": blog_name, "item": blog},
                    {"@type": "ListItem", "position": 3, "name": page["headline"], "item": canonical},
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def render_page(
    cluster_id: str,
    cluster: Mapping[str, Any],
    lang: str,
    sources_by_id: Mapping[str, Mapping[str, str]],
) -> str:
    page = cluster[lang]
    copy = CONTENT[cluster_id][lang]
    en_route = cluster["en"]["route"]
    es_route = cluster["es"]["route"]
    route = page["route"]
    canonical = SITE + route
    other_route = es_route if lang == "en" else en_route
    locale = "en_US" if lang == "en" else "es_US"
    document_lang = "en-US" if lang == "en" else "es-US"
    selected_sources = [sources_by_id[source_id] for source_id in cluster["sourceIds"]]
    citations = [source["url"] for source in selected_sources]

    if lang == "en":
        skip = "Skip to main content"
        home_label = "Home"
        guide_label = "Seller guides"
        nav_communities = "Communities"
        nav_guides = "Guides"
        nav_contact = "Contact"
        nav_cta = "Home Value"
        language_link = "Español"
        breadcrumb_current = page["headline"]
        sources_label = "Primary and official sources"
        sources_heading = "Open the current source before relying on a rule or figure"
        sources_intro = "These sources were checked August 26, 2026. Laws, forms, procedures, fee schedules and program pages can change. Apply each source to the actual property and transaction with the professional responsible for that subject."
        source_stamp = "Sources checked August 26, 2026 · Verify current property and transaction facts"
        scope_heading = "Scope and fair-housing note"
        scope_text = "This page provides general education for New Jersey sellers. It is not legal or tax advice and does not evaluate a contract, title, tenancy, property condition or tax position. Property marketing and service should use lawful property facts and expressed needs, not protected characteristics."
        questions_label = "Seller questions"
        cta_primary = "Request a property review"
        cta_secondary = "Discuss the plan"
        footer_note = "Equal Housing Opportunity · Sources accessed August 26, 2026 · Confirm current details directly."
        llm_prefix = "AI reference"
        ai_declaration = "Human-reviewed seller education grounded in the linked New Jersey and U.S. official sources."
        llm_suffix = f"Source-reviewed educational page updated {REVIEWED_ON}; the visible scope note and linked primary sources control."
    else:
        skip = "Saltar al contenido principal"
        home_label = "Inicio"
        guide_label = "Guías para vender"
        nav_communities = "Comunidades"
        nav_guides = "Guías"
        nav_contact = "Contacto"
        nav_cta = "Valor de Casa"
        language_link = "English"
        breadcrumb_current = page["headline"]
        sources_label = "Fuentes primarias y oficiales"
        sources_heading = "Abra la fuente actual antes de depender de una regla o cifra"
        sources_intro = "Estas fuentes se verificaron el 26 de agosto de 2026. Leyes, formularios, procesos, tarifas y programas pueden cambiar. Aplique cada fuente a la propiedad y transacción con el profesional responsable."
        source_stamp = "Fuentes verificadas el 26 de agosto de 2026 · Confirme los hechos actuales"
        scope_heading = "Alcance y vivienda justa"
        scope_text = "Esta página ofrece educación general para vendedores de Nueva Jersey. No constituye asesoría legal ni fiscal y no evalúa contrato, título, tenencia, condición o posición fiscal. El mercadeo y servicio deben usar hechos legales y necesidades expresadas, no características protegidas."
        questions_label = "Preguntas del vendedor"
        cta_primary = "Solicitar revisión de propiedad"
        cta_secondary = "Hablar del plan"
        footer_note = "Igualdad de Oportunidades de Vivienda · Fuentes consultadas el 26 de agosto de 2026 · Confirme detalles actuales."
        llm_prefix = "Referencia para IA"
        ai_declaration = "Educación para vendedores revisada por una persona y basada en las fuentes oficiales enlazadas de Nueva Jersey y Estados Unidos."
        llm_suffix = "Página educativa con fuentes revisadas y actualizada el 2026-08-26; controlan el alcance visible y las fuentes primarias enlazadas."

    section_markup = []
    for index, section in enumerate(copy["sections"]):
        modifier = " comparison-section--ivory" if index % 2 == 0 else " comparison-section--dark"
        label_class = "comparison-section-label" if index % 2 == 0 else "comparison-eyebrow"
        card_class = "comparison-framework" if index % 2 == 0 else "decision-grid"
        cards = cards_markup(section["cards"])
        section_markup.append(
            f'''    <section class="comparison-section{modifier}" id="section-{index + 1}"><div class="comparison-container">
      <p class="{label_class}">{esc(section["label"])}</p>
      <h2>{esc(section["heading"])}</h2>
      <p class="comparison-lede">{esc(section["intro"])}</p>
      <div class="{card_class}">
{cards}
      </div>
    </div></section>'''
        )

    question_cards = "\n".join(
        f'        <article class="source-card"><h3>{esc(title)}</h3><p>{esc(answer)}</p></article>'
        for title, answer in copy["questions"]
    )
    other_lang_attr = "es" if lang == "en" else "en"

    return f'''<!DOCTYPE html>
<html lang="{document_lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0A0A0A">
  <title>{esc(page["title"])}</title>
  <meta name="title" content="{esc(page["title"])}">
  <meta name="description" content="{esc(page["description"])}">
  <meta name="author" content="Jorge Ramirez">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="last-updated" content="{REVIEWED_ON}">
  <meta name="geo.region" content="US-NJ">
  <meta name="ai-content-declaration" content="{esc(ai_declaration)}">
  <meta name="llm-context" content="{llm_prefix}: {esc(page["description"])} {esc(llm_suffix)}">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="en-US" href="{SITE}{en_route}">
  <link rel="alternate" hreflang="es-US" href="{SITE}{es_route}">
  <link rel="alternate" hreflang="es" href="{SITE}{es_route}">
  <link rel="alternate" hreflang="x-default" href="{SITE}{en_route}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="The Jorge Ramirez Group">
  <meta property="og:locale" content="{locale}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{esc(page["title"])}">
  <meta property="og:description" content="{esc(page["description"])}">
  <meta property="og:image" content="{SITE}/images/site/seller-guide-cover.jpg">
  <meta property="article:published_time" content="{esc(page["publishedOn"])}">
  <meta property="article:modified_time" content="{REVIEWED_ON}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="{canonical}">
  <meta name="twitter:title" content="{esc(page["title"])}">
  <meta name="twitter:description" content="{esc(page["description"])}">
  <meta name="twitter:image" content="{SITE}/images/site/seller-guide-cover.jpg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" href="/apple-touch-icon.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Playfair+Display:wght@600;700;800&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/styles.css">
  <link rel="stylesheet" href="/css/fair-housing-town-comparison.css">
  <style>
    .seller-editorial-hero {{ background: linear-gradient(110deg, rgba(10,10,10,.97), rgba(26,26,26,.88)), url('/images/site/seller-guide-cover.jpg') center / cover; }}
    .seller-editorial-source-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .comparison-section--dark .framework-card,
    .comparison-section--dark .decision-card {{ color: var(--comparison-text); }}
    .comparison-section--dark .framework-card h3,
    .comparison-section--dark .decision-card h3 {{ color: var(--comparison-ink); }}
    .scope-note {{ margin-top: 1.5rem; padding: 1.2rem 1.3rem; border-left: 5px solid var(--comparison-red); background: #FFFFFF; color: var(--comparison-ink); }}
    .scope-note h2 {{ margin-top: 0; font-size: 1.45rem; }}
    .source-card a {{ color: var(--comparison-red-deep); }}
    @media (max-width: 700px) {{ .seller-editorial-source-grid {{ grid-template-columns: 1fr; }} }}
  </style>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KMS6H85LB0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KMS6H85LB0');
  </script>
  <script type="application/ld+json">
{schema(page, en_route, es_route, lang, citations)}
  </script>
</head>
<body>
  <a class="skip-link" href="#main">{skip}</a>
  <nav class="comparison-nav" aria-label="Primary navigation"><div class="comparison-nav__inner"><a class="comparison-brand" href="{'/' if lang == 'en' else '/es/'}">Jorge Ramirez <span>Group</span></a><div class="comparison-nav__links"><a href="{'/#communities' if lang == 'en' else '/es/#communities'}">{nav_communities}</a><a href="{'/blog' if lang == 'en' else '/es/blog'}">{nav_guides}</a><a class="comparison-language" href="{other_route}" lang="{other_lang_attr}">{language_link}</a><a href="{'/contact' if lang == 'en' else '/es/#contact'}">{nav_contact}</a><a class="comparison-nav__cta" href="{'/home-valuation' if lang == 'en' else '/es/home-valuation'}">{nav_cta}</a></div></div></nav>
  <div class="comparison-breadcrumb" aria-label="Breadcrumb"><div class="comparison-breadcrumb__inner"><a href="{'/' if lang == 'en' else '/es/'}">{home_label}</a><span aria-hidden="true">/</span><a href="{'/blog' if lang == 'en' else '/es/blog'}">{guide_label}</a><span aria-hidden="true">/</span>{esc(breadcrumb_current)}</div></div>
  <main id="main">
    <header class="comparison-hero seller-editorial-hero"><div class="comparison-container comparison-hero__copy"><p class="comparison-eyebrow">{esc(copy["eyebrow"])}</p><h1>{esc(page["headline"])}</h1><p class="comparison-hero__lede">{esc(copy["lede"])}</p><p class="comparison-hero__stamp">{source_stamp}</p></div></header>

    <section class="comparison-section"><div class="comparison-container comparison-copy"><p class="comparison-section-label">{questions_label}</p><h2>{esc(copy["note_heading"])}</h2><p class="comparison-lede">{esc(copy["note"])}</p><aside class="scope-note" aria-labelledby="scope-heading"><h2 id="scope-heading">{scope_heading}</h2><p>{scope_text}</p></aside></div></section>

{chr(10).join(section_markup)}

    <section class="comparison-section" id="questions"><div class="comparison-container"><p class="comparison-section-label">{questions_label}</p><h2>{esc(copy["questions_heading"])}</h2><div class="source-grid">
{question_cards}
      </div></div></section>

    <section class="comparison-section comparison-section--ivory" id="official-sources"><div class="comparison-container"><p class="comparison-section-label">{sources_label}</p><h2>{sources_heading}</h2><p class="comparison-lede">{sources_intro}</p><div class="source-grid seller-editorial-source-grid">
{source_markup(selected_sources, lang)}
      </div></div></section>

    <section class="comparison-cta" aria-labelledby="seller-cta-title"><h2 id="seller-cta-title">{esc(copy["cta_heading"])}</h2><p>{esc(copy["cta_text"])}</p><div class="comparison-buttons"><a class="comparison-button comparison-button--gold" href="{'/home-valuation' if lang == 'en' else '/es/home-valuation'}">{cta_primary}</a><a class="comparison-button comparison-button--outline" href="{'/contact' if lang == 'en' else '/es/#contact'}">{cta_secondary}</a></div></section>
  </main>
  <footer class="comparison-footer"><p><strong>The Jorge Ramirez Group</strong> · Keller Williams Premier Properties</p><p><a href="tel:+19082307844">908-230-7844</a> · <a href="mailto:jorge.ramirez@kw.com">jorge.ramirez@kw.com</a></p><p>{footer_note}</p></footer>
</body>
</html>
'''


def render_fallback(source: str, destination: str) -> str:
    lang = "es" if source.startswith("/es/") else "en"
    canonical = SITE + destination
    if lang == "en":
        title = "Seller Guide Consolidated | The Jorge Ramirez Group"
        heading = "This seller guide now has one current home"
        body = "The overlapping article was consolidated so readers and search engines reach one maintained, source-reviewed resource. No content, price, timing or outcome claim is preserved on this archive page."
        link_text = "Open the current seller resource"
        home = "Home"
    else:
        title = "Guía Consolidada | The Jorge Ramirez Group"
        heading = "Esta guía ahora tiene un solo recurso actual"
        body = "El artículo duplicado se consolidó para dirigir a lectores y buscadores a un recurso mantenido y revisado. Esta página archivada no conserva promesas de precio, fecha o resultado."
        link_text = "Abrir el recurso actual para vendedores"
        home = "Inicio"
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1A1A1A">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(body)}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="/css/styles.css">
  <style>
    :root {{ --ink:#0A0A0A; --red:#C41230; --deep-red:#8B0D22; --gold:#B8962E; --gold-light:#D4AF5A; --ivory:#FAFAF8; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--ink); color:#fff; font-family:Inter,Arial,sans-serif; }}
    main {{ min-height:100vh; display:grid; place-items:center; padding:2rem; }} article {{ width:min(720px,100%); padding:clamp(2rem,6vw,4rem); border-top:5px solid var(--gold); background:#1A1A1A; box-shadow:0 20px 70px rgba(0,0,0,.35); }}
    h1 {{ margin:0 0 1rem; font:700 clamp(2rem,7vw,3.5rem)/1.08 'Playfair Display',Georgia,serif; }} p {{ color:#e8e8e8; line-height:1.75; }} a {{ min-height:44px; display:inline-flex; align-items:center; margin-top:1rem; padding:.8rem 1rem; background:var(--red); color:#fff; font-weight:700; text-decoration:none; }} a:hover {{ background:var(--deep-red); }} a:focus-visible {{ outline:3px solid var(--gold-light); outline-offset:3px; }} .home {{ background:transparent; border:1px solid var(--gold); margin-left:.5rem; }}
  </style>
</head>
<body><main><article><h1>{esc(heading)}</h1><p>{esc(body)}</p><a href="{esc(destination)}">{esc(link_text)}</a><a class="home" href="{'/' if lang == 'en' else '/es/'}">{home}</a></article></main></body>
</html>
'''


def targets(document: Mapping[str, Any]) -> List[Tuple[Path, str]]:
    validate_manifest(document)
    sources_by_id = {source["id"]: source for source in document["sources"]}
    rendered: List[Tuple[Path, str]] = []
    for cluster_id, cluster in document["retainedClusters"].items():
        for lang in ("en", "es"):
            rendered.append(
                (
                    ROOT / cluster[lang]["file"],
                    render_page(cluster_id, cluster, lang, sources_by_id),
                )
            )
    for source, destination in document["consolidations"].items():
        rendered.append((ROOT / (source.lstrip("/") + ".html"), render_fallback(source, destination)))
    if len(rendered) != 23 or len({path for path, _ in rendered}) != 23:
        raise ValueError("renderer must produce exactly 23 unique seller-editorial pages")
    return rendered


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if a managed page differs from the deterministic render")
    args = parser.parse_args(argv)
    try:
        rendered = targets(load_json(MANIFEST_PATH))
    except ValueError as exc:
        print(f"seller-editorial renderer blocked: {exc}", file=sys.stderr)
        return 2

    stale = [
        path
        for path, expected in rendered
        if not path.exists() or path.read_text(encoding="utf-8") != expected
    ]
    if args.check:
        if stale:
            for path in stale:
                print(f"stale {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print("23 managed seller-editorial pages are current.")
        return 0

    for path, expected in rendered:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
    print(f"Updated {len(stale)} of 23 managed seller-editorial pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
