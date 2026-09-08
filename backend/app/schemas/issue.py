from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExtractionIssueBase(BaseModel):
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    issue_type: str  # 'AMBIGUOUS_TABLE_ASSOCIATION', 'OCR_FAILURE', 'MISSING_CONTEXT', 'ENTITY_AMBIGUITY', 'UNIT_AMBIGUITY', 'TEMPORAL_AMBIGUITY', 'LLM_EXTRACTION_FAILURE', 'CONFLICTING_EVIDENCE'
    description: str
    affected_text: Optional[str] = None
    attempted_resolution: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "DETECTED"


class ExtractionIssueCreate(ExtractionIssueBase):
    pass


class ExtractionIssueResponse(ExtractionIssueBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
