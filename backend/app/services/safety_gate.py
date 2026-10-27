import re
from typing import Tuple, List, Dict, Any, Union

SAFETY_REPLACEMENT = "[Removed by safety check. Please ask your doctor or pharmacist.]"
EMERGENCY_REPLY = "This could be an emergency. Please call your local emergency number or go to the nearest hospital now."

# Emergency keywords / phrases to detect in chat or user messages
EMERGENCY_PATTERNS = [
    r"\bchest\s+pain\b",
    r"\bpressure\s+in\s+(?:the\s+)?chest\b",
    r"\btrouble\s+breathing\b",
    r"\bdifficulty\s+breathing\b",
    r"\bshortness\s+of\s+breath\b",
    r"\bcan(?:'t|not)\s+breathe\b",
    r"\bsevere\s+allergic\s+reaction\b",
    r"\banaphylax(?:is|ic)\b",
    r"\b(?:swelling\s+of\s+(?:the\s+)?(?:face|throat)|face\s+(?:or\s+throat\s+)?swelling|throat\s+swelling)\b",
    r"\boverdose[ds]?\b",
    r"\b(?:took|taken)\s+too\s+(?:much|many)\b",
    r"\bswallowed\s+(?:too\s+many|a\s+bottle\s+of)\s+pills\b",
    r"\bunconscious(?:ness)?\b",
    r"\bunresponsive\b",
    r"\bpassed\s+out\b",
    r"\bheavy\s+bleeding\b",
    r"\bsevere\s+bleeding\b",
    r"\bcoughing\s+up\s+blood\b",
    r"\bvomiting\s+blood\b",
    r"\bthoughts\s+of\s+self[- ]?harm\b",
    r"\bself[- ]?harm\b",
    r"\bsuicid(?:e|al)\b",
    r"\bkill\s+myself\b",
    r"\bend(?:ing)?\s+my\s+life\b",
]

# Unsafe claims and absolute safety wording to block
ABSOLUTE_SAFETY_PATTERNS = [
    r"\brisk[- ]free\b",
    r"\bcompletely\s+safe\b",
    r"\bguaranteed\s+safe\b",
    r"\bguarantee\s+safety\b",
    r"\bno\s+side\s+effects\b",
    r"\bzero\s+side\s+effects\b",
    r"\bwithout\s+(?:any\s+)?side\s+effects\b",
    r"\b100%\s+safe\b",
    r"\babsolutely\s+safe\b",
    r"\bentirely\s+safe\b",
    r"\btotally\s+safe\b",
]

# Action verbs directing the patient to alter medication regimens
# (start, stop, skip, replace, switch, increase, decrease dosage)
MEDICATION_ACTION_PATTERNS = [
    # Stop / discontinue advice
    r"\b(?:you\s+should\s+|you\s+must\s+|be\s+sure\s+to\s+|please\s+)?(?:stop|discontinue|quit|cease|halt)\s+(?:taking|using|your|this|the)?\s*([a-zA-Z0-9_\- ]+)?\b",
    # Start / begin advice
    r"\b(?:you\s+should\s+|you\s+must\s+|be\s+sure\s+to\s+|please\s+)?(?:start|begin|commence)\s+(?:taking|using|on)\s+([a-zA-Z0-9_\- ]+)?\b",
    # Skip advice
    r"\b(?:you\s+should\s+|you\s+must\s+|please\s+)?(?:skip|miss|omit)\s+(?:a\s+|your\s+|the\s+)?(?:dose|pill|tablet|medication)\b",
    # Replace / substitute advice
    r"\b(?:you\s+should\s+|please\s+)?(?:replace|substitute)\s+(?:this|your|the)?\s*(?:medicine|medication|drug|pill|tablet|dose)?\s*(?:with|for)\b",
    # Switch advice
    r"\b(?:you\s+should\s+|please\s+)?(?:switch|change)\s+(?:to|from|over\s+to)\s+([a-zA-Z0-9_\- ]+)?\b",
    # Increase / raise dosage advice
    r"\b(?:you\s+should\s+|please\s+)?(?:increase|raise|up|double|boost)\s+(?:your\s+|the\s+)?(?:dose|dosage|amount)\b",
    # Decrease / lower dosage advice
    r"\b(?:you\s+should\s+|please\s+)?(?:decrease|lower|reduce|cut|taper)\s+(?:your\s+|the\s+)?(?:dose|dosage|amount)\b",
]

# Compile patterns for efficiency
_EMERGENCY_REGEXES = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]
_ABSOLUTE_SAFETY_REGEXES = [re.compile(p, re.IGNORECASE) for p in ABSOLUTE_SAFETY_PATTERNS]
_MED_ACTION_REGEXES = [re.compile(p, re.IGNORECASE) for p in MEDICATION_ACTION_PATTERNS]


def is_emergency(text: str) -> bool:
    """
    Check if the input text contains common emergency clinical signals.
    If true, the caller should bypass LLMs and immediately return EMERGENCY_REPLY.
    """
    if not text:
        return False
    lower = text.lower()
    for regex in _EMERGENCY_REGEXES:
        if regex.search(lower):
            return True
    return False


def check_text(text: str) -> Tuple[str, List[str]]:
    """
    Deterministically scan text for blocked phrases (prescriptive advice to change meds,
    or claims that a medicine is guaranteed safe / risk-free).
    Replaces blocked occurrences with SAFETY_REPLACEMENT and returns (sanitized_text, flags).
    """
    if not text or not isinstance(text, str):
        return text or "", []

    flags = []
    sanitized = text

    # 1. Check and replace absolute safety claims
    for regex in _ABSOLUTE_SAFETY_REGEXES:
        matches = list(regex.finditer(sanitized))
        if matches:
            for match in reversed(matches):
                matched_str = match.group(0)
                flags.append(f"Blocked unsafe claim: '{matched_str}'")
                start, end = match.span()
                sanitized = sanitized[:start] + SAFETY_REPLACEMENT + sanitized[end:]

    # 2. Check and replace prescriptive medication advice (start, stop, skip, switch, dosage changes)
    for regex in _MED_ACTION_REGEXES:
        matches = list(regex.finditer(sanitized))
        if matches:
            for match in reversed(matches):
                matched_str = match.group(0).strip()
                # Ensure we don't double replace already replaced safety notices
                if SAFETY_REPLACEMENT in matched_str:
                    continue
                flags.append(f"Blocked prescriptive advice: '{matched_str}'")
                start, end = match.span()
                sanitized = sanitized[:start] + SAFETY_REPLACEMENT + sanitized[end:]

    # Clean up redundant adjacent replacements if any
    double_replacement = f"{SAFETY_REPLACEMENT} {SAFETY_REPLACEMENT}"
    while double_replacement in sanitized:
        sanitized = sanitized.replace(double_replacement, SAFETY_REPLACEMENT)

    return sanitized, flags


def sanitize_dict_strings(data: Any) -> Tuple[Any, List[str]]:
    """
    Recursively traverse dictionaries, lists, and strings to apply safety checks.
    """
    flags: List[str] = []

    if isinstance(data, str):
        cleaned, f = check_text(data)
        flags.extend(f)
        return cleaned, flags
    elif isinstance(data, list):
        cleaned_list = []
        for item in data:
            cleaned_item, f = sanitize_dict_strings(item)
            cleaned_list.append(cleaned_item)
            flags.extend(f)
        return cleaned_list, flags
    elif isinstance(data, dict):
        cleaned_dict = {}
        for k, v in data.items():
            # Don't sanitize rule IDs, URLs, or type tags
            if k in ("url", "uri", "id", "rule_id", "type", "page", "status"):
                cleaned_dict[k] = v
            else:
                cleaned_v, f = sanitize_dict_strings(v)
                cleaned_dict[k] = cleaned_v
                flags.extend(f)
        return cleaned_dict, flags
    return data, flags
