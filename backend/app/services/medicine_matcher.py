import re
import json
import difflib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

PHARMA_STOPWORDS = {
    "tab", "tabs", "tablet", "tablets", "cap", "caps", "capsule", "capsules",
    "syr", "syrup", "inj", "injection", "drops", "ointment", "gel", "suspension",
    "solution", "rotacap", "inhaler", "cream", "lotion", "sachet", "rx",
    "sr", "er", "cr", "xr", "pr", "dr", "ds", "dt", "od", "bd", "tds", "tid",
    "bid", "qid", "qd", "sos", "hs", "ip", "bp", "usp", "advance", "plus", "forte"
}


def normalize_medicine_name(name: str) -> str:
    """
    Lower-case, strip strength numbers, dosage units, formulation affixes, and punctuation.
    Preserves core pharmacological identifier (e.g. 'Tablet Dolo 650' -> 'dolo').
    """
    if not name:
        return ""
    text = name.lower()
    # Strip common units and numbers (e.g., 650mg, 500 mg, 10ml, 5%)
    text = re.sub(r'\b\d+(\.\d+)?\s*(mg|mcg|g|ml|iu|%)\b', ' ', text)
    # Strip standalone numbers
    text = re.sub(r'\b\d+\b', ' ', text)
    # Strip non-alphanumeric characters
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = [w for w in text.split() if w not in PHARMA_STOPWORDS]
    return " ".join(tokens) if tokens else " ".join(text.split())


def load_medicine_catalog() -> List[Dict[str, Any]]:
    """
    Load curated sample medicines from medicine_catalog.example.json,
    merging verified brands and aliases from verified_medicines.json.
    """
    data_dir = Path(__file__).resolve().parent.parent / "data"
    catalog_path = data_dir / "medicine_catalog.example.json"
    verified_path = data_dir / "verified_medicines.json"

    medicines: List[Dict[str, Any]] = []
    seen_ids = set()

    if catalog_path.exists():
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("medicines", []):
                    med_id = item.get("id")
                    if med_id and med_id not in seen_ids:
                        seen_ids.add(med_id)
                        medicines.append(item)
        except Exception:
            pass

    # Merge entries from verified_medicines.json if present
    if verified_path.exists():
        try:
            with open(verified_path, "r", encoding="utf-8") as f:
                v_data = json.load(f)
                for v_item in v_data.get("medicines", []):
                    v_id = v_item.get("id")
                    brand = v_item.get("brand_name")
                    aliases = v_item.get("aliases", [])
                    raw_ings = v_item.get("ingredients", [])
                    ing_names = [i.get("name") if isinstance(i, dict) else str(i) for i in raw_ings]

                    names = [brand] + aliases
                    for cat_b in v_item.get("category_b_brands", []):
                        if isinstance(cat_b, dict) and cat_b.get("brand_name"):
                            names.append(cat_b["brand_name"])

                    # If id matches an existing entry, merge names
                    existing = next((m for m in medicines if m.get("id") == v_id), None)
                    if existing:
                        for n in names:
                            if n and n not in existing.get("names", []):
                                existing.setdefault("names", []).append(n)
                    elif v_id not in seen_ids:
                        seen_ids.add(v_id)
                        medicines.append({
                            "id": v_id,
                            "names": [n for n in names if n],
                            "ingredients": [i.lower() for i in ing_names if i]
                        })
        except Exception:
            pass

    return medicines


def match_medicine_name(name_text: str) -> Dict[str, Any]:
    """
    Match a detected medicine name against the catalog using normalization,
    exact token containment, and difflib SequenceMatcher.

    Returns:
      {
        "match_status": "matched" | "several_possible" | "not_found",
        "matched_id": str | None,
        "candidates": list[str],
        "ingredients": list[str],
        "catalog_status": "matched" | "several_possible" | "not_in_catalog",
        "note": str
      }
    """
    cleaned_query = normalize_medicine_name(name_text)
    if not cleaned_query:
        return {
            "match_status": "not_found",
            "matched_id": None,
            "candidates": [],
            "ingredients": [],
            "catalog_status": "not_in_catalog",
            "note": "Empty medicine name provided."
        }

    catalog = load_medicine_catalog()
    scores: List[Tuple[float, Dict[str, Any], str]] = []

    for entry in catalog:
        entry_id = entry.get("id")
        names = entry.get("names", [])
        ingredients = entry.get("ingredients", [])

        best_entry_score = 0.0
        best_entry_matched_name = ""

        for candidate_name in names:
            cleaned_candidate = normalize_medicine_name(candidate_name)
            if not cleaned_candidate:
                continue

            # 1. Exact equality check after normalization
            if cleaned_query == cleaned_candidate:
                ratio = 1.0
            # 2. Token subset containment (e.g. query "dolo" in candidate "dolo 650", or vice-versa)
            elif cleaned_query in cleaned_candidate.split() or cleaned_candidate in cleaned_query.split():
                ratio = 0.95
            else:
                ratio = difflib.SequenceMatcher(None, cleaned_query, cleaned_candidate).ratio()

            if ratio > best_entry_score:
                best_entry_score = ratio
                best_entry_matched_name = candidate_name

        if best_entry_score >= 0.68:
            scores.append((best_entry_score, entry, best_entry_matched_name))

    # Sort descending by score
    scores.sort(key=lambda x: x[0], reverse=True)

    if not scores:
        return {
            "match_status": "not_found",
            "matched_id": None,
            "candidates": [],
            "ingredients": [],
            "catalog_status": "not_in_catalog",
            "note": "Not found in local sample catalog. Absence from sample list does not mean the medicine is unknown or unsafe; live evidence research can be performed."
        }

    top_score, top_entry, top_name = scores[0]

    if top_score > 0.85:
        return {
            "match_status": "matched",
            "matched_id": top_entry.get("id"),
            "candidates": [top_name],
            "ingredients": top_entry.get("ingredients", []),
            "catalog_status": "matched",
            "note": f"Matched in local catalog with '{top_name}'."
        }
    else:
        # Ambiguous match (0.68 <= score <= 0.85): NEVER auto-pick!
        # Return up to 3 candidate catalog names
        unique_candidates: List[str] = []
        for s, ent, cand_name in scores[:3]:
            if cand_name not in unique_candidates:
                unique_candidates.append(cand_name)

        return {
            "match_status": "several_possible",
            "matched_id": None,
            "candidates": unique_candidates,
            "ingredients": [],
            "catalog_status": "several_possible",
            "note": "Multiple possible catalog matches found. Clinical review recommended."
        }
