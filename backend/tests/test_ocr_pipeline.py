import fitz
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.services.pdf_text_service import extract_pdf_text


def create_digital_pdf(tmp_path: Path, text: str) -> Path:
    pdf_path = tmp_path / "digital_rx.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def create_scanned_pdf(tmp_path: Path) -> Path:
    # A PDF page with no embedded text characters (simulate scanned document)
    pdf_path = tmp_path / "scanned_rx.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # Draw a line or shape without text
    page.draw_rect(fitz.Rect(50, 50, 200, 200), color=(0, 0, 0), fill=(0.9, 0.9, 0.9))
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def create_multi_page_pdf(tmp_path: Path, page_count: int) -> Path:
    pdf_path = tmp_path / f"multi_page_{page_count}.pdf"
    doc = fitz.open()
    for i in range(page_count):
        p = doc.new_page()
        p.insert_text((50, 50), f"Prescription Content for Page {i+1} with sufficient length to be digital.")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_digital_pdf_extraction(tmp_path):
    text = "Rx: Dolo 650 1 tablet twice daily for 5 days. Dr Smith Clinic."
    pdf_path = create_digital_pdf(tmp_path, text)

    is_scanned, page_count, pages = extract_pdf_text(pdf_path)
    assert not is_scanned
    assert page_count == 1
    assert "Dolo 650" in pages[0]["text"]


def test_scanned_pdf_detection(tmp_path):
    pdf_path = create_scanned_pdf(tmp_path)
    is_scanned, page_count, pages = extract_pdf_text(pdf_path)
    assert is_scanned
    assert page_count == 1


def test_pdf_page_limit(tmp_path):
    # 14 pages PDF - should cap at 10
    pdf_path = create_multi_page_pdf(tmp_path, 14)
    is_scanned, page_count, pages = extract_pdf_text(pdf_path)
    assert page_count == 10
    assert len(pages) == 10


def test_full_document_and_confirmation_flow(tmp_path):
    text = "Prescription:\n1. Dolo 650 twice daily for 5 days\n2. Ecosprin 75 once daily\n"
    pdf_path = create_digital_pdf(tmp_path, text)

    with TestClient(app) as client:
        with open(pdf_path, "rb") as f:
            upload_res = client.post(
                "/api/documents",
                files={"file": ("prescription.pdf", f, "application/pdf")}
            )
        assert upload_res.status_code == 200
        data = upload_res.json()
        analysis_id = data["id"]
        assert data["file_kind"] == "pdf"
        assert len(data["medicines"]) >= 1

        # Check retrieval of file for side-by-side preview
        file_res = client.get(f"/api/analyses/{analysis_id}/file")
        assert file_res.status_code == 200
        assert file_res.headers["content-type"] == "application/pdf"

        # Update and confirm medicines
        meds = data["medicines"]
        for m in meds:
            m["confirmed"] = True

        update_res = client.put(
            f"/api/analyses/{analysis_id}/medicines",
            json={
                "medicines": meds,
                "context": {
                    "age": 45,
                    "reason": "Fever and mild headache",
                    "allergies": "None",
                    "pregnancy": "no",
                    "kidney_liver": "Normal"
                }
            }
        )
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["status"] == "confirmed"
        assert updated_data["context"]["age"] == 45
        assert all(m["confirmed"] for m in updated_data["medicines"])
