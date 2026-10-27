import html
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
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

from app.core.config import settings
from app.schemas.analysis import AnalysisResponse


def _esc(val: Any) -> str:
    """Escapes HTML entities for safe inclusion in ReportLab Paragraphs."""
    if val is None:
        return ""
    return html.escape(str(val))


def generate_pdf_report(analysis: AnalysisResponse) -> Path:
    """
    Generates a comprehensive clinical-review PDF report using ReportLab.
    Saves the report to settings.report_path / f"medigraph_report_{analysis.id}.pdf".
    """
    settings.report_path.mkdir(parents=True, exist_ok=True)
    report_file = settings.report_path / f"medigraph_report_{analysis.id}.pdf"

    doc = SimpleDocTemplate(
        str(report_file),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569")
    )
    h2_style = ParagraphStyle(
        "Heading2Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )
    body_muted = ParagraphStyle(
        "BodyMuted",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748b")
    )
    alert_title_style = ParagraphStyle(
        "AlertTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#991b1b")
    )
    alert_body_style = ParagraphStyle(
        "AlertBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#7f1d1d")
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )

    story = []

    # 1. Title & Header Meta
    story.append(Paragraph("MediGraph AI &mdash; Medication Safety Report", title_style))
    created_time = analysis.created_at[:19].replace("T", " ") if analysis.created_at else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    header_meta = f"Analysis ID: {_esc(analysis.id)} | Document: {_esc(analysis.original_name)} | Date Generated: {_esc(created_time)} UTC"
    story.append(Paragraph(header_meta, subtitle_style))
    story.append(Spacer(1, 10))

    # 2. Prominent Safety Notice Box
    notice_text = (
        "<b>IMPORTANT MEDICAL SAFETY NOTICE:</b> MediGraph AI is an experimental prototype for medication safety research and education. "
        "It does not provide medical advice, diagnosis, or treatment recommendations. Always consult a qualified physician or "
        "pharmacist before starting, stopping, or changing any medication.<br/><br/>"
        "<b>Sample Coverage Notice:</b> Only the medicines and rules in our sample list were checked. "
        "A missing warning does not mean there is no interaction. Medicines not in our sample list are NEVER assumed to be safe."
    )
    notice_table = Table(
        [[Paragraph(notice_text, alert_body_style)]],
        colWidths=[540]
    )
    notice_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f87171")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(notice_table)
    story.append(Spacer(1, 12))

    # 3. Patient Context (if specified)
    story.append(Paragraph("Patient Context (Provided for Safety Review)", h2_style))
    ctx = analysis.context
    ctx_data = [
        [
            Paragraph("<b>Age:</b> " + (_esc(ctx.age) if ctx and ctx.age else "Not specified"), table_cell_style),
            Paragraph("<b>Pregnancy / Nursing:</b> " + (_esc(ctx.pregnancy) if ctx and ctx.pregnancy else "Not specified"), table_cell_style),
        ],
        [
            Paragraph("<b>Reason for Prescription:</b> " + (_esc(ctx.reason) if ctx and ctx.reason else "Not specified"), table_cell_style),
            Paragraph("<b>Known Allergies:</b> " + (_esc(ctx.allergies) if ctx and ctx.allergies else "None specified"), table_cell_style),
        ],
        [
            Paragraph("<b>Kidney / Liver Conditions:</b> " + (_esc(ctx.kidney_liver) if ctx and ctx.kidney_liver else "None specified"), table_cell_style),
            Paragraph("", table_cell_style),
        ]
    ]
    ctx_table = Table(ctx_data, colWidths=[270, 270])
    ctx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ctx_table)
    story.append(Spacer(1, 12))

    # 4. Confirmed Medicines Table
    story.append(Paragraph("1. Confirmed Medicines", h2_style))
    story.append(Paragraph("The following medicines were extracted and confirmed for this analysis:", body_muted))
    story.append(Spacer(1, 4))

    med_header = [
        Paragraph("Medicine Name", table_header_style),
        Paragraph("Strength", table_header_style),
        Paragraph("Dose", table_header_style),
        Paragraph("Frequency", table_header_style),
        Paragraph("Duration", table_header_style),
        Paragraph("Catalog Match", table_header_style),
        Paragraph("Active Ingredients", table_header_style),
    ]
    med_rows = [med_header]

    for m in analysis.medicines:
        match_label = "Matched" if m.match_status == "matched" else ("Several possible" if m.match_status == "several_possible" else "Not in list")
        ingredients_str = ", ".join(m.ingredients) if m.ingredients else "Unknown"
        med_rows.append([
            Paragraph(_esc(m.name_text), table_cell_style),
            Paragraph(_esc(m.strength or "-"), table_cell_style),
            Paragraph(_esc(m.dose or "-"), table_cell_style),
            Paragraph(_esc(m.frequency or "-"), table_cell_style),
            Paragraph(_esc(m.duration or "-"), table_cell_style),
            Paragraph(_esc(match_label), table_cell_style),
            Paragraph(_esc(ingredients_str), table_cell_style),
        ])

    med_table = Table(med_rows, colWidths=[105, 55, 65, 75, 60, 80, 100])
    med_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(med_table)
    story.append(Spacer(1, 14))

    results = analysis.results or {}
    interactions = results.get("interactions", [])
    duplicates = results.get("duplicates", [])
    coverage = results.get("coverage", {})
    evidence_list = results.get("evidence", [])
    alternatives = results.get("alternatives", {})
    review = results.get("review", {})
    flags = results.get("flags", [])

    # Medicine lookup helper
    med_lookup = {m.id: m.name_text for m in analysis.medicines}

    # 5. Interaction Findings
    story.append(Paragraph("2. Interaction Findings (Deterministic Safety Checks)", h2_style))
    if interactions:
        story.append(Paragraph(
            "<b>Warning:</b> Potential drug-drug interactions detected from our verified clinical rule database. "
            "Please review these carefully with a pharmacist or physician.",
            body_style
        ))
        story.append(Spacer(1, 4))

        int_header = [
            Paragraph("Medicines Involved", table_header_style),
            Paragraph("Severity", table_header_style),
            Paragraph("Clinical Note", table_header_style),
            Paragraph("Rule Source", table_header_style),
        ]
        int_rows = [int_header]
        for item in interactions:
            med_names = [med_lookup.get(mid, mid) for mid in item.get("medicines", [])]
            med_str = " + ".join(med_names)
            sev = item.get("severity", "unknown").upper()
            note = item.get("note", "Potential interaction detected.")
            source = item.get("source_label", "Sample demo rule")
            int_rows.append([
                Paragraph(_esc(med_str), table_cell_style),
                Paragraph(f"<b>{_esc(sev)}</b>", table_cell_style),
                Paragraph(_esc(note), table_cell_style),
                Paragraph(_esc(source), table_cell_style),
            ])

        int_table = Table(int_rows, colWidths=[120, 65, 235, 120])
        int_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f87171")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(int_table)
    else:
        story.append(Paragraph(
            "No known interactions detected among the checked medicines in our sample rules. "
            "<i>(Note: A missing warning does not mean there is no interaction.)</i>",
            body_style
        ))

    story.append(Spacer(1, 12))

    # 6. Duplicate Active Ingredients
    story.append(Paragraph("3. Duplicate Active Ingredients", h2_style))
    if duplicates:
        story.append(Paragraph(
            "<b>Warning:</b> The following active ingredients appear in more than one prescribed medicine. "
            "This can lead to accidental overdose or heightened toxicity.",
            body_style
        ))
        story.append(Spacer(1, 4))
        for dup in duplicates:
            ing = dup.get("ingredient", "Unknown")
            med_names = [med_lookup.get(mid, mid) for mid in dup.get("medicines", [])]
            story.append(Paragraph(
                f"&bull; <b>{_esc(ing.capitalize())}:</b> Prescribed in multiple medicines: <b>{_esc(', '.join(med_names))}</b>",
                body_style
            ))
    else:
        story.append(Paragraph("No duplicate active ingredients were detected among the confirmed medicines.", body_style))

    story.append(Spacer(1, 12))

    # 7. Unchecked Medicines & Coverage
    story.append(Paragraph("4. Interaction Rule Coverage & Unchecked Medicines", h2_style))
    total_meds = coverage.get("total", len(analysis.medicines))
    found_in_list = coverage.get("found_in_list", 0)
    not_found_ids = coverage.get("not_found", [])

    coverage_text = f"<b>Coverage:</b> {found_in_list} of {total_meds} medicines were found in our demonstration catalog and checked for known rules."
    story.append(Paragraph(coverage_text, body_style))
    story.append(Spacer(1, 4))

    if not_found_ids:
        story.append(Paragraph(
            "<b>Not checked (not in our sample list):</b>",
            alert_title_style
        ))
        for nfid in not_found_ids:
            name = med_lookup.get(nfid, nfid)
            story.append(Paragraph(
                f"&bull; <b>{_esc(name)}</b> &mdash; This medicine is not in our sample catalog. "
                "It was NOT checked against interaction rules and is <b>never assumed to be safe</b>.",
                alert_body_style
            ))
    else:
        story.append(Paragraph("All confirmed medicines were present in our demo catalog.", body_muted))

    story.append(Spacer(1, 14))

    # 8. Evidence & Scientific Research
    story.append(Paragraph("5. Pharmacist Evidence Research & Sources", h2_style))
    story.append(Paragraph(
        "Scientific research grounded with web sources. If no external sources were returned by search, "
        "findings are marked accordingly.",
        body_muted
    ))
    story.append(Spacer(1, 6))

    if evidence_list:
        for ev in evidence_list:
            mid = ev.get("medicine_id", "")
            m_name = med_lookup.get(mid, mid or "Medicine")
            status = ev.get("status", "ok")
            findings = ev.get("findings", [])
            sources = ev.get("sources", [])

            story.append(Paragraph(f"<b>Evidence for {_esc(m_name)}:</b>", body_style))
            if status == "unavailable":
                story.append(Paragraph("<i>Evidence research was unavailable for this medicine.</i>", body_muted))
            elif status == "no_source":
                for f in findings:
                    story.append(Paragraph(f"&bull; {_esc(f)} <i>(No external source found)</i>", body_style))
            else:
                for f in findings:
                    story.append(Paragraph(f"&bull; {_esc(f)}", body_style))

            if sources:
                source_links = []
                for s in sources:
                    s_title = s.get("title") or s.get("url") or "Source"
                    s_url = s.get("url") or ""
                    if s_url:
                        source_links.append(f'<a href="{_esc(s_url)}" color="#0284c7"><u>{_esc(s_title)}</u></a>')
                    else:
                        source_links.append(_esc(s_title))
                story.append(Paragraph(f"<b>Sources:</b> {', '.join(source_links)}", body_muted))
            else:
                story.append(Paragraph("<b>Sources:</b> No source links available.", body_muted))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No evidence research performed or available for this run.", body_muted))

    story.append(Spacer(1, 10))

    # 9. Alternative Options to Discuss with Clinician
    story.append(Paragraph("6. Alternative Treatment Options (For Discussion with Doctor)", h2_style))
    alt_status = alternatives.get("status", "unavailable")
    alt_missing = alternatives.get("missing", [])
    alt_items = alternatives.get("items", [])

    if alt_status == "needs_more_info":
        missing_str = ", ".join(alt_missing) if alt_missing else "Required patient context details"
        story.append(Paragraph(
            f"<b>Missing Context:</b> Clinical alternatives cannot be safely evaluated without complete patient context. "
            f"Missing required fields: <b>{_esc(missing_str)}</b>. Please provide these details to evaluate alternatives.",
            body_style
        ))
    elif alt_status == "ok" and alt_items:
        story.append(Paragraph(
            "<b>Important:</b> The following options are educational possibilities to discuss with a licensed physician. "
            "Never switch, stop, or change any medication without direct clinical consultation.",
            body_style
        ))
        story.append(Spacer(1, 4))
        for item in alt_items:
            mid = item.get("for_medicine_id", "")
            m_name = med_lookup.get(mid, mid or "Medicine")
            opts = item.get("options", [])
            story.append(Paragraph(f"<b>Discussion Options for {_esc(m_name)}:</b>", body_style))
            for opt in opts:
                story.append(Paragraph(f"&bull; {_esc(opt)}", body_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph(
            "Alternative research was not requested, unavailable, or patient context was incomplete.",
            body_muted
        ))

    story.append(Spacer(1, 12))

    # 10. Safety Critic Review & Safety Flags
    story.append(Paragraph("7. Safety Critic Review & Flagged Statements", h2_style))
    review_issues = review.get("issues", []) if isinstance(review, dict) else []
    if review_issues:
        story.append(Paragraph("<b>Safety Review Issues Identified:</b>", alert_title_style))
        for issue in review_issues:
            w = issue.get("where", "General")
            iss = issue.get("issue", "Safety flag")
            story.append(Paragraph(f"&bull; <b>[{_esc(w)}]</b> {_esc(iss)}", alert_body_style))
        story.append(Spacer(1, 4))

    if flags:
        story.append(Paragraph("<b>Safety Gate Interventions:</b>", alert_title_style))
        for fl in flags:
            story.append(Paragraph(f"&bull; {_esc(fl)}", alert_body_style))
    elif not review_issues:
        story.append(Paragraph("No safety critic flags or phrase violations were identified.", body_muted))

    story.append(Spacer(1, 14))

    # 11. Final Limitations & Clinician Review Notice
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=6, spaceAfter=8))
    story.append(Paragraph("<b>Limitations & Final Disclaimer:</b>", h2_style))
    final_disclaimer = (
        "This report was automatically synthesized by MediGraph AI using sample interaction databases and AI grounding tools. "
        "It is NOT a complete clinical review, medical diagnosis, or prescription directive. "
        "Medical knowledge evolves constantly and individual health factors drastically affect drug metabolism and safety.<br/><br/>"
        "<b>Action Required:</b> Please review this report in its entirety with a qualified healthcare provider, physician, "
        "or clinical pharmacist before making any health or medication decisions."
    )
    story.append(Paragraph(final_disclaimer, body_muted))

    # Build the document
    doc.build(story)
    return report_file
