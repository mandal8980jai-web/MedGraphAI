from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.db.database import init_db, get_db
from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.chat import router as chat_router
from app.api.routes.assistant import router as assistant_router, medicines_router


def cleanup_expired_analyses() -> None:
    """Deletes analyses and their associated files older than RETENTION_DAYS."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)
        cutoff_iso = cutoff_date.isoformat()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, stored_name FROM analyses WHERE created_at < ?", (cutoff_iso,))
            expired = cursor.fetchall()

            for row in expired:
                analysis_id = row["id"]
                stored_name = row["stored_name"]
                if stored_name:
                    upload_file = settings.upload_path / stored_name
                    if upload_file.exists():
                        try:
                            upload_file.unlink()
                        except Exception as e:
                            logger.warning(f"Could not delete expired upload file: {e}")

                report_file = settings.report_path / f"medigraph_report_{analysis_id}.pdf"
                if report_file.exists():
                    try:
                        report_file.unlink()
                    except Exception as e:
                        logger.warning(f"Could not delete expired report file: {e}")

                cursor.execute("DELETE FROM events WHERE analysis_id = ?", (analysis_id,))
                cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))

            conn.commit()
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired analyses older than {settings.RETENTION_DAYS} days.")
    except Exception as e:
        logger.error(f"Error during retention cleanup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MediGraph AI Backend...")
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.report_path.mkdir(parents=True, exist_ok=True)
    init_db()
    cleanup_expired_analyses()
    if not settings.is_llm_key_configured:
        logger.warning("LLM_API_KEY is not configured or is a placeholder. AI features will be disabled until set.")
    else:
        logger.info(f"Gemini API key is configured with model '{settings.LLM_MODEL}'.")
    yield
    logger.info("Shutting down MediGraph AI Backend...")


app = FastAPI(
    title="MediGraph AI API",
    description="OCR-First, Multi-Agent Medication Safety & Evidence Research System",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred. Please try again later."}
    )


# Include API routers
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(analyses_router)
app.include_router(chat_router)
app.include_router(assistant_router)
app.include_router(medicines_router)
