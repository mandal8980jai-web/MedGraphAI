import uuid
from typing import Dict, Any, Optional
from fastapi import BackgroundTasks, HTTPException
from app.db.repositories import (
    get_analysis_by_id,
    update_analysis_status_and_results,
    record_event
)
from app.workflows.analysis_workflow import run_full_analysis_workflow


def schedule_analysis_run(
    analysis_id: str,
    background_tasks: BackgroundTasks
) -> str:
    """
    Manager (Coordinator):
    Validates that the analysis exists and that ALL medicines have been explicitly confirmed.
    Refuses execution if any medicine is unconfirmed.
    Schedules the full multi-agent workflow in the background.
    Returns the unique run_id.
    """
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": "Analysis not found."})

    medicines = [m.model_dump() for m in analysis.medicines]
    if not medicines:
        raise HTTPException(
            status_code=400,
            detail={"error": "No medicines found in analysis. Please upload or add medicines first."}
        )

    # Refuse if any medicine is unconfirmed
    unconfirmed = [m for m in medicines if not m.get("confirmed")]
    if unconfirmed:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Cannot run analysis: {len(unconfirmed)} medicine(s) are not confirmed. Please check every row."}
        )

    run_id = str(uuid.uuid4())

    # Set status to running in DB
    update_analysis_status_and_results(analysis_id, status="running")

    # Log initial queue event
    record_event(
        analysis_id=analysis_id,
        run_id=run_id,
        component="Manager",
        status="waiting",
        task="Workflow queued",
        detail="Preparing environment and validating confirmed medicines."
    )

    context_dict = analysis.context.model_dump() if analysis.context else {}

    # Schedule background execution
    background_tasks.add_task(
        run_full_analysis_workflow,
        analysis_id=analysis_id,
        run_id=run_id,
        medicines=medicines,
        context=context_dict
    )

    return run_id
