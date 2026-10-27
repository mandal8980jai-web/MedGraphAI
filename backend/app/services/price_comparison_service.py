from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.services.medicine_equivalence_service import (
    find_verified_medicine,
    get_verified_alternatives_for_medicine
)
from app.services.pharmacy_search_service import get_pharmacy_listings


def build_medicine_price_comparison(
    medicine_query: str,
    strength: Optional[str] = None,
    dosage_form: Optional[str] = None,
    pack_size: Optional[str] = None,
    max_providers: int = 3
) -> Dict[str, Any]:
    """
    Constructs a complete price comparison and affordable alternatives response:
      - Up to 3 online pharmacies (Tata 1mg, PharmEasy, Apollo / Netmeds)
      - Direct medicine search links for each pharmacy
      - Honest pricing disclosure (Link-only mode: prices not fabricated)
      - Verified reference pricing benchmark where available in official catalog
      - Cheaper brand (Category B) and Jan Aushadhi generic (Category C) alternatives
      - Clinical safety substitution disclaimer
    """
    clean_query = medicine_query.strip()
    verified_med = find_verified_medicine(clean_query)

    if verified_med:
        med_name = verified_med.get("brand_name", clean_query)
        ing_str = ", ".join([f"{i.get('name', '').title()} {i.get('strength', '')}" for i in verified_med.get("ingredients", [])])
        strength_val = strength or ", ".join([i.get("strength", "") for i in verified_med.get("ingredients", [])])
        form_val = dosage_form or verified_med.get("dosage_form", "tablet")
        pack_val = pack_size or verified_med.get("standard_pack_size", "10-15 units")
        is_rx = verified_med.get("is_rx_required", False)
        reference_mrp = verified_med.get("reference_mrp_inr")
    else:
        med_name = clean_query
        ing_str = "Check packaging"
        strength_val = strength or "Standard dose"
        form_val = dosage_form or "Tablet"
        pack_val = pack_size or "Standard strip"
        is_rx = False
        reference_mrp = None

    # 1. Fetch pharmacy listings
    pharmacy_results = get_pharmacy_listings(
        medicine_name=med_name,
        active_ingredient=ing_str,
        strength=strength_val,
        dosage_form=form_val,
        pack_size=pack_val,
        is_rx_required=is_rx,
        max_providers=max_providers
    )

    # 2. Fetch verified alternatives
    alternatives_data = get_verified_alternatives_for_medicine(med_name)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "medicine_name": med_name,
        "active_ingredient": ing_str,
        "strength": strength_val,
        "dosage_form": form_val,
        "pack_size": pack_val,
        "is_rx_required": is_rx,
        "reference_benchmark_mrp": reference_mrp,
        "benchmark_note": "Benchmark MRP from verified essential medicines catalog. Final prices are determined by pharmacies." if reference_mrp else None,
        "retrieval_timestamp": now_iso,
        "providers_compared": pharmacy_results,
        "alternatives": alternatives_data,
        "price_honesty_note": (
            "Online pharmacy prices vary dynamically by pincode, prescription verification, coupons, and seller stock. "
            "To prevent inaccurate claims, direct pharmacy search links are provided above. Click 'View at Pharmacy' to check final live pricing."
        ),
        "safety_disclaimer": (
            "Notice: Lowest price does not automatically imply clinical suitability. Never replace or stop prescribed medicines "
            "without consulting your doctor or pharmacist. MediGraph AI provides educational decision-support and does not sell or deliver medicines."
        )
    }
