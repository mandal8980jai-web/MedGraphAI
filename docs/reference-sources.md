# Reference Sources & Grounding Policy

MediGraph AI adheres to strict data provenance rules to ensure traceability and prevent fabricated drug claims.

---

## 1. Local Reference Catalog & Rules

The system loads transparent local JSON files located in `backend/app/data/`:

1. **Medicine Catalog (`medicine_catalog.example.json`)**:
   - Contains sample brand names, aliases, and active chemical ingredients (e.g., Dolo 650 & Crocin &rarr; Paracetamol; Brufen &rarr; Ibuprofen; Ecosprin &rarr; Aspirin; Warfarin &rarr; Warfarin).
   - Serves as the demonstration baseline for fuzzy matching and active ingredient mapping.

2. **Interaction Rules (`interaction_rules.example.json`)**:
   - Contains verified pairwise active-ingredient interaction rules, severity classifications (`high`, `moderate`, `low`), concise clinical descriptions, and attribution labels.
   - Example rules:
     - `warfarin` + `aspirin` &rarr; High severity (May raise chance of severe bleeding).
     - `warfarin` + `ibuprofen` &rarr; High severity (Increased gastrointestinal bleeding risk).
     - `aspirin` + `ibuprofen` &rarr; Moderate severity (Decreased cardioprotective effect of aspirin).
     - `simvastatin` + `clarithromycin` &rarr; High severity (Significantly increased risk of myopathy and rhabdomyolysis).
   - Notice: Every interaction card and report includes the source attribution: *"Sample demo rule, verify with a pharmacist"*.

---

## 2. Web Grounding via Google Search

For dynamic evidence research and clinical indications:
- The **Pharmacist Research Agent** and **Alternative Research Agent** utilize Gemini's built-in **Google Search tool grounding**.
- Real external web citations (`title` and `url`) are extracted directly from the response's grounding metadata.
- If no grounding metadata is returned, the finding is marked with status `no_source` and displayed as *"No external source found"*.
- The system never fabricates or invents citation links.
