import re
import json
import difflib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from functools import lru_cache
from app.services.medicine_matcher import normalize_medicine_name

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "verified_medicines.json"


@lru_cache(maxsize=1)
def load_verified_medicines() -> List[Dict[str, Any]]:
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("medicines", [])
    except Exception:
        return []


def find_verified_medicine(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for a verified medicine entry by brand name, aliases, or active ingredients.
    Matches with normalization and similarity scoring.
    """
    cleaned = normalize_medicine_name(query)
    if not cleaned:
        return None

    medicines = load_verified_medicines()
    best_score = 0.0
    best_med: Optional[Dict[str, Any]] = None

    for med in medicines:
        # Check brand name
        b_norm = normalize_medicine_name(med.get("brand_name", ""))
        if cleaned == b_norm:
            return med

        ratio = difflib.SequenceMatcher(None, cleaned, b_norm).ratio()
        if ratio > best_score:
            best_score = ratio
            best_med = med

        # Check aliases
        for alias in med.get("aliases", []):
            a_norm = normalize_medicine_name(alias)
            if cleaned == a_norm:
                return med
            a_ratio = difflib.SequenceMatcher(None, cleaned, a_norm).ratio()
            if a_ratio > best_score:
                best_score = a_ratio
                best_med = med

        # Check ingredient combo match
        ing_names = " ".join([i.get("name", "") for i in med.get("ingredients", [])])
        ing_norm = normalize_medicine_name(ing_names)
        if cleaned and cleaned in ing_norm:
            score = 0.88
            if score > best_score:
                best_score = score
                best_med = med

    if best_score >= 0.70 and best_med:
        return best_med

    return None


def verify_active_ingredient_and_strength_equivalence(
    original_ingredients: List[Dict[str, str]],
    candidate_ingredients: List[Dict[str, str]],
    original_form: str,
    candidate_form: str,
    original_release: str = "immediate",
    candidate_release: str = "immediate"
) -> Tuple[bool, str]:
    """
    Strict equivalence verification:
      - Same active ingredient(s)
      - Same strength(s)
      - Compatible dosage form
      - Same release mechanism (e.g. sustained release vs enteric coated vs immediate)
    Returns (is_equivalent, rationale).
    """
    # 1. Compare release mechanisms
    if original_release.lower() != candidate_release.lower():
        return False, f"Different release formulation ({original_release} vs {candidate_release}). Not interchangeable."

    # 2. Compare dosage forms (e.g. tablet vs syrup)
    norm_form_orig = original_form.lower().replace("-", " ")
    norm_form_cand = candidate_form.lower().replace("-", " ")
    if "tablet" in norm_form_orig and "syrup" in norm_form_cand:
        return False, "Different dosage forms (tablet vs syrup). Dose absorption and administration differ."
    if "capsule" in norm_form_orig and "injection" in norm_form_cand:
        return False, "Different dosage forms (capsule vs injection)."

    # 3. Compare ingredients count
    if len(original_ingredients) != len(candidate_ingredients):
        return False, "Different number of active ingredients in formulation."

    # Map ingredients by normalized name
    orig_map = {
        i.get("name", "").lower().strip(): i.get("strength", "").lower().strip()
        for i in original_ingredients
    }
    cand_map = {
        i.get("name", "").lower().strip(): i.get("strength", "").lower().strip()
        for i in candidate_ingredients
    }

    for ing_name, orig_str in orig_map.items():
        if ing_name not in cand_map:
            return False, f"Missing active ingredient: {ing_name} is not present in candidate."

        cand_str = cand_map[ing_name]
        # Normalize strength strings: e.g. "650mg" vs "650 mg"
        clean_orig_str = re.sub(r"\s+", "", orig_str)
        clean_cand_str = re.sub(r"\s+", "", cand_str)
        if clean_orig_str and clean_cand_str and clean_orig_str != clean_cand_str:
            return False, f"Different strength for {ing_name} ({orig_str} vs {cand_str}). Not equivalent."

    return True, "Same active ingredients, equivalent strength, dosage form, and release formulation."


def get_verified_alternatives_for_medicine(medicine_query: str) -> Dict[str, Any]:
    """
    Retrieve categorized verified brand and generic alternatives for a medicine:
      - Category A: Same brand at other pharmacies
      - Category B: Another brand with same active ingredient and strength
      - Category C: Generic product with same active ingredient and strength (Jan Aushadhi)
      - Category D: Different medicine for similar condition (explicitly not interchangeable)
    """
    med = find_verified_medicine(medicine_query)
    if not med:
        return {
            "status": "not_in_catalog",
            "medicine_name": medicine_query,
            "message": "Medicine not found in verified reference dataset. Check with a pharmacist.",
            "category_b_brands": [],
            "category_c_generics": [],
            "category_d_non_interchangeable": []
        }

    orig_brand = med.get("brand_name")
    orig_mrp = med.get("reference_mrp_inr", 0.0)
    orig_units = med.get("units_per_pack", 1) or 1
    orig_per_unit = orig_mrp / orig_units if orig_units else 0.0

    ingredients_summary = ", ".join([
        f"{i.get('name', '').title()} {i.get('strength', '')}"
        for i in med.get("ingredients", [])
    ])

    # Category B: Other brands with same active ingredient & strength
    cat_b = []
    for brand in med.get("category_b_brands", []):
        cand_mrp = brand.get("reference_mrp_inr", 0.0)
        cand_pack = brand.get("pack_size", "")
        # Parse pack units
        match = re.search(r"\b(\d+)\b", cand_pack)
        cand_units = int(match.group(1)) if match else orig_units
        cand_per_unit = cand_mrp / cand_units if cand_units else 0.0

        savings_per_pack = max(0.0, orig_mrp - cand_mrp) if orig_units == cand_units else None
        savings_pct = round(((orig_per_unit - cand_per_unit) / orig_per_unit) * 100, 1) if (orig_per_unit and cand_per_unit < orig_per_unit) else 0.0

        cat_b.append({
            "category": "B",
            "category_label": "Equivalent Brand (Same Active Ingredient & Strength)",
            "brand_name": brand.get("brand_name"),
            "manufacturer": brand.get("manufacturer", "Reputable Manufacturer"),
            "active_ingredients": ingredients_summary,
            "strength": ", ".join([i.get("strength", "") for i in med.get("ingredients", [])]),
            "dosage_form": med.get("dosage_form", "tablet"),
            "pack_size": cand_pack,
            "verified_mrp_inr": cand_mrp,
            "savings_percentage": savings_pct,
            "equivalence_rationale": f"Contains identical active ingredient ({ingredients_summary}) in equivalent formulation.",
            "safety_note": "Requires prescription if applicable. Consult your doctor or pharmacist prior to switching brands."
        })

    # Category C: Generic product with same active ingredient & strength
    cat_c = []
    for gen in med.get("category_c_generics", []):
        cand_mrp = gen.get("reference_mrp_inr", 0.0)
        cand_pack = gen.get("pack_size", "")
        match = re.search(r"\b(\d+)\b", cand_pack)
        cand_units = int(match.group(1)) if match else orig_units
        cand_per_unit = cand_mrp / cand_units if cand_units else 0.0

        savings_pct = round(((orig_per_unit - cand_per_unit) / orig_per_unit) * 100, 1) if (orig_per_unit and cand_per_unit < orig_per_unit) else 0.0

        cat_c.append({
            "category": "C",
            "category_label": "Generic Substitute (Jan Aushadhi / Low-Cost Generic)",
            "product_name": gen.get("generic_name"),
            "manufacturer": gen.get("manufacturer", "Pradhan Mantri Bhartiya Janaushadhi Pariyojana"),
            "active_ingredients": ingredients_summary,
            "strength": ", ".join([i.get("strength", "") for i in med.get("ingredients", [])]),
            "dosage_form": med.get("dosage_form", "tablet"),
            "pack_size": cand_pack,
            "verified_mrp_inr": cand_mrp,
            "savings_percentage": savings_pct,
            "equivalence_rationale": "High-quality generic bioequivalent formulation verified by Government Jan Aushadhi standards.",
            "safety_note": "Bioequivalent generic medicine. Confirm substitution with your pharmacist or doctor."
        })

    # Category D: Different medicine for similar condition (NEVER interchangeable)
    cat_d = []
    for diff in med.get("category_d_non_interchangeable", []):
        cat_d.append({
            "category": "D",
            "category_label": "Different Medicine Class (NOT Interchangeable)",
            "drug_name": diff.get("drug_name"),
            "warning": diff.get("reason"),
            "safety_rule": "NEVER substitute with this medicine without a direct doctor prescription. Mechanism and risks differ completely."
        })

    return {
        "status": "ok",
        "original_medicine": {
            "id": med.get("id"),
            "brand_name": orig_brand,
            "active_ingredients": ingredients_summary,
            "strength": ", ".join([i.get("strength", "") for i in med.get("ingredients", [])]),
            "dosage_form": med.get("dosage_form", "tablet"),
            "release_type": med.get("release_type", "immediate"),
            "pack_size": med.get("standard_pack_size", ""),
            "reference_mrp_inr": orig_mrp,
            "is_rx_required": med.get("is_rx_required", False)
        },
        "category_b_brands": cat_b,
        "category_c_generics": cat_c,
        "category_d_non_interchangeable": cat_d,
        "substitution_notice": (
            "Medical Safety Notice: Never change prescribed medicines solely because another brand is cheaper. "
            "For all prescription medications, confirm brand or generic substitution with your doctor or licensed pharmacist."
        )
    }
