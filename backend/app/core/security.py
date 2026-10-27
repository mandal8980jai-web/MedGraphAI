import os
import uuid
from pathlib import Path
from fastapi import HTTPException
from app.core.config import settings


def sanitize_filename(original_name: str) -> str:
    """Strip dangerous characters and paths from an uploaded filename."""
    base = os.path.basename(original_name.strip())
    # Replace dangerous characters with underscores
    safe_chars = [c if (c.isalnum() or c in ".-_") else "_" for c in base]
    clean = "".join(safe_chars).lstrip(".")
    return clean or "document"


def generate_stored_filename(extension: str) -> str:
    """Generate a random UUID filename with a validated extension."""
    ext = extension.lower().lstrip(".")
    return f"{uuid.uuid4().hex}.{ext}"


def get_safe_file_path(stored_name: str) -> Path:
    """Ensure the resolved file path resides strictly inside UPLOAD_DIR (prevent directory traversal)."""
    upload_dir = settings.upload_path.resolve()
    target_path = (upload_dir / stored_name).resolve()
    if not str(target_path).startswith(str(upload_dir)):
        raise HTTPException(status_code=400, detail={"error": "Invalid file path."})
    return target_path
