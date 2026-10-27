from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.core.memory import get_current_rss_mb

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    llm_key_set: bool
    model: str
    memory_rss_mb: Optional[float] = None
    max_upload_mb: Optional[int] = None
    worker_concurrency: Optional[int] = None


@router.get("/health", response_model=HealthResponse)
@router.get("/api/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        llm_key_set=settings.is_llm_key_configured,
        model=settings.LLM_MODEL,
        memory_rss_mb=get_current_rss_mb(),
        max_upload_mb=settings.MAX_UPLOAD_MB,
        worker_concurrency=settings.WEB_CONCURRENCY
    )
