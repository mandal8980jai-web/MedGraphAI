import re
from typing import Tuple, Optional

# Regex patterns for Hindi in Devanagari script
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

# Common Hinglish marker words and phrases
HINGLISH_WORDS = {
    "kya", "hai", "hain", "ke", "ki", "ka", "ko", "se", "mein", "me", "par",
    "liye", "kis", "kaam", "aati", "aata", "khate", "khane", "hoti", "hota",
    "iski", "iska", "iske", "batao", "samjhao", "chahiye", "sasti", "sasta",
    "kahan", "milegi", "milega", "aur", "pe", "bhi", "toh", "ye", "yeh",
    "woh", "wo", "dawa", "dawakhana", "dard", "bukhar", "khansi", "pet",
    "side", "effects", "le", "sakta", "sakti", "kitna", "kitni", "kab",
    "kaise", "nahi", "mat", "karo", "kare", "karna", "baad", "pehle",
    "subah", "shaam", "dopahar", "raat", "goli", "tabiyat", "ilaaj"
}

# Explicit language switch trigger patterns
SWITCH_TO_ENGLISH_PATTERNS = [
    r"\bexplain\s+in\s+english\b",
    r"\bin\s+english\s+please\b",
    r"\benglish\s+mein\b",
    r"\benglish\s+me\b",
    r"\bswitch\s+to\s+english\b",
    r"\bspeak\s+in\s+english\b",
    r"\banswer\s+in\s+english\b",
    r"\benglish\b"
]

SWITCH_TO_HINDI_PATTERNS = [
    r"\bhindi\s+mein\s+samjhao\b",
    r"\bhindi\s+me\s+samjhao\b",
    r"\bhindi\s+mein\s+batao\b",
    r"\bhindi\s+me\s+batao\b",
    r"\bhindi\s+mein\b",
    r"\bhindi\s+me\b",
    r"\bexplain\s+in\s+hindi\b",
    r"\bswitch\s+to\s+hindi\b",
    r"हिंदी\s+में\s+बताओ",
    r"हिंदी\s+में\s+समझाओ",
    r"हिंदी\s+में"
]

SWITCH_TO_HINGLISH_PATTERNS = [
    r"\bhinglish\s+mein\b",
    r"\bhinglish\s+me\b",
    r"\bhinglish\s+mein\s+samjhao\b",
    r"\bswitch\s+to\s+hinglish\b",
    r"\broman\s+hindi\b"
]

_ENGLISH_SWITCH_REGEXES = [re.compile(p, re.IGNORECASE) for p in SWITCH_TO_ENGLISH_PATTERNS]
_HINDI_SWITCH_REGEXES = [re.compile(p, re.IGNORECASE) for p in SWITCH_TO_HINDI_PATTERNS]
_HINGLISH_SWITCH_REGEXES = [re.compile(p, re.IGNORECASE) for p in SWITCH_TO_HINGLISH_PATTERNS]


def detect_language(text: str, previous_language: Optional[str] = None) -> str:
    """
    Detect language of input text:
      - 'hi_devanagari': Hindi written in Devanagari script (e.g. 'डोलो 650 किस काम आती है?')
      - 'hinglish': Hindi written in Roman script (e.g. 'Dolo 650 kis liye khate hain?')
      - 'en': English (e.g. 'What is Dolo 650 used for?')
    Respects explicit language switch instructions and conversation memory.
    """
    if not text or not text.strip():
        return previous_language or "en"

    clean = text.strip()
    lower = clean.lower()

    # 1. Check explicit language switch requests
    for rx in _ENGLISH_SWITCH_REGEXES:
        if rx.search(lower):
            # If the user only said "Explain in English" or similar
            return "en"

    for rx in _HINDI_SWITCH_REGEXES:
        if rx.search(clean):
            # Check if prompt itself was in devanagari
            if DEVANAGARI_REGEX.search(clean):
                return "hi_devanagari"
            return "hi_devanagari"

    for rx in _HINGLISH_SWITCH_REGEXES:
        if rx.search(lower):
            return "hinglish"

    # 2. Check for Devanagari characters
    devanagari_chars = len(DEVANAGARI_REGEX.findall(clean))
    total_alpha = len(re.findall(r"\w", clean))

    if devanagari_chars > 0 and (total_alpha == 0 or devanagari_chars / max(total_alpha, 1) > 0.25):
        return "hi_devanagari"

    # 3. Check for Hinglish words (Roman script Hindi)
    words = set(re.findall(r"\b[a-zA-Z]+\b", lower))
    hinglish_match_count = len(words.intersection(HINGLISH_WORDS))

    if hinglish_match_count >= 2:
        return "hinglish"
    elif hinglish_match_count == 1:
        # Check specific strong Hinglish indicator words
        strong_hinglish = {"kahan", "milegi", "milega", "sasti", "sasta", "khate", "samjhao", "batao", "iska", "iske", "iski"}
        if words.intersection(strong_hinglish):
            return "hinglish"
        if previous_language in ("hinglish", "hi_devanagari"):
            return previous_language

    # 4. Short follow-up questions inheriting previous language preference
    short_query = len(clean.split()) <= 4
    if short_query and previous_language:
        # e.g., "Side effects?", "Any warnings?", "Price?" in Hinglish or Hindi context
        return previous_language

    return "en"


def get_language_system_directive(lang: str) -> str:
    """
    Returns strict language and script system instructions for Gemini.
    """
    if lang == "hi_devanagari":
        return (
            "LANGUAGE & SCRIPT INSTRUCTION:\n"
            "- The user is asking in Hindi (Devanagari script).\n"
            "- YOU MUST RESPOND IN HINDI USING DEVANAGARI SCRIPT (हिंदी भाषा).\n"
            "- Preserve medicine brand names, chemical salt names, strengths, and units "
            "(e.g., 'Dolo 650', 'Paracetamol 650 mg', 'Tablet') in clear English/Roman script "
            "alongside Devanagari for medical accuracy.\n"
            "- Use natural, respectful, and easily understandable Hindi.\n"
        )
    elif lang == "hinglish":
        return (
            "LANGUAGE & SCRIPT INSTRUCTION:\n"
            "- The user is asking in Hinglish (Hindi written in Roman / English script).\n"
            "- YOU MUST RESPOND IN CONVERSATIONAL HINGLISH using Roman alphabet.\n"
            "- Example style: 'Dolo 650 ek paracetamol tablet hai jo aamtaur par bukhar aur sharir dard ke liye di jaati hai...'\n"
            "- Preserve exact medicine names, salts, and strengths (e.g. Paracetamol 650 mg, Tablet, 15 tablets pack).\n"
            "- Do not switch to Devanagari unless explicitly asked. Keep the script in Roman English letters.\n"
        )
    else:
        return (
            "LANGUAGE & SCRIPT INSTRUCTION:\n"
            "- Respond in clear, accessible, and grammatically correct English.\n"
            "- Use plain language for medical concepts.\n"
        )
