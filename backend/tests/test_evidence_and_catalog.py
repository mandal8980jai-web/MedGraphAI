import pytest
from unittest.mock import patch, MagicMock
from app.services.medicine_matcher import normalize_medicine_name, match_medicine_name
from app.services.medical_evidence_service import (
    retrieve_medicine_evidence,
    query_openfda_drug_label,
    query_pubmed_literature,
    _EVIDENCE_CACHE
)
from app.agents.alternative_research_agent import (
    research_alternatives_for_medicines,
    check_missing_patient_context
)


def test_medicine_present_in_local_catalog():
    """Verify medicine directly present in catalog matches deterministically."""
    res_dolo = match_medicine_name("Dolo 650")
    assert res_dolo["match_status"] == "matched"
    assert res_dolo["matched_id"] == "paracetamol_dolo"
    assert "paracetamol" in res_dolo["ingredients"]
    assert res_dolo["catalog_status"] == "matched"

    res_eco = match_medicine_name("Ecosprin 75")
    assert res_eco["match_status"] == "matched"
    assert res_eco["matched_id"] == "aspirin_ecosprin"
    assert "aspirin" in res_eco["ingredients"]

    res_warf = match_medicine_name("Warfarin 5mg")
    assert res_warf["match_status"] == "matched"
    assert res_warf["matched_id"] == "warfarin_coumadin"
    assert "warfarin" in res_warf["ingredients"]


def test_verified_brand_generic_aliases():
    """Verify pharmaceutical form prefixes/suffixes and brand aliases match correctly."""
    aliases = [
        "Tablet Dolo 650",
        "Tab. Dolo 650",
        "Dolo 650 Tablet",
        "Dolo 650mg tab",
        "Dolo-650",
        "Calpol 650",
        "Crocin Advance",
        "Pacimol 650"
    ]
    for alias in aliases:
        res = match_medicine_name(alias)
        assert res["match_status"] == "matched", f"Failed for {alias}: {res}"
        assert res["catalog_status"] == "matched"
        assert "paracetamol" in res["ingredients"]


def test_unknown_medicine_honest_classification():
    """Unknown or unindexed medicines are not matched and not assumed safe."""
    res = match_medicine_name("Zylocran 50mg")
    assert res["match_status"] == "not_found"
    assert res["matched_id"] is None
    assert res["catalog_status"] == "not_in_catalog"
    assert "unknown or unsafe" in res["note"].lower()

    res_fake = match_medicine_name("NonExistentChemicalXYZ 100mg")
    assert res_fake["match_status"] == "not_found"
    assert res_fake["catalog_status"] == "not_in_catalog"


def test_successful_live_evidence_retrieval():
    """Live evidence retrieval queries authoritative medical databases (FDA / PubMed)."""
    # Clear cache for deterministic test
    _EVIDENCE_CACHE.pop("dolo", None)
    _EVIDENCE_CACHE.pop("paracetamol", None)

    med = {"id": "m1", "name_text": "Dolo 650"}
    res = retrieve_medicine_evidence(med)

    assert res["status"] == "ok"
    assert res["evidence_tier"] in ["live_evidence", "cached_evidence"]
    assert len(res["findings"]) > 0
    assert len(res["sources"]) > 0


def test_citation_validation():
    """Every retrieved source must have a valid title, HTTPS URL, and non-empty evidence excerpt."""
    med = {"id": "m1", "name_text": "Ibuprofen 400"}
    res = retrieve_medicine_evidence(med)

    assert len(res["sources"]) > 0
    for src in res["sources"]:
        assert src["title"] and isinstance(src["title"], str)
        assert src["url"].startswith("https://")
        assert src["source_type"] in ["official_drug_label", "peer_reviewed_research", "google_search_grounding"]
        assert "evidence_excerpt" in src and len(src["evidence_excerpt"]) > 5


def test_no_search_results_honest_handling():
    """Unknown / invented medicine returns no_results without inventing fake citations."""
    med = {"id": "m_fake", "name_text": "Zylocran 50mg"}
    res = retrieve_medicine_evidence(med)

    assert res["status"] == "no_results"
    assert res["evidence_tier"] == "not_confidently_identified"
    assert len(res["sources"]) == 0  # Crucial: NEVER fabricate fake citations
    assert any("no verified medical evidence" in f.lower() for f in res["findings"])


def test_provider_failure_graceful_fallback():
    """When external providers fail with timeout/network error, system falls back safely."""
    with patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
        _EVIDENCE_CACHE.clear()

        # 1. For a catalogued medicine, falls back to local catalog tier
        med_known = {"id": "m1", "name_text": "Brufen 400"}
        res_known = retrieve_medicine_evidence(med_known)
        assert res_known["status"] == "ok"
        assert res_known["evidence_tier"] == "local_catalog"
        assert any("catalog match" in f.lower() for f in res_known["findings"])

        # 2. For an unknown medicine, returns research_unavailable
        med_unknown = {"id": "m2", "name_text": "UncataloguedMedUnknown123"}
        res_unknown = retrieve_medicine_evidence(med_unknown)
        assert res_unknown["status"] in ["no_results", "unavailable"]


def test_alternatives_no_empty_bullets_with_context():
    """Alternatives research with context returns verified options and never empty bullet lists."""
    meds = [
        {"id": "m1", "name_text": "Dolo 650"},
        {"id": "m2", "name_text": "Zylocran 50mg"}
    ]
    context = {
        "age": "52",
        "reason": "Fever and joint pain",
        "allergies": "None",
        "pregnancy": "None",
        "kidney_liver": "Normal"
    }

    res = research_alternatives_for_medicines(meds, context)
    assert res["status"] == "ok"
    assert len(res["items"]) == 2

    # Check Dolo 650 alternatives
    dolo_item = res["items"][0]
    assert dolo_item["status"] == "ok"
    assert len(dolo_item["options"]) > 0
    # Must contain verified Category B brand or Category C generic
    assert any("equivalent brand" in opt.lower() or "generic" in opt.lower() for opt in dolo_item["options"])
    # Must contain safety directive
    assert any("never independently stop" in opt.lower() for opt in dolo_item["options"])

    # Check Zylocran (unknown drug) alternatives
    zylocran_item = res["items"][1]
    assert len(zylocran_item["options"]) > 0
    # Must explain that no verified alternatives are found instead of blank bullets
    assert any("no verified direct therapeutic alternatives" in opt.lower() for opt in zylocran_item["options"])
    assert any("never independently stop" in opt.lower() for opt in zylocran_item["options"])


def test_alternatives_needs_more_info_when_context_missing():
    """When clinical context is incomplete, status is needs_more_info and items=[] for safety."""
    meds = [{"id": "m1", "name_text": "Dolo 650"}]
    incomplete_context = {"age": "45"}

    res = research_alternatives_for_medicines(meds, incomplete_context)
    assert res["status"] == "needs_more_info"
    assert "reason" in res["missing"]
    assert "allergies" in res["missing"]
    assert len(res["items"]) == 0
