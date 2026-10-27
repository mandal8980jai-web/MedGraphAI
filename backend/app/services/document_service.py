import io
from pathlib import Path
from typing import Tuple
from PIL import Image
from fastapi import HTTPException, UploadFile
from app.core.config import settings
from app.core.security import generate_stored_filename, sanitize_filename


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}


def validate_file_signature(content: bytes, declared_ext: str) -> str:
    """Validate true file signatures against magic bytes."""
    ext = declared_ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Unsupported file type '{declared_ext}'. Please upload PNG, JPG, WebP, or PDF."}
        )

    # Check magic signatures
    if ext == ".png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(status_code=400, detail={"error": "File signature does not match PNG format."})
        kind = "image"
    elif ext in {".jpg", ".jpeg"}:
        if not content.startswith(b"\xff\xd8\xff"):
            raise HTTPException(status_code=400, detail={"error": "File signature does not match JPEG format."})
        kind = "image"
    elif ext == ".webp":
        if not (content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP"):
            raise HTTPException(status_code=400, detail={"error": "File signature does not match WebP format."})
        kind = "image"
    elif ext == ".pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail={"error": "File signature does not match PDF format."})
        kind = "pdf"
    else:
        raise HTTPException(status_code=400, detail={"error": "Unsupported file format."})

    # For images, verify image integrity with Pillow
    if kind == "image":
        try:
            with Image.open(io.BytesIO(content)) as img:
                img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail={"error": "Corrupted or invalid image file."})

    return kind


async def save_uploaded_document(file: UploadFile) -> Tuple[str, str, str, Path, bytes]:
    """Validate and safely persist uploaded document to UPLOAD_DIR."""
    original_name = sanitize_filename(file.filename or "upload")
    declared_ext = Path(original_name).suffix.lower()

    if not declared_ext or declared_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={"error": "File must have an allowed extension: .png, .jpg, .jpeg, .webp, or .pdf"}
        )

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail={"error": f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB} MB."}
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail={"error": "Uploaded file is empty."})

    file_kind = validate_file_signature(content, declared_ext)
    stored_name = generate_stored_filename(declared_ext)
    file_path = settings.upload_path / stored_name

    with open(file_path, "wb") as f:
        f.write(content)

    return original_name, stored_name, file_kind, file_path, content
