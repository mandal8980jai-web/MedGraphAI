from pathlib import Path
from typing import List, Dict, Union
import fitz  # PyMuPDF
from rapidocr_onnxruntime import RapidOCR

# Lazy singleton OCR instance to optimize memory and startup
_engine = None


def get_ocr_engine() -> RapidOCR:
    global _engine
    if _engine is None:
        _engine = RapidOCR()
    return _engine


def ocr_image(image_input: Union[Path, bytes]) -> List[Dict[str, any]]:
    """Perform OCR on a single image file or byte buffer."""
    engine = get_ocr_engine()
    if isinstance(image_input, Path):
        result, _ = engine(str(image_input))
    else:
        result, _ = engine(image_input)

    text_lines = []
    if result:
        for item in result:
            if len(item) > 1 and item[1]:
                text_lines.append(str(item[1]).strip())

    return [{
        "page": 1,
        "text": "\n".join(text_lines)
    }]


def ocr_scanned_pdf(file_path: Path) -> List[Dict[str, any]]:
    """
    Render scanned PDF pages to PNG at ~200 DPI using PyMuPDF,
    then process each page with RapidOCR.
    Caps at 10 pages. Preserves page numbers.
    """
    engine = get_ocr_engine()
    doc = fitz.open(file_path)
    page_limit = min(len(doc), 10)
    pages: List[Dict[str, any]] = []

    for i in range(page_limit):
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")

        result, _ = engine(img_bytes)
        text_lines = []
        if result:
            for item in result:
                if len(item) > 1 and item[1]:
                    text_lines.append(str(item[1]).strip())

        pages.append({
            "page": i + 1,
            "text": "\n".join(text_lines)
        })

    doc.close()
    return pages
