import pytest
from app.services.safety_gate import (
    check_text,
    is_emergency,
    SAFETY_REPLACEMENT,
    EMERGENCY_REPLY
)


def test_safety_gate_blocks_prescriptive_stop_advice():
    """Blocked phrase 'you should stop taking' is replaced with safety notice."""
    text = "You should stop taking your medication immediately."
    cleaned, flags = check_text(text)
    assert SAFETY_REPLACEMENT in cleaned
    assert "stop taking" not in cleaned.lower()
    assert len(flags) > 0


def test_safety_gate_blocks_dosage_changes():
    """Blocked phrases directing dose changes (increase/decrease/skip) are replaced."""
    # Test increase dose
    t1 = "Please increase your dose to 1000 mg."
    c1, f1 = check_text(t1)
    assert SAFETY_REPLACEMENT in c1
    assert len(f1) > 0

    # Test decrease dose
    t2 = "You must decrease your dosage by half."
    c2, f2 = check_text(t2)
    assert SAFETY_REPLACEMENT in c2
    assert len(f2) > 0

    # Test skip dose
    t3 = "You should skip your dose if you feel dizzy."
    c3, f3 = check_text(t3)
    assert SAFETY_REPLACEMENT in c3
    assert len(f3) > 0


def test_safety_gate_blocks_absolute_safety_claims():
    """Phrases like 'risk-free', 'completely safe', 'guaranteed safe', 'no side effects' are blocked."""
    t1 = "This medicine is completely safe for everyone."
    c1, f1 = check_text(t1)
    assert SAFETY_REPLACEMENT in c1
    assert "completely safe" not in c1.lower()

    t2 = "The combination is guaranteed safe and risk-free."
    c2, f2 = check_text(t2)
    assert SAFETY_REPLACEMENT in c2
    assert "risk-free" not in c2.lower()
    assert "guaranteed safe" not in c2.lower()

    t3 = "This herbal supplement has no side effects."
    c3, f3 = check_text(t3)
    assert SAFETY_REPLACEMENT in c3
    assert "no side effects" not in c3.lower()


def test_safety_gate_allows_safe_educational_text():
    """Objective factual descriptions pass untouched without flags."""
    safe_text = "Paracetamol is commonly used to relieve mild to moderate pain and reduce fever. Always discuss dosage with a licensed doctor or pharmacist."
    cleaned, flags = check_text(safe_text)
    assert cleaned == safe_text
    assert len(flags) == 0


def test_emergency_detection_clinical_signals():
    """Emergency phrases trigger is_emergency = True."""
    assert is_emergency("I am having severe chest pain right now.") is True
    assert is_emergency("Patient has trouble breathing and throat swelling.") is True
    assert is_emergency("My daughter is having a severe allergic reaction and anaphylaxis.") is True
    assert is_emergency("I think I took an overdose of pills.") is True
    assert is_emergency("Patient is unconscious and unresponsive.") is True
    assert is_emergency("There is heavy bleeding from the wound.") is True
    assert is_emergency("I am having thoughts of self-harm and suicide.") is True


def test_emergency_detection_non_emergency():
    """Normal clinical questions do not trigger emergency status."""
    assert is_emergency("What is Dolo 650 prescribed for?") is False
    assert is_emergency("Can this medicine be taken after meals?") is False
    assert is_emergency("What are common precautions for amoxicillin?") is False
