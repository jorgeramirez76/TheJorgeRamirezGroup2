#!/usr/bin/env python3
"""Render the six-page, source-backed New Jersey home-buyer PDF."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "guides" / "nj-home-buyer-guide.pdf"
MANIFEST = ROOT / "data" / "nj-home-buyer-guide-sources.json"
ASSETS = ROOT / "tools" / "pdf-assets"
INTER_REGULAR = ASSETS / "Inter-Regular.ttf"
INTER_SEMI = ASSETS / "Inter-SemiBold.ttf"
PLAYFAIR_SEMI = ASSETS / "PlayfairDisplay-SemiBold.ttf"
PLAYFAIR_BOLD = ASSETS / "PlayfairDisplay-Bold.ttf"

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 48

BLACK = HexColor("#0A0A0A")
INK = HexColor("#1A1A1A")
RED = HexColor("#C41230")
DEEP_RED = HexColor("#8B0D22")
GOLD = HexColor("#B8962E")
LIGHT_GOLD = HexColor("#D4AF5A")
IVORY = HexColor("#FAFAF8")
DEEP_IVORY = HexColor("#F8F6F2")
MUTED = HexColor("#655F55")
WHITE = HexColor("#FFFFFF")
SOFT_LINE = Color(184 / 255, 150 / 255, 46 / 255, alpha=0.32)

FONT_INTER = "GuideInter"
FONT_INTER_SEMI = "GuideInterSemi"
FONT_PLAYFAIR = "GuidePlayfair"
FONT_PLAYFAIR_BOLD = "GuidePlayfairBold"


def register_fonts() -> None:
    font_assets = (INTER_REGULAR, INTER_SEMI, PLAYFAIR_SEMI, PLAYFAIR_BOLD)
    if any(not path.exists() for path in font_assets):
        missing = [str(path) for path in font_assets if not path.exists()]
        raise FileNotFoundError("Missing licensed font asset(s): " + ", ".join(missing))
    pdfmetrics.registerFont(TTFont(FONT_INTER, INTER_REGULAR))
    pdfmetrics.registerFont(TTFont(FONT_INTER_SEMI, INTER_SEMI))
    pdfmetrics.registerFont(TTFont(FONT_PLAYFAIR, PLAYFAIR_SEMI))
    pdfmetrics.registerFont(TTFont(FONT_PLAYFAIR_BOLD, PLAYFAIR_BOLD))


def lines_for(text: str, font: str, size: float, width: float) -> list[str]:
    return simpleSplit(" ".join(text.split()), font, size, width)


def paragraph(
    canvas: Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = FONT_INTER,
    size: float = 9.4,
    leading: float = 13.3,
    color=INK,
) -> float:
    canvas.setFont(font, size)
    canvas.setFillColor(color)
    for line in lines_for(text, font, size, width):
        canvas.drawString(x, y, line)
        y -= leading
    return y


def eyebrow(canvas: Canvas, text: str, x: float, y: float, *, color=RED) -> None:
    canvas.setFillColor(color)
    canvas.setFont(FONT_INTER_SEMI, 8.2)
    canvas.drawString(x, y, text.upper())


def title(canvas: Canvas, text: str, x: float, y: float, width: float, *, size: float = 29) -> float:
    canvas.setFillColor(BLACK)
    canvas.setFont(FONT_PLAYFAIR_BOLD, size)
    leading = size * 1.08
    for line in lines_for(text, FONT_PLAYFAIR_BOLD, size, width):
        canvas.drawString(x, y, line)
        y -= leading
    return y


def section_intro(canvas: Canvas, label: str, heading: str, summary: str) -> float:
    y = PAGE_HEIGHT - 99
    eyebrow(canvas, label, MARGIN, y)
    y = title(canvas, heading, MARGIN, y - 27, PAGE_WIDTH - 2 * MARGIN)
    return paragraph(canvas, summary, MARGIN, y - 4, PAGE_WIDTH - 2 * MARGIN, size=10, leading=14.2, color=MUTED) - 9


def page_frame(canvas: Canvas, page_number: int, section: str) -> None:
    canvas.setFillColor(IVORY)
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFillColor(BLACK)
    canvas.rect(0, PAGE_HEIGHT - 64, PAGE_WIDTH, 64, stroke=0, fill=1)
    canvas.setFillColor(RED)
    canvas.rect(0, PAGE_HEIGHT - 64, 7, 64, stroke=0, fill=1)
    canvas.setFont(FONT_INTER_SEMI, 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN, PAGE_HEIGHT - 38, "THE JORGE RAMIREZ GROUP")
    section_width = pdfmetrics.stringWidth(section.upper(), FONT_INTER_SEMI, 7.5)
    canvas.setFont(FONT_INTER_SEMI, 7.5)
    canvas.setFillColor(LIGHT_GOLD)
    canvas.drawString(PAGE_WIDTH - MARGIN - section_width, PAGE_HEIGHT - 38, section.upper())
    canvas.setStrokeColor(SOFT_LINE)
    canvas.line(MARGIN, 36, PAGE_WIDTH - MARGIN, 36)
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT_INTER, 6.8)
    canvas.drawString(MARGIN, 22, "NEW JERSEY HOME BUYER GUIDE")
    page_text = f"{page_number} / 6"
    page_width = pdfmetrics.stringWidth(page_text, FONT_INTER_SEMI, 6.8)
    canvas.setFont(FONT_INTER_SEMI, 6.8)
    canvas.drawString(PAGE_WIDTH - MARGIN - page_width, 22, page_text)


def card(
    canvas: Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    label: str,
    heading: str,
    body: str,
    *,
    dark: bool = False,
) -> None:
    bottom = top - height
    canvas.setFillColor(INK if dark else WHITE)
    canvas.setStrokeColor(GOLD if dark else SOFT_LINE)
    canvas.roundRect(x, bottom, width, height, 10, stroke=1, fill=1)
    eyebrow(canvas, label, x + 18, top - 23, color=LIGHT_GOLD if dark else RED)
    canvas.setFont(FONT_PLAYFAIR, 15.5)
    canvas.setFillColor(WHITE if dark else BLACK)
    heading_y = top - 48
    for line in lines_for(heading, FONT_PLAYFAIR, 15.5, width - 36):
        canvas.drawString(x + 18, heading_y, line)
        heading_y -= 18
    paragraph(
        canvas,
        body,
        x + 18,
        heading_y - 5,
        width - 36,
        size=8.5,
        leading=12.2,
        color=DEEP_IVORY if dark else MUTED,
    )


def callout(canvas: Canvas, top: float, heading: str, body: str, *, accent=RED) -> float:
    height = 98
    bottom = top - height
    canvas.setFillColor(WHITE)
    canvas.setStrokeColor(SOFT_LINE)
    canvas.roundRect(MARGIN, bottom, PAGE_WIDTH - 2 * MARGIN, height, 10, stroke=1, fill=1)
    canvas.setFillColor(accent)
    canvas.roundRect(MARGIN, bottom, 6, height, 3, stroke=0, fill=1)
    canvas.setFillColor(BLACK)
    canvas.setFont(FONT_PLAYFAIR, 14.2)
    canvas.drawString(MARGIN + 21, top - 28, heading)
    paragraph(canvas, body, MARGIN + 21, top - 48, PAGE_WIDTH - 2 * MARGIN - 42, size=8.7, leading=12.2, color=MUTED)
    return bottom


def bullet_list(canvas: Canvas, items: list[str], x: float, y: float, width: float, *, size: float = 8.8) -> float:
    for item in items:
        canvas.setFillColor(RED)
        canvas.circle(x + 3, y + 2, 2.2, stroke=0, fill=1)
        y = paragraph(canvas, item, x + 14, y + 5, width - 14, size=size, leading=12.4, color=INK) - 7
    return y


def link_line(canvas: Canvas, label: str, url: str, x: float, y: float, width: float) -> float:
    y = paragraph(canvas, label, x, y, width, font=FONT_INTER_SEMI, size=7.5, leading=10.5, color=BLACK)
    url_lines = lines_for(url, FONT_INTER, 6.7, width)
    for line in url_lines:
        canvas.setFont(FONT_INTER, 6.7)
        canvas.setFillColor(DEEP_RED)
        canvas.drawString(x, y, line)
        line_width = pdfmetrics.stringWidth(line, FONT_INTER, 6.7)
        canvas.linkURL(url, (x, y - 2, x + line_width, y + 8), relative=0, thickness=0)
        y -= 9.2
    return y - 5


def source_map() -> dict[str, dict[str, object]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("reviewed") != "2026-08-26":
        raise ValueError("Source manifest review date must match the guide review date")
    return {record["id"]: record for record in manifest["sources"]}


def draw_cover(canvas: Canvas) -> None:
    canvas.setFillColor(BLACK)
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFillColor(RED)
    canvas.rect(0, 0, 12, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFillColor(GOLD)
    canvas.rect(12, 0, 3, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_INTER_SEMI, 9)
    canvas.drawString(54, 736, "THE JORGE RAMIREZ GROUP")
    canvas.setFillColor(LIGHT_GOLD)
    canvas.setFont(FONT_INTER_SEMI, 8)
    canvas.drawString(54, 690, "NEW JERSEY / DOCUMENT-FIRST ROADMAP")
    y = 627
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_PLAYFAIR_BOLD, 42)
    for line in ("New Jersey", "Home Buyer", "Guide"):
        canvas.drawString(54, y, line)
        y -= 49
    canvas.setFillColor(RED)
    canvas.rect(54, y + 13, 86, 4, stroke=0, fill=1)
    y = paragraph(
        canvas,
        "Plan the purchase from written loan terms, the signed contract, property records, independent due diligence, and final closing documents.",
        54,
        y - 19,
        462,
        size=12,
        leading=17,
        color=DEEP_IVORY,
    )
    canvas.setFillColor(INK)
    canvas.setStrokeColor(GOLD)
    canvas.roundRect(54, y - 110, 504, 89, 10, stroke=1, fill=1)
    eyebrow(canvas, "Primary sources", 74, y - 47, color=LIGHT_GOLD)
    paragraph(
        canvas,
        "NJDOBI  /  NJHMFA  /  Consumer Financial Protection Bureau  /  HUD",
        74,
        y - 69,
        464,
        font=FONT_INTER_SEMI,
        size=8.5,
        leading=12,
        color=WHITE,
    )
    canvas.setFillColor(LIGHT_GOLD)
    canvas.setFont(FONT_INTER_SEMI, 7.5)
    canvas.drawString(74, y - 92, "REVIEWED 2026-08-26")
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_PLAYFAIR, 17)
    canvas.drawString(54, 134, "Jorge Ramirez")
    paragraph(
        canvas,
        "New Jersey real estate agent  /  License #1754604  /  Keller Williams Premier Properties",
        54,
        112,
        500,
        font=FONT_INTER_SEMI,
        size=7.5,
        leading=11,
        color=DEEP_IVORY,
    )
    paragraph(
        canvas,
        "Serving Union, Essex, Morris, Hudson, Middlesex, and Somerset counties",
        54,
        83,
        500,
        size=7.5,
        leading=10,
        color=LIGHT_GOLD,
    )
    canvas.setFont(FONT_INTER, 7)
    canvas.setFillColor(DEEP_IVORY)
    canvas.drawString(54, 43, "thejorgeramirezgroup.com  /  908-230-7844")
    canvas.showPage()


def draw_budget_page(canvas: Canvas, sources: dict[str, dict[str, object]]) -> None:
    page_frame(canvas, 2, "Money plan")
    y = section_intro(
        canvas,
        "01 / Before the search",
        "Build the complete housing obligation",
        "A price target is useful only when the payment, upfront cash, property obligations, and reserves work together. Replace generic rules of thumb with written figures for the loan and address.",
    )
    gap = 14
    card_width = (PAGE_WIDTH - 2 * MARGIN - gap) / 2
    card(canvas, MARGIN, y, card_width, 130, "Monthly plan", "Carry the full payment", "Track principal and interest, property taxes, homeowners insurance, mortgage insurance when applicable, association obligations, utilities, maintenance, and other recurring costs.")
    card(canvas, MARGIN + card_width + gap, y, card_width, 130, "Upfront plan", "Name every cash category", "List deposits, lender and provider charges, prepaids, reserves, moving, property work, and the amount the final documents require. Credits and timing can change the result.")
    y -= 146
    card(canvas, MARGIN, y, card_width, 130, "Property plan", "Price the actual address", "Use current tax records, an insurance quote, association documents, inspection findings, municipal records, and expected maintenance instead of a townwide assumption.")
    card(canvas, MARGIN + card_width + gap, y, card_width, 130, "Decision rule", "Keep evidence beside each number", "Mark each figure as confirmed, estimated, or unknown. Note the source and date. Update the plan when the lender, contract, title work, insurance, or property record changes.", dark=True)
    y -= 151
    source = sources["cfpb-toolkit"]
    callout(canvas, y, "Start with the CFPB home-loan toolkit", "Use the federal toolkit to organize mortgage shopping, closing-cost review, and preparation. A calculator is a planning aid; lender and property documents control the real transaction.", accent=GOLD)
    link_line(canvas, str(source["publisher"]), str(source["url"]), MARGIN + 20, y - 111, PAGE_WIDTH - 2 * MARGIN - 40)
    canvas.showPage()


def draw_financing_page(canvas: Canvas, sources: dict[str, dict[str, object]]) -> None:
    page_frame(canvas, 3, "Financing")
    y = section_intro(
        canvas,
        "02 / Written loan terms",
        "Compare the documents, not a headline",
        "Make comparable loan requests, keep every written response, and ask the lender to explain differences. The right comparison includes the complete obligation and cash needed to close.",
    )
    card(canvas, MARGIN, y, PAGE_WIDTH - 2 * MARGIN, 137, "Loan Estimate", "Read the same fields across offers", "Compare loan type and term, rate and lock status, projected payment, mortgage insurance, origination charges, services, lender credits, prepayment features, and estimated cash to close. Ask what can change and why.")
    y -= 154
    card(canvas, MARGIN, y, PAGE_WIDTH - 2 * MARGIN, 146, "NJHMFA programs", "Verify eligibility at the current official source", "NJHMFA publishes program-specific rules for eligibility, property, occupancy, income, purchase price, education, and participating lenders. Terms can change. Save the program page, fact sheet, limits, and lender guidance used for your application.", dark=True)
    y -= 164
    eyebrow(canvas, "Verification questions", MARGIN, y)
    y = bullet_list(
        canvas,
        [
            "Is this Loan Estimate based on the same loan amount, property type, occupancy, and lock choice as the other offer?",
            "Which figures are lender-controlled, provider estimates, or property-specific items that still need confirmation?",
            "Does the lender participate in the NJHMFA program being considered, and which current document establishes eligibility?",
            "What written condition, deadline, or document could change the approval, payment, or cash needed to close?",
        ],
        MARGIN,
        y - 20,
        PAGE_WIDTH - 2 * MARGIN,
    )
    source = sources["cfpb-loan-estimate"]
    link_line(canvas, str(source["publisher"]) + " - Loan Estimate explainer", str(source["url"]), MARGIN, y - 2, 244)
    source = sources["njhmfa-programs"]
    link_line(canvas, str(source["publisher"]) + " - current homebuyer programs", str(source["url"]), 320, y - 2, 244)
    canvas.showPage()


def draw_contract_page(canvas: Canvas, sources: dict[str, dict[str, object]]) -> None:
    page_frame(canvas, 4, "Representation and contract")
    y = section_intro(
        canvas,
        "03 / Put the relationship in writing",
        "Know who represents whom - and what controls",
        "Read the Consumer Information Statement and written brokerage service agreement. Then treat the fully signed contract as the source for deadlines, notices, contingencies, rights, and remedies.",
    )
    card(canvas, MARGIN, y, PAGE_WIDTH - 2 * MARGIN, 132, "Brokerage agreement", "Clarify services, relationship, term, and compensation", "New Jersey recognizes multiple brokerage relationships. Broker compensation is negotiable and not set by law. Ask who may pay it, what happens if another party offers less, and how any change or exit is documented.")
    y -= 149
    card(canvas, MARGIN, y, PAGE_WIDTH - 2 * MARGIN, 151, "Attorney fact check", "Legal representation is a choice, not a state requirement", "New Jersey does not require a home buyer to hire an attorney. NJDOBI says many buyers choose legal representation. A licensee-prepared contract may contain an attorney-review clause; read the exact signed clause and consult an attorney if retained. Do not calculate a deadline from this guide.", dark=True)
    y -= 169
    eyebrow(canvas, "Before signing or sending notice", MARGIN, y)
    y = bullet_list(
        canvas,
        [
            "Identify the contract provision governing financing, appraisal, inspection, title, closing, possession, and included property.",
            "Confirm who must receive each notice, the permitted delivery method, and the deadline stated in the signed contract.",
            "Keep amendments, inspection responses, credits, repair agreements, and other negotiated changes in writing.",
            "Direct legal questions to an attorney; a real estate licensee cannot provide legal advice.",
        ],
        MARGIN,
        y - 19,
        PAGE_WIDTH - 2 * MARGIN,
    )
    source = sources["njdobi-buying-guide"]
    link_line(canvas, str(source["publisher"]) + " - official consumer buying guide", str(source["url"]), MARGIN, y - 3, PAGE_WIDTH - 2 * MARGIN)
    canvas.showPage()


def draw_property_page(canvas: Canvas, sources: dict[str, dict[str, object]]) -> None:
    page_frame(canvas, 5, "Property evidence")
    y = section_intro(
        canvas,
        "04 / Verify the address",
        "Build the decision from objective property facts",
        "Your criteria should connect to your needs and the specific address. Use neutral sources, your own visits, independent professionals, and the contract instead of demographic assumptions or place rankings.",
    )
    gap = 14
    card_width = (PAGE_WIDTH - 2 * MARGIN - gap) / 2
    card(canvas, MARGIN, y, card_width, 146, "Records", "Municipal and property file", "Review current tax records, zoning and permitted use, permits, flood and environmental sources, association documents, accessibility needs, and the commute you would actually make.")
    card(canvas, MARGIN + card_width + gap, y, card_width, 146, "Condition", "Independent inspection", "Read the inspection agreement and report. Match each concern to the qualified specialist and the contract provision governing notice, access, negotiation, or termination.")
    y -= 163
    card(canvas, MARGIN, y, card_width, 146, "Separate roles", "Value is not condition", "An appraisal supports a lender's value analysis. It does not replace inspection, title, survey, insurance, permit research, environmental review, or specialist evaluation.")
    card(canvas, MARGIN + card_width + gap, y, card_width, 146, "Fair housing", "Use neutral, address-specific evidence", "The Fair Housing Act applies when buying a home, seeking a mortgage, and taking part in other housing activities. Jorge does not rank locations by protected traits or demographic profiles.", dark=True)
    y -= 165
    source = sources["hud-fair-housing"]
    callout(canvas, y, "Keep the evidence file", "Save disclosures, reports, photographs, permits, association records, insurance terms, title materials, amendments, invoices, and written resolutions. Record what is verified, what remains open, and who is qualified to answer it.", accent=GOLD)
    link_line(canvas, str(source["publisher"]) + " - Fair Housing Act overview", str(source["url"]), MARGIN + 20, y - 111, PAGE_WIDTH - 2 * MARGIN - 40)
    canvas.showPage()


def draw_closing_page(canvas: Canvas, sources: dict[str, dict[str, object]]) -> None:
    page_frame(canvas, 6, "Closing and sources")
    y = section_intro(
        canvas,
        "05 / Reconcile before signing",
        "Close the gaps between every final document",
        "Compare the Closing Disclosure with the latest Loan Estimate. Trace changes, verify wire instructions through a trusted channel, use the final walk-through to compare condition with the contract, and retain the signed package.",
    )
    eyebrow(canvas, "Closing file", MARGIN, y)
    y = bullet_list(
        canvas,
        [
            "Resolve unexpected terms or charges with the lender and closing professionals before signing.",
            "Confirm title status, insurance terms, property condition, contract credits, deposits, and final cash instructions.",
            "Keep the deed and recording information, loan package, Closing Disclosure, settlement records, warranties, and future notice contacts.",
        ],
        MARGIN,
        y - 18,
        PAGE_WIDTH - 2 * MARGIN,
        size=8.4,
    )
    eyebrow(canvas, "Official source desk / checked 2026-08-26", MARGIN, y - 2)
    y -= 20
    source_rows = [
        ("njdobi-buying-guide", "New Jersey Department of Banking and Insurance"),
        ("njhmfa-programs", "New Jersey Housing and Mortgage Finance Agency"),
        ("cfpb-loan-estimate", "Consumer Financial Protection Bureau - Loan Estimate"),
        ("cfpb-closing-disclosure", "Consumer Financial Protection Bureau - Closing Disclosure"),
        ("hud-fair-housing", "U.S. Department of Housing and Urban Development"),
    ]
    left_x, right_x = MARGIN, 316
    column_width = 248
    left_y = right_y = y
    for index, (source_id, label) in enumerate(source_rows):
        source = sources[source_id]
        if index < 3:
            left_y = link_line(canvas, label, str(source["url"]), left_x, left_y, column_width)
        else:
            right_y = link_line(canvas, label, str(source["url"]), right_x, right_y, column_width)
    y = min(left_y, right_y) - 5
    canvas.setFillColor(INK)
    canvas.roundRect(MARGIN, y - 111, PAGE_WIDTH - 2 * MARGIN, 105, 10, stroke=0, fill=1)
    eyebrow(canvas, "Local contact", MARGIN + 19, y - 29, color=LIGHT_GOLD)
    paragraph(canvas, "Jorge Ramirez  /  License #1754604  /  Keller Williams Premier Properties", MARGIN + 19, y - 50, PAGE_WIDTH - 2 * MARGIN - 38, font=FONT_INTER_SEMI, size=8, leading=11, color=WHITE)
    paragraph(canvas, "Serving Union, Essex, Morris, Hudson, Middlesex, and Somerset counties", MARGIN + 19, y - 72, PAGE_WIDTH - 2 * MARGIN - 38, size=7.6, leading=10, color=DEEP_IVORY)
    paragraph(canvas, "908-230-7844  /  thejorgeramirezgroup.com/nj-home-buyer-guide", MARGIN + 19, y - 92, PAGE_WIDTH - 2 * MARGIN - 38, size=7.4, leading=10, color=LIGHT_GOLD)
    disclaimer = "Educational information only; not legal, tax, financial, mortgage, insurance, inspection, title, or engineering advice. The signed contract and your licensed professionals control the transaction."
    paragraph(canvas, disclaimer, MARGIN, 69, PAGE_WIDTH - 2 * MARGIN, size=6.8, leading=9, color=MUTED)
    canvas.setFont(FONT_INTER_SEMI, 6.8)
    canvas.setFillColor(DEEP_RED)
    canvas.drawString(MARGIN, 45, "Reviewed 2026-08-26")
    canvas.showPage()


def render(output: Path) -> None:
    sources = source_map()
    output.parent.mkdir(parents=True, exist_ok=True)
    register_fonts()
    canvas = Canvas(
        str(output),
        pagesize=letter,
        pageCompression=1,
        invariant=1,
    )
    canvas.setTitle("New Jersey Home Buyer Guide")
    canvas.setAuthor("Jorge Ramirez, The Jorge Ramirez Group")
    canvas.setSubject("Source-backed New Jersey home-buyer planning guide; reviewed 2026-08-26")
    canvas.setCreator("tools/render_nj_home_buyer_guide_pdf.py")
    canvas.setKeywords("New Jersey home buyer guide, Loan Estimate, Closing Disclosure, NJHMFA, NJDOBI")
    draw_cover(canvas)
    draw_budget_page(canvas, sources)
    draw_financing_page(canvas, sources)
    draw_contract_page(canvas, sources)
    draw_property_page(canvas, sources)
    draw_closing_page(canvas, sources)
    canvas.save()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the committed PDF differs from a fresh render")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="nj-buyer-guide-pdf-") as directory:
        candidate = Path(directory) / OUTPUT.name
        render(candidate)
        if args.check:
            if not OUTPUT.exists() or OUTPUT.read_bytes() != candidate.read_bytes():
                print(f"out of date: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
                return 1
            print("buyer-guide PDF is current")
            return 0
        os.replace(candidate, OUTPUT)
    print(f"rendered {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
