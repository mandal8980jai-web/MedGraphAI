import re
from typing import Dict, Any, List, Optional, Tuple
from app.services.safety_gate import is_emergency, check_text, EMERGENCY_REPLY
from app.services.language_detection_service import detect_language, get_language_system_directive
from app.services.medicine_equivalence_service import find_verified_medicine
from app.services.price_comparison_service import build_medicine_price_comparison
from app.services.gemini_client import call_gemini_chat, call_gemini_with_search


PRICE_INTENT_PATTERNS = [
    r"\bprice\b", r"\bcost\b", r"\bsasti\b", r"\bsasta\b", r"\bcheapest\b",
    r"\bcheaper\b", r"\bkahan\s+milegi\b", r"\bkahan\s+milega\b", r"\bwhere\s+to\s+buy\b",
    r"\bwhere\s+can\s+i\s+buy\b", r"\bbuy\b", r"\bpurchase\b", r"\border\b",
    r"\bpharmacy\b", r"\brate\b", r"\bkitne\s+ki\b", r"\bkitne\s+ka\b",
    r"\balternative\b", r"\balternatives\b", r"\bgeneric\b", r"\bsubstitute\b"
]
_PRICE_REGEXES = [re.compile(p, re.IGNORECASE) for p in PRICE_INTENT_PATTERNS]


def is_price_or_shopping_intent(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    for rx in _PRICE_REGEXES:
        if rx.search(lower):
            return True
    return False


def extract_medicine_from_context(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    prescription_medicines: Optional[List[Dict[str, Any]]] = None
) -> Tuple[Optional[str], bool]:
    """
    Identifies candidate medicine name from current prompt, conversation history, or prescription.
    Returns (medicine_name, is_ambiguous).
    """
    from app.services.medicine_equivalence_service import load_verified_medicines
    clean = message.strip()
    clean_lower = clean.lower()

    # 1. Check if user explicitly refers to a known prescription medicine
    if prescription_medicines:
        for pm in prescription_medicines:
            p_name = pm.get("name_text", "")
            if p_name and p_name.lower() in clean_lower:
                return p_name, False

    # 2. Check for pronoun resolution ("iska", "iske", "this medicine", "it", "yeh dawa")
    pronoun_pattern = re.compile(r"\b(iske|iska|iski|this\s+medicine|the\s+medicine|it|yeh\s+dawa|ye\s+dawa)\b", re.IGNORECASE)
    has_pronoun = bool(pronoun_pattern.search(clean))

    if has_pronoun and history:
        # Search backwards in history for a medicine name
        all_meds = load_verified_medicines()
        for msg in reversed(history):
            content = msg.get("content", "").lower()
            for med in all_meds:
                brand = med.get("brand_name", "")
                if brand.lower() in content:
                    return brand, False
                for alias in med.get("aliases", []):
                    if alias.lower() in content:
                        return brand, False

    # 3. Check for specific ambiguity keywords first:
    # E.g. "What is Dolo?" or "Tell me about Crocin"
    all_meds = load_verified_medicines()

    # Check if vague name is queried without strength
    dolo_words = re.findall(r"\bdolo\b", clean_lower)
    if dolo_words and not re.search(r"\b(650|500|120|250)\b", clean_lower):
        return "Dolo", True

    crocin_words = re.findall(r"\bcrocin\b", clean_lower)
    if crocin_words and not re.search(r"\b(650|500|advance|pain\s+relief|drops|syrup)\b", clean_lower):
        return "Crocin", True

    # 4. Search verified medicines in current message (prioritize longer matching aliases)
    best_candidate: Optional[str] = None
    best_len = 0
    for med in all_meds:
        brand = med.get("brand_name", "")
        if brand.lower() in clean_lower and len(brand) > best_len:
            best_candidate = brand
            best_len = len(brand)
        for alias in med.get("aliases", []):
            if alias.lower() in clean_lower and len(alias) > best_len:
                best_candidate = brand
                best_len = len(alias)

    if best_candidate:
        return best_candidate, False

    # 5. Direct lookup via find_verified_medicine
    verified = find_verified_medicine(clean)
    if verified:
        return verified.get("brand_name"), False

    # 6. If prescription medicines provided and only one exists, default to it
    if prescription_medicines and len(prescription_medicines) == 1 and (has_pronoun or is_price_or_shopping_intent(clean)):
        return prescription_medicines[0].get("name_text"), False

    return None, False


def process_medicine_chat(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    prescription_medicines: Optional[List[Dict[str, Any]]] = None,
    preferred_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main orchestration function for the Multilingual Medicine & Price Assistant.
    """
    # Step 0: Check empty message
    if not message or not message.strip():
        return {
            "reply": "Please type a question or medicine name to get started.",
            "language": "en",
            "medicine_detected": None,
            "price_comparison": None,
            "alternatives": None,
            "sources": [],
            "flags": ["Empty query provided"]
        }

    # Step 1: Emergency safety gate (instant bypass)
    if is_emergency(message):
        return {
            "reply": EMERGENCY_REPLY,
            "language": "en",
            "medicine_detected": None,
            "price_comparison": None,
            "alternatives": None,
            "sources": [],
            "flags": ["Emergency symptom detected - directed to emergency medical care"]
        }

    # Step 2: Language detection & preference handling
    detected_lang = detect_language(message, previous_language=preferred_language)
    lang_directive = get_language_system_directive(detected_lang)

    # Step 3: Medicine identification and ambiguity resolution
    med_name, is_ambiguous = extract_medicine_from_context(message, history, prescription_medicines)

    # If ambiguous medicine name (e.g., "Dolo" or "Crocin" with missing strength)
    if is_ambiguous:
        if detected_lang == "hi_devanagari":
            ambiguity_msg = (
                f"कृपया {med_name or 'दवा'} की सटीक स्ट्रेंथ और रूप स्पष्ट करें (उदाहरण के लिए: {med_name} 650 mg टैबलेट या 500 mg)। "
                "अलग-अलग स्ट्रेंथ और फॉर्मूलेशन के उपयोग और खुराक में अंतर होता है।"
            )
        elif detected_lang == "hinglish":
            ambiguity_msg = (
                f"Kripya {med_name or 'dawa'} ki exact strength aur formulation confirm karein (jaise ki: {med_name} 650 mg tablet ya 500 mg)। "
                "Alag-alag strength ke hisab se dose aur upyog badal jaate hain."
            )
        else:
            ambiguity_msg = (
                f"Please specify the exact brand strength and formulation for {med_name or 'the medication'} "
                f"(for example: {med_name} 650 mg tablet or 500 mg). Different strengths and dosage forms have distinct therapeutic indications."
            )

        return {
            "reply": ambiguity_msg,
            "language": detected_lang,
            "medicine_detected": med_name,
            "price_comparison": None,
            "alternatives": None,
            "sources": [],
            "flags": ["Ambiguous medicine strength/formulation requested clarification"]
        }

    # Step 4: Price comparison / Shopping intent check
    price_intent = is_price_or_shopping_intent(message)
    price_comp = None
    alternatives = None

    if med_name and (price_intent or "sasti" in message.lower() or "price" in message.lower() or "kahan" in message.lower()):
        price_comp = build_medicine_price_comparison(med_name)
        alternatives = price_comp.get("alternatives")

    # Step 5: Build clinical prompt for Gemini
    prescription_context_str = ""
    if prescription_medicines:
        p_list = [f"- {m.get('name_text', '')} ({m.get('strength', 'N/A')})" for m in prescription_medicines]
        prescription_context_str = "USER'S CURRENT CONFIRMED PRESCRIPTION MEDICINES:\n" + "\n".join(p_list) + "\n\n"

    system_prompt = (
        "You are MediGraph AI's Multilingual Medicine Information & Clinical Decision-Support Assistant.\n"
        f"{lang_directive}\n"
        "STRICT CLINICAL SAFETY RULES:\n"
        "1. You are an educational and decision-support assistant, NOT a doctor or personal pharmacist.\n"
        "2. NEVER diagnose the user or tell them to start, stop, increase, decrease, or replace any prescribed medicine.\n"
        "3. NEVER say any medicine is 'completely safe', 'risk-free', or has 'no side effects'.\n"
        "4. If discussing cheaper or generic alternatives, always state clearly: 'Confirm brand or generic substitution with your doctor or pharmacist.'\n"
        "5. For prescription-only medicines (antibiotics, blood pressure, statins, etc.), remind user that a valid doctor's prescription is legally required.\n"
        "6. If prices or buying is asked, direct them to verify live pricing and stock on authentic online pharmacies (Tata 1mg, PharmEasy, Netmeds, Apollo Pharmacy).\n"
        "7. Structure your answer clearly and naturally:\n"
        "   - Overview & Active Ingredients\n"
        "   - Common Uses\n"
        "   - Key Side Effects & Precautions\n"
        "   - Price & Pharmacy Advice (if relevant)\n"
        "   - Medical Safety Disclaimer\n\n"
        f"{prescription_context_str}"
        f"USER MESSAGE: {message}"
    )

    # Use search tool if key is set, or chat fallback
    search_res = call_gemini_with_search(system_prompt)
    if search_res.get("status") != "unavailable" and search_res.get("raw_text"):
        raw_reply = search_res["raw_text"]
        sources = search_res.get("sources", [])
    else:
        chat_res = call_gemini_chat(system_prompt, history=history)
        raw_reply = chat_res.get("reply", "")
        sources = []

    # Apply safety check gate
    safe_reply, flags = check_text(raw_reply)

    # Step 6: Return unified assistant response
    return {
        "reply": safe_reply,
        "language": detected_lang,
        "medicine_detected": med_name,
        "price_comparison": price_comp,
        "alternatives": alternatives,
        "sources": sources,
        "flags": flags
    }
