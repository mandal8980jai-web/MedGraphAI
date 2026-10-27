from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.db.repositories import get_analysis_by_id
from app.agents.conversation_agent import chat_with_conversation_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    analysis_id: str
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    flags: List[str] = Field(default_factory=list)
    language: Optional[str] = "en"


@router.post("", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """
    Chat endpoint powered by the Conversation Agent.
    Strictly observes clinical safety rules:
      - Emergency symptoms bypass LLM and trigger urgent care message immediately.
      - Never advises starting, stopping, skipping, or altering doses.
      - Does not receive raw prescription text (only confirmed medicines and review results).
      - Replaces unsafe claims deterministically with safety notices.
    """
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail={"error": "Message cannot be empty."})

    analysis = get_analysis_by_id(payload.analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": "Analysis not found."})

    medicines = [m.model_dump() for m in analysis.medicines]
    results = analysis.results if isinstance(analysis.results, dict) else {}
    context = analysis.context.model_dump() if analysis.context else {}

    chat_res = chat_with_conversation_agent(
        message=payload.message,
        medicines=medicines,
        results=results,
        context=context,
        history=payload.history
    )

    return ChatResponse(
        reply=chat_res.get("reply", ""),
        flags=chat_res.get("flags", []),
        language=chat_res.get("language", "en")
    )
