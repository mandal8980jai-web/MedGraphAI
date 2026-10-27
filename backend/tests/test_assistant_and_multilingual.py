import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.language_detection_service import detect_language
from app.services.medicine_equivalence_service import (
    find_verified_medicine,
    verify_active_ingredient_and_strength_equivalence,
    get_verified_alternatives_for_medicine
)
from app.services.pharmacy_search_service import get_pharmacy_listings, build_pharmacy_search_link
from app.services.price_comparison_service import build_medicine_price_comparison
from app.services.medicine_information_service import process_medicine_chat
from app.services.safety_gate import is_emergency, check_text, EMERGENCY_REPLY


@pytest.fixture
def client():
    return TestClient(app)


# Test 1: English medicine question
def test_english_medicine_question():
    lang = detect_language("What is Dolo 650 used for?")
    assert lang == "en"

    with patch("app.services.medicine_information_service.call_gemini_with_search") as mock_search, \
         patch("app.services.medicine_information_service.call_gemini_chat") as mock_chat:
        mock_search.return_value = {"status": "ok", "raw_text": "Dolo 650 contains paracetamol used for fever and mild pain.", "sources": []}
        res = process_medicine_chat("What is Dolo 650 used for?")
        assert res["language"] == "en"
        assert "Dolo 650" in res["reply"] or "paracetamol" in res["reply"]
        assert res["medicine_detected"] == "Dolo 650"


# Test 2: Hindi question written in Devanagari
def test_hindi_question_devanagari():
    lang = detect_language("डोलो 650 किस काम आती है?")
    assert lang == "hi_devanagari"

    with patch("app.services.medicine_information_service.call_gemini_with_search") as mock_search:
        mock_search.return_value = {"status": "ok", "raw_text": "डोलो 650 (Dolo 650) का उपयोग बुखार और दर्द के उपचार में किया जाता है।", "sources": []}
        res = process_medicine_chat("डोलो 650 किस काम आती है?")
        assert res["language"] == "hi_devanagari"
        assert "बुखार" in res["reply"] or "Dolo 650" in res["reply"]


# Test 3: Hinglish question written in Roman script
def test_hinglish_question_roman():
    lang = detect_language("Dolo 650 kis liye khate hain?")
    assert lang == "hinglish"

    with patch("app.services.medicine_information_service.call_gemini_with_search") as mock_search:
        mock_search.return_value = {"status": "ok", "raw_text": "Dolo 650 ek paracetamol tablet hai jo bukhar aur dard ke liye li jaati hai.", "sources": []}
        res = process_medicine_chat("Dolo 650 kis liye khate hain?")
        assert res["language"] == "hinglish"
        assert res["medicine_detected"] == "Dolo 650"


# Test 4: Language-switch request
def test_language_switch_request():
    # User was in Hinglish, then asks "Explain in English"
    lang_en = detect_language("Explain in English", previous_language="hinglish")
    assert lang_en == "en"

    # User in English asks "Hindi mein samjhao"
    lang_hi = detect_language("Hindi mein samjhao", previous_language="en")
    assert lang_hi in ("hi_devanagari", "hinglish")

    lang_deva = detect_language("हिंदी में समझाओ", previous_language="en")
    assert lang_deva == "hi_devanagari"


# Test 5: Follow-up question referring to a previously discussed medicine
def test_followup_pronoun_resolution():
    history = [
        {"role": "user", "content": "What is Dolo 650?"},
        {"role": "assistant", "content": "Dolo 650 is a paracetamol tablet."}
    ]
    with patch("app.services.medicine_information_service.call_gemini_with_search") as mock_search:
        mock_search.return_value = {"status": "ok", "raw_text": "Common side effects include nausea or allergic rash.", "sources": []}
        res = process_medicine_chat("Iske side effects kya hain?", history=history)
        assert res["medicine_detected"] == "Dolo 650"


# Test 6: Ambiguous medicine name
def test_ambiguous_medicine_name():
    # "Dolo" without 650 or 500 should trigger clarification request
    res = process_medicine_chat("What is Dolo?")
    assert "flags" in res
    assert any("ambiguous" in f.lower() for f in res["flags"])
    assert "strength" in res["reply"].lower() or "formulation" in res["reply"].lower()


# Test 7: Verified price comparison
def test_verified_price_comparison(client):
    res = client.get("/api/medicines/compare-prices?query=Dolo+650")
    assert res.status_code == 200
    data = res.json()
    assert data["medicine_name"] == "Dolo 650"
    assert len(data["providers_compared"]) >= 3
    # Check providers
    provider_names = [p["pharmacy_name"] for p in data["providers_compared"]]
    assert "Tata 1mg" in provider_names
    assert "PharmEasy" in provider_names
    # Price honesty: link-only mode must not claim fabricated prices
    for p in data["providers_compared"]:
        assert p["price_status"] == "unverified_link_only"
        assert "Price not verified" in p["price_display"]
        assert "http" in p["direct_url"]


# Test 8: Price unavailable for one or more pharmacies
def test_price_unavailable_link_fallback():
    listings = get_pharmacy_listings("RareMed 100mg")
    assert len(listings) >= 3
    for item in listings:
        assert item["price_status"] == "unverified_link_only"
        assert item["verified_price"] is None
        assert "Price not verified — check pharmacy website" in item["price_display"]


# Test 9: Different pack sizes
def test_different_pack_sizes():
    res = build_medicine_price_comparison("Dolo 650", pack_size="30 tablets")
    assert res["pack_size"] == "30 tablets"
    for p in res["providers_compared"]:
        assert p["pack_size"] == "30 tablets"


# Test 10: Different strengths and formulations
def test_different_strengths_and_formulations():
    # Comparing 650mg tablet vs 500mg tablet
    orig = [{"name": "paracetamol", "strength": "650 mg"}]
    cand_diff_strength = [{"name": "paracetamol", "strength": "500 mg"}]
    is_eq, msg = verify_active_ingredient_and_strength_equivalence(
        orig, cand_diff_strength, original_form="tablet", candidate_form="tablet"
    )
    assert is_eq is False
    assert "strength" in msg.lower()

    # Comparing tablet vs syrup
    cand_diff_form = [{"name": "paracetamol", "strength": "650 mg"}]
    is_eq_form, msg_form = verify_active_ingredient_and_strength_equivalence(
        orig, cand_diff_form, original_form="tablet", candidate_form="syrup"
    )
    assert is_eq_form is False
    assert "dosage form" in msg_form.lower()


# Test 11: Cheaper same-ingredient candidate
def test_cheaper_same_ingredient_candidate():
    alts = get_verified_alternatives_for_medicine("Dolo 650")
    assert alts["status"] == "ok"
    assert len(alts["category_b_brands"]) >= 1
    # Check Category C generic Jan Aushadhi
    assert len(alts["category_c_generics"]) >= 1
    jan_aushadhi = alts["category_c_generics"][0]
    assert "Jan Aushadhi" in jan_aushadhi["product_name"]
    assert jan_aushadhi["verified_mrp_inr"] < alts["original_medicine"]["reference_mrp_inr"]


# Test 12: Different active ingredient incorrectly suggested as equivalent
def test_different_active_ingredient_rejection():
    orig = [{"name": "paracetamol", "strength": "650 mg"}]
    different_ingredient = [{"name": "ibuprofen", "strength": "400 mg"}]
    is_eq, msg = verify_active_ingredient_and_strength_equivalence(
        orig, different_ingredient, original_form="tablet", candidate_form="tablet"
    )
    assert is_eq is False
    assert "missing" in msg.lower() or "different" in msg.lower()

    # In catalog, Category D must be marked as NOT interchangeable
    alts = get_verified_alternatives_for_medicine("Dolo 650")
    assert len(alts["category_d_non_interchangeable"]) >= 1
    cat_d = alts["category_d_non_interchangeable"][0]
    assert "NOT an interchangeable substitute" in cat_d["warning"] or "NOT interchangeable" in cat_d["warning"]


# Test 13: Missing Gemini API key handling
def test_missing_gemini_api_key_handling():
    with patch("app.core.config.settings.LLM_API_KEY", ""):
        with patch("app.services.gemini_client.get_genai_client", return_value=None):
            # Assistant should not crash when API key is missing
            res = process_medicine_chat("What is Dolo 650?")
            assert res is not None
            assert "reply" in res


# Test 14: External website timeout or failure
def test_external_website_timeout_handling():
    with patch("app.services.medicine_information_service.call_gemini_with_search") as mock_search, \
         patch("app.services.medicine_information_service.call_gemini_chat") as mock_chat:
        mock_search.return_value = {"status": "unavailable", "raw_text": "", "error": "Gemini did not answer in time."}
        mock_chat.return_value = {"status": "ok", "reply": "Dolo 650 information."}
        res = process_medicine_chat("Where to buy Dolo 650?")
        # Price comparison and links must still be provided
        assert res["price_comparison"] is not None
        assert len(res["price_comparison"]["providers_compared"]) >= 3


# Test 15: Prescription-required medicine notice
def test_prescription_required_medicine_notice():
    augmentin = find_verified_medicine("Augmentin 625 Duo")
    assert augmentin is not None
    assert augmentin["is_rx_required"] is True

    comp = build_medicine_price_comparison("Augmentin 625 Duo")
    assert comp["is_rx_required"] is True


# Test 16: Safety gate blocking unsafe substitution advice
def test_safety_gate_blocking_unsafe_advice():
    # Emergency detection
    assert is_emergency("I have severe chest pain and trouble breathing") is True
    res = process_medicine_chat("I have severe chest pain")
    assert res["reply"] == EMERGENCY_REPLY

    # Unsafe substitution directive
    unsafe_text = "You should stop taking your medicine and switch to generic immediately. It is 100% safe and risk-free."
    sanitized, flags = check_text(unsafe_text)
    assert "[Removed by safety check" in sanitized
    assert len(flags) >= 2


# Test 17: Existing OCR workflow preservation
def test_existing_ocr_workflow_preserved(client):
    # Documents endpoint exists and rejects empty payload
    res = client.post("/api/documents", files={})
    assert res.status_code == 422


# Test 18: Existing chatbot endpoint preserved
def test_existing_chat_endpoint_preserved(client):
    # Non-existent analysis returns 404
    res = client.post("/api/chat", json={"analysis_id": "non_existent", "message": "hello"})
    assert res.status_code == 404


# Test 19: Assistant chat endpoint endpoint integration
def test_assistant_chat_endpoint_integration(client):
    with patch("app.services.medicine_information_service.call_gemini_with_search") as mock_search:
        mock_search.return_value = {
            "status": "ok",
            "raw_text": "Dolo 650 is a common paracetamol brand.",
            "sources": [{"title": "Tata 1mg", "url": "https://www.1mg.com/drugs/dolo-650-tablet-42111"}]
        }
        res = client.post("/api/assistant/chat", json={
            "message": "Dolo 650 kis kaam aati hai aur sasti kahan milegi?",
            "history": []
        })
        assert res.status_code == 200
        data = res.json()
        assert data["language"] == "hinglish"
        assert data["medicine_detected"] == "Dolo 650"
        assert data["price_comparison"] is not None
        assert len(data["price_comparison"]["providers_compared"]) >= 3


# Test 20: Build and health checks
def test_health_check_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "llm_key_set" in data


# Test 21: Empty message rejection
def test_empty_message_validation(client):
    res_assistant = client.post("/api/assistant/chat", json={"message": "   ", "history": []})
    assert res_assistant.status_code == 400
    assert "Message cannot be empty." in res_assistant.text

    res_chat = client.post("/api/chat", json={"analysis_id": "test", "message": "   "})
    assert res_chat.status_code == 400
    assert "Message cannot be empty." in res_chat.text


# Test 22: Distinct error classification mapping
def test_distinct_error_classification():
    from app.services.gemini_client import classify_gemini_error

    auth_msg = classify_gemini_error(Exception("401 API_KEY_INVALID: API key not valid"))
    assert auth_msg == "Chat service configuration needs attention."

    rate_msg = classify_gemini_error(Exception("429 RESOURCE_EXHAUSTED Quota exceeded for metric"))
    assert rate_msg == "The AI service is temporarily busy. Please try again later."

    timeout_msg = classify_gemini_error(Exception("DeadlineExceeded: 504 Gateway Timeout timed out"))
    assert timeout_msg == "The request took too long. Please try again."

    other_msg = classify_gemini_error(Exception("Internal server unexpected failure"))
    assert other_msg == "Unable to complete the request. Please try again."
