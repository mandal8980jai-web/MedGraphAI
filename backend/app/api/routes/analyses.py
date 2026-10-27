import json
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from app.core.config import settings
from app.core.security import get_safe_file_path
from app.db.repositories import (
    get_analysis_by_id,
    list_all_analyses,
    update_medicines_and_context,
    delete_analysis_record,
    get_events_since,
    get_latest_run_id
)
from app.schemas.analysis import AnalysisResponse, AnalysisSummary, UpdateMedicinesRequest
from app.services.medicine_matcher import match_medicine_name
from app.services.interaction_engine import check_interactions
from app.services.knowledge_graph import build_knowledge_graph
from app.services.report_service import generate_pdf_report
from app.agents.coordinator import schedule_analysis_run

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


@router.get("", response_model=List[AnalysisSummary])
def get_analyses() -> List[AnalysisSummary]:
    """List past analyses for the History page."""
    return list_all_analyses()


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str) -> AnalysisResponse:
    """Retrieve full analysis record by ID."""
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": "Analysis not found."})

    # If results are not yet generated but medicines are present, compute safety checks & graph
    if (not analysis.results or "interactions" not in analysis.results) and analysis.medicines:
        interaction_res = check_interactions(analysis.medicines)
        graph_res = build_knowledge_graph(analysis.medicines, interaction_res["interactions"])
        computed_results = {
            "interactions": interaction_res["interactions"],
            "duplicates": interaction_res["duplicates"],
            "coverage": interaction_res["coverage"],
            "graph": graph_res,
            "notice": interaction_res["notice"]
        }
        analysis.results = computed_results

    return analysis


@router.get("/{analysis_id}/file")
def get_analysis_file(analysis_id: str):
    """Retrieve the original uploaded image or PDF file for side-by-side inspection."""
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": "Analysis not found."})

    safe_path = get_safe_file_path(analysis.stored_name)
    if not safe_path.exists():
        raise HTTPException(status_code=404, detail={"error": "Uploaded document file not found on disk."})

    media_type = "application/pdf" if analysis.file_kind == "pdf" else "image/png"
    return FileResponse(path=safe_path, media_type=media_type, filename=analysis.original_name)


@router.put("/{analysis_id}/medicines", response_model=AnalysisResponse)
def update_medicines(analysis_id: str, payload: UpdateMedicinesRequest) -> AnalysisResponse:
    """
    Save the user's corrected and confirmed medicine list and PatientContext.
    Re-runs catalog matching for any modified medicine names.
    """
    existing = get_analysis_by_id(analysis_id)
    if not existing:
        raise HTTPException(status_code=404, detail={"error": "Analysis not found."})

    updated_medicines = []
    for med in payload.medicines:
        # Re-run matching on name_text in case user edited the name
        match_info = match_medicine_name(med.name_text)
        updated_medicines.append({
            "id": med.id,
            "name_text": med.name_text,
            "strength": med.strength,
            "dose": med.dose,
            "frequency": med.frequency,
            "duration": med.duration,
            "page": med.page,
            "read_quality": med.read_quality,
            "match_status": match_info["match_status"] if not med.matched_id else med.match_status,
            "matched_id": med.matched_id or match_info["matched_id"],
            "candidates": match_info["candidates"],
            "ingredients": med.ingredients if med.ingredients else match_info["ingredients"],
            "confirmed": med.confirmed
        })

    context_dict = payload.context.model_dump() if payload.context else {}
    
    # Run deterministic safety checks and build knowledge graph
    interaction_res = check_interactions(updated_medicines)
    graph_res = build_knowledge_graph(updated_medicines, interaction_res["interactions"])
    results_dict = {
        "interactions": interaction_res["interactions"],
        "duplicates": interaction_res["duplicates"],
        "coverage": interaction_res["coverage"],
        "graph": graph_res,
        "notice": interaction_res["notice"]
    }

    success = update_medicines_and_context(analysis_id, updated_medicines, context_dict, results=results_dict)
    if not success:
        raise HTTPException(status_code=500, detail={"error": "Failed to update medicines."})

    updated = get_analysis_by_id(analysis_id)
    return updated


@router.post("/{analysis_id}/run")
def run_analysis(analysis_id: str, background_tasks: BackgroundTasks):
    """
    Start the multi-agent analysis workflow in the background.
    Refuses if any medicine is unconfirmed.
    Returns { "run_id": run_id }.
    """
    run_id = schedule_analysis_run(analysis_id, background_tasks)
    return {"run_id": run_id}


@router.get("/{analysis_id}/events")
async def stream_analysis_events(analysis_id: str):
    """
    SSE stream of events for the latest run.
    Reads new rows from SQLite every 0.5s and yields them.
    Closes automatically when the run completes.
    """
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": "Analysis not found."})

    async def event_generator():
        last_event_id = 0
        run_id = get_latest_run_id(analysis_id)

        # Wait up to 5 seconds for run_id if just started
        wait_cycles = 0
        while not run_id and wait_cycles < 10:
            await asyncio.sleep(0.5)
            run_id = get_latest_run_id(analysis_id)
            wait_cycles += 1

        terminal_seen = False
        post_terminal_count = 0

        while True:
            events = get_events_since(analysis_id, run_id=run_id, since_id=last_event_id)
            for ev in events:
                last_event_id = ev["id"]
                if ev.get("component") == "Manager" and ev.get("status") in ("done", "failed"):
                    terminal_seen = True
                yield f"data: {json.dumps(ev)}\n\n"

            if terminal_seen:
                post_terminal_count += 1
                if post_terminal_count >= 2:
                    break

            # Safety fallback: if analysis status reached done/failed in database
            current = get_analysis_by_id(analysis_id)
            if current and current.status in ("done", "failed") and terminal_seen:
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{analysis_id}/report")
def get_analysis_report(analysis_id: str):
    """Builds and returns the ReportLab PDF medication safety report."""
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": "Analysis not found."})

    # Ensure interactions and graph are computed if analysis is not yet run by agents
    if (not analysis.results or "interactions" not in analysis.results) and analysis.medicines:
        interaction_res = check_interactions(analysis.medicines)
        graph_res = build_knowledge_graph(analysis.medicines, interaction_res["interactions"])
        analysis.results = {
            "interactions": interaction_res["interactions"],
            "duplicates": interaction_res["duplicates"],
            "coverage": interaction_res["coverage"],
            "graph": graph_res,
            "notice": interaction_res["notice"]
        }

    report_path = generate_pdf_report(analysis)
    if not report_path.exists():
        raise HTTPException(status_code=500, detail={"error": "Failed to generate report file."})

    filename_base = analysis.original_name.rsplit(".", 1)[0] if analysis.original_name else analysis_id
    safe_filename = f"medigraph_report_{filename_base}.pdf"
    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=safe_filename
    )


@router.delete("/{analysis_id}")
def delete_analysis(analysis_id: str):
    """Deletes analysis database record, uploaded file, and report."""
    stored_name = delete_analysis_record(analysis_id)
    if not stored_name:
        raise HTTPException(status_code=404, detail={"error": "Analysis not found."})

    # Remove uploaded file
    upload_file = settings.upload_path / stored_name
    if upload_file.exists():
        try:
            upload_file.unlink()
        except Exception:
            pass

    # Remove report file if generated
    report_file = settings.report_path / f"medigraph_report_{analysis_id}.pdf"
    if report_file.exists():
        try:
            report_file.unlink()
        except Exception:
            pass

    return {"status": "deleted", "id": analysis_id}
