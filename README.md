# MediGraph AI

### OCR-First, Multi-Agent Medication Safety & Evidence Research System

MediGraph AI is an educational clinical decision-support prototype that transforms prescription documents (images and digital/scanned PDFs) into reviewed medication safety summaries. It extracts text locally, assists users with transparent medicine verification, checks deterministic drug-drug interactions and duplicate active ingredients, conducts grounded web research, and generates clinical PDF reports.

> **Important Medical Safety Notice:** MediGraph AI is an experimental decision-support prototype, not a certified medical device or a substitute for a licensed physician or pharmacist. Users must confirm all extracted medicines. The system never gives prescriptive instructions to start, stop, replace, or alter medicine doses. Alternative medications are educational topics for clinician review only. Never describe any medicine as "risk-free" or guaranteed safe.

---

## 1. The One Rule That Matters Most

The user configures **one value**: `LLM_API_KEY` (a Google Gemini API key) in `backend/.env`.

After installing dependencies and starting both servers, every feature works:
- No extra API keys.
- No external binary installs (no Tesseract, no Poppler).
- No external database server (runs on Python's built-in SQLite).
- If the Gemini key is not configured, the backend starts safely, reports `llm_key_set: false` at `/health`, and displays a clear setup banner in the UI.

---

## 2. Technology Stack & Dependencies

| Layer | Technology & Purpose |
|---|---|
| **Frontend** | React 18, Vite 5, TypeScript |
| **Styling** | Tailwind CSS with system/persisted dark mode |
| **Medicine Map** | `@xyflow/react` (React Flow) for interactive graph visualization |
| **Icons** | `lucide-react` |
| **Backend API** | Python 3.11, FastAPI, Uvicorn |
| **LLM Provider** | Single Gemini key via `google-genai` Python SDK (`LLM_MODEL`) |
| **Web Grounding** | Gemini Google Search tool (grounded citations only) |
| **PDF Extraction** | PyMuPDF (`fitz`) |
| **Local OCR** | `rapidocr-onnxruntime` (runs locally for images and scanned PDFs) |
| **Medicine Matching** | Python built-in `difflib` similarity matching |
| **Knowledge Graph** | NetworkX |
| **Local Database** | SQLite via Python's built-in `sqlite3` |
| **Live Progress** | Server-Sent Events (SSE) reading new database events every 0.5s |
| **PDF Report** | ReportLab |

---

## 3. Project Structure

```text
medigraph-ai/
├── README.md
├── IMPLEMENTATION.md
├── .gitignore
├── docs/
│   ├── architecture.md
│   ├── safety-and-limitations.md
│   └── reference-sources.md
├── storage/
│   ├── uploads/               # Uploaded prescription documents
│   ├── reports/               # Generated ReportLab PDF reports
│   └── sample_prescriptions/  # Synthetic demo test documents
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── SafetyNotice.tsx
│   │   │   ├── MissingKeyBanner.tsx
│   │   │   ├── upload/UploadZone.tsx
│   │   │   ├── confirm/ConfirmStep.tsx
│   │   │   ├── agent-panel/HelperPanel.tsx
│   │   │   ├── knowledge-graph/MedicineMap.tsx
│   │   │   ├── results/ResultsStep.tsx
│   │   │   └── chat/ChatPanel.tsx
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx
│   │   │   └── HistoryPage.tsx
│   │   ├── services/api.ts
│   │   └── types/index.ts
└── backend/
    ├── pyproject.toml
    ├── .env.example
    ├── app/
    │   ├── main.py
    │   ├── core/config.py, logging.py, security.py
    │   ├── db/database.py, repositories.py
    │   ├── schemas/analysis.py
    │   ├── api/routes/
    │   │   ├── health.py
    │   │   ├── documents.py
    │   │   ├── analyses.py
    │   │   └── chat.py
    │   ├── services/
    │   │   ├── document_service.py
    │   │   ├── pdf_text_service.py
    │   │   ├── ocr_service.py
    │   │   ├── medicine_matcher.py
    │   │   ├── interaction_engine.py
    │   │   ├── knowledge_graph.py
    │   │   ├── safety_gate.py
    │   │   ├── gemini_client.py
    │   │   └── report_service.py
    │   ├── agents/
    │   │   ├── coordinator.py
    │   │   ├── pharmacist_research_agent.py
    │   │   ├── alternative_research_agent.py
    │   │   ├── safety_critic_agent.py
    │   │   └── conversation_agent.py
    │   ├── workflows/analysis_workflow.py
    │   └── data/
    │       ├── medicine_catalog.example.json
    │       └── interaction_rules.example.json
    ├── scripts/
    │   └── make_sample_prescription.py
    └── tests/
        ├── test_foundation.py
        ├── test_upload_validation.py
        ├── test_ocr_pipeline.py
        ├── test_medicine_matching.py
        ├── test_interaction_engine.py
        ├── test_agent_workflow.py
        ├── test_safety_gates.py
        └── test_reports_and_history.py
```

---

## 4. Setup & Running Locally (Windows PowerShell)

### Terminal 1: Backend Setup & Launch

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .

# Copy environment template and add your Gemini key
copy .env.example .env
# Edit backend/.env and paste your Gemini key into LLM_API_KEY

# Start backend server
uvicorn app.main:app --reload
```

Backend will be active at: `http://localhost:8000` (API docs at `http://localhost:8000/docs`).

### Terminal 2: Frontend Setup & Launch

```powershell
cd frontend
npm install
npm run dev
```

Frontend will be active at: `http://localhost:5173`.

---

## 5. API Endpoints

All routes return errors in plain language: `{ "error": "Clear explanation" }`.

| Method & Path | Purpose |
|---|---|
| `GET /health` | Health check returning `{ status: "ok", llm_key_set: bool, model: str }` |
| `POST /api/documents` | Multipart document upload (PNG/JPG/WebP/PDF). Validates magic bytes, extracts text via PyMuPDF or local RapidOCR, matches medicines against catalog. |
| `GET /api/analyses` | Lists past analyses for the History page. |
| `GET /api/analyses/{id}` | Retrieves full analysis record, including confirmed medicines and safety results. |
| `GET /api/analyses/{id}/file` | Retrieves original uploaded image/PDF for side-by-side verification. |
| `PUT /api/analyses/{id}/medicines` | Saves user-confirmed medicine corrections and patient clinical context; re-runs matching and deterministic checks. |
| `POST /api/analyses/{id}/run` | Starts multi-agent background research workflow. Refuses if any medicine is unconfirmed. |
| `GET /api/analyses/{id}/events` | Server-Sent Events (SSE) live event stream for the active analysis run. |
| `POST /api/chat` | Patient educational assistant answering questions with safety checks and emergency interception. |
| `GET /api/analyses/{id}/report` | Builds and returns the comprehensive ReportLab PDF clinical report. |
| `DELETE /api/analyses/{id}` | Permanently deletes analysis database rows, uploaded file, and generated report. |

---

## 6. Synthetic Demo Prescriptions

To generate synthetic test documents without using real patient data:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts/make_sample_prescription.py
```

This generates 4 synthetic documents in `storage/sample_prescriptions/`:
1. `sample_prescription.png`: Clean synthetic prescription image.
2. `sample_prescription_blurry.png`: Blurred synthetic prescription testing OCR resilience.
3. `sample_prescription_digital.pdf`: Digital text PDF with embedded selectable characters.
4. `sample_prescription_scanned.pdf`: Raster image inside a PDF triggering the local OCR fallback.

All synthetic documents contain Dolo 650, Crocin (duplicate paracetamol), Ecosprin, Warfarin, and an uncatalogued medicine (Zylocran 50mg).

---

## 7. Running the Automated Test Suite

All tests pass without an active Gemini API key:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -v
```

To build and validate the frontend:

```powershell
cd frontend
npm run build
```

---

---

## 8. Production Deployment Guide (Render + Vercel)

This application is decoupled into an independent **FastAPI backend** (deployed to [Render](https://render.com)) and a **React/Vite frontend** (deployed to [Vercel](https://vercel.com)).

### Deployment Architecture

```text
[ User Browser ]
       │
       ▼ (HTTPS)
[ Vercel CDN ] ─── React / Vite SPA (frontend/)
       │
       ▼ (REST API / SSE via VITE_API_URL)
[ Render Web Service ] ─── FastAPI / Python 3.11 (backend/)
       │
       ├── Google Gemini API (LLM_API_KEY)
       ├── PyMuPDF & RapidOCR (Local ONNX OCR)
       └── SQLite & File Storage (Local or Persistent Disk)
```

---

### Step 1: Deploy Backend to Render

1. Log in to your [Render Dashboard](https://dashboard.render.com/) and click **New + > Web Service**.
2. Connect your GitHub repository: `https://github.com/mandal8980jai-web/MedGraphAI.git`.
3. Configure the service with these **exact settings**:
   - **Name**: `medigraph-backend` (or your preferred name)
   - **Region**: Choose the region closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend` *(CRITICAL: must be set to `backend`)*
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free (or Starter if you want persistent disk)
4. Under **Advanced Settings**:
   - **Health Check Path**: `/health`
5. Under **Environment Variables**, add:
   | Key | Value | Description |
   |---|---|---|
   | `LLM_API_KEY` | `your_gemini_api_key` | Your secret Google Gemini API key |
   | `LLM_MODEL` | `gemini-3.5-flash-lite` | Recommended model |
   | `APP_ENV` | `production` | Production mode |
   | `PYTHON_VERSION` | `3.11.9` | Matches tested runtime |
   | `CORS_ORIGIN_REGEX` | `https://.*\.vercel\.app` | Permits all Vercel production & preview URLs |
   | `FRONTEND_ORIGIN` | `https://localhost:5173` | Set initially; update with your real Vercel URL in Step 3 |
6. Click **Create Web Service**. Wait for the build and deployment to finish.
7. Copy your assigned Render URL (e.g. `https://medigraph-backend.onrender.com`).
8. Verify backend health in your browser:
   - Visit: `https://medigraph-backend.onrender.com/health`
   - Expected response: `{"status":"ok","llm_key_set":true,"model":"gemini-3.5-flash-lite"}`

---

### Step 2: Deploy Frontend to Vercel

1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New... > Project**.
2. Import the repository: `mandal8980jai-web/MedGraphAI`.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `frontend` *(CRITICAL)*
   - **Build Command**: `npm run build` (Default)
   - **Output Directory**: `dist` (Default)
   - **Install Command**: `npm install` (Default)
4. In the **Environment Variables** section, add:
   | Key | Value |
   |---|---|
   | `VITE_API_URL` | `https://medigraph-backend.onrender.com` *(use your actual Render backend URL without a trailing slash)* |
5. Click **Deploy**. Vercel will install dependencies, build the TypeScript bundle, and provide a production domain (e.g. `https://medigraph-ai.vercel.app`).
6. Single Page Application (SPA) routing is pre-configured via `frontend/vercel.json`, so page refreshes on `/history` work seamlessly.

---

### Step 3: Connect Frontend URL to Backend CORS

1. Return to your [Render Dashboard](https://dashboard.render.com/) -> `medigraph-backend` -> **Environment**.
2. Update `FRONTEND_ORIGIN` with your live Vercel domain:
   ```text
   FRONTEND_ORIGIN=https://medigraph-ai.vercel.app
   ```
3. Save changes. Render will automatically redeploy with the updated CORS origin.

---

### Step 4: Storage Considerations in Production

- **Free Tier (Default Ephemeral)**:
  - Render's free tier uses an ephemeral filesystem that resets on spin-down or redeploy.
  - The application is architected to handle this gracefully: the SQLite schema (`init_db()`) and storage directories are automatically recreated on startup, so the app functions immediately for all uploads and queries.
- **Paid Tier with Persistent Disk (Optional)**:
  - If you require persistent historical analyses and saved PDF reports across restarts, attach a **Persistent Disk** on Render (e.g. 1 GB mounted at `/var/data`).
  - Add these 3 environment variables in the Render Dashboard:
    ```text
    DATABASE_URL=sqlite:////var/data/medigraph.db
    UPLOAD_DIR=/var/data/storage/uploads
    REPORT_DIR=/var/data/storage/reports
    ```

---

## 9. Retention and Privacy Policy

- Raw prescription text is never written to logs or event streams.
- Uploaded files are stored with random UUID filenames outside the web root.
- Analyses and associated files older than `RETENTION_DAYS` (7 days) are automatically purged on backend startup.
- Users can delete any analysis at any time from the History page.
