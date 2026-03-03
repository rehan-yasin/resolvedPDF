"""
webapp/convert_resolved.py
--------------------------
Self-contained core engine for the web app.
Converts a .resolved (Markdown) file to PDF bytes.
"""

import re
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Preformatted, HRFlowable
)
from reportlab.lib.enums import TA_CENTER

# ── Color Palette (Professional Light Theme) ──────────────────────────────────
HEADER_BAR   = colors.HexColor("#1A1D2E")
ACCENT_BLUE  = colors.HexColor("#1E40AF")
ACCENT_GREEN = colors.HexColor("#16A34A")
ACCENT_YELL  = colors.HexColor("#92400E")
CODE_BG      = colors.HexColor("#F1F5F9")
CODE_TEXT    = colors.HexColor("#0F172A")
TABLE_HEADER = colors.HexColor("#1E3A5F")
TABLE_ROW1   = colors.HexColor("#FFFFFF")
TABLE_ROW2   = colors.HexColor("#F8FAFC")
TEXT_COLOR   = colors.HexColor("#0F172A")
MUTED        = colors.HexColor("#64748B")
BORDER       = colors.HexColor("#CBD5E1")
WHITE        = colors.white


def build_styles():
    styles = {}
    styles["h1"] = ParagraphStyle("h1", fontSize=22, leading=30, textColor=ACCENT_BLUE,
        fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=14)
    styles["h2"] = ParagraphStyle("h2", fontSize=15, leading=22, textColor=ACCENT_BLUE,
        fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=12)
    styles["h3"] = ParagraphStyle("h3", fontSize=12, leading=18, textColor=ACCENT_GREEN,
        fontName="Helvetica-Bold", spaceAfter=3, spaceBefore=8)
    styles["body"] = ParagraphStyle("body", fontSize=10, leading=16, textColor=TEXT_COLOR,
        fontName="Helvetica", spaceAfter=4)
    styles["bullet"] = ParagraphStyle("bullet", fontSize=10, leading=15, textColor=TEXT_COLOR,
        fontName="Helvetica", leftIndent=18, bulletIndent=6, spaceAfter=3)
    styles["blockquote"] = ParagraphStyle("blockquote", fontSize=10, leading=15,
        textColor=ACCENT_YELL, fontName="Helvetica-Oblique", leftIndent=20,
        borderPadding=(6, 10, 6, 10), spaceAfter=4,
        backColor=colors.HexColor("#FFFBEB"))
    styles["footer"] = ParagraphStyle("footer", fontSize=8, leading=10, textColor=MUTED,
        fontName="Helvetica", alignment=TA_CENTER)
    return styles


def escape_xml(text):
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def apply_inline(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#16A34A">\1</font>', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text


def parse_table(lines):
    rows = []
    for line in lines:
        line = line.strip()
        if re.match(r'^[\|\-\s:]+$', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cells)
    return rows


def build_table_flowable(rows, styles):
    if not rows:
        return None
    col_count = max(len(r) for r in rows)
    padded = [r + [''] * (col_count - len(r)) for r in rows]
    table_data = []
    for i, row in enumerate(padded):
        style = styles["h3"] if i == 0 else styles["body"]
        table_data.append([Paragraph(apply_inline(escape_xml(cell)), style) for cell in row])
    col_width = (A4[0] - 4 * cm) / col_count
    t = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  TABLE_HEADER),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0),  9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [TABLE_ROW1, TABLE_ROW2]),
        ("TEXTCOLOR",      (0, 1), (-1, -1), TEXT_COLOR),
        ("FONTNAME",       (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 1), (-1, -1), 9),
        ("GRID",           (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBELOW",      (0, 0), (-1, 0),  1.2, ACCENT_BLUE),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 10),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def md_to_flowables(md_text, styles):
    flowables = []
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith('### '):
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(apply_inline(escape_xml(stripped[4:])), styles["h3"]))
            i += 1; continue

        if stripped.startswith('## '):
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
            flowables.append(Spacer(1, 2))
            flowables.append(Paragraph(apply_inline(escape_xml(stripped[3:])), styles["h2"]))
            i += 1; continue

        if stripped.startswith('# '):
            flowables.append(Paragraph(apply_inline(escape_xml(stripped[2:])), styles["h1"]))
            flowables.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE))
            flowables.append(Spacer(1, 6))
            i += 1; continue

        if stripped.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1
            flowables.append(Spacer(1, 4))
            flowables.append(Preformatted('\n'.join(code_lines), ParagraphStyle(
                "pre", fontSize=8, leading=12, fontName="Courier", textColor=CODE_TEXT,
                backColor=CODE_BG, leftIndent=10, borderPadding=(8, 12, 8, 12))))
            flowables.append(Spacer(1, 4))
            continue

        if stripped.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i]); i += 1
            t = build_table_flowable(parse_table(table_lines), styles)
            if t:
                flowables.append(Spacer(1, 4)); flowables.append(t); flowables.append(Spacer(1, 6))
            continue

        if stripped.startswith('>'):
            flowables.append(Paragraph(apply_inline(escape_xml(stripped.lstrip('> ').strip())), styles["blockquote"]))
            i += 1; continue

        if stripped in ('---', '***', '___'):
            flowables.append(Spacer(1, 4))
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
            flowables.append(Spacer(1, 4))
            i += 1; continue

        if re.match(r'^[-*+] ', stripped):
            flowables.append(Paragraph("• " + apply_inline(escape_xml(stripped[2:])), styles["bullet"]))
            i += 1; continue

        if re.match(r'^\d+\. ', stripped):
            flowables.append(Paragraph(apply_inline(escape_xml(re.sub(r'^\d+\. ', '', stripped))), styles["bullet"]))
            i += 1; continue

        if stripped == '':
            flowables.append(Spacer(1, 4)); i += 1; continue

        flowables.append(Paragraph(apply_inline(escape_xml(stripped)), styles["body"]))
        i += 1

    return flowables


def convert_to_pdf_bytes(md_text: str, filename: str = "document") -> bytes:
    """Convert markdown text to PDF and return as bytes (for HTTP response)."""
    buffer = io.BytesIO()
    styles = build_styles()

    doc = SimpleDocTemplate(buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2.5*cm, bottomMargin=2.5*cm,
        title=filename, author="ResolvedPDF")

    def header_footer(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(HEADER_BAR)
        canvas.rect(0, h - 1.4*cm, w, 1.4*cm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(colors.HexColor("#93C5FD"))
        canvas.drawString(2*cm, h - 0.95*cm, filename)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawRightString(w - 2*cm, h - 0.95*cm,
                               f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · ResolvedPDF")
        canvas.setStrokeColor(ACCENT_BLUE)
        canvas.setLineWidth(0.8)
        canvas.line(0, h - 1.4*cm, w, h - 1.4*cm)
        canvas.setFillColor(HEADER_BAR)
        canvas.rect(0, 0, w, 1.1*cm, fill=1, stroke=0)
        canvas.setStrokeColor(ACCENT_BLUE)
        canvas.line(0, 1.1*cm, w, 1.1*cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawCentredString(w/2, 0.42*cm, f"Page {doc.page}  |  ResolvedPDF · resolvedpdf.com")
        canvas.restoreState()

    doc.build(md_to_flowables(md_text, styles), onFirstPage=header_footer, onLaterPages=header_footer)
    return buffer.getvalue()
