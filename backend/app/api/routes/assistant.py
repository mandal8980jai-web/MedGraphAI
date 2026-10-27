from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from app.services.medicine_information_service import process_medicine_chat
from app.services.price_comparison_service import build_medicine_price_comparison
from app.services.medicine_equivalence_service import (
    load_verified_medicines,
    find_verified_medicine,
    get_verified_alternatives_for_medicine
)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
medicines_router = APIRouter(prefix="/api/medicines", tags=["medicines"])


class AssistantChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    prescription_medicines: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = None


class AssistantChatResponse(BaseModel):
    reply: str
    language: str
    medicine_detected: Optional[str] = None
    price_comparison: Optional[Dict[str, Any]] = None
    alternatives: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, str]] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)


@router.post("/chat", response_model=AssistantChatResponse)
def assistant_chat_endpoint(payload: AssistantChatRequest) -> AssistantChatResponse:
    """
    Multilingual Medicine Information, Price Comparison, and Affordable Alternatives Assistant.
    Supports English, Devanagari Hindi, and Roman Hinglish with context memory and safety gates.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail={"error": "Message cannot be empty."})

    res = process_medicine_chat(
        message=payload.message,
        history=payload.history,
        prescription_medicines=payload.prescription_medicines,
        preferred_language=payload.language
    )

    return AssistantChatResponse(
        reply=res.get("reply", ""),
        language=res.get("language", "en"),
        medicine_detected=res.get("medicine_detected"),
        price_comparison=res.get("price_comparison"),
        alternatives=res.get("alternatives"),
        sources=res.get("sources", []),
        flags=res.get("flags", [])
    )


@medicines_router.get("/search")
def search_medicines(query: str = Query(..., min_length=1)) -> Dict[str, Any]:
    """
    Search catalog and verified medicines database.
    """
    all_meds = load_verified_medicines()
    q_lower = query.lower().strip()

    matches = []
    for med in all_meds:
        brand = med.get("brand_name", "")
        aliases = med.get("aliases", [])
        ingredients = [i.get("name", "") for i in med.get("ingredients", [])]

        if q_lower in brand.lower() or any(q_lower in a.lower() for a in aliases) or any(q_lower in i.lower() for i in ingredients):
            matches.append({
                "id": med.get("id"),
                "brand_name": brand,
                "ingredients": med.get("ingredients"),
                "dosage_form": med.get("dosage_form"),
                "standard_pack_size": med.get("standard_pack_size"),
                "reference_mrp_inr": med.get("reference_mrp_inr"),
                "is_rx_required": med.get("is_rx_required")
            })

    return {
        "query": query,
        "count": len(matches),
        "results": matches
    }


@medicines_router.get("/compare-prices")
def compare_prices_endpoint(
    query: str = Query(..., min_length=1),
    strength: Optional[str] = None,
    dosage_form: Optional[str] = None,
    pack_size: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare pharmacy listings and generate direct links for Tata 1mg, PharmEasy, Apollo, and Netmeds.
    """
    return build_medicine_price_comparison(
        medicine_query=query,
        strength=strength,
        dosage_form=dosage_form,
        pack_size=pack_size
    )


@medicines_router.get("/alternatives")
def alternatives_endpoint(query: str = Query(..., min_length=1)) -> Dict[str, Any]:
    """
    Retrieve categorized verified brand and generic alternatives with strict medical safety checks.
    """
    return get_verified_alternatives_for_medicine(query)
