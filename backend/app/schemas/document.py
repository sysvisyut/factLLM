from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentBase(BaseModel):
    filename: str
    content_hash: str
    file_size_bytes: int
    page_count: int


class DocumentCreate(DocumentBase):
    storage_path: str


class DocumentResponse(DocumentBase):
    id: str
    storage_path: str
    created_at: datetime
    fact_count: Optional[int] = 0
    issue_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    filename: str
    status: str
    message: str
