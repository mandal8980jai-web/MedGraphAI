import json
from typing import Dict, Any, List, Optional
from app.services.safety_gate import check_text
from app.services.medicine_equivalence_service import find_verified_medicine
from app.services.gemini_client import call_gemini_with_search, call_gemini_chat

REQUIRED_CONTEXT_FIELDS = [
    ("age", "Patient Age"),
    ("reason", "Condition / Reason for Prescription"),
    ("allergies", "Known Allergies"),
    ("pregnancy", "Pregnancy / Nursing Status"),
    ("kidney_liver", "Kidney or Liver Considerations"),
]

MANDATORY_SAFETY_DIRECTIVE = (
    "Clinical Safety Directive: Never independently stop, switch, or change prescribed medicines. "
    "All alternative candidates are educational discussion points for a licensed doctor or pharmacist."
)


def check_missing_patient_context(context: Optional[Dict[str, Any]]) -> List[str]:
    """Check which mandatory clinical context items are missing."""
    if not context:
        return [field for field, _ in REQUIRED_CONTEXT_FIELDS]

    missing = []
    for field_key, _ in REQUIRED_CONTEXT_FIELDS:
        val = context.get(field_key)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field_key)
    return missing


def research_alternatives_for_medicines(
    medicines: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Alternative Research Helper:
    Researches potential alternative candidates solely for clinician discussion.
    If clinical context is incomplete, sets status 'needs_more_info' and returns items=[].
    When clinical context is provided, combines verified pharmaceutical equivalence
    with AI pharmacology research. Never returns blank bullet lists or unsupported empty options.
    """
    missing = check_missing_patient_context(context)
    if missing:
        return {
            "status": "needs_more_info",
            "missing": missing,
            "items": [],
            "flags": []
        }

    items = []
    all_flags = []

    context_str = (
        f"Patient Age: {context.get('age')}, "
        f"Diagnosis/Reason: {context.get('reason')}, "
        f"Allergies: {context.get('allergies')}, "
        f"Pregnancy Status: {context.get('pregnancy')}, "
        f"Kidney/Liver History: {context.get('kidney_liver')}."
    )

    for med in medicines:
        med_id = med.get("id", "")
        med_name = med.get("name_text", "")
        raw_options: List[str] = []
        sources: List[Dict[str, Any]] = []

        # 1. Verified pharmaceutical equivalence benchmarks
        verified = find_verified_medicine(med_name)
        if verified:
            cat_b_brands = verified.get("category_b_brands", [])
            cat_c_generics = verified.get("category_c_generics", [])
            cat_d_warnings = verified.get("category_d_non_interchangeable", [])

            for b in cat_b_brands:
                b_name = b.get("brand_name")
                mfg = b.get("manufacturer", "")
                mrp = b.get("reference_mrp_inr")
                mrp_str = f" (~₹{mrp})" if mrp else ""
                mfg_str = f" [{mfg}]" if mfg else ""
                raw_options.append(
                    f"Therapeutically Equivalent Brand: {b_name}{mfg_str}{mrp_str}. "
                    f"Identical active salt and strength to discuss with your doctor."
                )

            for g in cat_c_generics:
                g_name = g.get("generic_name")
                g_mrp = g.get("reference_mrp_inr")
                g_mrp_str = f" (~₹{g_mrp})" if g_mrp else ""
                raw_options.append(
                    f"Government Generic Alternative: {g_name}{g_mrp_str}. "
                    f"Affordable bioequivalent option to verify with your pharmacist."
                )

            for w in cat_d_warnings:
                drug_w = w.get("drug_name", "")
                reason_w = w.get("reason", "")
                raw_options.append(
                    f"Non-Interchangeable Alert: {drug_w} is NOT a direct substitute ({reason_w})."
                )

            sources.append({
                "title": "National DPCO & Jan Aushadhi Equivalence Reference",
                "url": "https://janaushadhi.gov.in/",
                "source_type": "verified_catalog_benchmark"
            })

        # 2. AI pharmacology search call
        prompt = (
            f"You are a clinical decision-support pharmacology researcher.\n"
            f"Prescribed Medication: {med_name}\n"
            f"Patient Context: {context_str}\n\n"
            f"TASK:\n"
            f"Search for potential therapeutic classes or medication alternatives that a doctor or "
            f"pharmacist might consider if {med_name} causes adverse reactions or contraindications.\n\n"
            f"STRICT SAFETY DIRECTIVES:\n"
            f"- These are 'options to discuss with your doctor', NEVER instructions or advice to switch.\n"
            f"- Do NOT instruct the patient to stop, start, or change medications.\n"
            f"- Do NOT use words like 'risk-free', 'guaranteed safe', or 'completely safe'.\n\n"
            f"RESPONSE FORMAT:\n"
            f"Respond in valid JSON format:\n"
            f"{{\n"
            f'  "options": [\n'
            f'    "Candidate option A with clinical rationale to discuss with clinician",\n'
            f'    "Candidate option B with clinical rationale to discuss with clinician"\n'
            f"  ]\n"
            f"}}"
        )

        res = call_gemini_with_search(prompt)
        status = res.get("status", "unavailable")
        search_sources = res.get("sources", [])
        if search_sources:
            sources.extend(search_sources)

        if status != "unavailable" and res.get("parsed_json"):
            json_data = res["parsed_json"]
            if isinstance(json_data, dict) and "options" in json_data and isinstance(json_data["options"], list):
                for opt in json_data["options"]:
                    if str(opt) not in raw_options:
                        raw_options.append(str(opt))

        # 3. If no verified alternatives found and LLM had none (unknown/unindexed drug)
        if not raw_options:
            raw_options.append(
                f"No verified direct therapeutic alternatives or bioequivalent substitutes identified in evidence database for '{med_name}'."
            )
            raw_options.append(
                "Please consult your prescribing clinician or hospital pharmacist before considering any medication change."
            )

        # Always append mandatory safety directive
        raw_options.append(MANDATORY_SAFETY_DIRECTIVE)

        # Sanitize all options through safety gate
        sanitized_options = []
        for opt in raw_options:
            cleaned, f = check_text(opt)
            sanitized_options.append(cleaned)
            all_flags.extend(f)

        item_status = "ok" if (verified or sources) else "no_results"

        items.append({
            "for_medicine_id": med_id,
            "medicine_name": med_name,
            "options": sanitized_options,
            "sources": sources,
            "status": item_status
        })

    return {
        "status": "ok",
        "missing": [],
        "items": items,
        "flags": all_flags
    }
