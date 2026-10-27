import io
from pathlib import Path
from typing import Tuple
from PIL import Image
from fastapi import HTTPException, UploadFile
from app.core.config import settings
from app.core.security import generate_stored_filename, sanitize_filename
from app.core.logging import logger

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
CHUNK_SIZE = 64 * 1024  # 64 KB streaming buffer

# Decompression bomb protection for low-RAM Render 512 MB instances
Image.MAX_IMAGE_PIXELS = 50_000_000


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


def validate_file_on_disk(file_path: Path, declared_ext: str) -> str:
    """Validate file header signature and integrity from disk without loading full file into RAM."""
    ext = declared_ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Unsupported file type '{declared_ext}'. Please upload PNG, JPG, WebP, or PDF."}
        )

    with open(file_path, "rb") as f:
        header = f.read(4096)

    if ext == ".png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(status_code=400, detail={"error": "File signature does not match PNG format."})
        kind = "image"
    elif ext in {".jpg", ".jpeg"}:
        if not header.startswith(b"\xff\xd8\xff"):
            raise HTTPException(status_code=400, detail={"error": "File signature does not match JPEG format."})
        kind = "image"
    elif ext == ".webp":
        if not (header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP"):
            raise HTTPException(status_code=400, detail={"error": "File signature does not match WebP format."})
        kind = "image"
    elif ext == ".pdf":
        if not header.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail={"error": "File signature does not match PDF format."})
        kind = "pdf"
    else:
        raise HTTPException(status_code=400, detail={"error": "Unsupported file format."})

    if kind == "image":
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail={"error": "Corrupted or invalid image file."})

    return kind


async def save_uploaded_document(file: UploadFile) -> Tuple[str, str, str, Path, bytes]:
    """
    Stream and persist uploaded document to UPLOAD_DIR in 64 KB chunks.
    Enforces MAX_UPLOAD_MB limit without holding entire file in memory.
    Releases resources and deletes partial file on any error.
    """
    original_name = sanitize_filename(file.filename or "upload")
    declared_ext = Path(original_name).suffix.lower()

    if not declared_ext or declared_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={"error": "File must have an allowed extension: .png, .jpg, .jpeg, .webp, or .pdf"}
        )

    settings.upload_path.mkdir(parents=True, exist_ok=True)
    stored_name = generate_stored_filename(declared_ext)
    file_path = settings.upload_path / stored_name
    max_bytes = int(settings.MAX_UPLOAD_MB * 1024 * 1024)

    total_bytes = 0
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=400,
                        detail={"error": f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB} MB."}
                    )
                f.write(chunk)
    except Exception:
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        raise

    if total_bytes == 0:
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        raise HTTPException(status_code=400, detail={"error": "Uploaded file is empty."})

    try:
        file_kind = validate_file_on_disk(file_path, declared_ext)
    except Exception:
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        raise

    return original_name, stored_name, file_kind, file_path, b""
