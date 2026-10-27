import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


PRESCRIPTION_MEDICINES = [
    {
        "name": "Dolo 650",
        "strength": "650 mg",
        "instructions": "1 tablet twice daily after meals for 5 days",
    },
    {
        "name": "Crocin",
        "strength": "500 mg",
        "instructions": "1 tablet SOS for headache (as needed)",
    },
    {
        "name": "Ecosprin 75",
        "strength": "75 mg",
        "instructions": "1 tablet once daily after dinner",
    },
    {
        "name": "Warfarin 5mg",
        "strength": "5 mg",
        "instructions": "1 tablet once daily in evening with INR monitoring",
    },
    {
        "name": "Zylocran 50mg",
        "strength": "50 mg",
        "instructions": "1 tablet at bedtime for 10 days",
    },
]

DEMO_DISCLAIMER = "SYNTHETIC DEMO PRESCRIPTION — NOT A REAL PRESCRIPTION — FOR TESTING AND DEMO ONLY"


def create_prescription_image(output_path: Path) -> Path:
    """Generates a clean synthetic prescription document image using Pillow."""
    width, height = 850, 1100
    img = Image.new("RGB", (width, height), color="#fcfcfc")
    draw = ImageDraw.Draw(img)

    # Use default bitmap font
    try:
        font_title = ImageFont.load_default()
    except Exception:
        font_title = None

    # Draw border
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline="#0d9488", width=3)
    draw.rectangle([(25, 25), (width - 25, height - 25)], outline="#cbd5e1", width=1)

    # Watermark / Disclaimer Banner at Top
    draw.rectangle([(26, 26), (width - 26, 75)], fill="#fee2e2")
    draw.text((45, 42), DEMO_DISCLAIMER, fill="#991b1b")

    # Clinic Header
    draw.text((50, 95), "CITY MEDICAL CLINIC & PHARMACY", fill="#0f172a")
    draw.text((50, 115), "Dr. Jane Smith, MD — Reg. No. DEMO-12345", fill="#334155")
    draw.text((50, 135), "100 Healthcare Avenue, Suite 400 • Tel: (555) 019-2834", fill="#64748b")
    draw.line([(50, 160), (width - 50, 160)], fill="#0d9488", width=2)

    # Patient Context
    draw.text((50, 180), "PATIENT RECORD", fill="#0f172a")
    draw.text((50, 205), "Patient Name: Alex Mercer", fill="#1e293b")
    draw.text((320, 205), "Age: 52", fill="#1e293b")
    draw.text((440, 205), "Sex: Male", fill="#1e293b")
    draw.text((560, 205), "Date: 2026-10-26", fill="#1e293b")

    draw.text((50, 230), "Diagnosis / Reason: Cardiovascular care, mild fever, and joint aches", fill="#475569")
    draw.text((50, 250), "Allergies: Penicillin (reported)", fill="#475569")
    draw.text((320, 250), "Kidney/Liver: Normal renal function", fill="#475569")
    draw.line([(50, 275), (width - 50, 275)], fill="#e2e8f0", width=1)

    # Rx Symbol
    draw.text((50, 295), "Rx — PRESCRIBED MEDICATIONS:", fill="#0f172a")

    # Medicines List
    y_pos = 340
    for idx, med in enumerate(PRESCRIPTION_MEDICINES, 1):
        # Item block
        draw.text((70, y_pos), f"{idx}. {med['name']} ({med['strength']})", fill="#0f172a")
        draw.text((95, y_pos + 22), f"Sig: {med['instructions']}", fill="#334155")

        if "Zylocran" in med["name"]:
            draw.text((95, y_pos + 42), "[Invented medicine name — not in demo sample catalog]", fill="#b45309")
            y_pos += 70
        else:
            y_pos += 60

    # Physician Signature Area
    draw.line([(50, height - 160), (width - 50, height - 160)], fill="#e2e8f0", width=1)
    draw.text((width - 320, height - 140), "Dr. Jane Smith, MD", fill="#1e293b")
    draw.line([(width - 320, height - 110), (width - 80, height - 110)], fill="#334155", width=1)
    draw.text((width - 320, height - 100), "Authorized Signature", fill="#64748b")

    # Bottom Safety Disclaimer
    draw.rectangle([(26, height - 70), (width - 26, height - 26)], fill="#fee2e2")
    draw.text((45, height - 54), "TEST ARTIFACT ONLY — NEVER DISPENSE OR TAKE MEDICATIONS BASED ON THIS DOCUMENT", fill="#991b1b")

    img.save(output_path, format="PNG")
    return output_path


def create_blurry_prescription_image(clean_png_path: Path, output_path: Path) -> Path:
    """Generates a blurred version of the prescription PNG simulating camera shake or poor focus."""
    with Image.open(clean_png_path) as img:
        blurry = img.filter(ImageFilter.GaussianBlur(radius=2.5))
        blurry.save(output_path, format="PNG")
    return output_path


def create_digital_pdf(output_path: Path) -> Path:
    """Generates a clean digital-text PDF prescription using ReportLab."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#991b1b"),
        alignment=1  # Centered
    )
    title_style = ParagraphStyle(
        "PrescriptionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0f172a")
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569")
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )
    bold_style = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # Top Warning Box
    disclaimer_table = Table([[Paragraph(DEMO_DISCLAIMER, disclaimer_style)]], colWidths=[540])
    disclaimer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fee2e2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f87171")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(disclaimer_table)
    story.append(Spacer(1, 12))

    # Clinic Header
    story.append(Paragraph("CITY MEDICAL CLINIC & PHARMACY", title_style))
    story.append(Paragraph("Dr. Jane Smith, MD &bull; Reg. No. DEMO-12345 &bull; Tel: (555) 019-2834", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0d9488"), spaceBefore=6, spaceAfter=8))

    # Patient Context Table
    patient_info = [
        [
            Paragraph("<b>Patient Name:</b> Alex Mercer", body_style),
            Paragraph("<b>Age:</b> 52 &bull; <b>Sex:</b> Male", body_style),
            Paragraph("<b>Date:</b> 2026-10-26", body_style),
        ],
        [
            Paragraph("<b>Reason:</b> Cardiovascular care, fever, joint pain", body_style),
            Paragraph("<b>Allergies:</b> Penicillin", body_style),
            Paragraph("<b>Kidney/Liver:</b> Normal", body_style),
        ]
    ]
    p_table = Table(patient_info, colWidths=[200, 180, 160])
    p_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(p_table)
    story.append(Spacer(1, 14))

    # Rx Medicines
    story.append(Paragraph("Rx &mdash; PRESCRIBED MEDICATIONS:", bold_style))
    story.append(Spacer(1, 6))

    med_rows = [
        [
            Paragraph("<b>#</b>", bold_style),
            Paragraph("<b>Medication Name</b>", bold_style),
            Paragraph("<b>Strength</b>", bold_style),
            Paragraph("<b>Directions / Frequency / Duration</b>", bold_style),
        ]
    ]
    for idx, med in enumerate(PRESCRIPTION_MEDICINES, 1):
        note = " <i>(Invented name &mdash; not in sample catalog)</i>" if "Zylocran" in med["name"] else ""
        med_rows.append([
            Paragraph(str(idx), body_style),
            Paragraph(f"<b>{med['name']}</b>{note}", body_style),
            Paragraph(med["strength"], body_style),
            Paragraph(med["instructions"], body_style),
        ])

    m_table = Table(med_rows, colWidths=[25, 160, 75, 280])
    m_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(m_table)
    story.append(Spacer(1, 20))

    # Signature and Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=10, spaceAfter=8))
    story.append(Paragraph("Physician Signature: <i>Dr. Jane Smith, MD</i> (Demo Signature)", meta_style))
    story.append(Spacer(1, 14))

    # Bottom Warning Box
    bot_table = Table([[Paragraph("TEST ARTIFACT ONLY &bull; NEVER USE FOR ACTUAL MEDICAL TREATMENT", disclaimer_style)]], colWidths=[540])
    bot_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fee2e2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f87171")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(bot_table)

    doc.build(story)
    return output_path


def create_scanned_pdf(image_path: Path, output_path: Path) -> Path:
    """
    Generates a scanned-style PDF containing ONLY the raster image and no embedded text characters.
    When analyzed, PyMuPDF will detect zero digital characters and trigger RapidOCR.
    """
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # standard letter
    rect = fitz.Rect(18, 18, 594, 774)
    page.insert_image(rect, filename=str(image_path))
    doc.save(str(output_path))
    doc.close()
    return output_path


def generate_all_samples(output_dir: Path) -> dict:
    """Generates all 4 synthetic demo prescription files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_png = output_dir / "sample_prescription.png"
    blurry_png = output_dir / "sample_prescription_blurry.png"
    digital_pdf = output_dir / "sample_prescription_digital.pdf"
    scanned_pdf = output_dir / "sample_prescription_scanned.pdf"

    print(f"Generating synthetic prescription PNG -> {clean_png}")
    create_prescription_image(clean_png)

    print(f"Generating blurry synthetic prescription PNG -> {blurry_png}")
    create_blurry_prescription_image(clean_png, blurry_png)

    print(f"Generating digital-text prescription PDF -> {digital_pdf}")
    create_digital_pdf(digital_pdf)

    print(f"Generating scanned-style raster PDF -> {scanned_pdf}")
    create_scanned_pdf(clean_png, scanned_pdf)

    print("Successfully generated all 4 synthetic prescription demo files.")
    return {
        "clean_png": clean_png,
        "blurry_png": blurry_png,
        "digital_pdf": digital_pdf,
        "scanned_pdf": scanned_pdf,
    }


if __name__ == "__main__":
    target_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "sample_prescriptions"
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1]).resolve()
    generate_all_samples(target_dir)
