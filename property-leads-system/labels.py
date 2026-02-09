from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from typing import List
from pathlib import Path

LABEL_WIDTH = 2.625 * inch
LABEL_HEIGHT = 1.0 * inch
MARGIN_LEFT = 0.1875 * inch
MARGIN_TOP = 0.5 * inch
COL_GAP = 0.125 * inch

def create_labels_for_properties(props, filename: str) -> str:
    output = Path(__file__).parent / filename
    c = canvas.Canvas(str(output), pagesize=letter)
    width, height = letter
    
    for i, prop in enumerate(props):
        col = i % 3
        row = (i // 3) % 10
        
        x = MARGIN_LEFT + col * (LABEL_WIDTH + COL_GAP)
        y = height - MARGIN_TOP - (row + 1) * LABEL_HEIGHT
        
        name = prop.owner_name or 'Current Resident'
        addr = prop.address
        city = prop.city
        zipc = prop.zip_code
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 0.1*inch, y + 0.7*inch, name)
        c.setFont("Helvetica", 10)
        c.drawString(x + 0.1*inch, y + 0.45*inch, addr)
        c.drawString(x + 0.1*inch, y + 0.2*inch, f"{city}, NJ {zipc}")
        
        if (i + 1) % 30 == 0 and i < len(props) - 1:
            c.showPage()
    
    c.save()
    return str(output)