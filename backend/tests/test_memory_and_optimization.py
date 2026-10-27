import io
import fitz
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.memory import get_current_rss_mb
from app.services.ocr_service import (
    get_ocr_engine,
    preprocess_image_for_ocr,
    ocr_image,
    ocr_scanned_pdf
)
from app.services.medical_evidence_service import (
    _EVIDENCE_CACHE,
    _set_evidence_cache,
    MAX_EVIDENCE_CACHE_SIZE
)


def test_health_endpoint_memory_fields():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "llm_key_set" in data
        assert "model" in data
        assert "memory_rss_mb" in data
        assert isinstance(data["memory_rss_mb"], (int, float))
        assert data["max_upload_mb"] == settings.MAX_UPLOAD_MB
        assert data["worker_concurrency"] == 1

        api_res = client.get("/api/health")
        assert api_res.status_code == 200
        assert api_res.json()["status"] == "ok"


def test_ocr_engine_lazy_singleton():
    engine1 = get_ocr_engine()
    engine2 = get_ocr_engine()
    assert engine1 is engine2
    assert engine1 is not None


def test_preprocess_image_resizing():
    # Create an oversized test image (3600 x 2400)
    oversized = Image.new("RGB", (3600, 2400), color=(255, 255, 255))
    buf = io.BytesIO()
    oversized.save(buf, format="JPEG", quality=85)
    raw_bytes = buf.getvalue()

    arr = preprocess_image_for_ocr(raw_bytes)
    assert isinstance(arr, np.ndarray)
    h, w, c = arr.shape
    assert c == 3
    # Max dimension should be <= settings.OCR_MAX_IMAGE_DIMENSION (1800)
    assert max(h, w) <= settings.OCR_MAX_IMAGE_DIMENSION
    # Aspect ratio should be preserved: 3600/2400 = 1.5
    assert abs((w / h) - 1.5) < 0.05


def test_preprocess_image_normal_size_unmodified():
    # An image smaller than max dimension (800 x 600) should preserve its exact size
    normal = Image.new("RGB", (800, 600), color=(255, 255, 255))
    buf = io.BytesIO()
    normal.save(buf, format="PNG")

    arr = preprocess_image_for_ocr(buf.getvalue())
    h, w, c = arr.shape
    assert (w, h) == (800, 600)
    assert c == 3


def test_scanned_pdf_page_by_page_and_close(tmp_path):
    pdf_path = tmp_path / "scanned_test.pdf"
    doc = fitz.open()
    for i in range(3):
        p = doc.new_page(width=612, height=792)
        p.insert_text((50, 100), f"Medication page {i+1}: Amoxicillin 500mg")
    doc.save(str(pdf_path))
    doc.close()

    pages = ocr_scanned_pdf(pdf_path)
    assert len(pages) == 3
    assert pages[0]["page"] == 1
    assert pages[1]["page"] == 2
    assert pages[2]["page"] == 3


def test_evidence_cache_bounded_size():
    # Populate cache beyond MAX_EVIDENCE_CACHE_SIZE
    initial_keys = list(_EVIDENCE_CACHE.keys())
    for i in range(MAX_EVIDENCE_CACHE_SIZE + 20):
        _set_evidence_cache(f"test_med_{i}", {
            "medicine_id": f"id_{i}",
            "findings": [f"Finding {i}"],
            "sources": []
        })

    assert len(_EVIDENCE_CACHE) <= MAX_EVIDENCE_CACHE_SIZE


def test_upload_chunked_size_rejection(monkeypatch):
    with TestClient(app) as client:
        # Lower MAX_UPLOAD_MB to 0.002 MB (~2 KB)
        monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 0.002)
        large_bytes = b"A" * 5000
        res = client.post(
            "/api/documents",
            files={"file": ("too_large.png", large_bytes, "image/png")}
        )
        assert res.status_code == 400
        error_msg = str(res.json().get("detail", {}).get("error", ""))
        assert "exceeds" in error_msg.lower()
