# Safety Policies and System Limitations

> **CRITICAL MEDICAL NOTICE:** MediGraph AI is an experimental decision-support and educational prototype. It is NOT a medical device, diagnostic system, or clinical treatment directive. It is designed to assist clinicians and patients with transparent information review. Always consult a licensed physician or pharmacist before starting, stopping, or altering any medication.

---

## 1. Core Safety Rules & Invariants

1. **No Prescriptive Advice**:
   - The system must **never** advise a user to start, stop, skip, replace, switch, increase, or decrease medications or dosages.
   - Any LLM output attempting to give prescriptive instructions is intercepted by the deterministic safety gate and replaced with:  
     `"[Removed by safety check. Please ask your doctor or pharmacist.]"`

2. **No Absolute Safety Claims**:
   - The system must **never** describe any medicine, combination, or alternative as "risk-free", "completely safe", "guaranteed safe", or having "no side effects".
   - If no interaction is found in the sample database, the system explicitly reports:  
     *"Only the medicines and rules in our sample list were checked. A missing warning does not mean there is no interaction."*

3. **Unknown Medicines Are Never Labeled Safe**:
   - Medicines not found in the demonstration catalog are labeled *"Not checked: not in our list"*.
   - They are explicitly highlighted to ensure clinicians understand they have not been verified against interaction rules.

4. **Alternatives Are For Clinical Discussion Only**:
   - Alternative medications are always presented as *"options to discuss with your doctor"*.
   - If required patient context (age, diagnosis reason, allergies, pregnancy status, kidney/liver conditions) is incomplete, the system refuses to suggest alternatives and requests the missing fields.

5. **Immediate Emergency Interception**:
   - Patient chat inputs indicating severe emergencies (e.g., chest pain, trouble breathing, throat swelling, anaphylaxis, overdose, unconsciousness, heavy bleeding, self-harm) bypass the AI model immediately and return:  
     *"This could be an emergency. Please call your local emergency number or go to the nearest hospital now."*

---

## 2. Inherent System Limitations

- **Prototype Reference Data**: The local medicine catalog (`medicine_catalog.example.json`) and interaction rules (`interaction_rules.example.json`) are curated sample demo datasets. They do not constitute a complete pharmacopeia.
- **OCR Uncertainty**: OCR technology can misread handwriting, dosages, abbreviations, or degraded scans. High visual confidence does not guarantee clinical accuracy. User confirmation is mandatory.
- **AI Hallucination Mitigation**: Evidence findings are grounded using Google Search through the Gemini API. If external web citations are not returned, findings are explicitly flagged as *"No source found"* or marked *"Evidence unavailable"*.
- **Privacy & Retention**: Medical prescriptions uploaded for review are stored locally and automatically purged after `RETENTION_DAYS` (7 days), or when manually deleted by the user. Raw prescription text is never logged.
