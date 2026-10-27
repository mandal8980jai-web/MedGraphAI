import gc
import io
import threading
from pathlib import Path
from typing import List, Dict, Union, Any, Optional
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
from app.core.config import settings
from app.core.logging import logger
from app.core.memory import log_memory

# Global lock to strictly enforce single concurrent OCR task at a time (Render 512 MB constraint)
_ocr_lock = threading.Lock()
_engine_lock = threading.Lock()
_engine: Optional[RapidOCR] = None


def get_ocr_engine() -> RapidOCR:
    """Lazy thread-safe singleton initialization of RapidOCR engine."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                log_memory("Pre-RapidOCR Engine Init")
                _engine = RapidOCR()
                log_memory("Post-RapidOCR Engine Init")
    return _engine


def preprocess_image_for_ocr(image_input: Union[Path, bytes]) -> np.ndarray:
    """
    Open image, downscale oversized images to max dimension while preserving text readability,
    and convert to RGB numpy array. Releases Pillow image memory immediately.
    """
    if isinstance(image_input, Path):
        img = Image.open(str(image_input))
    else:
        img = Image.open(io.BytesIO(image_input))

    try:
        width, height = img.size
        max_dim = settings.OCR_MAX_IMAGE_DIMENSION

        if max(width, height) > max_dim:
            ratio = max_dim / float(max(width, height))
            new_size = (max(1, int(width * ratio)), max(1, int(height * ratio)))
            logger.info(f"Downscaling oversized image ({width}x{height} -> {new_size[0]}x{new_size[1]}) for low-memory OCR.")
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
        else:
            resized_img = img

        if resized_img.mode != "RGB":
            rgb_img = resized_img.convert("RGB")
            arr = np.array(rgb_img)
            if rgb_img is not resized_img:
                rgb_img.close()
        else:
            arr = np.array(resized_img)

        if resized_img is not img:
            resized_img.close()

        return arr
    finally:
        img.close()


def ocr_image(image_input: Union[Path, bytes]) -> List[Dict[str, Any]]:
    """Perform OCR on a single image file or byte buffer with concurrency limiting and resizing."""
    with _ocr_lock:
        log_memory("Start OCR Image")
        try:
            arr = preprocess_image_for_ocr(image_input)
            engine = get_ocr_engine()
            result, _ = engine(arr)
            del arr

            text_lines = []
            if result:
                for item in result:
                    if len(item) > 1 and item[1]:
                        text_lines.append(str(item[1]).strip())

            return [{
                "page": 1,
                "text": "\n".join(text_lines)
            }]
        finally:
            gc.collect()
            log_memory("End OCR Image")


def ocr_scanned_pdf(file_path: Path) -> List[Dict[str, Any]]:
    """
    Render scanned PDF pages individually using PyMuPDF, then process each page with RapidOCR.
    Caps at 10 pages. Preserves page numbers.
    Releases raster objects and pixmaps immediately after each page to stay under 512 MB.
    """
    with _ocr_lock:
        log_memory("Start OCR Scanned PDF", f"file={file_path.name}")
        engine = get_ocr_engine()
        doc = fitz.open(file_path)
        try:
            page_limit = min(len(doc), 10)
            pages: List[Dict[str, Any]] = []
            max_dim = settings.OCR_MAX_IMAGE_DIMENSION
            dpi = settings.OCR_PDF_DPI

            for i in range(page_limit):
                page = doc.load_page(i)
                rect = page.rect
                scale = dpi / 72.0
                if max(rect.width * scale, rect.height * scale) > max_dim:
                    scale = max_dim / max(rect.width, rect.height)

                matrix = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=matrix)

                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 4:
                    arr = arr[:, :, :3]
                elif pix.n == 1:
                    arr = np.stack([arr.squeeze(-1)] * 3, axis=-1)

                result, _ = engine(arr)
                del arr
                pix = None
                page = None

                text_lines = []
                if result:
                    for item in result:
                        if len(item) > 1 and item[1]:
                            text_lines.append(str(item[1]).strip())

                pages.append({
                    "page": i + 1,
                    "text": "\n".join(text_lines)
                })

                # Prompt garbage collection after every heavy page
                gc.collect()

            return pages
        finally:
            doc.close()
            gc.collect()
            log_memory("End OCR Scanned PDF")
