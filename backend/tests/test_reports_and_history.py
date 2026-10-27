import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app, cleanup_expired_analyses
from app.core.config import settings
from app.db.database import get_db
from app.db.repositories import save_analysis, get_analysis_by_id
from app.schemas.analysis import AnalysisResponse, Medicine, PatientContext
from app.services.report_service import generate_pdf_report


def test_generate_pdf_report_and_content():
    """Verify ReportLab PDF generation generates a valid PDF file."""
    test_id = f"test-pdf-{uuid.uuid4().hex}"
    analysis = AnalysisResponse(
        id=test_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        original_name="prescription_sample.pdf",
        stored_name=f"{test_id}.pdf",
        file_kind="pdf",
        text_source="pdf_text",
        page_count=1,
        medicines=[
            Medicine(
                id="m1",
                name_text="Dolo 650",
                strength="650 mg",
                dose="1 tab",
                frequency="twice daily",
                duration="5 days",
                match_status="matched",
                matched_id="paracetamol_dolo",
                ingredients=["paracetamol"],
                confirmed=True
            ),
            Medicine(
                id="m2",
                name_text="Crocin",
                strength="500 mg",
                dose="1 tab",
                frequency="as needed",
                duration="3 days",
                match_status="matched",
                matched_id="paracetamol_crocin",
                ingredients=["paracetamol"],
                confirmed=True
            ),
            Medicine(
                id="m3",
                name_text="Warfarin",
                strength="5 mg",
                dose="1 tab",
                frequency="once daily",
                duration="ongoing",
                match_status="matched",
                matched_id="warfarin_generic",
                ingredients=["warfarin"],
                confirmed=True
            ),
            Medicine(
                id="m4",
                name_text="Aspirin",
                strength="75 mg",
                dose="1 tab",
                frequency="once daily",
                duration="ongoing",
                match_status="matched",
                matched_id="aspirin_ecosprin",
                ingredients=["aspirin"],
                confirmed=True
            ),
            Medicine(
                id="m5",
                name_text="MysteriousHerb100",
                strength="100 mg",
                match_status="not_found",
                ingredients=[],
                confirmed=True
            )
        ],
        context=PatientContext(
            age=45,
            reason="Cardiovascular safety and fever",
            allergies="Penicillin",
            pregnancy="no",
            kidney_liver="Normal renal function"
        ),
        results={
            "interactions": [
                {
                    "rule_id": "r1",
                    "medicines": ["m3", "m4"],
                    "severity": "high",
                    "note": "Warfarin and Aspirin may increase the risk of bleeding.",
                    "source_label": "Sample demo rule, verify with a pharmacist"
                }
            ],
            "duplicates": [
                {
                    "ingredient": "paracetamol",
                    "medicines": ["m1", "m2"]
                }
            ],
            "coverage": {
                "total": 5,
                "found_in_list": 4,
                "not_found": ["m5"]
            },
            "evidence": [
                {
                    "medicine_id": "m1",
                    "findings": ["Paracetamol is used for antipyretic and analgesic relief."],
                    "sources": [{"title": "NIH StatPearls", "url": "https://ncbi.nlm.nih.gov"}],
                    "status": "ok"
                },
                {
                    "medicine_id": "m5",
                    "findings": ["No established clinical monographs found."],
                    "sources": [],
                    "status": "no_source"
                }
            ],
            "alternatives": {
                "status": "ok",
                "missing": [],
                "items": [
                    {
                        "for_medicine_id": "m1",
                        "options": ["Discuss paracetamol dosage limits with your doctor"],
                        "sources": []
                    }
                ]
            },
            "review": {
                "issues": [
                    {"where": "evidence m5", "issue": "No source found for MysteriousHerb100"}
                ]
            },
            "flags": ["[Removed by safety check. Please ask your doctor or pharmacist.]"],
            "notice": "Only the medicines and rules in our sample list were checked. A missing warning does not mean there is no interaction."
        },
        status="done"
    )

    pdf_path = generate_pdf_report(analysis)
    assert pdf_path.exists()
    assert pdf_path.is_file()

    # Read bytes and verify valid PDF header
    with open(pdf_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"

    # Clean up test file
    if pdf_path.exists():
        pdf_path.unlink()


def test_get_report_endpoint():
    """Test GET /api/analyses/{id}/report returns PDF."""
    client = TestClient(app)
    test_id = f"test-endpoint-{uuid.uuid4().hex}"
    now_iso = datetime.now(timezone.utc).isoformat()

    save_analysis(
        analysis_id=test_id,
        created_at=now_iso,
        original_name="test_rx.png",
        stored_name=f"{test_id}.png",
        file_kind="image",
        text_source="ocr",
        page_count=1,
        extracted_text="Dolo 650",
        medicines=[
            {
                "id": "m1",
                "name_text": "Dolo 650",
                "strength": "650 mg",
                "match_status": "matched",
                "matched_id": "paracetamol_dolo",
                "ingredients": ["paracetamol"],
                "confirmed": True
            }
        ],
        status="done"
    )

    response = client.get(f"/api/analyses/{test_id}/report")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")

    # Clean up generated report
    report_file = settings.report_path / f"medigraph_report_{test_id}.pdf"
    if report_file.exists():
        report_file.unlink()


def test_history_listing_and_deletion():
    """Test GET /api/analyses and DELETE /api/analyses/{id} cleans database and disk files."""
    client = TestClient(app)
    test_id = f"test-del-{uuid.uuid4().hex}"
    stored_name = f"{test_id}.png"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Create dummy upload and report files on disk
    upload_file = settings.upload_path / stored_name
    upload_file.write_text("dummy upload bytes")

    report_file = settings.report_path / f"medigraph_report_{test_id}.pdf"
    report_file.write_text("dummy report bytes")

    save_analysis(
        analysis_id=test_id,
        created_at=now_iso,
        original_name="deletion_rx.png",
        stored_name=stored_name,
        file_kind="image",
        text_source="ocr",
        page_count=1,
        extracted_text="Crocin 500",
        medicines=[
            {
                "id": "m1",
                "name_text": "Crocin",
                "strength": "500 mg",
                "match_status": "matched",
                "ingredients": ["paracetamol"],
                "confirmed": True
            }
        ],
        status="done"
    )

    # 1. Verify it appears in History list
    res_list = client.get("/api/analyses")
    assert res_list.status_code == 200
    analyses = res_list.json()
    assert any(a["id"] == test_id for a in analyses)

    # 2. Delete it
    res_del = client.delete(f"/api/analyses/{test_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"

    # 3. Verify files on disk are deleted
    assert not upload_file.exists()
    assert not report_file.exists()

    # 4. Verify database record is deleted
    assert get_analysis_by_id(test_id) is None
    res_get = client.get(f"/api/analyses/{test_id}")
    assert res_get.status_code == 404


def test_automatic_retention_cleanup():
    """Test cleanup_expired_analyses purges items older than RETENTION_DAYS."""
    test_old_id = f"test-old-{uuid.uuid4().hex}"
    test_recent_id = f"test-recent-{uuid.uuid4().hex}"

    old_date = (datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS + 2)).isoformat()
    recent_date = datetime.now(timezone.utc).isoformat()

    # Create files on disk for old analysis
    old_upload = settings.upload_path / f"{test_old_id}.png"
    old_upload.write_text("old file")
    old_report = settings.report_path / f"medigraph_report_{test_old_id}.pdf"
    old_report.write_text("old report")

    # Create files on disk for recent analysis
    recent_upload = settings.upload_path / f"{test_recent_id}.png"
    recent_upload.write_text("recent file")
    recent_report = settings.report_path / f"medigraph_report_{test_recent_id}.pdf"
    recent_report.write_text("recent report")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analyses (id, created_at, original_name, stored_name, file_kind, text_source, page_count, extracted_text, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (test_old_id, old_date, "old_rx.png", f"{test_old_id}.png", "image", "ocr", 1, "text", "done")
        )
        cursor.execute(
            """
            INSERT INTO analyses (id, created_at, original_name, stored_name, file_kind, text_source, page_count, extracted_text, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (test_recent_id, recent_date, "recent_rx.png", f"{test_recent_id}.png", "image", "ocr", 1, "text", "done")
        )
        conn.commit()

    # Run cleanup
    cleanup_expired_analyses()

    # Old analysis must be purged from database and disk
    assert not old_upload.exists()
    assert not old_report.exists()
    assert get_analysis_by_id(test_old_id) is None

    # Recent analysis must be preserved
    assert recent_upload.exists()
    assert recent_report.exists()
    assert get_analysis_by_id(test_recent_id) is not None

    # Clean up recent test artifacts
    if recent_upload.exists():
        recent_upload.unlink()
    if recent_report.exists():
        recent_report.unlink()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses WHERE id = ?", (test_recent_id,))
        conn.commit()
