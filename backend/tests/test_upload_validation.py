import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import get_safe_file_path
from app.services.document_service import validate_file_signature


def make_png_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="white")
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="white")
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_webp_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="white")
    img.save(buf, format="WEBP")
    return buf.getvalue()


def test_valid_signatures():
    png_bytes = make_png_bytes()
    assert validate_file_signature(png_bytes, ".png") == "image"

    jpeg_bytes = make_jpeg_bytes()
    assert validate_file_signature(jpeg_bytes, ".jpg") == "image"

    webp_bytes = make_webp_bytes()
    assert validate_file_signature(webp_bytes, ".webp") == "image"

    pdf_bytes = b"%PDF-1.4 sample pdf content"
    assert validate_file_signature(pdf_bytes, ".pdf") == "pdf"


def test_invalid_signature_txt_renamed_to_png():
    fake_png = b"This is plain text pretending to be a PNG."
    with pytest.raises(Exception):
        validate_file_signature(fake_png, ".png")


def test_path_traversal_prevention():
    """Verify get_safe_file_path blocks path traversal attempts."""
    with pytest.raises(Exception):
        get_safe_file_path("../../etc/passwd")

    with pytest.raises(Exception):
        get_safe_file_path("..\\..\\windows\\system32\\cmd.exe")


def test_upload_api_validation(monkeypatch):
    with TestClient(app) as client:
        # 1. Invalid extension
        res = client.post(
            "/api/documents",
            files={"file": ("malicious.exe", b"MZ......", "application/octet-stream")}
        )
        assert res.status_code == 400

        # 2. Fake signature (wrong real type)
        res = client.post(
            "/api/documents",
            files={"file": ("prescription.png", b"Not a real PNG", "image/png")}
        )
        assert res.status_code == 400

        # 3. Empty file
        res = client.post(
            "/api/documents",
            files={"file": ("empty.png", b"", "image/png")}
        )
        assert res.status_code == 400

        # 4. Oversize file check
        monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 0.001)  # ~1 KB limit for testing
        large_bytes = b"X" * 5000
        res = client.post(
            "/api/documents",
            files={"file": ("large.png", large_bytes, "image/png")}
        )
        assert res.status_code == 400
        assert "exceeds" in res.json().get("error", "").lower() or res.status_code == 400
        monkeypatch.undo()

        # 5. Path-like filenames sanitized safely
        png_bytes = make_png_bytes()
        res = client.post(
            "/api/documents",
            files={"file": ("../../etc/passwd.png", png_bytes, "image/png")}
        )
        assert res.status_code == 200
        data = res.json()
        assert not data["stored_name"].startswith("..")
        assert "/" not in data["stored_name"]
        assert "\\" not in data["stored_name"]

        # 6. Valid JPEG upload
        jpeg_bytes = make_jpeg_bytes()
        res = client.post(
            "/api/documents",
            files={"file": ("test_rx.jpg", jpeg_bytes, "image/jpeg")}
        )
        assert res.status_code == 200
        assert res.json()["file_kind"] == "image"

        # 7. Valid WebP upload
        webp_bytes = make_webp_bytes()
        res = client.post(
            "/api/documents",
            files={"file": ("test_rx.webp", webp_bytes, "image/webp")}
        )
        assert res.status_code == 200
        assert res.json()["file_kind"] == "image"

        # 8. Valid PDF upload
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
        res = client.post(
            "/api/documents",
            files={"file": ("test_rx.pdf", pdf_bytes, "application/pdf")}
        )
        assert res.status_code == 200
        assert res.json()["file_kind"] == "pdf"
