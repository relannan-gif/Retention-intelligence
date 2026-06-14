#!/usr/bin/env python3
"""
generate_pdf.py — Professional PDF generator for the OneRoyal Client Intelligence Platform
Handover Manual. Uses ReportLab Platypus for board-grade output.
"""

import re
import os
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, PageBreak, HRFlowable, KeepTogether, NextPageTemplate,
    FrameBreak,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable

# ── Brand colours ─────────────────────────────────────────────────────────────
C_GOLD   = colors.HexColor("#F0B429")
C_DARK   = colors.HexColor("#0A0E1A")
C_NAVY   = colors.HexColor("#0F1629")
C_CARD   = colors.HexColor("#141B2D")
C_BORDER = colors.HexColor("#1E2D4A")
C_TEXT   = colors.HexColor("#E8E8E8")
C_MUTED  = colors.HexColor("#94A3B8")
C_RED    = colors.HexColor("#EF4444")
C_GREEN  = colors.HexColor("#10B981")
C_AMBER  = colors.HexColor("#F59E0B")
C_BLUE   = colors.HexColor("#3B82F6")
C_PURPLE = colors.HexColor("#8B5CF6")

# Light equivalents for table backgrounds on white pages
C_TH_BG    = colors.HexColor("#0F1629")   # table header bg
C_TR_ALT   = colors.HexColor("#EEF3FA")   # alternating row
C_TR_WHITE = colors.white
C_BODY_BG  = colors.white
C_BODY_TXT = colors.HexColor("#1A1F36")
C_SECTION  = colors.HexColor("#0A0E1A")

PAGE_W, PAGE_H = A4  # 595.28 × 841.89 pt

# ── Page geometry ──────────────────────────────────────────────────────────────
MARGIN_L = 2.0 * cm
MARGIN_R = 2.0 * cm
MARGIN_T = 2.2 * cm
MARGIN_B = 2.2 * cm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# ── Styles ─────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    def S(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    styles = {
        # Cover
        "CoverTitle":    S("CoverTitle",    fontSize=28, textColor=C_GOLD,
                            fontName="Helvetica-Bold", alignment=TA_LEFT,
                            leading=34, spaceAfter=8),
        "CoverSubtitle": S("CoverSubtitle", fontSize=16, textColor=C_TEXT,
                            fontName="Helvetica", alignment=TA_LEFT,
                            leading=22, spaceAfter=6),
        "CoverMeta":     S("CoverMeta",     fontSize=10, textColor=C_MUTED,
                            fontName="Helvetica", alignment=TA_LEFT, leading=16),
        "CoverConfidential": S("CoverConfidential", fontSize=9, textColor=C_RED,
                            fontName="Helvetica-Bold", alignment=TA_LEFT),

        # Body
        "Body":          S("Body",          fontSize=9.5, textColor=C_BODY_TXT,
                            fontName="Helvetica", leading=14, spaceAfter=6,
                            alignment=TA_JUSTIFY),
        "BodyMono":      S("BodyMono",      fontSize=8.5, textColor=C_BODY_TXT,
                            fontName="Courier", leading=13, spaceAfter=4),

        # Headings
        "H1":            S("H1", fontSize=18, textColor=C_DARK,
                            fontName="Helvetica-Bold", spaceBefore=18,
                            spaceAfter=10, leading=22,
                            borderPad=4, backColor=colors.HexColor("#F4F6FC")),
        "H2":            S("H2", fontSize=13, textColor=C_GOLD,
                            fontName="Helvetica-Bold", spaceBefore=14,
                            spaceAfter=6, leading=17),
        "H3":            S("H3", fontSize=11, textColor=C_BODY_TXT,
                            fontName="Helvetica-Bold", spaceBefore=10,
                            spaceAfter=4, leading=14),
        "H4":            S("H4", fontSize=10, textColor=C_BODY_TXT,
                            fontName="Helvetica-Bold", spaceBefore=8,
                            spaceAfter=3, leading=13),

        # Code block
        "Code":          S("Code", fontSize=8, textColor=colors.HexColor("#1E3A5F"),
                            fontName="Courier", leading=11, spaceAfter=2,
                            backColor=colors.HexColor("#F0F4FA"),
                            leftIndent=8, rightIndent=8, borderPad=6),

        # Caution / info
        "Caution":       S("Caution", fontSize=9, textColor=colors.HexColor("#7C2D12"),
                            fontName="Helvetica-Bold", leading=13,
                            backColor=colors.HexColor("#FEF3C7"),
                            leftIndent=8, borderPad=6, spaceAfter=6),
        "Info":          S("Info", fontSize=9, textColor=colors.HexColor("#1E3A5F"),
                            fontName="Helvetica", leading=13,
                            backColor=colors.HexColor("#EFF6FF"),
                            leftIndent=8, borderPad=6, spaceAfter=6),

        # Bullet
        "Bullet":        S("Bullet", fontSize=9.5, textColor=C_BODY_TXT,
                            fontName="Helvetica", leading=13, spaceAfter=3,
                            leftIndent=12, firstLineIndent=-10),

        # TOC
        "TOC1":          S("TOC1", fontSize=11, textColor=C_BODY_TXT,
                            fontName="Helvetica-Bold", leading=15, spaceAfter=3),
        "TOC2":          S("TOC2", fontSize=10, textColor=C_BODY_TXT,
                            fontName="Helvetica", leading=14, leftIndent=16, spaceAfter=2),

        # Footer/header
        "Footer":        S("Footer", fontSize=8, textColor=C_MUTED,
                            fontName="Helvetica", leading=10),

        # Section label on H1
        "SectionLabel":  S("SectionLabel", fontSize=9, textColor=C_MUTED,
                            fontName="Helvetica-BoldOblique", leading=12,
                            spaceAfter=2),

        # Document control table
        "DocCtrl":       S("DocCtrl", fontSize=9.5, textColor=C_BODY_TXT,
                            fontName="Helvetica", leading=13),
        "DocCtrlBold":   S("DocCtrlBold", fontSize=9.5, textColor=C_BODY_TXT,
                            fontName="Helvetica-Bold", leading=13),

        # Caption
        "Caption":       S("Caption", fontSize=8.5, textColor=C_MUTED,
                            fontName="Helvetica-Oblique", leading=12,
                            alignment=TA_CENTER, spaceAfter=6),
    }
    return styles

ST = build_styles()

# ── Table helpers ──────────────────────────────────────────────────────────────
def make_table(rows, col_widths=None, header=True, small=False):
    """Build a styled Platypus Table from a list-of-list rows."""
    fsize = 8 if small else 9
    data = []
    for ri, row in enumerate(rows):
        data.append([
            Paragraph(str(cell), ParagraphStyle(
                f"tc_{ri}_{ci}",
                fontSize=fsize,
                fontName="Helvetica-Bold" if (ri == 0 and header) else "Helvetica",
                textColor=C_TEXT if (ri == 0 and header) else C_BODY_TXT,
                leading=fsize + 3,
                wordWrap="LTR",
            ))
            for ci, cell in enumerate(row)
        ])

    if col_widths is None:
        n = len(rows[0]) if rows else 1
        col_widths = [CONTENT_W / n] * n

    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)

    style_cmds = [
        ("BACKGROUND",  (0, 0), (-1, 0 if header else -1),
         C_TH_BG if header else C_TR_WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_TR_WHITE, C_TR_ALT]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D9E6")),
        ("LINEBELOW",   (0, 0), (-1, 0),   1.2, C_GOLD if header else C_BORDER),
        ("FONTSIZE",    (0, 0), (-1, -1), fsize),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


def make_kv_table(pairs, label_w=None):
    """Two-column key-value table."""
    if label_w is None:
        label_w = CONTENT_W * 0.35
    data = [[
        Paragraph(f"<b>{k}</b>", ParagraphStyle("kv_k", fontSize=9,
                  fontName="Helvetica-Bold", textColor=C_BODY_TXT, leading=13)),
        Paragraph(str(v), ParagraphStyle("kv_v", fontSize=9,
                  fontName="Helvetica", textColor=C_BODY_TXT, leading=13)),
    ] for k, v in pairs]
    t = Table(data, colWidths=[label_w, CONTENT_W - label_w])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_TR_WHITE, C_TR_ALT]),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D9E6")),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def divider(color=C_GOLD, thickness=1.0, top=6, bot=6):
    return [
        Spacer(1, top),
        HRFlowable(width=CONTENT_W, thickness=thickness, color=color,
                   spaceAfter=bot, lineCap="round"),
    ]


# ── Architecture diagrams (drawn with ReportLab graphics) ─────────────────────
class ArchDiagram(Flowable):
    """Architecture stack diagram."""
    def __init__(self, width=CONTENT_W, height=200):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        layers = [
            ("PRESENTATION LAYER  (pages/)",
             "1_Executive_Dashboard · 2_Client_List · 3_Scoring_Engine\n"
             "4_Action_Center · 5_Settings · 6_Data_Management · 7_Model_Validation",
             C_NAVY),
            ("BUSINESS LOGIC LAYER  (utils/)",
             "helpers.py · scoring.py · rules_engine.py\n"
             "snapshot_db.py · data_manager.py · session_init.py",
             colors.HexColor("#0D1B35")),
            ("CONFIGURATION LAYER  (config/)",
             "theme.py · scoring_rules.json",
             colors.HexColor("#0A1628")),
            ("INTEGRATION LAYER  (integrations/)",
             "data_validator.py · data_mapper.py · crm_connector.py · holistics_connector.py",
             colors.HexColor("#0F1E3C")),
            ("DATA LAYER",
             "data/sample_data.py · data/snapshots.db (SQLite)",
             colors.HexColor("#091224")),
        ]
        n = len(layers)
        layer_h = (self.height - 30) / n
        # Title
        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.setFillColor(C_GOLD)
        self.canv.drawString(0, self.height - 14, "OneRoyal Client Intelligence Platform — Application Stack")

        for i, (title, desc, bg) in enumerate(layers):
            y = self.height - 30 - (i + 1) * layer_h
            # Box
            self.canv.setFillColor(bg)
            self.canv.roundRect(0, y, self.width, layer_h - 3, 4, fill=1, stroke=0)
            # Gold left accent
            self.canv.setFillColor(C_GOLD)
            self.canv.rect(0, y, 3, layer_h - 3, fill=1, stroke=0)
            # Title
            self.canv.setFont("Helvetica-Bold", 8)
            self.canv.setFillColor(C_GOLD)
            self.canv.drawString(10, y + layer_h - 17, title)
            # Desc
            self.canv.setFont("Helvetica", 7.5)
            self.canv.setFillColor(C_MUTED)
            lines = desc.split("\n")
            for li, line in enumerate(lines):
                self.canv.drawString(10, y + layer_h - 28 - li * 11, line)


class DataFlowDiagram(Flowable):
    """Linear data flow diagram."""
    def __init__(self, width=CONTENT_W, height=120):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        nodes = [
            ("Data\nSource", C_NAVY),
            ("data_mapper\n.py", colors.HexColor("#0D1B35")),
            ("data_validator\n.py", colors.HexColor("#0A1628")),
            ("scoring.py\nrules_engine.py", C_GOLD),
            ("session_state\n[scored_df]", colors.HexColor("#0F1E3C")),
            ("Dashboard\nAction Center\nClient List", colors.HexColor("#091224")),
        ]
        box_w = (self.width - 30) / len(nodes)
        box_h = 55
        y_center = self.height / 2

        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.setFillColor(C_GOLD)
        self.canv.drawString(0, self.height - 12, "Data Flow: Source → Scoring Engine → Dashboard")

        for i, (label, bg) in enumerate(nodes):
            x = i * (box_w + 5)
            y = y_center - box_h / 2
            self.canv.setFillColor(bg)
            self.canv.roundRect(x, y, box_w - 2, box_h, 5, fill=1, stroke=0)
            if bg == C_GOLD:
                self.canv.setFillColor(C_DARK)
            else:
                self.canv.setFillColor(C_TEXT)
            self.canv.setFont("Helvetica-Bold", 7)
            lines = label.split("\n")
            for li, line in enumerate(lines):
                lw = self.canv.stringWidth(line, "Helvetica-Bold", 7)
                self.canv.drawString(x + (box_w - 2 - lw) / 2,
                                     y + box_h / 2 + 4 - li * 10, line)
            # Arrow
            if i < len(nodes) - 1:
                ax = x + box_w - 2
                self.canv.setFillColor(C_GOLD)
                self.canv.setStrokeColor(C_GOLD)
                self.canv.setLineWidth(1.5)
                self.canv.line(ax, y_center, ax + 5, y_center)
                # Arrowhead
                self.canv.setFillColor(C_GOLD)
                p = self.canv.beginPath()
                p.moveTo(ax + 5, y_center)
                p.lineTo(ax + 2, y_center + 3)
                p.lineTo(ax + 2, y_center - 3)
                p.close()
                self.canv.drawPath(p, fill=1, stroke=0)


class ScoringMatrix(Flowable):
    """3×3 segmentation matrix."""
    def __init__(self, width=CONTENT_W, height=200):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        cells = [
            ["Save Immediately",      "Senior Retention Review",  "Automated Retention"],
            ["Proactive Nurture",      "Standard Nurture",         "Light Touch"],
            ["VIP Expansion",          "Growth Program",           "Monitor"],
        ]
        col_labels = ["High Value", "Medium Value", "Low Value"]
        row_labels  = ["High Risk", "Medium Risk", "Low Risk"]
        cell_colors = [
            [C_RED,  colors.HexColor("#F97316"), C_AMBER],
            [C_AMBER, C_BLUE, colors.HexColor("#64748B")],
            [C_GREEN, colors.HexColor("#22C55E"), colors.HexColor("#94A3B8")],
        ]

        label_w = 60
        cell_w = (self.width - label_w) / 3
        header_h = 24
        cell_h = (self.height - header_h - 14) / 3

        # Title
        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.setFillColor(C_GOLD)
        self.canv.drawString(0, self.height - 12, "9-Segment Client Matrix: Risk × Value")

        # Column headers
        for ci, cl in enumerate(col_labels):
            x = label_w + ci * cell_w
            self.canv.setFillColor(C_NAVY)
            self.canv.rect(x, self.height - header_h - 14, cell_w - 2, header_h - 2, fill=1, stroke=0)
            self.canv.setFont("Helvetica-Bold", 7.5)
            self.canv.setFillColor(C_GOLD)
            cw = self.canv.stringWidth(cl, "Helvetica-Bold", 7.5)
            self.canv.drawString(x + (cell_w - 2 - cw) / 2, self.height - header_h - 14 + 6, cl)

        for ri in range(3):
            ry = self.height - header_h - 14 - (ri + 1) * cell_h
            # Row label
            self.canv.setFillColor(C_NAVY)
            self.canv.rect(0, ry, label_w - 4, cell_h - 2, fill=1, stroke=0)
            self.canv.setFont("Helvetica-Bold", 7)
            self.canv.setFillColor(C_TEXT)
            rlw = self.canv.stringWidth(row_labels[ri], "Helvetica-Bold", 7)
            self.canv.drawString((label_w - 4 - rlw) / 2, ry + cell_h / 2 - 4, row_labels[ri])
            # Cells
            for ci in range(3):
                x = label_w + ci * cell_w
                bg = cell_colors[ri][ci]
                self.canv.setFillColor(bg)
                self.canv.roundRect(x, ry, cell_w - 3, cell_h - 3, 4, fill=1, stroke=0)
                txt = cells[ri][ci]
                self.canv.setFont("Helvetica-Bold", 7)
                self.canv.setFillColor(colors.white)
                tw = self.canv.stringWidth(txt, "Helvetica-Bold", 7)
                if tw > cell_w - 10:
                    words = txt.split()
                    mid = len(words) // 2
                    l1 = " ".join(words[:mid])
                    l2 = " ".join(words[mid:])
                    for li, ln in enumerate([l1, l2]):
                        lw2 = self.canv.stringWidth(ln, "Helvetica-Bold", 7)
                        self.canv.drawString(x + (cell_w - lw2) / 2, ry + cell_h / 2 - 4 + (1 - li) * 8, ln)
                else:
                    self.canv.drawString(x + (cell_w - tw) / 2, ry + cell_h / 2 - 4, txt)


class ScoreFormulaBox(Flowable):
    """Visual formula boxes for all 6 scores."""
    def __init__(self, width=CONTENT_W, height=260):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        scores = [
            ("Retention Risk Score",   "#EF4444",
             "Σ weight × band_score(signal) → min-max 0–100\n"
             "Signals: Withdrawal Pressure · Volume Drop · Login Inactivity\n"
             "         Deposit Inactivity · Complaints · Equity Erosion · Equity Trend"),
            ("Commercial Value Score", "#F0B429",
             "Σ weight × band_score(component) → min-max 0–100\n"
             "Factors: Lifetime Deposits · Net Deposits · Current Equity\n"
             "         Volume · Redeposits · Tenure · VIP Status (×9)"),
            ("Profitability Score",    "#10B981",
             "A-Book: spread + commission + swap\n"
             "B-Book: captured_losses + commission + swap + spread\n"
             "M-Book: (0.6 × captured_losses) + spread + commission + swap → min-max 0–100"),
            ("Client Health Score",    "#3B82F6",
             "(100 − risk_score) × 0.50\n"
             "+ commercial_value_score × 0.30\n"
             "+ profitability_score × 0.20"),
            ("Priority Score",         "#8B5CF6",
             "risk_score × 0.30\n"
             "+ commercial_value_score × 0.25\n"
             "+ profitability_score × 0.30\n"
             "+ reactivation_score × 0.15"),
            ("Reactivation Score",     "#F59E0B",
             "Non-linear login window (peaks at 105 days)\n"
             "+ lifetime_deposits + redeposits + vol_90d + tenure"),
        ]
        n = len(scores)
        box_w = (self.width - 8) / 2
        box_h = (self.height - 20) / 3

        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.setFillColor(C_GOLD)
        self.canv.drawString(0, self.height - 12, "Scoring Engine — Formula Reference")

        for i, (name, clr, formula) in enumerate(scores):
            col = i % 2
            row = i // 2
            x = col * (box_w + 8)
            y = self.height - 20 - (row + 1) * box_h
            # Box bg
            self.canv.setFillColor(colors.HexColor("#F4F6FC"))
            self.canv.roundRect(x, y + 4, box_w - 4, box_h - 8, 5, fill=1, stroke=0)
            # Accent strip
            self.canv.setFillColor(colors.HexColor(clr))
            self.canv.roundRect(x, y + 4, 5, box_h - 8, 3, fill=1, stroke=0)
            # Title
            self.canv.setFont("Helvetica-Bold", 8)
            self.canv.setFillColor(colors.HexColor(clr))
            self.canv.drawString(x + 12, y + box_h - 16, name)
            # Formula
            self.canv.setFont("Courier", 6.5)
            self.canv.setFillColor(C_BODY_TXT)
            lines = formula.split("\n")
            for li, line in enumerate(lines):
                self.canv.drawString(x + 12, y + box_h - 28 - li * 9, line)


class ActionDecisionTree(Flowable):
    """11-rule action decision tree diagram."""
    def __init__(self, width=CONTENT_W, height=320):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        rules = [
            (1, "VIP + High Risk + High Value", "URGENT: VIP Retention — Escalate", "#EF4444", "Management Review"),
            (2, "High Risk + High Value + High Profitability", "Immediate Retention Call", "#EF4444", "Retention Team"),
            (3, "≥2 Complaints + High Risk", "Resolve Complaints + Retention Review", "#F97316", "Retention Team"),
            (4, "Large Withdrawal + High Risk", "Retention Call: Withdrawal Alert", "#F97316", "Account Manager"),
            (5, "High Risk (any)", "Retention Follow-Up", "#F59E0B", "Account Manager"),
            (6, "VIP + Low Risk + High Value", "VIP Expansion Offer", "#F0B429", "VIP Team"),
            (7, "VIP Upside ≥65 + Not VIP", "VIP Upsell Opportunity", "#10B981", "Sales Team"),
            (8, "Reactivation ≥65 + Dormant", "Reactivation Campaign", "#3B82F6", "Sales Team"),
            (9, "Volume Drop >50% + Risk ≥35", "Re-engagement: Trading Incentive", "#8B5CF6", "Account Manager"),
            (10, "≥1 Complaint", "Complaint Resolution", "#94A3B8", "Account Manager"),
            (11, "Default", "Monitor Only", "#64748B", "Account Manager"),
        ]

        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.setFillColor(C_GOLD)
        self.canv.drawString(0, self.height - 12, "Action Routing — 11-Rule Decision Tree (First Match Wins)")

        row_h = (self.height - 22) / len(rules)
        col_x = [0, self.width * 0.05, self.width * 0.42, self.width * 0.72]
        col_labels = ["#", "Condition", "Assigned Action", "Owner"]

        # Header
        self.canv.setFillColor(C_NAVY)
        self.canv.rect(0, self.height - 22 - row_h * 0.8, self.width, row_h * 0.8, fill=1, stroke=0)
        self.canv.setFont("Helvetica-Bold", 7)
        self.canv.setFillColor(C_GOLD)
        for ci, cl in enumerate(col_labels):
            self.canv.drawString(col_x[ci] + 2, self.height - 22 - row_h * 0.8 + 5, cl)

        for i, (num, cond, action, clr, owner) in enumerate(rules):
            y = self.height - 22 - (i + 1.8) * row_h
            bg = colors.HexColor("#F4F6FC") if i % 2 == 0 else colors.white
            self.canv.setFillColor(bg)
            self.canv.rect(0, y, self.width, row_h - 1, fill=1, stroke=0)
            # Priority number badge
            self.canv.setFillColor(colors.HexColor(clr))
            self.canv.roundRect(col_x[0], y + 2, 14, row_h - 5, 3, fill=1, stroke=0)
            self.canv.setFont("Helvetica-Bold", 7)
            self.canv.setFillColor(colors.white)
            self.canv.drawString(col_x[0] + 4, y + 5, str(num))
            # Condition
            self.canv.setFont("Helvetica", 7)
            self.canv.setFillColor(C_BODY_TXT)
            self.canv.drawString(col_x[1] + 2, y + 5, cond)
            # Action
            self.canv.setFont("Helvetica-Bold", 7)
            self.canv.setFillColor(colors.HexColor(clr))
            self.canv.drawString(col_x[2] + 2, y + 5, action)
            # Owner
            self.canv.setFont("Helvetica", 7)
            self.canv.setFillColor(C_MUTED)
            self.canv.drawString(col_x[3] + 2, y + 5, owner)


class RoadmapDiagram(Flowable):
    """5-phase implementation roadmap timeline."""
    def __init__(self, width=CONTENT_W, height=130):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        phases = [
            ("Phase 1", "Pilot", "NOW", "#10B981"),
            ("Phase 2", "Production\nData Connect", "Q3 2026", "#F0B429"),
            ("Phase 3", "CRM API\nIntegration", "Q4 2026", "#3B82F6"),
            ("Phase 4", "Automation\n& Alerting", "Q1 2027", "#8B5CF6"),
            ("Phase 5", "AI-Driven\nRecoms", "Q2 2027", "#EF4444"),
        ]
        n = len(phases)
        node_r = 18
        spacing = (self.width - 2 * node_r) / (n - 1)
        line_y = self.height / 2

        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.setFillColor(C_GOLD)
        self.canv.drawString(0, self.height - 12, "Implementation Roadmap — 5 Phases")

        # Connecting line
        self.canv.setStrokeColor(colors.HexColor("#D1D9E6"))
        self.canv.setLineWidth(2)
        self.canv.line(node_r, line_y, self.width - node_r, line_y)

        for i, (phase, label, timeline, clr) in enumerate(phases):
            cx = node_r + i * spacing
            # Circle
            self.canv.setFillColor(colors.HexColor(clr))
            self.canv.circle(cx, line_y, node_r, fill=1, stroke=0)
            # Phase number
            self.canv.setFont("Helvetica-Bold", 8)
            self.canv.setFillColor(colors.white)
            pw = self.canv.stringWidth(phase, "Helvetica-Bold", 8)
            self.canv.drawString(cx - pw / 2, line_y - 3, phase)
            # Label below
            self.canv.setFont("Helvetica", 7)
            self.canv.setFillColor(C_BODY_TXT)
            for li, ln in enumerate(label.split("\n")):
                lw = self.canv.stringWidth(ln, "Helvetica", 7)
                self.canv.drawString(cx - lw / 2, line_y - node_r - 10 - li * 9, ln)
            # Timeline above
            self.canv.setFont("Helvetica-BoldOblique", 7)
            self.canv.setFillColor(colors.HexColor(clr))
            tw = self.canv.stringWidth(timeline, "Helvetica-BoldOblique", 7)
            self.canv.drawString(cx - tw / 2, line_y + node_r + 4, timeline)


# ── Page templates ─────────────────────────────────────────────────────────────
class HeaderFooterCanvas:
    """Mixin that adds header/footer to regular pages."""
    def __init__(self, doc):
        self._doc = doc

    def on_page(self, canvas, doc):
        canvas.saveState()
        # Header line
        canvas.setStrokeColor(C_GOLD)
        canvas.setLineWidth(0.7)
        canvas.line(MARGIN_L, PAGE_H - MARGIN_T + 4,
                    PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 4)
        # Header left
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.setFillColor(C_NAVY)
        canvas.drawString(MARGIN_L, PAGE_H - MARGIN_T + 7,
                          "OneRoyal Client Intelligence Platform — Handover Manual")
        # Header right (section)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawRightString(PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 7,
                               getattr(doc, "_current_section", ""))
        # Footer line
        canvas.line(MARGIN_L, MARGIN_B - 4,
                    PAGE_W - MARGIN_R, MARGIN_B - 4)
        # Footer left
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(MARGIN_L, MARGIN_B - 14,
                          "INTERNAL — CONFIDENTIAL  |  OneRoyal Group  |  v1.0  |  June 2026")
        # Footer right (page number)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.setFillColor(C_NAVY)
        canvas.drawRightString(PAGE_W - MARGIN_R, MARGIN_B - 14,
                               f"Page {doc.page}")
        canvas.restoreState()


class OneRoyalDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        self._current_section = ""
        self._toc_entries = []

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            txt = flowable.getPlainText()
            if style_name == "H1":
                self._current_section = txt[:60]
                self.notify("TOCEntry", (0, txt, self.page))
            elif style_name == "H2":
                self.notify("TOCEntry", (1, txt, self.page))


def build_frames(has_header_footer=True):
    """Content frame for regular body pages."""
    return Frame(
        MARGIN_L, MARGIN_B,
        CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )


# ── Page callbacks ──────────────────────────────────────────────────────────────
def cover_page_cb(canvas, doc):
    canvas.saveState()
    # Dark background
    canvas.setFillColor(C_DARK)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Gold top band
    canvas.setFillColor(C_GOLD)
    canvas.rect(0, PAGE_H - 8, PAGE_W, 8, fill=1, stroke=0)
    # Gold left accent strip
    canvas.rect(0, 0, 6, PAGE_H, fill=1, stroke=0)
    # Bottom band
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, 0, PAGE_W, 90, fill=1, stroke=0)
    canvas.setFillColor(C_GOLD)
    canvas.rect(6, 0, PAGE_W - 6, 4, fill=1, stroke=0)
    canvas.restoreState()


def toc_page_cb(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_DARK)
    canvas.rect(0, PAGE_H - 50, PAGE_W, 50, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.setFillColor(C_GOLD)
    canvas.drawString(MARGIN_L, PAGE_H - 35, "Table of Contents")
    # Footer
    canvas.setStrokeColor(C_GOLD)
    canvas.setLineWidth(0.7)
    canvas.line(MARGIN_L, MARGIN_B - 4, PAGE_W - MARGIN_R, MARGIN_B - 4)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(MARGIN_L, MARGIN_B - 14,
                      "INTERNAL — CONFIDENTIAL  |  OneRoyal Group  |  v1.0  |  June 2026")
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(C_NAVY)
    canvas.drawRightString(PAGE_W - MARGIN_R, MARGIN_B - 14, f"Page {doc.page}")
    canvas.restoreState()


def body_page_cb(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(C_GOLD)
    canvas.setLineWidth(0.7)
    canvas.line(MARGIN_L, PAGE_H - MARGIN_T + 4, PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 4)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(C_NAVY)
    canvas.drawString(MARGIN_L, PAGE_H - MARGIN_T + 7,
                      "OneRoyal Client Intelligence Platform — Handover Manual")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_MUTED)
    sec = getattr(doc, "_current_section", "")
    canvas.drawRightString(PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 7, sec)
    canvas.line(MARGIN_L, MARGIN_B - 4, PAGE_W - MARGIN_R, MARGIN_B - 4)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(MARGIN_L, MARGIN_B - 14,
                      "INTERNAL — CONFIDENTIAL  |  OneRoyal Group  |  v1.0  |  June 2026")
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(C_NAVY)
    canvas.drawRightString(PAGE_W - MARGIN_R, MARGIN_B - 14, f"Page {doc.page}")
    canvas.restoreState()


# ── Content builders ──────────────────────────────────────────────────────────
def cover_content():
    """Cover page flowables (rendered on dark background)."""
    elems = []
    elems.append(Spacer(1, 3.2 * cm))

    # ORG name
    elems.append(Paragraph(
        "<font color='#F0B429'>ONE</font>"
        "<font color='#FFFFFF'>ROYAL</font>",
        ParagraphStyle("CoverOrg", fontSize=32, fontName="Helvetica-Bold",
                       textColor=C_GOLD, leading=38, spaceAfter=4,
                       leftIndent=MARGIN_L)
    ))
    elems.append(Spacer(1, 0.3 * cm))

    # Gold divider
    elems.append(HRFlowable(
        width=CONTENT_W + MARGIN_L, thickness=2, color=C_GOLD,
        spaceAfter=20,
    ))

    # Title
    elems.append(Paragraph(
        "Client Intelligence Platform",
        ParagraphStyle("CT1", fontSize=26, fontName="Helvetica-Bold",
                       textColor=C_TEXT, leading=32, spaceAfter=6,
                       leftIndent=MARGIN_L)
    ))
    elems.append(Paragraph(
        "Operational &amp; Technical Handover Manual",
        ParagraphStyle("CT2", fontSize=18, fontName="Helvetica",
                       textColor=C_MUTED, leading=24, spaceAfter=30,
                       leftIndent=MARGIN_L)
    ))

    elems.append(Spacer(1, 1.8 * cm))

    # Meta block
    meta = [
        ("Document Title",    "OneRoyal Client Intelligence Platform – Operational &amp; Technical Handover Manual"),
        ("Version",           "1.0"),
        ("Date",              "June 2026"),
        ("Classification",    "INTERNAL — CONFIDENTIAL"),
        ("Document Owner",    "Product Owner / Solution Architect"),
        ("Distribution",      "Executive Board · Project Manager · BI Team · CRM Team · Retention Team · Commercial Management"),
    ]
    for label, value in meta:
        row = Table(
            [[
                Paragraph(label, ParagraphStyle("ml", fontSize=9, fontName="Helvetica-Bold",
                           textColor=C_MUTED, leading=13)),
                Paragraph(value, ParagraphStyle("mv", fontSize=9, fontName="Helvetica",
                           textColor=C_TEXT, leading=13)),
            ]],
            colWidths=[90, CONTENT_W - 16],
        )
        row.setStyle(TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), MARGIN_L),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elems.append(row)

    elems.append(Spacer(1, 2.5 * cm))

    # Confidentiality notice
    elems.append(Paragraph(
        "⚠  CONFIDENTIAL — This document contains proprietary commercial and technical information "
        "belonging to OneRoyal Group. It is intended solely for the named distribution list. "
        "Unauthorised disclosure, reproduction, or distribution is strictly prohibited.",
        ParagraphStyle("ConfNote", fontSize=8.5, fontName="Helvetica",
                       textColor=colors.HexColor("#FCA5A5"), leading=13,
                       leftIndent=MARGIN_L, rightIndent=MARGIN_R,
                       backColor=colors.HexColor("#2D1B1B"), borderPad=8)
    ))

    return elems


def doc_control_page():
    """Document Control page."""
    elems = [PageBreak()]
    elems.append(Paragraph("Document Control", ST["H1"]))
    elems += divider()

    dc_rows = [
        ["Field", "Detail"],
        ["Document Title", "OneRoyal Client Intelligence Platform – Operational & Technical Handover Manual"],
        ["Version", "1.0"],
        ["Status", "DRAFT — For Review"],
        ["Date", "June 2026"],
        ["Author", "Product Owner / Solution Architect"],
        ["Approval Owner", "Head of Retention / Commercial Director"],
        ["Repository Branch", "claude/oneroyal-client-platform-pfb0lk"],
        ["Classification", "INTERNAL — CONFIDENTIAL"],
    ]
    elems.append(make_table(dc_rows, col_widths=[CONTENT_W * 0.28, CONTENT_W * 0.72]))
    elems.append(Spacer(1, 14))

    elems.append(Paragraph("Revision History", ST["H2"]))
    rev_rows = [
        ["Version", "Date", "Author", "Change Summary"],
        ["1.0", "June 2026", "Platform Team", "Initial release — full platform documentation covering all 7 pages, 6 scoring models, data requirements, roadmap, and appendices."],
    ]
    elems.append(make_table(rev_rows, col_widths=[CONTENT_W * 0.08, CONTENT_W * 0.15, CONTENT_W * 0.22, CONTENT_W * 0.55]))
    elems.append(Spacer(1, 14))

    elems.append(Paragraph("Distribution List", ST["H2"]))
    dist_rows = [
        ["Role", "Purpose"],
        ["Executive Board / Commercial Director", "Strategic oversight, revenue-at-risk reporting, roadmap approval"],
        ["Head of Retention", "Operational configuration, AM workload management, action queue oversight"],
        ["Account Managers", "Daily client action list, score interpretation, outcome logging"],
        ["BI / Analytics Team", "Data export specification, integration implementation, quality monitoring"],
        ["CRM Team", "CRM connector implementation, data field mapping, daily export scheduling"],
        ["Product / Platform Team", "Settings calibration, model validation, code deployments"],
        ["Compliance / Risk", "Score accountability, audit trail, data governance"],
    ]
    elems.append(make_table(dist_rows, col_widths=[CONTENT_W * 0.45, CONTENT_W * 0.55]))
    return elems


def executive_summary_page():
    """Executive Summary (Section 1)."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 1 — EXECUTIVE SUMMARY", ST["H1"]))
    elems += divider()

    elems.append(Paragraph(
        "The OneRoyal Client Intelligence Platform is an internal retention intelligence and commercial "
        "analytics tool that scores every active client across six quantitative dimensions, automatically "
        "prioritises them into an actionable queue, and routes specific recommendations to the correct team.",
        ST["Body"]
    ))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("Three Operational Questions Answered", ST["H2"]))
    q_rows = [
        ["Question", "Score Used", "Where Visible"],
        ["Who is about to leave?", "Retention Risk Score", "Executive Dashboard · Action Center"],
        ["Who is worth the most effort to save?", "Commercial Value Score + Profitability Score", "Action Center · Client List"],
        ["What exact action should we take — and who owns it?", "Priority Score → 11-Rule Decision Tree", "Action Center — Recommended Action + Owner"],
    ]
    elems.append(make_table(q_rows, col_widths=[CONTENT_W * 0.38, CONTENT_W * 0.35, CONTENT_W * 0.27]))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("Business Problems Solved", ST["H2"]))
    prob_rows = [
        ["Problem Without Platform", "Business Impact"],
        ["No risk scoring across all clients", "High-value clients churn undetected"],
        ["No value weighting", "Equal effort spent on $500 and $50,000 equity accounts"],
        ["No book-type-aware profitability", "A-Book and B-Book clients cannot be compared fairly"],
        ["No systematic action routing", "Retention follow-up depends on AM availability, not data"],
    ]
    elems.append(make_table(prob_rows, col_widths=[CONTENT_W * 0.5, CONTENT_W * 0.5]))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("Expected Business Outcomes", ST["H2"]))
    out_rows = [
        ["Outcome", "Measurable Target"],
        ["Reduce undetected churn", "High-risk clients identified 30–60 days before withdrawal"],
        ["Increase retention call conversion", "AMs call the right clients; target >40% success rate"],
        ["Prioritise revenue-generating clients", "Profitability-first action queue drives ROI on retention effort"],
        ["Identify VIP upgrade candidates", "VIP Upside Score surfaces non-VIP clients ready for upgrade"],
        ["Reactivate dormant accounts", "Reactivation Score identifies the best win-back candidates"],
        ["Validate model predictive accuracy", "Churn prediction target: >75% AUC; withdrawal: >80% AUC"],
    ]
    elems.append(make_table(out_rows, col_widths=[CONTENT_W * 0.45, CONTENT_W * 0.55]))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("Current Platform Maturity", ST["H2"]))
    mat_rows = [
        ["Capability", "Status"],
        ["6-score client scoring engine", "✅ Fully implemented"],
        ["Business rules engine (configurable bands)", "✅ Fully implemented"],
        ["9-segment client matrix", "✅ Fully implemented"],
        ["11-rule action routing", "✅ Fully implemented"],
        ["Dark / Light theme system", "✅ Fully implemented"],
        ["Historical snapshot database (SQLite)", "✅ Implemented"],
        ["Outcome tracking", "✅ Implemented"],
        ["Model validation page", "✅ Implemented (with simulated data)"],
        ["Real CRM integration", "⚠️ Placeholder only — requires BI team implementation"],
        ["Real Holistics integration", "⚠️ Placeholder only — requires BI team implementation"],
        ["Production database", "⚠️ SQLite (not suitable for >10k clients in production)"],
        ["User authentication", "❌ Not implemented"],
        ["Role-based access control", "❌ Not implemented"],
        ["Automated daily refresh", "⚠️ Manual trigger only"],
    ]
    elems.append(make_table(mat_rows, col_widths=[CONTENT_W * 0.55, CONTENT_W * 0.45]))
    return elems


def platform_architecture_page():
    """Section 2 — Platform Architecture."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 2 — PLATFORM ARCHITECTURE", ST["H1"]))
    elems += divider()

    elems.append(Paragraph("2.1 Application Stack", ST["H2"]))
    elems.append(Paragraph(
        "Python 3.11 + Streamlit multi-page application. Five architectural layers:",
        ST["Body"]
    ))
    elems.append(Spacer(1, 6))
    elems.append(ArchDiagram(width=CONTENT_W, height=190))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("2.2 Data Flow", ST["H2"]))
    elems.append(DataFlowDiagram(width=CONTENT_W, height=110))
    elems.append(Spacer(1, 6))
    elems.append(Paragraph(
        "Every data source (sample, file upload, CRM, Holistics) passes through the same pipeline: "
        "column renaming and date-to-days derivation in data_mapper.py, quality scoring in "
        "data_validator.py, then six-score computation by scoring.py + rules_engine.py. "
        "The resulting DataFrame is cached in st.session_state['scored_df'] for all pages.",
        ST["Body"]
    ))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("2.3 Session State Architecture", ST["H2"]))
    elems.append(Paragraph(
        "All session variables are initialised by utils/session_init.init_session_state(), "
        "called as the first action on every page after apply_theme(). This prevents KeyError "
        "crashes when a user navigates directly to any page.",
        ST["Body"]
    ))
    ss_rows = [
        ["Key", "Type", "Default", "Description"],
        ["theme", "str", "\"dark\"", "Current theme: \"dark\" or \"light\""],
        ["thresholds", "dict", "See §5", "Scoring threshold values (high_risk, high_value, etc.)"],
        ["risk_weights", "dict", "See §4.1", "7 retention risk factor weights"],
        ["value_weights", "dict", "See §4.2", "7 commercial value factor weights"],
        ["prof_weights", "dict", "See §4.3", "9 profitability factor weights"],
        ["react_weights", "dict", "See §4.4", "5 reactivation factor weights"],
        ["vip_weights", "dict", "See §4.5", "5 VIP upside factor weights"],
        ["scoring_rules", "dict", "From JSON", "Business rules bands (loaded from config/scoring_rules.json)"],
        ["scored_df", "DataFrame", "Generated", "Full scored client table (cached per session)"],
        ["data_source", "str", "\"sample\"", "Active data source key"],
        ["refresh_interval", "str", "\"manual\"", "Auto-refresh interval setting"],
    ]
    elems.append(make_table(ss_rows,
        col_widths=[CONTENT_W*0.20, CONTENT_W*0.10, CONTENT_W*0.16, CONTENT_W*0.54]))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("2.4 Scoring Engine Architecture", ST["H2"]))
    elems.append(Paragraph(
        "The first three scores (Retention Risk, Commercial Value, Profitability) use the "
        "Business Rules Engine — configurable band scoring defined in config/scoring_rules.json. "
        "The remaining three (Reactivation, VIP Upside, Health) use direct weighted formulas "
        "hard-coded in utils/scoring.py.",
        ST["Body"]
    ))
    scoring_rows = [
        ["Score", "Engine", "Configurable?", "Source"],
        ["Retention Risk Score", "Band-based (rules_engine.py)", "✅ Yes — via Settings", "utils/rules_engine.py:score_retention_risk()"],
        ["Commercial Value Score", "Band-based (rules_engine.py)", "✅ Yes — via Settings", "utils/rules_engine.py:score_commercial_value()"],
        ["Profitability Score", "Band-based (rules_engine.py)", "✅ Yes — via Settings", "utils/rules_engine.py:score_profitability()"],
        ["Reactivation Score", "Direct weighted formula", "Weights only", "utils/scoring.py:score_reactivation()"],
        ["VIP Upside Score", "Direct weighted formula", "Weights only", "utils/scoring.py:score_vip_upside()"],
        ["Client Health Score", "Composite formula", "❌ Hard-coded", "utils/scoring.py:compute_health_score()"],
        ["Priority Score", "Composite formula", "❌ Hard-coded", "utils/scoring.py:compute_priority_score()"],
    ]
    elems.append(make_table(scoring_rows,
        col_widths=[CONTENT_W*0.22, CONTENT_W*0.24, CONTENT_W*0.18, CONTENT_W*0.36]))
    return elems


def data_requirements_page():
    """Section 3 — Data Requirements."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 3 — DATA REQUIREMENTS", ST["H1"]))
    elems += divider()

    elems.append(Paragraph("3.1 Identity Fields (Required)", ST["H2"]))
    id_rows = [
        ["Column Name", "Description", "Type", "Req", "Example"],
        ["client_id", "Unique client identifier", "string", "✅", "CR10001"],
        ["client_name", "Full client name", "string", "✅", "Mohammed Al-Rashid"],
        ["country", "Country of residence", "string", "✅", "United Arab Emirates"],
        ["account_manager", "Assigned account manager", "string", "✅", "Sarah Johnson"],
        ["ib_name", "Introducing Broker name", "string", "Opt", "Gulf Traders IB"],
        ["book_type", "Trading book assignment", "string", "✅", "A-Book / B-Book / M-Book"],
        ["vip_status", "Whether client is VIP", "boolean", "Opt", "True / False"],
        ["client_tenure_days", "Days since account opened", "integer", "Opt", "847"],
    ]
    elems.append(make_table(id_rows,
        col_widths=[CONTENT_W*0.20, CONTENT_W*0.27, CONTENT_W*0.09, CONTENT_W*0.06, CONTENT_W*0.38]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("3.2 Financial Fields", ST["H2"]))
    fin_rows = [
        ["Column Name", "Description", "Required", "Example"],
        ["lifetime_deposits", "Total deposits ever made", "✅", "$45,000"],
        ["withdrawals_total", "Total withdrawals ever", "Optional", "$12,000"],
        ["net_deposits", "lifetime_deposits − withdrawals_total", "Derived", "$33,000"],
        ["current_equity", "Current account balance", "✅", "$28,500"],
        ["equity_30d_ago", "Balance 30 days ago", "✅ for risk", "$31,200"],
        ["withdrawal_amount_last_30d", "Withdrawal value in last 30 days", "✅ for risk", "$8,500"],
    ]
    elems.append(make_table(fin_rows,
        col_widths=[CONTENT_W*0.28, CONTENT_W*0.34, CONTENT_W*0.15, CONTENT_W*0.23]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("3.3 Revenue / Profitability Fields", ST["H2"]))
    elems.append(Paragraph(
        "These fields feed the Profitability Score and are critical for B-Book and M-Book clients. "
        "They must come from the trading platform, not the CRM.",
        ST["Body"]
    ))
    rev_rows = [
        ["Column Name", "Description", "A-Book", "B-Book", "M-Book"],
        ["spread_commission_revenue", "Monthly spread income", "✅", "✅", "✅"],
        ["commission_revenue", "Monthly commission income", "✅", "✅", "✅"],
        ["swap_revenue", "Monthly swap/overnight income", "✅", "✅", "✅"],
        ["captured_client_losses", "Net P&L captured from B/M-Book positions", "0 (zero)", "✅ Critical", "✅ Critical"],
        ["net_company_pnl", "Monthly total profit to company (computed)", "Derived", "Derived", "Derived"],
    ]
    elems.append(make_table(rev_rows,
        col_widths=[CONTENT_W*0.29, CONTENT_W*0.35, CONTENT_W*0.12, CONTENT_W*0.12, CONTENT_W*0.12]))
    elems.append(Spacer(1, 6))
    elems.append(Paragraph(
        "IMPORTANT — B-Book captured_client_losses: This field contains the net realised client P&L "
        "held internally. It can be negative (when B-Book clients are profitable). The scoring engine "
        "handles negative values by assigning 0 profitability points. This field must be computed by "
        "the trading platform, not the CRM.",
        ST["Caution"]
    ))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("3.4 BI Export Specification", ST["H2"]))
    elems.append(Paragraph("Recommended Lookback Periods", ST["H3"]))
    lb_rows = [
        ["Metric Type", "Recommended Period", "Reason"],
        ["Last login date", "Real-time or daily snapshot", "Detects sudden inactivity"],
        ["Last deposit/withdrawal date", "Real-time or daily snapshot", "Triggers withdrawal alert rule"],
        ["Trading volume", "30-day rolling", "Used directly in scoring"],
        ["Prior period volume", "Days 31–60 (previous 30-day window)", "Basis for volume drop signal"],
        ["Historical volume reference", "90-day reference point", "Used in VIP Upside Score"],
        ["Current equity", "Daily close balance", "Core to risk and value scoring"],
        ["Equity reference", "30-day-ago balance", "Equity trend signal in risk score"],
        ["Revenue (spread, commission, swap)", "Monthly aggregate", "Fed into profitability score"],
        ["Captured client losses (B/M)", "Monthly aggregate", "Profitability score, B/M book"],
        ["Lifetime deposits", "Cumulative from account open", "Commercial value score"],
        ["Complaints", "30-day count", "High-weight risk signal (weight ×9)"],
    ]
    elems.append(make_table(lb_rows,
        col_widths=[CONTENT_W*0.32, CONTENT_W*0.30, CONTENT_W*0.38]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("Recommended File Format", ST["H3"]))
    elems.append(Paragraph(
        "File: oneRoyal_client_intelligence_YYYYMMDD.csv  |  UTF-8 CSV  |  One row per client  |  "
        "Frequency: Daily at 03:00 server time  |  Date format: YYYY-MM-DD  |  "
        "Currency: USD numeric (e.g. 45000.00, not $45,000.00)  |  "
        "Boolean: true/false or 1/0  |  Null: empty string",
        ST["Body"]
    ))
    elems.append(Paragraph(
        "Excel format: Sheet name 'Clients', Row 1 = column headers, no merged cells, no formulas, "
        "no conditional formatting. File format: .xlsx",
        ST["Body"]
    ))
    return elems


def scoring_engine_page():
    """Section 4 — Scoring Engine."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 4 — SCORING ENGINE", ST["H1"]))
    elems += divider()

    elems.append(Paragraph(
        "All scores are on a 0–100 scale using min-max normalization: "
        "(value − min) / (max − min) × 100. "
        "If all values are equal (min = max), the score defaults to 50. "
        "All scores are rounded to 1 decimal place.",
        ST["Body"]
    ))
    elems.append(Spacer(1, 8))
    elems.append(ScoreFormulaBox(width=CONTENT_W, height=260))
    elems.append(Spacer(1, 10))

    # Retention Risk Score
    elems.append(Paragraph("4.1 Retention Risk Score", ST["H2"]))
    elems.append(Paragraph(
        "Higher score = higher risk of leaving. Source: utils/rules_engine.py:score_retention_risk()",
        ST["Body"]
    ))
    rr_rows = [
        ["Signal", "Input", "Band Points (Low → High)", "Default Weight"],
        ["Withdrawal Pressure", "withdrawal_30d / current_equity",
         "&lt;10%: 10pts | 10–30%: 50pts | ≥30%: 90pts", "8"],
        ["Volume Drop", "(prev_vol − curr_vol) / prev_vol",
         "≤0%: 5pts | 0–30%: 30pts | 30–60%: 65pts | &gt;60%: 90pts", "7"],
        ["Login Inactivity", "login_days_ago",
         "&lt;7d: 5pts | 7–30d: 25pts | 30–90d: 65pts | &gt;90d: 90pts", "6"],
        ["Deposit Inactivity", "last_deposit_days_ago",
         "&lt;30d: 5pts | 30–90d: 30pts | 90–180d: 60pts | &gt;180d: 90pts", "5"],
        ["Complaints", "complaints_30d + open_tickets",
         "0: 0pts | 1: 50pts | ≥2: 90pts", "9 (highest)"],
        ["Equity Erosion", "1 − (equity / net_deposits)",
         "≤0%: 0pts | 0–15%: 30pts | 15–30%: 65pts | &gt;30%: 90pts", "5"],
        ["Equity Trend 30d", "(equity_30d_ago − equity) / equity_30d_ago",
         "≤0%: 0pts | 0–15%: 30pts | 15–30%: 65pts | &gt;30%: 90pts", "6"],
    ]
    elems.append(make_table(rr_rows,
        col_widths=[CONTENT_W*0.18, CONTENT_W*0.24, CONTENT_W*0.45, CONTENT_W*0.13],
        small=True))
    elems.append(Spacer(1, 6))
    interp_rows = [
        ["Score Range", "Label", "Recommended Response"],
        ["0–29", "Low Risk", "Monitor — no immediate action"],
        ["30–59", "Medium Risk", "Consider proactive contact"],
        ["60–79", "High Risk", "Priority for retention action"],
        ["80–100", "Very High Risk", "Immediate intervention required"],
    ]
    elems.append(make_table(interp_rows, col_widths=[CONTENT_W*0.20, CONTENT_W*0.20, CONTENT_W*0.60]))
    elems.append(Spacer(1, 10))

    # Commercial Value Score
    elems.append(Paragraph("4.2 Commercial Value Score", ST["H2"]))
    elems.append(Paragraph(
        "Higher score = greater commercial importance. Source: utils/rules_engine.py:score_commercial_value()",
        ST["Body"]
    ))
    cv_rows = [
        ["Component", "Band Thresholds", "Default Weight"],
        ["Lifetime Deposits", "&lt;$1K: 10 | $1K–$10K: 35 | $10K–$50K: 60 | $50K–$200K: 85 | &gt;$200K: 100", "8"],
        ["Net Deposits", "&lt;$0: 0 | $0–$1K: 15 | $1K–$10K: 40 | $10K–$50K: 70 | &gt;$50K: 100", "7"],
        ["Current Equity", "&lt;$500: 5 | $500–$5K: 30 | $5K–$25K: 60 | $25K–$100K: 85 | &gt;$100K: 100", "8"],
        ["Trading Volume (30d)", "&lt;$1K: 5 | $1K–$10K: 25 | $10K–$100K: 55 | $100K–$500K: 80 | &gt;$500K: 100", "6"],
        ["Redeposit Count", "0: 0 | 1–2: 25 | 3–7: 55 | 8–15: 80 | &gt;15: 100", "5"],
        ["Client Tenure", "&lt;90d: 10 | 90–365d: 35 | 365–730d: 65 | &gt;730d: 100", "4"],
        ["VIP Status", "VIP = 100pts | Non-VIP = 0pts", "9 (highest)"],
    ]
    elems.append(make_table(cv_rows,
        col_widths=[CONTENT_W*0.22, CONTENT_W*0.62, CONTENT_W*0.16], small=True))
    elems.append(Spacer(1, 10))

    # Profitability Score
    elems.append(Paragraph("4.3 Profitability Score", ST["H2"]))
    elems.append(Paragraph(
        "Higher score = higher monthly profit to OneRoyal. Book-type-aware. "
        "Source: utils/rules_engine.py:score_profitability()",
        ST["Body"]
    ))
    prof_rows = [
        ["Book Type", "Formula", "Band Thresholds"],
        ["A-Book", "spread + commission + swap",
         "&lt;$50: 10 | $50–$200: 35 | $200–$500: 60 | $500–$2K: 85 | &gt;$2K: 100"],
        ["B-Book", "captured_losses + commission + swap + spread",
         "&lt;$0: 0 | $0–$100: 20 | $100–$500: 45 | $500–$2K: 70 | $2K–$5K: 90 | &gt;$5K: 100"],
        ["M-Book", "(0.6 × captured_losses) + spread + commission + swap",
         "&lt;$0: 0 | $0–$75: 20 | $75–$300: 45 | $300–$1K: 70 | &gt;$1K: 100"],
    ]
    elems.append(make_table(prof_rows,
        col_widths=[CONTENT_W*0.12, CONTENT_W*0.40, CONTENT_W*0.48], small=True))
    elems.append(Paragraph(
        "M-Book internal_ratio (default 0.6) is configurable in Settings → Business Rules Engine → Profitability Bands.",
        ST["Info"]
    ))
    elems.append(Spacer(1, 10))

    # Health and Priority
    elems.append(Paragraph("4.4 Client Health Score", ST["H2"]))
    elems.append(Paragraph(
        "Composite positive metric. Hard-coded in utils/scoring.py:compute_health_score(). "
        "NOT configurable via Settings.",
        ST["Body"]
    ))
    elems.append(Paragraph(
        "health_score = (100 − risk_score) × 0.50 + commercial_value_score × 0.30 + profitability_score × 0.20",
        ST["Code"]
    ))
    health_rows = [
        ["Range", "Label", "Color"],
        ["80–100", "Excellent", "#10B981 (Green)"],
        ["60–79", "Healthy", "#22C55E (Light Green)"],
        ["40–59", "Watchlist", "#F59E0B (Amber)"],
        ["20–39", "At Risk", "#F97316 (Orange)"],
        ["0–19", "Critical", "#EF4444 (Red)"],
    ]
    elems.append(make_table(health_rows, col_widths=[CONTENT_W*0.20, CONTENT_W*0.25, CONTENT_W*0.55]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("4.5 Priority Score", ST["H2"]))
    elems.append(Paragraph(
        "Used to rank the Action Center queue. Hard-coded in utils/scoring.py:compute_priority_score().",
        ST["Body"]
    ))
    elems.append(Paragraph(
        "priority_score = risk_score × 0.30 + value_score × 0.25 + profitability_score × 0.30 + reactivation_score × 0.15",
        ST["Code"]
    ))
    elems.append(Paragraph(
        "Design rationale: Risk and profitability are equally weighted at 30% each — a client that is "
        "both at risk AND profitable generates the highest urgency. Value contributes 25%, reactivation 15%.",
        ST["Body"]
    ))
    return elems


def segmentation_action_page():
    """Segmentation matrix and 11-rule action tree."""
    elems = [PageBreak()]
    elems.append(Paragraph("4.6 Segmentation Matrix & Action Routing", ST["H1"]))
    elems += divider()

    elems.append(Paragraph("9-Segment Client Matrix", ST["H2"]))
    elems.append(Paragraph(
        "Source: utils/scoring.py:assign_segments(). Clients are tiered into "
        "Low/Medium/High for both Risk and Value using the threshold values from Settings. "
        "The 3×3 matrix produces nine named segments.",
        ST["Body"]
    ))
    elems.append(Spacer(1, 6))
    elems.append(ScoringMatrix(width=CONTENT_W, height=200))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("11-Rule Action Decision Tree", ST["H2"]))
    elems.append(Paragraph(
        "Source: utils/scoring.py:assign_actions(). First-match wins. "
        "All threshold values (high_risk, high_value, high_profitability, large_withdrawal_pct) "
        "are configurable in Settings.",
        ST["Body"]
    ))
    elems.append(Spacer(1, 6))
    elems.append(ActionDecisionTree(width=CONTENT_W, height=310))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("Recommended Owner Routing", ST["H2"]))
    own_rows = [
        ["Condition", "Assigned Owner Team"],
        ["URGENT VIP Retention action", "Management Review"],
        ["VIP client (any risk level)", "VIP Team"],
        ["Immediate Retention Call", "Retention Team"],
        ["Reactivation Campaign or Re-engagement", "Sales Team"],
        ["All other actions", "Account Manager"],
    ]
    elems.append(make_table(own_rows, col_widths=[CONTENT_W*0.60, CONTENT_W*0.40]))
    return elems


def settings_page_section():
    """Section 5 — Settings."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 5 — SETTINGS PAGE REFERENCE", ST["H1"]))
    elems += divider()
    elems.append(Paragraph("Page: pages/5_Settings.py", ST["Body"]))
    elems.append(Spacer(1, 6))

    elems.append(Paragraph("5.1 Scoring Thresholds", ST["H2"]))
    elems.append(Paragraph(
        "These thresholds control when clients are labelled and which action rules trigger. "
        "They affect the segmentation matrix, action routing, and all dashboard KPIs.",
        ST["Body"]
    ))
    t_rows = [
        ["Setting", "Default", "Min", "Max", "Impact of Increase", "Impact of Decrease"],
        ["high_risk", "60", "10", "95",
         "Fewer high-risk clients; team focuses on severe cases",
         "More flagged; higher workload, more false positives"],
        ["high_value", "60", "10", "95",
         "Fewer in 'high value' bucket; higher bar for premium treatment",
         "More clients receive premium attention"],
        ["high_profitability", "60", "10", "95",
         "Fewer profitability-dependent action rules trigger",
         "More clients receive profitability-linked actions"],
        ["critical_priority", "65", "10", "95",
         "Fewer 'Critical' labels in Action Center",
         "More Critical labels; creates urgency inflation"],
    ]
    elems.append(make_table(t_rows,
        col_widths=[CONTENT_W*0.16, CONTENT_W*0.08, CONTENT_W*0.06, CONTENT_W*0.06,
                    CONTENT_W*0.32, CONTENT_W*0.32], small=True))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("5.2 Activity Thresholds", ST["H2"]))
    at_rows = [
        ["Setting", "Default", "Description"],
        ["login_inactivity_days", "30 days", "Days without login before a client is flagged as inactive in action rules"],
        ["large_withdrawal_pct", "30% of equity", "Withdrawal exceeding this % of equity triggers 'Retention Call: Withdrawal Alert'"],
        ["dormant_days", "30 days", "Days without login before account_status changes to 'Dormant'"],
    ]
    elems.append(make_table(at_rows, col_widths=[CONTENT_W*0.28, CONTENT_W*0.18, CONTENT_W*0.54]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("5.3 Business Rules Engine", ST["H2"]))
    elems.append(Paragraph(
        "Located in the lower section of Settings. Three tabs: Retention Risk Factors, "
        "Commercial Value Factors, Profitability Bands. For each factor the user can edit "
        "the Points (0–100) for each tier band. Higher points = stronger signal for that condition. "
        "After editing, clicking 'Save Scoring Rules & Rescore All Clients' writes changes to "
        "config/scoring_rules.json and immediately rescores all clients.",
        ST["Body"]
    ))
    elems.append(Paragraph(
        "CAUTION: Changing band points is a calibration decision that affects every client score. "
        "Changes should be made based on validated outcome data (see Section 9), not intuition. "
        "Keep a backup of config/scoring_rules.json before making changes.",
        ST["Caution"]
    ))
    return elems


def dashboard_and_pages_section():
    """Sections 6, 7, 8 — Pages."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 6 — EXECUTIVE DASHBOARD", ST["H1"]))
    elems += divider()
    elems.append(Paragraph("Page: pages/1_Executive_Dashboard.py", ST["Body"]))
    elems.append(Spacer(1, 6))

    elems.append(Paragraph("6.1 KPI Cards", ST["H2"]))
    kpi_rows = [
        ["KPI", "Formula", "Business Interpretation"],
        ["Total Clients", "len(df)", "Portfolio size"],
        ["Clients At Risk", "count(risk_score ≥ high_risk)", "Immediate retention workload"],
        ["High-Value At Risk", "count(risk ≥ high_risk AND value ≥ high_value)", "Revenue-priority intervention candidates"],
        ["Total Equity At Risk", "sum(current_equity where risk ≥ high_risk)", "Dollar value in jeopardy"],
        ["Annual Revenue At Risk", "sum(spread + commission + swap where risk ≥ high_risk) × 12", "Forward revenue exposure"],
        ["Annual Profitability At Risk", "sum(net_company_pnl where risk ≥ high_risk) × 12", "Forward profitability exposure"],
    ]
    elems.append(make_table(kpi_rows, col_widths=[CONTENT_W*0.25, CONTENT_W*0.40, CONTENT_W*0.35]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("6.2 Charts", ST["H2"]))
    chart_rows = [
        ["Chart", "Type", "Data"],
        ["Retention Risk Distribution", "Histogram (25 bins)", "retention_risk_score for all clients"],
        ["Client Health Distribution", "Bar chart", "Count per health label (5 labels)"],
        ["Profitability Score Distribution", "Histogram (25 bins)", "profitability_score for all clients"],
        ["Avg Profitability by Book Type", "Grouped bar", "Average profitability score per book type"],
        ["Annual Revenue At Risk by Country", "Horizontal bar (top 10)", "(spread + commission + swap) × 12 for at-risk clients"],
        ["Annual Revenue At Risk by AM", "Horizontal bar", "Revenue at risk per account manager"],
        ["Segmentation Matrix", "3×3 Heatmap", "Client count per Risk × Value cell"],
        ["Trend Analytics", "Multi-line (4 periods)", "avg_risk, avg_health, total_equity, annual_revenue"],
    ]
    elems.append(make_table(chart_rows, col_widths=[CONTENT_W*0.32, CONTENT_W*0.22, CONTENT_W*0.46]))

    # Section 7
    elems.append(PageBreak())
    elems.append(Paragraph("SECTION 7 — CLIENT LIST", ST["H1"]))
    elems += divider()
    elems.append(Paragraph("Page: pages/2_Client_List.py", ST["Body"]))
    elems.append(Spacer(1, 6))

    elems.append(Paragraph("7.1 Filter Controls", ST["H2"]))
    filt_rows = [
        ["Filter", "Type", "Column"],
        ["Search name or client ID", "Text input", "client_name OR client_id (case-insensitive)"],
        ["Country", "Dropdown", "country"],
        ["Account Manager", "Dropdown", "account_manager"],
        ["IB Name", "Dropdown", "ib_name"],
        ["Book Type", "Dropdown", "book_type (A-Book / B-Book / M-Book)"],
        ["Risk Level", "Dropdown", "risk_level (Low / Medium / High)"],
        ["Health", "Dropdown", "health_label"],
    ]
    elems.append(make_table(filt_rows, col_widths=[CONTENT_W*0.30, CONTENT_W*0.18, CONTENT_W*0.52]))
    elems.append(Spacer(1, 6))
    elems.append(Paragraph(
        "All filters are cumulative (AND logic). Sort column supports all 6 scores plus "
        "current_equity and lifetime_deposits.",
        ST["Body"]
    ))

    elems.append(Paragraph("7.2 Client Detail Panel", ST["H2"]))
    elems.append(Paragraph(
        "Below the table, a client selector shows: 6 score tiles (Risk, Value, Profitability, "
        "Reactivation, VIP Upside, Health) · Segment / Action / Owner / Reason · "
        "Financial summary (equity, deposits, PnL, account status, VIP) · "
        "Activity summary (login, deposit, withdrawal timing, volume, complaints) · "
        "Score Contribution Analysis — two horizontal bar charts showing which factors drove "
        "the Risk score and Value score.",
        ST["Body"]
    ))

    # Section 8
    elems.append(PageBreak())
    elems.append(Paragraph("SECTION 8 — ACTION CENTER", ST["H1"]))
    elems += divider()
    elems.append(Paragraph("Page: pages/4_Action_Center.py", ST["Body"]))
    elems.append(Spacer(1, 6))

    elems.append(Paragraph("8.1 Prioritisation Methodology", ST["H2"]))
    elems.append(Paragraph(
        "The Action Center displays all clients except those assigned 'Monitor Only'. "
        "Sort order: Profitability Score DESC → Commercial Value Score DESC → Retention Risk Score DESC. "
        "Design rationale: protecting profitable clients is the primary commercial objective.",
        ST["Body"]
    ))

    elems.append(Paragraph("8.2 KPI Summary", ST["H2"]))
    ac_kpi_rows = [
        ["KPI", "Calculation"],
        ["Clients Needing Action", "Count of clients with action ≠ 'Monitor Only'"],
        ["Avg Priority Score", "Mean priority_score for all action clients"],
        ["Annual Revenue at Stake", "sum(spread + commission + swap) × 12 for action clients"],
        ["Annual Profitability at Stake", "sum(net_company_pnl) × 12 for action clients"],
    ]
    elems.append(make_table(ac_kpi_rows, col_widths=[CONTENT_W*0.35, CONTENT_W*0.65]))

    elems.append(Paragraph("8.3 Recommended AM Daily Workflow", ST["H2"]))
    steps = [
        "Open Action Center each morning.",
        "Filter by own name under 'Filter by owner → Account Manager'.",
        "Work down the list in displayed order (profitability-first).",
        "For 'Immediate Retention Call' or 'Retention Follow-Up': review Client Detail page for score reasons, note the action reason text for talking points, log outcome in Model Validation.",
        "Flag 'URGENT: VIP Retention' clients for same-day escalation to management.",
    ]
    for i, step in enumerate(steps):
        elems.append(Paragraph(f"{i+1}.  {step}", ST["Bullet"]))
    elems.append(Spacer(1, 6))
    elems.append(Paragraph(
        "Escalation path: Management Review → Head of Retention + Commercial Director. "
        "VIP Team → Dedicated VIP relationship manager. "
        "Retention Team → Retention specialists, not AMs.",
        ST["Info"]
    ))
    return elems


def model_validation_section():
    """Section 9 — Model Validation."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 9 — MODEL VALIDATION", ST["H1"]))
    elems += divider()
    elems.append(Paragraph("Page: pages/7_Model_Validation.py", ST["Body"]))
    elems.append(Spacer(1, 6))

    tab_rows = [
        ["Tab", "Content"],
        ["Tab 1 — Prediction Accuracy", "AUC-style accuracy metrics for churn, withdrawal, reactivation predictions. Confusion matrix. Precision/recall/lift vs. random baseline."],
        ["Tab 2 — Score Factor Breakdown", "Factor-by-factor contribution analysis for Risk and Value scores across the portfolio. Box plots of score distributions."],
        ["Tab 3 — Retention Effectiveness", "Outcome logging form. Success rate tracking by action type and AM. Conversion funnel."],
        ["Tab 4 — Score Trend Analysis", "Historical score drift charts using snapshot_db.py data. Alerts for significant score movements."],
        ["Tab 5 — Data Snapshots", "Snapshot database explorer. View stored score snapshots and outcome records. Export capability."],
    ]
    elems.append(make_table(tab_rows, col_widths=[CONTENT_W*0.30, CONTENT_W*0.70]))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("9.1 Prediction Accuracy Methodology", ST["H2"]))
    elems.append(Paragraph(
        "When historical snapshot data and outcome data exist in snapshots.db, the platform "
        "computes an AUC-style metric by: (1) Loading score_snapshots (daily risk scores for all "
        "clients), (2) Joining with client_outcomes on client_id + outcome_type, "
        "(3) Sorting clients by risk score DESC and computing what fraction of actual churners "
        "appear in the top X% of the ranked list, (4) Computing the area under that detection curve "
        "normalised to 0–100%.",
        ST["Body"]
    ))
    elems.append(Spacer(1, 6))

    elems.append(Paragraph("9.2 Target Accuracy Levels", ST["H2"]))
    acc_rows = [
        ["Metric", "Target", "Current Status"],
        ["Churn Prediction AUC", "> 75%", "Simulated — requires real outcome data to validate"],
        ["Withdrawal Prediction AUC", "> 80%", "Simulated — requires real outcome data to validate"],
        ["Reactivation Prediction AUC", "> 65%", "Simulated — requires real outcome data to validate"],
    ]
    elems.append(make_table(acc_rows, col_widths=[CONTENT_W*0.35, CONTENT_W*0.20, CONTENT_W*0.45]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("9.3 Quarterly Model Review Framework", ST["H2"]))
    review_rows = [
        ["Review Item", "Responsible", "Frequency"],
        ["Churn AUC vs. target", "Analytics Team", "Quarterly"],
        ["Factor correlation check (any factor decorrelated from outcomes?)", "Analytics Team", "Quarterly"],
        ["Threshold calibration review (high_risk, high_value)", "Head of Retention", "Quarterly"],
        ["Band point audit (scoring_rules.json vs. actual signal quality)", "Product Team", "Bi-annually"],
        ["Retention action success rate (log in Model Validation)", "Head of Retention", "Monthly"],
        ["AM outcome logging compliance check", "Head of Retention", "Monthly"],
    ]
    elems.append(make_table(review_rows,
        col_widths=[CONTENT_W*0.50, CONTENT_W*0.25, CONTENT_W*0.25]))
    return elems


def roadmap_governance_section():
    """Sections 10, 11 — Roadmap and Governance."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 10 — IMPLEMENTATION ROADMAP", ST["H1"]))
    elems += divider()
    elems.append(Spacer(1, 6))
    elems.append(RoadmapDiagram(width=CONTENT_W, height=130))
    elems.append(Spacer(1, 12))

    road_rows = [
        ["Phase", "Title", "Timeline", "Key Deliverables", "Status"],
        ["1", "Pilot", "NOW", "Synthetic data, all 7 pages, scoring engine, settings", "✅ Complete"],
        ["2", "Production Data Connect", "Q3 2026",
         "BI team exports real CSV daily, data_mapper.py updated for real column names, "
         "data_validator.py quality gates tuned, first real client scores",
         "⚠️ Pending BI team"],
        ["3", "CRM API Integration", "Q4 2026",
         "crm_connector.py implemented (CRM API endpoint, auth), "
         "holistics_connector.py implemented, manual upload removed from production",
         "⚠️ Pending CRM team"],
        ["4", "Automation & Alerting", "Q1 2027",
         "Daily auto-refresh scheduler, email/Slack alerts for critical risk events, "
         "PostgreSQL migration for production scale",
         "❌ Not started"],
        ["5", "AI-Driven Recommendations", "Q2 2027",
         "ML churn model replacing rules-based risk score, "
         "NLP action recommendation using client communication history",
         "❌ Not started"],
    ]
    elems.append(make_table(road_rows,
        col_widths=[CONTENT_W*0.06, CONTENT_W*0.18, CONTENT_W*0.12,
                    CONTENT_W*0.46, CONTENT_W*0.18], small=True))

    # Section 11 — Governance
    elems.append(PageBreak())
    elems.append(Paragraph("SECTION 11 — GOVERNANCE", ST["H1"]))
    elems += divider()

    elems.append(Paragraph("11.1 Role Definitions", ST["H2"]))
    role_rows = [
        ["Role", "Responsibilities in Platform"],
        ["Head of Retention", "Owns threshold and weight calibration; reviews model accuracy quarterly; approves changes to action routing rules"],
        ["Account Managers", "Daily action queue execution; outcome logging in Model Validation; flag data quality issues"],
        ["BI / Analytics Team", "Daily CSV export to correct schema; maintains data pipeline; monitors data quality score; implements Holistics connector"],
        ["CRM Team", "Implements crm_connector.py against actual CRM API; ensures field mapping; manages authentication"],
        ["Platform / Product Team", "Code deployments; Settings calibration support; rules_engine tuning; model validation interpretation"],
        ["Commercial Director", "Executive Dashboard consumer; approves roadmap phases; reviews revenue-at-risk reports"],
        ["Compliance / Risk", "Score accountability; audit trail review; GDPR compliance for client data in snapshots.db"],
    ]
    elems.append(make_table(role_rows, col_widths=[CONTENT_W*0.25, CONTENT_W*0.75]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("11.2 Data Quality Controls", ST["H2"]))
    dq_rows = [
        ["Control", "Threshold", "Action if Breached"],
        ["Missing required fields (client_id, book_type, current_equity)", "Any missing = error", "Block upload; reject data source"],
        ["Data quality score (computed by data_validator.py)", "&lt; 70 = warning, &lt; 50 = fail", "Display warning; refuse to rescore if fail"],
        ["Duplicate client IDs", "Any duplicate = error", "Flag and deduplicate on most recent record"],
        ["current_equity negative values", "Any negative", "Set to 0; flag in quality report"],
        ["Stale data (last_login_date > 365 days in future)", "Any future date", "Flag as data error; use None"],
    ]
    elems.append(make_table(dq_rows,
        col_widths=[CONTENT_W*0.38, CONTENT_W*0.20, CONTENT_W*0.42]))
    return elems


def operating_manual_section():
    """Section 12 — Operating Manual."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 12 — OPERATING MANUAL", ST["H1"]))
    elems += divider()

    elems.append(Paragraph("12.1 First-Time Setup", ST["H2"]))
    setup_steps = [
        "Clone repository: git clone [repo_url]",
        "Install dependencies: pip install -r requirements.txt",
        "Run application: streamlit run app.py",
        "Navigate to Settings (page 5) and verify default thresholds are appropriate for your portfolio size.",
        "Navigate to Scoring Engine (page 3) to review default weights.",
        "Review sample data in Client List (page 2) to understand the scoring output format.",
    ]
    for i, step in enumerate(setup_steps):
        elems.append(Paragraph(f"{i+1}.  {step}", ST["Bullet"]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("12.2 Uploading Real Client Data", ST["H2"]))
    upload_steps = [
        "Prepare your data file matching the BI Export Specification in Section 3.4.",
        "Navigate to Data Management (page 6).",
        "Select 'Upload File' as the data source.",
        "Upload the CSV or Excel file.",
        "Review the Data Quality Report — ensure quality score > 70.",
        "Click 'Rescore All Clients'.",
        "Verify the Executive Dashboard shows the expected client count and score distributions.",
    ]
    for i, step in enumerate(upload_steps):
        elems.append(Paragraph(f"{i+1}.  {step}", ST["Bullet"]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("12.3 Daily Analysis Workflow", ST["H2"]))
    daily_rows = [
        ["Step", "Who", "Page", "Action"],
        ["1", "AM / Retention Lead", "Action Center (4)", "Review action queue sorted by profitability. Filter by own name."],
        ["2", "AM", "Client List (2)", "Click through any 'Immediate Retention Call' clients for score detail."],
        ["3", "AM", "Model Validation (7)", "Log outcome of any retention actions taken yesterday."],
        ["4", "Head of Retention", "Executive Dashboard (1)", "Check KPI cards and 'High-Value At Risk' count."],
        ["5", "BI Team", "Data Management (6)", "Upload fresh daily export. Verify quality score > 70."],
        ["6", "Analytics (weekly)", "Model Validation (7)", "Review prediction accuracy trends and score drift."],
    ]
    elems.append(make_table(daily_rows,
        col_widths=[CONTENT_W*0.07, CONTENT_W*0.20, CONTENT_W*0.22, CONTENT_W*0.51]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("12.4 Interpreting Scores", ST["H2"]))
    interp_rows = [
        ["Score", "What It Means", "Action Trigger"],
        ["Retention Risk ≥ 60", "Client shows 2+ warning signals", "Call within 24 hours"],
        ["Commercial Value ≥ 60", "Client is in top third for revenue and relationship value", "Prioritise over lower-value clients"],
        ["Profitability ≥ 60", "Client is a significant monthly profit contributor", "Assign to senior AM or retention specialist"],
        ["Health = Critical (0–19)", "High risk, low value, low profitability", "Automated retention or deprioritise"],
        ["Priority ≥ 65", "Critical priority label — top action urgency", "Escalate to team lead"],
        ["Reactivation ≥ 65", "Dormant client with high win-back probability", "Launch reactivation campaign"],
        ["VIP Upside ≥ 65", "Non-VIP client with VIP financial profile", "Initiate VIP upgrade conversation"],
    ]
    elems.append(make_table(interp_rows,
        col_widths=[CONTENT_W*0.28, CONTENT_W*0.38, CONTENT_W*0.34]))
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("12.5 Adjusting Settings", ST["H2"]))
    elems.append(Paragraph(
        "Threshold changes affect every labelled metric in the platform instantly. "
        "Before changing thresholds: (1) note current client counts in the Impact Preview section of Settings, "
        "(2) make the change, (3) click 'Save Settings & Rescore All Clients', "
        "(4) review the Impact Preview to verify the new client counts are operationally manageable.",
        ST["Body"]
    ))
    elems.append(Paragraph(
        "Typical calibration: if the Action Center shows >30% of clients needing action, raise high_risk "
        "by 5–10 points. If fewer than 5% are flagged, lower it by 5 points.",
        ST["Info"]
    ))
    return elems


def appendices_section():
    """Section 13 — Appendices."""
    elems = [PageBreak()]
    elems.append(Paragraph("SECTION 13 — APPENDICES", ST["H1"]))
    elems += divider()

    # Appendix A — Data Dictionary
    elems.append(Paragraph("Appendix A — Complete Data Dictionary", ST["H2"]))
    dd_rows = [
        ["Column", "Data Type", "Source", "Required", "Scoring Impact"],
        ["client_id", "string", "CRM", "✅", "Join key — no scoring impact"],
        ["client_name", "string", "CRM", "✅", "Display only"],
        ["country", "string", "CRM", "✅", "Display / filter only"],
        ["account_manager", "string", "CRM", "✅", "Action routing / workload"],
        ["book_type", "string", "CRM/Platform", "✅", "Profitability formula selector"],
        ["vip_status", "boolean", "CRM", "Optional", "Value score ×9, VIP upside, action rules"],
        ["client_tenure_days", "integer", "Derived", "Optional", "Value score + reactivation score"],
        ["lifetime_deposits", "float", "CRM", "✅", "Value score component (weight 8)"],
        ["withdrawals_total", "float", "CRM", "Optional", "net_deposits derivation"],
        ["net_deposits", "float", "Derived", "Derived", "Value score + equity erosion risk signal"],
        ["current_equity", "float", "Platform", "✅", "Risk score, value score (weight 8), withdrawal alert"],
        ["equity_30d_ago", "float", "Platform", "✅ for risk", "Equity trend risk signal (weight 6)"],
        ["login_days_ago", "integer", "CRM (derived)", "✅", "Risk score (weight 6) + reactivation score"],
        ["last_deposit_days_ago", "integer", "CRM (derived)", "✅", "Risk score (weight 5)"],
        ["withdrawal_amount_last_30d", "float", "Platform", "✅", "Risk score withdrawal pressure (weight 8)"],
        ["trading_volume_last_30d", "float", "Platform", "✅", "Risk score volume drop + value score"],
        ["trading_volume_previous_30d", "float", "Platform", "✅ for risk", "Volume drop risk signal (weight 7)"],
        ["volume_90d_ago", "float", "Platform", "Optional", "VIP upside trend + reactivation score"],
        ["spread_commission_revenue", "float", "Platform", "✅", "All three profitability book formulas"],
        ["commission_revenue", "float", "Platform", "Optional", "All three profitability book formulas"],
        ["swap_revenue", "float", "Platform", "Optional", "All three profitability book formulas"],
        ["captured_client_losses", "float", "Platform", "B/M-Book only", "B-Book and M-Book profitability formulas"],
        ["net_company_pnl", "float", "Derived", "Derived", "Priority score, Action Center ranking"],
        ["number_of_redeposits", "integer", "CRM/Platform", "Optional", "Value score (weight 5) + reactivation + VIP upside"],
        ["complaints_last_30d", "integer", "CRM", "✅", "Risk score (weight 9) — highest single weight"],
        ["open_tickets", "integer", "CRM", "Optional", "Added to complaints for risk signal"],
    ]
    elems.append(make_table(dd_rows,
        col_widths=[CONTENT_W*0.18, CONTENT_W*0.10, CONTENT_W*0.14, CONTENT_W*0.10, CONTENT_W*0.48],
        small=True))
    elems.append(Spacer(1, 10))

    # Appendix B — Formula Dictionary
    elems.append(Paragraph("Appendix B — Formula Dictionary", ST["H2"]))
    form_rows = [
        ["Metric", "Formula", "Notes"],
        ["Withdrawal Pressure", "withdrawal_30d / current_equity", "Clamped 0–1"],
        ["Volume Drop", "(prev_vol − curr_vol) / prev_vol", "Negative = volume growing (treated as 0 risk)"],
        ["Equity Erosion", "1 − (current_equity / net_deposits)", "Negative net_deposits → set to 0"],
        ["Equity Trend 30d", "(equity_30d_ago − equity) / equity_30d_ago", "Negative = equity growing (treated as 0 risk)"],
        ["Net Deposits", "lifetime_deposits − withdrawals_total", "Can be negative"],
        ["A-Book Profitability", "spread + commission + swap", "Pure fee-based"],
        ["B-Book Profitability", "captured_losses + commission + swap + spread", "Negative when client profitable"],
        ["M-Book Profitability", "(0.6 × captured_losses) + spread + commission + swap", "Ratio configurable in Settings"],
        ["Health Score", "(100 − risk) × 0.50 + value × 0.30 + profit × 0.20", "Hard-coded weights"],
        ["Priority Score", "risk × 0.30 + value × 0.25 + profit × 0.30 + react × 0.15", "Hard-coded weights"],
        ["Annual Revenue (at risk)", "sum(spread + commission + swap where at risk) × 12", "Approximation based on monthly data"],
        ["Min-Max Normalisation", "(x − min) / (max − min) × 100", "Defaults to 50 if min = max"],
        ["Reactivation Login Curve", "Peaks at 105 days; non-linear curve defined in scoring.py", "Only meaningful for dormant clients"],
    ]
    elems.append(make_table(form_rows,
        col_widths=[CONTENT_W*0.25, CONTENT_W*0.38, CONTENT_W*0.37], small=True))
    elems.append(Spacer(1, 10))

    # Appendix C — BI Export Mapping
    elems.append(Paragraph("Appendix C — BI Export Column Mapping", ST["H2"]))
    elems.append(Paragraph(
        "This table maps the recommended BI export column names to the application's internal "
        "schema. The data_mapper.py file performs this translation on upload.",
        ST["Body"]
    ))
    bi_rows = [
        ["BI Export Column", "Internal Column", "Transformation Required"],
        ["client_id", "client_id", "None"],
        ["client_name", "client_name", "None"],
        ["country", "country", "None"],
        ["account_manager", "account_manager", "None"],
        ["book_type", "book_type", "None"],
        ["vip_status", "vip_status", "String 'true'/'false' → boolean"],
        ["last_login_date", "login_days_ago", "DATE → (today − date).days"],
        ["last_deposit_date", "last_deposit_days_ago", "DATE → (today − date).days"],
        ["last_withdrawal_date", "last_withdrawal_days_ago", "DATE → (today − date).days"],
        ["withdrawals_30d", "withdrawal_amount_last_30d", "Rename only"],
        ["trading_volume_30d", "trading_volume_last_30d", "Rename only"],
        ["trading_volume_previous_30d", "trading_volume_previous_30d", "None"],
        ["volume_90d_ago", "volume_90d_ago", "None"],
        ["spread_revenue", "spread_commission_revenue", "Rename only"],
        ["commission_revenue", "commission_revenue", "None"],
        ["swap_revenue", "swap_revenue", "None"],
        ["company_pnl", "net_company_pnl", "Rename only"],
        ["captured_client_losses", "captured_client_losses", "None"],
        ["number_of_redeposits", "number_of_redeposits", "None"],
        ["complaints", "complaints_last_30d", "Rename only"],
        ["open_tickets", "open_tickets", "None"],
        ["client_tenure_months", "client_tenure_days", "months × 30.44"],
    ]
    elems.append(make_table(bi_rows,
        col_widths=[CONTENT_W*0.32, CONTENT_W*0.32, CONTENT_W*0.36], small=True))
    elems.append(Spacer(1, 10))

    # Appendix D — CRM Integration
    elems.append(Paragraph("Appendix D — Recommended CRM Integration Design", ST["H2"]))
    elems.append(Paragraph(
        "The CRM connector (integrations/crm_connector.py) currently contains placeholder methods "
        "with NotImplementedError. The BI team must implement the following:",
        ST["Body"]
    ))
    crm_rows = [
        ["Method", "Expected Return", "Implementation Notes"],
        ["connect()", "bool", "Authenticate against CRM API. Store session token."],
        ["fetch_clients()", "pd.DataFrame (internal schema)", "HTTP GET against CRM clients endpoint. Map columns using data_mapper.py."],
        ["test_connection()", "dict with 'success', 'client_count'", "Lightweight ping to verify connectivity."],
        ["get_client(client_id)", "dict (single client record)", "GET single client for real-time refresh."],
    ]
    elems.append(make_table(crm_rows,
        col_widths=[CONTENT_W*0.20, CONTENT_W*0.25, CONTENT_W*0.55]))
    elems.append(Spacer(1, 6))
    elems.append(Paragraph(
        "Minimum viable CRM API requirements: REST or GraphQL endpoint returning all active client accounts "
        "with the fields listed in Appendix C. Authentication: API key or OAuth2. "
        "Response format: JSON array or CSV download. Rate limit: must support full portfolio refresh "
        "within 2 minutes. Recommended: daily batch export to file rather than real-time API pull "
        "for large portfolios (>1,000 clients).",
        ST["Body"]
    ))
    elems.append(Spacer(1, 10))

    # Appendix E — Future Enhancements
    elems.append(Paragraph("Appendix E — Future Enhancement Roadmap", ST["H2"]))
    enh_rows = [
        ["Enhancement", "Phase", "Expected Benefit"],
        ["PostgreSQL migration", "Phase 4", "Multi-user concurrency, >10k clients, proper backup"],
        ["User authentication (login screen)", "Phase 4", "Role-based data access, audit trail by user"],
        ["Email/Slack alerts on critical risk events", "Phase 4", "Proactive notification without manual dashboard check"],
        ["ML churn model (replace rules-based risk score)", "Phase 5", "Higher prediction accuracy; learns from real outcomes"],
        ["NLP action recommendation", "Phase 5", "Personalised talking points based on client communication history"],
        ["Mobile-responsive UI", "Phase 4", "AMs can review action queue on mobile devices"],
        ["Automated outcome import from CRM", "Phase 3–4", "Eliminate manual outcome logging; improve model feedback loop"],
        ["Multi-portfolio / multi-brand support", "Phase 4+", "Scale to group-level analytics across multiple entities"],
    ]
    elems.append(make_table(enh_rows,
        col_widths=[CONTENT_W*0.40, CONTENT_W*0.12, CONTENT_W*0.48], small=True))
    return elems


# ── Build the PDF ──────────────────────────────────────────────────────────────
def build_pdf(output_path):
    doc = OneRoyalDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title="OneRoyal Client Intelligence Platform — Handover Manual",
        author="OneRoyal Product & Platform Team",
        subject="Operational & Technical Handover Manual v1.0",
        creator="OneRoyal CI Platform PDF Generator",
    )

    # Three page templates: cover, toc, body
    cover_frame  = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0,
                         topPadding=0, bottomPadding=0)
    toc_frame    = Frame(MARGIN_L, MARGIN_B + 10,
                         CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B - 20,
                         leftPadding=0, rightPadding=0, topPadding=30, bottomPadding=0)
    body_frame   = Frame(MARGIN_L, MARGIN_B,
                         CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B,
                         leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame],
                     onPage=cover_page_cb),
        PageTemplate(id="TOC",   frames=[toc_frame],
                     onPage=toc_page_cb),
        PageTemplate(id="Body",  frames=[body_frame],
                     onPage=body_page_cb),
    ])

    # Build TOC
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOCEntry1", fontSize=11, fontName="Helvetica-Bold",
                       textColor=C_NAVY, leading=16, leftIndent=0,
                       spaceAfter=3, firstLineIndent=0),
        ParagraphStyle("TOCEntry2", fontSize=10, fontName="Helvetica",
                       textColor=C_BODY_TXT, leading=14, leftIndent=20,
                       spaceAfter=2, firstLineIndent=0),
    ]

    # ── Assemble all flowables ─────────────────────────────────────────────────
    story = []

    # 1. Cover page
    story.append(NextPageTemplate("Cover"))
    story += cover_content()

    # 2. TOC page
    story.append(NextPageTemplate("TOC"))
    story.append(PageBreak())
    story.append(toc)

    # 3. Document Control
    story.append(NextPageTemplate("Body"))
    story += doc_control_page()

    # 4. Executive Summary
    story += executive_summary_page()

    # 5. Platform Architecture
    story += platform_architecture_page()

    # 6. Data Requirements
    story += data_requirements_page()

    # 7. Scoring Engine
    story += scoring_engine_page()

    # 8. Segmentation + Actions
    story += segmentation_action_page()

    # 9. Settings
    story += settings_page_section()

    # 10. Dashboard, Client List, Action Center
    story += dashboard_and_pages_section()

    # 11. Model Validation
    story += model_validation_section()

    # 12. Roadmap + Governance
    story += roadmap_governance_section()

    # 13. Operating Manual
    story += operating_manual_section()

    # 14. Appendices
    story += appendices_section()

    doc.multiBuild(story)
    return output_path


if __name__ == "__main__":
    out = "/home/user/Retention-intelligence/OneRoyal_CI_Platform_Handover_Manual_v1.0.pdf"
    print(f"Generating PDF → {out}")
    build_pdf(out)
    size_mb = os.path.getsize(out) / 1_048_576
    print(f"Done. File size: {size_mb:.2f} MB")
