import json
from typing import Dict, Any, List, Optional
from app.services.gemini_client import call_gemini_chat
from app.services.safety_gate import is_emergency, check_text, EMERGENCY_REPLY


def chat_with_conversation_agent(
    message: str,
    medicines: List[Dict[str, Any]],
    results: Optional[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Chat Helper (Conversation Agent):
    Answers questions about confirmed medicines and results.
    Explains findings in plain words. Asks for missing patient details.
    Strict privacy rule: Sees confirmed medicines and results, NOT raw prescription text.
    Strict safety rule: Blocks prescriptive dosage changes and redirects emergency symptoms immediately.
    """
    # 1. Emergency detection gate: immediate exit without LLM call
    if is_emergency(message):
        return {
            "reply": EMERGENCY_REPLY,
            "flags": ["Emergency symptom detected - directed to emergency services"]
        }

    # 2. Build structured safe context
    med_summary = [
        f"- {m.get('name_text', 'Unknown')} ({m.get('strength', 'strength not specified')}, dose: {m.get('dose', 'not specified')}, frequency: {m.get('frequency', 'not specified')})"
        for m in medicines
    ]

    interactions_summary = []
    if results and "interactions" in results:
        for inter in results.get("interactions", []):
            names = inter.get("medicine_names", inter.get("medicines", []))
            interactions_summary.append(f"- Warning ({inter.get('severity', 'moderate')}): {' + '.join(names)} -> {inter.get('note')}")

    duplicates_summary = []
    if results and "duplicates" in results:
        for dup in results.get("duplicates", []):
            duplicates_summary.append(f"- Duplicate active ingredient {dup.get('ingredient')} in {', '.join(dup.get('medicine_names', []))}")

    missing_context = []
    if not context or not context.get("age"):
        missing_context.append("age")
    if not context or not context.get("reason"):
        missing_context.append("condition being treated")
    if not context or not context.get("allergies"):
        missing_context.append("allergies")

    missing_notice = f"Missing clinical context: {', '.join(missing_context)}." if missing_context else "All clinical context provided."

    # Detect user language (English, Hindi Devanagari, or Hinglish)
    from app.services.language_detection_service import detect_language, get_language_system_directive
    user_lang = detect_language(message)
    lang_directive = get_language_system_directive(user_lang)

    system_instructions = (
        "You are MediGraph AI's friendly Patient Education & Medication Safety Assistant.\n"
        "You are helping a patient or student understand their confirmed medication review.\n\n"
        f"{lang_directive}\n"
        "STRICT SAFETY & MEDICAL RULES:\n"
        "1. NEVER tell a patient to start, stop, skip, switch, replace, increase, or decrease any medication or dose.\n"
        "2. NEVER say any medicine is 'completely safe', 'risk-free', or has 'no side effects'.\n"
        "3. Emphasize that all findings are decision-support aids for clinician review.\n"
        "4. Always recommend speaking with their doctor or pharmacist before making any changes.\n"
        "5. Explain medical terms in plain, easy-to-understand words.\n\n"
        f"CONFIRMED MEDICATIONS:\n" + ("\n".join(med_summary) if med_summary else "No confirmed medicines.") + "\n\n"
        f"CONFIGURED INTERACTIONS:\n" + ("\n".join(interactions_summary) if interactions_summary else "No configured interactions found in sample list.") + "\n\n"
        f"DUPLICATE ACTIVE INGREDIENTS:\n" + ("\n".join(duplicates_summary) if duplicates_summary else "None.") + "\n\n"
        f"PATIENT CONTEXT STATUS: {missing_notice}\n"
    )

    combined_prompt = f"{system_instructions}\n\nUSER QUESTION: {message}"

    res = call_gemini_chat(combined_prompt, history=history)
    raw_reply = res.get("reply", "")

    # Apply safety check gate to LLM response
    safe_reply, flags = check_text(raw_reply)

    return {
        "reply": safe_reply,
        "flags": flags,
        "language": user_lang
    }
