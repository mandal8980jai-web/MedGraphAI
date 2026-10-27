from pathlib import Path
from typing import List, Dict, Tuple, Any
import fitz  # PyMuPDF


def extract_pdf_text(file_path: Path) -> Tuple[bool, int, List[Dict[str, Any]]]:
    """
    Extract digital text page-by-page from a PDF using PyMuPDF.
    Caps processing at 10 pages.
    Detects if the PDF is scanned based on average characters per page (< 20 chars).
    Ensures PDF handle and pages are promptly freed from memory.
    """
    doc = fitz.open(file_path)
    try:
        total_pages = len(doc)
        page_limit = min(total_pages, 10)

        pages: List[Dict[str, Any]] = []
        total_chars = 0

        for i in range(page_limit):
            page = doc.load_page(i)
            text = page.get_text() or ""
            text_clean = text.strip()
            pages.append({
                "page": i + 1,
                "text": text_clean
            })
            total_chars += len(text_clean)
            page = None

        avg_chars = total_chars / max(1, page_limit)
        is_scanned = avg_chars < 20

        return is_scanned, page_limit, pages
    finally:
        doc.close()
