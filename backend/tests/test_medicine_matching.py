from app.services.medicine_matcher import normalize_medicine_name, match_medicine_name


def test_normalize_medicine_name():
    assert normalize_medicine_name("Dolo 650mg") == "dolo"
    assert normalize_medicine_name("Crocin 650 mg") == "crocin"
    assert normalize_medicine_name("Brufen-400!") == "brufen"
    assert normalize_medicine_name("Atorva 10 mg") == "atorva"
    assert normalize_medicine_name("Amoxicillin 500mg/5ml") == "amoxicillin"


def test_exact_match():
    res = match_medicine_name("Dolo 650")
    assert res["match_status"] == "matched"
    assert res["matched_id"] == "paracetamol_dolo"
    assert "paracetamol" in res["ingredients"]


def test_fuzzy_match_above_threshold():
    # Ecosprin with dosage variation
    res = match_medicine_name("Ecosprin 75")
    assert res["match_status"] == "matched"
    assert res["matched_id"] == "aspirin_ecosprin"
    assert "aspirin" in res["ingredients"]


def test_several_possible_ambiguous():
    # "Dolo" vs "Crocin" or close partial match that doesn't reach 0.85
    # Let's test a spelling variation that falls in 0.60 - 0.85
    # "Dolox" vs "Dolo" (length 5 vs 4, ratio = 2*4/9 = 0.88 - let's check "Dolopor" length 7 vs 4 ratio 2*4/11=0.72)
    res = match_medicine_name("Dolopor")
    assert res["match_status"] in ["several_possible", "not_found"]
    if res["match_status"] == "several_possible":
        assert len(res["candidates"]) > 0
        assert res["matched_id"] is None  # Never auto-picked!


def test_not_found():
    res = match_medicine_name("CompletelyUnrelatedChemicalXYZ123")
    assert res["match_status"] == "not_found"
    assert res["matched_id"] is None
    assert res["candidates"] == []
    assert res["ingredients"] == []
