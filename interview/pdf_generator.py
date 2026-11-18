import os
import io
import qrcode
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.utils import ImageReader


def build_interview_report_pdf(session, report, candidate_id: str = None) -> io.BytesIO:
    """
    Generate a multi-page, formatted corporate performance report PDF using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor('#1e3a8a')  # Deep blue
    accent_color = colors.HexColor('#0284c7')   # Sky blue
    success_color = colors.HexColor('#059669')  # Emerald
    dark_gray = colors.HexColor('#1f2937')
    light_bg = colors.HexColor('#f8fafc')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=0
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=accent_color,
        alignment=0
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=dark_gray
    )
    bold_body = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.white,
        alignment=1
    )

    story = []

    # 1. Header with branding and QR Code
    user = session.user
    profile = getattr(user, 'profile', None)
    college = profile.college_name if profile and profile.college_name else "University Institute of Technology"
    degree = profile.degree if profile and profile.degree else "Computer Science"
    candidate_name = user.get_full_name() or user.username
    cand_id = candidate_id or f"INT-{session.id:05d}-{session.created_at.strftime('%Y%m')}"

    # Generate QR Code in-memory
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(f"AI-INTERVIEW-VERIFIED: ID={cand_id}, Candidate={candidate_name}, Score={session.overall_score}/10")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1e3a8a", back_color="white")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    rl_qr = RLImage(qr_buf, width=60, height=60)

    header_table = Table(
        [
            [
                Paragraph("<b>AI INTERVIEW PREPARATION SYSTEM</b><br/><font size=9 color='#0284c7'>Intelligent Candidate Assessment & Readiness Evaluation Report</font>", title_style),
                rl_qr
            ]
        ],
        colWidths=[450, 80]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=4, spaceAfter=12))

    # 2. Student Info & Session Details Table
    info_data = [
        [
            Paragraph("<b>Candidate Name:</b>", bold_body), Paragraph(candidate_name, body_style),
            Paragraph("<b>Verification ID:</b>", bold_body), Paragraph(cand_id, body_style),
        ],
        [
            Paragraph("<b>Email Address:</b>", bold_body), Paragraph(user.email or "candidate@example.com", body_style),
            Paragraph("<b>Interview Date:</b>", bold_body), Paragraph(session.created_at.strftime("%B %d, %Y"), body_style),
        ],
        [
            Paragraph("<b>College / Degree:</b>", bold_body), Paragraph(f"{college} ({degree})", body_style),
            Paragraph("<b>Interview Type:</b>", bold_body), Paragraph(session.get_interview_type_display(), body_style),
        ],
        [
            Paragraph("<b>Target Role:</b>", bold_body), Paragraph(session.target_role, body_style),
            Paragraph("<b>Difficulty Level:</b>", bold_body), Paragraph(session.get_difficulty_display(), body_style),
        ],
    ]
    info_table = Table(info_data, colWidths=[100, 170, 110, 150])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # 3. Overall Performance Summary Banner
    overall = session.overall_score if session.overall_score is not None else 0.0
    readiness = report.readiness_level if report else "Placement Ready"

    banner_data = [
        [
            Paragraph(f"OVERALL INTERVIEW SCORE: <b>{overall:.1f} / 10.0</b>", badge_style),
            Paragraph(f"STATUS: <b>{readiness.upper()}</b>", badge_style)
        ]
    ]
    banner_table = Table(banner_data, colWidths=[280, 250])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), primary_color),
        ('BACKGROUND', (1, 0), (1, 0), success_color if overall >= 6.5 else colors.HexColor('#d97706')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 14))

    # 4. Multi-Domain Score Breakdown Table
    story.append(Paragraph("Competency & Domain Performance Breakdown", h2_style))
    scores_data = [
        [
            Paragraph("<b>Category</b>", bold_body),
            Paragraph("<b>Evaluated Domain</b>", bold_body),
            Paragraph("<b>Score (0-10)</b>", bold_body),
            Paragraph("<b>Proficiency Level</b>", bold_body)
        ],
        [
            Paragraph("Technical", body_style),
            Paragraph("Core Architecture, Concepts & Principles", body_style),
            Paragraph(f"{session.technical_score or overall:.1f}", bold_body),
            Paragraph("Proficient" if (session.technical_score or overall) >= 7.0 else "Intermediate", body_style)
        ],
        [
            Paragraph("Programming & Coding", body_style),
            Paragraph("Code Correctness, Time/Space Complexity", body_style),
            Paragraph(f"{session.coding_score or overall:.1f}", bold_body),
            Paragraph("Proficient" if (session.coding_score or overall) >= 7.0 else "Intermediate", body_style)
        ],
        [
            Paragraph("Project Architecture", body_style),
            Paragraph("Resume Project Depth & Design Decisions", body_style),
            Paragraph(f"{session.project_score or overall:.1f}", bold_body),
            Paragraph("Proficient" if (session.project_score or overall) >= 7.0 else "Intermediate", body_style)
        ],
        [
            Paragraph("HR & Professional", body_style),
            Paragraph("Behavioral Clarity & Communication", body_style),
            Paragraph(f"{session.hr_score or overall:.1f}", bold_body),
            Paragraph("Proficient" if (session.hr_score or overall) >= 7.0 else "Intermediate", body_style)
        ],
    ]
    scores_table = Table(scores_data, colWidths=[120, 220, 90, 100])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 14))

    # 5. Key Strengths, Areas for Improvement, Recommendations
    story.append(Paragraph("Evaluator Observations & Recommendations", h2_style))
    strengths_txt = report.strengths_summary if report and report.strengths_summary else "Clear technical communication and structured problem solving."
    weaknesses_txt = report.weaknesses_summary if report and report.weaknesses_summary else "Deepen production trade-off analysis and algorithmic edge cases."
    recs = report.key_recommendations if report and report.key_recommendations else ["System Design Fundamentals", "LeetCode/HackerRank Practice", "STAR Method"]

    obs_data = [
        [Paragraph("<b>Key Strengths:</b>", bold_body), Paragraph(strengths_txt, body_style)],
        [Paragraph("<b>Areas for Polish:</b>", bold_body), Paragraph(weaknesses_txt, body_style)],
        [Paragraph("<b>Recommended Topics:</b>", bold_body), Paragraph(", ".join(recs), body_style)],
    ]
    obs_table = Table(obs_data, colWidths=[120, 410])
    obs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(obs_table)
    story.append(Spacer(1, 16))

    # 6. Detailed Question-by-Question Analysis
    story.append(Paragraph("Detailed Question-by-Question Assessment", h2_style))

    questions = session.questions.all().order_by('question_number')
    for q in questions:
        has_ans = hasattr(q, 'answer')
        ans_text = q.answer.answer_text if has_ans else "No answer submitted."
        eval_obj = q.answer.evaluation if has_ans and hasattr(q.answer, 'evaluation') else None
        q_score = eval_obj.score if eval_obj else 0.0
        feedback = f"<b>Strengths:</b> {eval_obj.strengths}<br/><b>Improvements:</b> {eval_obj.improvements}" if eval_obj else "Not evaluated."

        q_table_data = [
            [
                Paragraph(f"<b>Q{q.question_number} [{q.get_category_display()}]:</b> {q.text}", bold_body),
                Paragraph(f"Score: <b>{q_score:.1f}/10</b>", ParagraphStyle('Score', parent=bold_body, alignment=2, textColor=primary_color))
            ],
            [
                Paragraph(f"<b>Candidate Answer:</b> {ans_text[:280]}{'...' if len(ans_text) > 280 else ''}", body_style),
                Paragraph("", body_style)
            ],
            [
                Paragraph(f"<b>AI Evaluator Feedback:</b> {feedback}", body_style),
                Paragraph("", body_style)
            ]
        ]
        q_table = Table(q_table_data, colWidths=[430, 100])
        q_table.setStyle(TableStyle([
            ('SPAN', (0, 1), (1, 1)),
            ('SPAN', (0, 2), (1, 2)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(KeepTogether([q_table, Spacer(1, 8)]))

    # Footer note
    story.append(Spacer(1, 12))
    footer_text = f"Generated by AI Interview Preparation System on {session.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC. Document certified under ID {cand_id}."
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.gray, alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer
