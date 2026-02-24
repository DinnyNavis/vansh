"""
PDF Generator Service — ReportLab-based print-ready PDF generation.
Creates elegant, book-formatted PDFs with cover page, chapters, and images.
"""

import os
import io
import logging
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    PageBreak,
    Table,
    TableStyle,
    Frame,
    PageTemplate,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# Color palette
# Color palette
MIDNIGHT = HexColor("#1A1A2E") # Signature Midnight
GOLD = HexColor("#C9A84C")
GOLD_LIGHT = HexColor("#E8D48B")
GOLD_DARK = HexColor("#A68A3E")
CHARCOAL = HexColor("#2D3436")
IVORY = HexColor("#FDFCF8")
CREAM = HexColor("#F7F5F0")
WARM_GRAY = HexColor("#636E72")

# Font Registration
def _register_fonts():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        fonts_dir = os.path.join(base_dir, "app", "assets", "fonts")
        
        pdfmetrics.registerFont(TTFont('PlayfairDisplay-Bold', os.path.join(fonts_dir, 'PlayfairDisplay-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('Inter-Regular', os.path.join(fonts_dir, 'Inter-Regular.ttf')))
        return True
    except Exception as e:
        logger.warning(f"Could not register custom fonts: {e}")
        return False

HAS_CUSTOM_FONTS = _register_fonts()
SERIF_BOLD = 'PlayfairDisplay-Bold' if HAS_CUSTOM_FONTS else 'Times-Bold'
SANS_REGULAR = 'Inter-Regular' if HAS_CUSTOM_FONTS else 'Helvetica'

def _build_styles():
    """Build custom paragraph styles for the book."""
    styles = getSampleStyleSheet()

    # Cover Styles
    styles.add(
        ParagraphStyle(
            "CoverCollection",
            parent=styles["Normal"],
            fontSize=9,
            textColor=GOLD_LIGHT,
            alignment=TA_CENTER,
            fontName=SANS_REGULAR,
            letterSpacing=4,
            spaceAfter=20,
        )
    )

    styles.add(
        ParagraphStyle(
            "BookTitle",
            parent=styles["Title"],
            fontSize=48,
            spaceAfter=30,
            textColor=GOLD_LIGHT,
            alignment=TA_CENTER,
            leading=56,
            fontName=SERIF_BOLD,
        )
    )

    styles.add(
        ParagraphStyle(
            "BookSubtitle",
            parent=styles["Normal"],
            fontSize=18,
            spaceAfter=40,
            textColor=IVORY,
            alignment=TA_CENTER,
            leading=26,
            fontName="Times-Italic",
            opacity=0.8,
        )
    )

    # Frontispiece Styles
    styles.add(
        ParagraphStyle(
            "Frontispiece",
            parent=styles["Normal"],
            fontSize=14,
            textColor=CHARCOAL,
            alignment=TA_CENTER,
            fontName=SERIF_BOLD,
            letterSpacing=2,
            spaceAfter=10,
        )
    )

    # ToC Styles
    styles.add(
        ParagraphStyle(
            "TOCHeader",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=MIDNIGHT,
            alignment=TA_LEFT,
            fontName=SERIF_BOLD,
            spaceAfter=30,
        )
    )

    styles.add(
        ParagraphStyle(
            "TOCEntry",
            parent=styles["Normal"],
            fontSize=11,
            textColor=CHARCOAL,
            alignment=TA_LEFT,
            fontName=SANS_REGULAR,
            leading=20,
        )
    )

    # Content Styles
    styles.add(
        ParagraphStyle(
            "ChapterNumLabel",
            parent=styles["Normal"],
            fontSize=8,
            textColor=GOLD,
            alignment=TA_LEFT,
            fontName=SANS_REGULAR,
            letterSpacing=3,
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            "ChapterTitle",
            parent=styles["Heading1"],
            fontSize=32,
            spaceBefore=0,
            spaceAfter=24,
            textColor=MIDNIGHT,
            alignment=TA_LEFT,
            leading=38,
            fontName=SERIF_BOLD,
        )
    )

    styles.add(
        ParagraphStyle(
            "BodyText_Custom",
            parent=styles["BodyText"],
            fontSize=12,
            spaceAfter=14,
            textColor=CHARCOAL,
            alignment=TA_JUSTIFY,
            leading=20,
            fontName="Times-Roman",
        )
    )

    styles.add(
        ParagraphStyle(
            "DropCap",
            parent=styles["Normal"],
            fontSize=50,
            textColor=GOLD,
            fontName=SERIF_BOLD,
            leading=40,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            "Flourish",
            parent=styles["Normal"],
            fontSize=24,
            textColor=GOLD,
            alignment=TA_CENTER,
            fontName="Times-Roman",
        )
    )

    return styles


class PDFGeneratorService:
    """Generates print-ready PDF books with "Golden Legacy" design."""

    def __init__(self, output_dir=None):
        self.output_dir = output_dir
        if not self.output_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.output_dir = os.path.join(base_dir, "uploads", "pdfs")
        
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_upload_dir = os.path.dirname(self.output_dir)
        self.current_project_title = "VANSH LEGACY"

    def _draw_background_and_border(self, canvas, doc):
        """Draw midnight background and luxury triple gold border for the cover."""
        canvas.saveState()
        
        # Draw Midnight background
        canvas.setFillColor(MIDNIGHT)
        canvas.rect(0, 0, A4[0], A4[1], fill=1)
        
        # Triple Border System
        # 1. Outer Double Gold Border (mimics 12px double)
        canvas.setStrokeColor(GOLD_DARK)
        canvas.setLineWidth(6)
        margin = 1 * cm
        canvas.rect(margin, margin, A4[0] - 2*margin, A4[1] - 2*margin)
        
        canvas.setStrokeColor(MIDNIGHT)
        canvas.setLineWidth(2)
        canvas.rect(margin + 2, margin + 2, A4[0] - 2*margin - 4, A4[1] - 2*margin - 4)
        
        # 2. Inner Gold Line (mimics outline-offset)
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(1)
        margin_inner = 1.8 * cm
        canvas.rect(margin_inner, margin_inner, A4[0] - 2*margin_inner, A4[1] - 2*margin_inner)
        
        # Decorative sparkles
        canvas.setFont(SERIF_BOLD if HAS_CUSTOM_FONTS else "Times-Roman", 14)
        canvas.setFillColor(GOLD_LIGHT)
        canvas.drawCentredString(A4[0]/2, A4[1] - 3.2*cm, "✧")
        canvas.drawCentredString(A4[0]/2, 3.2*cm, "✧")
        
        canvas.restoreState()

    def _add_page_decorations(self, canvas, doc):
        """Add page numbers, book title, and heritage branding to content pages."""
        page_num = canvas.getPageNumber()
        if page_num > 1:
            canvas.saveState()
            canvas.setFillColor(IVORY)
            canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            
            # Gutter effect (Soft gradient shadow)
            for i in range(20):
                alpha = 0.03 * (1 - i/20)
                canvas.setFillAlpha(alpha)
                canvas.setFillColor(HexColor("#000000"))
                canvas.rect(0.8*cm + (i*2), 0, 2, A4[1], stroke=0, fill=1)
            
            canvas.setFillAlpha(1.0)
            canvas.setStrokeAlpha(1.0)
            
            # Footer Line
            canvas.setStrokeColor(CHARCOAL)
            canvas.setLineWidth(0.5)
            canvas.setStrokeAlpha(0.1)
            canvas.line(doc.leftMargin, 2.2 * cm, A4[0] - doc.rightMargin, 2.2 * cm)
            
            # Footer Left: Book Title
            canvas.setFont(SANS_REGULAR, 8)
            canvas.setFillColor(CHARCOAL)
            canvas.setFillAlpha(0.5)
            canvas.drawString(doc.leftMargin, 1.6 * cm, self.current_project_title.upper())
            
            # Footer Center: Page Number with lines
            canvas.setFont("Times-Roman", 10)
            canvas.drawCentredString(A4[0] / 2, 1.6 * cm, f"— {page_num} —")
            
            # Footer Right: Heritage Branding
            canvas.setFont(SANS_REGULAR, 7)
            canvas.drawRightString(A4[0] - doc.rightMargin, 1.6 * cm, "VANSH HERITAGE STUDIO")
            
            canvas.restoreState()

    def _fetch_image(self, url_or_path, max_width=5.5 * inch, max_height=5 * inch):
        """Fetch and resize image for PDF embedding with museum-quality frame."""
        try:
            img_data = None
            if url_or_path.startswith(("http://", "https://")):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url_or_path, timeout=15, headers=headers)
                response.raise_for_status()
                img_data = io.BytesIO(response.content)
            elif url_or_path.startswith("/api/unguided/images/"):
                filename = url_or_path.split("/")[-1]
                local_path = os.path.join(self.base_upload_dir, "images", filename)
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        img_data = io.BytesIO(f.read())
            elif os.path.exists(url_or_path):
                with open(url_or_path, "rb") as f:
                    img_data = io.BytesIO(f.read())
            
            if not img_data:
                return None

            img = RLImage(img_data)
            ratio = min(max_width / img.drawWidth, max_height / img.drawHeight)
            img.drawWidth *= ratio
            img.drawHeight *= ratio
            
            # Museum-quality frame (White box with subtle grey ring)
            return Table([[img]], style=[
                ('BOX', (0,0), (-1,-1), 8, HexColor("#FFFFFF")), # Thicker white frame
                ('BOX', (0,0), (-1,-1), 0.2, HexColor("#CCCCCC")), # Very thin grey outer ring
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ])
        except Exception as e:
            logger.warning(f"Could not load image {url_or_path}: {e}")
            return None

    def _create_drop_cap_para(self, content, styles):
        """Create a paragraph with a large drop cap and perfect alignment."""
        if not content: return []
        
        first_letter = content[0]
        remaining_text = content[1:]
        
        # We use a Table to align the drop cap
        data = [[
            Paragraph(first_letter, styles["DropCap"]),
            Paragraph(remaining_text, styles["BodyText_Custom"])
        ]]
        
        # Tighter column for more natural feel
        t = Table(data, colWidths=[0.5 * inch, None], spaceBefore=10)
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        return [t]

    def _draw_frontispiece(self, canvas, doc):
        """Draw minimalist white frontispiece."""
        canvas.saveState()
        canvas.setFillColor(IVORY)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.restoreState()

    def generate(self, project_data, filename=None):
        """Generate a complete PDF book with professional structure and ToC."""
        self.current_project_title = project_data.get("cover_title", "VANSH LEGACY")
        
        if not filename:
            title_slug = self.current_project_title.lower().replace(" ", "_")[:30]
            filename = f"{title_slug}.pdf"

        output_path = os.path.join(self.output_dir, filename)
        styles = _build_styles()

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2.5 * cm,
            leftMargin=2.5 * cm,
            topMargin=3 * cm,
            bottomMargin=3 * cm,
        )

        # ToC Tracking
        toc_entries = []
        
        story = []

        # ========== 1. Frontispiece (Minimalist Title Page) ==========
        story.append(Spacer(1, 8 * cm))
        story.append(Paragraph(self.current_project_title.upper(), styles["Frontispiece"]))
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph("A VANSH PUBLICATION", styles["CoverCollection"]))
        story.append(PageBreak())

        # ========== 2. Luxury Cover Page ==========
        # (This will be handled by onFirstPage/PageTemplate if we keep that logic, 
        # but for better structure we use templates)
        story.append(Spacer(1, 4 * cm))
        story.append(Paragraph("A VANSH LEGACY COLLECTION", styles["CoverCollection"]))
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph(self.current_project_title.upper(), styles["BookTitle"]))
        
        subtitle = project_data.get("cover_subtitle") or project_data.get("subtitle", "")
        if subtitle:
            story.append(Spacer(1, 0.4 * inch))
            line = Table([[""]], colWidths=[1.8 * inch])
            line.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, GOLD)]))
            story.append(line)
            story.append(Spacer(1, 0.4 * inch))
            story.append(Paragraph(subtitle, styles["BookSubtitle"]))

        story.append(Spacer(1, 9 * cm))
        story.append(Paragraph("✧", styles["CoverCollection"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("ESTABLISHED MCMLXX / MMXXIV", styles["CoverCollection"]))
        story.append(PageBreak())

        # ========== 3. Table of Contents ==========
        story.append(Paragraph("Contents", styles["TOCHeader"]))
        story.append(Spacer(1, 20))
        
        chapters = project_data.get("chapters", [])
        for idx, chapter in enumerate(chapters):
            ch_title = chapter.get("chapter_title", f"Chapter {idx + 1}")
            # ToC Entry with dot leader (simulated with table and spaces for now/standard layout)
            toc_text = f"<b>{idx + 1}</b> &nbsp;&nbsp; {ch_title}"
            story.append(Paragraph(toc_text, styles["TOCEntry"]))
            story.append(Spacer(1, 12))
        
        story.append(PageBreak())

        # ========== 4. Main Chapters ==========
        for idx, chapter in enumerate(chapters):
            # Chapter Label with tailing line
            chapter_label = Paragraph(f"CHAPTER {idx + 1}", styles["ChapterNumLabel"])
            label_table = Table([[chapter_label, ""]], colWidths=[1.2 * inch, None])
            label_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LINEBELOW', (1,0), (1,0), 0.5, GOLD_LIGHT),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(label_table)
            story.append(Spacer(1, 10))
            
            # Chapter Title
            story.append(Paragraph(chapter.get("chapter_title", f"Chapter {idx + 1}"), styles["ChapterTitle"]))
            
            # Gold separator
            sep = Table([[""]], colWidths=[1.5 * inch])
            sep.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 1.5, GOLD)]))
            story.append(sep)
            story.append(Spacer(1, 30))

            # Image
            image_url = chapter.get("image_url")
            if image_url:
                img_table = self._fetch_image(image_url)
                if img_table:
                    story.append(img_table)
                    story.append(Spacer(1, 40))

            # Content with Drop Cap
            content = chapter.get("content", "")
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
            
            for p_idx, para_text in enumerate(paragraphs):
                if p_idx == 0:
                    story.extend(self._create_drop_cap_para(para_text, styles))
                else:
                    story.append(Paragraph(para_text, styles["BodyText_Custom"]))

            # Ornamental Flourish with Lines
            story.append(Spacer(1, 50)) # Fixed vertical rhythm
            
            divider_line = Table([[""]], colWidths=[1.8 * inch])
            divider_line.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.5, GOLD)]))
            
            fleur_para = Paragraph("❧", styles["Flourish"])
            fleur_table = Table([[divider_line, fleur_para, divider_line]], 
                                colWidths=[1.8 * inch, 0.4 * inch, 1.8 * inch])
            fleur_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(fleur_table)
            story.append(PageBreak())

        # Page Template Callbacks
        def on_page_logic(canvas, doc):
            page_num = canvas.getPageNumber()
            if page_num == 1:
                self._draw_frontispiece(canvas, doc)
            elif page_num == 2:
                self._draw_background_and_border(canvas, doc)
            else:
                self._add_page_decorations(canvas, doc)

        doc.build(story, onFirstPage=on_page_logic, onLaterPages=on_page_logic)
        return output_path
