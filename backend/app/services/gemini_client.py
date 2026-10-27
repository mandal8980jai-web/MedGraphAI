import re
import json
import time
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


_genai_client = None
_cached_key = None


def get_genai_client():
    global _genai_client, _cached_key
    if not genai or not settings.is_llm_key_configured:
        _genai_client = None
        _cached_key = None
        return None
    if _genai_client is None or _cached_key != settings.LLM_API_KEY:
        try:
            _genai_client = genai.Client(api_key=settings.LLM_API_KEY)
            _cached_key = settings.LLM_API_KEY
        except Exception as e:
            logger.warning(f"Could not initialize GenAI client: {e}")
            _genai_client = None
            _cached_key = None
            return None
    return _genai_client


def get_candidate_models() -> List[str]:
    """Returns preferred model followed by fallback models in priority order."""
    models = [settings.LLM_MODEL]
    fallbacks = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash"]
    for m in fallbacks:
        if m not in models:
            models.append(m)
    return models


def call_gemini_json(prompt: str, timeout_sec: int = 60, retries: int = 1) -> Optional[Any]:
    """Call Gemini expecting JSON output with timeout and cascade retries."""
    client = get_genai_client()
    if not client:
        return None

    candidate_models = get_candidate_models()
    for model_name in candidate_models:
        for attempt in range(retries + 1):
            try:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json"
                ) if types else None

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                if response and response.text:
                    clean_text = response.text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    elif clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    clean_text = clean_text.strip()
                    return json.loads(clean_text)
            except Exception as e:
                err_lower = str(e).lower()
                logger.warning(f"Gemini JSON call on '{model_name}' attempt {attempt + 1} failed: {type(e).__name__}")
                if "429" in err_lower or "401" in err_lower or "403" in err_lower or "not_found" in err_lower:
                    break
                if attempt < retries:
                    time.sleep(1.0)
                else:
                    break
    logger.error("Gemini JSON call failed across all candidate models.")
    return None


def classify_gemini_error(exc: Optional[Exception] = None) -> str:
    """
    Translates Gemini exceptions into distinct, user-friendly messages:
      - API key/auth: 'Chat service configuration needs attention.'
      - Rate limit/quota: 'The AI service is temporarily busy. Please try again later.'
      - Timeout: 'The request took too long. Please try again.'
      - Other failures: 'Unable to complete the request. Please try again.'
    """
    if not exc:
        return "Unable to complete the request. Please try again."

    err_str = str(exc)
    err_lower = err_str.lower()

    # 1. API Key / Authentication
    if any(k in err_lower for k in ["401", "403", "api_key_invalid", "unauthenticated", "permission_denied", "api key not valid"]):
        return "Chat service configuration needs attention."

    # 2. Rate limit / Quota
    if any(k in err_lower for k in ["429", "resource_exhausted", "quota", "rate limit", "exceeded your current quota"]):
        return "The AI service is temporarily busy. Please try again later."

    # 3. Request timeout
    if any(k in err_lower for k in ["deadline", "timeout", "timed out", "504", "timedout"]):
        return "The request took too long. Please try again."

    # 4. Other failures
    return "Unable to complete the request. Please try again."


def call_gemini_with_search(prompt: str, timeout_sec: int = 60, retries: int = 1) -> Dict[str, Any]:
    """
    Call Gemini with Google Search tool enabled.
    Extracts sources ONLY from grounding metadata, never from model text.
    Implements model fallback cascade and distinct error reporting.
    """
    client = get_genai_client()
    if not client or not settings.is_llm_key_configured:
        return {
            "raw_text": "",
            "parsed_json": None,
            "sources": [],
            "status": "unavailable",
            "error": "Chat service configuration needs attention."
        }

    candidate_models = get_candidate_models()
    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        for attempt in range(retries + 1):
            try:
                config = types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                ) if types else None

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )

                # Extract source links from grounding metadata
                sources = []
                if response and hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    gm = getattr(candidate, "grounding_metadata", None)
                    if gm:
                        chunks = getattr(gm, "grounding_chunks", None) or []
                        for ch in chunks:
                            web = getattr(ch, "web", None)
                            if web:
                                uri = getattr(web, "uri", None)
                                title = getattr(web, "title", None) or getattr(web, "domain", None) or "Medical Web Reference"
                                if uri and not any(s["url"] == uri for s in sources):
                                    sources.append({"title": title, "url": uri})

                raw_text = response.text.strip() if response and response.text else ""
                parsed_json = None
                if raw_text:
                    clean_text = raw_text
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    elif clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    clean_text = clean_text.strip()
                    try:
                        parsed_json = json.loads(clean_text)
                    except Exception:
                        pass

                status = "ok" if sources else "no_source"
                return {
                    "raw_text": raw_text,
                    "parsed_json": parsed_json,
                    "sources": sources,
                    "status": status,
                    "error": None
                }

            except Exception as e:
                last_error = e
                err_msg = str(e)
                logger.warning(f"Gemini search call on '{model_name}' attempt {attempt + 1} failed: {type(e).__name__}")
                is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                is_auth = any(k in err_msg.lower() for k in ["401", "403", "api_key_invalid", "unauthenticated"])
                if is_auth or is_rate_limit:
                    last_error = e
                    break
                if attempt < retries:
                    time.sleep(1.0)
                else:
                    break
            if last_error and any(k in str(last_error).lower() for k in ["429", "resource_exhausted", "401", "403"]):
                break

    user_facing_error = classify_gemini_error(last_error)
    return {
        "raw_text": "",
        "parsed_json": None,
        "sources": [],
        "status": "unavailable",
        "error": user_facing_error
    }


def call_gemini_chat(prompt: str, history: Optional[List[Dict[str, str]]] = None, timeout_sec: int = 60) -> Dict[str, Any]:
    """
    Call Gemini for conversation without search tools.
    Implements model fallback cascade and distinct error messaging.
    """
    client = get_genai_client()
    if not client or not settings.is_llm_key_configured:
        return {
            "reply": "Chat service configuration needs attention.",
            "status": "unavailable",
            "error": "Chat service configuration needs attention."
        }

    candidate_models = get_candidate_models()

    contents = []
    if history:
        for msg in history[-10:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(f"{role.upper()}: {msg.get('content', '')}")
    contents.append(f"USER: {prompt}")
    full_prompt = "\n\n".join(contents)

    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            reply = response.text.strip() if response and response.text else "No response received."
            return {
                "reply": reply,
                "status": "ok"
            }
        except Exception as e:
            last_error = e
            logger.warning(f"Gemini chat on model '{model_name}' failed: {type(e).__name__}")
            err_lower = str(e).lower()
            if any(k in err_lower for k in ["401", "403", "api_key_invalid", "unauthenticated"]):
                break

    user_facing_error = classify_gemini_error(last_error)
    return {
        "reply": user_facing_error,
        "status": "unavailable",
        "error": user_facing_error
    }


def fallback_extract_medicines(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministic rule-based extractor when Gemini API key is not configured or offline.
    Extracts visible medicine candidates without guessing.
    """
    medicines = []
    med_idx = 1

    # Common drug forms/prefixes to strip
    prefix_pattern = re.compile(r'^(tab|tablet|cap|capsule|syr|syrup|inj|injection)\.?\s+', re.IGNORECASE)
    # Strength pattern (e.g. 650mg, 500 mg, 10 mg, 400mg)
    strength_pattern = re.compile(r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|%))', re.IGNORECASE)
    # Frequency pattern (e.g. 1-0-1, 1-1-1, twice a day, once daily, tid, bid, od)
    freq_pattern = re.compile(r'(\b\d-\d-\d\b|\b\d-\d\b|\bonce daily\b|\btwice daily\b|\btwice a day\b|\bthree times a day\b|\bod\b|\bbid\b|\btid\b|\bqid\b)', re.IGNORECASE)
    # Duration pattern (e.g. 5 days, 7 days, 1 month)
    duration_pattern = re.compile(r'(\b\d+\s*(?:days?|weeks?|months?)\b)', re.IGNORECASE)

    for page_item in pages:
        page_num = page_item.get("page", 1)
        text = page_item.get("text", "")
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for line in lines:
            # Skip very short lines, numbers only, or doctor/hospital headers
            if len(line) < 3 or line.isdigit():
                continue
            lower_line = line.lower()
            if any(skip in lower_line for skip in ["dr.", "doctor", "clinic", "hospital", "patient", "date:", "rx", "signature", "phone:"]):
                continue

            cleaned_line = re.sub(r'^\d+[\.\)\-\]]\s*', '', line)
            cleaned_line = prefix_pattern.sub('', cleaned_line)
            parts = cleaned_line.split()
            if not parts:
                continue

            # Check if line contains strength
            strength_match = strength_pattern.search(cleaned_line)
            strength = strength_match.group(1) if strength_match else None

            freq_match = freq_pattern.search(cleaned_line)
            frequency = freq_match.group(1) if freq_match else None

            duration_match = duration_pattern.search(cleaned_line)
            duration = duration_match.group(1) if duration_match else None

            # Candidate name is the first word or two words before dosage
            name_text = parts[0]
            if len(parts) > 1 and not strength_pattern.match(parts[1]) and not parts[1].isdigit():
                name_text = f"{parts[0]} {parts[1]}"
            elif strength:
                name_text = f"{parts[0]} {strength}"

            # Check for unclear characters
            is_unclear = bool(re.search(r'[?~^#|]', name_text)) or len(name_text) < 3

            medicines.append({
                "id": f"m{med_idx}",
                "name_text": name_text,
                "strength": strength,
                "dose": None,
                "frequency": frequency,
                "duration": duration,
                "page": page_num,
                "read_quality": "unclear" if is_unclear else "clear",
                "confirmed": False
            })
            med_idx += 1

    return medicines


def extract_medicines_from_text(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract visible medicines from extracted text pages using Gemini (or deterministic fallback if key missing).
    Preserves page numbers, nulls missing fields, never guesses.
    """
    if not settings.is_llm_key_configured:
        logger.info("Extracting medicines using deterministic extractor (LLM key not configured).")
        return fallback_extract_medicines(pages)

    prompt = (
        "You are an OCR prescription text extractor. Analyze the following extracted prescription text page by page.\n"
        "RULES:\n"
        "1. Extract candidate medicine entries visible in the text.\n"
        "2. For each medicine, extract ONLY what is explicitly visible:\n"
        "   - name_text: string (medicine or brand or drug name)\n"
        "   - strength: string or null (e.g. '650 mg', '500 mg')\n"
        "   - dose: string or null (e.g. '1 tablet')\n"
        "   - frequency: string or null (e.g. 'twice a day', '1-0-1')\n"
        "   - duration: string or null (e.g. '5 days')\n"
        "   - page: integer (page number where found)\n"
        "   - read_quality: string ('clear' if text is easily readable, 'unclear' if smudged, broken, or ambiguous)\n"
        "3. NEVER guess or invent missing values. If a field is not visible, use null.\n"
        "4. DO NOT correct spelling by guessing.\n"
        "5. Output valid JSON as an array of objects.\n\n"
        f"PRESCRIPTION TEXT PAGES:\n{json.dumps(pages, indent=2)}"
    )

    result = call_gemini_json(prompt)
    if isinstance(result, list) and len(result) > 0:
        cleaned_list = []
        for i, item in enumerate(result):
            if isinstance(item, dict) and item.get("name_text"):
                cleaned_list.append({
                    "id": f"m{i+1}",
                    "name_text": str(item.get("name_text")),
                    "strength": item.get("strength") or None,
                    "dose": item.get("dose") or None,
                    "frequency": item.get("frequency") or None,
                    "duration": item.get("duration") or None,
                    "page": item.get("page") or 1,
                    "read_quality": "unclear" if item.get("read_quality") == "unclear" else "clear",
                    "confirmed": False
                })
        return cleaned_list

    logger.warning("Gemini extraction returned empty or invalid format, falling back to deterministic extractor.")
    return fallback_extract_medicines(pages)
