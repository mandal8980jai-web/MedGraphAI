import pytest
from app.services.interaction_engine import (
    check_interactions,
    SAMPLE_DATA_NOTICE,
    load_medicine_catalog,
    load_interaction_rules
)
from app.services.knowledge_graph import build_knowledge_graph
from app.schemas.analysis import Medicine


def test_catalog_and_rules_loaded():
    catalog = load_medicine_catalog()
    rules = load_interaction_rules()
    assert len(catalog) >= 10
    assert len(rules) >= 4

    # Ensure required sample demo medicines exist
    catalog_ids = {m["id"] for m in catalog}
    assert "paracetamol_dolo" in catalog_ids
    assert "paracetamol_crocin" in catalog_ids
    assert "ibuprofen_brufen" in catalog_ids
    assert "aspirin_ecosprin" in catalog_ids
    assert "metformin_glycomet" in catalog_ids
    assert "atorvastatin_atorva" in catalog_ids
    assert "amoxicillin_mox" in catalog_ids
    assert "warfarin_coumadin" in catalog_ids
    assert "clarithromycin_klaricid" in catalog_ids
    assert "simvastatin_zocor" in catalog_ids


def test_known_interaction_pair_high_severity():
    """Warfarin + Aspirin triggers configured high-severity interaction rule r1."""
    medicines = [
        {
            "id": "m1",
            "name_text": "Warfarin 5mg",
            "matched_id": "warfarin_coumadin",
            "ingredients": ["warfarin"],
            "confirmed": True
        },
        {
            "id": "m2",
            "name_text": "Ecosprin 75",
            "matched_id": "aspirin_ecosprin",
            "ingredients": ["aspirin"],
            "confirmed": True
        }
    ]

    result = check_interactions(medicines)
    interactions = result["interactions"]
    assert len(interactions) == 1
    inter = interactions[0]
    assert inter["rule_id"] == "r1"
    assert inter["severity"] == "high"
    assert "bleeding" in inter["note"].lower()
    assert "verify with a pharmacist" in inter["source_label"].lower()
    assert set(inter["medicines"]) == {"m1", "m2"}


def test_duplicate_active_ingredients():
    """Dolo 650 + Crocin both contain paracetamol, triggering duplicate ingredient warning."""
    medicines = [
        {
            "id": "m1",
            "name_text": "Dolo 650",
            "matched_id": "paracetamol_dolo",
            "ingredients": ["paracetamol"],
            "confirmed": True
        },
        {
            "id": "m2",
            "name_text": "Crocin 650",
            "matched_id": "paracetamol_crocin",
            "ingredients": ["paracetamol"],
            "confirmed": True
        }
    ]

    result = check_interactions(medicines)
    duplicates = result["duplicates"]
    assert len(duplicates) == 1
    dup = duplicates[0]
    assert dup["ingredient"] == "paracetamol"
    assert set(dup["medicines"]) == {"m1", "m2"}


def test_unknown_medicine_and_coverage():
    """Unknown medicines appear under not_found and are never labeled safe."""
    medicines = [
        {
            "id": "m1",
            "name_text": "Dolo 650",
            "matched_id": "paracetamol_dolo",
            "ingredients": ["paracetamol"],
            "confirmed": True
        },
        {
            "id": "m_unknown",
            "name_text": "RandomMysticHerb 9000",
            "matched_id": None,
            "ingredients": [],
            "confirmed": True
        }
    ]

    result = check_interactions(medicines)
    coverage = result["coverage"]
    assert coverage["total"] == 2
    assert coverage["found_in_list"] == 1
    assert coverage["not_found"] == ["m_unknown"]

    assert len(coverage["not_checked"]) == 1
    not_checked = coverage["not_checked"][0]
    assert not_checked["id"] == "m_unknown"
    assert "Not checked: not in our list" in not_checked["status"]
    assert "Never assumed safe" in not_checked["reason"]

    # Verify notice is exact
    expected_notice = "Only the medicines and rules in our sample list were checked. A missing warning does not mean there is no interaction."
    assert result["notice"] == expected_notice


def test_configured_moderate_interaction():
    """Aspirin + Ibuprofen triggers moderate severity NSAID interaction."""
    medicines = [
        {"id": "m1", "name_text": "Ecosprin 75", "matched_id": "aspirin_ecosprin", "confirmed": True},
        {"id": "m2", "name_text": "Brufen 400", "matched_id": "ibuprofen_brufen", "confirmed": True}
    ]
    result = check_interactions(medicines)
    interactions = result["interactions"]
    assert len(interactions) == 1
    assert interactions[0]["severity"] == "moderate"
    assert interactions[0]["rule_id"] == "r3"


def test_simvastatin_clarithromycin_interaction():
    """Simvastatin + Clarithromycin triggers high severity interaction."""
    medicines = [
        {"id": "m1", "name_text": "Simvastatin 20", "matched_id": "simvastatin_zocor", "confirmed": True},
        {"id": "m2", "name_text": "Clarithromycin 500", "matched_id": "clarithromycin_klaricid", "confirmed": True}
    ]
    result = check_interactions(medicines)
    interactions = result["interactions"]
    assert len(interactions) == 1
    assert interactions[0]["severity"] == "high"
    assert interactions[0]["rule_id"] == "r4"


def test_knowledge_graph_generation():
    """NetworkX knowledge graph generates medicine nodes, ingredient nodes, and severity edges."""
    medicines = [
        {"id": "m1", "name_text": "Warfarin", "matched_id": "warfarin_coumadin", "confirmed": True},
        {"id": "m2", "name_text": "Aspirin", "matched_id": "aspirin_ecosprin", "confirmed": True},
        {"id": "m3", "name_text": "UnknownFormula", "matched_id": None, "confirmed": True}
    ]
    inter_result = check_interactions(medicines)
    graph = build_knowledge_graph(medicines, inter_result["interactions"])

    nodes = graph["nodes"]
    edges = graph["edges"]

    node_ids = {n["id"] for n in nodes}
    assert "m1" in node_ids
    assert "m2" in node_ids
    assert "m3" in node_ids
    assert "warfarin" in node_ids
    assert "aspirin" in node_ids

    # Check node types
    node_map = {n["id"]: n for n in nodes}
    assert node_map["m1"]["type"] == "medicine"
    assert node_map["warfarin"]["type"] == "ingredient"
    assert node_map["m3"]["is_known"] is False

    # Check edge types
    contains_edges = [e for e in edges if e["type"] == "contains"]
    interact_edges = [e for e in edges if e["type"] == "interacts"]

    assert len(contains_edges) >= 2
    assert len(interact_edges) == 1
    assert interact_edges[0]["severity"] == "high"
    assert set([interact_edges[0]["source"], interact_edges[0]["target"]]) == {"m1", "m2"}


def test_name_matching_integration():
    """Interaction engine resolves medicines even without pre-set matched_id."""
    medicines = [
        {"id": "m1", "name_text": "Warfarin 5mg", "confirmed": True},
        {"id": "m2", "name_text": "Ecosprin 75mg", "confirmed": True}
    ]
    result = check_interactions(medicines)
    assert len(result["interactions"]) == 1
    assert result["interactions"][0]["rule_id"] == "r1"
    assert result["coverage"]["found_in_list"] == 2


def test_api_confirm_medicines_generates_graph_and_interactions():
    """Updating medicines via API triggers deterministic safety check & knowledge graph."""
    import uuid
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.repositories import save_analysis

    client = TestClient(app)
    analysis_id = f"test-analysis-part3-{uuid.uuid4().hex}"
    save_analysis(
        analysis_id=analysis_id,
        created_at="2026-10-26T20:00:00Z",
        original_name="rx_sample.png",
        stored_name="dummy_path.png",
        file_kind="image",
        text_source="ocr",
        page_count=1,
        extracted_text="Warfarin 5mg and Aspirin 100mg",
        medicines=[],
        status="uploaded"
    )

    update_payload = {
        "medicines": [
            {
                "id": "med_1",
                "name_text": "Warfarin 5mg",
                "confirmed": True
            },
            {
                "id": "med_2",
                "name_text": "Ecosprin 75",
                "confirmed": True
            }
        ],
        "context": {
            "age": 45,
            "reason": "Cardiovascular prevention"
        }
    }

    res = client.put(f"/api/analyses/{analysis_id}/medicines", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "confirmed"
    assert "results" in data
    assert data["results"] is not None

    results = data["results"]
    assert "interactions" in results
    assert len(results["interactions"]) == 1
    assert results["interactions"][0]["severity"] == "high"
    assert "graph" in results
    assert len(results["graph"]["nodes"]) >= 2
    assert "notice" in results
    assert "Only the medicines and rules in our sample list were checked" in results["notice"]
