from pydantic import BaseModel
from typing import Dict, Any, Optional


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    database: Dict[str, Any]
    llm_provider: str
    storage: Dict[str, Any]
