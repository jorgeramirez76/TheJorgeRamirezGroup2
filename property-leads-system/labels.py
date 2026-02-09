"""
Avery 5160 Label Generation

Generates PDF mailing labels formatted for Avery 5160 label sheets.
Specs: 30 labels per sheet, 1" x 2-5/8", 3 columns x 10 rows

Each label contains:
- Owner name
- Property address or owner mailing address
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os

# Avery 5160 specifications
LABEL_WIDTH = 2.625 * inch      # 2-5/8 inches
LABEL_HEIGHT = 1.0 * inch       # 1 inch
COLUMNS = 3
ROWS = 10

# Margins from Avery 5160 template
LEFT_MARGIN = 0.1875 * inch     # 3/16 inch
TOP_MARGIN = 0.5 * inch         # 1/2 inch

# Horizontal gap between columns
COLUMN_GAP = 0.125 * inch       # 1/8 inch

# Vertical gap between rows  
ROW_GAP = 0.0 * inch            # No vertical gap for 5160


def format_address_lines(name, address_line1, city, state, zip_code, address_line2=None):
    """
    Format address into lines for label.
    
    Returns list of lines to print.
    """
    lines = []
    
    # Owner name
    if name:
        lines.append(name[:35])  # Limit length
    
    # Address lines
    if address_line1:
        lines.append(address_line1[:35])
    if address_line2:
        lines.append(address_line2[:35])
    
    # City, State Zip
    city_state_zip = f"{city}, {state} {zip_code}" if city else f"{state} {zip_code}"
    lines.append(city_state_zip[:35])
    
    return lines


def parse_address(address_string):
    """
    Parse an address string into components.
    Expected formats:
    - "123 Main St, Newark, NJ 07102"
    - "123 Main St\nNewark, NJ 07102"
    """
    if not address_string:
        return None, None, None, None, None
    
    # Normalize line breaks
    address_string = address_string.replace('\n', ', ')
    
    parts = [p.strip() for p in address_string.split(',')]
    
    if len(parts) >= 2:
        street = parts[0]
        # Last part should have city, state, zip
        last_part = parts[-1]
        city_state_parts = last_part.split()
        
        if len(city_state_parts) >= 2:
            state = city_state_parts[-2] if len(city_state_parts[-2]) == 2 else 'NJ'
            zip_code = city_state_parts[-1] if city_state_parts[-1].isdigit() or '-' in city_state_parts[-1] else ''
            city = ' '.join(city_state_parts[:-2]) if len(city_state_parts) > 2 else ''
            return street, None, city, state, zip_code
    
    # Fallback - return as-is
    return address_string, None, '', 'NJ', ''


def create_label_pdf(properties, output_path=None, use_mailing_address=True):
    """
    Create a PDF with Avery 5160 formatted labels.
    
    Args:
        properties: List of Property objects
        output_path: Path to save PDF (if None, returns BytesIO buffer)
        use_mailing_address: If True, use owner_address; otherwise use property address
    
    Returns:
        Path to saved file, or BytesIO buffer if output_path is None
    """
    if output_path is None:
        buffer = BytesIO()
    else:
        buffer = output_path
    
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Start from top of page
    current_row = 0
    current_col = 0
    
    for prop in properties:
        # Determine which address to use
        if use_mailing_address and prop.owner_address:
            street, street2, city, state, zip_code = parse_address(prop.owner_address)
        else:
            street = prop.address
            street2 = None
            city = prop.city
            state = prop.state
            zip_code = prop.zip_code
        
        # Calculate label position
        x = LEFT_MARGIN + (current_col * (LABEL_WIDTH + COLUMN_GAP))
        y = height - TOP_MARGIN - (current_row * LABEL_HEIGHT) - LABEL_HEIGHT
        
        # Draw label content
        c.setFont("Helvetica", 10)
        
        lines = format_address_lines(
            prop.owner_name or 'Current Resident',
            street,
            city,
            state,
            zip_code,
            street2
        )
        
        # Draw text with padding
        text_x = x + 0.1 * inch
        text_y = y + LABEL_HEIGHT - 0.15 * inch
        line_height = 11  # points
        
        for line in lines:
            if text_y > y:  # Don't overflow label
                c.drawString(text_x, text_y, line)
                text_y -= line_height
        
        # Move to next label position
        current_col += 1
        if current_col >= COLUMNS:
            current_col = 0
            current_row += 1
            
            # Start new page if needed
            if current_row >= ROWS:
                c.showPage()
                current_row = 0
    
    c.save()
    
    if output_path is None:
        buffer.seek(0)
        return buffer
    else:
        return output_path


def export_labels_to_pdf(property_ids, output_path='labels.pdf', use_mailing_address=True):
    """
    Export specific properties to label PDF.
    
    Args:
        property_ids: List of property IDs to export
        output_path: Output PDF file path
        use_mailing_address: Use owner's mailing address if available
    
    Returns:
        Path to generated PDF
    """
    from database import get_session, Property
    
    session = get_session()
    properties = session.query(Property).filter(Property.id.in_(property_ids)).all()
    session.close()
    
    return create_label_pdf(properties, output_path, use_mailing_address)


def export_filtered_labels(city=None, min_score=0, max_score=100, 
                          output_path='filtered_labels.pdf',
                          use_mailing_address=True):
    """
    Export filtered properties to label PDF.
    
    Args:
        city: Filter by city
        min_score: Minimum sell score
        max_score: Maximum sell score
        output_path: Output PDF file path
        use_mailing_address: Use owner's mailing address if available
    
    Returns:
        Path to generated PDF
    """
    from database import get_session, get_filtered_properties
    
    session = get_session()
    properties = get_filtered_properties(session, city=city, 
                                        min_score=min_score, 
                                        max_score=max_score)
    session.close()
    
    return create_label_pdf(properties, output_path, use_mailing_address)


def preview_label_text(properties, max_preview=5):
    """
    Generate text preview of what labels will look like.
    
    Returns:
        String with label preview
    """
    preview = []
    preview.append("=" * 40)
    preview.append("LABEL PREVIEW (Avery 5160)")
    preview.append("=" * 40)
    preview.append(f"Total labels: {len(properties)}")
    preview.append(f"Pages needed: {(len(properties) + 29) // 30}")
    preview.append("")
    
    for i, prop in enumerate(properties[:max_preview]):
        preview.append(f"--- Label {i+1} ---")
        
        if prop.owner_address:
            street, street2, city, state, zip_code = parse_address(prop.owner_address)
        else:
            street = prop.address
            street2 = None
            city = prop.city
            state = prop.state
            zip_code = prop.zip_code
        
        name = prop.owner_name or 'Current Resident'
        preview.append(name[:35])
        preview.append(street[:35] if street else '')
        if street2:
            preview.append(street2[:35])
        preview.append(f"{city}, {state} {zip_code}"[:35])
        preview.append("")
    
    if len(properties) > max_preview:
        preview.append(f"... and {len(properties) - max_preview} more")
    
    return "\n".join(preview)


if __name__ == '__main__':
    # Demo label generation
    from database import init_db, get_session, Property
    
    init_db()
    
    session = get_session()
    
    # Get some properties to demo
    props = session.query(Property).limit(35).all()
    session.close()
    
    if props:
        # Create sample PDF
        output_file = 'demo_labels.pdf'
        create_label_pdf(props, output_file)
        print(f"Created {output_file}")
        print(preview_label_text(props))
    else:
        print("No properties in database. Run collector.py first.")