# MediGraph AI &mdash; System Architecture

MediGraph AI is an OCR-first, multi-agent medication safety and evidence research decision-support prototype. It transforms prescription documents (images and PDFs) into structured, clinician-reviewed medication summaries with deterministic safety checks and grounded web evidence.

---

## 1. High-Level Architecture Overview

The system combines deterministic services (which must never fail or hallucinate) with specialized AI helper agents (which assist with evidence research and patient communication):

```
┌────────────────────────────────────────────────────────┐
│             Frontend (React + Vite + TS)              │
│  Step 1: Upload ─> Step 2: Confirm ─> Step 3: Analysis │
│                        ─> Step 4: Results (Tabs)       │
└───────────────────────────▲────────────────────────────┘
                            │ REST / SSE
┌───────────────────────────▼────────────────────────────┐
│              FastAPI Backend (Python 3.11)             │
├──────────────────────────┬─────────────────────────────┤
│  Deterministic Services  │      Multi-Agent Roles      │
│  - Document Ingestion    │  - Manager (Coordinator)    │
│  - PyMuPDF Text Extractor│  - Safety Checker (Engine)  │
│  - RapidOCR Engine       │  - Evidence Helper (Search) │
│  - Medicine Matcher      │  - Alternatives Helper      │
│  - Interaction Engine    │  - Safety Critic (Reviewer) │
│  - Knowledge Graph       │  - Chat Helper (Education)  │
│  - Safety Gate Filter    │                             │
│  - ReportLab PDF Engine  │                             │
└──────────────────────────┴─────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Storage & Persistence                 │
│  - SQLite (analyses, events)                           │
│  - storage/uploads/ (securely named original files)    │
│  - storage/reports/ (generated PDF clinical reports)   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Four-Step Pipeline

1. **Step 1: Document Upload & Ingestion**
   - Accepts PNG, JPG, JPEG, WebP, and PDF files.
   - Enforces strict real-byte signature checks (e.g., `89 50 4E 47` for PNG, `%PDF` for PDF) and image integrity verification with Pillow. Rejects disguised files (e.g. `.txt` renamed to `.png`).
   - Generates randomized internal UUIDs to prevent directory traversal attacks.

2. **Step 2: Text Extraction & Medicine Confirmation**
   - **Digital PDFs**: Extracts character streams directly with PyMuPDF. If average character count per page is under 20, it is flagged as scanned.
   - **Images & Scanned PDFs**: Rendered to high-resolution bitmaps (200 DPI) and processed locally through `rapidocr-onnxruntime`. No cloud OCR services are used.
   - **Medicine Name Matching**: Extracts candidate drug names and matches them against the transparent demo catalog using Python's `difflib`. Similarity above 0.85 is marked `matched`; 0.60 to 0.85 is marked `several_possible`; below 0.60 is marked `not_found`.
   - **User Confirmation**: The UI presents a side-by-side inspection view. Every row must be explicitly confirmed before downstream analysis can start.

3. **Step 3: Real-Time Analysis & Medicine Map**
   - **Helper Activity Panel**: Streams live backend execution events via Server-Sent Events (SSE). Each event includes status (`waiting`, `running`, `done`, `failed`), task description, timestamp, and safe sanitized detail summaries.
   - **Interactive Medicine Map**: Network graph rendered with `@xyflow/react`. Nodes represent medicines and active ingredients; edges represent composition (`contains`) and interactions (`interacts`), colored by severity (red for high, amber for moderate).

4. **Step 4: Clinical Results & PDF Report**
   - Organized into 5 dedicated tabs:
     - **Medicines**: Confirmed medication list and catalog match status.
     - **Interactions**: Detected drug-drug interactions, duplicate active ingredients, and unchecked medicines with coverage notices.
     - **Evidence**: Grounded research findings with live citations.
     - **Alternatives**: Candidate discussion topics for clinicians.
     - **Chat**: Patient education assistant with strict safety filters and emergency detection.
   - **Download PDF Report**: Builds a structured document using ReportLab for offline clinical review.

---

## 3. Deterministic Safety Boundaries

Safety-critical operations are strictly deterministic and never delegated to an LLM:
- **Interaction Engine**: Cross-references active ingredients against configured clinical rules.
- **Duplicate Ingredient Detection**: Identifies shared active ingredients across multiple prescriptions to prevent accidental overdose.
- **Safety Gate**: Deterministic regex filter blocking prescriptive advice (e.g., "stop taking", "increase dose", "risk-free") and intercepting medical emergencies immediately without LLM involvement.
