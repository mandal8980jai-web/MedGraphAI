import json
import itertools
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from app.services.medicine_matcher import match_medicine_name

SAMPLE_DATA_NOTICE = (
    "Only the medicines and rules in our sample list were checked. "
    "A missing warning does not mean there is no interaction."
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_medicine_catalog() -> List[Dict[str, Any]]:
    """Load sample medicines from medicine_catalog.example.json."""
    catalog_path = DATA_DIR / "medicine_catalog.example.json"
    if not catalog_path.exists():
        return []
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("medicines", [])
    except Exception:
        return []


def load_interaction_rules() -> List[Dict[str, Any]]:
    """Load sample interaction rules from interaction_rules.example.json."""
    rules_path = DATA_DIR / "interaction_rules.example.json"
    if not rules_path.exists():
        return []
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("rules", [])
    except Exception:
        return []


def _extract_medicine_field(med: Any, field_name: str, default: Any = None) -> Any:
    """Helper to extract field whether med is a pydantic model or dict."""
    if isinstance(med, dict):
        return med.get(field_name, default)
    return getattr(med, field_name, default)


def resolve_medicine_details(med: Any, catalog_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Resolve ingredients and catalog match status for a medicine.
    Returns:
      {
        "id": str,
        "name_text": str,
        "found_in_list": bool,
        "catalog_id": str | None,
        "ingredients": list[str]
      }
    """
    med_id = str(_extract_medicine_field(med, "id", ""))
    name_text = str(_extract_medicine_field(med, "name_text", "")).strip()
    matched_id = _extract_medicine_field(med, "matched_id")
    ingredients = _extract_medicine_field(med, "ingredients") or []

    # 1. Try matching by matched_id if valid
    if matched_id and matched_id in catalog_map:
        cat_entry = catalog_map[matched_id]
        cat_ingredients = [i.lower() for i in cat_entry.get("ingredients", [])]
        return {
            "id": med_id,
            "name_text": name_text,
            "found_in_list": True,
            "catalog_id": matched_id,
            "ingredients": cat_ingredients or [i.lower() for i in ingredients]
        }

    # 2. Try matching by name_text via matcher
    match_info = match_medicine_name(name_text)
    if match_info["match_status"] == "matched" and match_info.get("matched_id"):
        cand_id = match_info["matched_id"]
        if cand_id in catalog_map:
            cat_entry = catalog_map[cand_id]
            cat_ingredients = [i.lower() for i in cat_entry.get("ingredients", [])]
            return {
                "id": med_id,
                "name_text": name_text,
                "found_in_list": True,
                "catalog_id": cand_id,
                "ingredients": cat_ingredients or [i.lower() for i in match_info.get("ingredients", [])]
            }

    # 3. Not found in catalog: never assume safe, ingredients unknown in sample list
    return {
        "id": med_id,
        "name_text": name_text,
        "found_in_list": False,
        "catalog_id": None,
        "ingredients": []
    }


def check_interactions(medicines: List[Any]) -> Dict[str, Any]:
    """
    Deterministic interaction engine for confirmed medicines.
    Uses only configured sample data.
    Detects:
      - configured interaction pairs with severity
      - duplicate active ingredients
      - unknown medicines (labeled 'Not checked: not in our list')
      - coverage counts
    """
    catalog = load_medicine_catalog()
    catalog_map = {m["id"]: m for m in catalog if "id" in m}
    rules = load_interaction_rules()

    resolved_medicines = [resolve_medicine_details(m, catalog_map) for m in medicines]

    found_ids = []
    not_found_ids = []
    not_checked_details = []

    for r_med in resolved_medicines:
        if r_med["found_in_list"]:
            found_ids.append(r_med["id"])
        else:
            not_found_ids.append(r_med["id"])
            not_checked_details.append({
                "id": r_med["id"],
                "name_text": r_med["name_text"],
                "status": "Not checked: not in our list (Not in demo catalog)",
                "reason": "Not in demo sample catalog. Never assumed safe. Absence from sample list does not mean the medicine is unknown or unsafe; live evidence research is available below."
            })

    # 1. Detect duplicate active ingredients
    ingredient_to_meds: Dict[str, List[Dict[str, str]]] = {}
    for r_med in resolved_medicines:
        if not r_med["found_in_list"]:
            continue
        for ing in r_med["ingredients"]:
            ingredient_to_meds.setdefault(ing, []).append({
                "id": r_med["id"],
                "name_text": r_med["name_text"]
            })

    duplicates = []
    for ing, meds in ingredient_to_meds.items():
        if len(meds) >= 2:
            duplicates.append({
                "ingredient": ing,
                "medicines": [m["id"] for m in meds],
                "medicine_names": [m["name_text"] for m in meds],
                "note": f"Same active ingredient ({ing}) detected in {len(meds)} medicines. Risk of accidental overdose."
            })

    # 2. Detect configured interaction pairs
    interactions = []
    for med_a, med_b in itertools.combinations(resolved_medicines, 2):
        if not med_a["found_in_list"] or not med_b["found_in_list"]:
            continue

        ings_a = set(med_a["ingredients"])
        ings_b = set(med_b["ingredients"])

        for rule in rules:
            rule_ings = set(i.lower() for i in rule.get("ingredients", []))
            # Rule applies if both ingredients are covered across the two medicines
            if rule_ings.issubset(ings_a | ings_b) and (rule_ings & ings_a) and (rule_ings & ings_b):
                interactions.append({
                    "rule_id": rule.get("id"),
                    "medicines": [med_a["id"], med_b["id"]],
                    "medicine_names": [med_a["name_text"], med_b["name_text"]],
                    "ingredients": list(rule_ings),
                    "severity": rule.get("severity", "moderate"),
                    "note": rule.get("note", ""),
                    "source_label": rule.get("source_label", "Sample demo rule, verify with a pharmacist")
                })

    coverage = {
        "total": len(medicines),
        "found_in_list": len(found_ids),
        "not_found": not_found_ids,
        "not_checked": not_checked_details
    }

    return {
        "interactions": interactions,
        "duplicates": duplicates,
        "coverage": coverage,
        "notice": SAMPLE_DATA_NOTICE
    }
