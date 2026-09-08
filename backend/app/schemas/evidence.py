from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class EvidenceAtomBase(BaseModel):
    page_number: int
    section_heading: Optional[str] = None
    exact_text: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    bbox: Optional[List[float]] = None
    table_cell_info: Optional[Dict[str, Any]] = None
    extraction_method: str = "native_text"
    source_hash: str


class EvidenceAtomCreate(EvidenceAtomBase):
    document_id: str


class EvidenceAtomResponse(EvidenceAtomBase):
    id: str
    document_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
