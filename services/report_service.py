"""
PDF Report generation service for individual student readiness assessments.
Uses ReportLab to build executive-ready printable reports.
"""

import io
from datetime import datetime
from typing import Optional, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)

import config
from services.scoring_service import get_component_scores_dict, get_readiness_level
from services.recommendation_service import analyze_skill_gaps, generate_recommendations


def generate_student_pdf_report(
    student: Any,
    rank: Optional[int] = None,
    percentile: Optional[float] = None
) -> bytes:
    """
    Generate a complete, professionally formatted PDF readiness report.
    Returns the binary content as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=12
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_text = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    bold_label = ParagraphStyle(
        "BoldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>TALENTFORGE CAREER READINESS SYSTEM</b>", ParagraphStyle(
                "HeaderLogo", fontName="Helvetica-Bold", fontSize=12, textColor=colors.HexColor("#2563EB")
            )),
            Paragraph(f"Generated: {datetime.now().strftime('%b %d, %Y %H:%M')}", ParagraphStyle(
                "HeaderDate", fontName="Helvetica", fontSize=8, alignment=2, textColor=colors.HexColor("#64748B")
            ))
        ]
    ]
    header_table = Table(header_data, colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=10))

    # 2. Document Title
    story.append(Paragraph("Student Placement Readiness Assessment", title_style))
    story.append(Paragraph("Confidential Diagnostic Evaluation & Competency Roadmap", subtitle_style))

    # 3. Student Particulars & Overall Score KPI Box
    level_color_map = {
        "Ready": colors.HexColor("#10B981"),
        "Almost Ready": colors.HexColor("#F59E0B"),
        "Needs Improvement": colors.HexColor("#EF4444")
    }
    level = getattr(student, "readiness_level", get_readiness_level(getattr(student, "overall_score", 0.0)))
    badge_bg = level_color_map.get(level, colors.HexColor("#64748B"))

    rank_str = f"#{rank}" if rank is not None else "N/A"
    pct_str = f"{percentile:.1f}th Percentile" if percentile is not None else "N/A"

    info_data = [
        [
            Paragraph("<b>Candidate Name:</b>", bold_label),
            Paragraph(getattr(student, "full_name", "N/A"), body_text),
            Paragraph("<b>Overall Score:</b>", bold_label),
            Paragraph(f"<b><font size=14 color='#1E293B'>{getattr(student, 'overall_score', 0.0):.1f} / 100</font></b>", body_text)
        ],
        [
            Paragraph("<b>Roll Number:</b>", bold_label),
            Paragraph(getattr(student, "roll_no", "N/A"), body_text),
            Paragraph("<b>Readiness Level:</b>", bold_label),
            Paragraph(f"<b>{level}</b>", ParagraphStyle("Lvl", parent=bold_label, textColor=badge_bg))
        ],
        [
            Paragraph("<b>Department:</b>", bold_label),
            Paragraph(getattr(student, "department", "N/A"), body_text),
            Paragraph("<b>Cohort Rank:</b>", bold_label),
            Paragraph(f"{rank_str} ({pct_str})", body_text)
        ],
        [
            Paragraph("<b>Graduation Year:</b>", bold_label),
            Paragraph(str(getattr(student, "graduation_year", "N/A")), body_text),
            Paragraph("<b>Academic CGPA:</b>", bold_label),
            Paragraph(f"{getattr(student, 'cgpa', 0.0):.2f} / 10.0", body_text)
        ]
    ]

    info_table = Table(info_data, colWidths=[105, 175, 110, 150])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # 4. Multi-Component Competency Breakdown Table
    story.append(Paragraph("1. Multi-Component Competency Breakdown", section_heading))

    comp_scores = get_component_scores_dict(student)
    breakdown_data = [
        [
            Paragraph("<b>Competency Area</b>", bold_label),
            Paragraph("<b>Weight</b>", bold_label),
            Paragraph("<b>Score / 100</b>", bold_label),
            Paragraph("<b>Benchmark</b>", bold_label),
            Paragraph("<b>Gap</b>", bold_label),
            Paragraph("<b>Status</b>", bold_label)
        ]
    ]

    for key, score in comp_scores.items():
        label = config.COMPONENT_LABELS.get(key, key.replace("_", " ").title())
        weight = int(config.COMPONENT_WEIGHTS.get(key, 0.1) * 100)
        gap = round(config.BENCHMARK_TARGET_SCORE - score, 1)

        if gap > 20:
            status_text = "<font color='#DC2626'><b>Critical Gap</b></font>"
        elif gap > 0:
            status_text = "<font color='#D97706'><b>Moderate Gap</b></font>"
        else:
            status_text = "<font color='#059669'><b>Target Met</b></font>"

        breakdown_data.append([
            Paragraph(label, body_text),
            Paragraph(f"{weight}%", body_text),
            Paragraph(f"{score:.1f}", body_text),
            Paragraph(f"{config.BENCHMARK_TARGET_SCORE:.0f}", body_text),
            Paragraph(f"{'+' if gap < 0 else ''}{-gap:.1f}" if gap <= 0 else f"-{gap:.1f}", body_text),
            Paragraph(status_text, body_text)
        ])

    comp_table = Table(breakdown_data, colWidths=[170, 65, 80, 75, 65, 85])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94A3B8")),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 14))

    # 5. Skill Gap Analysis & Recommendations
    story.append(Paragraph("2. Skill Gap Analysis & Recommended Action Items", section_heading))

    rec_data = generate_recommendations(student)
    recs = rec_data.get("recommendations", [])

    rec_rows = [
        [
            Paragraph("<b>Domain & Score</b>", bold_label),
            Paragraph("<b>Priority</b>", bold_label),
            Paragraph("<b>Target Action Steps</b>", bold_label)
        ]
    ]

    for rec in recs[:4]:  # Top 4 priority recommendations
        action_bullets = "<br/>• ".join(rec.get("actions", [])[:2])
        if action_bullets:
            action_bullets = "• " + action_bullets

        p_color = "#DC2626" if rec.get("priority") == "High" else "#D97706" if rec.get("priority") == "Medium" else "#059669"
        priority_html = f"<font color='{p_color}'><b>{rec.get('priority')}</b></font>"

        rec_rows.append([
            Paragraph(f"<b>{rec['label']}</b><br/><font size=7 color='#64748B'>Score: {rec['score']:.1f}/100</font>", body_text),
            Paragraph(priority_html, body_text),
            Paragraph(f"<b>{rec['title']}</b><br/>{action_bullets}", body_text)
        ])

    rec_table = Table(rec_rows, colWidths=[140, 70, 330])
    rec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94A3B8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 14))

    # 6. Official Sign-off and Disclaimer Block
    sign_off_data = [
        [
            Paragraph("<b>Institutional Remarks:</b><br/>This score indicates placement readiness evaluated against current hiring benchmarks. Regular re-assessment is advised after completing recommended milestones.", body_text),
            Paragraph("<b>Career Development Cell (CDC)</b><br/><br/><i>Authorized System Generated Evaluation</i>", ParagraphStyle("Sign", parent=body_text, alignment=2))
        ]
    ]
    sign_table = Table(sign_off_data, colWidths=[360, 180])
    sign_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(KeepTogether(sign_table))

    # Build document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
