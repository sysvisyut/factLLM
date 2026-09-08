from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProcessingJobResponse(BaseModel):
    id: str
    document_id: str
    stage: str
    status: str  # 'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'PARTIAL'
    progress_percentage: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
