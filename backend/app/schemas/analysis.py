from typing import List, Optional, Literal, Any, Dict
from pydantic import BaseModel, Field


class Medicine(BaseModel):
    id: str
    name_text: str
    strength: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    page: Optional[int] = 1
    read_quality: Literal["clear", "unclear"] = "clear"
    match_status: Literal["matched", "several_possible", "not_found"] = "not_found"
    matched_id: Optional[str] = None
    candidates: List[str] = Field(default_factory=list)
    ingredients: List[str] = Field(default_factory=list)
    confirmed: bool = False


class PatientContext(BaseModel):
    age: Optional[int] = None
    reason: Optional[str] = None
    allergies: Optional[str] = None
    pregnancy: Optional[Literal["yes", "no", "not_applicable"]] = None
    kidney_liver: Optional[str] = None


class AnalysisSummary(BaseModel):
    id: str
    created_at: str
    original_name: str
    status: str
    file_kind: Optional[str] = None
    text_source: Optional[str] = None
    page_count: Optional[int] = 1


class AnalysisResponse(BaseModel):
    id: str
    created_at: str
    original_name: str
    stored_name: str
    file_kind: str
    text_source: str
    page_count: int
    medicines: List[Medicine]
    context: Optional[PatientContext] = None
    results: Optional[Dict[str, Any]] = None
    status: str


class UpdateMedicinesRequest(BaseModel):
    medicines: List[Medicine]
    context: Optional[PatientContext] = None
