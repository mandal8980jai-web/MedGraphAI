import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.logging import logger
from app.services.document_service import save_uploaded_document
from app.services.pdf_text_service import extract_pdf_text
from app.services.ocr_service import ocr_image, ocr_scanned_pdf
from app.services.gemini_client import extract_medicines_from_text
from app.services.medicine_matcher import match_medicine_name
from app.db.repositories import save_analysis, get_analysis_by_id
from app.schemas.analysis import AnalysisResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=AnalysisResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a prescription image or PDF.
    Validates file signatures, runs PyMuPDF / RapidOCR, extracts medicines, and matches against catalog.
    """
    original_name, stored_name, file_kind, file_path, content = await save_uploaded_document(file)

    try:
        pages = []
        if file_kind == "pdf":
            is_scanned, page_count, pdf_pages = extract_pdf_text(file_path)
            if is_scanned:
                logger.info(f"PDF {stored_name} detected as scanned. Triggering RapidOCR fallback.")
                pages = ocr_scanned_pdf(file_path)
                text_source = "ocr"
            else:
                logger.info(f"PDF {stored_name} processed via PyMuPDF digital text.")
                pages = pdf_pages
                text_source = "pdf_text"
        else:
            logger.info(f"Image {stored_name} processed via RapidOCR.")
            pages = ocr_image(file_path)
            text_source = "ocr"
            page_count = 1

        full_extracted_text = "\n\n".join([f"--- Page {p.get('page', 1)} ---\n{p.get('text', '')}" for p in pages])

        # Extract candidate medicines
        candidate_medicines = extract_medicines_from_text(pages)

        # Match each medicine against transparent catalog
        matched_medicines = []
        for med in candidate_medicines:
            match_info = match_medicine_name(med["name_text"])
            matched_medicines.append({
                **med,
                "match_status": match_info["match_status"],
                "matched_id": match_info["matched_id"],
                "candidates": match_info["candidates"],
                "ingredients": match_info["ingredients"],
                "confirmed": False
            })

        analysis_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        save_analysis(
            analysis_id=analysis_id,
            created_at=created_at,
            original_name=original_name,
            stored_name=stored_name,
            file_kind=file_kind,
            text_source=text_source,
            page_count=page_count,
            extracted_text=full_extracted_text,
            medicines=matched_medicines,
            status="uploaded"
        )

        analysis = get_analysis_by_id(analysis_id)
        if not analysis:
            raise HTTPException(status_code=500, detail={"error": "Failed to persist document analysis."})

        return analysis

    except Exception as e:
        logger.error(f"Error processing uploaded document: {e}")
        # Clean up file on catastrophic failure
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail={"error": f"Failed to process document: {str(e)}"})
