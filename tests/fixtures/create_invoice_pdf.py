"""
Generate sample invoice PDF for testing.

This script creates a simple invoice PDF with a table structure suitable
for testing the PDFDataSource extraction capabilities.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


def create_invoice_pdf(filename: Path):
    """Create a sample invoice PDF with table.

    Invoice structure:
    - Header: Invoice #, Date, Vendor
    - Table: Line items (Item, Qty, Price, Total)
    - Footer: Total amount

    Args:
        filename: Path where PDF should be saved
    """
    c = canvas.Canvas(str(filename), pagesize=letter)
    width, height = letter

    # ========================================
    # Header Section
    # ========================================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "INVOICE")

    c.setFont("Helvetica", 12)
    c.drawString(1*inch, height - 1.5*inch, "Invoice #: INV-2024-001")
    c.drawString(1*inch, height - 1.8*inch, "Date: 2024-11-15")
    c.drawString(1*inch, height - 2.1*inch, "Vendor: Acme Corp")

    # ========================================
    # Table Section (Using bordered table)
    # ========================================
    y = height - 3*inch

    # Table header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1*inch, y, "Item")
    c.drawString(3*inch, y, "Qty")
    c.drawString(4*inch, y, "Price")
    c.drawString(5.5*inch, y, "Total")

    # Draw header underline
    c.line(0.9*inch, y - 0.1*inch, 6.5*inch, y - 0.1*inch)

    # Table rows (data)
    c.setFont("Helvetica", 11)

    # Row 1: Widget A
    y -= 0.4*inch
    c.drawString(1*inch, y, "Widget A")
    c.drawString(3*inch, y, "5")
    c.drawString(4*inch, y, "$10.00")
    c.drawString(5.5*inch, y, "$50.00")

    # Row 2: Widget B
    y -= 0.3*inch
    c.drawString(1*inch, y, "Widget B")
    c.drawString(3*inch, y, "3")
    c.drawString(4*inch, y, "$15.00")
    c.drawString(5.5*inch, y, "$45.00")

    # Row 3: Service Fee
    y -= 0.3*inch
    c.drawString(1*inch, y, "Service Fee")
    c.drawString(3*inch, y, "1")
    c.drawString(4*inch, y, "$119.50")
    c.drawString(5.5*inch, y, "$119.50")

    # ========================================
    # Footer Section
    # ========================================
    y -= 0.6*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(4.5*inch, y, "Total: $214.50")

    c.save()
    print(f"✅ Created invoice PDF: {filename}")


def create_invoice_with_borders(filename: Path):
    """Create invoice PDF with proper bordered table (better for extraction).

    Uses reportlab's Table class to create properly bordered table structure
    that pdfplumber can extract more reliably.
    """
    doc = SimpleDocTemplate(str(filename), pagesize=letter)

    # Build header text
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    styles = getSampleStyleSheet()
    story = []

    # Header
    header = Paragraph("<b>INVOICE</b>", styles['Title'])
    story.append(header)
    story.append(Spacer(1, 0.2*inch))

    # Invoice details
    invoice_info = Paragraph(
        "<b>Invoice #:</b> INV-2024-001<br/>"
        "<b>Date:</b> 2024-11-15<br/>"
        "<b>Vendor:</b> Acme Corp",
        styles['Normal']
    )
    story.append(invoice_info)
    story.append(Spacer(1, 0.3*inch))

    # Table data (header + rows)
    table_data = [
        ["Item", "Qty", "Price", "Total"],  # Header
        ["Widget A", "5", "$10.00", "$50.00"],
        ["Widget B", "3", "$15.00", "$45.00"],
        ["Service Fee", "1", "$119.50", "$119.50"],
    ]

    # Create table with borders
    table = Table(table_data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        # Header row style
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # Data rows style
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),

        # Borders (CRITICAL for pdfplumber "lines" strategy)
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.3*inch))

    # Total
    total_text = Paragraph("<b>Total: $214.50</b>", styles['Heading3'])
    story.append(total_text)

    # Build PDF
    doc.build(story)
    print(f"✅ Created bordered invoice PDF: {filename}")


if __name__ == "__main__":
    # Create output directory
    output_dir = Path(__file__).parent.parent.parent / "projects" / "invoice_transform" / "input"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate invoice with bordered table (BEST for pdfplumber)
    invoice_path = output_dir / "invoice_001.pdf"
    create_invoice_with_borders(invoice_path)

    print(f"\n📄 Invoice PDF created at: {invoice_path}")
    print(f"   Use this file for the Invoice Transform POC")
