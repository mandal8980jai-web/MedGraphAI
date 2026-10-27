import pytest
import asyncio
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.db.repositories import save_analysis, get_analysis_by_id, get_events_since
from app.agents.alternative_research_agent import check_missing_patient_context, research_alternatives_for_medicines
from app.agents.pharmacist_research_agent import research_medicine_evidence
from app.agents.safety_critic_agent import review_safety_and_evidence
from app.workflows.analysis_workflow import run_full_analysis_workflow


@pytest.fixture
def client():
    return TestClient(app)


def test_refuse_analysis_unconfirmed_medicines(client):
    """Refuses to analyze if any medicine is unconfirmed."""
    analysis_id = f"test-unconfirmed-{uuid.uuid4().hex}"
    save_analysis(
        analysis_id=analysis_id,
        created_at="2026-10-26T12:00:00Z",
        original_name="test_rx.png",
        stored_name="dummy.png",
        file_kind="image",
        text_source="ocr",
        page_count=1,
        extracted_text="Dolo 650",
        medicines=[{"id": "m1", "name_text": "Dolo 650", "confirmed": False}],
        status="uploaded"
    )

    res = client.post(f"/api/analyses/{analysis_id}/run")
    assert res.status_code == 400
    assert "not confirmed" in res.json()["detail"]["error"]


def test_alternative_research_needs_more_info_without_gemini_call():
    """Missing patient context fields trigger needs_more_info and skip LLM calls entirely."""
    incomplete_context = {
        "age": 45,
        "reason": "Pain relief"
        # allergies, pregnancy, kidney_liver missing
    }

    missing = check_missing_patient_context(incomplete_context)
    assert set(missing) == {"allergies", "pregnancy", "kidney_liver"}

    # With missing context, research_alternatives_for_medicines must NOT call Gemini
    with patch("app.agents.alternative_research_agent.call_gemini_with_search") as mock_gemini:
        res = research_alternatives_for_medicines(
            medicines=[{"id": "m1", "name_text": "Dolo 650"}],
            context=incomplete_context
        )
        assert res["status"] == "needs_more_info"
        assert set(res["missing"]) == {"allergies", "pregnancy", "kidney_liver"}
        assert len(res["items"]) == 0
        mock_gemini.assert_not_called()


def test_research_without_sources_sets_no_source():
    """If Gemini answers but no grounding metadata links return, status is 'no_source'."""
    mock_gemini_return = {
        "raw_text": '{"findings": ["Paracetamol is an analgesic and antipyretic."]}',
        "parsed_json": {"findings": ["Paracetamol is an analgesic and antipyretic."]},
        "sources": [],  # No grounding sources returned!
        "status": "no_source",
        "error": None
    }

    with patch("app.agents.pharmacist_research_agent.call_gemini_with_search", return_value=mock_gemini_return):
        res = research_medicine_evidence(
            medicine={"id": "m1", "name_text": "Dolo 650"},
            other_medicines=[]
        )
        assert res["status"] == "no_source"
        assert len(res["sources"]) == 0
        assert len(res["findings"]) > 0


def test_rate_limit_and_timeout_handling():
    """Rate limits (429) or timeouts return 'unavailable' with a plain readable explanation."""
    mock_timeout_return = {
        "raw_text": "",
        "parsed_json": None,
        "sources": [],
        "status": "unavailable",
        "error": "Gemini rate limit reached. Please retry in a few moments."
    }

    with patch("app.agents.pharmacist_research_agent.call_gemini_with_search", return_value=mock_timeout_return):
        res = research_medicine_evidence(
            medicine={"id": "m1", "name_text": "Warfarin"},
            other_medicines=[]
        )
        assert res["status"] == "unavailable"
        assert "rate limit reached" in res["findings"][0].lower()


def test_partial_agent_failure_resilience():
    """When one helper fails, the remaining workflow stages still complete successfully."""
    analysis_id = f"test-resilience-{uuid.uuid4().hex}"
    run_id = f"run-resilience-{uuid.uuid4().hex}"

    confirmed_meds = [
        {"id": "m1", "name_text": "Warfarin 5mg", "confirmed": True, "ingredients": ["warfarin"], "matched_id": "warfarin_coumadin"},
        {"id": "m2", "name_text": "Ecosprin 75", "confirmed": True, "ingredients": ["aspirin"], "matched_id": "aspirin_ecosprin"}
    ]

    save_analysis(
        analysis_id=analysis_id,
        created_at="2026-10-26T12:00:00Z",
        original_name="test_rx.png",
        stored_name="dummy.png",
        file_kind="image",
        text_source="ocr",
        page_count=1,
        extracted_text="Warfarin and Ecosprin",
        medicines=confirmed_meds,
        status="confirmed"
    )

    # Mock evidence helper to fail with an exception
    with patch("app.workflows.analysis_workflow.research_medicine_evidence", side_effect=RuntimeError("Network timeout")):
        asyncio.run(run_full_analysis_workflow(
            analysis_id=analysis_id,
            run_id=run_id,
            medicines=confirmed_meds,
            context={}
        ))

    analysis = get_analysis_by_id(analysis_id)
    assert analysis.status == "done"
    results = analysis.results
    assert results is not None
    # Deterministic interactions must still be found!
    assert len(results["interactions"]) == 1
    assert results["interactions"][0]["severity"] == "high"
    # Evidence marks unavailable for failed items
    assert all(e["status"] == "unavailable" for e in results["evidence"])


def test_chat_emergency_handling(client):
    """Emergency queries immediately return emergency advice and bypass LLM."""
    analysis_id = f"test-chat-emergency-{uuid.uuid4().hex}"
    save_analysis(
        analysis_id=analysis_id,
        created_at="2026-10-26T12:00:00Z",
        original_name="test_rx.png",
        stored_name="dummy.png",
        file_kind="image",
        text_source="ocr",
        page_count=1,
        extracted_text="Dolo 650",
        medicines=[{"id": "m1", "name_text": "Dolo 650", "confirmed": True}],
        status="confirmed"
    )

    with patch("app.agents.conversation_agent.call_gemini_chat") as mock_chat:
        res = client.post("/api/chat", json={
            "analysis_id": analysis_id,
            "message": "I took too much and now have severe chest pain and trouble breathing!",
            "history": []
        })
        assert res.status_code == 200
        data = res.json()
        assert "call your local emergency number or go to the nearest hospital now" in data["reply"]
        assert len(data["flags"]) > 0
        mock_chat.assert_not_called()


def test_chat_non_emergency_and_safety_filtering(client):
    """Non-emergency queries use Conversation Agent and filter out prescriptive changes."""
    analysis_id = f"test-chat-normal-{uuid.uuid4().hex}"
    save_analysis(
        analysis_id=analysis_id,
        created_at="2026-10-26T12:00:00Z",
        original_name="test_rx.png",
        stored_name="dummy.png",
        file_kind="image",
        text_source="ocr",
        page_count=1,
        extracted_text="Dolo 650",
        medicines=[{"id": "m1", "name_text": "Dolo 650", "confirmed": True}],
        status="confirmed"
    )

    # Mock Gemini returning prescriptive advice to test safety filter
    mock_llm_reply = {
        "reply": "Dolo 650 contains paracetamol. You should stop taking it if your temperature is normal.",
        "status": "ok"
    }

    with patch("app.agents.conversation_agent.call_gemini_chat", return_value=mock_llm_reply):
        res = client.post("/api/chat", json={
            "analysis_id": analysis_id,
            "message": "What is Dolo 650 used for?",
            "history": []
        })
        assert res.status_code == 200
        data = res.json()
        assert "[Removed by safety check. Please ask your doctor or pharmacist.]" in data["reply"]
        assert "stop taking" not in data["reply"].lower()
        assert len(data["flags"]) > 0

