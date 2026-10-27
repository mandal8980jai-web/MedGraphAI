# MediGraph AI: Implementation Guide

**For:** Antigravity IDE (AI coding agent)
**Read first:** `README.md` (project rules and safety policy). This file turns the README into build steps. If the two ever disagree, the README's safety rules win.

---

## 0. How to work

1. Build **one phase at a time**, in order. After each phase, run its "Done when" checks. Do not start the next phase until they pass.
2. Build **only what is listed here and in the README**. No login, no LangGraph, no WebSockets, no OpenCV, no extra pages, no extra libraries beyond section 3.
3. Library APIs change. Before using `google-genai`, `rapidocr-onnxruntime`, `@xyflow/react`, or Tailwind, check the **installed version's** docs and use what actually works.
4. Use **plain words** everywhere a user can see them (see section 12). Use simple names in code too.
5. Never put the API key in the frontend, in source code, in logs, or in Git.

## 1. The one rule that matters most

> The user adds **one value**: `LLM_API_KEY` (a Gemini key) in `backend/.env`.
> After install and two start commands, **every feature must work**. No other key, no extra program (no Tesseract, no Poppler), no database server.

## 2. Fixed decisions (do not change)

| Topic | Decision |
|---|---|
| LLM | Gemini through the `google-genai` Python SDK. Model name read from `LLM_MODEL`. |
| Evidence and links | Gemini's built-in **Google Search tool**. Links come from the tool's **grounding data**, never from text the model writes. |
| PDF text | PyMuPDF |
| OCR | `rapidocr-onnxruntime` (pip only, runs locally). Used for images and scanned PDFs. |
| Medicine name matching | Python `difflib` (no extra library) |
| Database | SQLite through Python's built-in `sqlite3` |
| Live progress | Server-Sent Events (SSE). The server reads new events from the database every 0.5 s. |
| Report | ReportLab |
| `.env` location | `backend/.env` only, copied from `backend/.env.example`. Do **not** create a root `.env.example`. |
| Python | 3.11 |

## 3. Dependencies (nothing else)

**Backend (`backend/pyproject.toml`):**
`fastapi`, `uvicorn[standard]`, `python-multipart`, `pydantic`, `pydantic-settings`, `google-genai`, `pymupdf`, `rapidocr-onnxruntime`, `pillow`, `networkx`, `reportlab`.
Dev only: `pytest`, `httpx`.

**Frontend (`frontend/package.json`):**
`react`, `react-dom`, `react-router-dom`, `@xyflow/react`, `lucide-react` (icons), `tailwindcss` (with its Vite or PostCSS setup), `typescript`, `vite`.

## 4. Environment file

`backend/.env.example` (placeholders only):

```dotenv
# The only value the user must fill in
LLM_API_KEY=put_your_gemini_key_here

# Gemini model name. Check Google AI Studio for a current one.
LLM_MODEL=gemini-2.5-flash

APP_ENV=development
DATABASE_URL=sqlite:///./medigraph.db
UPLOAD_DIR=../storage/uploads
REPORT_DIR=../storage/reports
MAX_UPLOAD_MB=15
RETENTION_DAYS=7
FRONTEND_ORIGIN=http://localhost:5173
LOG_LEVEL=INFO
```

- `core/config.py` loads these with `pydantic-settings`.
- If `LLM_API_KEY` is empty or still the placeholder, the backend must still start. `/health` returns `llm_key_set: false`, and the frontend shows a clear banner: "Add your Gemini key to backend/.env and restart the backend."
- Frontend reads `VITE_API_URL` (default `http://localhost:8000`). It is not a secret.
- `.gitignore` must cover: `.env`, `*.db`, `.venv/`, `node_modules/`, `storage/uploads/*`, `storage/reports/*` (keep the `.gitkeep` files), `__pycache__/`, `dist/`.

## 5. Folder structure

Use exactly the README's tree. Additions allowed (all small, all required by the README):

- `backend/app/services/safety_gate.py` (safety wording checks)
- `backend/app/services/gemini_client.py` (the single adapter for all Gemini calls)
- `backend/scripts/make_sample_prescription.py` (makes a fake prescription for demos and tests)
- `backend/app/data/` holds `medicine_catalog.example.json` and `interaction_rules.example.json`. The code loads these files directly. Do not duplicate them.
- `docs/architecture.md`, `docs/safety-and-limitations.md`, `docs/reference-sources.md`: short, plain-language, written in Phase 6.

## 6. Data and shapes

### 6.1 Database tables (create on startup if missing)

```sql
analyses(
  id TEXT PRIMARY KEY,            -- uuid
  created_at TEXT,                -- ISO time, UTC
  original_name TEXT,
  stored_name TEXT,               -- safe internal name
  file_kind TEXT,                 -- 'image' or 'pdf'
  text_source TEXT,               -- 'pdf_text' or 'ocr'
  page_count INTEGER,
  extracted_text TEXT,            -- never written to logs
  medicines_json TEXT,            -- list of Medicine (6.2)
  context_json TEXT,              -- PatientContext (6.3)
  results_json TEXT,              -- final Results (6.5)
  status TEXT                     -- 'uploaded','confirmed','running','done','failed'
)

events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  analysis_id TEXT,
  run_id TEXT,
  time TEXT,
  component TEXT,                 -- e.g. 'Reader', 'Safety Checker', 'Evidence Helper'
  status TEXT,                    -- 'waiting','running','done','failed','skipped'
  task TEXT,                      -- short plain sentence
  detail TEXT                     -- safe short summary. No raw prescription text. No keys.
)
```

### 6.2 Medicine (one row in the confirm table)

```json
{
  "id": "m1",
  "name_text": "Dolo 650",
  "strength": "650 mg",
  "dose": "1 tablet",
  "frequency": "twice a day",
  "duration": "5 days",
  "page": 1,
  "read_quality": "clear",          // 'clear' or 'unclear' (the model's own report)
  "match_status": "matched",        // 'matched', 'several_possible', 'not_found'
  "matched_id": "paracetamol_dolo",
  "candidates": ["..."],
  "ingredients": ["paracetamol"],
  "confirmed": false
}
```

Rules: fill a field **only if it is visible** in the text. Otherwise use `null`. Never guess.

### 6.3 PatientContext (all optional in the form)

`age`, `reason` (why the medicine was prescribed), `allergies`, `pregnancy` (`yes` / `no` / `not_applicable`), `kidney_liver`.

### 6.4 Catalog and rule files

`medicine_catalog.example.json`:
```json
{ "note": "Sample list for demo. Not complete. Check with a pharmacist.",
  "medicines": [ { "id": "paracetamol_dolo", "names": ["Dolo 650", "Dolo", "Paracetamol 650"], "ingredients": ["paracetamol"] } ] }
```

`interaction_rules.example.json`:
```json
{ "note": "Sample rules for demo. Not complete. Check with a pharmacist.",
  "rules": [ { "id": "r1", "ingredients": ["warfarin", "aspirin"], "severity": "high",
               "note": "May raise the chance of bleeding.", "source_label": "Sample demo rule" } ] }
```

Include at least these so the demo works: Dolo 650 and Crocin (paracetamol), Brufen (ibuprofen), Ecosprin (aspirin), Glycomet (metformin), Atorva (atorvastatin), Mox (amoxicillin), plus warfarin and clarithromycin and simvastatin. Rules to include: warfarin + aspirin, warfarin + ibuprofen, aspirin + ibuprofen, simvastatin + clarithromycin. Keep every note short and general. Put "Sample demo rule, verify with a pharmacist" in `source_label`. Do not add detail you are not sure is correct.

### 6.5 Results

```json
{
  "interactions": [ { "rule_id": "r1", "medicines": ["m1","m2"], "severity": "high", "note": "...", "source_label": "..." } ],
  "duplicates":   [ { "ingredient": "paracetamol", "medicines": ["m1","m3"] } ],
  "coverage":     { "total": 4, "found_in_list": 3, "not_found": ["m4"] },
  "evidence":     [ { "medicine_id": "m1", "findings": ["..."], "sources": [ { "title": "...", "url": "..." } ], "status": "ok" } ],
  "alternatives": { "status": "ok | needs_more_info | unavailable", "missing": ["age"], "items": [ { "for_medicine_id": "m1", "options": ["..."], "sources": [] } ] },
  "review":       { "issues": [ { "where": "evidence m1", "issue": "No source found" } ] },
  "graph":        { "nodes": [ { "id": "m1", "label": "Dolo 650", "type": "medicine" } ], "edges": [ { "from": "m1", "to": "paracetamol", "type": "contains" } ] },
  "flags":        [ "Removed by safety check: evidence m2" ]
}
```

Evidence `status` is `ok`, `no_source` (model answered but no links came back), or `unavailable` (call failed). Show the right plain message for each. Never show a finding as sourced when `sources` is empty.

## 7. API endpoints

All under the FastAPI app. Enable CORS only for `FRONTEND_ORIGIN`. Return errors as `{ "error": "plain sentence" }`.

| Method and path | Purpose |
|---|---|
| `GET /health` | `{ status, llm_key_set }` |
| `POST /api/documents` | Upload (multipart `file`). Validates, reads text, extracts medicines, matches them. Returns the new analysis (id, text_source, page_count, medicines). |
| `GET /api/analyses` | List for the History page (id, created_at, original_name, status) |
| `GET /api/analyses/{id}` | Full analysis, including results |
| `GET /api/analyses/{id}/file` | The original image or PDF (for side-by-side checking) |
| `PUT /api/analyses/{id}/medicines` | Save the user's corrected and confirmed list plus PatientContext. Re-runs matching on edited names. |
| `POST /api/analyses/{id}/run` | Start the analysis in the background. Returns `{ run_id }`. Refuse if any medicine is not confirmed. |
| `GET /api/analyses/{id}/events` | SSE stream of events for the latest run. Closes when the run ends. |
| `POST /api/chat` | `{ analysis_id, message, history }` returns `{ reply, flags }`. `history` is the last 10 messages, kept in the browser only. |
| `GET /api/analyses/{id}/report` | Builds and returns the PDF |
| `DELETE /api/analyses/{id}` | Deletes database rows, the uploaded file, and the report |

On startup, delete analyses (and their files) older than `RETENTION_DAYS`.

## 8. Phase plan

### Phase 1: Foundation

Tasks
- Create all folders and manifests. Add `.gitignore` and `backend/.env.example`.
- `core/config.py`, `core/logging.py` (never log keys, file contents, or extracted text), `db/database.py` (create tables).
- `GET /health`, CORS.
- Frontend shell: Vite + React + TypeScript + Tailwind, router with `/` (Dashboard) and `/history`, top bar with app name, nav links, **theme toggle**, and a "Backend connected" status dot that calls `/health`.
- Theme: class-based dark mode. Add an inline script in `index.html` that sets the `dark` class before first paint (follow the system on first visit, then use the saved choice from `localStorage` key `theme`). For Tailwind v4 use `@custom-variant dark (&:where(.dark, .dark *));`.
- Missing-key banner (section 4).

Done when
- Both servers start with the documented commands.
- Page shows "Backend connected". Toggle switches light and dark, and the choice survives a refresh with no flash.

### Phase 2: Read the document

Tasks
- `document_service.py`: allow only `.png .jpg .jpeg .webp .pdf`. Check size against `MAX_UPLOAD_MB`. Check the **real file bytes** (PNG `89 50 4E 47`, JPEG `FF D8 FF`, WebP `RIFF....WEBP`, PDF `%PDF`). For images, also open with Pillow and call `verify()`. Save as `<uuid>.<ext>` inside `UPLOAD_DIR`. Never use the user's file name for a path.
- `pdf_text_service.py`: PyMuPDF text per page, keeping the page number. If the average is under about 20 characters per page, treat it as scanned.
- `ocr_service.py`: the **only** file that imports RapidOCR. Images go straight to OCR. Scanned PDF pages are drawn to images with PyMuPDF (about 200 dpi) and then OCR'd. Limit to 10 pages. Keep the page number with the text. Do not fill in missing characters.
- `gemini_client.py`: one function for "give me JSON" (no tools, JSON output with a schema) and one for "research with Google Search" (see Phase 4). Both: timeout (about 60 s), 2 retries with a short wait, and clear errors with no secrets in them.
- Medicine extraction (in `document_service.py` or a small helper): send the extracted text to Gemini and ask for a list of Medicine objects (6.2). Prompt rules: only what is visible; use `null` when missing; mark `read_quality: "unclear"` when the text looks broken; do not correct spelling by guessing.
- `medicine_matcher.py`: lower-case the name, remove strength numbers and punctuation, then compare to catalog names. Close match above 0.85 = `matched`. Between 0.6 and 0.85 = `several_possible` with up to 3 candidates. Below that = `not_found`. Never auto-pick from `several_possible`.
- Upload route and the analyses routes it needs.
- Frontend **Upload step**: drag and drop zone plus a button, file type and size hints, preview, a spinner with plain text ("Reading your document..."), and error messages from the backend.
- Frontend **Confirm step**: original image or PDF on one side, editable table on the other (every field editable, add and remove rows). Rows with `unclear`, `several_possible`, or `not_found` get an amber "Please check" tag, and the user must pick a candidate or edit the name, then tick "I checked this row". The **Continue** button stays disabled until every row is confirmed. Below the table, the optional patient details form (6.3) with a note explaining why each item matters.

Done when
- A sample PNG and a sample PDF both give a medicine table.
- A scanned PDF uses OCR. A digital PDF does not.
- A `.txt` file renamed to `.png` is rejected. An oversized file is rejected.
- Continue stays disabled until all rows are confirmed.

### Phase 3: Safety checks and medicine map

Tasks
- `interaction_engine.py`: after confirmation, collect ingredients per medicine (from the catalog). For every pair, look for a rule. Also find ingredients that appear in two or more medicines (duplicates). Return the structures from 6.5, plus the `coverage` numbers.
- `knowledge_graph.py`: build a NetworkX graph: medicine nodes, ingredient nodes, `contains` edges, and `interacts` edges (with severity). Convert it to the plain nodes and edges lists in 6.5 for the frontend.
- Always include in the result a plain statement: "Only the medicines and rules in our sample list were checked. A missing warning does not mean there is no interaction."
- Medicines not in the list are shown as "Not checked: not in our list". They are never called safe.

Done when
- Warfarin + aspirin gives a high-severity item. Dolo 650 + Crocin gives a duplicate-ingredient item.
- An unknown medicine appears under "Not checked".
- Unit tests for matcher and engine pass (Phase 6 names).

### Phase 4: Helpers and the Manager

**Safety gate first (`safety_gate.py`)**, plain code, no LLM:
- `check_text(text)` returns the text, or a replaced version, plus a flag. It blocks (case-insensitive) phrases that tell the user to start, stop, skip, replace, switch, increase, or decrease a medicine or dose, and phrases such as "risk-free", "completely safe", "guaranteed safe", "no side effects". Blocked text is replaced with: "[Removed by safety check. Please ask your doctor or pharmacist.]" and a flag is added to `results.flags`.
- `is_emergency(text)` returns true for common emergency wording in the chat (for example chest pain, trouble breathing, severe allergic reaction, swelling of the face or throat, overdose, unconsciousness, heavy bleeding, thoughts of self-harm). If true, skip the LLM and reply with: "This could be an emergency. Please call your local emergency number or go to the nearest hospital now."
- Every piece of LLM text, in every helper and in chat, passes through `check_text` before it is saved or returned.

**Helpers (`app/agents/`)**, each a small file with a prompt and one function:

| Helper (file) | Job | Gemini call |
|---|---|---|
| Chat Helper (`conversation_agent.py`) | Answers questions about the confirmed medicines and the results. Explains the steps in plain words. Asks for missing patient details. Sees the confirmed list and a short summary of results, **not** the raw prescription text. | JSON/text, no search |
| Evidence Helper (`pharmacist_research_agent.py`) | One call **per medicine**: what it is used for, common cautions, and known interactions with the other medicines on the list. Uses only search results. If nothing is found, says so. | Google Search tool |
| Alternatives Helper (`alternative_research_agent.py`) | One call per medicine, **only if** age, reason, allergies, pregnancy, and kidney/liver details are all filled in. Otherwise set `status: "needs_more_info"` with the `missing` list and **do not call Gemini**. Output is "options to discuss with your doctor", never advice to switch. | Google Search tool |
| Safety Reviewer (`safety_critic_agent.py`) | Code first: flag any finding with no sources, any blocked phrase, any medicine not checked. Then one optional Gemini call that reads the structured results and lists claims that look unsupported or contradictory. | JSON, no search |
| Manager (`coordinator.py`) | Plain Python (not an LLM). Runs the steps below, writes an event for each status change, handles failures, saves results. | none |

**Google Search calls:** Gemini cannot always return forced-JSON and use the search tool in the same call. So for the two research helpers: ask for JSON in the prompt, parse the text carefully (strip code fences, handle bad JSON by retrying once, then mark `unavailable`). Get `sources` from the response's **grounding metadata** (web title and url), not from model text. If the grounding list is empty, set `status: "no_source"`. Check the installed SDK docs for the exact field names.

**Order of work (`workflows/analysis_workflow.py`):**
1. Safety Checker (interaction engine and map) runs first.
2. Evidence Helper and Alternatives Helper run **in parallel** (use `asyncio.to_thread` around the SDK calls, and allow at most 3 Gemini calls at the same time to respect rate limits).
3. Safety Reviewer runs last.
4. The Manager saves `results_json`, sets status to `done`, or `failed` with a plain error.

If one helper fails, the others still finish. The failed part shows as "Unavailable" with a plain reason (for example "Gemini did not answer in time"). Rate-limit errors must say so.

**Events:** for each step the Manager writes `waiting` → `running` → `done` or `failed` to the `events` table. Fields follow the table in 6.1. `detail` is a short safe sentence such as "3 medicines checked, 1 warning". Never put prescription text or keys in an event. The events endpoint reads new rows every 0.5 s and sends them as SSE.

Done when
- With a valid key, a full run on the sample prescription finishes and fills every results tab.
- With no key, the run fails fast with the plain message and nothing crashes.
- Events appear in the UI as they happen.
- A reply containing "you should stop taking" is replaced by the safety message in tests.

### Phase 5: Dashboard and report

**Dashboard** is one page with a 4-step progress bar: **1 Upload → 2 Confirm → 3 Analysis → 4 Results**. Users can go back to earlier steps.

- **Analysis step:** left side is the **Helper panel**: a list of the helpers, each with a status badge (Waiting, Working, Done, Failed), a short task sentence, and a time; click a row to see its detail text. Right side is the **Medicine map** (React Flow): medicine nodes, ingredient nodes, edges coloured by type, red for high-severity interactions, zoom and drag enabled, and a small legend. When a run starts, nodes and statuses update from real events only. No fake animation.
- **Results step** has tabs:
  - **Medicines:** the confirmed table and the match status.
  - **Interactions:** cards with severity colour, plain note, and the coverage notice. Duplicates and "Not checked" items are listed here too.
  - **Evidence:** one expandable card per medicine, with findings and source links (open in a new tab). Show "Evidence not available" or "No source found" when that is the status.
  - **Alternatives:** options to discuss with a doctor. If details are missing, show which ones, with a button that goes back to the details form.
  - **Chat:** message box, history in browser state, quick-question buttons (for example "Explain these results simply"), and a typing indicator.
  - Top of Results: **Download PDF report** button, and the permanent safety notice.
- **History page:** a list of past analyses (name, date, status). Open one to view its results again. Delete button with a confirm dialog.

**Look and feel (professional):**
- Light and dark palettes using Tailwind colours. Calm blue or teal as the main colour, amber for "please check", red for high risk, green for done. Text contrast must be readable in both themes.
- Rounded cards, steady spacing, one font family, clear headings.
- Hover and focus states, disabled-button styles, loading skeletons or spinners, toast messages for errors, an empty state on History.
- Works on a laptop and on a phone-width screen (stack the panels).
- Keyboard accessible: labels on inputs, visible focus ring, `aria-label` on icon buttons.

**Report (`report_service.py`, ReportLab):** title and date; the safety notice; confirmed medicines; interaction findings; duplicates; not-checked medicines; evidence with source links; alternatives (or what is missing); reviewer notes and flags; limits ("sample list, not complete, not medical advice"); and "Please review this report with a doctor or pharmacist." Save to `REPORT_DIR` and return it.

Done when
- All four steps work end to end in both themes.
- The PDF opens and has every section above.
- Deleting an analysis removes its upload and report files.

### Phase 6: Tests, sample data, docs

- `backend/scripts/make_sample_prescription.py`: uses Pillow and ReportLab to make a **fake** prescription as PNG and as PDF. It lists: Dolo 650, Crocin (duplicate paracetamol), Ecosprin, a warfarin line, and one made-up name that is not in the catalog. Also make one blurry copy of the PNG and one scanned-style PDF (an image placed inside a PDF).
- `backend/tests/` with the README's files:
  - `test_upload_validation.py`: wrong extension, wrong real type, oversize, path-like names, good PNG/JPG/WebP/PDF.
  - `test_ocr_pipeline.py`: digital PDF uses text, scanned PDF uses OCR, empty file handled.
  - `test_medicine_matching.py`: exact, close, several-possible, not-found, strength stripped.
  - `test_interaction_engine.py`: known pair, duplicate ingredient, unknown medicine, coverage numbers.
  - `test_safety_gates.py`: blocked phrases, "risk-free", emergency wording, normal text passes.
  - Gemini calls are **mocked** in tests. Tests must pass with no key.
- Write the three `docs/` files in plain language: how it is built, safety and limits, and which sources are used (Google Search through Gemini; the sample list and rules, which are not complete).
- Update the root `README.md` section 6 with the real commands and the real endpoint paths from section 7.
- Run `npm run build` and `pytest` and fix every error.

## 9. Safety rules (always on)

- Never tell the user to start, stop, skip, switch, or change the dose of any medicine.
- Never say anything is "safe" or "risk-free". Say "no warning found in our sample list" instead.
- Alternatives are always labelled "to discuss with your doctor".
- Do not invent sources, facts, or interactions. No source means the screen says so.
- Do not treat OCR confidence as medical confidence. Do not show OCR scores as if they mean the result is correct.
- The safety notice from the README is visible on every page and in the PDF.
- Prototype only: not production ready, not clinically checked.

## 10. Security and privacy checklist

- Key only in `backend/.env`, read by the backend. Not in the frontend, source, logs, events, or Git.
- File checks use real bytes, not names. Safe generated file names. No path traversal.
- No raw prescription text in logs or events.
- Retention: manual delete plus automatic cleanup after `RETENTION_DAYS`.
- Demo and test files are fake only.

## 11. Final checklist (definition of done)

- [ ] Fresh clone + install + `LLM_API_KEY` in `.env` + two start commands = everything works.
- [ ] Image upload, PDF upload, and scanned PDF upload all work.
- [ ] No row can be analysed until the user confirms it.
- [ ] Interactions and duplicates show for the sample prescription. Coverage notice is visible.
- [ ] Evidence shows real links, or says clearly that none were found.
- [ ] Helper panel shows real events.
- [ ] Chat works and the emergency message works.
- [ ] PDF report downloads and contains every section.
- [ ] Dark and light mode both look good on every screen, and the choice is remembered.
- [ ] `pytest` passes with no key. `npm run build` passes.
- [ ] No secrets or real prescriptions in Git.

## 12. Plain wording for screens

| Do not show | Show instead |
|---|---|
| Deterministic rules | Safety checks |
| Knowledge graph | Medicine map |
| Agent | Helper |
| Coordinator | Manager |
| Uncertainty / low confidence | Please check |
| OCR | Reading the document |
| Grounding / citations | Sources |
| Ingredient overlap | Same ingredient found twice |
| Contraindication | Not suitable in some cases (ask your doctor) |
| Payload, schema, endpoint | (never on screen) |

Write short sentences. Explain every warning in one line a student can understand.

## 13. Start commands (document these in the README)

```powershell
# Terminal 1: backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env      # then paste your Gemini key into LLM_API_KEY
uvicorn app.main:app --reload

# Terminal 2: frontend
cd frontend
npm install
npm run dev
```
