#!/usr/bin/env python3
"""Build the source-led NJ Home Seller Planning Guide PDF deterministically."""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "guides" / "nj-home-seller-guide.pdf"
REVIEW_DATE = "August 27, 2026"
PAGE_COUNT = 11

INK_HEX = "#1A1A1A"
DEEP_RED_HEX = "#C41230"
GOLD_HEX = "#B8962E"
IVORY_HEX = "#FAFAF8"
INK = colors.HexColor(INK_HEX)
DEEP_RED = colors.HexColor(DEEP_RED_HEX)
GOLD = colors.HexColor(GOLD_HEX)
IVORY = colors.HexColor(IVORY_HEX)
MUTED = colors.HexColor("#5D5A54")
LINE = colors.HexColor("#DED7C8")
WHITE = colors.white

FONT_DIR = ROOT / "tools" / "pdf-assets"
LOGO = ROOT / "images" / "jorge-logo.jpg"

PAGE_HEADERS = {
    2: "How to use this guide",
    3: "Build the evidence file",
    4: "Condition and disclosures",
    5: "Listing services and compensation",
    6: "Marketing and showing plan",
    7: "Offer comparison worksheet",
    8: "Estimated net proceeds",
    9: "Contract-to-closing file",
    10: "Master seller checklist",
    11: "Primary sources and contact",
}


def register_fonts() -> None:
    fonts = {
        "Inter": "Inter-Regular.ttf",
        "Inter-SemiBold": "Inter-SemiBold.ttf",
        "Playfair-SemiBold": "PlayfairDisplay-SemiBold.ttf",
        "Playfair-Bold": "PlayfairDisplay-Bold.ttf",
    }
    for name, filename in fonts.items():
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))


class DeterministicCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        kwargs["invariant"] = 1
        kwargs["pageCompression"] = 1
        super().__init__(*args, **kwargs)


def set_metadata(pdf: canvas.Canvas) -> None:
    pdf.setTitle("NJ Home Seller Planning Guide")
    pdf.setAuthor("The Jorge Ramirez Group")
    pdf.setSubject(
        "Source-led New Jersey home seller planning guide with evidence, disclosure, "
        "offer-comparison, and net-proceeds worksheets"
    )
    pdf.setCreator("The Jorge Ramirez Group deterministic PDF generator")


def draw_cover(pdf: canvas.Canvas, doc: BaseDocTemplate) -> None:
    del doc
    set_metadata(pdf)
    width, height = letter
    pdf.saveState()
    pdf.setFillColor(INK)
    pdf.rect(0, 0, width, height, stroke=0, fill=1)
    pdf.setFillColor(DEEP_RED)
    pdf.rect(0, 0, 18, height, stroke=0, fill=1)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(2)
    pdf.line(48, height - 42, width - 48, height - 42)
    pdf.line(48, 70, width - 48, 70)

    pdf.setFillColor(IVORY)
    pdf.roundRect(54, 596, 292, 124, 8, stroke=0, fill=1)
    pdf.drawImage(
        str(LOGO),
        68,
        615,
        width=264,
        height=92,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )

    pdf.setFont("Inter-SemiBold", 8)
    pdf.setFillColor(GOLD)
    pdf.drawString(54, 88, "SOURCE-LED EDITION | REVIEWED AUGUST 27, 2026")
    pdf.setFont("Inter", 8.3)
    pdf.setFillColor(colors.HexColor("#E9E4D9"))
    pdf.drawString(54, 49, "908-230-7844  |  jorge.ramirez@kw.com  |  thejorgeramirezgroup.com")
    pdf.restoreState()


def draw_content_background(pdf: canvas.Canvas, doc: BaseDocTemplate) -> None:
    """Paint the page field before flowables without occupying their frame."""

    del doc
    set_metadata(pdf)
    width, height = letter
    pdf.saveState()
    pdf.setFillColor(IVORY)
    pdf.rect(0, 0, width, height, stroke=0, fill=1)
    pdf.setFillColor(DEEP_RED)
    pdf.rect(0, 0, 8, height, stroke=0, fill=1)
    pdf.restoreState()


def draw_content_furniture(pdf: canvas.Canvas, doc: BaseDocTemplate) -> None:
    """Paint invariant running furniture after flowables so it cannot be covered."""

    page = doc.page
    width, height = letter
    pdf.saveState()
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1)
    pdf.line(46, height - 35, width - 46, height - 35)
    pdf.setFont("Inter-SemiBold", 7.5)
    pdf.setFillColor(INK)
    pdf.drawString(46, height - 26, "THE JORGE RAMIREZ GROUP")
    pdf.setFont("Inter", 7.5)
    pdf.setFillColor(MUTED)
    pdf.drawRightString(width - 46, height - 26, PAGE_HEADERS.get(page, "NJ HOME SELLER PLANNING GUIDE"))

    pdf.setStrokeColor(LINE)
    pdf.line(46, 36, width - 46, 36)
    pdf.setFont("Inter", 7.3)
    pdf.setFillColor(MUTED)
    pdf.drawString(46, 23, "908-230-7844  |  thejorgeramirezgroup.com")
    pdf.drawRightString(width - 46, 23, f"PAGE {page} OF {PAGE_COUNT}")
    pdf.bookmarkPage(f"page-{page}")
    pdf.addOutlineEntry(PAGE_HEADERS.get(page, f"Page {page}"), f"page-{page}", level=0)
    pdf.restoreState()


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=base["Normal"],
            fontName="Inter-SemiBold",
            fontSize=8.5,
            leading=11,
            textColor=GOLD,
            spaceAfter=12,
            uppercase=True,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontName="Playfair-Bold",
            fontSize=34,
            leading=38,
            textColor=WHITE,
            alignment=TA_LEFT,
            spaceAfter=16,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=base["Normal"],
            fontName="Inter",
            fontSize=12,
            leading=18,
            textColor=colors.HexColor("#EEE9DD"),
            spaceAfter=24,
        ),
        "cover_identity": ParagraphStyle(
            "cover_identity",
            parent=base["Normal"],
            fontName="Inter-SemiBold",
            fontSize=9.5,
            leading=14,
            textColor=WHITE,
        ),
        "kicker": ParagraphStyle(
            "kicker",
            parent=base["Normal"],
            fontName="Inter-SemiBold",
            fontSize=7.8,
            leading=10,
            textColor=GOLD,
            spaceAfter=7,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Playfair-Bold",
            fontSize=23,
            leading=27,
            textColor=INK,
            spaceAfter=13,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Playfair-SemiBold",
            fontSize=14.5,
            leading=18,
            textColor=DEEP_RED,
            spaceBefore=13,
            spaceAfter=7,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontName="Inter-SemiBold",
            fontSize=9.4,
            leading=12,
            textColor=INK,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Inter",
            fontSize=9.25,
            leading=13.4,
            textColor=colors.HexColor("#2E2D2A"),
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName="Inter",
            fontSize=7.2,
            leading=10.1,
            textColor=MUTED,
            spaceAfter=4,
        ),
        "table": ParagraphStyle(
            "table",
            parent=base["BodyText"],
            fontName="Inter",
            fontSize=7.7,
            leading=10.4,
            textColor=colors.HexColor("#2E2D2A"),
        ),
        "table_head": ParagraphStyle(
            "table_head",
            parent=base["BodyText"],
            fontName="Inter-SemiBold",
            fontSize=7.4,
            leading=9.4,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "callout": ParagraphStyle(
            "callout",
            parent=base["BodyText"],
            fontName="Inter",
            fontSize=9.2,
            leading=13.3,
            textColor=INK,
        ),
        "source": ParagraphStyle(
            "source",
            parent=base["BodyText"],
            fontName="Inter",
            fontSize=7.4,
            leading=10.5,
            textColor=colors.HexColor("#2E2D2A"),
            spaceAfter=3,
        ),
        "cta_title": ParagraphStyle(
            "cta_title",
            parent=base["Heading2"],
            fontName="Playfair-Bold",
            fontSize=18,
            leading=22,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=7,
        ),
        "cta_body": ParagraphStyle(
            "cta_body",
            parent=base["BodyText"],
            fontName="Inter",
            fontSize=9.2,
            leading=13,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
    }


def P(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def page_intro(st: dict[str, ParagraphStyle], kicker: str, title: str, text: str):
    return [
        P(kicker.upper(), st["kicker"]),
        P(title, st["h1"]),
        Table(
            [[P(text, st["callout"])]],
            colWidths=[7.08 * inch],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2EDE2")),
                    ("BOX", (0, 0), (-1, -1), 0.75, GOLD),
                    ("LINEBEFORE", (0, 0), (0, -1), 4, DEEP_RED),
                    ("LEFTPADDING", (0, 0), (-1, -1), 13),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 13),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            ),
        ),
        Spacer(1, 8),
    ]


def bullets(items: list[str], st: dict[str, ParagraphStyle]) -> ListFlowable:
    return ListFlowable(
        [ListItem(P(item, st["body"]), leftIndent=9) for item in items],
        bulletType="bullet",
        bulletFontName="Inter-SemiBold",
        bulletFontSize=7,
        bulletColor=DEEP_RED,
        leftIndent=18,
        bulletIndent=4,
        spaceAfter=5,
    )


def two_column_cards(cards: list[tuple[str, str]], st: dict[str, ParagraphStyle]) -> Table:
    cells = []
    for title, body in cards:
        cells.append([P(title, st["h3"]), P(body, st["small"])])
    rows = []
    for index in range(0, len(cells), 2):
        row = []
        for cell in cells[index : index + 2]:
            row.append(cell)
        while len(row) < 2:
            row.append("")
        rows.append(row)
    return Table(
        rows,
        colWidths=[3.46 * inch, 3.46 * inch],
        hAlign="LEFT",
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        ),
    )


def worksheet_table(
    rows: list[list[str]],
    widths: list[float],
    st: dict[str, ParagraphStyle],
    header: bool = True,
) -> Table:
    data = []
    for row_index, row in enumerate(rows):
        style = st["table_head"] if header and row_index == 0 else st["table"]
        data.append([P(value, style) for value in row])
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.55, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 1 if header else 0), (-1, -1), WHITE),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), INK))
    return Table(data, colWidths=widths, repeatRows=1 if header else 0, style=TableStyle(commands))


def heading_block(st: dict[str, ParagraphStyle], title: str, body: str):
    return KeepTogether([P(title, st["h2"]), P(body, st["body"])])


def source_link(label: str, url: str, note: str, st: dict[str, ParagraphStyle]) -> Paragraph:
    return P(
        f'<b>{label}</b><br/><link href="{url}" color="#8A6D14"><u>{url}</u></link><br/>{note}',
        st["source"],
    )


def build_story(st: dict[str, ParagraphStyle]):
    story = [
        Spacer(1, 186),
        P("NEW JERSEY SELLER RESOURCE", st["cover_kicker"]),
        P("NJ Home Seller<br/>Planning Guide", st["cover_title"]),
        P(
            "An evidence-first workbook for pricing research, property records, disclosures, "
            "brokerage services, offer comparison, estimated net proceeds, and the signed "
            "transaction file.",
            st["cover_sub"],
        ),
        P(
            "Jorge Ramirez | NJ real estate salesperson #1754604<br/>"
            "Full-time Realtor with Keller Williams Premier Properties since 2017.",
            st["cover_identity"],
        ),
        NextPageTemplate("content"),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "01 | Start here",
        "Use This Guide as a Planning File",
        "This guide organizes questions and documents. It does not predict a sale price, "
        "buyer response, closing date, cost, tax result, or net proceeds. Replace every "
        "estimate with current property-specific records, written agreements, signed documents, "
        "and advice from the professional responsible for that subject.",
    )
    story += [
        P("Keep facts, estimates, and decisions separate", st["h2"]),
        two_column_cards(
            [
                ("Verified fact", "A current source or signed document tied to the property, party, and date."),
                ("Planning estimate", "A working figure that must be replaced when a written quote or final document arrives."),
                ("Seller decision", "A choice about preparation, access, price strategy, terms, or timing documented by the seller."),
                ("Specialist conclusion", "Legal, tax, appraisal, inspection, engineering, title, insurance, or municipal advice from the qualified source."),
            ],
            st,
        ),
        P("Who answers which question?", st["h2"]),
        worksheet_table(
            [
                ["Topic", "Start with", "Escalate to"],
                ["Property and market evidence", "Current comparable sales, competition, listing terms", "Appraiser for an appraisal conclusion"],
                ["Contract, title, deed, disclosures", "Signed forms and transaction records", "New Jersey attorney or responsible legal professional"],
                ["Taxes and estimated payments", "NJ Division of Taxation forms and instructions", "Qualified tax adviser"],
                ["Condition and systems", "Seller records and current disclosure form", "Inspector, engineer, environmental or trade professional"],
            ],
            [1.65 * inch, 2.68 * inch, 2.75 * inch],
            st,
        ),
        Spacer(1, 6),
        P(
            f"Source status: official materials and links were reviewed on {REVIEW_DATE}. Rules, "
            "forms, fees, and agency guidance can change. Confirm the current version before use.",
            st["small"],
        ),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "02 | Before pricing",
        "Build the Property and Market Evidence File",
        "A broker price opinion or comparative market analysis is a marketing estimate based on "
        "available evidence. It is not an appraisal by a New Jersey licensed or certified appraiser. "
        "Record the data date, property differences, and limits before selecting a list-price strategy.",
    )
    story += [
        P("Seller priorities worksheet", st["h2"]),
        worksheet_table(
            [
                ["Decision area", "Seller entry"],
                ["Preferred occupancy or move constraint", "________________________________________________"],
                ["Other transaction that affects timing", "________________________________________________"],
                ["Access, pets, security, or notice needs", "________________________________________________"],
                ["Repairs, permits, claims, or known condition items", "________________________________________________"],
                ["Price and term priorities to discuss", "________________________________________________"],
            ],
            [2.55 * inch, 4.53 * inch],
            st,
        ),
        P("Evidence to date and label", st["h2"]),
        bullets(
            [
                "Recent closed sales selected for relevant location, property type, size, condition, features, and sale date.",
                "Current competing and pending listings, with status and source date recorded.",
                "Municipal tax record, permit or certificate records available to the seller, and association documents when applicable.",
                "Mortgage or lien payoff requests, insurance information, leases, warranties, service records, and invoices that may affect the transaction.",
                "A written note explaining each material adjustment or uncertainty instead of a single unsupported price number.",
            ],
            st,
        ),
        P("Questions for the pricing meeting", st["h2"]),
        worksheet_table(
            [
                ["Question", "Notes"],
                ["Which data date or property difference could change the price range?", "_______________________________________________"],
                ["Which property differences are not captured well?", "_______________________________________________"],
                ["What current competition could affect buyer attention?", "_______________________________________________"],
                ["What evidence would trigger a strategy review?", "_______________________________________________"],
            ],
            [3.2 * inch, 3.88 * inch],
            st,
        ),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "03 | Before marketing",
        "Document Condition, Disclosures, and Preparation",
        "Use the current official Seller's Property Condition Disclosure Statement and answer from "
        "the seller's knowledge. The form is not a warranty or a substitute for buyer inspections. "
        "Known material information, flood questions, and property records should be handled with "
        "the current form and qualified legal guidance.",
    )
    story += [
        P("Current New Jersey disclosure file", st["h2"]),
        bullets(
            [
                "Download the current Seller's Property Condition Disclosure Statement from the New Jersey Division of Consumer Affairs forms page. The listed form is effective April 20, 2026.",
                "Use the New Jersey DEP flood-disclosure resources and current property tool for flood questions; do not rely on memory or a marketing summary.",
                "Collect permits, certificates, invoices, warranties, insurance claims, environmental records, association documents, and known repair history that apply.",
                "Ask a New Jersey attorney about disclosure duties, exemptions, wording, and contract consequences for the seller's facts.",
            ],
            st,
        ),
        P("Preparation decision log", st["h2"]),
        worksheet_table(
            [
                ["Item", "Evidence or purpose", "Written scope / quote", "Seller decision"],
                ["________________", "________________", "________________", "________________"],
                ["________________", "________________", "________________", "________________"],
                ["________________", "________________", "________________", "________________"],
                ["________________", "________________", "________________", "________________"],
            ],
            [1.34 * inch, 2.05 * inch, 1.85 * inch, 1.84 * inch],
            st,
        ),
        P("Use a documented purpose, not an outcome claim", st["h2"]),
        P(
            "A seller may prepare, repair, replace, clean, stage, or leave an item as-is after "
            "considering condition, cost, disclosure, access, and marketing goals. Record the source "
            "and seller decision. No preparation item can promise a particular price, buyer response, "
            "or recovery of cost.",
            st["body"],
        ),
        P(
            "Official form: https://www.njconsumeraffairs.gov/Documents/Sellers-Property-Condition-Disclosure-Statement.pdf",
            st["small"],
        ),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "04 | Before signing",
        "Compare Listing Services and Compensation in Writing",
        "New Jersey requires a written brokerage services agreement for residential real estate "
        "services. NJDOBI Bulletin 24-11 explains that broker compensation is fully negotiable and "
        "not set by law. Review services, duration, compensation, payment sources, authority, and "
        "termination terms in the proposed agreement.",
    )
    story += [
        P("Agreement review worksheet", st["h2"]),
        worksheet_table(
            [
                ["Agreement item", "What the document says", "Question or decision"],
                ["Agency or business relationship", "____________________________", "____________________________"],
                ["Services and excluded services", "____________________________", "____________________________"],
                ["Start, duration, and termination", "____________________________", "____________________________"],
                ["Compensation and payment sources", "____________________________", "____________________________"],
                ["Marketing and showing authority", "____________________________", "____________________________"],
                ["Seller duties and approvals", "____________________________", "____________________________"],
            ],
            [2.02 * inch, 2.53 * inch, 2.53 * inch],
            st,
        ),
        P("Questions to ask every brokerage", st["h2"]),
        two_column_cards(
            [
                ("Evidence", "How will the price range and later strategy reviews be documented?"),
                ("Marketing", "Which first-party and listing-service channels are included, and who approves the materials?"),
                ("Communication", "What reporting cadence, access protocol, and decision record will the seller receive?"),
                ("Compensation", "How is compensation calculated, who may pay it, and what does the agreement authorize?"),
            ],
            st,
        ),
        P(
            "Do not compare compensation alone. Compare the complete written service, authority, "
            "duration, cost, and termination package, then ask an attorney to explain legal terms if needed.",
            st["body"],
        ),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "05 | Before launch",
        "Approve a Factual Marketing and Showing Plan",
        "Marketing should describe the property accurately, use seller-approved materials, follow "
        "fair-housing requirements, and protect access and personal information. Distribution and "
        "showing activity do not establish a future price or outcome.",
    )
    story += [
        P("Marketing plan review", st["h2"]),
        worksheet_table(
            [
                ["Plan component", "Owner", "Approval / source", "Status"],
                ["Property facts and measurements", "____________", "____________________", "____________"],
                ["Photography, captions, and usage rights", "____________", "____________________", "____________"],
                ["Listing description and fair-housing review", "____________", "____________________", "____________"],
                ["Listing service and first-party distribution", "____________", "____________________", "____________"],
                ["Showing notice, access, pets, and security", "____________", "____________________", "____________"],
                ["Feedback and strategy-review record", "____________", "____________________", "____________"],
            ],
            [2.25 * inch, 1.05 * inch, 2.38 * inch, 1.4 * inch],
            st,
        ),
        P("Accuracy and fair-housing checkpoints", st["h2"]),
        bullets(
            [
                "Verify statements about rooms, systems, improvements, permits, association features, transit, taxes, and measurements before publication.",
                "Describe property attributes and current official resources; do not rank communities or describe who should live in a location.",
                "Do not use protected-class preferences, family-status targeting, demographic profiles, or subjective school and safety claims.",
                "Remove account information, medications, valuables, family schedules, keys, mail, and sensitive documents before access begins.",
                "Document seller approval for material changes to price, terms, description, showing access, or distribution.",
            ],
            st,
        ),
        P("Seller notes", st["h2"]),
        P("________________________________________________________________________________<br/>________________________________________________________________________________<br/>________________________________________________________________________________", st["body"]),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "06 | When offers arrive",
        "Compare Price and Terms on One Evidence Sheet",
        "The largest price is not automatically the preferred offer. Compare financing evidence, "
        "deposit, contingencies, credits, property included, dates, and other signed terms. Ask the "
        "responsible professionals to explain legal, lending, appraisal, and tax implications.",
    )
    story += [
        worksheet_table(
            [
                ["Offer field", "Offer A", "Offer B", "Offer C"],
                ["Price (seller entry)", "$ ____________", "$ ____________", "$ ____________"],
                ["Deposit and due dates", "______________", "______________", "______________"],
                ["Financing evidence", "______________", "______________", "______________"],
                ["Inspection terms", "______________", "______________", "______________"],
                ["Appraisal terms", "______________", "______________", "______________"],
                ["Credits or concessions", "$ ____________", "$ ____________", "$ ____________"],
                ["Proposed contract dates", "______________", "______________", "______________"],
                ["Included or excluded property", "______________", "______________", "______________"],
                ["Other terms and risks", "______________", "______________", "______________"],
            ],
            [1.74 * inch, 1.78 * inch, 1.78 * inch, 1.78 * inch],
            st,
        ),
        P("Decision questions", st["h2"]),
        bullets(
            [
                "Which terms are verified by documents, and which depend on future approval or performance?",
                "Which contingency, date, credit, or included item matters most to the seller's plan?",
                "What happens under the signed language if financing, appraisal, inspection, title, or another condition changes?",
                "Which question belongs with the attorney, lender, tax adviser, title professional, or other specialist?",
                "What counteroffer or clarification, if any, should be documented in writing?",
            ],
            st,
        ),
        P("Seller decision and reason", st["h2"]),
        P("Selected offer / response: ____________________________  Date: __________________<br/>Reason and professional input: ______________________________________________________<br/>________________________________________________________________________________", st["body"]),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "07 | Financial planning",
        "Build an Estimated Net-Proceeds Worksheet",
        "Every amount below is seller-entered from a current written source. This is a planning "
        "worksheet, not a settlement statement or tax calculation. Replace estimates with the final "
        "figures from the responsible provider and signed transaction documents.",
    )
    story += [
        worksheet_table(
            [
                ["Line item", "Seller-entered amount", "Source / date"],
                ["Proposed sale price", "$ __________________", "________________________"],
                ["Mortgage, lien, or other payoff", "$ __________________", "________________________"],
                ["Brokerage compensation", "$ __________________", "________________________"],
                ["Realty Transfer Fee estimate", "$ __________________", "________________________"],
                ["Legal or settlement services", "$ __________________", "________________________"],
                ["Title, recording, or association items", "$ __________________", "________________________"],
                ["Agreed credits, repairs, or concessions", "$ __________________", "________________________"],
                ["Moving, occupancy, or other seller cost", "$ __________________", "________________________"],
                ["GIT/REP estimated payment, if applicable", "$ __________________", "________________________"],
                ["Estimated net proceeds", "$ __________________", "Recalculate when inputs change"],
            ],
            [2.65 * inch, 2.05 * inch, 2.38 * inch],
            st,
        ),
        P("New Jersey transfer and income-tax documents", st["h2"]),
        P(
            "The New Jersey Division of Taxation says the State imposes the Realty Transfer Fee on "
            "the seller for recording a deed, subject to the current schedule and applicable exemptions. "
            "A GIT/REP form is a separate Gross Income Tax filing required with a deed. Depending on "
            "residency and the form instructions, an estimated Gross Income Tax payment may apply. "
            "Use the official form name and instructions. Ask a qualified tax adviser and the closing professional "
            "to select and complete the current official forms for the seller's facts.",
            st["body"],
        ),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "08 | After contract",
        "Track the Signed Contract-to-Closing File",
        "The signed contract, amendments, notices, and professional instructions control the transaction. "
        "Use their dates and responsibilities rather than a generic schedule. Keep one indexed file so "
        "open items, approvals, payments, and final documents can be traced.",
    )
    story += [
        P("Transaction tracker", st["h2"]),
        worksheet_table(
            [
                ["Document or task", "Responsible party", "Document date / status"],
                ["Signed contract and all amendments", "__________________", "____________________________"],
                ["Seller disclosures and acknowledgments", "__________________", "____________________________"],
                ["Title, deed, payoff, and lien items", "__________________", "____________________________"],
                ["Inspection reports and written resolutions", "__________________", "____________________________"],
                ["Appraisal or financing items affecting seller", "__________________", "____________________________"],
                ["Municipal, association, certificate, or permit items", "__________________", "____________________________"],
                ["Insurance, utility, occupancy, and move coordination", "__________________", "____________________________"],
                ["Settlement figures, tax forms, and recording package", "__________________", "____________________________"],
            ],
            [2.83 * inch, 1.7 * inch, 2.55 * inch],
            st,
        ),
        P("Questions before signing or approving a change", st["h2"]),
        two_column_cards(
            [
                ("Authority", "Who is authorized to approve this item, and is the approval documented?"),
                ("Date", "Which signed document sets the date, and has a later writing changed it?"),
                ("Money", "Which provider supplied the figure, and is it still an estimate or final amount?"),
                ("Risk", "Which professional should explain the consequence if the condition is not satisfied?"),
            ],
            st,
        ),
        P("Final file to retain", st["h2"]),
        P(
            "Keep the signed agreement and amendments, disclosures, inspection resolutions, title and deed "
            "documents, settlement figures, payoff proof, GIT/REP and RTF records, invoices, warranties, and "
            "professional advice according to the retention guidance provided by the responsible professionals.",
            st["body"],
        ),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "09 | Master review",
        "Pre-Listing and Transaction Checklist",
        "Use the checkboxes as a conversation guide. A checked item means the source, date, owner, and next "
        "step are documented. It does not mean a specialist has approved an issue outside the reviewer's scope.",
    )
    story += [
        P("Before the listing agreement", st["h2"]),
        bullets(
            [
                "[ ] Seller goals, occupancy, access, and connected transaction are documented.",
                "[ ] Property facts, tax record, permits, association records, leases, and known condition documents are collected.",
                "[ ] Comparable evidence and its limits are explained; an appraisal is requested if an appraisal conclusion is needed.",
                "[ ] Proposed services, duration, compensation, payment sources, authority, and termination terms are reviewed in writing.",
            ],
            st,
        ),
        P("Before marketing", st["h2"]),
        bullets(
            [
                "[ ] Current Seller's Property Condition Disclosure Statement and flood resources are reviewed.",
                "[ ] Preparation choices have a written scope, cost source, purpose, and seller decision.",
                "[ ] Marketing facts, image rights, fair-housing review, distribution, access, pets, and security are approved.",
                "[ ] Sensitive records, valuables, keys, medications, account details, and personal schedules are secured.",
            ],
            st,
        ),
        P("When offers arrive", st["h2"]),
        bullets(
            [
                "[ ] Price, financing evidence, deposit, contingencies, credits, property included, and dates are compared together.",
                "[ ] Legal, lending, appraisal, title, inspection, and tax questions are assigned to the proper professional.",
                "[ ] The seller's selection, counteroffer, or rejection is documented in writing.",
            ],
            st,
        ),
        P("After contract", st["h2"]),
        bullets(
            [
                "[ ] Signed documents and updates are indexed with responsible parties and current status.",
                "[ ] Net-proceeds inputs are replaced as written figures change.",
                "[ ] Deed, payoff, title, disclosure, RTF, GIT/REP, settlement, and move records are retained as advised.",
            ],
            st,
        ),
        P("Open items", st["h2"]),
        P("________________________________________________________________________________<br/>________________________________________________________________________________", st["body"]),
        PageBreak(),
    ]

    story += page_intro(
        st,
        "10 | Verify before use",
        "Primary New Jersey Sources",
        "Open the current agency page before relying on a form or rule. The notes below summarize the "
        "source's role; they do not replace the full source, signed agreement, or professional advice.",
    )
    story += [
        source_link(
            "NJDOBI Bulletin 24-11",
            "https://www.nj.gov/dobi/bulletins/blt24_11.pdf",
            "Brokerage services agreements, business relationships, Property Condition Disclosure Statement, and fully negotiable broker compensation.",
            st,
        ),
        source_link(
            "NJ Division of Consumer Affairs - Statutes, Regulations, and Forms",
            "https://www.njconsumeraffairs.gov/ocp/Pages/regulations.aspx",
            "Current Seller's Property Condition Disclosure Statement and instructions; the forms page lists the disclosure statement effective April 20, 2026.",
            st,
        ),
        source_link(
            "NJDEP Flood Risk Notification",
            "https://dep.nj.gov/flooddisclosure/",
            "Seller flood-disclosure overview and the State's property research tool.",
            st,
        ),
        source_link(
            "NJ Division of Taxation - Realty Transfer Fee",
            "https://www.nj.gov/treasury/taxation/realty.shtml",
            "Current RTF overview, schedules, forms, seller responsibility, and exemptions.",
            st,
        ),
        source_link(
            "NJ Division of Taxation - GIT/REP FAQs",
            "https://www.nj.gov/treasury/taxation/gitrepfaqs.shtml",
            "Gross Income Tax forms recorded with a deed and when an estimated payment may apply.",
            st,
        ),
        source_link(
            "NJ Division of Taxation - Buying, Selling, or Transferring Real Property",
            "https://www.nj.gov/treasury/taxation/realtytransfees.shtml",
            "Central State page for transfer-related taxes, fees, procedures, and official forms.",
            st,
        ),
        source_link(
            "NJ Department of Banking and Insurance - Buying a Home",
            "https://nj.gov/dobi/division_consumers/pdf/buyingahome.pdf",
            "Consumer overview of transaction roles and documents; confirm current practice with the responsible professional.",
            st,
        ),
        source_link(
            "U.S. EPA - Lead-Based Paint Disclosure Rule",
            "https://www.epa.gov/lead/lead-based-paint-disclosure-rule-section-1018-title-x",
            "Federal disclosure and information requirements for most pre-1978 housing.",
            st,
        ),
        Spacer(1, 8),
        Table(
            [[
                P("Ready to organize your seller evidence file?", st["cta_title"]),
                P(
                    "For a no-obligation real estate planning conversation, call "
                    "<b>908-230-7844</b> or email <b>jorge.ramirez@kw.com</b>.<br/>"
                    "Home-value planning: thejorgeramirezgroup.com/home-valuation",
                    st["cta_body"],
                ),
            ]],
            colWidths=[2.95 * inch, 4.13 * inch],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), DEEP_RED),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 14),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            ),
        ),
        Spacer(1, 7),
        P(
            "Jorge Ramirez | NJ real estate salesperson #1754604 | Full-time Realtor with "
            "Keller Williams Premier Properties since 2017.<br/>488 Springfield Ave, Summit, NJ 07901 | "
            "Office: 908-273-2991 | Equal Housing Opportunity<br/>General educational information, "
            "not legal, tax, financial, appraisal, engineering, environmental, title, insurance, or "
            "inspection advice. (c) 2026 The Jorge Ramirez Group.",
            st["small"],
        ),
    ]
    return story


def build_pdf(output: Path) -> None:
    register_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=46,
        rightMargin=46,
        topMargin=51,
        bottomMargin=45,
        title="NJ Home Seller Planning Guide",
        author="The Jorge Ramirez Group",
        subject="Source-led New Jersey home seller planning workbook",
        allowSplitting=1,
    )
    cover_frame = Frame(54, 92, 504, 650, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="cover")
    content_frame = Frame(46, 42, 520, 705, leftPadding=4, rightPadding=4, topPadding=8, bottomPadding=8, id="content")
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[cover_frame], onPage=draw_cover),
            PageTemplate(
                id="content",
                frames=[content_frame],
                onPage=draw_content_background,
                onPageEnd=draw_content_furniture,
            ),
        ]
    )
    doc.build(build_story(styles()), canvasmaker=DeterministicCanvas)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that --output exactly matches a fresh deterministic build.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    output = arguments.output.resolve()
    if arguments.check:
        if not output.is_file():
            raise SystemExit(f"missing generated PDF: {output}")
        with tempfile.TemporaryDirectory(prefix="seller-guide-check-") as temp_dir:
            fresh = Path(temp_dir) / output.name
            build_pdf(fresh)
            if fresh.read_bytes() != output.read_bytes():
                raise SystemExit(
                    "seller guide is stale; regenerate with "
                    f"{Path(__file__).name} --output {output}"
                )
        print(f"seller guide is current and deterministic: {output}")
    else:
        build_pdf(output)
