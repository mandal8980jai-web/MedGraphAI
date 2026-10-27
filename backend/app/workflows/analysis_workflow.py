import asyncio
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.db.repositories import (
    record_event,
    update_analysis_status_and_results
)
from app.services.interaction_engine import check_interactions, SAMPLE_DATA_NOTICE
from app.services.knowledge_graph import build_knowledge_graph
from app.agents.pharmacist_research_agent import research_medicine_evidence
from app.agents.alternative_research_agent import research_alternatives_for_medicines
from app.agents.safety_critic_agent import review_safety_and_evidence


async def run_full_analysis_workflow(
    analysis_id: str,
    run_id: str,
    medicines: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]]
) -> None:
    """
    Executes the multi-stage analysis workflow:
    1. Safety Checker (deterministic rules & knowledge graph)
    2. Evidence Helper & Alternatives Helper in parallel (bounded to 3 concurrent calls)
    3. Safety Reviewer (critic)
    4. Coordinator saves results and marks analysis done
    Records real status events to SQLite at every transition.
    """
    logger.info(f"Starting analysis workflow for analysis={analysis_id}, run={run_id}")
    collected_flags: List[str] = []

    try:
        # Start Manager
        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Manager",
            status="running",
            task="Initiating analysis workflow",
            detail=f"Scheduling tasks for {len(medicines)} confirmed medicines."
        )

        # -------------------------------------------------------------
        # STEP 1: Safety Checker (Deterministic engine & NetworkX graph)
        # -------------------------------------------------------------
        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Safety Checker",
            status="running",
            task="Checking configured interaction rules and duplicates",
            detail="Scanning catalog rules and active ingredients."
        )

        safety_res = check_interactions(medicines)
        interactions = safety_res.get("interactions", [])
        duplicates = safety_res.get("duplicates", [])
        coverage = safety_res.get("coverage", {})
        graph = build_knowledge_graph(medicines, interactions)

        inter_count = len(interactions)
        dup_count = len(duplicates)
        detail_msg = f"{len(medicines)} medicines checked: {inter_count} interaction warning(s), {dup_count} duplicate(s)."

        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Safety Checker",
            status="done",
            task="Interaction checks and medicine map complete",
            detail=detail_msg
        )

        # -------------------------------------------------------------
        # STEP 2: Evidence Helper & Alternatives Helper in parallel
        # -------------------------------------------------------------
        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Evidence Helper",
            status="running",
            task="Researching medical evidence (FDA, DailyMed, PubMed, Grounding)",
            detail="Searching official indications, cautions, and drug interactions."
        )

        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Alternatives Helper",
            status="running",
            task="Evaluating clinician discussion options",
            detail="Checking required patient clinical context."
        )

        # Semaphore limiting concurrent Gemini API calls to max 3
        semaphore = asyncio.Semaphore(3)

        async def bounded_evidence_call(med: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await asyncio.to_thread(research_medicine_evidence, med, medicines)

        async def bounded_alternatives_call() -> Dict[str, Any]:
            async with semaphore:
                return await asyncio.to_thread(research_alternatives_for_medicines, medicines, context)

        # Launch evidence tasks for all medicines and alternatives task concurrently
        evidence_tasks = [bounded_evidence_call(m) for m in medicines]
        alternatives_task = bounded_alternatives_call()

        evidence_results, alternatives_result = await asyncio.gather(
            asyncio.gather(*evidence_tasks, return_exceptions=True),
            alternatives_task,
            return_exceptions=True
        )

        # Process evidence results
        processed_evidence = []
        if isinstance(evidence_results, (list, tuple)):
            for idx, res in enumerate(evidence_results):
                med = medicines[idx]
                if isinstance(res, Exception):
                    logger.error(f"Evidence helper failed for {med.get('name_text')}: {res}")
                    processed_evidence.append({
                        "medicine_id": med.get("id"),
                        "medicine_name": med.get("name_text"),
                        "findings": ["Evidence research failed unexpectedly."],
                        "sources": [],
                        "status": "unavailable"
                    })
                elif isinstance(res, dict):
                    processed_evidence.append(res)
                    collected_flags.extend(res.get("flags", []))
        else:
            processed_evidence = []

        sourced_count = sum(1 for e in processed_evidence if e.get("status") == "ok")
        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Evidence Helper",
            status="done",
            task="Evidence research complete",
            detail=f"{len(processed_evidence)} medicine(s) researched, {sourced_count} with verified web sources."
        )

        # Process alternatives results
        if isinstance(alternatives_result, Exception):
            logger.error(f"Alternatives helper failed: {alternatives_result}")
            processed_alternatives = {
                "status": "unavailable",
                "missing": [],
                "items": []
            }
        elif isinstance(alternatives_result, dict):
            processed_alternatives = alternatives_result
            collected_flags.extend(alternatives_result.get("flags", []))
        else:
            processed_alternatives = {"status": "unavailable", "missing": [], "items": []}

        alt_status = processed_alternatives.get("status")
        if alt_status == "needs_more_info":
            missing_str = ", ".join(processed_alternatives.get("missing", []))
            alt_detail = f"Clinical details missing: {missing_str}. Skipped LLM calls for safety."
        elif alt_status == "ok":
            alt_detail = f"Researched options for {len(processed_alternatives.get('items', []))} medicine(s)."
        else:
            alt_detail = "Alternative candidate research was unavailable."

        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Alternatives Helper",
            status="done" if alt_status != "unavailable" else "failed",
            task="Alternative candidate review complete",
            detail=alt_detail
        )

        # -------------------------------------------------------------
        # STEP 3: Safety Critic Agent (Safety Reviewer)
        # -------------------------------------------------------------
        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Safety Reviewer",
            status="running",
            task="Reviewing claims, citations, and coverage limitations",
            detail="Checking unsupported findings and potential contradictions."
        )

        intermediate_results = {
            "interactions": interactions,
            "duplicates": duplicates,
            "coverage": coverage,
            "evidence": processed_evidence,
            "alternatives": processed_alternatives,
            "flags": collected_flags
        }

        critic_result = await asyncio.to_thread(review_safety_and_evidence, intermediate_results, medicines)
        review_issues = critic_result.get("issues", [])

        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Safety Reviewer",
            status="done",
            task="Safety and citation review complete",
            detail=f"Identified {len(review_issues)} clinical safety or coverage note(s)."
        )

        # -------------------------------------------------------------
        # STEP 4: Manager finalizes and saves results
        # -------------------------------------------------------------
        final_results = {
            "interactions": interactions,
            "duplicates": duplicates,
            "coverage": coverage,
            "evidence": processed_evidence,
            "alternatives": processed_alternatives,
            "review": {"issues": review_issues},
            "graph": graph,
            "flags": collected_flags,
            "notice": SAMPLE_DATA_NOTICE
        }

        update_analysis_status_and_results(
            analysis_id=analysis_id,
            status="done",
            results=final_results
        )

        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Manager",
            status="done",
            task="Medication safety analysis completed",
            detail="All deterministic and research phases finished. Results ready for review."
        )
        logger.info(f"Workflow successfully completed for analysis={analysis_id}")

    except Exception as e:
        logger.error(f"Workflow encountered fatal error for analysis={analysis_id}: {e}", exc_info=True)
        record_event(
            analysis_id=analysis_id,
            run_id=run_id,
            component="Manager",
            status="failed",
            task="Analysis workflow failed",
            detail=f"System error during analysis: {str(e)[:120]}"
        )
        update_analysis_status_and_results(
            analysis_id=analysis_id,
            status="failed",
            results={"error": "Analysis workflow failed. Please retry."}
        )
