"""
convert_resolved.py
-------------------
Core engine: converts a .resolved (Markdown) file into a styled PDF.
Uses markdown2 for parsing and reportlab for PDF rendering.
"""

import re
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Preformatted, HRFlowable, KeepTogether, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import base64
import urllib.request
import urllib.parse
import tempfile
import json
import io

# ─── Color Palette (Professional Light Theme — optimised for white PDF pages) ──
PAGE_BG      = colors.white
HEADER_BAR   = colors.HexColor("#1A1D2E")   # very dark navy — header/footer bar
ACCENT_BLUE  = colors.HexColor("#1E40AF")   # deep royal blue — h1/h2
ACCENT_GREEN = colors.HexColor("#16A34A")   # vivid medium green — h3
ACCENT_YELL  = colors.HexColor("#92400E")   # dark amber — blockquotes
CODE_BG      = colors.HexColor("#F1F5F9")   # very light slate — code background
CODE_TEXT    = colors.HexColor("#0F172A")   # near-black — code text
TABLE_HEADER = colors.HexColor("#1E3A5F")   # dark navy — table header
TABLE_ROW1   = colors.HexColor("#FFFFFF")   # white
TABLE_ROW2   = colors.HexColor("#F8FAFC")   # very pale blue-grey
TEXT_COLOR   = colors.HexColor("#0F172A")   # near-black — body text
MUTED        = colors.HexColor("#64748B")   # medium slate — muted labels
BORDER       = colors.HexColor("#CBD5E1")   # light slate — table/hr borders
WHITE        = colors.white


def fetch_mermaid_image(mermaid_text):
    """Fetch mermaid chart as a JPEG from mermaid.ink API."""
    try:
        # Mermaid Live Editor JSON state format
        state = {
            "code": mermaid_text,
            "mermaid": {"theme": "default"}
        }
        json_str = json.dumps(state)
        # Use simple base64, URL safe encoding is expected by the API
        b64 = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        url = f"https://mermaid.ink/img/{b64}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpeg')
                tmp.write(response.read())
                tmp.close()
                return tmp.name
    except Exception as e:
        print(f"Mermaid rendering failed: {e}")
    return None


def build_styles():
    """Return a dict of named ParagraphStyles."""
    styles = {}

    styles["h1"] = ParagraphStyle(
        "h1",
        fontSize=22, leading=30, textColor=ACCENT_BLUE,
        fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=14,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        fontSize=15, leading=22, textColor=ACCENT_BLUE,
        fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=12,
    )
    styles["h3"] = ParagraphStyle(
        "h3",
        fontSize=12, leading=18, textColor=ACCENT_GREEN,
        fontName="Helvetica-Bold", spaceAfter=3, spaceBefore=8,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontSize=10, leading=16, textColor=TEXT_COLOR,
        fontName="Helvetica", spaceAfter=4,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontSize=10, leading=15, textColor=TEXT_COLOR,
        fontName="Helvetica", leftIndent=18, bulletIndent=6,
        spaceAfter=3,
    )
    styles["blockquote"] = ParagraphStyle(
        "blockquote",
        fontSize=10, leading=15, textColor=ACCENT_YELL,
        fontName="Helvetica-Oblique", leftIndent=20,
        borderPadding=(6, 10, 6, 10), spaceAfter=4,
        backColor=colors.HexColor("#FFFBEB"),   # very pale amber tint
    )
    styles["code"] = ParagraphStyle(
        "code",
        fontSize=8.5, leading=13, textColor=CODE_TEXT,
        fontName="Courier", leftIndent=12, spaceAfter=2,
        backColor=CODE_BG,
    )
    styles["footer"] = ParagraphStyle(
        "footer",
        fontSize=8, leading=10, textColor=MUTED,
        fontName="Helvetica", alignment=TA_CENTER,
    )
    return styles


def escape_xml(text):
    """Escape characters that break ReportLab XML parsing."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def apply_inline(text):
    """Convert inline markdown (**bold**, `code`, *italic*) to ReportLab XML."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#A6E3A1">\1</font>', text)
    # Links → just show label
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text


def parse_table(lines):
    """Parse markdown table lines into a list-of-lists."""
    rows = []
    for line in lines:
        line = line.strip()
        if re.match(r'^[\|\-\s:]+$', line):
            continue  # separator row
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cells)
    return rows


def build_table_flowable(rows, styles):
    """Turn parsed rows into a styled ReportLab Table."""
    if not rows:
        return None

    col_count = max(len(r) for r in rows)
    # Pad rows to equal length
    padded = [r + [''] * (col_count - len(r)) for r in rows]

    # Build cell paragraphs
    table_data = []
    for i, row in enumerate(padded):
        style = styles["h3"] if i == 0 else styles["body"]
        table_data.append([
            Paragraph(apply_inline(escape_xml(cell)), style)
            for cell in row
        ])

    col_width = (A4[0] - 4 * cm) / col_count
    t = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
    t.setStyle(TableStyle([
        # Header row — dark navy bg, white bold text
        ("BACKGROUND",     (0, 0), (-1, 0),  TABLE_HEADER),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0),  9),
        # Data rows — alternating white / pale grey
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [TABLE_ROW1, TABLE_ROW2]),
        ("TEXTCOLOR",      (0, 1), (-1, -1), TEXT_COLOR),
        ("FONTNAME",       (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 1), (-1, -1), 9),
        # Borders
        ("GRID",           (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBELOW",      (0, 0), (-1, 0),  1.2, ACCENT_BLUE),
        # Padding
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 10),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def md_to_flowables(md_text, styles):
    """Convert markdown text string to a list of ReportLab flowables."""
    flowables = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Headings ──────────────────────────────────────────────────────────
        if stripped.startswith('### '):
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(
                apply_inline(escape_xml(stripped[4:])), styles["h3"]
            ))
            i += 1
            continue

        if stripped.startswith('## '):
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
            flowables.append(Spacer(1, 2))
            flowables.append(Paragraph(
                apply_inline(escape_xml(stripped[3:])), styles["h2"]
            ))
            i += 1
            continue

        if stripped.startswith('# '):
            title_text = escape_xml(stripped[2:])
            flowables.append(Paragraph(apply_inline(title_text), styles["h1"]))
            flowables.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE))
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # ── Code block & Mermaid Flowcharts ────────────────────────────────────────────────────────
        if stripped.startswith('```'):
            lang = stripped[3:].strip().lower()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_text = '\n'.join(code_lines)
            
            # --- Mermaid Injection ---
            if lang == 'mermaid':
                img_path = fetch_mermaid_image(code_text)
                if img_path:
                    try:
                        flowables.append(Spacer(1, 4))
                        img = ImageReader(img_path)
                        img_w, img_h = img.getSize()
                        # Constrain width to the pdf page bounds
                        max_w = A4[0] - 4 * cm
                        if img_w > max_w:
                            ratio = max_w / img_w
                            img_w = max_w
                            img_h = img_h * ratio
                        
                        flowables.append(Image(img_path, width=img_w, height=img_h))
                        flowables.append(Spacer(1, 6))
                        continue
                    except Exception as e:
                        print(f"Error drawing Mermaid image: {e}")
            
            # Fallback for normal code
            flowables.append(Spacer(1, 4))
            flowables.append(Preformatted(
                code_text,
                ParagraphStyle(
                    "pre", fontSize=8, leading=12,
                    fontName="Courier", textColor=CODE_TEXT,
                    backColor=CODE_BG, leftIndent=10,
                    borderPadding=(8, 12, 8, 12),
                )
            ))
            flowables.append(Spacer(1, 4))
            continue

        # ── Table ─────────────────────────────────────────────────────────────
        if stripped.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            rows = parse_table(table_lines)
            t = build_table_flowable(rows, styles)
            if t:
                flowables.append(Spacer(1, 4))
                flowables.append(t)
                flowables.append(Spacer(1, 6))
            continue

        # ── Blockquote ────────────────────────────────────────────────────────
        if stripped.startswith('>'):
            text = stripped.lstrip('> ').strip()
            flowables.append(Paragraph(
                apply_inline(escape_xml(text)), styles["blockquote"]
            ))
            i += 1
            continue

        # ── Horizontal Rule ───────────────────────────────────────────────────
        if stripped in ('---', '***', '___'):
            flowables.append(Spacer(1, 4))
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # ── Bullet list ───────────────────────────────────────────────────────
        if re.match(r'^[-*+] ', stripped):
            text = stripped[2:]
            flowables.append(Paragraph(
                "• " + apply_inline(escape_xml(text)), styles["bullet"]
            ))
            i += 1
            continue

        # ── Numbered list ─────────────────────────────────────────────────────
        if re.match(r'^\d+\. ', stripped):
            text = re.sub(r'^\d+\. ', '', stripped)
            flowables.append(Paragraph(
                apply_inline(escape_xml(text)), styles["bullet"]
            ))
            i += 1
            continue

        # ── Empty line ────────────────────────────────────────────────────────
        if stripped == '':
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # ── Regular paragraph ─────────────────────────────────────────────────
        flowables.append(Paragraph(
            apply_inline(escape_xml(stripped)), styles["body"]
        ))
        i += 1

    return flowables


def convert_resolved_to_pdf(input_path: str, output_path: str = None) -> str:
    """
    Convert a .resolved (Markdown) file to a PDF.

    Args:
        input_path:  Full path to the .resolved file
        output_path: Where to save the PDF. If None, saves next to the input.

    Returns:
        The absolute path to the generated PDF.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    # Default output path
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = base + ".pdf"

    with open(input_path, 'r', encoding='utf-8') as f:
        # Remove DOS carriage returns \r which render as black squares in PDF code blocks
        md_text = f.read().replace('\r', '')

    styles = build_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=os.path.basename(input_path),
        author="Resolved2PDF",
    )

    def header_footer(canvas, doc):
        canvas.saveState()
        w, h = A4
        # Header bar — dark navy
        canvas.setFillColor(HEADER_BAR)
        canvas.rect(0, h - 1.4 * cm, w, 1.4 * cm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(colors.HexColor("#93C5FD"))   # light blue on dark bar
        canvas.drawString(2 * cm, h - 0.95 * cm, os.path.basename(input_path))
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94A3B8"))   # light muted on dark bar
        canvas.drawRightString(w - 2 * cm, h - 0.95 * cm,
                               f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        # Thin accent line under header
        canvas.setStrokeColor(ACCENT_BLUE)
        canvas.setLineWidth(0.8)
        canvas.line(0, h - 1.4 * cm, w, h - 1.4 * cm)
        # Footer bar — dark navy
        canvas.setFillColor(HEADER_BAR)
        canvas.rect(0, 0, w, 1.1 * cm, fill=1, stroke=0)
        canvas.setStrokeColor(ACCENT_BLUE)
        canvas.line(0, 1.1 * cm, w, 1.1 * cm)
        
        # Left: Page Number
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawString(2 * cm, 0.42 * cm, f"Page {doc.page}")

        # Right: Branding and Link
        brand_text = "Converted by Resolved2PDF  |  "
        link_text = "resolved2pdf.com"
        
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        link_w = canvas.stringWidth(link_text, "Helvetica", 8)
        canvas.drawRightString(w - 2 * cm - link_w, 0.42 * cm, brand_text)
        
        canvas.setFillColor(colors.HexColor("#93C5FD")) # light blue link color
        canvas.drawRightString(w - 2 * cm, 0.42 * cm, link_text)
        
        # Make the link clickable
        x1 = w - 2 * cm - link_w
        y1 = 0.42 * cm - 4
        x2 = w - 2 * cm
        y2 = 0.42 * cm + 8
        canvas.linkURL("https://resolved2pdf.com", (x1, y1, x2, y2), relative=1)
        
        canvas.restoreState()

    content = md_to_flowables(md_text, styles)
    doc.build(content, onFirstPage=header_footer, onLaterPages=header_footer)

    return os.path.abspath(output_path)


def convert_to_pdf_bytes(md_text: str, filename: str = "document") -> bytes:
    """Convert markdown text to PDF and return as bytes (for HTTP response)."""
    # Remove DOS carriage returns
    md_text = md_text.replace('\r', '')
    
    buffer = io.BytesIO()
    styles = build_styles()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2.5*cm, bottomMargin=2.5*cm,
        title=filename, author="Resolved2PDF"
    )

    def header_footer(canvas, doc_obj):
        canvas.saveState()
        w, h = A4
        # Header bar
        canvas.setFillColor(HEADER_BAR)
        canvas.rect(0, h - 1.4*cm, w, 1.4*cm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(colors.HexColor("#93C5FD"))
        canvas.drawString(2*cm, h - 0.95*cm, filename)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawRightString(w - 2 * cm, h - 0.95 * cm,
                               f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        canvas.setStrokeColor(ACCENT_BLUE)
        canvas.setLineWidth(0.8)
        canvas.line(0, h - 1.4*cm, w, h - 1.4*cm)
        
        # Footer bar
        canvas.setFillColor(HEADER_BAR)
        canvas.rect(0, 0, w, 1.1*cm, fill=1, stroke=0)
        canvas.setStrokeColor(ACCENT_BLUE)
        canvas.line(0, 1.1*cm, w, 1.1*cm)
        
        # Left: Page Number
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawString(2 * cm, 0.42 * cm, f"Page {doc.page}")

        # Right: Branding and Link
        brand_text = "Converted by Resolved2PDF  |  "
        link_text = "resolved2pdf.com"
        
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        link_w = canvas.stringWidth(link_text, "Helvetica", 8)
        canvas.drawRightString(w - 2 * cm - link_w, 0.42 * cm, brand_text)
        
        canvas.setFillColor(colors.HexColor("#93C5FD"))
        canvas.drawRightString(w - 2 * cm, 0.42 * cm, link_text)
        
        # Make link clickable
        x1 = w - 2 * cm - link_w
        y1 = 0.42 * cm - 4
        x2 = w - 2 * cm
        y2 = 0.42 * cm + 8
        canvas.linkURL("https://resolved2pdf.com", (x1, y1, x2, y2), relative=1)
        
        canvas.restoreState()

    doc.build(md_to_flowables(md_text, styles), onFirstPage=header_footer, onLaterPages=header_footer)
    return buffer.getvalue()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python convert_resolved.py <file.resolved> [output.pdf]")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    result = convert_resolved_to_pdf(inp, out)
    print(f"✅  PDF saved to: {result}")
