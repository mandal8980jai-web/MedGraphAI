import json
from typing import Optional, List, Dict, Any
from app.db.database import get_db
from app.schemas.analysis import AnalysisResponse, AnalysisSummary, Medicine, PatientContext


def save_analysis(
    analysis_id: str,
    created_at: str,
    original_name: str,
    stored_name: str,
    file_kind: str,
    text_source: str,
    page_count: int,
    extracted_text: str,
    medicines: List[Dict[str, Any]],
    status: str = "uploaded"
) -> None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO analyses (
                id, created_at, original_name, stored_name, file_kind,
                text_source, page_count, extracted_text, medicines_json,
                context_json, results_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_id,
                created_at,
                original_name,
                stored_name,
                file_kind,
                text_source,
                page_count,
                extracted_text,
                json.dumps(medicines),
                json.dumps({}),
                json.dumps({}),
                status
            )
        )
        conn.commit()


def get_analysis_by_id(analysis_id: str) -> Optional[AnalysisResponse]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, original_name, stored_name, file_kind,
                   text_source, page_count, medicines_json, context_json,
                   results_json, status
            FROM analyses WHERE id = ?
            """,
            (analysis_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        medicines_data = json.loads(row["medicines_json"] or "[]")
        context_data = json.loads(row["context_json"] or "{}")
        results_data = json.loads(row["results_json"] or "{}")

        medicines = [Medicine(**m) for m in medicines_data]
        context = PatientContext(**context_data) if context_data else None

        return AnalysisResponse(
            id=row["id"],
            created_at=row["created_at"],
            original_name=row["original_name"],
            stored_name=row["stored_name"],
            file_kind=row["file_kind"],
            text_source=row["text_source"],
            page_count=row["page_count"],
            medicines=medicines,
            context=context,
            results=results_data if results_data else None,
            status=row["status"]
        )


def list_all_analyses() -> List[AnalysisSummary]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, original_name, status, file_kind, text_source, page_count
            FROM analyses
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        return [
            AnalysisSummary(
                id=r["id"],
                created_at=r["created_at"],
                original_name=r["original_name"],
                status=r["status"],
                file_kind=r["file_kind"],
                text_source=r["text_source"],
                page_count=r["page_count"]
            )
            for r in rows
        ]


def update_medicines_and_context(
    analysis_id: str,
    medicines: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
    results: Optional[Dict[str, Any]] = None
) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        if results is not None:
            cursor.execute(
                """
                UPDATE analyses
                SET medicines_json = ?, context_json = ?, results_json = ?, status = 'confirmed'
                WHERE id = ?
                """,
                (
                    json.dumps(medicines),
                    json.dumps(context or {}),
                    json.dumps(results),
                    analysis_id
                )
            )
        else:
            cursor.execute(
                """
                UPDATE analyses
                SET medicines_json = ?, context_json = ?, status = 'confirmed'
                WHERE id = ?
                """,
                (
                    json.dumps(medicines),
                    json.dumps(context or {}),
                    analysis_id
                )
            )
        conn.commit()
        return cursor.rowcount > 0


def delete_analysis_record(analysis_id: str) -> Optional[str]:
    """Deletes analysis and related events. Returns stored_name so caller can remove disk files."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT stored_name FROM analyses WHERE id = ?", (analysis_id,))
        row = cursor.fetchone()
        if not row:
            return None
        stored_name = row["stored_name"]
        cursor.execute("DELETE FROM events WHERE analysis_id = ?", (analysis_id,))
        cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        return stored_name


def update_analysis_status_and_results(
    analysis_id: str,
    status: str,
    results: Optional[Dict[str, Any]] = None
) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        if results is not None:
            cursor.execute(
                """
                UPDATE analyses
                SET status = ?, results_json = ?
                WHERE id = ?
                """,
                (status, json.dumps(results), analysis_id)
            )
        else:
            cursor.execute(
                """
                UPDATE analyses
                SET status = ?
                WHERE id = ?
                """,
                (status, analysis_id)
            )
        conn.commit()
        return cursor.rowcount > 0


def record_event(
    analysis_id: str,
    run_id: str,
    component: str,
    status: str,
    task: str,
    detail: str = ""
) -> int:
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (analysis_id, run_id, time, component, status, task, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (analysis_id, run_id, now_iso, component, status, task, detail)
        )
        conn.commit()
        return cursor.lastrowid or 0


def get_events_since(
    analysis_id: str,
    run_id: Optional[str] = None,
    since_id: int = 0
) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if run_id:
            cursor.execute(
                """
                SELECT id, analysis_id, run_id, time, component, status, task, detail
                FROM events
                WHERE analysis_id = ? AND run_id = ? AND id > ?
                ORDER BY id ASC
                """,
                (analysis_id, run_id, since_id)
            )
        else:
            cursor.execute(
                """
                SELECT id, analysis_id, run_id, time, component, status, task, detail
                FROM events
                WHERE analysis_id = ? AND id > ?
                ORDER BY id ASC
                """,
                (analysis_id, since_id)
            )
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "analysis_id": r["analysis_id"],
                "run_id": r["run_id"],
                "time": r["time"],
                "component": r["component"],
                "status": r["status"],
                "task": r["task"],
                "detail": r["detail"]
            }
            for r in rows
        ]


def get_latest_run_id(analysis_id: str) -> Optional[str]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT run_id FROM events
            WHERE analysis_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (analysis_id,)
        )
        row = cursor.fetchone()
        return row["run_id"] if row else None

