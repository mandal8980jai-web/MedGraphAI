import json
from typing import Dict, Any, List, Optional
from app.services.gemini_client import call_gemini_json
from app.services.safety_gate import check_text


def review_safety_and_evidence(
    results: Dict[str, Any],
    medicines: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Safety Reviewer (Safety Critic Agent):
    Deterministic verification first:
      - Flags findings lacking citation sources.
      - Flags unverified/unknown medicines outside demo catalog.
      - Flags duplicate active ingredients.
      - Flags any blocked prescriptive advice or safety claims.
    Followed by an optional Gemini consistency check.
    """
    issues: List[Dict[str, str]] = []

    # 1. Check for evidence findings lacking verified grounding sources
    evidence_list = results.get("evidence", [])
    for ev in evidence_list:
        med_id = ev.get("medicine_id", "unknown")
        med_name = ev.get("medicine_name", med_id)
        status = ev.get("status")
        sources = ev.get("sources", [])
        if status == "no_source" or not sources:
            issues.append({
                "where": f"Evidence for {med_name}",
                "issue": "No verified external sources were retrieved for these findings."
            })
        elif status == "unavailable":
            issues.append({
                "where": f"Evidence for {med_name}",
                "issue": "External evidence research was unavailable."
            })

    # 2. Check for unknown medicines not covered by the demo catalog
    coverage = results.get("coverage", {})
    not_found = coverage.get("not_found", [])
    if not_found:
        med_names = [m.get("name_text", m.get("id")) for m in medicines if m.get("id") in not_found]
        issues.append({
            "where": "Demo Catalog Coverage",
            "issue": f"{len(not_found)} medicine(s) ({', '.join(med_names)}) not found in sample demo list. Never assumed safe."
        })

    # 3. Check duplicate active ingredients
    duplicates = results.get("duplicates", [])
    for dup in duplicates:
        ing = dup.get("ingredient", "unknown")
        meds = dup.get("medicine_names", dup.get("medicines", []))
        issues.append({
            "where": f"Active Ingredient Overlap ({ing})",
            "issue": f"Duplicate active ingredient found in {', '.join(meds)}. Risk of unintended overdose."
        })

    # 4. Check safety flags from previous phases
    flags = results.get("flags", [])
    for flag in flags:
        issues.append({
            "where": "Safety Gate",
            "issue": flag
        })

    # 5. Optional Gemini consistency check
    prompt = (
        "You are a Safety Reviewer Agent reviewing medication safety analysis findings.\n"
        "Check for clinical contradictions, unsupported claims, or safety omissions.\n\n"
        f"ANALYSIS SUMMARY:\n"
        f"- Prescribed Medicines: {[m.get('name_text') for m in medicines]}\n"
        f"- Configured Interactions: {results.get('interactions', [])}\n"
        f"- Evidence Findings: {[{'med': e.get('medicine_name'), 'findings': e.get('findings')} for e in evidence_list]}\n\n"
        "TASK:\n"
        "List any apparent clinical contradictions or ungrounded claims.\n"
        "Format as valid JSON:\n"
        "{\n"
        '  "critique_issues": [\n'
        '    {"where": "section or medicine", "issue": "brief plain description"}\n'
        "  ]\n"
        "}"
    )

    llm_result = call_gemini_json(prompt, timeout_sec=30, retries=1)
    if isinstance(llm_result, dict) and "critique_issues" in llm_result:
        for item in llm_result.get("critique_issues", []):
            if isinstance(item, dict) and item.get("where") and item.get("issue"):
                cleaned_issue, _ = check_text(item["issue"])
                issues.append({
                    "where": str(item["where"]),
                    "issue": cleaned_issue
                })

    return {
        "issues": issues
    }
